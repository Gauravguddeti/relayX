"""
Integration tests for auth_routes.py - Authentication API endpoints

These tests verify:
- User signup flow
- User login flow
- Token refresh flow
- Token verification
- Error handling for auth endpoints

NOTE: These tests use a minimal FastAPI app with just auth routes
to avoid importing the full main.py which has many dependencies.
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.testclient import TestClient


# ==================== MOCK SETUP ====================

class MockSupabaseResponse:
    """Mock Supabase query response"""
    def __init__(self, data=None, error=None):
        self.data = data if data is not None else []
        self.error = error


class MockSupabaseQuery:
    """Mock Supabase query builder with chainable methods"""
    def __init__(self, data=None):
        self._data = data if data is not None else []
        self._insert_data = None
        self._update_data = None
    
    def select(self, *args, **kwargs):
        return self
    
    def insert(self, data):
        self._insert_data = data
        # Return self for chaining
        return MockSupabaseQuery([{**data, "id": "generated-uuid-123", "created_at": datetime.utcnow().isoformat()}])
    
    def update(self, data):
        self._update_data = data
        return self
    
    def delete(self):
        return self
    
    def eq(self, field, value):
        return self
    
    def single(self):
        return self
    
    def execute(self):
        # If insert was called, return the inserted data with an ID
        if self._insert_data:
            result = self._insert_data.copy()
            result["id"] = "generated-uuid-123"
            result["created_at"] = datetime.utcnow().isoformat()
            return MockSupabaseResponse(data=[result])
        return MockSupabaseResponse(data=self._data)


def create_mock_supabase():
    """Create a mock Supabase client with configurable table data"""
    mock = MagicMock()
    table_data = {}
    
    def table(name):
        if name not in table_data:
            table_data[name] = MockSupabaseQuery()
        return table_data[name]
    
    mock.table = table
    mock._table_data = table_data
    return mock


def create_test_app(mock_supabase):
    """Create a minimal FastAPI app with just auth routes for testing"""
    app = FastAPI()
    
    # Import and configure auth_routes with mock
    import auth_routes
    auth_routes.supabase = mock_supabase
    
    app.include_router(auth_routes.router)
    
    return app


# ==================== SIGNUP TESTS ====================

class TestSignup:
    """Tests for POST /auth/signup endpoint"""
    
    def test_signup_success(self):
        """Successful signup should return tokens and user"""
        mock_db = create_mock_supabase()
        
        # No existing user
        mock_db._table_data["users"] = MockSupabaseQuery(data=[])
        # Will return inserted user
        mock_db._table_data["agents"] = MockSupabaseQuery(data=[])
        mock_db._table_data["auth_tokens"] = MockSupabaseQuery(data=[])
        
        app = create_test_app(mock_db)
        client = TestClient(app)
        
        response = client.post("/auth/signup", json={
            "email": "newuser@example.com",
            "password": "secure_password_123",
            "name": "New User"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
    
    def test_signup_duplicate_email(self):
        """Signup with existing email should return 400"""
        mock_db = create_mock_supabase()
        
        # User already exists
        mock_db._table_data["users"] = MockSupabaseQuery(data=[
            {"id": "existing-user-id", "email": "existing@example.com"}
        ])
        
        app = create_test_app(mock_db)
        client = TestClient(app)
        
        response = client.post("/auth/signup", json={
            "email": "existing@example.com",
            "password": "secure_password_123"
        })
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_signup_invalid_email(self):
        """Signup with invalid email should return 422"""
        mock_db = create_mock_supabase()
        app = create_test_app(mock_db)
        client = TestClient(app)
        
        response = client.post("/auth/signup", json={
            "email": "not-an-email",
            "password": "secure_password_123"
        })
        
        assert response.status_code == 422


# ==================== LOGIN TESTS ====================

class TestLogin:
    """Tests for POST /auth/login endpoint"""
    
    def test_login_success(self):
        """Successful login should return tokens"""
        from auth import get_password_hash
        
        mock_db = create_mock_supabase()
        
        # Existing user with hashed password
        hashed_pw = get_password_hash("correct_password")
        mock_db._table_data["users"] = MockSupabaseQuery(data=[{
            "id": "user-123",
            "email": "user@example.com",
            "password_hash": hashed_pw,
            "name": "Test User"
        }])
        mock_db._table_data["auth_tokens"] = MockSupabaseQuery(data=[])
        
        app = create_test_app(mock_db)
        client = TestClient(app)
        
        response = client.post("/auth/login", json={
            "email": "user@example.com",
            "password": "correct_password"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "user@example.com"
        assert "password_hash" not in data["user"]  # Should be removed
    
    def test_login_wrong_password(self):
        """Login with wrong password should return 401"""
        from auth import get_password_hash
        
        mock_db = create_mock_supabase()
        
        hashed_pw = get_password_hash("correct_password")
        mock_db._table_data["users"] = MockSupabaseQuery(data=[{
            "id": "user-123",
            "email": "user@example.com",
            "password_hash": hashed_pw
        }])
        
        app = create_test_app(mock_db)
        client = TestClient(app)
        
        response = client.post("/auth/login", json={
            "email": "user@example.com",
            "password": "wrong_password"
        })
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_login_nonexistent_user(self):
        """Login with non-existent email should return 401"""
        mock_db = create_mock_supabase()
        
        # No users exist
        mock_db._table_data["users"] = MockSupabaseQuery(data=[])
        
        app = create_test_app(mock_db)
        client = TestClient(app)
        
        response = client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "any_password"
        })
        
        assert response.status_code == 401


# ==================== TOKEN VERIFICATION TESTS ====================

class TestVerifyToken:
    """Tests for GET /auth/verify-token endpoint"""
    
    def test_verify_token_valid(self):
        """Valid token should return user_id"""
        from auth import create_access_token
        
        mock_db = create_mock_supabase()
        app = create_test_app(mock_db)
        client = TestClient(app)
        
        token = create_access_token(data={"sub": "user-123"})
        
        response = client.get(
            "/auth/verify-token",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["valid"] is True
        assert response.json()["user_id"] == "user-123"
    
    def test_verify_token_missing(self):
        """Missing token should return 401"""
        mock_db = create_mock_supabase()
        app = create_test_app(mock_db)
        client = TestClient(app)
        
        response = client.get("/auth/verify-token")
        
        assert response.status_code == 401
    
    def test_verify_token_invalid(self):
        """Invalid token should return 401"""
        mock_db = create_mock_supabase()
        app = create_test_app(mock_db)
        client = TestClient(app)
        
        response = client.get(
            "/auth/verify-token",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == 401


# ==================== GET CURRENT USER TESTS ====================

class TestGetMe:
    """Tests for GET /auth/me endpoint"""
    
    def test_get_me_success(self):
        """Authenticated request should return user details"""
        from auth import create_access_token
        
        mock_db = create_mock_supabase()
        mock_db._table_data["users"] = MockSupabaseQuery(data=[{
            "id": "user-123",
            "email": "user@example.com",
            "name": "Test User",
            "password_hash": "should_be_removed"
        }])
        
        app = create_test_app(mock_db)
        client = TestClient(app)
        
        token = create_access_token(data={"sub": "user-123"})
        
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "user@example.com"
        assert "password_hash" not in data
    
    def test_get_me_unauthorized(self):
        """Unauthenticated request should return 401"""
        mock_db = create_mock_supabase()
        app = create_test_app(mock_db)
        client = TestClient(app)
        
        response = client.get("/auth/me")
        
        assert response.status_code == 401
