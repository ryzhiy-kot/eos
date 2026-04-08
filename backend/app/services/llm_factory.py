"""LLM agent factory — creates agents based on configuration.

Uses the BaseLLMAgent interface to enable swappable implementations.
"""

from __future__ import annotations

from typing import Any

from app.agents.adapters import create_groq_agent
from app.agents.base import BaseLLMAgent
from app.agents.groq_agent import GroqAgent
from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_llm_agent(
    name: str,
    instruction: str,
    description: str | None = None,
    tools: list[Any] | None = None,
    input_schema: type | None = None,
    output_schema: type | None = None,
) -> BaseLLMAgent:
    """Factory to create an LLM agent based on configuration.

    Returns a BaseLLMAgent interface, enabling interchangeable implementations.

    Args:
        name: Agent identifier.
        instruction: System instruction for the agent.
        description: Optional human-readable description.
        tools: List of tools available to the agent.
        input_schema: Pydantic model for input validation.
        output_schema: Pydantic model for output validation.

    Returns:
        BaseLLMAgent instance (GroqAdapter or future providers).
    """
    settings = get_settings()
    provider = settings.LLM_PROVIDER.lower()

    if provider == "groq":
        logger.info(
            "Creating GroqAgent '%s' with model '%s'", name, settings.LLM_MODEL
        )
        return create_groq_agent(
            name=name,
            instruction=instruction,
            description=description,
            tools=tools,
            model=settings.LLM_MODEL,
            api_key=settings.LLM_API_KEY or None,
        )

    # Default: Create GroqAgent (can be extended for Gemini, Claude, etc.)
    logger.info(
        "Creating default GroqAgent '%s' with model '%s'", name, settings.LLM_MODEL
    )
    return create_groq_agent(
        name=name,
        instruction=instruction,
        description=description,
        tools=tools,
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY or None,
    )