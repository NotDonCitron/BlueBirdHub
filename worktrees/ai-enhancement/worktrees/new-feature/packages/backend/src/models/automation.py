"""
Automation models for OrdnungsHub
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from src.backend.database.database import Base

class Automation(Base):
    __tablename__ = "automations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    trigger_type = Column(String(50), nullable=False)  # schedule, event, manual
    enabled = Column(Boolean, default=True)
    actions = Column(JSON)  # List of actions to perform
    schedule = Column(String(100))  # Cron expression for scheduled automations
    event_type = Column(String(100))  # Event type for event-driven automations
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_run = Column(DateTime)

class AutomationLog(Base):
    __tablename__ = "automation_logs"

    id = Column(Integer, primary_key=True, index=True)
    automation_id = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)  # success, error, running
    message = Column(Text)
    actions_executed = Column(Integer, default=0)
    duration = Column(Integer)  # Duration in seconds
    error_details = Column(Text)
    created_at = Column(DateTime, server_default=func.now())