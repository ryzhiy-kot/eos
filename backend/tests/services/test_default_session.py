import pytest
from app.services.user_service import UserService
from app.models.workspace import Workspace
from app.models.chat import ChatSession
from app.models.user import User

@pytest.mark.asyncio
async def test_ensure_personal_workspace_creates_session(db_session):
    # Create a dummy user
    user_id = "test_user_personal_ws"
    user = await UserService.create_user(db_session, user_id)
    await db_session.commit()
    await db_session.refresh(user)

    # Trigger ensure_personal_workspace
    updated_user = await UserService.ensure_personal_workspace(db_session, user)

    # Verify workspace created
    assert updated_user.active_workspace_id is not None
    workspace_id = updated_user.active_workspace_id

    workspace = await db_session.get(Workspace, workspace_id)
    assert workspace is not None
    assert workspace.name == f"{user_id}'s Workspace"

    # Check session created in workspace state
    panes = workspace.state["panes"]
    assert len(panes) == 1
    pane_id = list(panes.keys())[0]

    # Check session entity
    pane = panes[pane_id]
    session_id = pane["id"] # The pane ID is used as key, but let's check artifact/session linkage
    # Actually in our logic, pane_id="P1", but session_id is a UUID stored in artifact

    artifact_id = pane["artifactId"]
    artifact_data = workspace.state["artifacts"][artifact_id]
    db_session_id = artifact_data["session_id"]

    session = await db_session.get(ChatSession, db_session_id)
    assert session is not None
    assert session.workspace_id == workspace_id

    # Check artifact payload (should be empty messages)
    assert artifact_data["payload"]["messages"] == []

    # Check focusedPaneId
    assert workspace.state["focusedPaneId"] == pane_id
