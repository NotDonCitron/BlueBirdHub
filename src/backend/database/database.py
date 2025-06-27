from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool, QueuePool
from sqlalchemy.engine import Engine
import os
import sqlite3
from pathlib import Path
from typing import Optional
from loguru import logger
import time

from src.backend.database.database_config import DatabaseConfig

# Initialize database configuration
config = DatabaseConfig()

# Create data directory if it doesn't exist
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Database URL from configuration
DATABASE_URL = config.get_database_url()

# Create optimized engine with configuration
engine_config = config.get_engine_config()
engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,  # StaticPool is optimal for SQLite
    **engine_config
)

# SQLite Performance Optimizations
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Configure SQLite for optimal performance using DatabaseConfig
    Applied when each connection is created
    """
    if 'sqlite' in str(dbapi_connection):
        cursor = dbapi_connection.cursor()
        
        # Apply all SQLite pragmas from configuration
        for pragma, value in config.SQLITE_PRAGMAS.items():
            if isinstance(value, bool):
                cursor.execute(f"PRAGMA {pragma}")
            else:
                cursor.execute(f"PRAGMA {pragma}={value}")
        
        cursor.close()
        logger.debug("SQLite performance pragmas applied from configuration")

# Create optimized session factory with configuration
session_config = config.get_session_config()
SessionLocal = sessionmaker(
    bind=engine,
    **session_config
)

# Base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    """
    Database session dependency for FastAPI.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize the database by creating all tables.
    Should be called on application startup.
    """
    # Import all model modules to register them with SQLAlchemy
    from src.backend.models import (
        user, workspace, task, file_metadata,
        supplier, team
    )
    # Temporarily disabled to fix startup issues
    # from src.backend.models import calendar, workflow, analytics, search
    Base.metadata.create_all(bind=engine)