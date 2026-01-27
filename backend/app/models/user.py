from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, unique=True, index=True, nullable=False)  # LDAP Login
    profile = Column(JSON, default=dict)
    enabled = Column(Boolean, default=True)
    active_workspace_id = Column(String, nullable=True)

    memberships = relationship("WorkspaceMember", back_populates="user")


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    workspace_id = Column(String, ForeignKey("workspaces.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    role = Column(String, default="VIEWER")  # OWNER, EDITOR, VIEWER

    user = relationship("User", back_populates="memberships")
    workspace = relationship("Workspace", back_populates="members")
