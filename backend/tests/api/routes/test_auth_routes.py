import pytest
import httpx
from fastapi import FastAPI
from asgi_lifespan import LifespanManager

from app.main import app
from app.config import get_settings

settings = get_settings()

@pytest.fixture(scope="module")
def api_prefix():
    return settings.API_PREFIX

@pytest.fixture
async def client():
    async with LifespanManager(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield client

@pytest.mark.asyncio
async def test_login_success_mock_trader(client, api_prefix):
    response = await client.post(
        f"{api_prefix}/auth/login",
        json={"username": "trader", "password": "trader123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data

@pytest.mark.asyncio
async def test_login_invalid_credentials(client, api_prefix):
    response = await client.post(
        f"{api_prefix}/auth/login",
        json={"username": "trader", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

@pytest.mark.asyncio
async def test_get_me(client, api_prefix):
    # First, login to get an access token
    login_response = await client.post(
        f"{api_prefix}/auth/login",
        json={"username": "trader", "password": "trader123"}
    )
    access_token = login_response.json()["access_token"]

    # Request the current user's profile
    response = await client.get(
        f"{api_prefix}/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "trader@company.com"
    assert data["role"] == "trader"
    assert data["display_name"] == "Jane Trader"

@pytest.mark.asyncio
async def test_get_me_invalid_token(client, api_prefix):
    response = await client.get(
        f"{api_prefix}/auth/me",
        headers={"Authorization": "Bearer invalid.token.string"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"

@pytest.mark.asyncio
async def test_refresh_token(client, api_prefix):
    # Login to get a refresh token
    login_response = await client.post(
        f"{api_prefix}/auth/login",
        json={"username": "trader", "password": "trader123"}
    )
    refresh_token = login_response.json()["refresh_token"]

    # Refresh the token
    refresh_response = await client.post(
        f"{api_prefix}/auth/refresh?refresh_token={refresh_token}"
    )
    assert refresh_response.status_code == 200
    data = refresh_response.json()
    assert "access_token" in data
    assert "refresh_token" in data

@pytest.mark.asyncio
async def test_logout(client, api_prefix):
    # Login to get an access token
    login_response = await client.post(
        f"{api_prefix}/auth/login",
        json={"username": "trader", "password": "trader123"}
    )
    access_token = login_response.json()["access_token"]

    # Logout
    logout_response = await client.post(
        f"{api_prefix}/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert logout_response.status_code == 200
    assert logout_response.json() == {"message": "Logged out successfully"}

    # Verify that the access token has been invalidated
    get_me_response = await client.get(
        f"{api_prefix}/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert get_me_response.status_code == 401
    assert get_me_response.json()["detail"] == "Token has been revoked"
