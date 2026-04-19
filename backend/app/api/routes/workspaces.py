from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from app.schemas import (
    WorkspaceCreate,
    WorkspaceListResponse,
    WorkspaceResponse,
    WorkspaceUpdate,
)
from app.services.auth import get_current_user
from app.services.session_service import get_session_service

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("/", response_model=WorkspaceListResponse)
async def list_workspaces(current_user: dict = Depends(get_current_user)):
    session_service = get_session_service()
    workspaces = await session_service.list_workspaces(current_user["sub"])
    return WorkspaceListResponse(
        workspaces=[
            WorkspaceResponse(
                id=w.id,
                user_id=w.user_id,
                name=w.name,
                artifact_positions=w.artifact_positions,
                created_at=w.created_at,
                updated_at=w.updated_at,
            )
            for w in workspaces
        ]
    )


@router.post("/", response_model=WorkspaceResponse)
async def create_workspace(
    request: WorkspaceCreate,
    current_user: dict = Depends(get_current_user),
):
    session_service = get_session_service()
    workspace = await session_service.create_workspace(
        user_id=current_user["sub"],
        name=request.name,
    )
    return WorkspaceResponse(
        id=workspace.id,
        user_id=workspace.user_id,
        name=workspace.name,
        artifact_positions=workspace.artifact_positions,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    current_user: dict = Depends(get_current_user),
):
    session_service = get_session_service()
    workspace = await session_service.get_workspace(workspace_id)
    if not workspace or workspace.user_id != current_user["sub"]:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return WorkspaceResponse(
        id=workspace.id,
        user_id=workspace.user_id,
        name=workspace.name,
        artifact_positions=workspace.artifact_positions,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: str,
    request: WorkspaceUpdate,
    current_user: dict = Depends(get_current_user),
):
    session_service = get_session_service()
    workspace = await session_service.get_workspace(workspace_id)
    if not workspace or workspace.user_id != current_user["sub"]:
        raise HTTPException(status_code=404, detail="Workspace not found")
    workspace = await session_service.update_workspace(
        workspace_id,
        name=request.name,
        artifact_positions=request.artifact_positions,
    )
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return WorkspaceResponse(
        id=workspace.id,
        user_id=workspace.user_id,
        name=workspace.name,
        artifact_positions=workspace.artifact_positions,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


@router.delete("/{workspace_id}")
async def delete_workspace(
    workspace_id: str,
    current_user: dict = Depends(get_current_user),
):
    session_service = get_session_service()
    workspace = await session_service.get_workspace(workspace_id)
    if not workspace or workspace.user_id != current_user["sub"]:
        raise HTTPException(status_code=404, detail="Workspace not found")
    await session_service.delete_workspace(workspace_id)
    return {"message": "Workspace deleted"}