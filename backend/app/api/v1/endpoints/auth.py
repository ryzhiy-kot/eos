from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.user import UpdateActiveWorkspaceRequest, User as UserSchema
from app.schemas.token import Token
from app.services.auth.protocol import AuthServiceProtocol
from app.services.auth.dependency import get_auth_service
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/login", response_model=Token, tags=["auth"])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthServiceProtocol = Depends(get_auth_service),
):
    from app.services.user_service import UserService

    # Authenticate
    result = await auth_service.authenticate(db, form_data.username, form_data.password)

    if result.error or not result.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.error or "Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not result.user.enabled:
        raise HTTPException(status_code=403, detail="User account disabled")

    # Sync to local DB
    user = await UserService.sync_user(db, result.user)

    # Ensure workspace
    await UserService.ensure_personal_workspace(db, user)

    return Token(
        access_token=result.session_token,
        token_type="bearer"
    )

@router.get("/me", response_model=UserSchema, tags=["auth"])
async def read_users_me(
    current_user: UserSchema = Depends(get_current_user),
):
    return current_user

@router.post("/sync", response_model=UserSchema, tags=["auth"])
async def sync_auth(
    current_user: UserSchema = Depends(get_current_user),
):
    return current_user

@router.post("/logout", tags=["auth"])
async def logout(
    current_user: UserSchema = Depends(get_current_user),
    auth_service: AuthServiceProtocol = Depends(get_auth_service),
):
    return {"message": "Logged out successfully"}

@router.post("/update-active-workspace", response_model=UserSchema, tags=["auth"])
async def update_active_workspace(
    req: UpdateActiveWorkspaceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user)
):
    from app.services.user_service import UserService

    if req.user_id != current_user.user_id:
         raise HTTPException(status_code=403, detail="Cannot update another user's workspace")

    user = await UserService.update_active_workspace(db, req.user_id, req.workspace_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
