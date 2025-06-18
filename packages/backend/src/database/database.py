from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
from pathlib import Path

# Create data directory if it doesn't exist (for SQLite fallback)
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Database URL - Check environment first, fallback to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/ordnungshub.db")

# Create engine with appropriate configuration
if DATABASE_URL.startswith("postgresql"):
    # PostgreSQL configuration
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Set to True for SQL query logging during development
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True  # Verify connections before use
    )
else:
    # SQLite configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # Needed for SQLite
        poolclass=StaticPool,  # Better for SQLite in async environment
        echo=False  # Set to True for SQL query logging during development
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
    from models import user, workspace, task, file_metadata
    Base.metadata.create_all(bind=engine)