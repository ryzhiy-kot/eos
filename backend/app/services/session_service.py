import logging
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

engine = create_async_engine(
    settings.SESSION_DB_URL,
    echo=settings.DEBUG,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    artifacts: Mapped[list["Artifact"]] = relationship(
        "Artifact", back_populates="session", cascade="all, delete-orphan"
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="session", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["Session"] = relationship("Session", back_populates="messages")


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    spec: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    columns: Mapped[list | None] = mapped_column(JSON, nullable=True)
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    format: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["Session"] = relationship("Session", back_populates="artifacts")


async def init_db():
    """Initialize the database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session_maker():
    """Get the async session maker."""
    return async_session


class SessionService:
    """Service for managing sessions and artifacts using SQLAlchemy."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession] | None = None):
        self._session_factory = session_factory or async_session

    async def _generate_name(self) -> str:
        """Generate an auto-name based on current date."""
        now = datetime.now(UTC)
        return f"Session - {now.strftime('%b %d, %Y')}"

    async def create_session(self, user_id: str, name: str | None = None) -> Session:
        """Create a new session."""
        session_id = str(uuid4())
        session_name = name or await self._generate_name()

        async with self._session_factory() as session:
            db_session = Session(
                id=session_id,
                user_id=user_id,
                name=session_name,
            )
            session.add(db_session)
            await session.commit()
            await session.refresh(db_session)
            logger.info(f"Created session {session_id} for user {user_id}")
            return db_session

    async def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID."""
        async with self._session_factory() as session:
            result = await session.get(Session, session_id)
            if result:
                await session.refresh(result)
            return result

    async def list_sessions(self, user_id: str) -> list[Session]:
        """List all sessions for a user."""
        from sqlalchemy import select

        async with self._session_factory() as session:
            stmt = (
                select(Session)
                .where(Session.user_id == user_id)
                .order_by(Session.updated_at.desc())
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update_session(self, session_id: str, name: str) -> Session | None:
        """Update a session's name."""
        async with self._session_factory() as session:
            db_session = await session.get(Session, session_id)
            if not db_session:
                return None
            db_session.name = name
            await session.commit()
            await session.refresh(db_session)
            logger.info(f"Updated session {session_id} name to '{name}'")
            return db_session

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and its artifacts."""
        async with self._session_factory() as session:
            db_session = await session.get(Session, session_id)
            if not db_session:
                return False
            await session.delete(db_session)
            await session.commit()
            logger.info(f"Deleted session {session_id}")
            return True

    async def save_artifact(
        self,
        session_id: str,
        artifact_type: str,
        title: str | None = None,
        spec: dict | None = None,
        columns: list | None = None,
        data: dict | None = None,
        content: str | None = None,
        format: str | None = None,
    ) -> Artifact | None:
        """Save an artifact associated with a session."""
        async with self._session_factory() as session:
            db_session = await session.get(Session, session_id)
            if not db_session:
                logger.warning(f"Cannot save artifact: session {session_id} not found")
                return None

            artifact = Artifact(
                id=str(uuid4()),
                session_id=session_id,
                type=artifact_type,
                title=title,
                spec=spec,
                columns=columns,
                data=data,
                content=content,
                format=format,
            )
            session.add(artifact)
            await session.commit()
            await session.refresh(artifact)
            logger.info(f"Saved artifact {artifact.id} for session {session_id}")
            return artifact

    async def get_artifacts(self, session_id: str) -> list[Artifact]:
        """Get all artifacts for a session."""
        from sqlalchemy import select

        async with self._session_factory() as session:
            stmt = (
                select(Artifact)
                .where(Artifact.session_id == session_id)
                .order_by(Artifact.created_at.desc())
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_artifact(self, artifact_id: str) -> Artifact | None:
        """Get a specific artifact by ID."""
        async with self._session_factory() as session:
            return await session.get(Artifact, artifact_id)

    async def save_message(self, session_id: str, role: str, content: str) -> Message | None:
        """Save a message to a session."""
        async with self._session_factory() as session:
            db_session = await session.get(Session, session_id)
            if not db_session:
                logger.warning(f"Cannot save message: session {session_id} not found")
                return None

            message = Message(
                id=str(uuid4()),
                session_id=session_id,
                role=role,
                content=content,
            )
            session.add(message)
            await session.commit()
            await session.refresh(message)
            logger.info(f"Saved message {message.id} for session {session_id}")
            return message

    async def get_messages(self, session_id: str) -> list[Message]:
        """Get all messages for a session, ordered by creation time."""
        from sqlalchemy import select

        async with self._session_factory() as session:
            stmt = (
                select(Message)
                .where(Message.session_id == session_id)
                .order_by(Message.created_at.asc())
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def clear_messages(self, session_id: str) -> bool:
        """Clear all messages for a session."""
        from sqlalchemy import delete

        async with self._session_factory() as session:
            stmt = delete(Message).where(Message.session_id == session_id)
            await session.execute(stmt)
            await session.commit()
            logger.info(f"Cleared messages for session {session_id}")
            return True


def get_session_service() -> SessionService:
    """Get or create a SessionService instance."""
    if not hasattr(get_session_service, "_instance"):
        get_session_service._instance = SessionService()
    return get_session_service._instance
