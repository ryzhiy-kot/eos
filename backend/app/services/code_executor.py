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
    """Execute code and stream any display calls."""

    local_ns = context.copy()
    local_ns["display"] = collector

    old_stdout = sys.stdout
    old_stderr = sys.stderr

    try:
        sys.stdout = StringIO()
        sys.stderr = StringIO()

        try:
            exec(code, local_ns)
        except Exception as e:
            yield {"type": "error", "content": f"Execution error: {str(e)}"}
            return

        stdout = sys.stdout.getvalue()
        if stdout:
            yield {"type": "text", "content": stdout}

        for artifact in collector.artifacts:
            yield {
                "type": artifact["type"],
                "id": artifact["id"],
                "title": artifact.get("title", ""),
                "spec": artifact.get("spec"),
                "columns": artifact.get("columns"),
                "data": artifact.get("data"),
                "content": artifact.get("content"),
                "pdfData": artifact.get("data"),
                "format": artifact.get("format"),
            }

        yield {"type": "done", "artifacts": collector.artifacts}

    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
