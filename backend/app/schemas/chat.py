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

from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, Dict, List
from datetime import datetime
from .base import BaseResponse
from .artifact import Artifact


class ChatMessageBase(BaseModel):
    role: str
    content: str


class ChatMessageCreate(ChatMessageBase):
    session_id: str


class ChatMessage(ChatMessageBase):
    id: int
    session_id: str
    created_at: datetime
    artifacts: List[Artifact] = []

    model_config = ConfigDict(from_attributes=True)


class ChatSessionBase(BaseModel):
    name: str
    workspace_id: str


class ChatSessionCreate(ChatSessionBase):
    pass


class ChatSessionUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


class ChatSession(ChatSessionBase):
    id: str
    is_active: bool
    created_at: datetime
    messages: List[ChatMessage] = []

    model_config = ConfigDict(from_attributes=True)


class ExecutionRequest(BaseModel):
    type: str  # "command" or "chat"
    session_id: str
    command_name: Optional[str] = None
    args: Optional[List[str]] = None
    action: Optional[str] = None
    context_artifacts: Optional[Dict[str, Artifact]] = None
    referenced_artifact_ids: Optional[List[str]] = []
    stream: bool = False


class ExecutionResult(BaseModel):
    output_message: Optional[ChatMessage] = None
    new_artifacts: Optional[List[Artifact]] = None
    status: str = "success"  # success, error, warning
    metadata: Optional[Dict[str, Any]] = None


class ExecutionResponse(BaseResponse):
    result: ExecutionResult
