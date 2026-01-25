from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, Dict


class UserBase(BaseModel):
    user_id: str
    profile: Dict[str, Any] = {}
    enabled: bool = True


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class WorkspaceMemberBase(BaseModel):
    workspace_id: str
    user_id: int
    role: str = "VIEWER"


class WorkspaceMember(WorkspaceMemberBase):
    model_config = ConfigDict(from_attributes=True)


class AuthSyncRequest(BaseModel):
    user_id: str
