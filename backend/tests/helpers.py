"""
Helper functions for tests - copies of main.py functions to avoid import issues

These are exact copies of functions from main.py that we need for testing,
extracted to avoid importing the full application with all its dependencies.
"""
import re
import time
from collections import defaultdict


# ==================== CONTENT MODERATION ====================

async def moderate_content(text: str) -> dict:
    """
    Check text content for harmful/inappropriate content using keyword-based filtering.
    Returns: {"flagged": bool, "categories": list, "matched_terms": list}
    """
    # Harmful patterns to detect
    HARMFUL_PATTERNS = {
        "illegal": [
            r"\bhack\w*\s+(into|account|system|password)",
            r"\bsteal\w*\s+(money|credit|data|information)",
            r"\billegal\s+(activity|drugs|weapon)",
            r"\bfraud\w*",
            r"\bscam\w*\s+(people|users|customers)",
            r"\blaunder\w*\s+money",
            r"\bcreate\s+(fake|counterfeit)",
            r"\bexploit\w*\s+(vulnerability|security)",
        ],
        "harmful": [
            r"\bharm\w*\s+(yourself|others|people)",
            r"\bkill\w*\s+(yourself|someone|people)",
            r"\bsuicide",
            r"\bself.harm",
            r"\bviolent\s+(attack|assault)",
        ],
        "privacy": [
            r"\bshare\s+(private|personal|confidential)\s+information",
            r"\bdisclose\s+(ssn|social security|password|credit card)",
            r"\bcollect\s+(private|personal)\s+data\s+without",
        ],
        "abuse": [
            r"\bharassment",
            r"\bbully\w*\s+(people|users|customers)",
            r"\bthreaten\w*\s+(to|with)",
            r"\bintimid\w+",
        ]
    }
    
    text_lower = text.lower()
    flagged = False
    matched_categories = []
    matched_terms = []
    
    for category, patterns in HARMFUL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                flagged = True
                if category not in matched_categories:
                    matched_categories.append(category)
                # Extract matched text
                match = re.search(pattern, text_lower)
                if match:
                    matched_terms.append(match.group(0))
    
    return {
        "flagged": flagged,
        "categories": matched_categories,
        "matched_terms": matched_terms[:3]  # Limit to first 3 matches
    }


# ==================== RATE LIMITING ====================

# In-memory rate limiter (per user_id)
rate_limit_store = defaultdict(list)


def check_rate_limit(user_id: str, limit: int = 5, window_seconds: int = 60) -> bool:
    """
    Check if user has exceeded rate limit.
    Args:
        user_id: User identifier
        limit: Max requests allowed in window
        window_seconds: Time window in seconds
    Returns:
        True if within limit, False if exceeded
    """
    now = time.time()
    cutoff = now - window_seconds
    
    # Remove old timestamps outside the window
    rate_limit_store[user_id] = [ts for ts in rate_limit_store[user_id] if ts > cutoff]
    
    # Check if limit exceeded
    if len(rate_limit_store[user_id]) >= limit:
        return False
    
    # Add current timestamp
    rate_limit_store[user_id].append(now)
    return True


def get_rate_limit_reset(user_id: str, window_seconds: int = 60) -> int:
    """Get seconds until rate limit resets for user"""
    if not rate_limit_store[user_id]:
        return 0
    oldest_timestamp = min(rate_limit_store[user_id])
    reset_time = oldest_timestamp + window_seconds
    return max(0, int(reset_time - time.time()))


# ==================== PERMISSIONS ====================

# Simple role-based access control
ADMIN_USERS = ["admin", "system"]


def is_admin(user_id: str) -> bool:
    """Check if user has admin privileges"""
    return user_id in ADMIN_USERS


def check_prompt_permission(user_id: str, prompt_owner_id: str, is_locked: bool) -> bool:
    """
    Check if user can edit a prompt.
    Rules:
    - Admins can edit anything
    - Users can only edit their own non-locked prompts
    - No one can edit locked templates (system templates)
    """
    if is_locked:
        return False  # Locked templates cannot be edited by anyone
    if is_admin(user_id):
        return True
    return user_id == prompt_owner_id
