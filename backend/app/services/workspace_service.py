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
from typing import List, Optional
from app.models.workspace import Workspace
from app.models.user import WorkspaceMember
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate
import uuid
import time
import logging

logger = logging.getLogger(__name__)

class WorkspaceService:
    @staticmethod
    async def get_workspaces(
        db: AsyncSession, is_archived: bool = False
    ) -> List[Workspace]:
        stmt = select(Workspace).where(Workspace.is_archived == is_archived)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_workspace(db: AsyncSession, workspace_id: str) -> Optional[Workspace]:
        stmt = select(Workspace).where(Workspace.id == workspace_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_workspace(
        db: AsyncSession, workspace_in: WorkspaceCreate
    ) -> Workspace:
        db_obj = Workspace(
            name=workspace_in.name,
            state=workspace_in.state,
            is_archived=workspace_in.is_archived,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def update_workspace(
        db: AsyncSession, workspace_id: str, workspace_in: WorkspaceUpdate
    ) -> Optional[Workspace]:
        db_obj = await WorkspaceService.get_workspace(db, workspace_id)
        if not db_obj:
            return None

        update_data = workspace_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def delete_workspace(db: AsyncSession, workspace_id: str) -> bool:
        db_obj = await WorkspaceService.get_workspace(db, workspace_id)
        if not db_obj:
            return False

        db_obj.is_archived = True
        await db.commit()
        return True

    @staticmethod
    async def archive_pane(
        db: AsyncSession,
        workspace_id: str,
        pane_data: dict,
        user_id: Optional[int] = None,
    ) -> bool:
        from app.models.archived_pane import ArchivedPane

        db_obj = ArchivedPane(
            workspace_id=workspace_id,
            user_id=user_id,
            pane_data=pane_data,
        )
        db.add(db_obj)
        await db.commit()
        return True

    @staticmethod
    async def initialize_personal_workspace(db: AsyncSession, user_id: str, user_db_id: int) -> str:
        """
        Creates a new personal workspace for a user with a default empty chat session.
        Returns the workspace ID.
        """
        ws_id = str(uuid.uuid4())

        # Prepare initial session (Chat Artifact)
        pane_id = "P1"
        session_id = str(uuid.uuid4())
        # We treat the session AS the artifact

        initial_state = {
            "panes": {
                pane_id: {
                    "id": pane_id,
                    "type": "chat",
                    "artifactId": session_id, # Point to session ID
                    "title": "Chat",
                    "isSticky": False,
                    "lineage": {
                        "parentIds": [],
                        "command": "init",
                        "timestamp": f"{time.time()}",
                    },
                }
            },
            "artifacts": {
                session_id: {
                    "id": session_id,
                    "type": "chat",
                    "payload": [], # Chat payload is a list of messages
                    "session_id": None, # Root chat has no parent session
                    "mutations": [],
                    "metadata": {"name": "Chat"}
                }
            },
            "activeLayout": [pane_id],
            "archive": [],
            "focusedPaneId": pane_id
        }

        workspace = Workspace(
            id=ws_id,
            name=f"{user_id}'s Workspace",
            state=initial_state,
            is_archived=False,
        )
        db.add(workspace)
        await db.flush()

        member = WorkspaceMember(
            workspace_id=workspace.id, user_id=user_db_id, role="OWNER"
        )
        db.add(member)

        # Create session (Chat Artifact) in DB via Service
        from app.services.session_service import SessionService
        await SessionService.create_session(
            db,
            session_id=session_id,
            name="Chat",
            workspace_id=ws_id,
        )

        await db.commit()
        return ws_id
