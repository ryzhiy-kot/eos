from fastapi import APIRouter, Query, WebSocket, Depends

from app.api.websocket.manager import market_stream_handler, risk_stream_handler
from app.services.panel_service import stream_panel
from app.services.auth import get_current_user

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/market")
async def websocket_market(websocket: WebSocket, symbols: str | None = Query(None)):
    symbol_list = symbols.split(",") if symbols else None
    await market_stream_handler(websocket, symbol_list)


@router.websocket("/ws/risk")
async def websocket_risk(websocket: WebSocket):
    await risk_stream_handler(websocket)


@router.websocket("/ws/panels/{panel_id}")
async def websocket_panel_stream(websocket: WebSocket, panel_id: str, current_user: dict = Depends(get_current_user)):
    from uuid import UUID
    try:
        panel_uuid = UUID(panel_id)
    except ValueError:
        await websocket.send_json({"error": "Invalid panel ID"})
        return
    
    user_uuid = UUID(current_user["sub"])
    await stream_panel(websocket, panel_uuid, user_uuid)
