import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.api.routes.auth import TRADER_USER_ID

@pytest.mark.asyncio
async def test_login_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/auth/login",
            json={"username": "trader", "password": "trader123"},
        )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_failure():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/auth/login",
            json={"username": "trader", "password": "wrong_password"},
        )
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}

@pytest.mark.asyncio
async def test_get_me():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # First login to get the token
        login_response = await ac.post(
            "/api/auth/login",
            json={"username": "trader", "password": "trader123"},
        )
        token = login_response.json()["access_token"]

        # Then get me
        response = await ac.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == TRADER_USER_ID
    assert data["role"] == "trader"

@pytest.mark.asyncio
async def test_logout():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # First login to get the token
        login_response = await ac.post(
            "/api/auth/login",
            json={"username": "trader", "password": "trader123"},
        )
        token = login_response.json()["access_token"]

        # Then logout
        response = await ac.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json() == {"message": "Logged out successfully"}

        # Trying to use the token again should fail
        me_response = await ac.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 401
        assert me_response.json() == {"detail": "Token has been revoked"}
