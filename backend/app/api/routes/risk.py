"""Risk routes — REST API for risk metrics and positions."""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.schemas import PositionResponse
from app.services.auth import get_current_user
from app.services.financial_api import MockFinancialService, mock_service

router = APIRouter(prefix="/risk", tags=["risk"])


def get_mock_service() -> MockFinancialService:
    """Dependency injection for MockFinancialService."""
    return mock_service


@router.get("/portfolio")
async def get_portfolio_risk(
    current_user: dict = Depends(get_current_user),
    mock_svc: MockFinancialService = Depends(get_mock_service),
) -> dict:
    """Get portfolio risk metrics."""
    return mock_svc.get_risk_metrics()


@router.get("/var-history")
async def get_var_history(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
    mock_svc: MockFinancialService = Depends(get_mock_service),
) -> list[dict]:
    """Get historical VaR data."""
    return mock_svc.get_risk_history(days=days)


@router.get("/positions", response_model=list[PositionResponse])
async def get_positions(
    desk: Optional[str] = Query(None),
    strategy: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    mock_svc: MockFinancialService = Depends(get_mock_service),
) -> list[dict]:
    """Get positions with optional filtering by desk or strategy."""
    positions = mock_svc.get_positions()
    if desk:
        positions = [p for p in positions if p["desk"].lower() == desk.lower()]
    if strategy:
        positions = [p for p in positions if p["strategy"].lower() == strategy.lower()]
    return positions