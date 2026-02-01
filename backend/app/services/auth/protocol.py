from typing import Protocol, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserBase
from pydantic import BaseModel
from datetime import datetime

class AuthResult(BaseModel):
    user: Optional[UserBase] = None
    session_token: Optional[str] = None
    session_expires_at: Optional[datetime] = None
    error: Optional[str] = None
    extra_info: Dict = {}

class AuthServiceProtocol(Protocol):
    async def authenticate(
        self, db: AsyncSession, username: str, password: Optional[str] = None
    ) -> AuthResult:
        ...

    async def validate_token(self, token: str, db: AsyncSession) -> Optional[UserBase]:
        ...

    async def logout(self, session_token: str) -> None:
        ...
