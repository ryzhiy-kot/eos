from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.models.chat import ChatSession, ChatMessage
from app.models.artifact import Artifact


class SessionService:
    @staticmethod
    async def get_sessions(db: AsyncSession, workspace_id: str) -> List[ChatSession]:
        stmt = (
            select(ChatSession)
            .where(ChatSession.workspace_id == workspace_id)
            .options(
                selectinload(ChatSession.messages)
                .selectinload(ChatMessage.artifacts)
                .selectinload(Artifact.mutations)
            )
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_session(db: AsyncSession, session_id: str) -> Optional[ChatSession]:
        stmt = (
            select(ChatSession)
            .where(ChatSession.id == session_id)
            .options(
                selectinload(ChatSession.messages)
                .selectinload(ChatMessage.artifacts)
                .selectinload(Artifact.mutations)
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_session(
        db: AsyncSession,
        session_id: str,
        name: str,
        workspace_id: str = "default_workspace",
    ) -> ChatSession:
        db_obj = ChatSession(id=session_id, name=name, workspace_id=workspace_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj, ["messages"])
        return db_obj

    @staticmethod
    async def save_message(
        db: AsyncSession,
        session_id: str,
        role: str,
        content: str,
        artifacts: List = None,
    ) -> ChatMessage:
        db_obj = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
        )
        if artifacts:
            db_obj.artifacts = artifacts

        db.add(db_obj)
        await db.commit()

        # Re-query with deep loading
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.id == db_obj.id)
            .options(
                selectinload(ChatMessage.artifacts).selectinload(Artifact.mutations)
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one()

    @staticmethod
    async def update_session(
        db: AsyncSession,
        session_id: str,
        name: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[ChatSession]:
        db_obj = await SessionService.get_session(db, session_id)
        if not db_obj:
            return None

        if name is not None:
            db_obj.name = name
        if is_active is not None:
            db_obj.is_active = is_active

        await db.commit()
        await db.refresh(db_obj)
        return db_obj
