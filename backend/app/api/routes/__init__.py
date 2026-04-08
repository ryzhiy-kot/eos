from .routes.agents import router as agents_router
from .routes.auth import router as auth_router
from .routes.market import router as market_router
from .routes.panels import router as panels_router
from .routes.pnl import router as pnl_router
from .routes.risk import router as risk_router

__all__ = [
    "auth_router",
    "market_router",
    "risk_router",
    "pnl_router",
    "agents_router",
    "panels_router",
]
