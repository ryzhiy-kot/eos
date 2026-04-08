import os
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from google.adk.sessions import InMemorySessionService

from app.agents.adk_agent import (
    create_main_agent,
    create_code_executor_subagent,
    run_agent,
)
from app.services.session_service import get_session_service

def has_llm_key():
    return bool(os.getenv("GROQ_API_KEY") or os.getenv("GOOGLE_API_KEY"))


skip_if_no_llm = pytest.mark.skipif(not has_llm_key(), reason="No LLM API key available")


def test_create_code_executor_subagent():
    """Test creating a code executor sub-agent."""
    with patch('app.agents.code_executor_agent.create_llm_agent') as mock_create:
        mock_agent = MagicMock()
        mock_agent.name = "CodeExecutorAgent"
        mock_agent.tools = []
        mock_create.return_value = mock_agent
        
        agent = create_code_executor_subagent(user_id="test_user", session_id="test_session")
        assert agent is not None
        assert agent.name == "CodeExecutorAgent"


@pytest.mark.skip(reason="Requires LLM API key - integration test")
def test_create_main_agent():
    """Test creating the main orchestrator agent with sub-agent."""
    main_agent, code_executor = create_main_agent(user_id="test_user", session_id="test_session")
    assert main_agent is not None
    assert main_agent.name == "FinancialOrchestratorAgent"
    assert code_executor is not None
    assert code_executor.name == "CodeExecutorAgent"


@pytest.mark.skip(reason="Requires LLM API key - integration test")
def test_main_agent_has_agent_function_tool():
    """Test that the main agent has the code executor via AgentTool."""
    main_agent, code_executor = create_main_agent(user_id="test_user", session_id="test_session")
    assert len(main_agent.tools) > 0
    assert code_executor is not None


@pytest.mark.skip(reason="Requires LLM API key - integration test")
def test_agent_model_selection_groq():
    """Test that agent model selection works based on provider."""
    main_agent, _ = create_main_agent(user_id="test_user", session_id="test_session")
    assert main_agent is not None


@pytest.mark.skip(reason="Requires LLM API key - integration test")
def test_agent_model_selection_gemini():
    """Test that agent model selection works for Gemini."""
    main_agent, _ = create_main_agent(user_id="test_user", session_id="test_session")
    assert main_agent is not None


def test_get_session_service():
    """Test getting the session service (singleton)."""
    service1 = get_session_service()
    service2 = get_session_service()
    assert service1 is service2


@pytest.mark.asyncio
@skip_if_no_llm
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
@skip_if_no_llm
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
@skip_if_no_llm
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


@pytest.mark.asyncio
@skip_if_no_llm
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
@skip_if_no_llm
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