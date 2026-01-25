from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import AuthSyncRequest, User as UserSchema

router = APIRouter()


@router.post("/sync", response_model=UserSchema, tags=["auth"])
async def sync_auth(req: AuthSyncRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.user_id == req.user_id)
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()

    if not db_user:
        db_user = User(user_id=req.user_id)
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
    return db_user
