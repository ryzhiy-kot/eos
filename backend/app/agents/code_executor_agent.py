import logging

from typing import Any
from google.adk.tools import FunctionTool
from pydantic import BaseModel, Field

from ..config import get_settings
from ..services.artifact_collector import ArtifactCollector
from ..services.code_executor import execute_code_streaming
from ..services.context_injector import (
    build_execution_context,
    get_execution_environment_doc,
)
from ..services.llm_factory import create_llm_agent


logger = logging.getLogger(__name__)

settings = get_settings()

CODE_EXECUTOR_NAME = "CodeExecutorAgent"


class CodeExecutorInput(BaseModel):
    """Input schema for CodeExecutorAgent."""

    request: str = Field(description="The user's request or task for code execution")
    code: str | None = Field(
        default=None,
        description="Optional Python code to execute directly. If not provided, the agent will generate code based on the request.",
    )


class CodeExecutorOutput(BaseModel):
    """Output schema for CodeExecutorAgent."""

    success: bool = Field(
        description="True if execution succeeded, False if there was an error."
    )
    text_outputs: list[str] = Field(
        description="List of all captured stdout (print calls) output."
    )
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

    Args:
        request: The initial user request. used as code if `code` is not provided.
        code: Optional Python code to execute directly. Takes precedence over `request`.
        user_id: Unique identifier for the user (for data scoping).
        session_id: Active session identifier (for context continuity).

    Returns:
        CodeExecutorOutput: The result of the code execution.

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
                    "id": event.get(
                        "id", f"{event['type']}_{len(result['artifacts'])}"
                    ),
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
) -> Any:
    """Create the CodeExecutorAgent with appropriate tools."""
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

    return create_llm_agent(
        name=CODE_EXECUTOR_NAME,
        instruction=instruction,
        description="Specialized agent for executing Python code for financial analysis",
        tools=tools,
        input_schema=CodeExecutorInput,
        output_schema=CodeExecutorOutput,
    )
