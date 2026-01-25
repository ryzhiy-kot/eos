from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Dict
import random
from app.models.artifact import Artifact, MutationRecord
from app.schemas.chat import ExecutionRequest
from app.services.session_service import SessionService


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

        # Mock Response
        phrases = [
            "I've analyzed the referenced artifacts. It seems there are some interesting patterns.",
            "Based on the context you provided, I recommend looking at these data points.",
            "Could you clarify which part of the artifact you're most interested in?",
            "I've processed your request. Let me know if you need any specific transformations.",
            "Interesting observation. Applying that logic to the current workspace state...",
        ]
        response_text = random.choice(phrases)
        if artifacts:
            refs = ", ".join([f"@[{a.id}]" for a in artifacts])
            response_text = (
                f"**Context Received**: I'm now processing {refs}. \n\n{response_text}"
            )

        assistant_msg = await SessionService.save_message(
            db, req.session_id, "assistant", response_text
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
