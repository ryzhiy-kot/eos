import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.api.routes.auth import TRADER_USER_ID, ADMIN_USER_ID

# Using the httpx.AsyncClient pattern

@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    response = await async_client.post(
        "/api/auth/login",
        json={"username": "trader", "password": "trader123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "expires_in" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(async_client: AsyncClient):
    response = await async_client.post(
        "/api/auth/login",
        json={"username": "trader", "password": "wrongpassword"}
    )

    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_invalid_user(async_client: AsyncClient):
    response = await async_client.post(
        "/api/auth/login",
        json={"username": "nonexistent", "password": "password"}
    )

    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


@pytest.mark.asyncio
async def test_refresh_token(async_client: AsyncClient):
    # 1. First, login to get a refresh token
    login_response = await async_client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert login_response.status_code == 200
    refresh_token = login_response.json()["refresh_token"]

    # 2. Use refresh token to get new tokens
    refresh_response = await async_client.post(
        "/api/auth/refresh",
        params={"refresh_token": refresh_token}
    )

    assert refresh_response.status_code == 200
    data = refresh_response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "expires_in" in data


@pytest.mark.asyncio
async def test_get_me(async_client: AsyncClient):
    # 1. Login to get access token
    login_response = await async_client.post(
        "/api/auth/login",
        json={"username": "trader", "password": "trader123"}
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    # 2. Call /me with token
    me_response = await async_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert me_response.status_code == 200
    data = me_response.json()
    assert data["id"] == TRADER_USER_ID
    assert data["email"] == "trader@company.com"
    assert data["display_name"] == "Jane Trader"
    assert data["role"] == "trader"


@pytest.mark.asyncio
async def test_get_me_unauthorized(async_client: AsyncClient):
    # Call /me without token
    me_response = await async_client.get("/api/auth/me")
    assert me_response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_logout(async_client: AsyncClient):
    # 1. Login to get token
    login_response = await async_client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    # 2. Call logout with token
    logout_response = await async_client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert logout_response.status_code == 200
    assert logout_response.json()["message"] == "Logged out successfully"

    # 3. Try to use invalidated token to get /me
    me_response = await async_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert me_response.status_code == 401
    assert "revoked" in me_response.json()["detail"].lower()
