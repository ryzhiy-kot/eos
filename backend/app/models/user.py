import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TRADER = "trader"
    RISK_MANAGER = "risk_manager"
    VIEWER = "viewer"


class AssetClass(str, enum.Enum):
    EQUITY = "equity"
    FIXED_INCOME = "fixed_income"
    FX = "fx"
    COMMODITY = "commodity"
    DERIVATIVE = "derivative"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.VIEWER)
    ldap_dn: Mapped[str | None] = mapped_column(String(500), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    positions: Mapped[list["Position"]] = relationship(back_populates="user")
    conversations: Mapped[list["AgentConversation"]] = relationship(back_populates="user")


class Instrument(Base):
    __tablename__ = "instruments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    exchange: Mapped[str | None] = mapped_column(String(50), nullable=True)
    asset_class: Mapped[AssetClass] = mapped_column(SAEnum(AssetClass))
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class Desk(Base):
    __tablename__ = "desks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    strategies: Mapped[list["Strategy"]] = relationship(back_populates="desk")


class Strategy(Base):
    __tablename__ = "strategies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    desk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("desks.id"))

    desk: Mapped["Desk"] = relationship(back_populates="strategies")
    books: Mapped[list["Book"]] = relationship(back_populates="strategy")


class Book(Base):
    __tablename__ = "books"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    strategy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("strategies.id"))

    strategy: Mapped["Strategy"] = relationship(back_populates="books")
    positions: Mapped[list["Position"]] = relationship(back_populates="book")


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    instrument_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instruments.id"))
    book_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("books.id"))
    quantity: Mapped[float] = mapped_column(Numeric(20, 6))
    avg_price: Mapped[float] = mapped_column(Numeric(20, 6))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="positions")
    instrument: Mapped["Instrument"] = relationship()
    book: Mapped["Book"] = relationship(back_populates="positions")


class RiskSnapshot(Base):
    __tablename__ = "risk_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("books.id"), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    var_95: Mapped[float | None] = mapped_column(Numeric(20, 6), nullable=True)
    var_99: Mapped[float | None] = mapped_column(Numeric(20, 6), nullable=True)
    delta: Mapped[float | None] = mapped_column(Numeric(20, 6), nullable=True)
    gamma: Mapped[float | None] = mapped_column(Numeric(20, 6), nullable=True)
    vega: Mapped[float | None] = mapped_column(Numeric(20, 6), nullable=True)
    theta: Mapped[float | None] = mapped_column(Numeric(20, 6), nullable=True)
    pnl: Mapped[float | None] = mapped_column(Numeric(20, 6), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instrument_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instruments.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    open: Mapped[float] = mapped_column(Numeric(20, 6))
    high: Mapped[float] = mapped_column(Numeric(20, 6))
    low: Mapped[float] = mapped_column(Numeric(20, 6))
    close: Mapped[float] = mapped_column(Numeric(20, 6))
    volume: Mapped[float | None] = mapped_column(Numeric(20, 2), nullable=True)


class AgentConversation(Base):
    __tablename__ = "agent_conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[list["AgentMessage"]] = relationship(back_populates="conversation")


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_conversations.id"))
    role: Mapped[str] = mapped_column(String(20))  # user, assistant, system
    content_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation: Mapped["AgentConversation"] = relationship(back_populates="messages")
