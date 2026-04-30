import pytest
import asyncio
from datetime import datetime, UTC
from fastapi import HTTPException
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    invalidate_token,
    hash_password,
    verify_password,
    ldap_authenticate,
    token_blacklist,
)
from app.config import get_settings

settings = get_settings()

def test_create_access_token():
    user_id = "test-user-id"
    role = "trader"
    token = create_access_token(user_id, role)
    assert isinstance(token, str)

    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["role"] == role
    assert payload["type"] == "access"
    assert "exp" in payload

def test_create_refresh_token():
    user_id = "test-user-id"
    token = create_refresh_token(user_id)
    assert isinstance(token, str)

    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"
    assert "exp" in payload

def test_decode_token_invalid():
    with pytest.raises(HTTPException) as excinfo:
        decode_token("invalid.token.here")
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Invalid token"

def test_invalidate_token_and_decode():
    token = create_access_token("user_id", "trader")
    # Clean up state just in case
    if token in token_blacklist:
        token_blacklist.remove(token)

    payload = decode_token(token)
    assert payload["sub"] == "user_id"

    invalidate_token(token)

    with pytest.raises(HTTPException) as excinfo:
        decode_token(token)
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Token has been revoked"

    # cleanup
    token_blacklist.remove(token)

@pytest.mark.asyncio
async def test_hash_and_verify_password():
    password = "supersecretpassword"
    hashed = await hash_password(password)

    assert isinstance(hashed, str)
    assert hashed != password

    is_valid = await verify_password(password, hashed)
    assert is_valid is True

    is_invalid = await verify_password("wrongpassword", hashed)
    assert is_invalid is False

@pytest.mark.asyncio
async def test_ldap_authenticate_failure():
    # Attempting to test ldap authenticate with wrong credentials against nothing should return None
    # since we mock nothing and there's no actual ldap server running during tests.
    res = await ldap_authenticate("testuser", "testpassword")
    assert res is None
