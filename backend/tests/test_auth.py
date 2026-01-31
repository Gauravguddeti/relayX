"""
Unit tests for auth.py - JWT authentication utilities

These tests verify:
- Password hashing and verification
- Access token creation and validation
- Refresh token creation and validation
- Token expiration handling
"""
import pytest
import sys
import os
from datetime import timedelta
from unittest.mock import patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user_id,
)


class TestPasswordHashing:
    """Tests for password hashing functions"""
    
    def test_password_hashing_creates_hash(self):
        """Password hashing should create a bcrypt hash"""
        password = "my_secure_password123"
        hashed = get_password_hash(password)
        
        assert hashed is not None
        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt identifier
    
    def test_password_hashing_different_each_time(self):
        """Same password should create different hashes (due to salt)"""
        password = "my_secure_password123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
    
    def test_verify_password_correct(self):
        """Correct password should verify successfully"""
        password = "my_secure_password123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Incorrect password should fail verification"""
        password = "my_secure_password123"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_empty(self):
        """Empty password should fail verification"""
        password = "my_secure_password123"
        hashed = get_password_hash(password)
        
        assert verify_password("", hashed) is False


class TestAccessTokens:
    """Tests for JWT access token creation and verification"""
    
    def test_create_access_token_basic(self):
        """Access token should be created with user data"""
        user_id = "user-123"
        token = create_access_token(data={"sub": user_id})
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_contains_payload(self):
        """Access token should contain the original payload"""
        user_id = "user-123"
        token = create_access_token(data={"sub": user_id})
        
        payload = verify_token(token)
        
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "exp" in payload
    
    def test_create_access_token_custom_expiry(self):
        """Access token should respect custom expiry"""
        user_id = "user-123"
        custom_expiry = timedelta(hours=2)
        token = create_access_token(data={"sub": user_id}, expires_delta=custom_expiry)
        
        payload = verify_token(token)
        
        assert payload["sub"] == user_id
    
    def test_verify_token_valid(self):
        """Valid token should decode correctly"""
        user_id = "user-123"
        token = create_access_token(data={"sub": user_id})
        
        payload = verify_token(token)
        
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
    
    def test_verify_token_invalid_format(self):
        """Invalid token format should raise HTTPException"""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid-token-format")
        
        assert exc_info.value.status_code == 401
    
    def test_verify_token_expired(self):
        """Expired token should raise HTTPException"""
        from fastapi import HTTPException
        
        # Create token with negative expiry (already expired)
        user_id = "user-123"
        token = create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(seconds=-10)  # Already expired
        )
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)
        
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()


class TestRefreshTokens:
    """Tests for JWT refresh token creation"""
    
    def test_create_refresh_token_basic(self):
        """Refresh token should be created with user data"""
        user_id = "user-123"
        token = create_refresh_token(data={"sub": user_id})
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token_type(self):
        """Refresh token should have type 'refresh'"""
        user_id = "user-123"
        token = create_refresh_token(data={"sub": user_id})
        
        payload = verify_token(token)
        
        assert payload["type"] == "refresh"
        assert payload["sub"] == user_id
    
    def test_refresh_token_different_from_access(self):
        """Refresh and access tokens should be different"""
        user_id = "user-123"
        access_token = create_access_token(data={"sub": user_id})
        refresh_token = create_refresh_token(data={"sub": user_id})
        
        assert access_token != refresh_token


class TestGetCurrentUserId:
    """Tests for get_current_user_id dependency"""
    
    @pytest.mark.asyncio
    async def test_valid_authorization_header(self):
        """Valid bearer token should return user_id"""
        from auth import create_access_token
        
        user_id = "user-123"
        token = create_access_token(data={"sub": user_id})
        auth_header = f"Bearer {token}"
        
        result = await get_current_user_id(authorization=auth_header)
        
        assert result == user_id
    
    @pytest.mark.asyncio
    async def test_missing_authorization_header(self):
        """Missing authorization header should raise 401"""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_id(authorization=None)
        
        assert exc_info.value.status_code == 401
        assert "Not authenticated" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_invalid_scheme(self):
        """Non-bearer scheme should raise 401"""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_id(authorization="Basic some-token")
        
        assert exc_info.value.status_code == 401
        assert "Invalid authentication scheme" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_refresh_token_rejected(self):
        """Refresh token should be rejected for access"""
        from fastapi import HTTPException
        from auth import create_refresh_token
        
        user_id = "user-123"
        refresh_token = create_refresh_token(data={"sub": user_id})
        auth_header = f"Bearer {refresh_token}"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_id(authorization=auth_header)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token type" in exc_info.value.detail
