from app.api.routes.agents import router as agents_router
from app.api.routes.auth import router as auth_router
from app.api.routes.market import router as market_router
from app.api.routes.pnl import router as pnl_router
from app.api.routes.risk import router as risk_router

__all__ = ["auth_router", "market_router", "risk_router", "pnl_router", "agents_router"]
