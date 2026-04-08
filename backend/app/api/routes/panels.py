from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.schemas import (
    PanelCreate,
    PanelDataResponse,
    PanelResponse,
    PanelUpdate,
)
from app.services.auth import get_current_user
from app.services.panel_service import (
    create_panel,
    delete_panel,
    get_panel,
    get_panels,
    refresh_panel,
    update_panel,
)

router = APIRouter(prefix="/panels", tags=["panels"])


@router.get("/", response_model=list[PanelResponse])
async def list_panels(current_user: dict = Depends(get_current_user)):
    panels = await get_panels(current_user["sub"])
    return [
        PanelResponse(
            id=p.id,
            user_id=p.user_id,
            artifact_id=p.artifact_id,
            name=p.name,
            bq_function=p.bq_function,
            bq_params=p.bq_params,
            refresh_interval=p.refresh_interval,
            is_pinned=p.is_pinned,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in panels
    ]


@router.post("/", response_model=PanelResponse)
async def create_panel_endpoint(
    panel: PanelCreate,
    current_user: dict = Depends(get_current_user),
):
    new_panel = await create_panel(
        user_id=current_user["sub"],
        artifact_id=panel.artifact_id,
        name=panel.name,
        bq_function=panel.bq_function,
        bq_params=panel.bq_params,
        refresh_interval=panel.refresh_interval,
    )
    return PanelResponse(
        id=new_panel.id,
        user_id=new_panel.user_id,
        artifact_id=new_panel.artifact_id,
        name=new_panel.name,
        bq_function=new_panel.bq_function,
        bq_params=new_panel.bq_params,
        refresh_interval=new_panel.refresh_interval,
        is_pinned=new_panel.is_pinned,
        created_at=new_panel.created_at,
        updated_at=new_panel.updated_at,
    )


@router.get("/{panel_id}", response_model=PanelResponse)
async def get_panel_endpoint(
    panel_id: str,
    current_user: dict = Depends(get_current_user),
):
    panel = await get_panel(panel_id, current_user["sub"])
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")
    return PanelResponse(
        id=panel.id,
        user_id=panel.user_id,
        artifact_id=panel.artifact_id,
        name=panel.name,
        bq_function=panel.bq_function,
        bq_params=panel.bq_params,
        refresh_interval=panel.refresh_interval,
        is_pinned=panel.is_pinned,
        created_at=panel.created_at,
        updated_at=panel.updated_at,
    )


@router.get("/{panel_id}/refresh", response_model=PanelDataResponse)
async def refresh_panel_endpoint(
    panel_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        data = await refresh_panel(panel_id, current_user["sub"])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return PanelDataResponse(data=data, last_updated=datetime.now())


@router.delete("/{panel_id}")
async def delete_panel_endpoint(
    panel_id: str,
    current_user: dict = Depends(get_current_user),
):
    deleted = await delete_panel(panel_id, current_user["sub"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Panel not found")
    return {"status": "deleted"}


@router.put("/{panel_id}", response_model=PanelResponse)
async def update_panel_endpoint(
    panel_id: str,
    panel_update: PanelUpdate,
    current_user: dict = Depends(get_current_user),
):
    panel = await update_panel(
        panel_id,
        current_user["sub"],
        name=panel_update.name,
        refresh_interval=panel_update.refresh_interval,
    )
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")
    return PanelResponse(
        id=panel.id,
        user_id=panel.user_id,
        artifact_id=panel.artifact_id,
        name=panel.name,
        bq_function=panel.bq_function,
        bq_params=panel.bq_params,
        refresh_interval=panel.refresh_interval,
        is_pinned=panel.is_pinned,
        created_at=panel.created_at,
        updated_at=panel.updated_at,
    )
