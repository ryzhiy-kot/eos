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


# Data Command Schemas
class PlotRequest(BaseModel):
    pane_id: str
    prompt: str


class RunRequest(BaseModel):
    pane_id: str
    code: str


class DiffRequest(BaseModel):
    pane_id_1: str
    pane_id_2: str


class SummarizeRequest(BaseModel):
    pane_id: str


# Response Models
class BaseResponse(BaseModel):
    """Base response model for all API responses"""

    success: bool = True
    message: Optional[str] = None


class ErrorResponse(BaseResponse):
    """Error response model"""

    success: bool = False
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class PlotResult(BaseModel):
    """Result data for plot command"""

    type: str = "visual"
    url: str
    description: str
    metadata: Optional[Dict[str, Any]] = None


class PlotResponse(BaseResponse):
    """Response for plot command"""

    result: PlotResult


class RunResult(BaseModel):
    """Result data for run command"""

    type: str = "code"
    output: str
    status: str  # success, error, warning
    execution_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class RunResponse(BaseResponse):
    """Response for run command"""

    result: RunResult


class DiffResult(BaseModel):
    """Result data for diff command"""

    type: str = "data"
    differences: str
    summary: str
    changes_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class DiffResponse(BaseResponse):
    """Response for diff command"""

    result: DiffResult


class SummarizeResult(BaseModel):
    """Result data for summarize command"""

    type: str = "doc"
    summary: str
    key_points: list[str]
    word_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class SummarizeResponse(BaseResponse):
    """Response for summarize command"""

    result: SummarizeResult


class DeleteWorkspaceResponse(BaseResponse):
    """Response for workspace deletion"""

    status: str


class HealthCheckResponse(BaseModel):
    """Response for health check endpoint"""

    status: str


class RootResponse(BaseModel):
    """Response for root endpoint"""

    message: str
