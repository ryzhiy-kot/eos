"""Protocol and registry for mock response handlers.

Implements the Strategy pattern (OCP) — new handlers can be registered
without modifying existing code.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass, field


@dataclass
class HandlerMatch:
    """Result of a keyword match check."""

    matched: bool
    priority: int = 0  # Higher = matched first when multiple handlers match


MockResponseHandler = Callable[[str, dict], AsyncGenerator[dict, None]]
MatchPredicate = Callable[[str], bool]


@dataclass
class RegisteredHandler:
    """A registered mock response handler with its metadata."""

    keywords: list[str]
    handler: MockResponseHandler
    priority: int = 0
    description: str = ""
    match_fn: MatchPredicate | None = None


class MockResponseRegistry:
    """Registry for mock response handlers.

    Handlers are matched against user messages by keyword or custom predicate.
    Handlers with custom match_fn are evaluated first, then keyword-based handlers.
    """

    def __init__(self) -> None:
        self._handlers: list[RegisteredHandler] = []

    def register(
        self,
        keywords: list[str],
        priority: int = 0,
        description: str = "",
        match_fn: MatchPredicate | None = None,
    ) -> Callable[[MockResponseHandler], MockResponseHandler]:
        """Decorator to register a mock response handler.

        Args:
            keywords: List of keywords that trigger this handler.
            priority: Match priority (higher = preferred when multiple match).
            description: Human-readable description of what this handler does.
            match_fn: Optional custom predicate for matching. If provided,
                      this is evaluated instead of keyword matching.

        Returns:
            Decorator function.
        """

        def decorator(func: MockResponseHandler) -> MockResponseHandler:
            self._handlers.append(
                RegisteredHandler(
                    keywords=keywords,
                    handler=func,
                    priority=priority,
                    description=description,
                    match_fn=match_fn,
                )
            )
            return func

        return decorator

    def get_handler(self, message: str) -> MockResponseHandler | None:
        """Find the best matching handler for the given message.

        Custom match_fn handlers are evaluated first, then keyword-based handlers.
        Among matches, highest priority wins.

        Args:
            message: User message (should be lowercased by caller).

        Returns:
            The matching handler function, or None if no match.
        """
        msg_lower = message.lower()
        matches: list[tuple[int, RegisteredHandler]] = []

        for registered in self._handlers:
            if registered.match_fn is not None:
                if registered.match_fn(message):
                    matches.append((registered.priority, registered))
            elif any(kw in msg_lower for kw in registered.keywords):
                matches.append((registered.priority, registered))

        if not matches:
            return None

        matches.sort(key=lambda x: x[0], reverse=True)
        return matches[0][1].handler

    def list_handlers(self) -> list[dict[str, str]]:
        """List all registered handlers with their metadata.

        Returns:
            List of dicts with 'keywords', 'description' keys.
        """
        return [
            {"keywords": h.keywords, "description": h.description}
            for h in self._handlers
        ]


# Global registry instance
registry = MockResponseRegistry()
