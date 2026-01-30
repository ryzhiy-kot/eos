import pytest
from httpx import AsyncClient
from app.services.auth.local import SESSIONS

@pytest.mark.asyncio
async def test_auth_flow(client: AsyncClient):
    # 1. Login
    username = "integration_test_user"

    response = await client.post("/api/v1/auth/login", json={"username": username, "password": "any"})
    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == username
    assert "session_token" in data
    assert "session_expires_at" in data
    # active_workspace_id should be present in LoggedInUser (which inherits User)
    assert "active_workspace_id" in data

    token = data["session_token"]
    assert token

    # Verify session stored in memory
    assert token in SESSIONS

    # 2. Logout
    response = await client.post("/api/v1/auth/logout", json={"session_token": token})
    assert response.status_code == 200

    # Verify session removed
    assert token not in SESSIONS
