# PROJECT: EoS
# AUTHOR: Kyrylo Yatsenko
# YEAR: 2026
# * COPYRIGHT NOTICE:
# © 2026 Kyrylo Yatsenko. All rights reserved.
#
# This work represents a proprietary methodology for Human-Machine Interaction (HMI).
# All source code, logic structures, and User Experience (UX) frameworks
# contained herein are the sole intellectual property of Kyrylo Yatsenko.
#
# ATTRIBUTION REQUIREMENT:
# Any use of this program, or any portion thereof (including code snippets and
# interaction patterns), may not be used, redistributed, or adapted
# without explicit, visible credit to Kyrylo Yatsenko as the original author.

import pytest
from httpx import AsyncClient

async def get_auth_headers(client: AsyncClient, username="test_user"):
    login_data = {"username": username, "password": "password"}
    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_auth_sync(client: AsyncClient):
    headers = await get_auth_headers(client, "test_user")

    # Sync is now GET /me or POST /sync with auth header
    response = await client.post("/api/v1/auth/sync", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "test_user"


@pytest.mark.asyncio
async def test_workspace_lifecycle(client: AsyncClient):
    headers = await get_auth_headers(client, "test_user")

    # 1. Create workspace
    workspace_data = {
        "name": "Research Session",
        "state": {"panes": [{"id": "P1", "type": "chat"}], "visibleIds": ["P1"]},
    }
    response = await client.post("/api/v1/workspaces/", json=workspace_data, headers=headers)
    assert response.status_code == 201
    ws = response.json()
    assert ws["name"] == "Research Session"
    ws_id = ws["id"]

    # 2. List workspaces
    response = await client.get("/api/v1/workspaces/", headers=headers)
    assert response.status_code == 200
    workspaces = response.json()
    assert len(workspaces) >= 1
    assert any(w["id"] == ws_id for w in workspaces)

    # 3. Update workspace
    update_data = {"name": "Updated Session"}
    response = await client.patch(f"/api/v1/workspaces/{ws_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Session"

    # 4. Soft delete (Archive)
    response = await client.delete(f"/api/v1/workspaces/{ws_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "archived"

    # 5. Verify it's gone from list
    response = await client.get("/api/v1/workspaces/", headers=headers)
    assert response.status_code == 200
    workspaces = response.json()
    assert not any(w["id"] == ws_id for w in workspaces)
