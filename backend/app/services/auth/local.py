from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import User as UserSchema
from app.services.user_service import UserService
from app.services.auth.protocol import AuthServiceProtocol, AuthResult
import secrets
from datetime import datetime, timedelta

# In-memory session store
SESSIONS: Dict[str, datetime] = {}

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
            token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=24)
            SESSIONS[token] = expires_at

            return AuthResult(
                user=UserSchema.model_validate(user),
                session_token=token,
                session_expires_at=expires_at
            )

        return AuthResult(error="Authentication failed")

    async def logout(self, session_token: str) -> None:
        if session_token in SESSIONS:
            del SESSIONS[session_token]
