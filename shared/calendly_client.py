"""
Calendly API Client for scheduling appointments during calls.
"""
import os
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import httpx

logger = logging.getLogger(__name__)


class CalendlyClient:
    """Client for interacting with Calendly API."""
    
    def __init__(self):
        self.api_token = os.getenv("CALENDLY_API_TOKEN")
        self.event_type_url = os.getenv("CALENDLY_EVENT_TYPE_URL")
        self.base_url = "https://api.calendly.com"
        
        if not self.api_token:
            logger.warning("CALENDLY_API_TOKEN not set. Calendly features will be disabled.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    def is_configured(self) -> bool:
        """Check if Calendly is properly configured."""
        return bool(self.api_token and self.event_type_url)
    
    async def get_user_info(self) -> Optional[Dict]:
        """Get current user information."""
        if not self.is_configured():
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/users/me",
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting Calendly user info: {e}")
            return None
    
    async def get_available_times(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """
        Get available time slots for scheduling.
        
        Args:
            start_date: ISO format date (YYYY-MM-DD). Defaults to today.
            end_date: ISO format date (YYYY-MM-DD). Defaults to 30 days from start.
        
        Returns:
            List of available time slots
        """
        if not self.is_configured():
            return []
        
        # Default to today if not specified
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")
        
        if not end_date:
            end = datetime.now() + timedelta(days=30)
            end_date = end.strftime("%Y-%m-%d")
        
        try:
            # Get event type URI from URL
            event_type_uri = self.event_type_url.replace("https://calendly.com/", "")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/event_type_available_times",
                    headers=self.headers,
                    params={
                        "event_type": event_type_uri,
                        "start_time": f"{start_date}T00:00:00Z",
                        "end_time": f"{end_date}T23:59:59Z"
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                return data.get("collection", [])
        except Exception as e:
            logger.error(f"Error getting available times: {e}")
            return []
    
    async def create_scheduling_link(
        self,
        name: str,
        email: str,
        phone: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a personalized scheduling link for a prospect.
        
        Args:
            name: Prospect's name
            email: Prospect's email
            phone: Prospect's phone number
            notes: Additional notes about the meeting
        
        Returns:
            Scheduling URL or None if failed
        """
        if not self.is_configured():
            return None
        
        try:
            # Build pre-filled URL parameters
            params = {
                "name": name,
                "email": email,
            }
            
            if phone:
                params["a1"] = phone  # Custom question answer
            
            if notes:
                params["notes"] = notes
            
            # Create query string
            query_parts = [f"{k}={v}" for k, v in params.items()]
            query_string = "&".join(query_parts)
            
            # Return pre-filled URL
            return f"{self.event_type_url}?{query_string}"
        except Exception as e:
            logger.error(f"Error creating scheduling link: {e}")
            return None
    
    async def schedule_event(
        self,
        name: str,
        email: str,
        start_time: str,
        phone: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Schedule an event directly (if user has permissions).
        
        Args:
            name: Invitee name
            email: Invitee email
            start_time: ISO format datetime (e.g., "2024-01-15T10:00:00Z")
            phone: Invitee phone number
            notes: Additional notes
        
        Returns:
            Event details or None if failed
        """
        if not self.is_configured():
            return None
        
        try:
            payload = {
                "event": self.event_type_url,
                "invitees": [
                    {
                        "name": name,
                        "email": email,
                    }
                ],
                "start_time": start_time
            }
            
            if phone:
                payload["invitees"][0]["phone"] = phone
            
            if notes:
                payload["notes"] = notes
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/scheduled_events",
                    headers=self.headers,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error scheduling event: {e}")
            return None
    
    async def send_scheduling_link_sms(
        self,
        phone: str,
        name: str,
        email: str,
        twilio_client
    ) -> bool:
        """
        Send scheduling link via SMS using Twilio.
        
        Args:
            phone: Recipient phone number
            name: Prospect name
            email: Prospect email
            twilio_client: Initialized Twilio client
        
        Returns:
            True if sent successfully
        """
        link = await self.create_scheduling_link(name, email, phone)
        
        if not link:
            return False
        
        try:
            message = (
                f"Hi {name}! Thanks for your interest. "
                f"Schedule a call with us here: {link}"
            )
            
            twilio_client.messages.create(
                body=message,
                from_=os.getenv("TWILIO_PHONE_NUMBER"),
                to=phone
            )
            
            logger.info(f"Sent Calendly link to {phone}")
            return True
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return False


# Global instance
calendly_client = CalendlyClient()
