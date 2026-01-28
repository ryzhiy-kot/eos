# PROJECT: MONAD
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
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.artifact import Artifact as ArtifactSchema
from app.services.artifact_service import ArtifactService

router = APIRouter()


@router.get("/{id}", response_model=ArtifactSchema, tags=["artifacts"])
async def get_artifact(id: str, db: AsyncSession = Depends(get_db)):
    db_obj = await ArtifactService.get_artifact(db, id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return db_obj


@router.post("/", response_model=ArtifactSchema, tags=["artifacts"])
async def create_artifact(
    artifact_in: ArtifactSchema, db: AsyncSession = Depends(get_db)
):
    return await ArtifactService.create_or_update_artifact(db, artifact_in)
