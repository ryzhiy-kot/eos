import pytest
from httpx import AsyncClient
from app.core import security

@pytest.mark.asyncio
async def test_auth_flow(client: AsyncClient):
    # 1. Login
    username = "integration_test_user"

    # Changed to Form Data for OAuth2
    response = await client.post("/api/v1/auth/login", data={"username": username, "password": "any"})
    assert response.status_code == 200
    data = response.json()

    assert data["token_type"] == "bearer"
    assert "access_token" in data

    user_data = data["user"]
    assert user_data["user_id"] == username
    assert "active_workspace_id" in user_data

    token = data["access_token"]
    assert token

    # Verify token is valid JWT
    payload = security.verify_token(token)
    assert payload["sub"] == username

    # 2. Access Protected Endpoint
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/workspaces/", headers=headers)
    assert response.status_code == 200

    # 3. Logout (No-op for JWT but endpoint should exist)
    response = await client.post("/api/v1/auth/logout", json={"session_token": token}, headers=headers)
    assert response.status_code == 200

    # 4. Verify access with invalid token
    invalid_headers = {"Authorization": "Bearer invalid_token"}
    response = await client.get("/api/v1/workspaces/", headers=invalid_headers)
    assert response.status_code == 401
