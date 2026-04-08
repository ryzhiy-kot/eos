"""Session service — business logic for sessions, messages, and artifacts.

Uses the centralized database session from app.db.session and models
from app.models.session_models.

This module follows SRP — it handles only session/artifact/message management,
not database connections or model definitions.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.db.session import async_session
from app.models.session_models import Artifact, Message, Session

logger = get_logger(__name__)


async def init_db() -> None:
    """Initialize database tables (for backward compatibility)."""
    from app.db.session import engine

    async with engine.begin() as conn:
        await conn.run_sync(Session.metadata.create_all)


class SessionService:
    """Service for managing sessions, messages, and artifacts."""

    def __init__(self, session_factory=None):
        self._session_factory = session_factory

    async def _get_session_factory(self):
        """Get the session factory, lazily to avoid import cycle."""
        return async_session

    async def _generate_name(self) -> str:
        """Generate an auto-name based on current date."""
        now = datetime.now(UTC)
        return f"Session - {now.strftime('%b %d, %Y')}"

    async def create_session(self, user_id: str, name: str | None = None) -> Session:
        """Create a new session."""
        session_id = str(uuid4())
        session_name = name or await self._generate_name()

        async with async_session() as db_session:
            db_session = Session(
                id=session_id,
                user_id=user_id,
                name=session_name,
            )
            db_session.add(db_session)
            await db_session.commit()
            await db_session.refresh(db_session)
            logger.info("Created session %s for user %s", session_id, user_id)
            return db_session

    async def ensure_session(
        self, session_id: str, user_id: str, name: str | None = None
    ) -> Session:
        """Ensure a session exists, creating it if necessary."""
        async with async_session() as db_session:
            db_session = await db_session.get(Session, session_id)
            if db_session:
                return db_session

            session_name = name or await self._generate_name()
            db_session = Session(
                id=session_id,
                user_id=user_id,
                name=session_name,
            )
            db_session.add(db_session)
            await db_session.commit()
            await db_session.refresh(db_session)
            logger.info("Lazily created session %s for user %s", session_id, user_id)
            return db_session

    async def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID."""
        async with async_session() as db_session:
            result = await db_session.get(Session, session_id)
            if result:
                await db_session.refresh(result)
            return result

    async def list_sessions(self, user_id: str) -> list[Session]:
        """List all sessions for a user."""
        async with async_session() as db_session:
            stmt = (
                select(Session)
                .where(Session.user_id == user_id)
                .order_by(Session.updated_at.desc())
            )
            result = await db_session.execute(stmt)
            return list(result.scalars().all())

    async def update_session(self, session_id: str, name: str) -> Session | None:
        """Update a session's name."""
        async with async_session() as db_session:
            db_session_obj = await db_session.get(Session, session_id)
            if not db_session_obj:
                return None
            db_session_obj.name = name
            await db_session.commit()
            await db_session.refresh(db_session_obj)
            logger.info("Updated session %s name to '%s'", session_id, name)
            return db_session_obj

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and its artifacts."""
        async with async_session() as db_session:
            db_session = await db_session.get(Session, session_id)
            if not db_session:
                return False
            await db_session.delete(db_session)
            await db_session.commit()
            logger.info("Deleted session %s", session_id)
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
        async with async_session() as db_session:
            db_session_obj = await db_session.get(Session, session_id)
            if not db_session_obj:
                logger.warning("Cannot save artifact: session %s not found", session_id)
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
            db_session.add(artifact)
            await db_session.commit()
            await db_session.refresh(artifact)
            logger.info("Saved artifact %s for session %s", artifact.id, session_id)
            return artifact

    async def get_artifacts(self, session_id: str) -> list[Artifact]:
        """Get all artifacts for a session."""
        async with async_session() as db_session:
            stmt = (
                select(Artifact)
                .where(Artifact.session_id == session_id)
                .order_by(Artifact.created_at.desc())
            )
            result = await db_session.execute(stmt)
            return list(result.scalars().all())

    async def get_artifact(self, artifact_id: str) -> Artifact | None:
        """Get a specific artifact by ID."""
        async with async_session() as db_session:
            return await db_session.get(Artifact, artifact_id)

    async def save_message(
        self, session_id: str, role: str, content: str
    ) -> Message | None:
        """Save a message to a session."""
        async with async_session() as db_session:
            db_session_obj = await db_session.get(Session, session_id)
            if not db_session_obj:
                logger.warning("Cannot save message: session %s not found", session_id)
                return None

            message = Message(
                id=str(uuid4()),
                session_id=session_id,
                role=role,
                content=content,
            )
            db_session.add(message)
            await db_session.commit()
            await db_session.refresh(message)
            logger.info("Saved message %s for session %s", message.id, session_id)
            return message

    async def get_messages(self, session_id: str) -> list[Message]:
        """Get all messages for a session, ordered by creation time."""
        async with async_session() as db_session:
            stmt = (
                select(Message)
                .where(Message.session_id == session_id)
                .order_by(Message.created_at.asc())
            )
            result = await db_session.execute(stmt)
            return list(result.scalars().all())

    async def clear_messages(self, session_id: str) -> bool:
        """Clear all messages for a session."""
        async with async_session() as db_session:
            stmt = delete(Message).where(Message.session_id == session_id)
            await db_session.execute(stmt)
            await db_session.commit()
            logger.info("Cleared messages for session %s", session_id)
            return True


# Singleton instance for backward compatibility
_session_service: SessionService | None = None


def get_session_service() -> SessionService:
    """Get or create a SessionService singleton."""
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service
