"""Panel routes — REST API for dashboard panels."""

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
from app.services.panel_service import PanelService, get_panel_service

router = APIRouter(prefix="/panels", tags=["panels"])


def get_panel_service_dep() -> PanelService:
    """Dependency injection for PanelService."""
    return get_panel_service()


@router.get("/", response_model=list[PanelResponse])
async def list_panels(
    current_user: dict = Depends(get_current_user),
    panel_service: PanelService = Depends(get_panel_service_dep),
) -> list[PanelResponse]:
    """List all pinned panels for the current user."""
    panels = await panel_service.get_panels(UUID(current_user["sub"]))
    return [PanelResponse.model_validate(p) for p in panels]


@router.post("/", response_model=PanelResponse)
async def create_panel_endpoint(
    panel: PanelCreate,
    current_user: dict = Depends(get_current_user),
    panel_service: PanelService = Depends(get_panel_service_dep),
) -> PanelResponse:
    """Create a new panel."""
    new_panel = await panel_service.create_panel(
        user_id=UUID(current_user["sub"]),
        artifact_id=panel.artifact_id,
        name=panel.name,
        bq_function=panel.bq_function,
        bq_params=panel.bq_params,
        refresh_interval=panel.refresh_interval,
    )
    return PanelResponse.model_validate(new_panel)


@router.get("/{panel_id}", response_model=PanelResponse)
async def get_panel_endpoint(
    panel_id: UUID,
    current_user: dict = Depends(get_current_user),
    panel_service: PanelService = Depends(get_panel_service_dep),
) -> PanelResponse:
    """Get a specific panel by ID."""
    panel = await panel_service.get_panel(panel_id, UUID(current_user["sub"]))
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")
    return PanelResponse.model_validate(panel)


@router.get("/{panel_id}/refresh", response_model=PanelDataResponse)
async def refresh_panel_endpoint(
    panel_id: UUID,
    current_user: dict = Depends(get_current_user),
    panel_service: PanelService = Depends(get_panel_service_dep),
) -> PanelDataResponse:
    """Refresh panel data by re-executing its bq function."""
    try:
        data = await panel_service.refresh_panel(panel_id, UUID(current_user["sub"]))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return PanelDataResponse(data=data, last_updated=datetime.now())


@router.delete("/{panel_id}")
async def delete_panel_endpoint(
    panel_id: UUID,
    current_user: dict = Depends(get_current_user),
    panel_service: PanelService = Depends(get_panel_service_dep),
) -> dict:
    """Delete a panel."""
    deleted = await panel_service.delete_panel(panel_id, UUID(current_user["sub"]))
    if not deleted:
        raise HTTPException(status_code=404, detail="Panel not found")
    return {"status": "deleted"}


@router.put("/{panel_id}", response_model=PanelResponse)
async def update_panel_endpoint(
    panel_id: UUID,
    panel_update: PanelUpdate,
    current_user: dict = Depends(get_current_user),
    panel_service: PanelService = Depends(get_panel_service_dep),
) -> PanelResponse:
    """Update a panel's properties."""
    panel = await panel_service.update_panel(
        panel_id,
        UUID(current_user["sub"]),
        name=panel_update.name,
        refresh_interval=panel_update.refresh_interval,
    )
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")
    return PanelResponse.model_validate(panel)