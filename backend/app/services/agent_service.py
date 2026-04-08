"""Agent service — orchestrates agent message processing and mock responses.

Responsibilities:
- Route real agent messages to the LLM provider
- Route mock messages through the handler registry (Strategy pattern)
- Persist artifacts to the session service

The mock response logic is delegated to handlers in app/services/mock_responses/.
Adding a new response type requires only registering a new handler — no changes
to this file (Open/Closed Principle).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from app.config import get_settings
from app.core.logging import get_logger
from .context_injector import build_execution_context
from .mock_responses.registry import registry
from .session_service import SessionService

# Import all handlers so they register themselves
import app.services.mock_responses.handler_pnl  # noqa: F401
import app.services.mock_responses.handler_risk  # noqa: F401
import app.services.mock_responses.handler_curves  # noqa: F401
import app.services.mock_responses.handler_fx  # noqa: F401
import app.services.mock_responses.handler_positions  # noqa: F401
import app.services.mock_responses.handler_news  # noqa: F401
import app.services.mock_responses.handler_report  # noqa: F401

logger = get_logger(__name__)

FALLBACK_RESPONSE = """I can help you analyze:

- **P&L**: Ask "What's my P&L?" or "Show me profit by desk"
- **Risk**: Ask "What's my risk?" or "Show VaR and Greeks"
- **FX Rates**: Ask "Show me FX rates" or "What's EURUSD?"
- **Interest Curves**: Ask "Show interest rate curves"
- **Positions**: Ask "Show my positions" or "What books do I have?"
- **Market News**: Ask "Any market news?"
- **Reports**: Ask "Generate a PDF report"

*Note: Using mock data for demonstration.*

Try asking: "What's my P&L today?" or "Show me risk for FX desk"
"""


async def _persist_artifacts(
    session_service: SessionService,
    session_id: str,
    artifacts: list[dict],
) -> None:
    """Persist all collected artifacts to the session store."""
    for artifact in artifacts:
        await session_service.save_artifact(
            session_id=session_id,
            artifact_type=artifact.get("type", "unknown"),
            title=artifact.get("title"),
            spec=artifact.get("spec"),
            columns=artifact.get("columns"),
            data=artifact.get("data"),
            content=artifact.get("content"),
            format=artifact.get("format"),
        )


async def process_agent_message(
    message: str,
    user_id: str,
    session_id: str,
) -> AsyncGenerator[dict, None]:
    """Process a message via the real LLM agent.

    Args:
        message: User message text.
        user_id: Authenticated user ID.
        session_id: Session identifier.

    Yields:
        Event dicts from the LLM agent.
    """
    try:
        from app.agents.adk_agent import run_agent

        async for event in run_agent(
            message=message,
            user_id=user_id,
            session_id=session_id,
        ):
            yield event

    except Exception as e:
        logger.error("Error processing agent message: %s", e, exc_info=True)
        yield {"type": "error", "content": str(e)}


async def generate_mock_response(
    message: str,
    user_id: str,
    session_id: str,
    session_service: SessionService,
) -> AsyncGenerator[dict, None]:
    """Generate a mock response using the handler registry.

    Args:
        message: User message text.
        user_id: Authenticated user ID (unused in mock mode).
        session_id: Session identifier for artifact persistence.
        session_service: Service for persisting artifacts.

    Yields:
        Event dicts (text, chart, table, pdf, error, done).
    """
    exec_context, collector = build_execution_context(user_id, [])

    handler = registry.get_handler(message)
    if handler is not None:
        async for event in handler(message, {"collector": collector, "bq": exec_context["bq"]}):
            yield event
    else:
        yield {"type": "text", "content": FALLBACK_RESPONSE}

    await _persist_artifacts(session_service, session_id, collector.artifacts)
    yield {"type": "done", "artifacts": collector.artifacts}


async def chat_stream(
    message: str,
    user_id: str,
    session_id: str,
    session_service: SessionService,
) -> AsyncGenerator[dict, None]:
    """Public API for the chat endpoint.

    Routes to mock or real agent based on DEMO_MODE setting.

    Args:
        message: User message text.
        user_id: Authenticated user ID.
        session_id: Session identifier.
        session_service: Service for session and artifact management.

    Yields:
        Event dicts from the selected agent.
    """
    settings = get_settings()

    if settings.DEMO_MODE:
        async for event in generate_mock_response(
            message=message,
            user_id=user_id,
            session_id=session_id,
            session_service=session_service,
        ):
            yield event
    else:
        async for event in process_agent_message(
            message=message,
            user_id=user_id,
            session_id=session_id,
        ):
            yield event
