import asyncio
from datetime import UTC, datetime, timedelta

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from ..config import get_settings

settings = get_settings()
security = HTTPBearer()

# In-memory token blacklist (use Redis in production)
token_blacklist: set[str] = set()


def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "role": role, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": user_id, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    if token in token_blacklist:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def invalidate_token(token: str) -> None:
    """Add token to blacklist to invalidate it."""
    token_blacklist.add(token)
    # Clean up expired tokens periodically (simplified)
    if len(token_blacklist) > 1000:
        token_blacklist.clear()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    return payload


def hash_password_sync(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password_sync(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


async def hash_password(password: str) -> str:
    return await asyncio.to_thread(hash_password_sync, password)


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return await asyncio.to_thread(verify_password_sync, plain_password, hashed_password)


def _ldap_bind_and_search(server, user_dn, password, username, search_base):
    from ldap3 import Connection
    conn = Connection(
        server,
        user=f"{user_dn},{search_base}",
        password=password,
        auto_bind=True,
    )
    conn.search(
        search_base,
        f"(uid={username})",
        attributes=["mail", "cn", "uid"],
    )
    return conn


async def ldap_authenticate(username: str, password: str) -> dict | None:
    """Authenticate against LDAP server. Returns user info dict or None."""
    try:
        from ldap3 import ALL, Server

        server = Server(settings.LDAP_SERVER, get_info=ALL)
        user_dn = settings.LDAP_USER_SEARCH_FILTER.format(username=username)

        # Try to bind with user credentials and search, executed in thread
        conn = await asyncio.to_thread(
            _ldap_bind_and_search,
            server,
            user_dn,
            password,
            username,
            settings.LDAP_USER_SEARCH_BASE,
        )

        if not conn.entries:
            conn.unbind()
            return None

        entry = conn.entries[0]
        conn.unbind()

        return {
            "username": str(entry.uid) if hasattr(entry, "uid") else username,
            "email": str(entry.mail) if hasattr(entry, "mail") else f"{username}@company.com",
            "display_name": str(entry.cn) if hasattr(entry, "cn") else username,
        }
    except Exception:
        return None
