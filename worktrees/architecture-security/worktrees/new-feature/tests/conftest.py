import pytest
from fastapi.testclient import TestClient
from src.backend.main import app
from src.backend.database.database import init_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Initialize database for all tests."""
    try:
        init_db()
        print("Test database initialized")
    except Exception as e:
        print(f"Failed to initialize test database: {e}")

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    from unittest.mock import MagicMock
    session = MagicMock()
    return session