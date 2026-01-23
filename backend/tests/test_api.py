import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_auth_sync(client: AsyncClient):
    # First sync - create user
    response = await client.post("/api/auth/sync", json={"user_id": "test_user"})
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "test_user"
    user_id_int = data["id"]

    # Second sync - get same user
    response = await client.post("/api/auth/sync", json={"user_id": "test_user"})
    assert response.status_code == 200
    assert response.json()["id"] == user_id_int


@pytest.mark.asyncio
async def test_workspace_lifecycle(client: AsyncClient):
    # Ensure user exists
    await client.post("/api/auth/sync", json={"user_id": "test_user"})

    # 1. Create workspace
    workspace_data = {
        "name": "Research Session",
        "state": {"panes": [{"id": "P1", "type": "chat"}], "visibleIds": ["P1"]},
    }
    response = await client.post(
        "/api/workspaces?user_id=test_user", json=workspace_data
    )
    assert response.status_code == 200
    ws = response.json()
    assert ws["name"] == "Research Session"
    ws_id = ws["id"]

    # 2. List workspaces
    response = await client.get("/api/workspaces?user_id=test_user")
    assert response.status_code == 200
    workspaces = response.json()
    assert len(workspaces) >= 1
    assert any(w["id"] == ws_id for w in workspaces)

    # 3. Update workspace
    update_data = {"name": "Updated Session"}
    response = await client.put(f"/api/workspaces/{ws_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Session"

    # 4. Soft delete (Archive)
    response = await client.delete(f"/api/workspaces/{ws_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "archived"

    # 5. Verify it's gone from list
    response = await client.get("/api/workspaces?user_id=test_user")
    assert response.status_code == 200
    workspaces = response.json()
    assert not any(w["id"] == ws_id for w in workspaces)
