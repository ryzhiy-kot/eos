import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_list_workspaces():
    """Test listing workspaces."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/workspaces/")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_workspace_schema():
    """Test workspace schema fields."""
    from app.schemas import WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse
    
    ws_create = WorkspaceCreate(name="Test")
    assert ws_create.name == "Test"
    
    ws_update = WorkspaceUpdate(name="Updated", artifact_positions={"a1": {"x": 1, "y": 2, "width": 100, "height": 100, "visible": True}})
    assert ws_update.name == "Updated"
    assert ws_update.artifact_positions == {"a1": {"x": 1, "y": 2, "width": 100, "height": 100, "visible": True}}