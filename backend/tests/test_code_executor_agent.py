import pytest
import pytest_asyncio

from app.agents.code_executor_agent import (
    create_code_executor_agent,
    create_execute_code_tool,
    execute_code,
)


@pytest.mark.asyncio
async def test_execute_code_simple_calculation():
    """Test executing simple Python code."""
    result = await execute_code(
        code="result = 2 + 2",
        user_id="test_user",
        session_id="test_session",
    )

    assert result["success"] is True
    assert result["error"] is None


@pytest.mark.asyncio
async def test_execute_code_with_bq_function():
    """Test executing code that uses bq.pnl function."""
    code = """
pnl_data = bq.pnl(desk='FX')
print('P&L data retrieved:', pnl_data.get('total_pnl'))
display.chart([{'name': d['desk'], 'value': d['total_pnl']} for d in pnl_data['desks']], chart_type='bar', title='P&L by Desk')
"""
    result = await execute_code(
        code=code,
        user_id="test_user",
        session_id="test_session",
    )

    assert result["success"] is True
    assert len(result["text_outputs"]) > 0 or len(result["artifacts"]) > 0


@pytest.mark.asyncio
async def test_execute_code_with_display_table():
    """Test executing code that generates a table."""
    code = """
data = [{"name": "AAPL", "price": 150}, {"name": "GOOGL", "price": 2800}]
display.table(data, title="Stock Prices")
"""
    result = await execute_code(
        code=code,
        user_id="test_user",
        session_id="test_session",
    )

    assert result["success"] is True
    assert len(result["artifacts"]) > 0
    assert result["artifacts"][0]["type"] == "table"


@pytest.mark.asyncio
async def test_execute_code_with_display_text():
    """Test executing code that displays text."""
    code = """
display.text("# Hello\\n\\nThis is a test.", format='markdown')
"""
    result = await execute_code(
        code=code,
        user_id="test_user",
        session_id="test_session",
    )

    assert result["success"] is True
    assert len(result["text_outputs"]) > 0


@pytest.mark.asyncio
async def test_execute_code_with_syntax_error():
    """Test executing code with a syntax error."""
    code = """
this is invalid python
"""
    result = await execute_code(
        code=code,
        user_id="test_user",
        session_id="test_session",
    )

    assert result["success"] is False or result["error"] is not None
    if result["success"]:
        assert "text_outputs" in result or "artifacts" in result


@pytest.mark.asyncio
async def test_execute_code_multiple_artifacts():
    """Test executing code that generates multiple artifacts."""
    code = """
data = [{'name': 'AAPL', 'price': 150}]
display.chart(data, chart_type='bar', title='Chart 1')
display.table(data, title='Table 1')
"""
    result = await execute_code(
        code=code,
        user_id="test_user",
        session_id="test_session",
    )

    assert result["success"] is True
    assert len(result["artifacts"]) >= 1


def test_create_execute_code_tool():
    """Test creating the execute_code tool."""
    tool = create_execute_code_tool()
    assert tool.name == "execute_code"
    assert tool.func is not None


def test_create_code_executor_agent():
    """Test creating the code executor agent."""
    agent = create_code_executor_agent(user_id="test_user", session_id="test_session")
    assert agent.name == "CodeExecutorAgent"
    assert len(agent.tools) > 0


@pytest.mark.asyncio
async def test_execute_code_with_fx_rates():
    """Test executing code that fetches FX rates."""
    code = """
fx_data = bq.fx_rates()
print('FX data retrieved, rates count:', len(fx_data.get('rates', [])))
"""
    result = await execute_code(
        code=code,
        user_id="test_user",
        session_id="test_session",
    )

    assert result["success"] is True
    assert len(result["text_outputs"]) > 0


@pytest.mark.asyncio
async def test_execute_code_with_risk_data():
    """Test executing code that fetches risk data."""
    code = """
risk_data = bq.risk()
print('Risk data retrieved, desks count:', len(risk_data.get('desks', [])))
"""
    result = await execute_code(
        code=code,
        user_id="test_user",
        session_id="test_session",
    )

    assert result["success"] is True
    assert len(result["text_outputs"]) > 0
