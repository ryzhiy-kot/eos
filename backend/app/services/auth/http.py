from typing import Optional
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.services.user_service import UserService
from app.services.auth.protocol import AuthServiceProtocol

class HttpAuthService(AuthServiceProtocol):
    def __init__(self, url: str, api_key: str = ""):
        self.url = url
        self.api_key = api_key

    async def authenticate(
        self, db: AsyncSession, username: str, password: Optional[str] = None
    ) -> Optional[User]:
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
                    # The remote service should return user details.
                    # We expect at least a user_id matching the username or a specific ID.
                    # For now, we'll assume the remote confirms the 'username' is valid.

                    remote_user_id = data.get("user_id", username)
                    profile_data = data.get("profile", {})

                    # Sync with local DB
                    user = await UserService.get_by_user_id(db, remote_user_id)
                    if not user:
                         user = await UserService.create_user(db, remote_user_id, profile_data)
                         await db.commit()
                         # Re-fetch to ensure clean state
                         user = await UserService.get_by_user_id(db, remote_user_id)

                    return user

                elif response.status_code == 401 or response.status_code == 403:
                    return None
                else:
                    # Log error or handle unexpected status
                    print(f"Auth Service Error: {response.status_code} - {response.text}")
                    return None

        except httpx.RequestError as e:
            print(f"Auth Service Request Failed: {e}")
            return None
