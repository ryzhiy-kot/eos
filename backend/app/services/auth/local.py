from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import User as UserSchema, UserBase
from app.services.user_service import UserService
from app.services.auth.protocol import AuthServiceProtocol

class LocalAuthService(AuthServiceProtocol):
    async def authenticate(
        self, db: AsyncSession, username: str, password: Optional[str] = None
    ) -> Optional[UserBase]:
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
            return UserSchema.model_validate(user)
        return None
