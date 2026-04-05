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
    session_id: str | None = None
    history: list[dict] | None = None


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


class SessionCreate(BaseModel):
    name: str | None = None


class SessionUpdate(BaseModel):
    name: str


class SessionResponse(BaseModel):
    id: str
    user_id: str
    name: str
    created_at: datetime
    updated_at: datetime


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]


class ArtifactResponse(BaseModel):
    id: str
    session_id: str
    type: str
    title: str | None = None
    spec: dict | None = None
    columns: list | None = None
    data: dict | None = None
    content: str | None = None
    format: str | None = None
    created_at: datetime


class ArtifactListResponse(BaseModel):
    artifacts: list[ArtifactResponse]


class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime


class MessageListResponse(BaseModel):
    messages: list[MessageResponse]


class PanelCreate(BaseModel):
    artifact_id: str
    name: str
    bq_function: str
    bq_params: dict = {}
    refresh_interval: int = 0


class PanelUpdate(BaseModel):
    name: str | None = None
    refresh_interval: int | None = None


class PanelResponse(BaseModel):
    id: str
    artifact_id: str
    name: str
    bq_function: str
    bq_params: dict
    refresh_interval: int
    is_pinned: bool
    created_at: datetime
    updated_at: datetime


class PanelDataResponse(BaseModel):
    data: dict
    last_updated: datetime
