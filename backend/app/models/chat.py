from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Table,
)
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
import uuid
from app.db.base_class import Base

# Association table for many-to-many relationship
message_artifacts = Table(
    "message_artifacts",
    Base.metadata,
    Column("message_id", Integer, ForeignKey("chat_messages.id"), primary_key=True),
    Column("artifact_id", String, ForeignKey("artifacts.id"), primary_key=True),
)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    artifacts = relationship("Artifact", back_populates="session", lazy="selectin")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    session = relationship("ChatSession", back_populates="messages")
    # Formal relationship to artifacts
    artifacts = relationship(
        "Artifact",
        secondary=message_artifacts,
        back_populates="messages",
        lazy="selectin",
    )
