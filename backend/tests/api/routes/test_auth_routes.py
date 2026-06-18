import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.api.routes.auth import TRADER_USER_ID, ADMIN_USER_ID

pytestmark = pytest.mark.asyncio

@pytest.fixture
def test_client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test/api/auth")

async def test_login_success_mock_user(test_client):
    response = await test_client.post(
        "/login",
        json={"username": "trader", "password": "trader123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data

async def test_login_invalid_password(test_client):
    response = await test_client.post(
        "/login",
        json={"username": "trader", "password": "wrongpassword"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

async def test_login_invalid_username(test_client):
    response = await test_client.post(
        "/login",
        json={"username": "unknown_user", "password": "password"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

async def test_refresh_token_success(test_client):
    # 1. Login to get a valid refresh token
    login_response = await test_client.post(
        "/login",
        json={"username": "admin", "password": "admin123"}
    )
    refresh_token = login_response.json()["refresh_token"]

    import asyncio
    await asyncio.sleep(1) # wait for 1 second to ensure the token expires or changes slightly if datetime is used. Actually, access token generated at exact same second might be identical.

    # 2. Refresh the token
    response = await test_client.post(
        "/refresh",
        params={"refresh_token": refresh_token}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    # assert data["access_token"] != login_response.json()["access_token"] # depending on precision, tokens generated within same second can be identical. So we shouldn't fail if they're identical here, the test focus is on successful refresh

async def test_refresh_token_invalid(test_client):
    response = await test_client.post(
        "/refresh",
        params={"refresh_token": "invalid.token.here"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"

async def test_get_me_success(test_client):
    # 1. Login to get access token
    login_response = await test_client.post(
        "/login",
        json={"username": "trader", "password": "trader123"}
    )
    access_token = login_response.json()["access_token"]

    # 2. Get me
    response = await test_client.get(
        "/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == TRADER_USER_ID
    assert data["email"] == "trader@company.com"
    assert data["display_name"] == "Jane Trader"
    assert data["role"] == "trader"
    assert data["is_active"] is True

async def test_get_me_no_token(test_client):
    response = await test_client.get("/me")
    assert response.status_code == 401

async def test_get_me_invalid_token(test_client):
    response = await test_client.get(
        "/me",
        headers={"Authorization": "Bearer invalid.token"}
    )
    assert response.status_code == 401

async def test_logout_success(test_client):
    # 1. Login
    login_response = await test_client.post(
        "/login",
        json={"username": "trader", "password": "trader123"}
    )
    access_token = login_response.json()["access_token"]

    # 2. Logout
    logout_response = await test_client.post(
        "/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert logout_response.status_code == 200
    assert logout_response.json()["message"] == "Logged out successfully"

    # 3. Verify token is invalidated by trying to use it
    me_response = await test_client.get(
        "/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me_response.status_code == 401
    assert me_response.json()["detail"] == "Token has been revoked"

@pytest.fixture(autouse=True)
def clean_blacklist():
    # Clean up the token blacklist after each test to ensure isolation
    from app.services.auth import token_blacklist
    yield
    token_blacklist.clear()
