from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import User as UserSchema
from app.services.user_service import UserService
from app.services.auth.protocol import AuthServiceProtocol, AuthResult
from datetime import datetime, timedelta, timezone
from app.core import security
from app.core.config import get_settings

settings = get_settings()

class LocalAuthService(AuthServiceProtocol):
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

            # Re-fetch to ensure loading options if needed (though new obj has empty memberships)
            user = await UserService.get_by_user_id(db, username)

        if user:
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            token = security.create_access_token(
                data={"sub": user.user_id}, expires_delta=access_token_expires
            )
            expires_at = datetime.now(timezone.utc) + access_token_expires

            return AuthResult(
                user=UserSchema.model_validate(user),
                session_token=token,
                session_expires_at=expires_at
            )

        return AuthResult(error="Authentication failed")

    async def logout(self, session_token: str) -> None:
        # JWTs are stateless, no server-side invalidation in this simple implementation
        pass
