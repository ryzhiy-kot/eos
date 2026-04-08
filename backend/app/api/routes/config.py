from fastapi import APIRouter

from ...config import get_settings

router = APIRouter(prefix="", tags=["config"])


@router.get("/config")
async def get_config():
    settings = get_settings()
    return {
        "app_name": settings.APP_NAME,
        "display_name": settings.DISPLAY_NAME,
        "version": "0.1.0",
    }
