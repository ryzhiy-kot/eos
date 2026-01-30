from typing import Protocol, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserBase

class AuthServiceProtocol(Protocol):
    async def authenticate(
        self, db: AsyncSession, username: str, password: Optional[str] = None
    ) -> Optional[Tuple[UserBase, str, datetime]]:
        """
        Authenticates a user and returns a tuple of (UserBase, session_token, expires_at).
        """
        ...

    async def logout(self, session_token: str) -> None:
        """
        Invalidates the session token.
        """
        ...
