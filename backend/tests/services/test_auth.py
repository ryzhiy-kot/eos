import pytest
from jose import jwt

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
from app.config import get_settings


@pytest.fixture(autouse=True)
def clear_blacklist():
    token_blacklist.clear()
    yield
    token_blacklist.clear()


@pytest.mark.asyncio
async def test_hash_and_verify_password():
    password = "supersecretpassword"
    hashed = await hash_password(password)

    assert hashed != password

    is_valid = await verify_password(password, hashed)
    assert is_valid is True

    is_invalid = await verify_password("wrongpassword", hashed)
    assert is_invalid is False


def test_create_and_decode_access_token():
    settings = get_settings()
    user_id = "test_user_id"
    role = "admin"

    token = create_access_token(user_id, role)
    assert isinstance(token, str)

    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["role"] == role
    assert payload["type"] == "access"
    assert "exp" in payload


def test_create_and_decode_refresh_token():
    user_id = "test_user_id"

    token = create_refresh_token(user_id)
    assert isinstance(token, str)

    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"
    assert "role" not in payload
    assert "exp" in payload


def test_invalidate_token():
    user_id = "test_user_id"
    role = "admin"

    token = create_access_token(user_id, role)

    # Verify works before invalidation
    payload = decode_token(token)
    assert payload["sub"] == user_id

    # Invalidate
    invalidate_token(token)

    # Should raise error now
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token)

    assert exc_info.value.status_code == 401
    assert "revoked" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_ldap_authenticate_failure():
    # Because there's no real LDAP server running in the test environment,
    # it should fail and return None without raising an unhandled exception.
    result = await ldap_authenticate("testuser", "testpass")
    assert result is None
