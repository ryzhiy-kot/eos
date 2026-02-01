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
from app.models.user import User
from app.schemas.user import UserBase
from app.services.workspace_service import WorkspaceService
from typing import Optional

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

        # Delegate workspace creation to WorkspaceService
        ws_id = await WorkspaceService.initialize_personal_workspace(db, user.user_id, user.id)

        # Set active workspace id
        user.active_workspace_id = ws_id
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
        Initializes default data (admin user).
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
