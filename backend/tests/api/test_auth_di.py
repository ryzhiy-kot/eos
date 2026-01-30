import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.services.auth.protocol import AuthServiceProtocol
from app.services.auth.dependency import get_auth_service
from app.models.user import User
from typing import Optional

# Mock Auth Service
class MockAuthService(AuthServiceProtocol):
    async def authenticate(
        self, db: AsyncSession, username: str, password: Optional[str] = None
    ) -> Optional[User]:
        if username == "mock_user":
            return User(id=999, user_id="mock_user", enabled=True, profile={"name": "Mock User"}, memberships=[])
        return None

@pytest.mark.asyncio
async def test_auth_dependency_injection(client: AsyncClient):
    # Override the dependency
    # Preserve existing overrides (like get_db from conftest)
    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_auth_service] = lambda: MockAuthService()

    try:
        # Test valid login with mock service
        # If I return None, I should get 401 (as I just added). This proves my Mock service was called and returned None.
        # Because the default LocalAuthService would have auto-registered "unknown_user" and returned 200.
        response = await client.post("/api/v1/auth/login", json={"username": "unknown_user"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Authentication failed"

    finally:
        app.dependency_overrides = original_overrides

@pytest.mark.asyncio
async def test_default_auth_service(client: AsyncClient):
    # Test with default service (LocalAuthService)
    # This relies on auto-registration
    username = "test_auto_reg_user_di"
    response = await client.post("/api/v1/auth/login", json={"username": username})
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == username
