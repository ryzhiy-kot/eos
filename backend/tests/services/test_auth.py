import pytest
import asyncio
from datetime import datetime, UTC
from fastapi import HTTPException
from app.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    invalidate_token,
    get_current_user,
    ldap_authenticate,
    token_blacklist
)
from app.config import get_settings

settings = get_settings()

@pytest.mark.asyncio
async def test_password_hashing():
    password = "supersecretpassword123!"
    hashed = await hash_password(password)
    assert hashed != password
    assert await verify_password(password, hashed)
    assert not await verify_password("wrongpassword", hashed)

@pytest.mark.asyncio
async def test_create_and_decode_access_token():
    user_id = "test-user-id"
    role = "admin"
    token = create_access_token(user_id, role)

    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["role"] == role
    assert payload["type"] == "access"
    assert "exp" in payload

@pytest.mark.asyncio
async def test_create_and_decode_refresh_token():
    user_id = "test-user-id"
    token = create_refresh_token(user_id)

    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"
    assert "exp" in payload

@pytest.mark.asyncio
async def test_token_invalidation():
    user_id = "test-user-id"
    token = create_access_token(user_id, "trader")

    # Valid initially
    payload = decode_token(token)
    assert payload["sub"] == user_id

    # Invalidate token
    invalidate_token(token)

    # Should raise HTTPException after invalidation
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token)
    assert exc_info.value.status_code == 401
    assert "revoked" in exc_info.value.detail

    # Cleanup token blacklist to not affect other tests
    token_blacklist.clear()

@pytest.mark.asyncio
async def test_get_current_user_invalid_type():
    from fastapi.security import HTTPAuthorizationCredentials

    user_id = "test-user-id"
    # Create refresh token instead of access token
    token = create_refresh_token(user_id)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials)
    assert exc_info.value.status_code == 401
    assert "Invalid token type" in exc_info.value.detail

@pytest.mark.asyncio
async def test_ldap_authenticate_failure():
    # Since LDAP server is not configured in tests, it should gracefully fail and return None
    result = await ldap_authenticate("testuser", "testpassword")
    assert result is None
