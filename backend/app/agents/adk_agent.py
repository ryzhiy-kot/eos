import json
import logging
from collections.abc import AsyncGenerator

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.agent_tool import AgentTool
from google.genai import types

from app.config import get_settings
from app.services.context_injector import get_execution_environment_doc
from app.services.llm_factory import create_llm_agent

logger = logging.getLogger(__name__)

settings = get_settings()

APP_NAME = "finagent"
MAIN_AGENT_NAME = "FinancialOrchestratorAgent"


def create_code_executor_subagent(user_id: str, session_id: str) -> LlmAgent:
    """Create the CodeExecutorAgent as a sub-agent."""
    from app.agents.code_executor_agent import create_code_executor_agent

    return create_code_executor_agent(user_id=user_id, session_id=session_id)


def create_main_agent(
    user_id: str,
    session_id: str,
) -> tuple[LlmAgent, LlmAgent]:
    """Create the main orchestrator agent with the code executor as a sub-agent.

    Args:
        user_id: The user ID for context
        session_id: The session ID for context

    Returns:
        Tuple of (main_agent, code_executor_agent)
    """
    code_executor_agent = create_code_executor_subagent(user_id, session_id)

    agent_function_tool = AgentTool(agent=code_executor_agent)

    tools = [agent_function_tool]

    execution_env_doc = get_execution_environment_doc()

    system_instruction = f"""You are a Quantitative Analyst for FX, Rates, Credit, and Commodities trading. Help traders analyze P&L, risk, and market data.

Delegate complex tasks (calculations, analysis, visualizations) to the CodeExecutorAgent using the agent_function tool.

{execution_env_doc}

Guidelines:
1. Use CodeExecutorAgent for data analysis and visualizations
2. Explain findings in plain English
3. Format currency values properly (e.g., $1,234,567.89)"""

    main_agent = create_llm_agent(
        name=MAIN_AGENT_NAME,
        instruction=system_instruction,
        description="Financial trading assistant orchestrator with data analysis capabilities",
        tools=tools,
    )

    return main_agent, code_executor_agent


def get_adk_session_service() -> InMemorySessionService:
    """Get or create the global ADK in-memory session service."""
    if not hasattr(get_adk_session_service, "_instance"):
        get_adk_session_service._instance = InMemorySessionService()
    return get_adk_session_service._instance


async def save_artifacts_to_db(session_id: str, artifacts: list[dict]) -> None:
    """Save artifacts to the database via session service."""
    try:
        from app.services.session_service import get_session_service

        session_service = get_session_service()
        for artifact in artifacts:
            await session_service.save_artifact(
                session_id=session_id,
                artifact_type=artifact.get("type", "unknown"),
                title=artifact.get("title"),
                spec=artifact.get("spec"),
                columns=artifact.get("columns"),
                data=artifact.get("data"),
                content=artifact.get("content"),
                format=artifact.get("format"),
            )
    except Exception as e:
        logger.error(f"Failed to save artifacts to DB: {e}")


async def save_message_to_db(session_id: str, role: str, content: str) -> None:
    """Save a message to the database."""
    try:
        from app.services.session_service import get_session_service

        session_service = get_session_service()
        await session_service.save_message(session_id, role, content)
    except Exception as e:
        logger.error(f"Failed to save message to DB: {e}")


async def load_messages_from_db(session_id: str) -> list[dict]:
    """Load previous messages from the database."""
    try:
        from app.services.session_service import get_session_service

        session_service = get_session_service()
        messages = await session_service.get_messages(session_id)
        return [{"role": m.role, "content": m.content} for m in messages]
    except Exception as e:
        logger.error(f"Failed to load messages from DB: {e}")
        return []


async def run_agent(
    message: str,
    user_id: str,
    session_id: str,
) -> AsyncGenerator[dict, None]:
    """Run the main agent with the given message and session.

    The agent will orchestrate between data query tools and the code executor sub-agent.
    Artifacts generated during execution are saved to the database.
    Messages are also persisted to enable session history navigation.
    """
    adk_session_service = get_adk_session_service()

    await save_message_to_db(session_id, "user", message)

    previous_messages = await load_messages_from_db(session_id)
    for prev_msg in previous_messages:
        try:
            await adk_session_service.create_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id,
            )
            prev_content = types.Content(
                role=prev_msg["role"], parts=[types.Part(text=prev_msg["content"])]
            )
            await adk_session_service.append_message(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id,
                message=prev_content,
            )
        except Exception as e:
            logger.debug(f"Failed to append previous message to ADK session: {e}")

    try:
        await adk_session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
        )
    except Exception as e:
        logger.debug(f"ADK session already exists or failed to create: {e}")

    main_agent, _ = create_main_agent(user_id, session_id)

    runner = Runner(
        agent=main_agent,
        app_name=APP_NAME,
        session_service=adk_session_service,
    )

    content = types.Content(role="user", parts=[types.Part(text=message)])

    all_artifacts = []
    assistant_response = ""

    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):
            if not event.content or not event.content.parts:
                continue

            for part in event.content.parts:
                if part.text:
                    assistant_response += part.text
                    yield {"type": "text", "content": part.text}

                if part.executable_code:
                    yield {
                        "type": "code",
                        "content": part.executable_code.code,
                        "language": part.executable_code.language,
                    }

                if part.code_execution_result:
                    outcome = part.code_execution_result.outcome
                    output = part.code_execution_result.output
                    assistant_response += (
                        f"\n\n> **Execution {outcome}**:\n```\n{output}\n```\n"
                    )
                    text_output = (
                        f"\n\n> **Execution {outcome}**:\n```\n{output}\n```\n"
                    )
                    yield {"type": "text", "content": text_output}

                if part.function_call:
                    yield {
                        "type": "function_call",
                        "name": part.function_call.name,
                        "args": part.function_call.args,
                    }

                if part.function_response:
                    try:
                        response = part.function_response.response
                        if isinstance(response, dict):
                            if "artifacts" in response:
                                all_artifacts.extend(response["artifacts"])
                            if "text_outputs" in response:
                                for text in response["text_outputs"]:
                                    yield {"type": "text", "content": text}
                            response_str = json.dumps(response)
                        else:
                            response_str = str(response)
                    except (TypeError, ValueError):
                        response_str = str(part.function_response.response)
                    yield {
                        "type": "function_response",
                        "name": part.function_response.name,
                        "response": response_str,
                    }

    except Exception as e:
        logger.error(f"Error running agent: {e}", exc_info=True)
        yield {"type": "error", "content": str(e)}

    if assistant_response.strip():
        await save_message_to_db(session_id, "assistant", assistant_response)

    if all_artifacts:
        await save_artifacts_to_db(session_id, all_artifacts)

    yield {"type": "done", "artifacts": all_artifacts}
