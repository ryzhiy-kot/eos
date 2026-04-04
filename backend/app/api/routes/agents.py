import json
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.schemas import AgentChatRequest
from app.services.auth import get_current_user
from app.services.agent_service import chat_stream, get_available_functions

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/chat")
async def agent_chat(request: AgentChatRequest, current_user: dict = Depends(get_current_user)):
    """Send a message to the AI agent and stream the response."""

    conversation_history = []
    if request.history:
        for msg in request.history:
            conversation_history.append((msg.get("role", "user"), msg.get("content", "")))

    async def generate_response():
        async for event in chat_stream(
            message=request.message,
            user_id=current_user.get("sub", "unknown"),
            session_id=request.session_id or "default",
            history=conversation_history,
        ):
            yield json.dumps(event) + "\n"

    return StreamingResponse(
        generate_response(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/functions")
async def list_functions(current_user: dict = Depends(get_current_user)):
    """List available functions for the agent."""
    return get_available_functions()


@router.get("/conversations")
async def list_conversations(current_user: dict = Depends(get_current_user)):
    """List conversation history for the current user."""
    return {
        "conversations": [
            {
                "id": str(uuid4()),
                "title": "Morning Risk Review",
                "created_at": datetime.now(UTC).isoformat(),
            },
            {
                "id": str(uuid4()),
                "title": "P&L Attribution Analysis",
                "created_at": datetime.now(UTC).isoformat(),
            },
        ]
    }
