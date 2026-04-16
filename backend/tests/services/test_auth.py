import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import bcrypt
import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt

from app.api.routes.auth import TRADER_USER_ID, router as auth_router
from app.config import get_settings
from app.main import app
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_password_sync,
    invalidate_token,
    ldap_authenticate,
    verify_password,
    token_blacklist,
)

settings = get_settings()


@pytest.fixture(autouse=True)
def clear_token_blacklist():
    """Clear the in-memory token blacklist before each test."""
    token_blacklist.clear()
    yield


@pytest.fixture
def test_client():
    """Create a test client that uses the FastAPI app."""
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def test_create_access_token():
    user_id = "test_user_id"
    role = "trader"
    token = create_access_token(user_id, role)

    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert payload["sub"] == user_id
    assert payload["role"] == role
    assert payload["type"] == "access"
    assert "exp" in payload


def test_create_refresh_token():
    user_id = "test_user_id"
    token = create_refresh_token(user_id)

    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"
    assert "exp" in payload


def test_hash_password_sync():
    password = "my_secret_password"
    hashed = hash_password_sync(password)
    assert hashed != password
    assert bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


@pytest.mark.asyncio
async def test_hash_password():
    password = "my_secret_password_async"
    hashed = await hash_password(password)
    assert hashed != password
    assert bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


@pytest.mark.asyncio
async def test_verify_password():
    password = "password123"
    hashed = await hash_password(password)
    is_valid = await verify_password(password, hashed)
    assert is_valid is True

    is_invalid = await verify_password("wrong_password", hashed)
    assert is_invalid is False


@pytest.mark.asyncio
async def test_ldap_authenticate_success():
    with patch("ldap3.Connection") as mock_conn_class, \
         patch("ldap3.Server") as mock_server_class:
        mock_conn_instance = MagicMock()
        mock_conn_class.return_value = mock_conn_instance

        mock_entry = MagicMock()
        mock_entry.uid = "testuser"
        mock_entry.mail = "testuser@company.com"
        mock_entry.cn = "Test User"

        mock_conn_instance.entries = [mock_entry]

        result = await ldap_authenticate("testuser", "password123")

        assert result is not None
        assert result["username"] == "testuser"
        assert result["email"] == "testuser@company.com"
        assert result["display_name"] == "Test User"

        mock_conn_instance.search.assert_called_once()
        mock_conn_instance.unbind.assert_called_once()


@pytest.mark.asyncio
async def test_ldap_authenticate_failure():
    with patch("ldap3.Connection") as mock_conn_class, \
         patch("ldap3.Server") as mock_server_class:
        mock_conn_instance = MagicMock()
        mock_conn_class.return_value = mock_conn_instance

        # Simulate no entries found
        mock_conn_instance.entries = []

        result = await ldap_authenticate("testuser", "wrongpassword")

        assert result is None
        mock_conn_instance.search.assert_called_once()
        mock_conn_instance.unbind.assert_called_once()


@pytest.mark.asyncio
async def test_login_mock_user_success(test_client):
    response = await test_client.post("/api/auth/login", json={"username": "trader", "password": "trader123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_mock_user_invalid_credentials(test_client):
    response = await test_client.post("/api/auth/login", json={"username": "trader", "password": "wrongpassword"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_refresh_token_success(test_client):
    # First, get a valid refresh token
    login_response = await test_client.post("/api/auth/login", json={"username": "trader", "password": "trader123"})
    refresh_token = login_response.json()["refresh_token"]

    # Now refresh it
    response = await test_client.post("/api/auth/refresh", params={"refresh_token": refresh_token})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_token_invalid(test_client):
    response = await test_client.post("/api/auth/refresh", params={"refresh_token": "invalid_token"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_success(test_client):
    login_response = await test_client.post("/api/auth/login", json={"username": "trader", "password": "trader123"})
    access_token = login_response.json()["access_token"]

    response = await test_client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "trader@company.com"
    assert data["role"] == "trader"
    assert data["id"] == TRADER_USER_ID


@pytest.mark.asyncio
async def test_get_me_unauthorized(test_client):
    response = await test_client.get("/api/auth/me")
    assert response.status_code == 401 # FastAPI HTTPBearer without token returns 401 if auto_error=True but we didn't specify. actually often 403. But let's check it handles correctly.


@pytest.mark.asyncio
async def test_logout_success(test_client):
    login_response = await test_client.post("/api/auth/login", json={"username": "trader", "password": "trader123"})
    access_token = login_response.json()["access_token"]

    response = await test_client.post("/api/auth/logout", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() == {"message": "Logged out successfully"}

    # Verify the token is invalid after logout
    response_after = await test_client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert response_after.status_code == 401
    assert response_after.json()["detail"] == "Token has been revoked"
