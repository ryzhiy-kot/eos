import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.api.routes.auth import MOCK_USERS

@pytest.mark.asyncio
async def test_login_success():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/auth/login", json={"username": "trader", "password": "trader123"})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

@pytest.mark.asyncio
async def test_login_invalid_credentials():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/auth/login", json={"username": "trader", "password": "wrongpassword"})
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_refresh_token_success():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First login to get a refresh token
        login_res = await client.post("/api/auth/login", json={"username": "trader", "password": "trader123"})
        assert login_res.status_code == 200
        refresh_token = login_res.json()["refresh_token"]

        # Now refresh
        import asyncio
        await asyncio.sleep(1) # Ensure exp changes because time moves
        refresh_res = await client.post("/api/auth/refresh", params={"refresh_token": refresh_token})
        assert refresh_res.status_code == 200
        data = refresh_res.json()
        assert "access_token" in data
        assert "refresh_token" in data

@pytest.mark.asyncio
async def test_refresh_token_invalid():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        refresh_res = await client.post("/api/auth/refresh", params={"refresh_token": "invalid.token.here"})
        assert refresh_res.status_code == 401

@pytest.mark.asyncio
async def test_get_me_success():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Login
        login_res = await client.post("/api/auth/login", json={"username": "trader", "password": "trader123"})
        access_token = login_res.json()["access_token"]

        # Get Me
        me_res = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert me_res.status_code == 200
        data = me_res.json()
        assert data["email"] == "trader@company.com"
        assert data["role"] == "trader"
        assert data["is_active"] is True

@pytest.mark.asyncio
async def test_logout_success():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Login
        login_res = await client.post("/api/auth/login", json={"username": "trader", "password": "trader123"})
        access_token = login_res.json()["access_token"]

        # Logout
        logout_res = await client.post("/api/auth/logout", headers={"Authorization": f"Bearer {access_token}"})
        assert logout_res.status_code == 200
        assert logout_res.json()["message"] == "Logged out successfully"

        # Ensure token is invalidated by trying to hit /me
        me_res = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert me_res.status_code == 401
