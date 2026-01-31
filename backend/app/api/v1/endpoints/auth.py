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

from app.schemas.user import UpdateActiveWorkspaceRequest, LoggedInUser
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.user import AuthSyncRequest, User as UserSchema
from app.schemas.user import LoginRequest
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class LogoutRequest(BaseModel):
    session_token: str


@router.post("/sync", response_model=UserSchema, tags=["auth"])
async def sync_auth(req: AuthSyncRequest, db: AsyncSession = Depends(get_db)):
    from app.services.user_service import UserService

    user = await UserService.get_by_user_id(db, req.user_id)
    if not user:
        user = await UserService.create_user(db, req.user_id)
        await db.commit()
        # Refresh with memberships loaded
        user = await UserService.get_by_user_id(db, req.user_id)

    # Ensure workspace and active ID
    user = await UserService.ensure_personal_workspace(db, user)
    return user


from app.services.auth.protocol import AuthServiceProtocol
from app.services.auth.dependency import get_auth_service


@router.post("/login", response_model=LoggedInUser, tags=["auth"])
async def login(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthServiceProtocol = Depends(get_auth_service),
):
    from app.services.user_service import UserService

    # Authenticate (or auto-register)
    result = await auth_service.authenticate(db, req.username, req.password)

    if result.error or not result.user:
        raise HTTPException(
            status_code=401, detail=result.error or "Authentication failed"
        )

    if not result.user.enabled:
        raise HTTPException(status_code=403, detail="User account disabled")

    # Sync to local DB
    user = await UserService.sync_user(db, result.user)

    # Ensure workspace
    user = await UserService.ensure_personal_workspace(db, user)

    user_schema = UserSchema.model_validate(user)

    return LoggedInUser(
        **user_schema.model_dump(),
        session_token=result.session_token or "",
        session_expires_at=result.session_expires_at or datetime.utcnow(),
    )


@router.post("/logout", tags=["auth"])
async def logout(
    req: LogoutRequest,
    auth_service: AuthServiceProtocol = Depends(get_auth_service),
):
    await auth_service.logout(req.session_token)
    return {"message": "Logged out successfully"}


@router.post("/update-active-workspace", response_model=UserSchema, tags=["auth"])
async def update_active_workspace(
    req: UpdateActiveWorkspaceRequest, db: AsyncSession = Depends(get_db)
):
    from app.services.user_service import UserService

    user = await UserService.update_active_workspace(db, req.user_id, req.workspace_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
