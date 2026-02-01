import pytest
from app.services.user_service import UserService
from app.models.workspace import Workspace
from app.models.artifact import Artifact
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

    # In unified model, pane.artifactId points to the Chat Artifact (Session)
    session_id = pane["artifactId"]

    # Check that artifact info is in state
    assert session_id in workspace.state["artifacts"]
    artifact_data = workspace.state["artifacts"][session_id]

    # Verify DB entity
    session_artifact = await db_session.get(Artifact, session_id)
    assert session_artifact is not None
    assert session_artifact.type == "chat"
    assert session_artifact.workspace_id == workspace_id
    assert session_artifact.payload == []

    # Check artifact payload in state (should be empty list)
    assert artifact_data["payload"] == []

    # Check focusedPaneId
    assert workspace.state["focusedPaneId"] == pane_id
