import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.auth.http import HttpAuthService
from app.schemas.user import UserBase

from datetime import datetime
from app.schemas.user import UserBase

@pytest.mark.asyncio
async def test_http_auth_success():
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "user": {
                "user_id": "test_user",
                "profile": {"name": "Test User"},
                "enabled": True
            },
            "session_token": "mock_token",
            "session_expires_at": datetime.now().isoformat()
        }
        mock_client.post.return_value = mock_response

        service = HttpAuthService()
        result = await service.authenticate(None, "test_user", "password")

        assert result is not None
        user, token, expires = result
        assert isinstance(user, UserBase)
        assert user.user_id == "test_user"
        assert user.profile["name"] == "Test User"
        assert token == "mock_token"

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

        assert result is None
