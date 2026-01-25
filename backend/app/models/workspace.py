from sqlalchemy import Column, String, JSON, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
import uuid
from app.db.base_class import Base


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    state = Column(JSON, default=lambda: {"panes": [], "visibleIds": []})
    is_archived = Column(Boolean, default=False)
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    members = relationship("WorkspaceMember", back_populates="workspace")
