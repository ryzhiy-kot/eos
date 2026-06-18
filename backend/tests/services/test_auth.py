import pytest
from jose import jwt
from fastapi import HTTPException
from unittest.mock import patch, MagicMock

from app.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    invalidate_token,
    hash_password,
    verify_password,
    ldap_authenticate,
    token_blacklist,
    settings
)

pytestmark = pytest.mark.asyncio

async def test_password_hashing():
    password = "supersecretpassword123!"
    hashed = await hash_password(password)

    assert hashed != password
    assert hashed.startswith("$2b$")

    # Should verify correctly
    is_valid = await verify_password(password, hashed)
    assert is_valid is True

    # Should fail with wrong password
    is_valid = await verify_password("wrongpassword", hashed)
    assert is_valid is False

def test_token_creation_and_decoding():
    user_id = "test_user_id_123"
    role = "trader"

    # Test Access Token
    access_token = create_access_token(user_id, role)
    decoded_access = decode_token(access_token)

    assert decoded_access["sub"] == user_id
    assert decoded_access["role"] == role
    assert decoded_access["type"] == "access"
    assert "exp" in decoded_access

    # Test Refresh Token
    refresh_token = create_refresh_token(user_id)
    decoded_refresh = decode_token(refresh_token)

    assert decoded_refresh["sub"] == user_id
    assert decoded_refresh["type"] == "refresh"
    assert "role" not in decoded_refresh
    assert "exp" in decoded_refresh

def test_token_invalidation():
    user_id = "test_user_id_123"
    token = create_access_token(user_id, "trader")

    # Before invalidation, should decode successfully
    decode_token(token)

    # Invalidate token
    invalidate_token(token)
    assert token in token_blacklist

    # After invalidation, should raise HTTPException
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token has been revoked"

    # Cleanup blacklist for other tests
    token_blacklist.clear()

def test_invalid_token_decoding():
    with pytest.raises(HTTPException) as exc_info:
        decode_token("invalid.token.string")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token"

@patch('ldap3.Server')
@patch('ldap3.Connection')
async def test_ldap_authenticate_success(mock_connection_class, mock_server_class):
    # Setup mock connection
    mock_conn_instance = MagicMock()
    mock_connection_class.return_value = mock_conn_instance

    # Setup mock entry
    mock_entry = MagicMock()
    mock_entry.uid = "johndoe"
    mock_entry.mail = "johndoe@company.com"
    mock_entry.cn = "John Doe"

    mock_conn_instance.entries = [mock_entry]

    result = await ldap_authenticate("johndoe", "password123")

    assert result is not None
    assert result["username"] == "johndoe"
    assert result["email"] == "johndoe@company.com"
    assert result["display_name"] == "John Doe"

    mock_conn_instance.unbind.assert_called_once()

@patch('ldap3.Server')
@patch('ldap3.Connection')
async def test_ldap_authenticate_no_entries(mock_connection_class, mock_server_class):
    # Setup mock connection
    mock_conn_instance = MagicMock()
    mock_connection_class.return_value = mock_conn_instance

    # No entries found
    mock_conn_instance.entries = []

    result = await ldap_authenticate("johndoe", "wrongpassword")

    assert result is None
    mock_conn_instance.unbind.assert_called_once()

@patch('ldap3.Connection', side_effect=Exception("Connection failed"))
async def test_ldap_authenticate_exception(mock_connection_class):
    # If connection throws exception (e.g. invalid credentials for bind)
    result = await ldap_authenticate("johndoe", "wrongpassword")
    assert result is None
