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

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict
import uuid
from datetime import datetime, UTC

from app.models.artifact import Artifact, MutationRecord
from app.schemas.chat import (
    ChatSession as ChatSessionSchema,
    ChatMessage as ChatMessageSchema,
)
from app.schemas.artifact import Artifact as ArtifactSchema


class SessionService:
    @staticmethod
    async def get_sessions(
        db: AsyncSession, workspace_id: str
    ) -> List[ChatSessionSchema]:
        stmt = select(Artifact).where(
            Artifact.workspace_id == workspace_id, Artifact.type == "chat"
        )
        result = await db.execute(stmt)
        artifacts = result.scalars().all()
        # Note: listing sessions usually doesn't need all messages/children loaded
        # But our schema requires 'messages'. We might send empty list for summary?
        # Or load them. Chat payloads are usually small enough.
        # But we won't load child artifacts for the list view to save BW.
        return [
            SessionService._map_artifact_to_session(a, load_children=False)
            for a in artifacts
        ]

    @staticmethod
    async def get_session(
        db: AsyncSession, session_id: str
    ) -> Optional[ChatSessionSchema]:
        stmt = (
            select(Artifact)
            .where(Artifact.id == session_id, Artifact.type == "chat")
            .options(selectinload(Artifact.mutations))
        )
        result = await db.execute(stmt)
        chat_artifact = result.scalar_one_or_none()
        if not chat_artifact:
            return None

        # Fetch child artifacts to populate message.artifacts
        child_stmt = select(Artifact).where(Artifact.session_id == session_id)
        child_res = await db.execute(child_stmt)
        child_artifacts_map = {a.id: a for a in child_res.scalars().all()}

        return SessionService._map_artifact_to_session(
            chat_artifact, child_artifacts_map
        )

    @staticmethod
    async def create_session(
        db: AsyncSession,
        session_id: str,
        name: str,
        workspace_id: str = "default_workspace",
    ) -> ChatSessionSchema:
        artifact = Artifact(
            id=session_id,
            type="chat",
            workspace_id=workspace_id,
            payload=[],
            artifact_metadata={"name": name, "is_active": True},
            session_id=session_id,  # Self-reference for root? Or None.
            # Schema says session_id is Optional. Model says Nullable=True.
            # For a root chat, session_id should probably be None or itself.
            # Let's make it None to avoid recursion issues in some generic traversals.
        )
        artifact.session_id = None  # Explicitly None for root chat

        db.add(artifact)

        mutation = MutationRecord(
            artifact_id=session_id,
            version_id="v1",
            origin={"type": "creation", "sessionId": session_id},
            payload=[],
            change_summary="Chat created",
            status="committed",
        )
        db.add(mutation)
        await db.commit()
        return SessionService._map_artifact_to_session(artifact)

    @staticmethod
    async def save_message(
        db: AsyncSession,
        session_id: str,
        role: str,
        content: str,
        artifacts: List[Artifact] = None,
    ) -> ChatMessageSchema:
        stmt = select(Artifact).where(Artifact.id == session_id)
        result = await db.execute(stmt)
        chat_artifact = result.scalar_one()

        current_payload = (
            chat_artifact.payload if isinstance(chat_artifact.payload, list) else []
        )

        new_msg_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC)

        artifact_ids = [a.id for a in artifacts] if artifacts else []

        new_msg = {
            "id": new_msg_id,
            "role": role,
            "content": content,
            "created_at": timestamp.isoformat(),
            "artifact_ids": artifact_ids,
        }

        new_payload = current_payload + [new_msg]
        chat_artifact.payload = new_payload

        # Mutation
        version_id = f"v{int(timestamp.timestamp() * 1000)}"

        mutation = MutationRecord(
            artifact_id=session_id,
            version_id=version_id,
            origin={
                "type": "chat_message",
                "role": role,
                "sessionId": session_id,
            },
            payload=new_payload,
            change_summary=f"Message from {role}",
            status="committed",
        )
        db.add(mutation)
        await db.commit()

        # Construct return object
        # Ensure we pass Pydantic models for artifacts
        pydantic_artifacts = []
        if artifacts:
            for a in artifacts:
                # 'a' might be an ORM object or Pydantic object
                if isinstance(a, Artifact):
                    # Manual construction to avoid MissingGreenlet on lazy 'mutations'
                    pydantic_artifacts.append(ArtifactSchema(
                        id=a.id,
                        type=a.type,
                        name=a.name,
                        payload=a.payload,
                        metadata=a.artifact_metadata,
                        session_id=a.session_id,
                        created_at=a.created_at,
                        mutations=[]
                    ))
                else:
                    pydantic_artifacts.append(a)

        return ChatMessageSchema(
            id=new_msg_id,
            session_id=session_id,
            role=role,
            content=content,
            created_at=timestamp,
            artifacts=pydantic_artifacts,
        )

    @staticmethod
    async def update_session(
        db: AsyncSession,
        session_id: str,
        name: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[ChatSessionSchema]:
        stmt = select(Artifact).where(Artifact.id == session_id)
        result = await db.execute(stmt)
        chat_artifact = result.scalar_one_or_none()
        if not chat_artifact:
            return None

        metadata = dict(chat_artifact.artifact_metadata or {})

        if name is not None:
            metadata["name"] = name
        if is_active is not None:
            metadata["is_active"] = is_active

        chat_artifact.artifact_metadata = metadata
        await db.commit()

        # We should also record a mutation for metadata change?
        # Ideally yes, but for now we update in place for simple props.

        return SessionService._map_artifact_to_session(chat_artifact)

    @staticmethod
    def _map_artifact_to_session(
        artifact: Artifact, child_artifacts_map: Dict = None, load_children: bool = True
    ) -> ChatSessionSchema:
        messages = []
        raw_msgs = artifact.payload if isinstance(artifact.payload, list) else []

        # If we are not loading children (e.g. list view), we skip artifact resolution
        # But we still map the messages structure

        for m in raw_msgs:
            # m is dict
            msg_artifacts = []
            if load_children and "artifact_ids" in m and child_artifacts_map:
                msg_artifacts = [
                    ArtifactSchema.model_validate(child_artifacts_map[aid])
                    for aid in m["artifact_ids"]
                    if aid in child_artifacts_map
                ]

            created_at_val = None
            if m.get("created_at"):
                try:
                    created_at_val = datetime.fromisoformat(m["created_at"])
                except ValueError:
                    pass

            messages.append(
                ChatMessageSchema(
                    id=m.get("id", str(uuid.uuid4())),
                    session_id=artifact.id,
                    role=m.get("role", "unknown"),
                    content=m.get("content", ""),
                    created_at=created_at_val,
                    artifacts=msg_artifacts,
                )
            )

        metadata = artifact.artifact_metadata or {}

        return ChatSessionSchema(
            id=artifact.id,
            name=metadata.get("name", "Untitled Chat"),
            workspace_id=artifact.workspace_id or "unknown",
            is_active=metadata.get("is_active", True),
            created_at=artifact.created_at,
            messages=messages,
        )
