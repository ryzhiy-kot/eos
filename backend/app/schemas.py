from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, Dict
from datetime import datetime


class UserBase(BaseModel):
    user_id: str
    profile: Dict[str, Any] = {}
    enabled: bool = True


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


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


class WorkspaceMemberBase(BaseModel):
    workspace_id: str
    user_id: int
    role: str = "VIEWER"


class WorkspaceMember(WorkspaceMemberBase):
    model_config = ConfigDict(from_attributes=True)


class AuthSyncRequest(BaseModel):
    user_id: str
