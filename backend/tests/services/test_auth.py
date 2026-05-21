import pytest
from datetime import UTC, datetime, timedelta
from jose import jwt
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    invalidate_token,
    get_current_user,
    hash_password,
    verify_password,
    ldap_authenticate,
    token_blacklist,
)
from app.config import get_settings
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

settings = get_settings()

@pytest.fixture(autouse=True)
def clear_blacklist():
    token_blacklist.clear()
    yield

@pytest.mark.asyncio
async def test_hash_and_verify_password():
    password = "secure_password_123"
    hashed = await hash_password(password)
    assert hashed != password
    assert await verify_password(password, hashed) is True
    assert await verify_password("wrong_password", hashed) is False

def test_create_and_decode_access_token():
    user_id = "test_user"
    role = "admin"
    token = create_access_token(user_id, role)

    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["role"] == role
    assert payload["type"] == "access"

def test_create_and_decode_refresh_token():
    user_id = "test_user"
    token = create_refresh_token(user_id)

    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"

def test_decode_invalid_token():
    with pytest.raises(HTTPException) as exc:
        decode_token("invalid.token.here")
    assert exc.value.status_code == 401

def test_token_invalidation():
    token = create_access_token("user1", "user")
    invalidate_token(token)

    with pytest.raises(HTTPException) as exc:
        decode_token(token)
    assert exc.value.status_code == 401
    assert "revoked" in exc.value.detail

@pytest.mark.asyncio
async def test_get_current_user():
    token = create_access_token("user1", "user")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    user = await get_current_user(creds)
    assert user["sub"] == "user1"

@pytest.mark.asyncio
async def test_get_current_user_invalid_type():
    token = create_refresh_token("user1")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with pytest.raises(HTTPException) as exc:
        await get_current_user(creds)
    assert exc.value.status_code == 401
    assert "type" in exc.value.detail

@pytest.mark.asyncio
async def test_ldap_authenticate_failure():
    # Since we don't have a real LDAP server, it should return None
    result = await ldap_authenticate("fakeuser", "fakepass")
    assert result is None
