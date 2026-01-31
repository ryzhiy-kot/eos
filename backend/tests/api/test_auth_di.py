import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.services.auth.protocol import AuthServiceProtocol, AuthResult
from app.services.auth.dependency import get_auth_service
from app.models.user import User
from app.schemas.user import User as UserSchema
from typing import Optional


# Mock Auth Service
class MockAuthService(AuthServiceProtocol):
    async def authenticate(
        self, db: AsyncSession, username: str, password: Optional[str] = None
    ) -> AuthResult:
        if username == "mock_user":
            user = User(
                id=999,
                user_id="mock_user",
                enabled=True,
                profile={"name": "Mock User"},
                memberships=[],
            )
            # Ensure user is Pydantic model
            user_schema = UserSchema.model_validate(user)
            return AuthResult(user=user_schema, session_token="mock_token_123")
        return AuthResult(error="Authentication failed")

    async def logout(self, session_token: str) -> None:
        pass


@pytest.mark.asyncio
async def test_auth_dependency_injection(client: AsyncClient):
    # Override the dependency
    # Preserve existing overrides (like get_db from conftest)
    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_auth_service] = lambda: MockAuthService()

    try:
        # Test valid login with mock service
        # Using Form Data
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "unknown_user", "password": "any"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Authentication failed"

        # Test success
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "mock_user", "password": "any"}
        )
        assert response.status_code == 200
        assert response.json()["access_token"] == "mock_token_123"

    finally:
        app.dependency_overrides = original_overrides


@pytest.mark.asyncio
async def test_default_auth_service(client: AsyncClient):
    # Test with default service (LocalAuthService)
    # This relies on auto-registration
    username = "test_auto_reg_user_di"
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": "password"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["user_id"] == username
