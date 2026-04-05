import logging
from typing import Any

from google.adk.agents import LlmAgent
from pydantic import BaseModel

from app.agents.groq_agent import GroqAgent
from app.config import get_settings

logger = logging.getLogger(__name__)


def create_llm_agent(
    name: str,
    instruction: str,
    description: str | None = None,
    tools: list[Any] | None = None,
    input_schema: type[BaseModel] | None = None,
    output_schema: type[BaseModel] | None = None,
) -> Any:
    """Factory to create an LLM agent based on unified configuration.

    Uses unified settings (LLM_API_KEY, LLM_MODEL) if provided, otherwise
    falls back to provider-specific settings.
    """
    settings = get_settings()

    # Determine which provider to use
    provider = settings.LLM_PROVIDER.lower()

    # Unify config: prioritize LLM_API_KEY / LLM_MODEL, fallback to provider specifics
    if provider == "groq":
        api_key = settings.LLM_API_KEY
        model = settings.LLM_MODEL
        agent_class = GroqAgent
    else:
        # Default to Gemini
        api_key = settings.LLM_API_KEY
        model = settings.LLM_MODEL
        agent_class = LlmAgent

    logger.info(
        f"Creating {agent_class.__name__} '{name}' using provider '{provider}' and model '{model}'"
    )

    agent_kwargs = {
        "name": name,
        "model": model,
        "instruction": instruction,
        "description": description or f"Agent {name}",
        "tools": tools or [],
    }

    # Optional schemas
    if input_schema:
        agent_kwargs["input_schema"] = input_schema
    if output_schema:
        agent_kwargs["output_schema"] = output_schema

    # Special handling for local API keys if needed (though agents handle env fallback)
    if api_key:
        agent_kwargs["api_key"] = api_key

    return agent_class(**agent_kwargs)
