import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_login_success_mock_user(async_client):
    response = await async_client.post(
        "/api/auth/login",
        json={"username": "trader", "password": "trader123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data

@pytest.mark.asyncio
async def test_login_invalid_credentials(async_client):
    response = await async_client.post(
        "/api/auth/login",
        json={"username": "trader", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

@pytest.mark.asyncio
async def test_refresh_token_success(async_client):
    # First login to get a refresh token
    login_resp = await async_client.post(
        "/api/auth/login",
        json={"username": "trader", "password": "trader123"}
    )
    refresh_token = login_resp.json()["refresh_token"]

    response = await async_client.post(
        "/api/auth/refresh",
        params={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

@pytest.mark.asyncio
async def test_refresh_token_invalid(async_client):
    response = await async_client.post(
        "/api/auth/refresh",
        params={"refresh_token": "invalid.refresh.token"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_me_success(async_client):
    login_resp = await async_client.post(
        "/api/auth/login",
        json={"username": "trader", "password": "trader123"}
    )
    access_token = login_resp.json()["access_token"]

    response = await async_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "trader@company.com"
    assert data["role"] == "trader"

@pytest.mark.asyncio
async def test_get_me_unauthorized(async_client):
    response = await async_client.get("/api/auth/me")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_logout_success(async_client):
    login_resp = await async_client.post(
        "/api/auth/login",
        json={"username": "trader", "password": "trader123"}
    )
    access_token = login_resp.json()["access_token"]

    response = await async_client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"

    # Verify the token is actually invalid now
    me_resp = await async_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me_resp.status_code == 401
