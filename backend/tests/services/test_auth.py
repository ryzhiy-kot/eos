import pytest
from jose import jwt
from datetime import UTC, datetime, timedelta

from app.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    invalidate_token,
    token_blacklist,
    hash_password,
    verify_password,
    ldap_authenticate,
)
from app.config import get_settings
from fastapi import HTTPException, status

settings = get_settings()

@pytest.mark.asyncio
async def test_hash_and_verify_password():
    password = "supersecretpassword"

    hashed = await hash_password(password)
    assert hashed != password
    assert hashed.startswith("$2b$")

    is_valid = await verify_password(password, hashed)
    assert is_valid is True

    is_invalid = await verify_password("wrongpassword", hashed)
    assert is_invalid is False

def test_create_access_token():
    user_id = "test-user-id"
    role = "trader"
    token = create_access_token(user_id, role)

    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert payload["sub"] == user_id
    assert payload["role"] == role
    assert payload["type"] == "access"
    assert "exp" in payload

def test_create_refresh_token():
    user_id = "test-user-id"
    token = create_refresh_token(user_id)

    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"
    assert "exp" in payload

def test_decode_valid_token():
    user_id = "test-user-id"
    role = "trader"
    token = create_access_token(user_id, role)

    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["role"] == role
    assert payload["type"] == "access"

def test_decode_invalid_token():
    with pytest.raises(HTTPException) as excinfo:
        decode_token("invalid.token.string")
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert excinfo.value.detail == "Invalid token"

def test_invalidate_token():
    user_id = "test-user-id"
    role = "trader"
    token = create_access_token(user_id, role)

    # Token should be valid initially
    payload = decode_token(token)
    assert payload["sub"] == user_id

    # Invalidate the token
    invalidate_token(token)
    assert token in token_blacklist

    # Decoding an invalidated token should raise an error
    with pytest.raises(HTTPException) as excinfo:
        decode_token(token)
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert excinfo.value.detail == "Token has been revoked"

@pytest.mark.asyncio
async def test_ldap_authenticate_connection_error():
    # Attempting to connect to a non-existent LDAP server should fail gracefully and return None
    result = await ldap_authenticate("testuser", "testpassword")
    assert result is None
