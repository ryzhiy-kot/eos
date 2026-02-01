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

        # Prepare initial session
        pane_id = "P1"
        session_id = str(uuid.uuid4())
        artifact_id = str(uuid.uuid4())

        initial_state = {
            "panes": {
                pane_id: {
                    "id": pane_id,
                    "type": "chat",
                    "artifactId": artifact_id,
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
                artifact_id: {
                    "id": artifact_id,
                    "type": "chat",
                    "payload": {
                        "messages": []
                    },
                    "session_id": session_id,
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

        # Create session in DB
        from app.services.session_service import SessionService
        await SessionService.create_session(
            db,
            session_id=session_id,
            name="Chat",
            workspace_id=ws_id,
        )

        # Create artifact in DB
        from app.models.artifact import Artifact, MutationRecord
        db_artifact = Artifact(
            id=artifact_id,
            type="chat",
            artifact_metadata={"name": "Chat"},
            session_id=session_id,
            storage_backend="db",
            payload={"messages": []}
        )
        db.add(db_artifact)

        mutation = MutationRecord(
            artifact_id=artifact_id,
            version_id="v1",
            parent_id=None,
            origin={"type": "manual_edit", "sessionId": session_id},
            change_summary="Initial creation",
            payload={"messages": []},
            status="committed",
        )
        db_artifact.mutations.append(mutation)
        db.add(mutation)

        await db.commit()
        return ws_id

    @staticmethod
    async def ensure_default_workspace(db: AsyncSession, admin_user_id: int):
        """
        Ensures the system default workspace exists.
        """
        stmt = select(Workspace).where(Workspace.id == "default_workspace")
        result = await db.execute(stmt)
        default_ws = result.scalar_one_or_none()

        if not default_ws:
            # Create default chat session ID and Artifact ID
            default_session_id = "default_session"
            default_artifact_id = f"A_{default_session_id}"

            default_ws = Workspace(
                id="default_workspace",
                name="Default Workspace",
                state={
                    "panes": {
                        default_session_id: {
                            "id": default_session_id,
                            "type": "chat",
                            "artifactId": default_artifact_id,
                            "title": "General",
                            "isSticky": True,
                            "lineage": {
                                "parentIds": [],
                                "command": "init",
                                "timestamp": f"{time.time()}",
                            },
                        }
                    },
                    "artifacts": {
                        default_artifact_id: {
                            "id": default_artifact_id,
                            "type": "chat",
                            "payload": {
                                "messages": []
                            },
                            "session_id": default_session_id,
                            "mutations": [],
                            "metadata": {"name": "General"}
                        }
                    },
                    "activeLayout": [default_session_id],
                    "archive": [],
                    "focusedPaneId": default_session_id
                },
                is_archived=False,
            )
            db.add(default_ws)
            await db.flush()
            logger.info("✓ Created default workspace")

            # Link admin to default workspace
            stmt = select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == default_ws.id,
                WorkspaceMember.user_id == admin_user_id,
            )
            result = await db.execute(stmt)
            if not result.scalar_one_or_none():
                member = WorkspaceMember(
                    workspace_id=default_ws.id, user_id=admin_user_id, role="OWNER"
                )
                db.add(member)
                logger.info("✓ Linked admin to default workspace")

            # Create the actual Session record
            from app.services.session_service import SessionService

            await SessionService.create_session(
                db,
                session_id=default_session_id,
                name="General",
                workspace_id=default_ws.id,
            )

            # Create the Artifact record for default workspace
            from app.models.artifact import Artifact, MutationRecord
            db_artifact = Artifact(
                id=default_artifact_id,
                type="chat",
                artifact_metadata={"name": "General"},
                session_id=default_session_id,
                storage_backend="db",
                payload={"messages": []}
            )
            db.add(db_artifact)

            mutation = MutationRecord(
                artifact_id=default_artifact_id,
                version_id="v1",
                parent_id=None,
                origin={"type": "manual_edit", "sessionId": default_session_id},
                change_summary="Initial creation",
                payload={"messages": []},
                status="committed",
            )
            db_artifact.mutations.append(mutation)
            db.add(mutation)

            logger.info("✓ Created default chat session and artifact")

        await db.commit()
