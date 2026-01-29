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

from pydantic import BaseModel
from typing import Optional


class BaseResponse(BaseModel):
    """Base response model for all API responses"""

    success: bool = True
    message: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Response for health check endpoint"""

    status: str


class RootResponse(BaseModel):
    """Response for root endpoint"""

    message: str
