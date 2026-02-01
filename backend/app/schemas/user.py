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


class UserBase(BaseModel):
    user_id: str
    profile: Dict[str, Any] = {}
    enabled: bool = True


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int
    active_workspace_id: Optional[str] = None
    memberships: List["WorkspaceMember"] = []
    model_config = ConfigDict(from_attributes=True)


class WorkspaceMemberBase(BaseModel):
    workspace_id: str
    user_id: int
    role: str = "VIEWER"


class WorkspaceMember(WorkspaceMemberBase):
    model_config = ConfigDict(from_attributes=True)


class UpdateActiveWorkspaceRequest(BaseModel):
    user_id: str
    workspace_id: str
