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
from typing import Optional, Any, Dict
from datetime import datetime
from .base import BaseResponse


class WorkspaceBase(BaseModel):
    name: str
    state: Dict[str, Any] = {"panes": [], "visibleIds": []}
    is_archived: bool = False


class WorkspaceCreate(WorkspaceBase):
    pass


class Workspace(WorkspaceBase):
    id: str
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    state: Optional[Dict[str, Any]] = None
    is_archived: Optional[bool] = None


class DeleteWorkspaceResponse(BaseResponse):
    """Response for workspace deletion"""

    status: str
