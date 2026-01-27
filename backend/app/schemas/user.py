from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, Dict, List


class UserBase(BaseModel):
    user_id: str
    profile: Dict[str, Any] = {}
    enabled: bool = True
    active_workspace_id: Optional[str] = None


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int
    memberships: List["WorkspaceMember"] = []
    model_config = ConfigDict(from_attributes=True)


class WorkspaceMemberBase(BaseModel):
    workspace_id: str
    user_id: int
    role: str = "VIEWER"


class WorkspaceMember(WorkspaceMemberBase):
    model_config = ConfigDict(from_attributes=True)


class AuthSyncRequest(BaseModel):
    user_id: str


class UpdateActiveWorkspaceRequest(BaseModel):
    user_id: str
    workspace_id: str


class LoginRequest(BaseModel):
    username: str
    password: Optional[str] = None
