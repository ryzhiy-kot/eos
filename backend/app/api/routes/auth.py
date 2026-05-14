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
    hash_password_sync,
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
        "password_hash": hash_password_sync("admin123"),
        "is_active": True,
    },
    "trader": {
        "id": TRADER_USER_ID,
        "email": "trader@company.com",
        "display_name": "Jane Trader",
        "role": "trader",
        "password_hash": hash_password_sync("trader123"),
        "is_active": True,
    },
}

MOCK_USERS_BY_ID = {user["id"]: user for user in MOCK_USERS.values()}


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User Login",
    description="Authenticate a user using LDAP or mock credentials and return access and refresh tokens."
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
        is_valid = await verify_password(request.password, user_data["password_hash"])
        if not is_valid:
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
    description="Exchange a valid refresh token for a new access token and refresh token."
)
async def refresh_token(refresh_token: str):
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    user_id = payload["sub"]
    user = MOCK_USERS_BY_ID.get(user_id)
    role = user["role"] if user else "trader"

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
    description="Retrieve the profile information of the currently authenticated user."
)
async def get_me(current_user: dict = Depends(get_current_user)):
    user_id = current_user["sub"]
    user = MOCK_USERS_BY_ID.get(user_id)
    if user:
        return UserResponse(
            id=user["id"],
            email=user["email"],
            display_name=user["display_name"],
            role=user["role"],
            is_active=user["is_active"],
            last_login=datetime.now(UTC),
        )
    raise HTTPException(status_code=404, detail="User not found")


@router.post(
    "/logout",
    response_model=dict,
    summary="User Logout",
    description="Invalidate the user's current access token."
)
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    invalidate_token(credentials.credentials)
    return {"message": "Logged out successfully"}
