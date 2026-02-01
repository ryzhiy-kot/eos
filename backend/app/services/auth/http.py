import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from app.schemas.user import UserBase, User as UserSchema
from app.services.auth.protocol import AuthServiceProtocol, AuthResult
from app.services.user_service import UserService
from app.core.config import get_settings
from datetime import datetime, timezone, timedelta
import jwt

logger = logging.getLogger(__name__)

class HttpAuthService(AuthServiceProtocol):
    def __init__(self):
        self.settings = get_settings()
        self.url = self.settings.AUTH_SERVICE_URL
        self.api_key = self.settings.AUTH_API_KEY

    async def authenticate(
        self, db: AsyncSession, username: str, password: Optional[str] = None
    ) -> AuthResult:
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Support both form data (OAuth2) and JSON depending on upstream?
        # Current implementation sends JSON. We'll stick to JSON for the upstream request unless specified.
        payload = {"username": username, "password": password}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.url,
                    data=payload,
                    headers=headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()

                    # Adapt to OAuth2 or custom response
                    token = data.get("access_token") or data.get("session_token")

                    expires_at = None
                    if "expires_in" in data:
                        expires_at = datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"])
                    elif "session_expires_at" in data:
                        val = data["session_expires_at"]
                        if isinstance(val, str):
                            try:
                                expires_at = datetime.fromisoformat(val)
                            except ValueError:
                                pass

                    # If we don't have user info in response, we might need to fetch it or create a stub
                    # But the protocol says we return a UserBase.
                    # We try to validate from data
                    try:
                        user = UserBase.model_validate(data)
                    except Exception:
                        # If data doesn't match UserBase, maybe we use the username provided
                        user = UserBase(user_id=username, enabled=True)

                    return AuthResult(
                        user=user,
                        session_token=token,
                        session_expires_at=expires_at,
                        extra_info=data
                    )
                elif response.status_code == 401:
                    logger.info(f"Authentication failed for user: {username}")
                    return AuthResult(error="Authentication failed")
                else:
                    logger.error(f"Auth Service Error: {response.status_code} - {response.text}")
                    return AuthResult(error=f"Remote Auth Error: {response.status_code}")
        except Exception as e:
            logger.error(f"Auth Service Exception: {e}")
            return AuthResult(error=str(e))

    async def validate_token(self, token: str, db: AsyncSession) -> Optional[UserBase]:
        # Try to validate locally using shared secret
        try:
            payload = jwt.decode(token, self.settings.SECRET_KEY, algorithms=[self.settings.ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id:
                # We trust the token, now get/sync user locally
                user = await UserService.get_by_user_id(db, user_id)
                if not user:
                    # Auto-create if valid token but no local user?
                    # Or return None? Protocol implies checking valid session.
                    # LocalAuthService creates user on login. Validate just checks existence.
                    return None
                return UserSchema.model_validate(user)
        except jwt.PyJWTError:
            pass

        # If local validation fails (maybe opaque token?), we could try calling an introspection endpoint
        # But we don't have a configured introspection URL.
        # Fallback: Assume invalid.
        return None

    async def logout(self, session_token: str) -> None:
        logger.info(f"Logout requested for token: {session_token} (HttpAuthService - No-op)")
