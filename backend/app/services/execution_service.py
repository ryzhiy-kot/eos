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
from sqlalchemy.orm import selectinload
from typing import Dict
import random
import json
from app.models.artifact import Artifact, MutationRecord
from app.schemas.chat import ExecutionRequest
from app.services.session_service import SessionService
from app.schemas.artifact import Artifact as ArtifactSchema
from app.core.llm_protocol import (
    LLMRequest,
    LLMMessage,
    TextDeltaEvent,
    ArtifactStartEvent,
    ArtifactChunkEvent,
    ArtifactEndEvent,
)
from app.services.llm_providers import get_llm_provider


class ExecutionService:
    @staticmethod
    async def execute(db: AsyncSession, req: ExecutionRequest) -> Dict:
        if req.type == "chat":
            return await ExecutionService._execute_chat(db, req)
        elif req.type == "command":
            return await ExecutionService._execute_command(db, req)
        return {"success": False, "message": "Unsupported execution type"}

    @staticmethod
    async def _execute_chat(db: AsyncSession, req: ExecutionRequest) -> Dict:
        # Resolve or create session
        db_session = await SessionService.get_session(db, req.session_id)
        if not db_session:
            db_session = await SessionService.create_session(
                db, req.session_id, f"Chat {req.session_id[:8]}"
            )

        # Resolve existing artifacts
        artifacts = []
        if req.referenced_artifact_ids:
            art_stmt = (
                select(Artifact)
                .where(Artifact.id.in_(req.referenced_artifact_ids))
                .options(selectinload(Artifact.mutations))
            )
            art_result = await db.execute(art_stmt)
            artifacts = art_result.scalars().all()

        # Save user message
        await SessionService.save_message(
            db,
            req.session_id,
            "user",
            req.action or "",
            artifacts=artifacts,
        )

        # Convert artifacts to Pydantic models for the LLM Protocol
        pydantic_artifacts = [ArtifactSchema.model_validate(a) for a in artifacts]

        # Construct LLMRequest
        llm_messages = [
            LLMMessage(role="user", content=req.action or "", artifacts=pydantic_artifacts)
        ]

        llm_req = LLMRequest(
            session_id=req.session_id,
            messages=llm_messages,
            context_artifacts=pydantic_artifacts
        )

        provider = get_llm_provider()

        full_text = ""
        new_artifacts_map = {} # id -> {type, metadata, chunks}

        # Consume the stream
        async for event in provider.generate_stream(llm_req):
            if isinstance(event, TextDeltaEvent):
                full_text += event.content
            elif isinstance(event, ArtifactStartEvent):
                new_artifacts_map[event.artifact_id] = {
                    "type": event.artifact_type,
                    "metadata": event.artifact_metadata or {},
                    "payload_chunks": []
                }
            elif isinstance(event, ArtifactChunkEvent):
                if event.artifact_id in new_artifacts_map:
                    new_artifacts_map[event.artifact_id]["payload_chunks"].append(event.chunk)
            elif isinstance(event, ArtifactEndEvent):
                pass

        # Process generated artifacts
        new_artifact_models = []
        for art_id, data in new_artifacts_map.items():
            payload_str = "".join(data["payload_chunks"])
            try:
                payload = json.loads(payload_str)
            except json.JSONDecodeError:
                payload = {"raw_content": payload_str}

            new_art = Artifact(
                id=art_id,
                type=data["type"],
                payload=payload,
                artifact_metadata=data["metadata"],
                session_id=db_session.id,
            )
            new_artifact_models.append(new_art)

            # Create mutation record
            mutation = MutationRecord(
                artifact_id=new_art.id,
                version_id="v1",
                parent_id=None,
                origin={
                    "type": "chat_inference",
                    "sessionId": req.session_id,
                    "prompt": req.action,
                    "triggeringCommand": "chat",
                },
                change_summary="Generated by LLM",
                payload=new_art.payload,
                status="committed"
            )
            new_art.mutations.append(mutation)
            db.add(new_art)
            db.add(mutation)

        assistant_msg = await SessionService.save_message(
            db, req.session_id, "assistant", full_text, artifacts=new_artifact_models
        )

        return {
            "success": True,
            "result": {
                "output_message": assistant_msg,
                "status": "success",
                "metadata": {"session_id": req.session_id},
            },
        }

    @staticmethod
    async def _execute_command(db: AsyncSession, req: ExecutionRequest) -> Dict:
        # Ensure session exists
        db_session = await SessionService.get_session(db, req.session_id)
        if not db_session:
            db_session = await SessionService.create_session(
                db, req.session_id, f"Cmd {req.session_id[:8]}"
            )

        cmd = req.command_name.lower()
        new_artifact_models = []
        status = "success"
        output_msg_text = f"Command {cmd} executed successfully."

        # Mock generation logic
        if cmd == "plot":
            new_art = Artifact(
                id=f"A_PLOT_{random.randint(1000, 9999)}",
                type="visual",
                payload={
                    "format": "svg",
                    "url": f"data:image/svg+xml,<svg>Mock plot</svg>",
                    "alt": "Plot",
                },
                session_id=db_session.id,
            )
            new_artifact_models.append(new_art)
        elif cmd == "run":
            new_art = Artifact(
                id=f"A_CODE_{random.randint(1000, 9999)}",
                type="code",
                payload={
                    "language": "python",
                    "source": f"Executed code: {req.action[:50] if req.action else ''}...",
                },
                session_id=db_session.id,
            )
            new_artifact_models.append(new_art)
        elif cmd == "optimize":
            new_art = Artifact(
                id=f"A_OPT_{random.randint(1000, 9999)}",
                type="code",
                payload={
                    "language": "python",
                    "source": "# Optimized Code\nprint('Hello Optimized World')",
                },
                session_id=db_session.id,
            )
            new_artifact_models.append(new_art)
        # ... other commands (diff, summarize) can be added similarly
        else:
            status = "error"
            output_msg_text = f"Unknown command: {cmd}"

        # Persist and create mutations
        for art in new_artifact_models:
            db.add(art)
            mutation = MutationRecord(
                artifact_id=art.id,
                version_id="v1",
                parent_id=None,
                origin={
                    "type": "adhoc_command",
                    "sessionId": req.session_id,
                    "prompt": req.action,
                    "triggeringCommand": f"/{req.command_name}",
                },
                change_summary="Initial creation",
                payload=art.payload,
                status="committed" if cmd != "optimize" else "ghost",  # Logic for ghost
            )
            art.mutations.append(mutation)  # Link in memory
            db.add(mutation)

        msg = await SessionService.save_message(
            db,
            req.session_id,
            "assistant" if status == "success" else "system",
            output_msg_text,
            artifacts=new_artifact_models,
        )

        return {
            "success": True,
            "result": {
                "output_message": msg,
                "new_artifacts": msg.artifacts,
                "status": status,
                "metadata": {"session_id": req.session_id},
            },
        }
