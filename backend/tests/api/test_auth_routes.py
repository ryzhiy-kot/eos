import pytest
import httpx
from fastapi import FastAPI
from app.main import app
from app.config import get_settings

settings = get_settings()

from httpx import ASGITransport

@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver" + settings.API_PREFIX) as client:
        yield client

@pytest.mark.asyncio
async def test_login_success(async_client):
    # Test valid credentials for mock user
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
async def test_login_failure(async_client):
    # Test invalid credentials
    response = await async_client.post(
        "/auth/login",
        json={"username": "trader", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid credentials"

@pytest.mark.asyncio
async def test_get_me(async_client):
    # First login to get a token
    login_response = await async_client.post(
        "/auth/login",
        json={"username": "trader", "password": "trader123"}
    )
    token = login_response.json()["access_token"]

    # Use token to fetch /me
    response = await async_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "trader@company.com"
    assert data["role"] == "trader"

@pytest.mark.asyncio
async def test_get_me_unauthorized(async_client):
    # Test accessing without a valid token
    response = await async_client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalidtoken"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"

@pytest.mark.asyncio
async def test_refresh_token(async_client):
    # Login to get refresh token
    login_response = await async_client.post(
        "/auth/login",
        json={"username": "trader", "password": "trader123"}
    )
    refresh_token = login_response.json()["refresh_token"]

    # Call refresh endpoint with it
    refresh_response = await async_client.post(
        "/auth/refresh",
        params={"refresh_token": refresh_token}
    )
    assert refresh_response.status_code == 200
    data = refresh_response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    # Depending on timing, the new refresh token might be identical or different.
    # But we ensure it is a valid token structure.
    assert len(data["refresh_token"]) > 0

@pytest.mark.asyncio
async def test_logout(async_client):
    # Login to get token
    login_response = await async_client.post(
        "/auth/login",
        json={"username": "trader", "password": "trader123"}
    )
    token = login_response.json()["access_token"]

    # Call logout
    logout_response = await async_client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert logout_response.status_code == 200
    assert logout_response.json() == {"message": "Logged out successfully"}

    # Calling /me after logout should fail because token was invalidated
    me_response = await async_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 401
    assert me_response.json()["detail"] == "Token has been revoked"
