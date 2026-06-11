import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.api.routes.auth import TRADER_USER_ID

API_PREFIX = "/api"


@pytest.mark.asyncio
async def test_login_success():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=f"http://test{API_PREFIX}"
    ) as client:
        response = await client.post(
            "/auth/login", json={"username": "trader", "password": "trader123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_failure():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=f"http://test{API_PREFIX}"
    ) as client:
        response = await client.post(
            "/auth/login", json={"username": "trader", "password": "wrongpassword"}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_and_get_me():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=f"http://test{API_PREFIX}"
    ) as client:
        # First login
        login_response = await client.post(
            "/auth/login", json={"username": "trader", "password": "trader123"}
        )
        assert login_response.status_code == 200
        tokens = login_response.json()

        # Test Refresh Token
        refresh_response = await client.post(
            "/auth/refresh", params={"refresh_token": tokens["refresh_token"]}
        )
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        assert "access_token" in new_tokens

        # Test get me
        me_response = await client.get(
            "/auth/me", headers={"Authorization": f"Bearer {new_tokens['access_token']}"}
        )
        assert me_response.status_code == 200
        user_data = me_response.json()
        assert user_data["id"] == TRADER_USER_ID
        assert user_data["role"] == "trader"


@pytest.mark.asyncio
async def test_logout():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=f"http://test{API_PREFIX}"
    ) as client:
        # First login
        login_response = await client.post(
            "/auth/login", json={"username": "trader", "password": "trader123"}
        )
        assert login_response.status_code == 200
        tokens = login_response.json()

        # Test Logout
        logout_response = await client.post(
            "/auth/logout", headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert logout_response.status_code == 200

        # Try getting me with invalidated token
        me_response = await client.get(
            "/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert me_response.status_code == 401
