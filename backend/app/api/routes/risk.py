from fastapi import APIRouter, Depends, Query

from app.schemas import PositionResponse
from app.services.auth import get_current_user
from app.services.financial_api import mock_service

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/portfolio")
async def get_portfolio_risk(current_user: dict = Depends(get_current_user)):
    return mock_service.get_risk_metrics()


@router.get("/var-history")
async def get_var_history(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
):
    return mock_service.get_risk_history(days=days)


@router.get("/positions", response_model=list[PositionResponse])
async def get_positions(
    desk: str | None = Query(None),
    strategy: str | None = Query(None),
    current_user: dict = Depends(get_current_user),
):
    positions = mock_service.get_positions()
    if desk:
        positions = [p for p in positions if p["desk"].lower() == desk.lower()]
    if strategy:
        positions = [p for p in positions if p["strategy"].lower() == strategy.lower()]
    return positions
