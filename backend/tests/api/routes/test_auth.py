import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_login_success(async_client):
    response = await async_client.post(
        "/api/auth/login",
        json={"username": "trader", "password": "trader123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_credentials(async_client):
    response = await async_client.post(
        "/api/auth/login",
        json={"username": "trader", "password": "wrongpassword"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_login_invalid_user(async_client):
    response = await async_client.post(
        "/api/auth/login",
        json={"username": "nonexistent", "password": "password"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_me(async_client):
    # First login to get a token
    login_response = await async_client.post(
        "/api/auth/login",
        json={"username": "trader", "password": "trader123"}
    )
    token = login_response.json()["access_token"]

    # Use token to get user info
    response = await async_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "trader@company.com"
    assert data["role"] == "trader"

@pytest.mark.asyncio
async def test_refresh_token(async_client):
    # First login to get a refresh token
    login_response = await async_client.post(
        "/api/auth/login",
        json={"username": "trader", "password": "trader123"}
    )
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
async def test_logout(async_client):
    # First login to get a token
    login_response = await async_client.post(
        "/api/auth/login",
        json={"username": "trader", "password": "trader123"}
    )
    token = login_response.json()["access_token"]

    # Logout
    response = await async_client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Logged out successfully"}

    # Verify token is invalidated
    me_response = await async_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 401
