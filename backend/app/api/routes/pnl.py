"""P&L routes — REST API for profit and loss data."""

from fastapi import APIRouter, Depends

from app.services.auth import get_current_user
from app.services.financial_api import MockFinancialService, mock_service

router = APIRouter(prefix="/pnl", tags=["pnl"])


def get_mock_service() -> MockFinancialService:
    """Dependency injection for MockFinancialService."""
    return mock_service


@router.get("/attribution")
async def get_pnl_attribution(
    current_user: dict = Depends(get_current_user),
    mock_svc: MockFinancialService = Depends(get_mock_service),
) -> dict:
    """Get P&L attribution data."""
    return mock_svc.get_pnl_attribution()