from typing import Protocol, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserBase

class AuthServiceProtocol(Protocol):
    async def authenticate(
        self, db: AsyncSession, username: str, password: Optional[str] = None
    ) -> Optional[UserBase]:
        ...
