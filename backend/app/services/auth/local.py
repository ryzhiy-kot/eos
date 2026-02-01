from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import User as UserSchema, UserBase
from app.services.user_service import UserService
from app.services.auth.protocol import AuthServiceProtocol, AuthResult
from app.core.config import get_settings
import jwt
from datetime import datetime, timedelta, timezone

class LocalAuthService(AuthServiceProtocol):
    def __init__(self):
        self.settings = get_settings()

    def _create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.settings.SECRET_KEY, algorithm=self.settings.ALGORITHM)
        return encoded_jwt

    async def authenticate(
        self, db: AsyncSession, username: str, password: Optional[str] = None
    ) -> AuthResult:
        # Simple auth logic compatible with current implementation
        user = await UserService.get_by_user_id(db, username)

        if not user:
            # Fallback logic for admin or auto-registration
            if username == "admin":
                user = await UserService.create_user(
                    db, "admin", {"name": "Administrator"}
                )
                # Commit to ensure ID is generated for subsequent steps
                await db.commit()
            else:
                # Auto-register
                user = await UserService.create_user(db, username, {"name": username})
                await db.commit()

            # Re-fetch to ensure loading options if needed
            user = await UserService.get_by_user_id(db, username)

        if user:
            access_token_expires = timedelta(hours=24)
            access_token = self._create_access_token(
                data={"sub": user.user_id}, expires_delta=access_token_expires
            )
            expires_at = datetime.now(timezone.utc) + access_token_expires

            return AuthResult(
                user=UserSchema.model_validate(user),
                session_token=access_token,
                session_expires_at=expires_at
            )

        return AuthResult(error="Authentication failed")

    async def validate_token(self, token: str, db: AsyncSession) -> Optional[UserBase]:
        try:
            payload = jwt.decode(token, self.settings.SECRET_KEY, algorithms=[self.settings.ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
        except jwt.PyJWTError:
            return None

        user = await UserService.get_by_user_id(db, user_id)
        if user:
            return UserSchema.model_validate(user)
        return None

    async def logout(self, session_token: str) -> None:
        # Stateless JWTs cannot be invalidated without a blacklist.
        # For this scope, we accept client-side discard.
        pass
