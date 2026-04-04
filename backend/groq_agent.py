import os
import asyncio
from typing import AsyncGenerator, List, Optional, Any
import logging
import json

from groq import AsyncGroq
from google.genai import types
from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event
from google.adk.tools import FunctionTool
from pydantic import ConfigDict, PrivateAttr

logger = logging.getLogger(__name__)

class GroqAgent(BaseAgent):
    """
    A custom ADK agent that uses GROQ as its underlying LLM provider.
    """
    # Allow extra fields for Groq-specific config and skip strict validation for AsyncGroq
    model_config = ConfigDict(extra='allow', arbitrary_types_allowed=True)

    model: str = "llama-3.1-8b-instant"
    api_key: Optional[str] = None
    instruction: Optional[str] = None
    tools: List[FunctionTool] = []
    
    # Use PrivateAttr for the client to avoid Pydantic serialization/validation issues
    _client: AsyncGroq = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        self.api_key = self.api_key or os.getenv("LLM_API_KEY")
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

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Executes the agent logic by calling GROQ API.
        """
        logger.info(f"GroqAgent '{self.name}' starting execution.")

        # 1. Prepare messages
        messages = []
        if self.instruction:
            messages.append({"role": "system", "content": self.instruction})

        # ADK history is in ctx.session.events
        for event in ctx.session.events:
            if event.content and event.content.parts:
                # Map ADK/GenAI roles to Groq roles
                # event.author 'user' maps to 'user', anything else to 'assistant'
                role = "user" if event.author == "user" else "assistant"
                
                text_parts = [p.text for p in event.content.parts if p.text]
                if text_parts:
                    messages.append({"role": role, "content": " ".join(text_parts)})
                
                # Handle existing tool calls in history
                for part in (event.content.parts if event.content else []):
                    if part.function_call:
                        # Convert GenAI types.FunctionCall to Groq tool_call
                        messages.append({
                            "role": "assistant",
                            "tool_calls": [{
                                "id": part.function_call.name + "_call", # Mock ID if not present
                                "type": "function",
                                "function": {
                                    "name": part.function_call.name,
                                    "arguments": json.dumps(part.function_call.args)
                                }
                            }]
                        })
                    if part.function_response:
                        messages.append({
                            "role": "tool",
                            "tool_call_id": part.function_response.name + "_call",
                            "content": json.dumps(part.function_response.response)
                        })

        # 2. Prepare tools
        groq_tools = []
        for tool in self.tools:
            decl = tool._get_declaration()
            if decl:
                raw_schema = decl.parameters.model_dump() if hasattr(decl.parameters, "model_dump") else decl.parameters
                schema = self._sanitize_groq_schema(raw_schema)
                
                logger.debug(f"Tool '{decl.name}' sanitized schema: {schema}")
                groq_tools.append({
                    "type": "function",
                    "function": {
                        "name": decl.name,
                        "description": decl.description,
                        "parameters": schema
                    }
                })

        try:
            # 3. Call GROQ with streaming
            call_kwargs = {
                "messages": messages,
                "model": self.model,
                "stream": True,
            }
            if groq_tools:
                call_kwargs["tools"] = groq_tools
                call_kwargs["tool_choice"] = "auto"

            stream = await self._client.chat.completions.create(**call_kwargs)

            tool_calls_deltas = {} # index -> {id, name, arguments}

            async for chunk in stream:
                if not chunk.choices:
                    continue
                
                delta = chunk.choices[0].delta
                
                # logger.debug(f"Groq Delta: {delta}")

                # Handle text content
                if delta.content:
                    yield Event(
                        invocation_id=ctx.invocation_id,
                        author=self.name,
                        branch=ctx.branch,
                        content=types.Content(
                            role="model",
                            parts=[types.Part(text=delta.content)]
                        ),
                        partial=True
                    )
                
                # Handle tool calls (accumulate)
                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index
                        if idx not in tool_calls_deltas:
                            tool_calls_deltas[idx] = {"id": "", "name": "", "arguments": ""}
                        
                        if tc_delta.id:
                            tool_calls_deltas[idx]["id"] = tc_delta.id
                        if tc_delta.function:
                            if tc_delta.function.name:
                                tool_calls_deltas[idx]["name"] = tc_delta.function.name
                                logger.debug(f"Found tool call name: {tc_delta.function.name}")
                            if tc_delta.function.arguments:
                                tool_calls_deltas[idx]["arguments"] += tc_delta.function.arguments

            # Yield completed tool calls after the stream loop
            for idx, tc in tool_calls_deltas.items():
                if tc["name"]:
                    try:
                        args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                    except Exception as e:
                        logger.warning(f"Failed to parse tool arguments for {tc['name']}: {e}")
                        args = {"raw_arguments": tc["arguments"]}
                    
                    yield Event(
                        invocation_id=ctx.invocation_id,
                        author=self.name,
                        branch=ctx.branch,
                        content=types.Content(
                            role="model",
                            parts=[types.Part(
                                function_call=types.FunctionCall(
                                    name=tc["name"],
                                    args=args
                                )
                            )]
                        ),
                        partial=False
                    )
            
            # Final completion event
            yield Event(
                invocation_id=ctx.invocation_id,
                author=self.name,
                branch=ctx.branch,
                content=types.Content(
                    role="model",
                    parts=[types.Part(text="")]
                ),
                partial=False
            )

        except Exception as e:
            logger.error(f"Error in GroqAgent: {e}", exc_info=True)
            yield Event(
                invocation_id=ctx.invocation_id,
                author=self.name,
                branch=ctx.branch,
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=f"Error calling GROQ: {str(e)}")]
                ),
                partial=False
            )

if __name__ == "__main__":
    # Quick verification demo
    from google.adk.sessions import InMemorySessionService
    from google.adk.runners import Runner
    import dotenv
    dotenv.load_dotenv()

    async def main():
        logging.basicConfig(level=logging.ERROR)
        
        # Initialize agent
        def get_weather(location: str):
            """Gets the current weather in a location."""
            return f"The weather in {location} is sunny, 25°C."

        weather_tool = FunctionTool(
            func=get_weather
        )

        agent = GroqAgent(
            name="GroqHelper",
            instruction="You are a helpful assistant powered by GROQ. Use tools if needed.",
            description="A helpful assistant using Llama 3 via Groq with tool support.",
            tools=[weather_tool]
        )

        # Session setup
        session_service = InMemorySessionService()
        session_id = "session_123"
        user_id = "user_1"
        await session_service.create_session(app_name="groq_test", user_id=user_id, session_id=session_id)
        
        test_runner = Runner(
            agent=agent,
            app_name="groq_test",
            session_service=session_service
        )

        print("--- Calling GroqAgent ---")
        user_content = types.Content(role="user", parts=[types.Part(text="What's the weather in Tokyo?")])
        
        async for event in test_runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_content
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
