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

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from typing import Optional
import random
from app.models.artifact import Artifact, MutationRecord
from app.schemas.artifact import Artifact as ArtifactSchema


class ArtifactService:
    @staticmethod
    async def get_artifact(db: AsyncSession, artifact_id: str) -> Optional[Artifact]:
        stmt = (
            select(Artifact)
            .where(Artifact.id == artifact_id)
            .options(selectinload(Artifact.mutations))
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def _update_artifact_logic(
        db: AsyncSession, existing: Artifact, artifact_in: ArtifactSchema
    ) -> Artifact:
        new_version_id = "v1"
        parent_id = None

        # Resolve versioning
        mut_stmt = (
            select(MutationRecord)
            .where(MutationRecord.artifact_id == artifact_in.id)
            .order_by(MutationRecord.timestamp.desc())
        )
        mut_result = await db.execute(mut_stmt)
        latest_mut = mut_result.scalars().first()

        if latest_mut:
            parent_id = latest_mut.version_id
            try:
                v_num = int(parent_id.replace("v", "")) + 1
                new_version_id = f"v{v_num}"
            except (ValueError, AttributeError):
                new_version_id = f"v{random.randint(2, 999)}"

        # Update handle
        existing.type = artifact_in.type
        existing.payload = artifact_in.payload
        existing.artifact_metadata = artifact_in.metadata or {}
        if artifact_in.session_id:
            existing.session_id = artifact_in.session_id

        mutation = MutationRecord(
            artifact_id=artifact_in.id,
            version_id=new_version_id,
            parent_id=parent_id,
            origin={"type": "manual_edit", "sessionId": artifact_in.session_id},
            change_summary="Update via manual edit or sync",
            payload=artifact_in.payload,
            status="committed",
        )
        existing.mutations.append(mutation)
        db.add(mutation)
        await db.commit()
        await db.refresh(existing, ["mutations"])
        return existing

    @staticmethod
    async def create_or_update_artifact(
        db: AsyncSession, artifact_in: ArtifactSchema
    ) -> Artifact:
        existing = await ArtifactService.get_artifact(db, artifact_in.id)

        if existing:
            return await ArtifactService._update_artifact_logic(db, existing, artifact_in)

        try:
            artifact_obj = Artifact(
                id=artifact_in.id,
                type=artifact_in.type,
                payload=artifact_in.payload,
                artifact_metadata=artifact_in.metadata or {},
                session_id=artifact_in.session_id or "default_session",
            )
            db.add(artifact_obj)

            mutation = MutationRecord(
                artifact_id=artifact_in.id,
                version_id="v1",
                parent_id=None,
                origin={"type": "manual_edit", "sessionId": artifact_in.session_id},
                change_summary="Initial upload/creation",
                payload=artifact_in.payload,
                status="committed",
            )
            artifact_obj.mutations.append(mutation)
            db.add(mutation)

            await db.commit()
            await db.refresh(artifact_obj, ["mutations"])
            return artifact_obj
        except IntegrityError:
            await db.rollback()
            # Race condition: artifact created by another process/request
            existing = await ArtifactService.get_artifact(db, artifact_in.id)
            if existing:
                return await ArtifactService._update_artifact_logic(
                    db, existing, artifact_in
                )
            raise

    @staticmethod
    async def create_adhoc_mutation(
        db: AsyncSession,
        artifact_id: str,
        payload: any,
        origin: dict,
        version_id: str,
        parent_id: Optional[str] = None,
    ) -> MutationRecord:
        mutation = MutationRecord(
            artifact_id=artifact_id,
            version_id=version_id,
            parent_id=parent_id,
            origin=origin,
            change_summary="AI Optimization (Ghost Preview)",
            payload=payload,
            status="ghost",
        )
        db.add(mutation)
        await db.commit()
        await db.refresh(mutation)
        return mutation
