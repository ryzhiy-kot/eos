import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from app.schemas.user import UserBase
from app.services.auth.protocol import AuthServiceProtocol, AuthResult
from app.core.config import get_settings
from datetime import datetime

logger = logging.getLogger(__name__)

class HttpAuthService(AuthServiceProtocol):
    def __init__(self):
        settings = get_settings()
        self.url = settings.AUTH_SERVICE_URL
        self.api_key = settings.AUTH_API_KEY

    async def authenticate(
        self, db: AsyncSession, username: str, password: Optional[str] = None
    ) -> AuthResult:
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {"username": username, "password": password}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.url,
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    # Expect compatible UserBase data
                    user = UserBase.model_validate(data)

                    token = data.get("session_token")
                    expires_at = data.get("session_expires_at")

                    if expires_at and isinstance(expires_at, str):
                        try:
                            expires_at = datetime.fromisoformat(expires_at)
                        except ValueError:
                            expires_at = None

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

    async def logout(self, session_token: str) -> None:
        logger.info(f"Logout requested for token: {session_token} (HttpAuthService - No-op)")
