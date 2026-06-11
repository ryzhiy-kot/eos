import pytest
from jose import jwt

from app.config import get_settings
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
    invalidate_token,
    ldap_authenticate,
    token_blacklist,
)

settings = get_settings()


@pytest.mark.asyncio
async def test_create_and_decode_access_token():
    user_id = "test_user_1"
    role = "trader"
    token = create_access_token(user_id, role)

    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["role"] == role
    assert payload["type"] == "access"
    assert "exp" in payload


@pytest.mark.asyncio
async def test_create_and_decode_refresh_token():
    user_id = "test_user_2"
    token = create_refresh_token(user_id)

    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"
    assert "exp" in payload


@pytest.mark.asyncio
async def test_invalidate_token():
    user_id = "test_user_3"
    token = create_access_token(user_id, "trader")

    # Invalidate
    invalidate_token(token)

    # Check that it's in blacklist
    assert token in token_blacklist

    # Try decoding
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        decode_token(token)

    assert exc.value.status_code == 401
    assert "revoked" in exc.value.detail


@pytest.mark.asyncio
async def test_password_hashing():
    password = "supersecretpassword123!"
    hashed = await hash_password(password)

    assert hashed != password
    assert await verify_password(password, hashed) is True
    assert await verify_password("wrongpassword", hashed) is False


@pytest.mark.asyncio
async def test_ldap_authenticate_failure():
    # Since we don't have a real LDAP server running in test,
    # it should handle the connection failure gracefully and return None
    result = await ldap_authenticate("testuser", "testpass")
    assert result is None
