"""Execution context builder for agent code execution.

Constructs the namespace injected into the sandbox with bq.*, display.*,
and utility modules.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from .artifact_collector import ArtifactCollector
from .mock_data.generators import (
    mock_fx_rates,
    mock_interest_curves,
    mock_news,
    mock_pnl,
    mock_positions,
    mock_risk,
)

if TYPE_CHECKING:
    from collections.abc import Callable


class DotDict:
    """A dict-like object that allows attribute-style access.

    Wraps a dict and provides attribute access to keys while maintaining
    full dict interface compatibility.
    """

    __slots__ = ("_data",)

    def __init__(self, data: dict) -> None:
        object.__setattr__(self, "_data", data)

    def __getattr__(self, name: str):
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

    def __setattr__(self, name: str, value) -> None:
        self._data[name] = value

    def __getitem__(self, key: str):
        return self._data[key]

    def __setitem__(self, key: str, value) -> None:
        self._data[key] = value

    def __contains__(self, key: object) -> bool:
        return key in self._data

    def __dir__(self) -> list[str]:
        return list(self._data.keys())

    def __repr__(self) -> str:
        return f"DotDict({self._data!r})"

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()


def build_execution_context(
    user_id: str,
    conversation_history: list | None = None,
) -> tuple[dict, ArtifactCollector]:
    """Build the execution context injected into the agent sandbox.

    Args:
        user_id: Authenticated user identifier.
        conversation_history: Previous conversation messages.

    Returns:
        Tuple of (context dict, ArtifactCollector instance).
    """
    collector = ArtifactCollector()

    bq_functions: dict[str, Callable] = {
        "pnl": mock_pnl,
        "risk": mock_risk,
        "fx_rates": mock_fx_rates,
        "curves": mock_interest_curves,
        "positions": mock_positions,
        "news": mock_news,
    }

    context = {
        "bq": DotDict(bq_functions),
        "display": collector,
        "pd": None,
        "np": None,
        "json": json,
        "_user_id": user_id,
        "_history": conversation_history or [],
    }

    return context, collector
