import pytest
import asyncio
from unittest.mock import patch, MagicMock
from fastapi import FastAPI, Depends, HTTPException, status
from httpx import AsyncClient, ASGITransport
from jose import JWTError, jwt

from app.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    verify_password,
    ldap_authenticate,
    token_blacklist,
    settings,
)

# Mock app for integration testing of dependency injection
app = FastAPI()

@app.get("/secure-data")
async def secure_endpoint(user: dict = Depends(get_current_user)):
    return {"message": "secure data", "user_id": user["sub"]}

@pytest.mark.asyncio
async def test_password_hashing_and_verification():
    password = "supersecretpassword"
    hashed = await hash_password(password)

    assert hashed != password
    assert isinstance(hashed, str)

    is_valid = await verify_password(password, hashed)
    assert is_valid is True

    is_invalid = await verify_password("wrongpassword", hashed)
    assert is_invalid is False


@pytest.mark.asyncio
async def test_jwt_token_generation_and_decoding():
    user_id = "test-user-123"
    role = "trader"

    # Test Access Token
    access_token = await create_access_token(user_id, role)
    assert isinstance(access_token, str)

    decoded_access = await decode_token(access_token)
    assert decoded_access["sub"] == user_id
    assert decoded_access["role"] == role
    assert decoded_access["type"] == "access"
    assert "exp" in decoded_access

    # Test Refresh Token
    refresh_token = await create_refresh_token(user_id)
    assert isinstance(refresh_token, str)

    decoded_refresh = await decode_token(refresh_token)
    assert decoded_refresh["sub"] == user_id
    assert decoded_refresh["type"] == "refresh"
    assert "role" not in decoded_refresh
    assert "exp" in decoded_refresh


@pytest.mark.asyncio
async def test_decode_invalid_token():
    with pytest.raises(HTTPException) as excinfo:
        await decode_token("invalid.token.here")

    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert excinfo.value.detail == "Invalid token"


@pytest.mark.asyncio
async def test_decode_revoked_token():
    user_id = "test-user"
    token = await create_access_token(user_id, "admin")

    # Revoke token
    token_blacklist.add(token)

    with pytest.raises(HTTPException) as excinfo:
        await decode_token(token)

    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert excinfo.value.detail == "Token has been revoked"

    # Cleanup
    token_blacklist.remove(token)


@pytest.mark.asyncio
async def test_ldap_authenticate_success():
    with patch("ldap3.Connection") as MockConnection:
        # Mock LDAP connection and entry
        mock_conn = MagicMock()
        MockConnection.return_value = mock_conn

        mock_entry = MagicMock()
        mock_entry.uid = "jdoe"
        mock_entry.mail = "jdoe@example.com"
        mock_entry.cn = "John Doe"

        mock_conn.entries = [mock_entry]

        result = await ldap_authenticate("jdoe", "password123")

        assert result is not None
        assert result["username"] == "jdoe"
        assert result["email"] == "jdoe@example.com"
        assert result["display_name"] == "John Doe"


@pytest.mark.asyncio
async def test_ldap_authenticate_failure():
    with patch("ldap3.Connection") as MockConnection:
        # Mock LDAP connection with no entries (failed search/bind)
        mock_conn = MagicMock()
        MockConnection.return_value = mock_conn
        mock_conn.entries = []

        result = await ldap_authenticate("invalid", "wrongpass")

        assert result is None


@pytest.mark.asyncio
async def test_dependency_injection_success():
    user_id = "test-user-id"
    token = await create_access_token(user_id, "admin")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/secure-data", headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "secure data"
    assert data["user_id"] == user_id


@pytest.mark.asyncio
async def test_dependency_injection_missing_token():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/secure-data")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_dependency_injection_invalid_token_type():
    user_id = "test-user-id"
    # Create refresh token instead of access token
    token = await create_refresh_token(user_id)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/secure-data", headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token type"}
