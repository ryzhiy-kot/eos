from typing import Dict
from app.core.llm_protocol import TextDeltaEvent
import logging
import os
from typing import AsyncGenerator
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import uvicorn
from app.core.llm_protocol import LLMRequest

from groq import Groq

from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Groq EoS Demo Provider")
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.FileHandler("groq.app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# --- Configuration ---
API_KEY = os.getenv("LLM_API_KEY")
MODEL_NAME = os.getenv("LLM_MODEL_NAME", "llama-3.1-8b-instant")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "20"))
logger.info(API_KEY)
logger.info(MODEL_NAME)
logger.info(MAX_TOKENS)


async def generate_event_stream(request: LLMRequest) -> AsyncGenerator[str, None]:
    """
    Generates SSE events compliant with EoS LLM Protocol.
    """
    logger.info(f"Received request for session {request.session_id}")
    client = Groq(api_key=API_KEY or request.api_key)
    # 2. Extract last user message
    if not request.messages:
        logger.warning("No messages in request")
        return

    # 3. Prepare tools
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "The city or location"}
                    },
                    "required": ["location"]
                }
            }
        }
    ]

    try:
        with client.chat.completions.with_streaming_response.create(
            messages=[
                {"role": msg.role, "content": msg.content} for msg in request.messages
            ],
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS,
            tools=tools,
            tool_choice="auto",
        ) as response:
            tool_calls_accumulator = {} # index -> {name, arguments}

            for line in response.iter_lines():
                if not line:
                    continue
                
                # Groq returns 'data: {...}'
                if line.startswith("data: "):
                    line = line[6:]
                if line == "[DONE]":
                    break
                
                try:
                    data = json.loads(line)
                    delta = data["choices"][0]["delta"]
                    
                    if "content" in delta and delta["content"]:
                        yield _sse(
                            TextDeltaEvent(type="text_delta", content=delta["content"]).model_dump()
                        )
                    
                    if "tool_calls" in delta:
                        for tc in delta["tool_calls"]:
                            idx = tc["index"]
                            if idx not in tool_calls_accumulator:
                                tool_calls_accumulator[idx] = {"name": "", "arguments": ""}
                            
                            if "function" in tc:
                                if "name" in tc["function"] and tc["function"]["name"]:
                                    tool_calls_accumulator[idx]["name"] = tc["function"]["name"]
                                if "arguments" in tc["function"] and tc["function"]["arguments"]:
                                    tool_calls_accumulator[idx]["arguments"] += tc["function"]["arguments"]

                except Exception as ex:
                    logger.error(f"Error parsing Groq delta: {ex}")

            # Yield completed tool calls after the stream loop
            for idx, tc in tool_calls_accumulator.items():
                if tc["name"]:
                    try:
                        args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                    except Exception as e:
                        logger.warning(f"Failed to parse tool arguments in demo: {e}")
                        args = {"raw_arguments": tc["arguments"]}
                    
                    from app.core.llm_protocol import ToolCallEvent, FunctionCall
                    yield _sse(
                        ToolCallEvent(
                            type="tool_call",
                            tool_calls=[FunctionCall(name=tc["name"], args=args)]
                        ).model_dump()
                    )

                except Exception as ex:
                    logger.error(f"Error parsing Groq delta: {ex}")

    except Exception as e:
        logger.error(f"Error in Groq completion: {e}")


def _sse(data: Dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


@app.post("/generate")
async def generate(request: LLMRequest):
    return StreamingResponse(
        generate_event_stream(request), media_type="text/event-stream"
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
