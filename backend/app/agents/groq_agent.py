from google.genai import types
import asyncio
import json
import logging
import os
from collections.abc import AsyncGenerator
from typing import Any, List, Optional

from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event

from groq import AsyncGroq
from pydantic import ConfigDict, PrivateAttr

logger = logging.getLogger(__name__)


class GroqAgent(BaseAgent):
    """
    A custom ADK agent that uses GROQ as its underlying LLM provider.
    """

    # Allow extra fields for Groq-specific config and skip strict validation for AsyncGroq
    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)

    model: str = "llama-3.1-8b-instant"
    api_key: Optional[str] = None
    instruction: Optional[str] = None
    tools: List[Any] = []
    sub_agents: List[Any] = []

    # Use PrivateAttr for the client to avoid Pydantic serialization/validation issues
    _client: AsyncGroq = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        self.api_key = data.get("api_key") or os.getenv("GROQ_API_KEY")
        self._client = AsyncGroq(api_key=self.api_key)

    def _sanitize_groq_schema(self, schema: Any) -> Any:
        """
        Recursively sanitizes the schema for Groq/OpenAI compatibility:
        - Removes None values.
        - Converts Enums to lowercase strings.
        - Maps snake_case keys to JSON schema conventional keys.
        """
        if isinstance(schema, list):
            return [self._sanitize_groq_schema(item) for item in schema]
        if isinstance(schema, dict):
            sanitized = {}
            for k, v in schema.items():
                if v is None:
                    continue

                # Map snake_case to camelCase for standard JSON schema
                new_key = {
                    "additional_properties": "additionalProperties",
                    "any_of": "anyOf",
                    "max_items": "maxItems",
                    "max_length": "maxLength",
                    "max_properties": "maxProperties",
                    "min_items": "minItems",
                    "min_length": "minLength",
                    "min_properties": "minProperties",
                }.get(k, k)

                val = self._sanitize_groq_schema(v)

                # Special handling for 'type' enums
                if new_key == "type" and hasattr(val, "value"):
                    val = val.value.lower()
                elif new_key == "type" and isinstance(val, str):
                    val = val.lower()

                sanitized[new_key] = val
            return sanitized
        return schema

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Executes the agent logic by calling GROQ API.
        Handles tool execution by calling tools and passing results back to the LLM.
        """
        logger.info(f"GroqAgent '{self.name}' starting execution.")

        max_tool_iterations = 10
        iteration = 0

        while iteration < max_tool_iterations:
            iteration += 1

            # 1. Prepare messages from history
            messages = []
            if self.instruction:
                messages.append({"role": "system", "content": self.instruction})

            # ADK history is in ctx.session.events
            for event in ctx.session.events:
                if event.content and event.content.parts:
                    role = "user" if event.author == "user" else "assistant"

                    text_parts = [p.text for p in event.content.parts if p.text]
                    if text_parts:
                        messages.append({"role": role, "content": " ".join(text_parts)})

                    for part in event.content.parts:
                        if part.function_call:
                            messages.append(
                                {
                                    "role": "assistant",
                                    "tool_calls": [
                                        {
                                            "id": part.function_call.name + "_call",
                                            "type": "function",
                                            "function": {
                                                "name": part.function_call.name,
                                                "arguments": json.dumps(part.function_call.args),
                                            },
                                        }
                                    ],
                                }
                            )
                        if part.function_response:
                            messages.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": part.function_response.name + "_call",
                                    "content": json.dumps(part.function_response.response),
                                }
                            )

            # 2. Prepare tools
            groq_tools = []
            tool_map = {}
            for tool in self.tools:
                decl = tool._get_declaration()
                if decl:
                    tool_map[decl.name] = tool
                    raw_schema = (
                        decl.parameters.model_dump()
                        if hasattr(decl.parameters, "model_dump")
                        else decl.parameters
                    )
                    schema = self._sanitize_groq_schema(raw_schema)
                    groq_tools.append(
                        {
                            "type": "function",
                            "function": {
                                "name": decl.name,
                                "description": decl.description,
                                "parameters": schema,
                            },
                        }
                    )

            logger.debug(f"GroqAgent tools: {[t['function']['name'] for t in groq_tools]}")
            logger.debug(f"GroqAgent tool schemas: {groq_tools}")

            try:
                # 3. Call GROQ
                call_kwargs = {
                    "messages": messages,
                    "model": self.model,
                    "stream": True,
                }
                if groq_tools:
                    call_kwargs["tools"] = groq_tools
                    call_kwargs["tool_choice"] = "auto"

                stream = await self._client.chat.completions.create(**call_kwargs)

                tool_calls_deltas = {}
                text_content = []
                has_tool_calls = False

                async for chunk in stream:
                    if not chunk.choices:
                        continue

                    delta = chunk.choices[0].delta

                    if delta.content:
                        text_content.append(delta.content)
                        yield Event(
                            invocation_id=ctx.invocation_id,
                            author=self.name,
                            branch=ctx.branch,
                            content=types.Content(
                                role="model", parts=[types.Part(text=delta.content)]
                            ),
                            partial=True,
                        )

                    if delta.tool_calls:
                        has_tool_calls = True
                        for tc_delta in delta.tool_calls:
                            idx = tc_delta.index
                            if idx not in tool_calls_deltas:
                                tool_calls_deltas[idx] = {"id": "", "name": "", "arguments": ""}

                            if tc_delta.id:
                                tool_calls_deltas[idx]["id"] = tc_delta.id
                            if tc_delta.function:
                                if tc_delta.function.name:
                                    tool_calls_deltas[idx]["name"] = tc_delta.function.name
                                if tc_delta.function.arguments:
                                    tool_calls_deltas[idx]["arguments"] += (
                                        tc_delta.function.arguments
                                    )

                # If no tool calls, we're done
                if not has_tool_calls or not tool_calls_deltas:
                    yield Event(
                        invocation_id=ctx.invocation_id,
                        author=self.name,
                        branch=ctx.branch,
                        content=types.Content(role="model", parts=[types.Part(text="")]),
                        partial=False,
                    )
                    break

                # Execute tools and yield results
                for idx, tc in tool_calls_deltas.items():
                    if not tc["name"]:
                        continue

                    try:
                        args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                    except Exception as e:
                        logger.warning(f"Failed to parse tool arguments: {e}")
                        args = {}

                    # Find and execute the tool
                    tool = tool_map.get(tc["name"])
                    if tool:
                        try:
                            # Execute the tool function directly
                            result = tool.func(**args)
                        except Exception as e:
                            logger.error(f"Tool execution error for {tc['name']}: {e}")
                            result = {"error": str(e)}

                        logger.info(f"Tool {tc['name']} executed, result: {str(result)[:100]}")

                        # Yield function call event
                        yield Event(
                            invocation_id=ctx.invocation_id,
                            author=self.name,
                            branch=ctx.branch,
                            content=types.Content(
                                role="model",
                                parts=[
                                    types.Part(
                                        function_call=types.FunctionCall(name=tc["name"], args=args)
                                    )
                                ],
                            ),
                            partial=False,
                        )

                        # Yield function response event
                        yield Event(
                            invocation_id=ctx.invocation_id,
                            author="tool",
                            branch=ctx.branch,
                            content=types.Content(
                                role="tool",
                                parts=[
                                    types.Part(
                                        function_response=types.FunctionResponse(
                                            name=tc["name"],
                                            id=tc["id"] or tc["name"] + "_call",
                                            response=result,
                                        )
                                    )
                                ],
                            ),
                            partial=False,
                        )
                    else:
                        logger.warning(f"Tool not found: {tc['name']}")

                # Continue to next iteration to get LLM response to tool results

            except Exception as e:
                logger.error(f"Error in GroqAgent: {e}", exc_info=True)
                yield Event(
                    invocation_id=ctx.invocation_id,
                    author=self.name,
                    branch=ctx.branch,
                    content=types.Content(
                        role="model", parts=[types.Part(text=f"Error: {str(e)}")]
                    ),
                    partial=False,
                )
                break


if __name__ == "__main__":
    # Quick verification demo
    import dotenv
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService

    dotenv.load_dotenv()

    async def main():
        logging.basicConfig(level=logging.ERROR)

        # Initialize agent
        def get_weather(location: str):
            """Gets the current weather in a location."""
            return f"The weather in {location} is sunny, 25°C."

        weather_tool = FunctionTool(func=get_weather)

        agent = GroqAgent(
            name="GroqHelper",
            instruction="You are a helpful assistant powered by GROQ. Use tools if needed.",
            description="A helpful assistant using Llama 3 via Groq with tool support.",
            tools=[weather_tool],
        )

        # Session setup
        session_service = InMemorySessionService()
        session_id = "session_123"
        user_id = "user_1"
        await session_service.create_session(
            app_name="groq_test", user_id=user_id, session_id=session_id
        )

        test_runner = Runner(agent=agent, app_name="groq_test", session_service=session_service)

        print("--- Calling GroqAgent ---")
        user_content = types.Content(
            role="user", parts=[types.Part(text="What's the weather in Tokyo?")]
        )

        async for event in test_runner.run_async(
            user_id=user_id, session_id=session_id, new_message=user_content
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(part.text, end="", flush=True)
                    if part.function_call:
                        print(f"\n[Tool Call] {part.function_call.name}({part.function_call.args})")
        print("\n--- Done ---")

    if os.getenv("LLM_API_KEY") or os.getenv("MOCK_GROQ"):
        if not os.getenv("LLM_API_KEY"):
            print("Running with MOCK GROQ data...")
        asyncio.run(main())
    else:
        print("Set LLM_API_KEY to run the real demo, or MOCK_GROQ=1 for a simulated run.")
