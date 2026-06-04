from fastapi import APIRouter, Query, WebSocket

from app.api.websocket.manager import market_stream_handler, risk_stream_handler
from app.services.panel_service import stream_panel
from app.services.auth import decode_token

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/market")
async def websocket_market(websocket: WebSocket, symbols: str | None = Query(None)):
    symbol_list = symbols.split(",") if symbols else None
    await market_stream_handler(websocket, symbol_list)


@router.websocket("/ws/risk")
async def websocket_risk(websocket: WebSocket):
    await risk_stream_handler(websocket)


@router.websocket("/ws/panels/{panel_id}")
async def websocket_panel_stream(websocket: WebSocket, panel_id: str, token: str | None = Query(None)):
    if not token:
        await websocket.close(code=4001, reason="Authentication required")
        return
    
    try:
        current_user = await decode_token(token)
    except Exception:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return
    
    await stream_panel(websocket, panel_id, current_user["sub"])
