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

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Any, Dict, List
from datetime import datetime


class MutationOrigin(BaseModel):
    type: str  # adhoc_command, chat_inference, manual_edit
    sessionId: Optional[str] = None
    prompt: Optional[str] = None
    triggeringCommand: Optional[str] = None


class MutationRecord(BaseModel):
    id: int
    artifact_id: str
    version_id: str
    parent_id: Optional[str] = None
    timestamp: datetime
    origin: MutationOrigin
    change_summary: Optional[str] = None
    payload: Any
    checksum: Optional[str] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


# Artifact Structured Payloads
class ArtifactCreate(BaseModel):
    id: Optional[str] = None
    type: str
    name: str
    payload: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, validation_alias="artifact_metadata"
    )
    session_id: Optional[str] = None


class ArtifactUpdate(BaseModel):
    name: Optional[str] = None
    payload: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, validation_alias="artifact_metadata"
    )


class Artifact(BaseModel):
    id: str
    type: str  # chat, visual, code, doc, data
    name: str
    payload: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, validation_alias="artifact_metadata"
    )
    session_id: str
    created_at: Optional[datetime] = None
    mutations: List[MutationRecord] = []

    model_config = ConfigDict(from_attributes=True)
