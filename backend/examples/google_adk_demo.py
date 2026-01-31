import os
import sys
import json
import asyncio
import uuid
import logging
from typing import AsyncGenerator, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("adk_demo")

# Ensure we can import from app
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

try:
    from google.adk.agents import LlmAgent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.adk.code_executors import BuiltInCodeExecutor
    from google.genai import types
except ImportError as e:
    logger.error(f"Failed to import google-adk: {e}")
    print("google-adk not installed. Please install it with `pip install google-adk`.")
    sys.exit(1)

try:
    from app.core.llm_protocol import LLMRequest, LLMMessage, TextDeltaEvent, ArtifactStartEvent, ArtifactChunkEvent, ArtifactEndEvent
except ImportError as e:
    logger.error(f"Failed to import EoS protocol: {e}")
    # Fallback/Mock definitions if running completely standalone
    from pydantic import BaseModel
    class Artifact(BaseModel):
        id: str
        type: str
        payload: Optional[Dict[str, Any]] = None
    class LLMMessage(BaseModel):
        role: str
        content: str
        artifacts: list = []
    class LLMRequest(BaseModel):
        session_id: str
        messages: list[LLMMessage]
        context_artifacts: list = []

# --- Configuration ---
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    logger.warning("GOOGLE_API_KEY not set. The agent will likely fail.")

AGENT_NAME = "eos_demo_agent"
APP_NAME = "eos_demo"
MODEL_NAME = "gemini-2.0-flash"

# --- ADK Setup ---
# We use a global session service for the demo.
# In a real app, you might want persistent storage.
session_service = InMemorySessionService()

# Create the agent once
code_agent = LlmAgent(
    name=AGENT_NAME,
    model=MODEL_NAME,
    code_executor=BuiltInCodeExecutor(),
    instruction="""You are an intelligent assistant integrated into the EoS platform.
    You have access to a python code execution environment.
    When asked to perform calculations, data analysis, or tasks better suited for code,
    write and execute Python code.
    """,
    description="EoS Agent with Code Execution",
)

# Initialize the Runner
# Note: Runner in ADK (Python) might be per-request or reused depending on version.
# The quickstart initializes it once.
runner = Runner(agent=code_agent, app_name=APP_NAME, session_service=session_service)


app = FastAPI(title="Google ADK EoS Demo Provider")

async def generate_event_stream(request: LLMRequest) -> AsyncGenerator[str, None]:
    """
    Generates SSE events compliant with EoS LLM Protocol.
    """
    logger.info(f"Received request for session {request.session_id}")

    # 1. Prepare Session
    # ADK sessions are managed by the service. We ensure one exists.
    # We ignore the history from EoS request for this demo and rely on ADK's memory,
    # or creates a new one if missing.
    try:
        # Check if session exists (InMemorySessionService implementation specific)
        # But create_session is idempotent-ish or we catch error?
        # The quickstart uses: session = asyncio.run(session_service.create_session(...))
        # We are already async.
        # Check if we can just get it?
        # BaseSessionService usually has get_session but InMemory might differ.
        # We'll try to create and ignore if exists or handle correctly.
        # Actually InMemorySessionService.create_session typically returns the session.
        # If it already exists, we might need a way to get it.
        # Looking at docs, typically you just pass session_id to run_async.
        # We will try to ensure it exists.
        await session_service.create_session(
            app_name=APP_NAME,
            user_id="eos_user", # Simplified user ID
            session_id=request.session_id
        )
    except Exception:
        # It might already exist, which is fine.
        pass

    # 2. Extract last user message
    if not request.messages:
        logger.warning("No messages in request")
        return

    last_msg = request.messages[-1]
    # Convert to Google GenAI Content
    # We assume the last message is from user.
    content = types.Content(
        role="user",
        parts=[types.Part(text=last_msg.content)]
    )

    # 3. Run ADK Runner
    current_artifact_id: Optional[str] = None

    try:
        async for event in runner.run_async(
            user_id="eos_user",
            session_id=request.session_id,
            new_message=content
        ):
            # Inspect event content
            if not event.content or not event.content.parts:
                continue

            for part in event.content.parts:
                # --- Code Generation ---
                if part.executable_code:
                    code = part.executable_code.code
                    if not current_artifact_id:
                        current_artifact_id = str(uuid.uuid4())
                        # Start Artifact
                        yield _sse(ArtifactStartEvent(
                            type="artifact_start",
                            artifact_id=current_artifact_id,
                            artifact_type="code",
                            artifact_metadata={"language": "python", "tool_use": "code_execution"}
                        ).model_dump())

                    # Chunk
                    yield _sse(ArtifactChunkEvent(
                        type="artifact_chunk",
                        artifact_id=current_artifact_id,
                        chunk=code
                    ).model_dump())

                # --- Code Execution Result ---
                elif part.code_execution_result:
                    # If we had an open artifact, close it first
                    if current_artifact_id:
                        yield _sse(ArtifactEndEvent(
                            type="artifact_end",
                            artifact_id=current_artifact_id
                        ).model_dump())
                        current_artifact_id = None

                    # Stream result as text (or could be another artifact)
                    outcome = part.code_execution_result.outcome
                    output = part.code_execution_result.output
                    text_output = f"\n\n> **Execution {outcome}**:\n```\n{output}\n```\n"

                    yield _sse(TextDeltaEvent(
                        type="text_delta",
                        content=text_output
                    ).model_dump())

                # --- Text Content ---
                elif part.text:
                    text = part.text
                    # Close artifact if open (unlikely to interleave, but safe)
                    if current_artifact_id:
                        yield _sse(ArtifactEndEvent(
                            type="artifact_end",
                            artifact_id=current_artifact_id
                        ).model_dump())
                        current_artifact_id = None

                    if text:
                        yield _sse(TextDeltaEvent(
                            type="text_delta",
                            content=text
                        ).model_dump())

        # End of stream cleanup
        if current_artifact_id:
            yield _sse(ArtifactEndEvent(
                type="artifact_end",
                artifact_id=current_artifact_id
            ).model_dump())

    except Exception as e:
        logger.error(f"Error running ADK agent: {e}", exc_info=True)
        yield _sse({"type": "error", "content": str(e)})

def _sse(data: Dict) -> str:
    return f"data: {json.dumps(data)}\n\n"

@app.post("/generate")
async def generate(request: LLMRequest):
    return StreamingResponse(
        generate_event_stream(request),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
