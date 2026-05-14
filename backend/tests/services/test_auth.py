import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.api.routes.auth import TRADER_USER_ID


@pytest.fixture
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_login_success_mock(async_client: AsyncClient):
    response = await async_client.post(
        "/api/auth/login",
        json={"username": "trader", "password": "trader123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_failure_mock(async_client: AsyncClient):
    response = await async_client.post(
        "/api/auth/login",
        json={"username": "trader", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_refresh_token(async_client: AsyncClient):
    # First login to get a refresh token
    login_response = await async_client.post(
        "/api/auth/login",
        json={"username": "trader", "password": "trader123"},
    )
    assert login_response.status_code == 200
    refresh_token = login_response.json()["refresh_token"]

    # Use refresh token to get a new token pair
    response = await async_client.post(
        f"/api/auth/refresh?refresh_token={refresh_token}"
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_get_me(async_client: AsyncClient):
    # First login to get an access token
    login_response = await async_client.post(
        "/api/auth/login",
        json={"username": "trader", "password": "trader123"},
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    # Get user profile
    response = await async_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == TRADER_USER_ID
    assert data["role"] == "trader"


@pytest.mark.asyncio
async def test_logout(async_client: AsyncClient):
    # First login
    login_response = await async_client.post(
        "/api/auth/login",
        json={"username": "trader", "password": "trader123"},
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    # Logout
    logout_response = await async_client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_response.status_code == 200
    assert logout_response.json()["message"] == "Logged out successfully"

    # Verify token is invalidated
    me_response = await async_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_response.status_code == 401
    assert me_response.json()["detail"] == "Token has been revoked"
