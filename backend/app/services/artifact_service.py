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

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from typing import Optional, Union
import random
import uuid
from app.models.artifact import Artifact, MutationRecord
from app.schemas.artifact import ArtifactCreate, ArtifactUpdate


from app.core.config import get_settings
from app.core.artifact.factory import get_artifact_store


class ArtifactService:
    @staticmethod
    async def get_artifact(db: AsyncSession, artifact_id: str, token: Optional[str] = None) -> Optional[Artifact]:
        stmt = (
            select(Artifact)
            .where(Artifact.id == artifact_id)
            .options(selectinload(Artifact.mutations))
        )
        result = await db.execute(stmt)
        artifact = result.scalar_one_or_none()

        if artifact and artifact.storage_backend != "db" and artifact.storage_key:
            store = get_artifact_store()
            try:
                content = await store.load(artifact.id, artifact.storage_key, token=token)
                # Rehydrate payload for the consumer
                artifact.payload = content
            except Exception as e:
                # Log error but return artifact with missing payload or handle gracefully
                # For now we assume consistency
                pass

        return artifact

    @staticmethod
    async def _update_artifact_logic(
        db: AsyncSession,
        existing: Artifact,
        artifact_in: Union[ArtifactCreate, ArtifactUpdate],
        token: Optional[str] = None
    ) -> Artifact:
        new_version_id = "v1"
        parent_id = None

        # Resolve versioning
        mut_stmt = (
            select(MutationRecord)
            .where(MutationRecord.artifact_id == existing.id)
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

        # Prepare metadata
        metadata = existing.artifact_metadata or {}
        if artifact_in.metadata:
            metadata.update(artifact_in.metadata)
        if artifact_in.name:
            metadata["name"] = artifact_in.name

        # Handle payload and storage
        payload = existing.payload
        if artifact_in.payload is not None:
            payload = artifact_in.payload

        # Only update storage if payload changed
        settings = get_settings()
        storage_key = existing.storage_key
        if artifact_in.payload is not None:
            store = get_artifact_store()
            storage_key = await store.save(existing.id, payload, token=token)
            existing.storage_backend = settings.ARTIFACT_STORAGE_BACKEND
            existing.storage_key = storage_key
            if settings.ARTIFACT_STORAGE_BACKEND == "db":
                existing.payload = payload
            else:
                existing.payload = None  # Offloaded

        # Update handle
        if hasattr(artifact_in, "type") and artifact_in.type:
             existing.type = artifact_in.type

        existing.artifact_metadata = metadata

        if hasattr(artifact_in, "session_id") and artifact_in.session_id:
            existing.session_id = artifact_in.session_id

        # Create mutation
        if artifact_in.payload is not None:
            mutation = MutationRecord(
                artifact_id=existing.id,
                version_id=new_version_id,
                parent_id=parent_id,
                origin={
                    "type": "manual_edit",
                    "sessionId": existing.session_id,
                },
                change_summary="Update via manual edit or sync",
                payload=payload,
                status="committed",
            )
            existing.mutations.append(mutation)
            db.add(mutation)

        db.add(existing)
        await db.commit()
        await db.refresh(existing, ["mutations"])

        # Ensure payload is visible on return
        if existing.payload is None and payload is not None:
            existing.payload = payload

        return existing

    @staticmethod
    async def create_or_update_artifact(
        db: AsyncSession, artifact_in: ArtifactCreate, token: Optional[str] = None
    ) -> Artifact:
        if artifact_in.id:
            existing = await ArtifactService.get_artifact(db, artifact_in.id, token=token)
            if existing:
                return await ArtifactService._update_artifact_logic(
                    db, existing, artifact_in, token=token
                )

        # Generate ID if missing
        new_id = artifact_in.id or str(uuid.uuid4())

        # Prepare metadata
        metadata = artifact_in.metadata or {}
        metadata["name"] = artifact_in.name

        # Handle external storage
        store = get_artifact_store()
        storage_key = await store.save(new_id, artifact_in.payload, token=token)
        settings = get_settings()

        try:
            artifact_obj = Artifact(
                id=new_id,
                type=artifact_in.type,
                artifact_metadata=metadata,
                session_id=artifact_in.session_id or "default_session",
                storage_backend=settings.ARTIFACT_STORAGE_BACKEND,
                storage_key=storage_key,
                payload=artifact_in.payload
                if settings.ARTIFACT_STORAGE_BACKEND == "db"
                else None,
            )
            db.add(artifact_obj)

            mutation = MutationRecord(
                artifact_id=new_id,
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

            # Ensure payload is visible on return
            if artifact_obj.payload is None and artifact_in.payload is not None:
                artifact_obj.payload = artifact_in.payload

            return artifact_obj
        except IntegrityError:
            await db.rollback()
            # Race condition: artifact created by another process/request
            if artifact_in.id:
                existing = await ArtifactService.get_artifact(db, artifact_in.id, token=token)
                if existing:
                    return await ArtifactService._update_artifact_logic(
                        db, existing, artifact_in, token=token
                    )
            raise

    @staticmethod
    async def update_artifact(
        db: AsyncSession, existing: Artifact, artifact_in: ArtifactUpdate, token: Optional[str] = None
    ) -> Artifact:
        return await ArtifactService._update_artifact_logic(db, existing, artifact_in, token=token)

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
