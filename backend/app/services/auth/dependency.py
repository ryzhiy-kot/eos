from fastapi import Depends
from app.core.config import get_settings, Settings
from app.services.auth.protocol import AuthServiceProtocol
from app.services.auth.local import LocalAuthService

def get_auth_service(settings: Settings = Depends(get_settings)) -> AuthServiceProtocol:
    if settings.AUTH_PROVIDER == "local":
        return LocalAuthService()
    # Placeholder for other providers
    # elif settings.AUTH_PROVIDER == "ldap":
    #     return LdapAuthService()

    # Default to local if unknown (or raise error)
    return LocalAuthService()
