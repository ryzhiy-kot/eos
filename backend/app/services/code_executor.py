import asyncio
import sys
from io import StringIO
from typing import Any, AsyncGenerator


class OutputCollector:
    def __init__(self):
        self.stdout = StringIO()
        self.stderr = StringIO()

    def get_stdout(self) -> str:
        return self.stdout.getvalue()

    def get_stderr(self) -> str:
        return self.stderr.getvalue()


async def execute_code_streaming(
    code: str,
    context: dict,
    collector: Any,
) -> AsyncGenerator[dict, None]:
    """Execute code and stream any display calls.

    Args:
        code: Python code to execute.
        context: Execution context with bq.* and display.* functions.
        collector: ArtifactCollector instance to capture display artifacts.

    Yields:
        dict events with type "text", "chart", "table", "pdf", "text", "error", "done"
    """
    local_ns = {
        "bq": context.get("bq"),
        "display": collector,
        "pd": context.get("pd"),
        "np": context.get("np"),
        "json": context.get("json"),
        "_user_id": context.get("_user_id", "unknown"),
        "_session_id": context.get("_session_id", "unknown"),
    }

    old_stdout = sys.stdout
    old_stderr = sys.stderr

    stdout_capture = StringIO()
    stderr_capture = StringIO()

    try:
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture

        try:
            exec(code, local_ns)
        except Exception as e:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            yield {"type": "error", "content": f"Execution error: {str(e)}"}
            return

    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    stdout = stdout_capture.getvalue()
    if stdout:
        yield {"type": "text", "content": stdout}

    for idx, artifact in enumerate(collector.artifacts):
        yield {
            "type": artifact["type"],
            "id": artifact.get("id", f"{artifact['type']}_{idx}"),
            "title": artifact.get("title", ""),
            "chart_type": artifact.get("chart_type"),
            "spec": artifact.get("spec"),
            "columns": artifact.get("columns"),
            "data": artifact.get("data"),
            "content": artifact.get("content"),
            "pdfData": artifact.get("data"),
            "format": artifact.get("format"),
        }

    yield {"type": "done", "artifacts": collector.artifacts}
