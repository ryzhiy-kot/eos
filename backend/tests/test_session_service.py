import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.services.session_service import Base, Session, Artifact, SessionService, Workspace


@pytest_asyncio.fixture
async def test_engine():
    """Create a test engine with in-memory SQLite."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(test_engine):
    """Create a session factory for tests."""
    return async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def session_service(session_factory):
    """Create a SessionService instance for tests."""
    return SessionService(session_factory=session_factory)


@pytest_asyncio.fixture
async def test_session(session_service):
    """Create a test session."""
    return await session_service.create_session(user_id="test_user", name="Test Session")


@pytest.mark.asyncio
async def test_create_session(session_service):
    """Test creating a new session."""
    session = await session_service.create_session(user_id="user123", name="My Session")
    assert session.id is not None
    assert session.user_id == "user123"
    assert session.name == "My Session"
    assert session.created_at is not None


@pytest.mark.asyncio
async def test_create_session_with_auto_name(session_service):
    """Test creating a session with auto-generated name."""
    session = await session_service.create_session(user_id="user123")
    assert session.id is not None
    assert session.user_id == "user123"
    assert session.name.startswith("Session - ")


@pytest.mark.asyncio
async def test_get_session(session_service, test_session):
    """Test retrieving a session by ID."""
    retrieved = await session_service.get_session(test_session.id)
    assert retrieved is not None
    assert retrieved.id == test_session.id
    assert retrieved.name == test_session.name


@pytest.mark.asyncio
async def test_get_nonexistent_session(session_service):
    """Test retrieving a session that doesn't exist."""
    retrieved = await session_service.get_session("nonexistent-id")
    assert retrieved is None


@pytest.mark.asyncio
async def test_list_sessions(session_service):
    """Test listing all sessions for a user."""
    await session_service.create_session(user_id="user1", name="Session 1")
    await session_service.create_session(user_id="user1", name="Session 2")
    await session_service.create_session(user_id="user2", name="Other User Session")

    user1_sessions = await session_service.list_sessions("user1")
    assert len(user1_sessions) == 2
    assert all(s.user_id == "user1" for s in user1_sessions)

    user2_sessions = await session_service.list_sessions("user2")
    assert len(user2_sessions) == 1


@pytest.mark.asyncio
async def test_update_session(session_service, test_session):
    """Test updating a session's name."""
    updated = await session_service.update_session(test_session.id, "Updated Name")
    assert updated is not None
    assert updated.name == "Updated Name"


@pytest.mark.asyncio
async def test_update_nonexistent_session(session_service):
    """Test updating a session that doesn't exist."""
    updated = await session_service.update_session("nonexistent", "New Name")
    assert updated is None


@pytest.mark.asyncio
async def test_delete_session(session_service, test_session):
    """Test deleting a session."""
    result = await session_service.delete_session(test_session.id)
    assert result is True

    deleted = await session_service.get_session(test_session.id)
    assert deleted is None


@pytest.mark.asyncio
async def test_delete_nonexistent_session(session_service):
    """Test deleting a session that doesn't exist."""
    result = await session_service.delete_session("nonexistent")
    assert result is False


@pytest.mark.asyncio
async def test_save_artifact(session_service, test_session):
    """Test saving an artifact."""
    artifact = await session_service.save_artifact(
        session_id=test_session.id,
        artifact_type="chart",
        title="Test Chart",
        spec={"type": "bar"},
        data={"values": [1, 2, 3]},
    )
    assert artifact is not None
    assert artifact.id is not None
    assert artifact.session_id == test_session.id
    assert artifact.type == "chart"
    assert artifact.title == "Test Chart"


@pytest.mark.asyncio
async def test_save_artifact_invalid_session(session_service):
    """Test saving an artifact to a non-existent session."""
    artifact = await session_service.save_artifact(
        session_id="nonexistent-session",
        artifact_type="chart",
        title="Test",
    )
    assert artifact is None


@pytest.mark.asyncio
async def test_get_artifacts(session_service, test_session):
    """Test retrieving artifacts for a session."""
    await session_service.save_artifact(
        session_id=test_session.id, artifact_type="chart", title="Chart 1"
    )
    await session_service.save_artifact(
        session_id=test_session.id, artifact_type="table", title="Table 1"
    )
    await session_service.save_artifact(
        session_id=test_session.id, artifact_type="text", title="Text 1"
    )

    artifacts = await session_service.get_artifacts(test_session.id)
    assert len(artifacts) == 3
    assert all(a.session_id == test_session.id for a in artifacts)


@pytest.mark.asyncio
async def test_get_artifact(session_service, test_session):
    """Test retrieving a specific artifact."""
    created = await session_service.save_artifact(
        session_id=test_session.id,
        artifact_type="chart",
        title="Specific Chart",
    )
    assert created is not None

    retrieved = await session_service.get_artifact(created.id)
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.title == "Specific Chart"


