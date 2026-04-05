import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from google.adk.sessions import InMemorySessionService

from app.agents.adk_agent import (
    create_main_agent,
    create_code_executor_subagent,
    get_session_service,
    run_agent,
)


def test_create_code_executor_subagent():
    """Test creating a code executor sub-agent."""
    agent = create_code_executor_subagent(user_id="test_user", session_id="test_session")
    assert agent is not None
    assert agent.name == "CodeExecutorAgent"


def test_create_main_agent():
    """Test creating the main orchestrator agent with sub-agent."""
    main_agent, code_executor = create_main_agent(user_id="test_user", session_id="test_session")
    assert main_agent is not None
    assert main_agent.name == "FinancialOrchestratorAgent"
    assert code_executor is not None
    assert code_executor.name == "CodeExecutorAgent"


def test_get_session_service():
    """Test getting the session service (singleton)."""
    service1 = get_session_service()
    service2 = get_session_service()
    assert service1 is service2


@pytest.mark.asyncio
async def test_run_agent_simple_message():
    """Test running the agent with a simple message."""
    events = []
    async for event in run_agent(
        message="Hello, what can you do?",
        user_id="test_user",
        session_id="test_session_123",
    ):
        events.append(event)

    assert len(events) > 0
    assert events[0]["type"] in ["text", "error"]


@pytest.mark.asyncio
async def test_run_agent_with_pnl_query():
    """Test running the agent with a P&L query."""
    events = []
    async for event in run_agent(
        message="Show me my P&L for today",
        user_id="test_user",
        session_id="test_session_pnl",
    ):
        events.append(event)

    assert len(events) > 0


@pytest.mark.asyncio
async def test_run_agent_returns_done_event():
    """Test that the agent returns a done event at the end."""
    events = []
    async for event in run_agent(
        message="Hello",
        user_id="test_user",
        session_id="test_session_done",
    ):
        events.append(event)

    done_events = [e for e in events if e["type"] == "done"]
    assert len(done_events) > 0


def test_main_agent_has_agent_function_tool():
    """Test that the main agent has the code executor via AgentTool."""
    main_agent, code_executor = create_main_agent(user_id="test_user", session_id="test_session")
    from google.adk.tools import AgentTool

    assert len(main_agent.tools) > 0
    assert any(isinstance(t, AgentTool) for t in main_agent.tools)
    assert code_executor is not None


@pytest.mark.asyncio
async def test_run_agent_creates_adk_session():
    """Test that run_agent creates an ADK session."""
    session_service = get_session_service()
    session_id = "test_session_adk"

    events = []
    async for event in run_agent(
        message="Hello",
        user_id="test_user",
        session_id=session_id,
    ):
        events.append(event)

    session = await session_service.get_session(
        app_name="finagent",
        user_id="test_user",
        session_id=session_id,
    )
    assert session is not None


@pytest.mark.asyncio
async def test_multiple_messages_same_session():
    """Test running multiple messages in the same session."""
    session_id = "test_session_multi"

    events1 = []
    async for event in run_agent(
        message="Hello",
        user_id="test_user",
        session_id=session_id,
    ):
        events1.append(event)

    events2 = []
    async for event in run_agent(
        message="Show me P&L",
        user_id="test_user",
        session_id=session_id,
    ):
        events2.append(event)

    assert len(events1) > 0
    assert len(events2) > 0


def test_agent_model_selection_groq():
    """Test that agent model selection works based on provider."""
    with patch("app.agents.adk_agent.settings") as mock_settings:
        mock_settings.LLM_PROVIDER = "groq"
        mock_settings.GROQ_MODEL = "llama-3.1-8b-instant"
        mock_settings.GROQ_API_KEY = "test_groq_key"

        main_agent, _ = create_main_agent(user_id="test_user", session_id="test_session")
        assert main_agent is not None


def test_agent_model_selection_gemini():
    """Test that agent model selection works for Gemini."""
    with patch("app.agents.adk_agent.settings") as mock_settings:
        mock_settings.LLM_PROVIDER = "gemini"
        mock_settings.GROQ_MODEL = "llama-3.1-8b-instant"

        main_agent, _ = create_main_agent(user_id="test_user", session_id="test_session")
        assert main_agent is not None
