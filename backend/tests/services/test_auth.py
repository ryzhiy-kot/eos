import pytest
from unittest.mock import patch, MagicMock

from app.services.auth import (
    hash_password,
    verify_password,
    hash_password_sync,
    verify_password_sync,
    ldap_authenticate,
    create_access_token,
    create_refresh_token,
    decode_token,
    invalidate_token,
    token_blacklist,
)
from jose import jwt, JWTError

@pytest.mark.asyncio
async def test_hash_and_verify_password():
    password = "test_password_123"

    hashed = await hash_password(password)
    assert hashed != password
    assert isinstance(hashed, str)

    is_valid = await verify_password(password, hashed)
    assert is_valid is True

    is_invalid = await verify_password("wrong_password", hashed)
    assert is_invalid is False

def test_hash_and_verify_password_sync():
    password = "test_password_123"

    hashed = hash_password_sync(password)
    assert hashed != password
    assert isinstance(hashed, str)

    is_valid = verify_password_sync(password, hashed)
    assert is_valid is True

@pytest.mark.asyncio
async def test_ldap_authenticate_success():
    with patch("ldap3.Server"), \
         patch("ldap3.Connection") as mock_conn:

        mock_entry = MagicMock(uid="jdoe", mail="jdoe@example.com", cn="John Doe")

        mock_instance = mock_conn.return_value
        mock_instance.entries = [mock_entry]

        result = await ldap_authenticate("jdoe", "password123")

        assert result is not None
        assert result["username"] == "jdoe"
        assert result["email"] == "jdoe@example.com"
        assert result["display_name"] == "John Doe"

@pytest.mark.asyncio
async def test_ldap_authenticate_failure():
    with patch("ldap3.Server"), \
         patch("ldap3.Connection") as mock_conn:

        mock_instance = mock_conn.return_value
        mock_instance.entries = []

        result = await ldap_authenticate("jdoe", "wrong_password")

        assert result is None

@pytest.mark.asyncio
async def test_jwt_tokens():
    user_id = "test_user_id"
    role = "trader"

    access_token = create_access_token(user_id, role)
    refresh_token = create_refresh_token(user_id)

    assert isinstance(access_token, str)
    assert isinstance(refresh_token, str)

    decoded_access = decode_token(access_token)
    assert decoded_access["sub"] == user_id
    assert decoded_access["role"] == role
    assert decoded_access["type"] == "access"

    decoded_refresh = decode_token(refresh_token)
    assert decoded_refresh["sub"] == user_id
    assert decoded_refresh["type"] == "refresh"

@pytest.mark.asyncio
async def test_invalidate_token():
    token_blacklist.clear()

    user_id = "test_user_id"
    role = "trader"
    token = create_access_token(user_id, role)

    decode_token(token)  # Should not raise

    await invalidate_token(token)

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token has been revoked"
