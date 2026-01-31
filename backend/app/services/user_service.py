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

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.user import User, WorkspaceMember
from app.models.workspace import Workspace
from app.schemas.user import UserBase
from typing import Optional
import uuid
import time

logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    async def sync_user(db: AsyncSession, user_data: UserBase) -> User:
        user = await UserService.get_by_user_id(db, user_data.user_id)
        if not user:
            # Create new user
            user = await UserService.create_user(
                db, user_data.user_id, user_data.profile
            )
            await db.commit()
            # Refresh to get ID
            user = await UserService.get_by_user_id(db, user_data.user_id)
        else:
            # Update profile and enabled status
            if user_data.profile:
                user.profile = user_data.profile
            user.enabled = user_data.enabled
            await db.commit()

        return user

    @staticmethod
    async def get_by_user_id(db: AsyncSession, user_id: str) -> Optional[User]:
        stmt = (
            select(User)
            .where(User.user_id == user_id)
            .options(selectinload(User.memberships))
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(db: AsyncSession, user_id: str, profile: dict = None) -> User:
        if profile is None:
            profile = {}

        db_user = User(user_id=user_id, profile=profile, enabled=True)
        db.add(db_user)
        await (
            db.flush()
        )  # Commit is handled by caller usually, or at end of service method
        return db_user

    @staticmethod
    async def authenticate_user(db: AsyncSession, username: str) -> Optional[User]:
        # DEPRECATED: Use app.services.auth.local.LocalAuthService or similar instead
        # Simple auth logic compatible with current implementation
        user = await UserService.get_by_user_id(db, username)

        if not user:
            # Fallback logic for admin or auto-registration
            if username == "admin":
                user = await UserService.create_user(
                    db, "admin", {"name": "Administrator"}
                )
                # Commit to ensure ID is generated for subsequent steps
                await db.commit()
            else:
                # Auto-register
                user = await UserService.create_user(db, username, {"name": username})
                await db.commit()

            # Re-fetch to ensure loading options if needed (though new obj has empty memberships)
            user = await UserService.get_by_user_id(db, username)

        return user

    @staticmethod
    async def ensure_personal_workspace(db: AsyncSession, user: User) -> User:
        """
        Ensures the user has at least one workspace and an active workspace set.
        Returns the updated user object with memberships reloaded.
        """
        if user.memberships:
            if not user.active_workspace_id and len(user.memberships) > 0:
                user.active_workspace_id = user.memberships[0].workspace_id
                await db.commit()
            return user

        # Logic to create workspace
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
            name=f"{user.user_id}'s Workspace",
            state=initial_state,
            is_archived=False,
        )
        db.add(workspace)
        await db.flush()

        member = WorkspaceMember(
            workspace_id=workspace.id, user_id=user.id, role="OWNER"
        )
        db.add(member)

        # Set active workspace id
        user.active_workspace_id = workspace.id

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

        # Refresh user
        return await UserService.get_by_user_id(db, user.user_id)

    @staticmethod
    async def update_active_workspace(
        db: AsyncSession, user_id: str, workspace_id: str
    ) -> Optional[User]:
        user = await UserService.get_by_user_id(db, user_id)
        if user:
            user.active_workspace_id = workspace_id
            await db.commit()
            await db.refresh(user)
        return user

    @staticmethod
    async def initialize_defaults(db: AsyncSession):
        """
        Initializes default data (admin user, default workspace).
        This should be called on application startup.
        """
        # Check if admin user exists
        stmt = select(User).where(User.user_id == "admin")
        result = await db.execute(stmt)
        admin_user = result.scalar_one_or_none()

        if not admin_user:
            admin_user = User(
                user_id="admin", profile={"name": "Administrator"}, enabled=True
            )
            db.add(admin_user)
            await db.flush()
            logger.info("✓ Created default 'admin' user")

        # Check if default workspace exists
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
            # Check if link already exists to be safe
            stmt = select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == default_ws.id,
                WorkspaceMember.user_id == admin_user.id,
            )
            result = await db.execute(stmt)
            if not result.scalar_one_or_none():
                member = WorkspaceMember(
                    workspace_id=default_ws.id, user_id=admin_user.id, role="OWNER"
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
