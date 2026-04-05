import logging

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from pydantic import BaseModel, Field

from app.agents.groq_agent import GroqAgent
from app.config import get_settings
from app.services.artifact_collector import ArtifactCollector
from app.services.code_executor import execute_code_streaming
from app.services.context_injector import (
    build_execution_context,
    get_execution_environment_doc,
)

logger = logging.getLogger(__name__)

settings = get_settings()

CODE_EXECUTOR_NAME = "CodeExecutorAgent"
CODE_EXECUTOR_MODEL = "gemini-2.0-flash"


class CodeExecutorInput(BaseModel):
    """Input schema for CodeExecutorAgent."""

    request: str = Field(description="The user's request or task for code execution")
    code: str | None = Field(
        default=None,
        description="Optional Python code to execute directly. If not provided, the agent will generate code based on the request.",
    )


class CodeExecutorOutput(BaseModel):
    """Output schema for CodeExecutorAgent."""

    success: bool = Field(description="True if execution succeeded, False if there was an error.")
    text_outputs: list[str] = Field(description="List of all captured stdout (print calls) output.")
    artifacts: list[dict] = Field(description="List of generated visual artifacts.")
    error: str | None = Field(
        default=None, description="Error message if execution failed, None otherwise."
    )


async def execute_code(
    request: str = "", code: str | None = None, user_id: str = "", session_id: str = ""
) -> CodeExecutorOutput:
    """Execute Python code in a sandboxed environment and return results with artifacts.

    This function is the primary tool for the CodeExecutorAgent. It runs Python code
    with access to financial data and visualization utilities.

    Execution Environment:
    ----------------------
    The following functions and modules are pre-injected into the execution namespace:

    Data Query (bq.*):
    - bq.pnl(desk=None, date=None, currency="USD") - Get P&L data
    - bq.risk(desk=None, metric_type="full") - Get risk metrics (VaR, Greeks)
    - bq.fx_rates(pair=None) - Get real-time FX rates
    - bq.curves(curve_type=None) - Get interest rate curves (USD, EUR, GBP, JPY, CHF)
    - bq.positions(desk=None) - Get current trading positions
    - bq.news(keywords=None, max_results=10) - Get market news

    Display Utilities (display.*):
    - display.chart(data, chart_type="bar", title="") - bar, line, candlestick, gauge
    - display.table(data, title="", max_rows=50) - Generate a sortable table
    - display.text(content, format="markdown") - Render Markdown or plain text
    - display.pdf(content, title="") - Generate a downloadable PDF report

    Standard Modules:
    - pandas (as pd), numpy (as np), json, random, datetime

    Args:
        request: The initial user request. used as code if `code` is not provided.
        code: Optional Python code to execute directly. Takes precedence over `request`.
        user_id: Unique identifier for the user (for data scoping).
        session_id: Active session identifier (for context continuity).

    Returns:
        dict: {
            "success": bool,           # True if execution succeeded
            "text_outputs": list[str], # All captured stdout (print calls)
            "artifacts": list[dict],   # Structured visual artifacts for the GUI
            "error": str | None        # Error message if execution failed
        }

    Example:
        >>> code = "pnl = bq.pnl(desk='FX'); display.chart(pnl['history'], title='FX P&L')"
        >>> result = await execute_code(code=code, user_id="trader_1")
    """

    # Determine which code to actually execute
    code_to_run = code if code else request

    # Initialize the artifact collector and execution context
    collector = ArtifactCollector()
    context, _ = build_execution_context(user_id, [])

    # Inject display utilities and session metadata into the context
    context["display"] = collector
    context["_user_id"] = user_id
    context["_session_id"] = session_id

    # Initialize the result structure
    result = {
        "success": True,
        "text_outputs": [],
        "artifacts": [],
        "error": None,
    }

    try:
        # Consume the streaming execution events
        async for event in execute_code_streaming(code_to_run, context, collector):
            if event["type"] == "error":
                result["success"] = False
                result["error"] = event.get("content")
            elif event["type"] == "text":
                # Collect captured stdout from print statements
                result["text_outputs"].append(event["content"])
            elif event["type"] in ("chart", "table", "pdf", "text"):
                # Format and store artifacts (charts, tables, etc.)
                artifact_data = {
                    "type": event["type"],
                    "id": event.get("id", f"{event['type']}_{len(result['artifacts'])}"),
                    "title": event.get("title", ""),
                    "spec": event.get("spec"),
                    "columns": event.get("columns"),
                    "data": event.get("data"),
                    "content": event.get("content"),
                    "format": event.get("format"),
                }
                result["artifacts"].append(artifact_data)
            elif event["type"] == "done":
                # Final pass to ensure all artifacts are captured
                for artifact in event.get("artifacts", []):
                    result["artifacts"].append(artifact)

    except Exception as e:
        # Handle unexpected errors during the streaming process
        logger.error(f"Code execution error: {e}", exc_info=True)
        result["success"] = False
        result["error"] = str(e)

    return CodeExecutorOutput(**result)


def create_execute_code_tool() -> FunctionTool:
    """Create the execute_code function tool.

    Execute Python code to perform calculations, data analysis, and generate visualizations.

    Args:
    - request: str - The user's request (used as code if code not provided)
    - code: str - The Python code to execute (takes precedence)
    - user_id: str - The user ID for context
    - session_id: str - The session ID for context

    Returns a dict with:
    - success: bool - Whether execution succeeded
    - text_outputs: list[str] - Any text printed during execution
    - artifacts: list[dict] - Charts, tables, PDFs generated
    - error: str | None - Error message if failed
    """
    return FunctionTool(func=execute_code)


def create_code_executor_agent(
    user_id: str | None = None,
    session_id: str | None = None,
) -> LlmAgent:
    """Create the CodeExecutorAgent with appropriate tools.

    Args:
        user_id: Optional user ID for context
        session_id: Optional session ID for context

    Returns:
        LlmAgent configured for code execution
    """
    tools = [create_execute_code_tool()]
    
    execution_env_doc = get_execution_environment_doc()

    instruction = f"""You are a Code Execution Specialist agent.

Your role is to execute Python code to help users with financial calculations, data analysis, and visualizations.

IMPORTANT WORKFLOW:
1. Write Python code that uses bq.* and display.* functions
2. Pass your code to the execute_code tool via the 'request' parameter
3. The execute_code tool runs your code and returns results

DO NOT call bq.* or display.* directly - they are only available inside execute_code.

{execution_env_doc}

Guidelines:
- Write clean, executable Python code
- Use bq.* to fetch data, display.* to generate visualizations
- Always include print() statements for intermediate results
- If execute_code returns success: False, analyze the error, fix your code, and retry
- Do not stop until you succeed"""

    agent_kwargs = {
        "name": CODE_EXECUTOR_NAME,
        "instruction": instruction,
        "description": "Specialized agent for executing Python code for financial analysis",
        "tools": tools,
        "input_schema": CodeExecutorInput,
    }

    if settings.LLM_PROVIDER == "groq":
        logger.info("Using GroqAgent for CodeExecutorAgent")
        return GroqAgent(
            model=settings.GROQ_MODEL,
            **agent_kwargs,
        )
    else:
        logger.info(f"Using Gemini for CodeExecutorAgent (provider: {settings.LLM_PROVIDER})")
        return LlmAgent(
            model=CODE_EXECUTOR_MODEL,
            **agent_kwargs,
        )
