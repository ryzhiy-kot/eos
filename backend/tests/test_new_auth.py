import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_oauth2_login_and_protected_access(client: AsyncClient):
    # 1. Login with form data
    # LocalAuthService creates user if not exists
    login_data = {"username": "testuser", "password": "password"}
    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200, response.text
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    token = token_data["access_token"]

    # 2. Access protected endpoint /me
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["user_id"] == "testuser"

    # 3. Access protected workspace endpoint
    response = await client.get("/api/v1/workspaces/", headers=headers)
    assert response.status_code == 200

    # 4. Fail without token
    response = await client.get("/api/v1/workspaces/")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_admin_login(client: AsyncClient):
    login_data = {"username": "admin", "password": "password"}
    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]

    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["user_id"] == "admin"
