import asyncio
from datetime import UTC, datetime

from fastapi import WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.services.financial_api import mock_service

logger = get_logger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time data streaming."""

    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        await websocket.accept()
        if channel not in self._connections:
            self._connections[channel] = []
        self._connections[channel].append(websocket)
        logger.info(f"WebSocket connected to channel: {channel}")

    def disconnect(self, websocket: WebSocket, channel: str) -> None:
        if channel in self._connections:
            self._connections[channel] = [
                ws for ws in self._connections[channel] if ws != websocket
            ]
            if not self._connections[channel]:
                del self._connections[channel]
        logger.info(f"WebSocket disconnected from channel: {channel}")

    async def broadcast(self, channel: str, message: dict) -> None:
        if channel not in self._connections:
            return
        dead = []
        for ws in self._connections[channel]:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections[channel].remove(ws)

    async def send_personal(self, websocket: WebSocket, message: dict) -> None:
        try:
            await websocket.send_json(message)
        except Exception:
            pass


manager = ConnectionManager()


async def market_stream_handler(websocket: WebSocket, symbols: list[str] | None = None):
    """Stream live market data for requested symbols."""
    symbols = symbols or ["AAPL", "MSFT", "GOOGL", "NVDA", "EURUSD"]
    await manager.connect(websocket, "market")
    try:
        while True:
            quotes = [mock_service.get_quote(s) for s in symbols]
            await manager.send_personal(
                websocket,
                {
                    "type": "market_update",
                    "data": [{**q, "timestamp": q["timestamp"].isoformat()} for q in quotes],
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        manager.disconnect(websocket, "market")


async def risk_stream_handler(websocket: WebSocket):
    """Stream live risk updates."""
    await manager.connect(websocket, "risk")
    try:
        while True:
            risk = mock_service.get_risk_metrics()
            await manager.send_personal(
                websocket,
                {
                    "type": "risk_update",
                    "data": risk,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        manager.disconnect(websocket, "risk")
