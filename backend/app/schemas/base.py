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
