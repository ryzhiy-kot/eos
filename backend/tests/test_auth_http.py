import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.auth.http import HttpAuthService
from app.schemas.user import UserBase
from app.services.auth.protocol import AuthResult

@pytest.mark.asyncio
async def test_http_auth_success():
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "user_id": "test_user",
            "profile": {"name": "Test User"},
            "enabled": True,
            "session_token": "token123",
            "session_expires_at": "2026-01-01T00:00:00"
        }
        mock_client.post.return_value = mock_response

        service = HttpAuthService()
        result = await service.authenticate(None, "test_user", "password")

        assert isinstance(result, AuthResult)
        assert result.user is not None
        assert isinstance(result.user, UserBase)
        assert result.user.user_id == "test_user"
        assert result.user.profile["name"] == "Test User"
        assert result.session_token == "token123"

@pytest.mark.asyncio
async def test_http_auth_failure():
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_client.post.return_value = mock_response

        service = HttpAuthService()
        result = await service.authenticate(None, "test_user", "wrong_password")

        assert isinstance(result, AuthResult)
        assert result.error == "Authentication failed"
        assert result.user is None
