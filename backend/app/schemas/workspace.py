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
