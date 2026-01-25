from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.user import AuthSyncRequest, User as UserSchema
from fastapi import HTTPException
from app.schemas.user import LoginRequest

router = APIRouter()


@router.post("/sync", response_model=UserSchema, tags=["auth"])
async def sync_auth(req: AuthSyncRequest, db: AsyncSession = Depends(get_db)):
    from app.services.user_service import UserService

    user = await UserService.get_by_user_id(db, req.user_id)
    if not user:
        user = await UserService.create_user(db, req.user_id)
        await db.commit()
        await db.refresh(user)
    return user


@router.post("/login", response_model=UserSchema, tags=["auth"])
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    from app.services.user_service import UserService

    # Authenticate (or auto-register)
    user = await UserService.authenticate_user(db, req.username)

    if not user.enabled:
        raise HTTPException(status_code=403, detail="User account disabled")

    # Ensure workspace
    user = await UserService.ensure_personal_workspace(db, user)

    return user
