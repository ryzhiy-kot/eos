"""Database models for the session service.

Defines SQLAlchemy ORM models for sessions, messages, and artifacts.
Separated from service layer to follow SRP — models define structure,
services handle business logic.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Session(Base):
    """User session model."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    artifacts: Mapped[list[Artifact]] = relationship(
        "Artifact", back_populates="session", cascade="all, delete-orphan"
    )
    messages: Mapped[list[Message]] = relationship(
        "Message", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, user_id={self.user_id}, name={self.name})>"


class Message(Base):
    """Chat message within a session."""

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped[Session] = relationship("Session", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role}, session_id={self.session_id})>"


class Artifact(Base):
    """Generated artifact (chart, table, PDF, text) within a session."""

    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    spec: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    columns: Mapped[list | None] = mapped_column(JSON, nullable=True)
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    format: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped[Session] = relationship("Session", back_populates="artifacts")

    def __repr__(self) -> str:
        return f"<Artifact(id={self.id}, type={self.type}, session_id={self.session_id})>"