import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.auth.http import HttpAuthService
from app.services.user_service import UserService
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_http_auth_success(db_session: AsyncSession):
    # Setup
    provider = HttpAuthService(url="http://mock-auth/login", api_key="secret")

    # Mock httpx response (use MagicMock for the response object itself)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "user_id": "remote_user",
        "profile": {"name": "Remote User"}
    }

    # Mock httpx client
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_response

        # Call authenticate
        user = await provider.authenticate(db_session, "remote_user", "password")

        # Verify
        assert user is not None
        assert user.user_id == "remote_user"
        assert user.profile["name"] == "Remote User"

        # Check DB
        db_user = await UserService.get_by_user_id(db_session, "remote_user")
        assert db_user is not None

        # Verify request headers/payload
        mock_client.post.assert_called_with(
            "http://mock-auth/login",
            json={"username": "remote_user", "password": "password"},
            headers={"Authorization": "Bearer secret"},
            timeout=10.0
        )

@pytest.mark.asyncio
async def test_http_auth_failure(db_session: AsyncSession):
    provider = HttpAuthService(url="http://mock-auth/login")

    mock_response = MagicMock()
    mock_response.status_code = 401

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_response

        user = await provider.authenticate(db_session, "unknown", "pass")
        assert user is None
