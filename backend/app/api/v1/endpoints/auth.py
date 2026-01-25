from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import AuthSyncRequest, User as UserSchema

from fastapi import HTTPException
from app.schemas.user import LoginRequest


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


@router.post("/login", response_model=UserSchema, tags=["auth"])
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Simple login flow: check if user exists.
    # In a real app, verify password here.
    from sqlalchemy.orm import selectinload

    stmt = (
        select(User)
        .where(User.user_id == req.username)
        .options(selectinload(User.memberships))
    )
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()

    if not db_user:
        # Check if it's the admin fallback
        if req.username == "admin":
            # This should have been created on startup, but just in case
            db_user = User(
                user_id="admin", profile={"name": "Administrator"}, enabled=True
            )
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
        else:
            # First time user creation logic
            db_user = User(
                user_id=req.username, profile={"name": req.username}, enabled=True
            )
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)

    if not db_user.enabled:
        raise HTTPException(status_code=403, detail="User account disabled")

    # If user has no workspaces, create a default one for them
    # Need to re-fetch to ensure memberships are loaded if we just created the user
    # Or strict check
    if not db_user.memberships:
        from app.models.workspace import Workspace
        from app.models.user import WorkspaceMember
        import uuid

        # Create personal workspace
        ws_id = str(uuid.uuid4())
        # For legacy compatibility, if it's admin, try to link default_workspace if it exists
        if db_user.user_id == "admin":
            # Try to find default_workspace
            ws_stmt = select(Workspace).where(Workspace.id == "default_workspace")
            ws_res = await db.execute(ws_stmt)
            existing_ws = ws_res.scalar_one_or_none()
            if existing_ws:
                ws_id = existing_ws.id
                workspace = existing_ws
            else:
                # Fallback if startup didn't run?
                workspace = Workspace(
                    id="default_workspace",
                    name="Default Workspace",
                    state={
                        "panes": {},
                        "artifacts": {},
                        "activeLayout": [],
                        "archive": [],
                    },
                    is_archived=False,
                )
                db.add(workspace)
        else:
            workspace = Workspace(
                id=ws_id,
                name=f"{db_user.user_id}'s Workspace",
                state={"panes": {}, "artifacts": {}, "activeLayout": [], "archive": []},
                is_archived=False,
            )
            db.add(workspace)

        await db.flush()

        member = WorkspaceMember(
            workspace_id=workspace.id, user_id=db_user.id, role="OWNER"
        )
        db.add(member)
        await db.commit()

        # Refresh user to return with memberships
        result = await db.execute(stmt)
        db_user = result.scalar_one_or_none()

    return db_user
