from fastapi import APIRouter, Query, WebSocket

from app.api.websocket.manager import market_stream_handler, risk_stream_handler

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/market")
async def websocket_market(websocket: WebSocket, symbols: str | None = Query(None)):
    symbol_list = symbols.split(",") if symbols else None
    await market_stream_handler(websocket, symbol_list)


@router.websocket("/ws/risk")
async def websocket_risk(websocket: WebSocket):
    await risk_stream_handler(websocket)
