from contextlib import asynccontextmanager

import dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.middleware import LoggingMiddleware
from .api.routes import agents, auth, config, market, panels, pnl, risk
from .api.websocket import router as ws_router
from .config import get_settings
from .core.logging import get_logger

dotenv.load_dotenv()

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.DISPLAY_NAME} Platform...")
    from app.services.session_service import init_db

    await init_db()
    logger.info("Database initialized")
    yield
    logger.info(f"Shutting down {settings.DISPLAY_NAME} Platform...")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="LLM-powered financial data visualization platform",
    lifespan=lifespan,
)

app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(config.router, prefix=settings.API_PREFIX)
app.include_router(market.router, prefix=settings.API_PREFIX)
app.include_router(risk.router, prefix=settings.API_PREFIX)
app.include_router(pnl.router, prefix=settings.API_PREFIX)
app.include_router(agents.router, prefix=settings.API_PREFIX)
app.include_router(panels.router, prefix=settings.API_PREFIX)
app.include_router(ws_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "docs": "/docs",
        "version": "0.1.0",
    }
