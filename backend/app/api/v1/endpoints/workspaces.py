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

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.schemas.workspace import (
    Workspace,
    WorkspaceCreate,
    WorkspaceUpdate,
    DeleteWorkspaceResponse,
)
from app.services.workspace_service import WorkspaceService
from app.api.deps import get_current_user
from app.schemas.user import User

router = APIRouter()


@router.get("/", response_model=List[Workspace], tags=["workspaces"])
async def list_workspaces(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await WorkspaceService.get_workspaces(db)


@router.post(
    "/",
    response_model=Workspace,
    status_code=status.HTTP_201_CREATED,
    tags=["workspaces"],
)
async def create_workspace(
    workspace_in: WorkspaceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await WorkspaceService.create_workspace(db, workspace_in)


@router.get("/{id}", response_model=Workspace, tags=["workspaces"])
async def get_workspace(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_obj = await WorkspaceService.get_workspace(db, id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return db_obj


@router.patch("/{id}", response_model=Workspace, tags=["workspaces"])
async def update_workspace(
    id: str,
    workspace_in: WorkspaceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_obj = await WorkspaceService.update_workspace(db, id, workspace_in)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return db_obj


@router.delete("/{id}", response_model=DeleteWorkspaceResponse, tags=["workspaces"])
async def delete_workspace(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = await WorkspaceService.delete_workspace(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {"status": "archived"}


@router.post("/{id}/archive-pane", tags=["workspaces"])
async def archive_pane(
    id: str,
    pane_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = await WorkspaceService.archive_pane(db, id, pane_data)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to archive pane")
    return {"status": "success"}
