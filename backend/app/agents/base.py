"""Abstract base class for LLM agents.

Defines the interface that all LLM agent implementations must follow.
This enables interchangeable agent implementations (Groq, Gemini, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any


class BaseLLMAgent(ABC):
    """Abstract base class for LLM agents.

    All agent implementations must provide:
    - async run(): Execute the agent with a message
    - name: Agent identifier
    - model: Model name being used

    This interface enables:
    - Swappable LLM providers (LSP)
    - Dependency injection of agents (DIP)
    - Testing with mock agents
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the agent's name identifier."""

    @property
    @abstractmethod
    def model(self) -> str:
        """Return the model name being used."""

    @abstractmethod
    async def run(
        self,
        message: str,
        user_id: str,
        session_id: str,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Run the agent with a user message.

        Args:
            message: User input message.
            user_id: Authenticated user identifier.
            session_id: Session for conversation context.

        Yields:
            Event dicts with keys: type (text, chart, table, etc.), content, etc.
        """
        pass