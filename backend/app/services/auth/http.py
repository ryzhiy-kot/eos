import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from app.schemas.user import UserBase
from app.services.auth.protocol import AuthServiceProtocol, AuthResult
from app.core.config import get_settings
from datetime import datetime, timedelta, timezone

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

        # Send as Form Data (OAuth2 standard for password grant)
        data_payload = {"username": username, "password": password}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.url,
                    data=data_payload,
                    headers=headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()

                    # Expect access_token in response
                    token = data.get("access_token")
                    token_type = data.get("token_type") # e.g. "bearer"

                    # Try to get user from nested 'user' key first
                    user_data = data.get("user")

                    user = None
                    if user_data and isinstance(user_data, dict):
                         # If user_id is missing, inject it from login args
                         if "user_id" not in user_data:
                             user_data["user_id"] = username
                         try:
                             user = UserBase.model_validate(user_data)
                         except Exception as e:
                             logger.warning(f"Failed to validate user from 'user' field: {e}")

                    # If no user found or validation failed, try constructing from root if it looks like a user
                    if not user:
                         # Check if root has user_id
                         if "user_id" in data:
                             try:
                                 user = UserBase.model_validate(data)
                             except Exception as e:
                                 logger.warning(f"Failed to validate user from root: {e}")

                    # Fallback: Create minimal user
                    if not user:
                        user = UserBase(user_id=username, name=username)


                    # Calculate expiry
                    expires_in = data.get("expires_in")
                    expires_at = None
                    if expires_in:
                         expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)


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
