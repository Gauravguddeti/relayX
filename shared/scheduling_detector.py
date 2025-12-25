"""
Scheduling detection service - extracts meeting intent and details from call transcripts.
"""
import os
import json
import re
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging
from groq import Groq

logger = logging.getLogger(__name__)


class SchedulingDetector:
    """Detects scheduling intent and extracts meeting details from conversations."""
    
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        if not self.groq_api_key:
            logger.warning("GROQ_API_KEY not set - scheduling detection disabled")
    
    async def detect_scheduling_intent(
        self,
        transcript: str,
        call_summary: str = "",
        outcome: str = ""
    ) -> Optional[Dict]:
        """
        Analyze transcript and call data to detect if a meeting/demo was scheduled.
        
        Args:
            transcript: Full call transcript
            call_summary: AI-generated summary
            outcome: Call outcome (interested, not_interested, etc.)
        
        Returns:
            Dict with scheduling details if detected, None otherwise:
            {
                "scheduled": True,
                "event_type": "demo" | "call" | "followup" | "meeting",
                "date": "YYYY-MM-DD",
                "time": "HH:MM",
                "timezone": "America/New_York",
                "contact_name": str,
                "notes": str,
                "confidence": float  # 0.0 to 1.0
            }
        """
        if not self.groq_api_key:
            return None
        
        # Only proceed if outcome suggests interest
        if outcome and outcome not in ["interested", "call_later"]:
            logger.info(f"Skipping scheduling detection - outcome: {outcome}")
            return None
        
        try:
            client = Groq(api_key=self.groq_api_key)
            
            prompt = f"""Analyze this call to determine if a meeting/demo/call was scheduled.

TRANSCRIPT:
{transcript}

CALL SUMMARY:
{call_summary}

OUTCOME: {outcome}

INSTRUCTIONS:
1. Determine if a specific date/time was agreed upon for a future meeting, demo, or call
2. Extract the following details if scheduling occurred:
   - Event type: "demo", "followup", "call", or "meeting"
   - Date: Convert relative dates (tomorrow, next week, Monday, etc.) to absolute YYYY-MM-DD format
   - Time: Extract time in HH:MM format (24-hour). If only "morning"/"afternoon" mentioned, use 10:00/14:00
   - Timezone: Infer from context or use "America/New_York" as default
   - Contact name: Extract from transcript
   - Notes: Brief summary of what was agreed (e.g., "demo of premium features")
   - Confidence: 0.0-1.0 score of how certain you are scheduling occurred

TODAY'S DATE: {datetime.now().strftime('%Y-%m-%d')}

IMPORTANT RULES:
- Only return scheduling data if a SPECIFIC time was agreed (not just "call me back" or "I'll think about it")
- "Tomorrow at 4 PM" = scheduled
- "Call me next week sometime" = NOT scheduled (too vague)
- "Let me check my calendar and get back to you" = NOT scheduled
- Always convert relative dates to absolute dates using today's date above

Return ONLY valid JSON (no other text):
{{
  "scheduled": true/false,
  "event_type": "demo/followup/call/meeting",
  "date": "YYYY-MM-DD",
  "time": "HH:MM",
  "timezone": "America/New_York",
  "contact_name": "",
  "notes": "",
  "confidence": 0.0-1.0
}}

If no scheduling detected, return: {{"scheduled": false}}"""

            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.1,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if not json_match:
                logger.warning(f"No JSON found in scheduling detection response: {content}")
                return None
            
            result = json.loads(json_match.group())
            
            # Validate result
            if not result.get("scheduled"):
                logger.info("No scheduling detected in call")
                return None
            
            # Validate required fields
            required = ["event_type", "date", "time"]
            if not all(result.get(field) for field in required):
                logger.warning(f"Missing required scheduling fields: {result}")
                return None
            
            # Validate confidence threshold
            confidence = result.get("confidence", 0.0)
            if confidence < 0.7:
                logger.info(f"Scheduling confidence too low: {confidence}")
                return None
            
            logger.info(f"✅ Scheduling detected: {result.get('event_type')} on {result.get('date')} at {result.get('time')}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse scheduling detection JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error detecting scheduling intent: {e}")
            return None
    
    def convert_to_iso_datetime(self, date_str: str, time_str: str, timezone: str = "America/New_York") -> str:
        """
        Convert date and time strings to ISO format datetime with proper timezone.
        
        Args:
            date_str: Date in YYYY-MM-DD format
            time_str: Time in HH:MM format (24-hour)
            timezone: IANA timezone
        
        Returns:
            ISO format datetime string with timezone (e.g., "2024-12-25T14:30:00-05:00")
        """
        try:
            from datetime import datetime
            from dateutil import tz
            
            # Parse the date and time
            dt_naive = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            
            # Get timezone object
            tz_obj = tz.gettz(timezone)
            if not tz_obj:
                # Fallback to UTC if timezone not found
                tz_obj = tz.UTC
            
            # Localize the datetime to the specified timezone
            dt_aware = dt_naive.replace(tzinfo=tz_obj)
            
            # Convert to ISO format with timezone
            iso_datetime = dt_aware.isoformat()
            
            return iso_datetime
        except Exception as e:
            logger.error(f"Error converting to ISO datetime: {e}")
            raise


# Global instance
scheduling_detector = SchedulingDetector()
