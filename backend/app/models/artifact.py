from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from app.db.base_class import Base


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(String, primary_key=True)
    type = Column(String, nullable=False)  # chat, visual, code, doc, data
    payload = Column(JSON, nullable=False)
    artifact_metadata = Column(JSON, default=dict)
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    session = relationship("ChatSession", back_populates="artifacts")
    messages = relationship(
        "ChatMessage", secondary="message_artifacts", back_populates="artifacts"
    )
    mutations = relationship(
        "MutationRecord",
        back_populates="artifact",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class MutationRecord(Base):
    __tablename__ = "mutation_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    artifact_id = Column(String, ForeignKey("artifacts.id"), nullable=False)
    version_id = Column(String, nullable=False)  # e.g., 'v1', 'v2'
    parent_id = Column(String, nullable=True)  # parent version_id
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))
    origin = Column(
        JSON, nullable=False
    )  # {type, sessionId, prompt, triggeringCommand}
    change_summary = Column(String, nullable=True)
    payload = Column(JSON, nullable=False)
    checksum = Column(String, nullable=True)
    status = Column(String, default="committed")

    artifact = relationship("Artifact", back_populates="mutations")
