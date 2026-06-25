import pytest
from jose import jwt

from app.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    invalidate_token,
    verify_password,
    token_blacklist,
)
from app.config import get_settings
from fastapi import HTTPException, status

settings = get_settings()

@pytest.mark.asyncio
async def test_hash_and_verify_password():
    password = "secret_password"
    hashed = await hash_password(password)

    # Should verify correctly
    assert await verify_password(password, hashed) is True

    # Should fail with wrong password
    assert await verify_password("wrong_password", hashed) is False


def test_create_and_decode_access_token():
    user_id = "test-user-123"
    role = "trader"

    token = create_access_token(user_id, role)
    payload = decode_token(token)

    assert payload["sub"] == user_id
    assert payload["role"] == role
    assert payload["type"] == "access"
    assert "exp" in payload


def test_create_and_decode_refresh_token():
    user_id = "test-user-123"

    token = create_refresh_token(user_id)
    payload = decode_token(token)

    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"
    assert "exp" in payload


def test_invalidate_token():
    user_id = "test-user-123"
    role = "trader"

    token = create_access_token(user_id, role)

    # Ensure token is valid initially
    decode_token(token)

    # Invalidate token
    invalidate_token(token)

    # Check if decode fails
    with pytest.raises(HTTPException) as excinfo:
        decode_token(token)

    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert excinfo.value.detail == "Token has been revoked"

    # Clean up token blacklist
    token_blacklist.clear()


def test_decode_invalid_token():
    with pytest.raises(HTTPException) as excinfo:
        decode_token("invalid.token.here")

    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert excinfo.value.detail == "Invalid token"
