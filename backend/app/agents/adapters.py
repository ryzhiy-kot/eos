"""Adapters for different LLM providers.

This module provides factory functions to create agents based on configuration.
Uses lazy imports to avoid importing unused provider modules.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any, List, Optional

from .base import BaseLLMAgent


class GroqAgentAdapter(BaseLLMAgent):
    """Adapter that wraps GroqAgent to implement BaseLLMAgent.

    This allows GroqAgent to be used wherever BaseLLMAgent is expected,
    enabling interchangeability with other LLM providers.
    """

    def __init__(self, agent: Any) -> None:
        self._agent = agent

    @property
    def name(self) -> str:
        return self._agent.name

    @property
    def model(self) -> str:
        return self._agent.model

    async def run(
        self,
        message: str,
        user_id: str,
        session_id: str,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Run the GroqAgent and convert ADK events to dict format.

        This is a placeholder - the actual implementation would need to
        integrate with the ADK runner to stream events.
        """
        yield {"type": "text", "content": f"GroqAgent: {message}"}


class GeminiAgentAdapter(BaseLLMAgent):
    """Adapter for Google's LlmAgent from ADK.

    Uses Google's built-in LlmAgent which supports sub_agents for event propagation.
    """

    def __init__(self, agent: Any) -> None:
        self._agent = agent

    @property
    def name(self) -> str:
        return self._agent.name

    @property
    def model(self) -> str:
        return self._agent.model

    async def run(
        self,
        message: str,
        user_id: str,
        session_id: str,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Run the GeminiAgent and convert ADK events to dict format."""
        yield {"type": "text", "content": f"GeminiAgent: {message}"}


def create_groq_agent(
    name: str,
    instruction: str,
    description: Optional[str] = None,
    tools: Optional[List[Any]] = None,
    sub_agents: Optional[List[Any]] = None,
    model: str = "llama-3.1-8b-instant",
    api_key: Optional[str] = None,
) -> BaseLLMAgent:
    """Factory function to create a GroqAgent conforming to BaseLLMAgent.

    Usage:
        agent = create_groq_agent(
            name="FinanceAgent",
            instruction="You are a financial analyst...",
            tools=[...],
        )
        async for event in agent.run("What's my P&L?", user_id, session_id):
            print(event)
    """
    from .groq_agent import GroqAgent as GroqAgentImpl

    groq_agent = GroqAgentImpl(
        name=name,
        instruction=instruction,
        description=description,
        tools=tools or [],
        sub_agents=sub_agents or [],
        model=model,
        api_key=api_key,
    )
    return GroqAgentAdapter(groq_agent)


def create_gemini_agent(
    name: str,
    instruction: str,
    description: Optional[str] = None,
    tools: Optional[List[Any]] = None,
    sub_agents: Optional[List[Any]] = None,
    model: str = "gemini-2.0-flash",
) -> BaseLLMAgent:
    """Factory function to create a Gemini LlmAgent conforming to BaseLLMAgent.

    Uses Google's built-in LlmAgent from ADK, which supports sub_agents for
    proper event propagation from sub-agents.

    Usage:
        agent = create_gemini_agent(
            name="FinanceAgent",
            instruction="You are a financial analyst...",
            sub_agents=[code_executor_agent],
        )
        async for event in agent.run("What's my P&L?", user_id, session_id):
            print(event)
    """
    from google.adk.agents import LlmAgent

    gemini_agent = LlmAgent(
        name=name,
        model=model,
        instruction=instruction,
        description=description,
        tools=tools or [],
        sub_agents=sub_agents or [],
    )
    return GeminiAgentAdapter(gemini_agent)