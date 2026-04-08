"""Custom exception hierarchy for the application.

Domain-specific exceptions following the SRP — each exception represents
a specific category of error (authentication, authorization, data, etc.).

Usage:
    from app.exceptions import (
        FinAgentError,
        AuthenticationError,
        AuthorizationError,
        DataError,
        SessionError,
    )
"""

from __future__ import annotations


class FinAgentError(Exception):
    """Base exception for all FinAgent errors.

    All application-specific exceptions inherit from this class.
    """

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict:
        """Convert exception to dict for JSON responses."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class AuthenticationError(FinAgentError):
    """Raised when authentication fails (invalid credentials, token, etc.)."""


class AuthorizationError(FinAgentError):
    """Raised when user lacks permission for an operation."""


class TokenError(FinAgentError):
    """Raised when token is invalid, expired, or revoked."""


class SessionError(FinAgentError):
    """Raised when session operations fail (not found, invalid, etc.)."""


class ArtifactError(FinAgentError):
    """Raised when artifact operations fail."""


class DataError(FinAgentError):
    """Raised when data operations fail (invalid input, not found, etc.)."""


class AgentError(FinAgentError):
    """Raised when agent execution fails."""


class LLMError(AgentError):
    """Raised when LLM API calls fail."""


class CodeExecutionError(AgentError):
    """Raised when code execution fails (syntax error, timeout, etc.)."""


class ConfigurationError(FinAgentError):
    """Raised when configuration is invalid or missing."""


class DatabaseError(FinAgentError):
    """Raised when database operations fail."""