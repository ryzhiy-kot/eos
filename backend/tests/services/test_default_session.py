import pytest
from sqlalchemy import select
from app.services.user_service import UserService
from app.models.workspace import Workspace
from app.models.chat import ChatSession


@pytest.mark.asyncio
async def test_initialize_defaults_creates_session(db_session):
    # Ensure clean slate for default objects if possible,
    # but db_session fixture usually rolls back.
    # However, initialize_defaults might have run or might check existence.

    # Let's delete default workspace if exists to force creation logic
    ws = await db_session.get(Workspace, "default_workspace")
    if ws:
        await db_session.delete(ws)
        await db_session.commit()

    # Run initialization
    await UserService.initialize_defaults(db_session)

    # Check default workspace state
    ws = await db_session.get(Workspace, "default_workspace")
    assert ws is not None
    assert "default_session" in ws.state["panes"]
    assert "default_session" in ws.state["activeLayout"]

    # Check session entity
    session = await db_session.get(ChatSession, "default_session")
    assert session is not None
    assert session.name == "General"
    assert session.workspace_id == "default_workspace"

    # Verify artifacts are present in state
    assert "artifacts" in ws.state
    panes = ws.state["panes"]
    default_pane = panes["default_session"]

    assert "artifactId" in default_pane
    assert "title" in default_pane

    artifact_id = default_pane["artifactId"]
    assert artifact_id in ws.state["artifacts"]
    assert ws.state["artifacts"][artifact_id]["type"] == "chat"
