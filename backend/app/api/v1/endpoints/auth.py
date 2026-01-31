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

from app.schemas.user import UpdateActiveWorkspaceRequest
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.user import AuthSyncRequest, User as UserSchema
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()


class LogoutRequest(BaseModel):
    session_token: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: Optional[UserSchema] = None
    session_expires_at: Optional[datetime] = None

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
from app.api import deps


@router.post("/login", response_model=TokenResponse, tags=["auth"])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthServiceProtocol = Depends(get_auth_service),
):
    from app.services.user_service import UserService

    # Authenticate (or auto-register)
    result = await auth_service.authenticate(db, form_data.username, form_data.password)

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

    return TokenResponse(
        access_token=result.session_token,
        token_type="bearer",
        user=user_schema,
        session_expires_at=result.session_expires_at
    )


@router.post("/logout", tags=["auth"])
async def logout(
    req: LogoutRequest,
    auth_service: AuthServiceProtocol = Depends(get_auth_service),
    current_user: UserSchema = Depends(deps.get_current_user),
):
    await auth_service.logout(req.session_token)
    return {"message": "Logged out successfully"}


@router.post("/update-active-workspace", response_model=UserSchema, tags=["auth"])
async def update_active_workspace(
    req: UpdateActiveWorkspaceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserSchema = Depends(deps.get_current_user),
):
    from app.services.user_service import UserService

    # Verify that the user being updated matches the authenticated user
    if req.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Cannot update another user's workspace")

    user = await UserService.update_active_workspace(db, req.user_id, req.workspace_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
