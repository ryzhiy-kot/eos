# PROJECT: EoS
# AUTHOR: Kyrylo Yatsenko
# YEAR: 2026
# * COPYRIGHT NOTICE:
# © 2026 Kyrylo Yatsenko. All rights reserved.
#
# This work represents a proprietary methodology for Human-Machine Interaction (HMI).
# All source code, logic structures, and User Experience (UX) frameworks
# contained herein are the sole intellectual property of Kyrylo Yatsenko.
#
# ATTRIBUTION REQUIREMENT:
# Any use of this program, or any portion thereof (including code snippets and
# interaction patterns), may not be used, redistributed, or adapted
# without explicit, visible credit to Kyrylo Yatsenko as the original author.

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.schemas.chat import (
    ChatSession,
    ChatSessionUpdate,
    ExecutionRequest,
    ExecutionResponse,
)
from app.services.session_service import SessionService
from app.services.execution_service import ExecutionService
from app.api import deps
from app.schemas.user import User

router = APIRouter()


@router.get(
    "/workspace/{workspace_id}", response_model=List[ChatSession], tags=["sessions"]
)
async def list_sessions(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    return await SessionService.get_sessions(db, workspace_id)


@router.get("/{id}", response_model=ChatSession, tags=["sessions"])
async def get_session(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    db_obj = await SessionService.get_session(db, id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_obj


@router.patch("/{id}", response_model=ChatSession, tags=["sessions"])
async def update_session(
    id: str,
    session_in: ChatSessionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    db_obj = await SessionService.update_session(
        db, id, name=session_in.name, is_active=session_in.is_active
    )
    if not db_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_obj


@router.post("/execute", response_model=ExecutionResponse, tags=["sessions"])
async def execute_interaction(
    req: ExecutionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    if req.stream and req.type == "chat":
        return StreamingResponse(
            ExecutionService.execute_stream(db, req), media_type="text/event-stream"
        )

    result = await ExecutionService.execute(db, req)
    if not result.get("success"):
        raise HTTPException(
            status_code=400, detail=result.get("message", "Execution failed")
        )
    return result
