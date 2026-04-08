"""Dependency injection providers for services.

Provides FastAPI Depends() factories for all services,
enabling proper DI and testability.
"""

from __future__ import annotations

from functools import lru_cache

from .session_service import SessionService, get_session_service


@lru_cache
def get_session_service_dep() -> SessionService:
    """Get the SessionService singleton for dependency injection."""
    return get_session_service()


def get_current_user_dep():
    """Get the current authenticated user (placeholder for auth service)."""
    from .auth import get_current_user

    return get_current_user
