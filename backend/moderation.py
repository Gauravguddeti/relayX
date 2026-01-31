
import re
from loguru import logger

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
    
    # Handle empty or None text
    if not text:
        return {
            "flagged": False,
            "categories": [],
            "matched_terms": []
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
