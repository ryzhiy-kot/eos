import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import User as UserSchema, UserBase
from app.services.user_service import UserService
from app.services.auth.protocol import AuthServiceProtocol

# In-memory session store for local development
# In production, this should be in Redis or DB
_LOCAL_SESSIONS: Dict[str, datetime] = {}

class LocalAuthService(AuthServiceProtocol):
    async def authenticate(
        self, db: AsyncSession, username: str, password: Optional[str] = None
    ) -> Optional[Tuple[UserBase, str, datetime]]:
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
            # Generate Session
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
            _LOCAL_SESSIONS[token] = expires_at

            return UserSchema.model_validate(user), token, expires_at

        return None

    async def logout(self, session_token: str) -> None:
        if session_token in _LOCAL_SESSIONS:
            del _LOCAL_SESSIONS[session_token]
