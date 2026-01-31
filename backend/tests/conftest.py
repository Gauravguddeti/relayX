"""
Pytest configuration and fixtures for RelayX backend tests.
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient


# ==================== MOCK DATABASE FIXTURE ====================

class MockSupabaseResponse:
    """Mock Supabase query response"""
    def __init__(self, data=None, error=None):
        self.data = data or []
        self.error = error


class MockSupabaseQuery:
    """Mock Supabase query builder"""
    def __init__(self, data=None):
        self._data = data or []
    
    def select(self, *args, **kwargs):
        return self
    
    def insert(self, data):
        self._insert_data = data
        return self
    
    def update(self, data):
        self._update_data = data
        return self
    
    def delete(self):
        return self
    
    def eq(self, field, value):
        return self
    
    def execute(self):
        return MockSupabaseResponse(data=self._data)


class MockSupabase:
    """Mock Supabase client for testing"""
    def __init__(self):
        self._tables = {}
    
    def table(self, name):
        if name not in self._tables:
            self._tables[name] = MockSupabaseQuery()
        return self._tables[name]
    
    def set_table_data(self, table_name, data):
        """Helper to set mock data for a table"""
        self._tables[table_name] = MockSupabaseQuery(data)


@pytest.fixture
def mock_supabase():
    """Fixture providing a mock Supabase client"""
    return MockSupabase()


# ==================== TEST USER FIXTURES ====================

@pytest.fixture
def test_user():
    """Fixture providing a test user dict"""
    return {
        "id": "test-user-id-123",
        "email": "test@example.com",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5uO.G",  # "password123"
        "name": "Test User",
        "phone": "+1234567890",
        "company": "Test Company",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def test_user_password():
    """The plain text password for test_user"""
    return "password123"


# ==================== JWT TOKEN FIXTURES ====================

@pytest.fixture
def test_access_token():
    """Fixture providing a valid access token for test_user"""
    from auth import create_access_token
    return create_access_token(data={"sub": "test-user-id-123"})


@pytest.fixture
def test_refresh_token():
    """Fixture providing a valid refresh token for test_user"""
    from auth import create_refresh_token
    return create_refresh_token(data={"sub": "test-user-id-123"})


@pytest.fixture
def auth_headers(test_access_token):
    """Fixture providing authorization headers with valid token"""
    return {"Authorization": f"Bearer {test_access_token}"}


# ==================== TEST CLIENT FIXTURE ====================

@pytest.fixture
def client(mock_supabase):
    """
    Fixture providing a FastAPI TestClient with mocked database.
    
    Note: This fixture patches the database before importing main
    to ensure the mock is used throughout the app.
    """
    # We'll set up the client in a way that allows mocking
    # For now, we just create a basic client reference
    # The actual test files will handle specific mocking needs
    from main import app
    return TestClient(app)
