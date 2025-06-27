"""
Team and collaboration models for multi-user workspace management
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

from src.backend.database.database import Base

class TeamRole(enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

class WorkspacePermission(enum.Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    SHARE = "share"
    ADMIN = "admin"

class Team(Base):
    """Team model for organizing users into groups"""
    __tablename__ = "teams"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Team settings
    max_members = Column(Integer, default=50)
    is_public = Column(Boolean, default=False)
    invite_code = Column(String(50), unique=True)
    
    # Relationships
    creator = relationship("User", back_populates="created_teams")
    memberships = relationship("TeamMembership", back_populates="team", cascade="all, delete-orphan")
    workspace_shares = relationship("WorkspaceShare", back_populates="team")
    
    # Analytics relationships - re-enabled
    team_metrics = relationship("TeamMetrics", back_populates="team", cascade="all, delete-orphan")
    kpis = relationship("KPITracking", back_populates="team", cascade="all, delete-orphan")
    analytics_insights = relationship("AnalyticsInsights", back_populates="team", cascade="all, delete-orphan")

class TeamMembership(Base):
    """User membership in teams with roles"""
    __tablename__ = "team_memberships"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(Enum(TeamRole), default=TeamRole.MEMBER)
    joined_at = Column(DateTime, default=datetime.utcnow)
    invited_by = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    team = relationship("Team", back_populates="memberships")
    user = relationship("User", foreign_keys=[user_id], back_populates="team_memberships")
    inviter = relationship("User", foreign_keys=[invited_by])

class WorkspaceShare(Base):
    """Workspace sharing with users and teams"""
    __tablename__ = "workspace_shares"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    
    # Can be shared with individual user or team
    shared_with_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    shared_with_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    
    permissions = Column(String(255))  # JSON array of permissions
    shared_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    shared_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Access tracking
    last_accessed = Column(DateTime)
    access_count = Column(Integer, default=0)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="shares")
    shared_with_user = relationship("User", foreign_keys=[shared_with_user_id])
    team = relationship("Team", back_populates="workspace_shares")
    sharer = relationship("User", foreign_keys=[shared_by])

class TaskAssignment(Base):
    """Task assignment to multiple users"""
    __tablename__ = "task_assignments"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    
    # Assignment details
    role = Column(String(50))  # "owner", "collaborator", "reviewer"
    estimated_hours = Column(Integer)
    actual_hours = Column(Integer)
    completion_percentage = Column(Integer, default=0)
    
    # Status tracking
    is_active = Column(Boolean, default=True)
    accepted_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    task = relationship("Task", back_populates="assignments")
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="task_assignments")
    assigner = relationship("User", foreign_keys=[assigned_by])

class WorkspaceActivity(Base):
    """Activity log for workspace collaboration"""
    __tablename__ = "workspace_activities"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    action_type = Column(String(50), nullable=False)  # "created", "updated", "shared", "task_added", etc.
    action_description = Column(Text)
    entity_type = Column(String(50))  # "task", "file", "workspace", "user"
    entity_id = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    action_metadata = Column(Text)  # JSON for additional data
    
    # Relationships
    workspace = relationship("Workspace", back_populates="activities")
    user = relationship("User", back_populates="workspace_activities")

class TaskComment(Base):
    """Comments and collaboration on tasks"""
    __tablename__ = "task_comments"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    content = Column(Text, nullable=False)
    comment_type = Column(String(50), default="comment")  # "comment", "status_change", "assignment"
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Threading support
    parent_comment_id = Column(Integer, ForeignKey("task_comments.id"), nullable=True)
    
    # Attachments and mentions
    attachments = Column(Text)  # JSON array of file paths
    mentions = Column(Text)  # JSON array of mentioned user IDs
    
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    task = relationship("Task", back_populates="comments")
    user = relationship("User", back_populates="task_comments")
    parent_comment = relationship("TaskComment", remote_side=[id])
    replies = relationship("TaskComment", back_populates="parent_comment")

class WorkspaceInvite(Base):
    """Workspace invitation system"""
    __tablename__ = "workspace_invites"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Can invite by email or user ID
    invited_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    invited_email = Column(String(255), nullable=True)
    
    permissions = Column(String(255))  # JSON array of permissions
    invite_code = Column(String(100), unique=True, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime)
    
    status = Column(String(20), default="pending")  # "pending", "accepted", "declined", "expired"
    message = Column(Text)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="invites")
    inviter = relationship("User", foreign_keys=[invited_by])
    invited_user = relationship("User", foreign_keys=[invited_user_id])