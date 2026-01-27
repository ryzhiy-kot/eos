from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, Optional
from datetime import datetime


class ArchivedPaneBase(BaseModel):
    workspace_id: str
    pane_data: Dict[str, Any]


class ArchivedPaneCreate(ArchivedPaneBase):
    user_id: Optional[int] = None


class ArchivedPane(ArchivedPaneBase):
    id: str
    user_id: Optional[int]
    archived_at: datetime

    model_config = ConfigDict(from_attributes=True)
