from datetime import datetime

from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    role: str
    is_active: bool
    last_login: datetime | None = None


class InstrumentResponse(BaseModel):
    id: str
    symbol: str
    name: str
    exchange: str | None
    asset_class: str
    currency: str


class QuoteResponse(BaseModel):
    symbol: str
    bid: float
    ask: float
    last: float
    change: float
    change_pct: float
    volume: float
    timestamp: datetime


class OHLCVResponse(BaseModel):
    timestamp: datetime | str
    open: float
    high: float
    low: float
    close: float
    volume: float


class PositionResponse(BaseModel):
    id: str
    symbol: str
    instrument_name: str
    book: str
    strategy: str
    desk: str
    quantity: float
    avg_price: float
    current_price: float
    pnl: float
    pnl_pct: float
    delta: float | None = None
    gamma: float | None = None
    vega: float | None = None
    theta: float | None = None


class RiskResponse(BaseModel):
    timestamp: str
    var_95: float
    var_99: float
    delta: float
    gamma: float
    vega: float
    theta: float
    pnl: float
    by_desk: list[dict] = []


class PnLAttributionResponse(BaseModel):
    timestamp: str
    total_pnl: float
    by_instrument: list[dict]
    by_desk: list[dict]
    by_factor: list[dict]
    top_contributors: list[dict]
    top_detractors: list[dict]


class AgentChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class AgentChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    content: str
    charts: list[dict] = []
    tables: list[dict] = []
    created_at: datetime


class ReportRequest(BaseModel):
    report_type: str  # risk, pnl, attribution
    parameters: dict = {}
    format: str = "pdf"