@pytest.mark.asyncio
async def test_get_nonexistent_artifact(session_service):
    """Test retrieving an artifact that doesn't exist."""
    retrieved = await session_service.get_artifact("nonexistent-id")
    assert retrieved is None


@pytest.mark.asyncio
async def test_session_retention_after_relogin(session_service):
    """Test that sessions and artifacts persist and can be retrieved after simulated re-login."""
    user_id = "user_relogin_test"

    session1 = await session_service.create_session(user_id=user_id, name="Morning Analysis")
    session2 = await session_service.create_session(user_id=user_id, name="Afternoon Review")

    await session_service.save_artifact(
        session_id=session1.id,
        artifact_type="chart",
        title="P&L Chart",
        data={"values": [100, 200, 300]},
    )
    await session_service.save_artifact(
        session_id=session1.id,
        artifact_type="table",
        title="Positions",
        data={"rows": ["AAPL", "GOOGL"]},
    )
    await session_service.save_artifact(
        session_id=session2.id,
        artifact_type="text",
        title="Notes",
        content="Some notes",
    )

    retrieved_sessions = await session_service.list_sessions(user_id)
    assert len(retrieved_sessions) == 2

    session1_artifacts = await session_service.get_artifacts(session1.id)
    assert len(session1_artifacts) == 2

    session2_artifacts = await session_service.get_artifacts(session2.id)
    assert len(session2_artifacts) == 1


@pytest.mark.asyncio
async def test_cascade_delete_artifacts(session_service, test_session):
    """Test that deleting a session also deletes its artifacts."""
    await session_service.save_artifact(
        session_id=test_session.id, artifact_type="chart", title="Chart 1"
    )
    await session_service.save_artifact(
        session_id=test_session.id, artifact_type="table", title="Table 1"
    )

    artifacts_before = await session_service.get_artifacts(test_session.id)
    assert len(artifacts_before) == 2

    await session_service.delete_session(test_session.id)

    artifacts_after = await session_service.get_artifacts(test_session.id)
    assert len(artifacts_after) == 0


@pytest.mark.asyncio
async def test_create_workspace(session_service):
    """Test creating a new workspace."""
    workspace = await session_service.create_workspace(user_id="user123", name="My Workspace")
    assert workspace.id is not None
    assert workspace.user_id == "user123"
    assert workspace.name == "My Workspace"
    assert workspace.artifact_positions == {}


@pytest.mark.asyncio
async def test_get_workspace(session_service):
    """Test retrieving a workspace by ID."""
    workspace = await session_service.create_workspace(user_id="user123", name="Test Workspace")
    retrieved = await session_service.get_workspace(workspace.id)
    assert retrieved is not None
    assert retrieved.id == workspace.id
    assert retrieved.name == "Test Workspace"


@pytest.mark.asyncio
async def test_list_workspaces(session_service):
    """Test listing workspaces for a user."""
    await session_service.create_workspace(user_id="user123", name="Workspace 1")
    await session_service.create_workspace(user_id="user123", name="Workspace 2")
    
    workspaces = await session_service.list_workspaces("user123")
    assert len(workspaces) == 2
    names = [w.name for w in workspaces]
    assert "Workspace 1" in names
    assert "Workspace 2" in names


@pytest.mark.asyncio
async def test_update_workspace_name(session_service):
    """Test updating workspace name."""
    workspace = await session_service.create_workspace(user_id="user123", name="Original Name")
    
    updated = await session_service.update_workspace(workspace.id, name="New Name")
    assert updated is not None
    assert updated.name == "New Name"


@pytest.mark.asyncio
async def test_update_workspace_positions(session_service):
    """Test updating workspace artifact positions."""
    workspace = await session_service.create_workspace(user_id="user123", name="Test")
    
    positions = {"artifact1": {"x": 100, "y": 200, "width": 400, "height": 300, "visible": True}}
    updated = await session_service.update_workspace(workspace.id, artifact_positions=positions)
    assert updated is not None
    assert updated.artifact_positions == positions


@pytest.mark.asyncio
async def test_delete_workspace(session_service):
    """Test deleting a workspace."""
    workspace = await session_service.create_workspace(user_id="user123", name="To Delete")
    workspace_id = workspace.id
    
    result = await session_service.delete_workspace(workspace_id)
    assert result is True
    
    retrieved = await session_service.get_workspace(workspace_id)
    assert retrieved is None


@pytest.mark.asyncio
async def test_workspace_with_artifact_workspace_id(session_service):
    """Test saving artifact with workspace_id."""
    workspace = await session_service.create_workspace(user_id="user123", name="Test")
    session = await session_service.create_session(user_id="user123")
    
    artifact = await session_service.save_artifact(
        session_id=session.id,
        artifact_type="chart",
        title="Test Chart",
        workspace_id=workspace.id,
    )
    assert artifact is not None
    assert artifact.workspace_id == workspace.id
