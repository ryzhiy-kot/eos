from fastapi import APIRouter, Depends, Query

from app.schemas import InstrumentResponse, OHLCVResponse, QuoteResponse
from app.services.auth import get_current_user
from app.services.financial_api import mock_service

router = APIRouter(prefix="/market", tags=["market"])

INSTRUMENTS = [
    InstrumentResponse(
        id=str(i),
        symbol=inst["symbol"],
        name=inst["name"],
        exchange=inst["exchange"],
        asset_class=inst["asset_class"].value,
        currency=inst["currency"],
    )
    for i, inst in enumerate(mock_service.seed_database()["instruments"])
]


@router.get("/instruments", response_model=list[InstrumentResponse])
async def list_instruments(
    asset_class: str | None = Query(None),
    search: str | None = Query(None),
    current_user: dict = Depends(get_current_user),
):
    results = INSTRUMENTS
    if asset_class:
        results = [i for i in results if i.asset_class == asset_class]
    if search:
        q = search.lower()
        results = [i for i in results if q in i.symbol.lower() or q in i.name.lower()]
    return results


@router.get("/quote/{symbol}", response_model=QuoteResponse)
async def get_quote(symbol: str, current_user: dict = Depends(get_current_user)):
    return mock_service.get_quote(symbol)


@router.get("/ohlcv/{symbol}", response_model=list[OHLCVResponse])
async def get_ohlcv(
    symbol: str,
    days: int = Query(90, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
):
    return mock_service.get_ohlcv(symbol, days=days)
