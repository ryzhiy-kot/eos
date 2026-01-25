from fastapi import APIRouter, Depends, HTTPException
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

router = APIRouter()


@router.get(
    "/workspace/{workspace_id}", response_model=List[ChatSession], tags=["sessions"]
)
async def list_sessions(workspace_id: str, db: AsyncSession = Depends(get_db)):
    return await SessionService.get_sessions(db, workspace_id)


@router.get("/{id}", response_model=ChatSession, tags=["sessions"])
async def get_session(id: str, db: AsyncSession = Depends(get_db)):
    db_obj = await SessionService.get_session(db, id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_obj


@router.patch("/{id}", response_model=ChatSession, tags=["sessions"])
async def update_session(
    id: str, session_in: ChatSessionUpdate, db: AsyncSession = Depends(get_db)
):
    # Simple logic here as proof of concept for the refactor
    db_obj = await SessionService.get_session(db, id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Session not found")

    if session_in.name:
        db_obj.name = session_in.name
    if session_in.is_active is not None:
        db_obj.is_active = session_in.is_active

    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.post("/execute", response_model=ExecutionResponse, tags=["sessions"])
async def execute_interaction(
    req: ExecutionRequest, db: AsyncSession = Depends(get_db)
):
    result = await ExecutionService.execute(db, req)
    if not result.get("success"):
        raise HTTPException(
            status_code=400, detail=result.get("message", "Execution failed")
        )
    return result
