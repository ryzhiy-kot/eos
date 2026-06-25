import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.api.routes.auth import TRADER_USER_ID, ADMIN_USER_ID


@pytest.fixture
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test/api"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_login_success_mock_user(async_client):
    response = await async_client.post(
        "/auth/login",
        json={"username": "trader", "password": "trader123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_failure_wrong_password(async_client):
    response = await async_client.post(
        "/auth/login",
        json={"username": "trader", "password": "wrong_password"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


@pytest.mark.asyncio
async def test_login_failure_unknown_user(async_client):
    response = await async_client.post(
        "/auth/login",
        json={"username": "unknown", "password": "password"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


@pytest.mark.asyncio
async def test_refresh_token(async_client):
    # First login to get a refresh token
    login_res = await async_client.post(
        "/auth/login",
        json={"username": "trader", "password": "trader123"}
    )
    assert login_res.status_code == 200
    refresh_token = login_res.json()["refresh_token"]

    # Use refresh token to get new tokens
    refresh_res = await async_client.post(
        "/auth/refresh",
        params={"refresh_token": refresh_token}
    )
    assert refresh_res.status_code == 200
    data = refresh_res.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_get_me(async_client):
    # Login to get access token
    login_res = await async_client.post(
        "/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert login_res.status_code == 200
    access_token = login_res.json()["access_token"]

    # Fetch profile
    me_res = await async_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me_res.status_code == 200
    data = me_res.json()
    assert data["id"] == ADMIN_USER_ID
    assert data["email"] == "admin@company.com"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_logout(async_client):
    # Login to get access token
    login_res = await async_client.post(
        "/auth/login",
        json={"username": "trader", "password": "trader123"}
    )
    assert login_res.status_code == 200
    access_token = login_res.json()["access_token"]

    # Logout
    logout_res = await async_client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert logout_res.status_code == 200
    assert logout_res.json() == {"message": "Logged out successfully"}

    # Try to use access token again (should fail)
    me_res = await async_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me_res.status_code == 401
    assert me_res.json() == {"detail": "Token has been revoked"}
