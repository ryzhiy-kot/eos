"""LLM agent factory — creates agents based on configuration.

Uses the BaseLLMAgent interface to enable swappable implementations.
Uses lazy imports to avoid importing unused provider modules.
"""

from __future__ import annotations

from typing import Any, List, Optional, Type

from ..agents.base import BaseLLMAgent
from ..config import get_settings
from ..core.logging import get_logger

logger = get_logger(__name__)


def create_llm_agent(
    name: str,
    instruction: str,
    description: Optional[str] = None,
    tools: Optional[List[Any]] = None,
    sub_agents: Optional[List[Any]] = None,
    input_schema: Optional[Type] = None,
    output_schema: Optional[Type] = None,
) -> BaseLLMAgent:
    """Factory to create an LLM agent based on configuration.

    Returns a BaseLLMAgent interface, enabling interchangeable implementations.
    Uses lazy imports - only imports the provider that is configured.

    Args:
        name: Agent identifier.
        instruction: System instruction for the agent.
        description: Optional human-readable description.
        tools: List of tools available to the agent.
        sub_agents: List of sub-agents (for event propagation).
        input_schema: Pydantic model for input validation.
        output_schema: Pydantic model for output validation.

    Returns:
        BaseLLMAgent instance (GroqAgent or GeminiAgent based on config).
    """
    settings = get_settings()
    provider = settings.LLM_PROVIDER.lower()

    if provider == "groq":
        from ..agents.adapters import create_groq_agent

        logger.info(
            "Creating GroqAgent '%s' with model '%s'", name, settings.LLM_MODEL
        )
        return create_groq_agent(
            name=name,
            instruction=instruction,
            description=description,
            tools=tools,
            sub_agents=sub_agents,
            model=settings.LLM_MODEL,
            api_key=settings.LLM_API_KEY or None,
        )

    if provider == "gemini":
        from ..agents.adapters import create_gemini_agent

        logger.info(
            "Creating GeminiAgent '%s' with model '%s'", name, settings.LLM_MODEL
        )
        return create_gemini_agent(
            name=name,
            instruction=instruction,
            description=description,
            tools=tools,
            sub_agents=sub_agents,
            model=settings.LLM_MODEL,
        )

    # Default fallback to Groq
    from ..agents.adapters import create_groq_agent

    logger.warning(
        "Unknown LLM provider '%s', defaulting to GroqAgent '%s' with model '%s'",
        provider,
        name,
        settings.LLM_MODEL,
    )
    return create_groq_agent(
        name=name,
        instruction=instruction,
        description=description,
        tools=tools,
        sub_agents=sub_agents,
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY or None,
    )