from fastapi import Depends
from app.core.config import get_settings, Settings
from app.services.auth.protocol import AuthServiceProtocol
from app.services.auth.local import LocalAuthService
from app.services.auth.http import HttpAuthService

def get_auth_service(settings: Settings = Depends(get_settings)) -> AuthServiceProtocol:
    if settings.AUTH_PROVIDER == "local":
        return LocalAuthService()
    elif settings.AUTH_PROVIDER == "http":
        return HttpAuthService(
            url=settings.AUTH_SERVICE_URL,
            api_key=settings.AUTH_API_KEY
        )

    # Default to local if unknown (or raise error)
    return LocalAuthService()
