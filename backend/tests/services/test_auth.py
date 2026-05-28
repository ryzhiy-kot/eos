import pytest
from jose import jwt
from datetime import datetime, UTC, timedelta
from app.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    invalidate_token,
    ldap_authenticate,
    token_blacklist,
)
from app.config import get_settings
from fastapi import HTTPException, status

settings = get_settings()

@pytest.mark.asyncio
async def test_password_hashing():
    password = "secretpassword"
    hashed = await hash_password(password)
    assert hashed != password
    assert await verify_password(password, hashed) is True
    assert await verify_password("wrongpassword", hashed) is False

def test_create_access_token():
    user_id = "test-user-id"
    role = "trader"
    token = create_access_token(user_id, role)
    assert token is not None

    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["role"] == role
    assert payload["type"] == "access"

def test_create_refresh_token():
    user_id = "test-user-id"
    token = create_refresh_token(user_id)
    assert token is not None

    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"
    assert "role" not in payload

def test_decode_invalid_token():
    with pytest.raises(HTTPException) as excinfo:
        decode_token("invalid_token_string")
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert excinfo.value.detail == "Invalid token"

def test_invalidate_token():
    user_id = "test-user-id"
    token = create_access_token(user_id, "trader")

    # Valid token should be decoded successfully
    payload = decode_token(token)
    assert payload["sub"] == user_id

    # Invalidate token
    invalidate_token(token)
    assert token in token_blacklist

    # Decoded invalidated token should raise HTTPException
    with pytest.raises(HTTPException) as excinfo:
        decode_token(token)
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert excinfo.value.detail == "Token has been revoked"

@pytest.mark.asyncio
async def test_ldap_authenticate_failure():
    # Attempting to authenticate with invalid credentials or missing LDAP server
    # should return None
    result = await ldap_authenticate("wronguser", "wrongpassword")
    assert result is None
