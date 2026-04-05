import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas import (
    AgentChatRequest,
    ArtifactListResponse,
    ArtifactResponse,
    MessageListResponse,
    MessageResponse,
    SessionCreate,
    SessionListResponse,
    SessionResponse,
    SessionUpdate,
)
from app.services.agent_service import chat_stream
from app.services.auth import get_current_user
from app.services.context_injector import get_available_functions
from app.services.session_service import get_session_service

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: SessionCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new session for the current user."""
    session_service = get_session_service()
    session = await session_service.create_session(
        user_id=current_user.get("sub", "unknown"),
        name=request.name,
    )
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        name=session.name,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(current_user: dict = Depends(get_current_user)):
    """List all sessions for the current user."""
    session_service = get_session_service()
    sessions = await session_service.list_sessions(user_id=current_user.get("sub", "unknown"))
    return SessionListResponse(
        sessions=[
            SessionResponse(
                id=s.id,
                user_id=s.user_id,
                name=s.name,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in sessions
        ]
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific session by ID."""
    session_service = get_session_service()
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.get("sub", "unknown"):
        raise HTTPException(status_code=403, detail="Not authorized to access this session")
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        name=session.name,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: SessionUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update a session's name."""
    session_service = get_session_service()
    session = await session_service.update_session(session_id, request.name)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.get("sub", "unknown"):
        raise HTTPException(status_code=403, detail="Not authorized to update this session")
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        name=session.name,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a session and its artifacts."""
    session_service = get_session_service()
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.get("sub", "unknown"):
        raise HTTPException(status_code=403, detail="Not authorized to delete this session")
    await session_service.delete_session(session_id)
    return {"message": "Session deleted successfully"}


@router.get("/sessions/{session_id}/artifacts", response_model=ArtifactListResponse)
async def list_session_artifacts(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """List all artifacts for a session."""
    session_service = get_session_service()
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.get("sub", "unknown"):
        raise HTTPException(status_code=403, detail="Not authorized to access this session")
    artifacts = await session_service.get_artifacts(session_id)
    return ArtifactListResponse(
        artifacts=[
            ArtifactResponse(
                id=a.id,
                session_id=a.session_id,
                type=a.type,
                title=a.title,
                spec=a.spec,
                columns=a.columns,
                data=a.data,
                content=a.content,
                format=a.format,
                created_at=a.created_at,
            )
            for a in artifacts
        ]
    )


@router.get("/artifacts/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(artifact_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific artifact by ID."""
    session_service = get_session_service()
    artifact = await session_service.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    session = await session_service.get_session(artifact.session_id)
    if not session or session.user_id != current_user.get("sub", "unknown"):
        raise HTTPException(status_code=403, detail="Not authorized to access this artifact")
    return ArtifactResponse(
        id=artifact.id,
        session_id=artifact.session_id,
        type=artifact.type,
        title=artifact.title,
        spec=artifact.spec,
        columns=artifact.columns,
        data=artifact.data,
        content=artifact.content,
        format=artifact.format,
        created_at=artifact.created_at,
    )


@router.get("/sessions/{session_id}/messages", response_model=MessageListResponse)
async def list_session_messages(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """List all messages for a session."""
    session_service = get_session_service()
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.get("sub", "unknown"):
        raise HTTPException(status_code=403, detail="Not authorized to access this session")
    messages = await session_service.get_messages(session_id)
    return MessageListResponse(
        messages=[
            MessageResponse(
                id=m.id,
                session_id=m.session_id,
                role=m.role,
                content=m.content,
                created_at=m.created_at,
            )
            for m in messages
        ]
    )


@router.post("/chat")
async def agent_chat(request: AgentChatRequest, current_user: dict = Depends(get_current_user)):
    """Send a message to the AI agent and stream the response.

    The backend manages session history via Google ADK. If session_id is not provided,
    a new session is automatically created.
    """
    user_id = current_user.get("sub", "unknown")
    session_service = get_session_service()

    session_id = request.session_id
    if not session_id:
        session = await session_service.create_session(user_id=user_id, name=None)
        session_id = session.id

    async def generate_response():
        yield json.dumps({"type": "session_id", "session_id": session_id}) + "\n"
        async for event in chat_stream(
            message=request.message,
            user_id=user_id,
            session_id=session_id,
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
