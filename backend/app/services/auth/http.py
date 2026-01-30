import logging
from typing import Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from app.schemas.user import UserBase
from app.services.auth.protocol import AuthServiceProtocol
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class HttpAuthService(AuthServiceProtocol):
    def __init__(self):
        settings = get_settings()
        self.url = settings.AUTH_SERVICE_URL
        self.api_key = settings.AUTH_API_KEY

    async def authenticate(
        self, db: AsyncSession, username: str, password: Optional[str] = None
    ) -> Optional[Tuple[UserBase, str, datetime]]:
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
                    # Expect user data + session info
                    user = UserBase.model_validate(data.get("user"))
                    token = data.get("session_token")
                    expires_at = datetime.fromisoformat(data.get("session_expires_at"))
                    return user, token, expires_at
                elif response.status_code == 401:
                    logger.info(f"Authentication failed for user: {username}")
                    return None
                else:
                    logger.error(f"Auth Service Error: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Auth Service Exception: {e}")
            return None

    async def logout(self, session_token: str) -> None:
        # Optional: Call remote logout if supported
        pass
