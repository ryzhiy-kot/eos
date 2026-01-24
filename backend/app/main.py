from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from contextlib import asynccontextmanager
import asyncio
import json

from .database import engine, Base, get_db
from . import models, schemas


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="Elyon API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=schemas.RootResponse)
async def root():
    return {"message": "Welcome to Elyon API"}


@app.post("/api/auth/sync", response_model=schemas.User)
async def auth_sync(req: schemas.AuthSyncRequest, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    result = await db.execute(
        select(models.User).where(models.User.user_id == req.user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        user = models.User(user_id=req.user_id, profile={})
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


@app.get("/api/workspaces", response_model=List[schemas.Workspace])
async def list_workspaces(user_id: str, db: AsyncSession = Depends(get_db)):
    # Find internal user ID
    user_result = await db.execute(
        select(models.User).where(models.User.user_id == user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get non-archived workspaces where user is a member
    result = await db.execute(
        select(models.Workspace)
        .join(models.WorkspaceMember)
        .where(models.WorkspaceMember.user_id == user.id)
        .where(models.Workspace.is_archived.is_(False))
        .order_by(models.Workspace.updated_at.desc())
    )
    return result.scalars().all()


@app.post("/api/workspaces", response_model=schemas.Workspace)
async def create_workspace(
    user_id: str, req: schemas.WorkspaceCreate, db: AsyncSession = Depends(get_db)
):
    user_result = await db.execute(
        select(models.User).where(models.User.user_id == user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    workspace = models.Workspace(name=req.name, state=req.state)
    db.add(workspace)
    await db.flush()  # Get workspace ID

    member = models.WorkspaceMember(
        workspace_id=workspace.id, user_id=user.id, role="OWNER"
    )
    db.add(member)

    await db.commit()
    await db.refresh(workspace)
    return workspace


@app.put("/api/workspaces/{workspace_id}", response_model=schemas.Workspace)
async def update_workspace(
    workspace_id: str, req: schemas.WorkspaceUpdate, db: AsyncSession = Depends(get_db)
):
    # Check exists
    result = await db.execute(
        select(models.Workspace).where(models.Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(workspace, key, value)

    await db.commit()
    await db.refresh(workspace)
    return workspace


@app.delete(
    "/api/workspaces/{workspace_id}", response_model=schemas.DeleteWorkspaceResponse
)
async def delete_workspace(workspace_id: str, db: AsyncSession = Depends(get_db)):
    # Soft archive
    result = await db.execute(
        select(models.Workspace).where(models.Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    workspace.is_archived = True
    await db.commit()
    return {"success": True, "status": "archived"}


# Data Command Endpoints
@app.post("/api/commands/plot", response_model=schemas.PlotResponse)
async def plot_command(req: schemas.PlotRequest):
    # Mock implementation - replace with actual plotting logic
    return {
        "success": True,
        "result": {
            "type": "visual",
            "url": f"data:image/svg+xml,<svg>Mock plot for {req.pane_id}</svg>",
            "description": f"Generated plot based on: {req.prompt}",
        },
    }


@app.post("/api/commands/run", response_model=schemas.RunResponse)
async def run_command(req: schemas.RunRequest):
    # Mock implementation - replace with actual code execution
    return {
        "success": True,
        "result": {
            "type": "code",
            "output": f"Executed code on pane {req.pane_id}",
            "status": "success",
        },
    }


@app.post("/api/commands/diff", response_model=schemas.DiffResponse)
async def diff_command(req: schemas.DiffRequest):
    # Mock implementation - replace with actual diff logic
    return {
        "success": True,
        "result": {
            "type": "data",
            "differences": f"Comparing {req.pane_id_1} and {req.pane_id_2}",
            "summary": "Mock diff result",
        },
    }


@app.post("/api/commands/summarize", response_model=schemas.SummarizeResponse)
async def summarize_command(req: schemas.SummarizeRequest):
    # Mock implementation - replace with actual summarization
    return {
        "success": True,
        "result": {
            "type": "doc",
            "summary": f"Summary of pane {req.pane_id}",
            "key_points": ["Point 1", "Point 2", "Point 3"],
        },
    }


# SSE Event Stream Endpoint
async def event_generator():
    """Generate SSE events for real-time communication"""
    try:
        while True:
            # Send heartbeat every 30 seconds
            heartbeat = {
                "type": "heartbeat",
                "timestamp": asyncio.get_event_loop().time(),
            }
            yield f"data: {json.dumps(heartbeat)}\n\n"
            await asyncio.sleep(30)
    except asyncio.CancelledError:
        # Client disconnected
        pass


@app.get("/api/events/stream")
async def event_stream():
    """SSE endpoint for real-time server-to-client communication"""
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@app.get("/api/health", response_model=schemas.HealthCheckResponse)
async def health_check():
    return {"status": "healthy"}
