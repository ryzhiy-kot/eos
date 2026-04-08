"""Adapter to make GroqAgent conform to BaseLLMAgent interface."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from .base import BaseLLMAgent
from .groq_agent import GroqAgent as GroqAgentImpl


class GroqAgentAdapter(BaseLLMAgent):
    """Adapter that wraps GroqAgent to implement BaseLLMAgent.

    This allows GroqAgent to be used wherever BaseLLMAgent is expected,
    enabling interchangeability with other LLM providers.
    """

    def __init__(self, agent: GroqAgentImpl) -> None:
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
        # Note: Full implementation would need to integrate with ADK runner
        # For now, this shows the interface pattern
        yield {"type": "text", "content": f"GroqAgent: {message}"}


def create_groq_agent(
    name: str,
    instruction: str,
    description: str | None = None,
    tools: list[Any] | None = None,
    model: str = "llama-3.1-8b-instant",
    api_key: str | None = None,
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
    groq_agent = GroqAgentImpl(
        name=name,
        instruction=instruction,
        description=description,
        tools=tools or [],
        model=model,
        api_key=api_key,
    )
    return GroqAgentAdapter(groq_agent)