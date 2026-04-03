from fastapi import APIRouter, Depends

from app.services.auth import get_current_user
from app.services.financial_api import mock_service

router = APIRouter(prefix="/pnl", tags=["pnl"])


@router.get("/attribution")
async def get_pnl_attribution(current_user: dict = Depends(get_current_user)):
    return mock_service.get_pnl_attribution()
