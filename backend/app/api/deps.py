from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.db.session import get_db
from app.schemas.user import User as UserSchema
from app.services.user_service import UserService

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False  # We handle the error manually to check for query param
)


async def get_current_user(
    token: Annotated[Optional[str], Depends(reusable_oauth2)],
    token_query: Annotated[Optional[str], Query(alias="token")] = None,
    db: AsyncSession = Depends(get_db),
) -> UserSchema:
    # Prioritize Bearer token, then query param
    final_token = token or token_query

    if not final_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = security.verify_token(final_token)
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await UserService.get_by_user_id(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return UserSchema.model_validate(user)
