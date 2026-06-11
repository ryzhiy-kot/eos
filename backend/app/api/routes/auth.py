from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ...config import get_settings
from ...schemas import LoginRequest, TokenResponse, UserResponse
from ...services.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    invalidate_token,
    ldap_authenticate,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()
security = HTTPBearer()

# Fixed UUIDs for consistent user IDs across restarts
TRADER_USER_ID = "550e8400-e29b-41d4-a716-446655440000"
ADMIN_USER_ID = "550e8400-e29b-41d4-a716-446655440001"

# In-memory user store for mock mode (replace with DB in production)
MOCK_USERS = {
    "admin": {
        "id": ADMIN_USER_ID,
        "email": "admin@company.com",
        "display_name": "Admin User",
        "role": "admin",
        "password_hash": "$2b$12$hlWOtQZYxhOHFy0i4VTHf.D8yeikXgf6umtmVDt94.nI3x39Y78By",
        "is_active": True,
    },
    "trader": {
        "id": TRADER_USER_ID,
        "email": "trader@company.com",
        "display_name": "Jane Trader",
        "role": "trader",
        "password_hash": "$2b$12$Kp/jkd6rMAItfSy1bUNPxOtebCPZNwq0k/Ab75owhidMRsV5rEZSO",
        "is_active": True,
    },
}


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
    description="Authenticate user with LDAP or mock credentials and return JWT tokens.",
)
async def login(request: LoginRequest):
    # Try LDAP first, fallback to mock users
    ldap_user = await ldap_authenticate(request.username, request.password)
    if ldap_user:
        user_data = {
            "id": str(uuid4()),
            "email": ldap_user["email"],
            "display_name": ldap_user["display_name"],
            "role": "trader",
            "is_active": True,
        }
    elif request.username in MOCK_USERS:
        user_data = MOCK_USERS[request.username]
        if not await verify_password(request.password, user_data["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    access_token = create_access_token(user_data["id"], user_data["role"])
    refresh_token = create_refresh_token(user_data["id"])

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh Token",
    description="Get a new access token using a valid refresh token.",
)
async def refresh_token(refresh_token: str):
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    user_id = payload["sub"]
    # Find user role (simplified)
    role = "trader"
    for u in MOCK_USERS.values():
        if u["id"] == user_id:
            role = u["role"]
            break

    access_token = create_access_token(user_id, role)
    new_refresh_token = create_refresh_token(user_id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User",
    description="Retrieve information about the currently authenticated user.",
)
async def get_me(current_user: dict = Depends(get_current_user)):
    user_id = current_user["sub"]
    for u in MOCK_USERS.values():
        if u["id"] == user_id:
            return UserResponse(
                id=u["id"],
                email=u["email"],
                display_name=u["display_name"],
                role=u["role"],
                is_active=u["is_active"],
                last_login=datetime.now(UTC),
            )
    raise HTTPException(status_code=404, detail="User not found")


from pydantic import BaseModel

class LogoutResponse(BaseModel):
    message: str

@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout",
    description="Invalidate the current token.",
)
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    invalidate_token(credentials.credentials)
    return LogoutResponse(message="Logged out successfully")
