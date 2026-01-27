from sqlalchemy import Column, String, Integer, JSON, ForeignKey, DateTime
from datetime import datetime, UTC
import uuid
from app.db.base_class import Base


class ArchivedPane(Base):
    __tablename__ = "archived_panes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(
        String, ForeignKey("workspaces.id"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    pane_data = Column(JSON, nullable=False)
    archived_at = Column(DateTime, default=lambda: datetime.now(UTC))
