# PROJECT: MONAD
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
