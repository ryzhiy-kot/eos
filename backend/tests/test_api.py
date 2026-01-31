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


@pytest.mark.asyncio
async def test_auth_sync(client: AsyncClient):
    # First sync - create user
    response = await client.post("/api/v1/auth/sync", json={"user_id": "test_user"})
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "test_user"
    user_id_int = data["id"]

    # Second sync - get same user
    response = await client.post("/api/v1/auth/sync", json={"user_id": "test_user"})
    assert response.status_code == 200
    assert response.json()["id"] == user_id_int


@pytest.mark.asyncio
async def test_workspace_lifecycle(authenticated_client: AsyncClient):
    # Ensure user exists is handled by authenticated_client fixture

    # 1. Create workspace
    workspace_data = {
        "name": "Research Session",
        "state": {"panes": [{"id": "P1", "type": "chat"}], "visibleIds": ["P1"]},
    }
    response = await authenticated_client.post("/api/v1/workspaces/", json=workspace_data)
    assert response.status_code == 201
    ws = response.json()
    assert ws["name"] == "Research Session"
    ws_id = ws["id"]

    # 2. List workspaces
    response = await authenticated_client.get("/api/v1/workspaces/")
    assert response.status_code == 200
    workspaces = response.json()
    assert len(workspaces) >= 1
    assert any(w["id"] == ws_id for w in workspaces)

    # 3. Update workspace
    update_data = {"name": "Updated Session"}
    response = await authenticated_client.patch(f"/api/v1/workspaces/{ws_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Session"

    # 4. Soft delete (Archive)
    response = await authenticated_client.delete(f"/api/v1/workspaces/{ws_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "archived"

    # 5. Verify it's gone from list
    response = await authenticated_client.get("/api/v1/workspaces/")
    assert response.status_code == 200
    workspaces = response.json()
    assert not any(w["id"] == ws_id for w in workspaces)
