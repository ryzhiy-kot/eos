import os
import random
import json
import httpx
from typing import AsyncGenerator
from app.core.llm_protocol import (
    LLMProvider,
    LLMRequest,
    LLMEvent,
    TextDeltaEvent,
    ArtifactStartEvent,
    ArtifactChunkEvent,
    ArtifactEndEvent,
)

class MockLLMProvider(LLMProvider):
    async def generate_stream(self, request: LLMRequest) -> AsyncGenerator[LLMEvent, None]:
        # Mocking context awareness
        if request.context_artifacts:
             refs = ", ".join([f"@[{a.id}]" for a in request.context_artifacts])
             yield TextDeltaEvent(content=f"**Context Received**: I'm now processing {refs}. \n\n")

        phrases = [
            "I've analyzed the referenced artifacts.",
            " Based on the context you provided,",
            " I recommend looking at these data points.",
            " Could you clarify which part of the artifact you're most interested in?",
        ]

        # Always yield at least one chunk
        yield TextDeltaEvent(content=phrases[0])

        # Simulate thinking or incremental generation
        for chunk in phrases[1:]:
            if random.random() > 0.5: # specific selection
                yield TextDeltaEvent(content=chunk)

        # Mock artifact generation
        # Let's say we generate a plot sometimes
        if random.random() > 0.7:
             art_id = f"A_PLOT_{random.randint(1000, 9999)}"
             yield ArtifactStartEvent(
                 artifact_id=art_id,
                 artifact_type="visual",
                 artifact_metadata={"alt": "Plot"}
             )

             payload = {
                "format": "svg",
                "url": f"data:image/svg+xml,<svg>Mock plot {art_id}</svg>",
                "alt": "Plot",
             }
             payload_str = json.dumps(payload)
             # Simulate chunking of payload
             chunk_size = 10
             for i in range(0, len(payload_str), chunk_size):
                 yield ArtifactChunkEvent(artifact_id=art_id, chunk=payload_str[i:i+chunk_size])

             yield ArtifactEndEvent(artifact_id=art_id)


class HttpLLMProvider(LLMProvider):
    def __init__(self):
        self.url = os.getenv("LLM_SERVICE_URL", "http://localhost:8001/generate")
        self.api_key = os.getenv("LLM_API_KEY", "")

    async def generate_stream(self, request: LLMRequest) -> AsyncGenerator[LLMEvent, None]:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                self.url,
                json=request.model_dump(mode="json"),
                headers=headers,
                timeout=60.0
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        event_type = data.get("type")
                        if event_type == "text_delta":
                            yield TextDeltaEvent(**data)
                        elif event_type == "artifact_start":
                            yield ArtifactStartEvent(**data)
                        elif event_type == "artifact_chunk":
                            yield ArtifactChunkEvent(**data)
                        elif event_type == "artifact_end":
                            yield ArtifactEndEvent(**data)
                    except json.JSONDecodeError:
                        pass

def get_llm_provider() -> LLMProvider:
    provider_type = os.getenv("LLM_PROVIDER", "mock").lower()
    if provider_type == "http":
        return HttpLLMProvider()
    return MockLLMProvider()
