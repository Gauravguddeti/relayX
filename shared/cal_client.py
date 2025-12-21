"""
Cal.com API Client for scheduling appointments during calls.
"""
import os
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import httpx

logger = logging.getLogger(__name__)


class CalClient:
    """Client for interacting with Cal.com API."""
    
    def __init__(self):
        self.api_key = os.getenv("CAL_API_KEY")
        self.base_url = "https://api.cal.com/v1"
        
        if not self.api_key:
            logger.warning("CAL_API_KEY not set. Cal.com features will be disabled.")
    
    def is_configured(self) -> bool:
        """Check if Cal.com is properly configured."""
        return bool(self.api_key)
    
    async def get_user_info(self) -> Optional[Dict]:
        """Get current user information."""
        if not self.is_configured():
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/me",
                    params={"apiKey": self.api_key},
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting Cal.com user info: {e}")
            return None
    
    async def get_event_types(self) -> List[Dict]:
        """Get all event types for the user."""
        if not self.is_configured():
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/event-types",
                    params={"apiKey": self.api_key},
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                return data.get("event_types", [])
        except Exception as e:
            logger.error(f"Error getting event types: {e}")
            return []
    
    async def get_bookings(self, status: str = "upcoming") -> List[Dict]:
        """
        Get user's bookings from Cal.com.
        
        Args:
            status: Filter by status (upcoming, past, cancelled)
        
        Returns:
            List of bookings
        """
        if not self.is_configured():
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/bookings",
                    params={
                        "apiKey": self.api_key,
                        "status": status
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                return data.get("bookings", [])
        except Exception as e:
            logger.error(f"Error getting bookings: {e}")
            return []
    
    async def get_available_slots(
        self,
        event_type_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        timezone: str = "UTC"
    ) -> List[Dict]:
        """
        Get available time slots for an event type.
        
        Args:
            event_type_id: Cal.com event type ID
            start_date: ISO format date (YYYY-MM-DD). Defaults to today.
            end_date: ISO format date (YYYY-MM-DD). Defaults to 30 days from start.
            timezone: IANA timezone (e.g., "America/New_York")
        
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
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/slots",
                    params={
                        "apiKey": self.api_key,
                        "eventTypeId": event_type_id,
                        "startTime": f"{start_date}T00:00:00Z",
                        "endTime": f"{end_date}T23:59:59Z",
                        "timeZone": timezone
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                return data.get("slots", [])
        except Exception as e:
            logger.error(f"Error getting available slots: {e}")
            return []
    
    async def create_booking(
        self,
        event_type_id: int,
        start_time: str,
        name: str,
        email: str,
        phone: Optional[str] = None,
        notes: Optional[str] = None,
        timezone: str = "UTC"
    ) -> Optional[Dict]:
        """
        Create a booking for an event.
        
        Args:
            event_type_id: Cal.com event type ID
            start_time: ISO format datetime (e.g., "2024-01-15T10:00:00Z")
            name: Attendee name
            email: Attendee email
            phone: Attendee phone number
            notes: Additional notes
            timezone: IANA timezone
        
        Returns:
            Booking details or None if failed
        """
        if not self.is_configured():
            return None
        
        try:
            payload = {
                "eventTypeId": event_type_id,
                "start": start_time,
                "responses": {
                    "name": name,
                    "email": email,
                },
                "timeZone": timezone,
                "language": "en"
            }
            
            if phone:
                payload["responses"]["phone"] = phone
            
            if notes:
                payload["responses"]["notes"] = notes
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/bookings",
                    params={"apiKey": self.api_key},
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error creating booking: {e}")
            return None
    
    async def get_booking_link(
        self,
        event_type_slug: str,
        username: str,
        name: Optional[str] = None,
        email: Optional[str] = None
    ) -> str:
        """
        Create a booking link with pre-filled information.
        
        Args:
            event_type_slug: Event type slug from Cal.com
            username: Cal.com username
            name: Pre-fill name
            email: Pre-fill email
        
        Returns:
            Booking URL
        """
        base_url = f"https://cal.com/{username}/{event_type_slug}"
        
        params = []
        if name:
            params.append(f"name={name}")
        if email:
            params.append(f"email={email}")
        
        if params:
            return f"{base_url}?{'&'.join(params)}"
        return base_url
    
    async def send_booking_link_sms(
        self,
        phone: str,
        name: str,
        email: str,
        booking_url: str,
        twilio_client
    ) -> bool:
        """
        Send booking link via SMS using Twilio.
        
        Args:
            phone: Recipient phone number
            name: Prospect name
            email: Prospect email
            booking_url: Cal.com booking URL
            twilio_client: Initialized Twilio client
        
        Returns:
            True if sent successfully
        """
        if not booking_url:
            logger.error("No booking URL provided for SMS")
            return False
        
        try:
            message = (
                f"Hi {name}! Thanks for your interest. "
                f"Schedule a call with us here: {booking_url}"
            )
            
            from_number = os.getenv("TWILIO_PHONE_NUMBER")
            if not from_number:
                logger.error("TWILIO_PHONE_NUMBER not set")
                return False
            
            logger.info(f"Attempting to send SMS to {phone} from {from_number}")
            
            result = twilio_client.messages.create(
                body=message,
                from_=from_number,
                to=phone
            )
            
            logger.info(f"Sent Cal.com link to {phone}, SID: {result.sid}")
            return True
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            logger.error(f"Phone: {phone}, From: {os.getenv('TWILIO_PHONE_NUMBER')}")
            return False


# Global instance
cal_client = CalClient()
