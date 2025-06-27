from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.backend.database.database import Base

class Workspace(Base):
    __tablename__ = "workspaces"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    theme = Column(String(50), default="default")
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    icon = Column(String(50))
    color = Column(String(7))  # Hex color code
    layout_config = Column(JSON)  # Store widget positions and settings
    ambient_sound = Column(String(100))  # Ambient sound preference
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_accessed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="workspaces")
    tasks = relationship("Task", back_populates="workspace", cascade="all, delete-orphan")
    suppliers = relationship("Supplier", back_populates="workspace", cascade="all, delete-orphan")
    
    # Collaboration relationships
    shares = relationship("WorkspaceShare", back_populates="workspace", cascade="all, delete-orphan")
    activities = relationship("WorkspaceActivity", back_populates="workspace", cascade="all, delete-orphan")
    invites = relationship("WorkspaceInvite", back_populates="workspace", cascade="all, delete-orphan")
    
    # Calendar relationships - re-enabled
    calendars = relationship("Calendar", back_populates="workspace", cascade="all, delete-orphan")
    calendar_shares = relationship("CalendarShare", back_populates="workspace", cascade="all, delete-orphan")
    
    # Analytics relationships - re-enabled
    activity_events = relationship("ActivityEvent", back_populates="workspace", cascade="all, delete-orphan")
    time_tracking = relationship("TimeTracking", back_populates="workspace", cascade="all, delete-orphan")
    productivity_metrics = relationship("ProductivityMetrics", back_populates="workspace", cascade="all, delete-orphan")
    team_metrics = relationship("TeamMetrics", back_populates="workspace", cascade="all, delete-orphan")
    kpis = relationship("KPITracking", back_populates="workspace", cascade="all, delete-orphan")
    analytics_insights = relationship("AnalyticsInsights", back_populates="workspace", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Workspace(id={self.id}, name='{self.name}', theme='{self.theme}')>"


class WorkspaceTheme(Base):
    __tablename__ = "workspace_themes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    primary_color = Column(String(7), nullable=False)  # Hex color
    secondary_color = Column(String(7), nullable=False)  # Hex color
    accent_color = Column(String(7), nullable=False)  # Hex color
    background_color = Column(String(7), nullable=False)  # Hex color
    text_color = Column(String(7), nullable=False)  # Hex color
    is_dark_mode = Column(Boolean, default=False)
    is_system = Column(Boolean, default=True)  # System theme vs user-created
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<WorkspaceTheme(id={self.id}, name='{self.name}')>"