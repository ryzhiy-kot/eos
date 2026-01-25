from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1.api import api_router
from app.core.config import get_settings
from app.db.session import engine
from app.db.base_class import Base
import app.models  # Ensure all models are registered

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Initialize default user and workspace
    from app.db.session import AsyncSessionLocal
    from app.models.user import User, WorkspaceMember
    from app.models.workspace import Workspace
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        # Check if admin user exists
        stmt = select(User).where(User.user_id == "admin")
        result = await session.execute(stmt)
        admin_user = result.scalar_one_or_none()

        if not admin_user:
            admin_user = User(
                user_id="admin", profile={"name": "Administrator"}, enabled=True
            )
            session.add(admin_user)
            await session.flush()
            print("✓ Created default 'admin' user")

        # Check if default workspace exists
        stmt = select(Workspace).where(Workspace.id == "default_workspace")
        result = await session.execute(stmt)
        default_ws = result.scalar_one_or_none()

        if not default_ws:
            default_ws = Workspace(
                id="default_workspace",
                name="Default Workspace",
                state={"panes": {}, "artifacts": {}, "activeLayout": [], "archive": []},
                is_archived=False,
            )
            session.add(default_ws)
            await session.flush()
            print("✓ Created default workspace")

            # Link admin to default workspace
            member = WorkspaceMember(
                workspace_id=default_ws.id, user_id=admin_user.id, role="OWNER"
            )
            session.add(member)
            print("✓ Linked admin to default workspace")

        await session.commit()

    yield
    # Shutdown logic (if any)


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 API Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/")
async def root():
    return {"message": "Elyon Backend API is running."}
