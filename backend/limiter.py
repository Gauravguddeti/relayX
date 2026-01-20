"""
Simple in-memory rate limiter for API protection.
Uses a sliding window or fixed window counter per client IP/User.
"""
import time
from collections import defaultdict
from fastapi import Request, HTTPException
from loguru import logger

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.limit = requests_per_minute
        self.window = 60  # seconds
        # Store request timestamps: { "ip_or_user": [ts1, ts2, ...] }
        self.requests = defaultdict(list)

    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        # Filter out timestamps older than the window
        self.requests[client_id] = [
            ts for ts in self.requests[client_id] 
            if ts > now - self.window
        ]
        
        if len(self.requests[client_id]) < self.limit:
            self.requests[client_id].append(now)
            return True
        return False

# Global instance
# 60 requests per minute per IP for general protection
global_limiter = RateLimiter(requests_per_minute=60)

async def check_rate_limit(request: Request):
    """
    Dependency to check rate limit for the client IP.
    """
    client_ip = request.client.host if request.client else "unknown"
    
    # Allow localhost to bypass (optional, but good for dev)
    if client_ip in ["127.0.0.1", "localhost", "::1"]:
        return

    if not global_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=429, 
            detail="Too many requests. Please try again later."
        )
