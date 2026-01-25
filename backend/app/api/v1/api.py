from fastapi import APIRouter
from app.api.v1.endpoints import workspaces, sessions, artifacts, auth, events

api_router = APIRouter()

api_router.include_router(workspaces.router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(artifacts.router, prefix="/artifacts", tags=["artifacts"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
