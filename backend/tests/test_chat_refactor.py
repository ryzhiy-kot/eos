import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.models.artifact import Artifact, MutationRecord
from app.models.workspace import Workspace
from app.services.session_service import SessionService
from app.services.execution_service import ExecutionService, ExecutionRequest
from app.db.base_class import Base

# Setup in-memory DB for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def db_session():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session

    await engine.dispose()

@pytest.mark.asyncio
async def test_chat_refactor_flow(db_session: AsyncSession):
    # 0. Create Workspace
    ws = Workspace(id="ws1", name="Test Workspace")
    db_session.add(ws)
    await db_session.commit()

    # 1. Create Session
    session_id = "chat_session_1"
    session_schema = await SessionService.create_session(
        db_session, session_id, "My Chat", workspace_id="ws1"
    )

    assert session_schema.id == session_id
    assert session_schema.name == "My Chat"
    assert session_schema.workspace_id == "ws1"
    assert len(session_schema.messages) == 0

    # Verify DB state
    art = await db_session.get(Artifact, session_id)
    assert art is not None
    assert art.type == "chat"
    assert art.session_id is None
    assert art.workspace_id == "ws1"
    assert len(art.mutations) == 1 # Creation mutation

    # 2. Add Message
    msg_schema = await SessionService.save_message(
        db_session, session_id, "user", "Hello World"
    )

    assert msg_schema.role == "user"
    assert msg_schema.content == "Hello World"
    assert msg_schema.session_id == session_id

    # Verify DB state
    await db_session.refresh(art)
    assert len(art.payload) == 1
    assert art.payload[0]["content"] == "Hello World"
    assert len(art.mutations) == 2

    # 3. Add Message with Artifact
    # Create a code artifact first
    code_art = Artifact(
        id="code_1",
        type="code",
        payload={"code": "print('hi')"},
        session_id=session_id, # Link to chat
        workspace_id="ws1"
    )
    db_session.add(code_art)
    await db_session.commit()

    msg_schema_2 = await SessionService.save_message(
        db_session, session_id, "assistant", "Here is code", artifacts=[code_art]
    )

    assert len(msg_schema_2.artifacts) == 1
    assert msg_schema_2.artifacts[0].id == "code_1"

    # Verify Payload
    await db_session.refresh(art)
    assert len(art.payload) == 2
    assert art.payload[1]["artifact_ids"] == ["code_1"]

    # 4. Get Session (Full Load)
    loaded_session = await SessionService.get_session(db_session, session_id)
    assert len(loaded_session.messages) == 2
    assert len(loaded_session.messages[1].artifacts) == 1
    assert loaded_session.messages[1].artifacts[0].id == "code_1"
