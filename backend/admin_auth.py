"""
Admin middleware and authentication
"""
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import os
import hashlib
import secrets
from datetime import datetime, timedelta

# Admin credentials (hashed)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
# Default password: "RelayX@2025" - double hashed with SHA256 + bcrypt-style salt
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "ffebe158749246f68e0b188cfd39b9ad:f42d80f42a4d269d036ddff5b5ef041c5b5987a309f959db39140c10c5f6c1c8")

# Session store (in production, use Redis or database)
admin_sessions = {}

security = HTTPBearer()


def hash_password_double(password: str, salt: str = None) -> str:
    """
    Double hashing: SHA256 + salted SHA256
    Format: salt:hash
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    # First hash with SHA256
    first_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Second hash with salt
    salted = f"{salt}:{first_hash}".encode()
    second_hash = hashlib.sha256(salted).hexdigest()
    
    return f"{salt}:{second_hash}"


def verify_password_double(password: str, stored_hash: str) -> bool:
    """Verify password against stored double hash"""
    try:
        salt, stored_second_hash = stored_hash.split(":")
        # Recreate the hash process
        first_hash = hashlib.sha256(password.encode()).hexdigest()
        salted = f"{salt}:{first_hash}".encode()
        second_hash = hashlib.sha256(salted).hexdigest()
        
        return second_hash == stored_second_hash
    except:
        return False


def create_admin_session(username: str) -> str:
    """Create admin session token"""
    token = secrets.token_urlsafe(32)
    admin_sessions[token] = {
        "username": username,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=24)
    }
    return token


def verify_admin_session(token: str) -> Optional[dict]:
    """Verify admin session token"""
    session = admin_sessions.get(token)
    if not session:
        return None
    
    if datetime.utcnow() > session["expires_at"]:
        del admin_sessions[token]
        return None
    
    return session


def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dependency to verify admin token"""
    token = credentials.credentials
    session = verify_admin_session(token)
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired admin session")
    
    return session


def is_admin_user(user_id: str) -> bool:
    """Check if user_id belongs to admin (Test User in this case)"""
    # Admin user_id from database
    ADMIN_USER_ID = "6bc4291b-cd1e-49d1-98a8-31c12bbdb7f2"
    return user_id == ADMIN_USER_ID
