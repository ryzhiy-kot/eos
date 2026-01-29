from abc import ABC, abstractmethod
from typing import List, Optional, AsyncGenerator, Any, Dict, Literal
from pydantic import BaseModel, Field
from app.schemas.artifact import Artifact

class LLMMessage(BaseModel):
    role: str
    content: str
    artifacts: List[Artifact] = []

class LLMRequest(BaseModel):
    session_id: str
    messages: List[LLMMessage]
    context_artifacts: List[Artifact] = []

class LLMEvent(BaseModel):
    type: str

class TextDeltaEvent(LLMEvent):
    type: Literal["text_delta"] = "text_delta"
    content: str

class ArtifactStartEvent(LLMEvent):
    type: Literal["artifact_start"] = "artifact_start"
    artifact_id: str
    artifact_type: str
    artifact_metadata: Optional[Dict[str, Any]] = None

class ArtifactChunkEvent(LLMEvent):
    type: Literal["artifact_chunk"] = "artifact_chunk"
    artifact_id: str
    chunk: str

class ArtifactEndEvent(LLMEvent):
    type: Literal["artifact_end"] = "artifact_end"
    artifact_id: str

class LLMProvider(ABC):
    @abstractmethod
    async def generate_stream(self, request: LLMRequest) -> AsyncGenerator[LLMEvent, None]:
        pass
