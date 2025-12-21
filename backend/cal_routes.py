"""
Cal.com integration routes for booking appointments.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging

from shared.cal_client import cal_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cal", tags=["cal"])


class BookingLinkRequest(BaseModel):
    """Request to create a booking link."""
    event_type_slug: str
    username: str
    name: Optional[str] = None
    email: Optional[str] = None


class CreateBookingRequest(BaseModel):
    """Request to create a booking directly."""
    event_type_id: int
    start_time: str  # ISO format datetime
    name: str
    email: str
    phone: Optional[str] = None
    notes: Optional[str] = None
    timezone: str = "UTC"


class SendLinkSMSRequest(BaseModel):
    """Request to send booking link via SMS."""
    phone: str
    name: str
    email: str
    booking_url: str


@router.get("/bookings")
async def get_bookings():
    """Get upcoming bookings from Cal.com."""
    try:
        bookings = await cal_client.get_bookings()
        return {"bookings": bookings}
    except Exception as e:
        logger.error(f"Failed to fetch bookings: {e}")
        return {"bookings": []}


@router.get("/status")
async def get_cal_status():
    """Check if Cal.com integration is configured."""
    is_configured = cal_client.is_configured()
    
    if is_configured:
        user_info = await cal_client.get_user_info()
        event_types = await cal_client.get_event_types()
        
        # Extract nested user object if it exists
        user = user_info.get('user') if user_info and 'user' in user_info else user_info
        
        return {
            "configured": True,
            "connected": True,
            "user": user,
            "event_types": event_types
        }
    
    return {
        "configured": False,
        "connected": False,
        "message": "Cal.com API key not configured"
    }


@router.get("/event-types")
async def get_event_types():
    """Get all event types for the user."""
    if not cal_client.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Cal.com integration not configured"
        )
    
    event_types = await cal_client.get_event_types()
    return {"event_types": event_types}


@router.get("/available-slots")
async def get_available_slots(
    event_type_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    timezone: str = "UTC"
):
    """
    Get available time slots for an event type.
    
    Query params:
        - event_type_id: Cal.com event type ID
        - start_date: YYYY-MM-DD format (defaults to today)
        - end_date: YYYY-MM-DD format (defaults to 30 days from start)
        - timezone: IANA timezone (defaults to UTC)
    """
    if not cal_client.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Cal.com integration not configured"
        )
    
    slots = await cal_client.get_available_slots(
        event_type_id=event_type_id,
        start_date=start_date,
        end_date=end_date,
        timezone=timezone
    )
    return {"available_slots": slots}


@router.post("/create-link")
async def create_booking_link(request: BookingLinkRequest):
    """
    Create a booking link with pre-filled information.
    
    This creates a Cal.com URL that pre-fills the prospect's information.
    """
    if not cal_client.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Cal.com integration not configured"
        )
    
    link = await cal_client.get_booking_link(
        event_type_slug=request.event_type_slug,
        username=request.username,
        name=request.name,
        email=request.email
    )
    
    return {"booking_url": link}


@router.post("/create-booking")
async def create_booking(request: CreateBookingRequest):
    """
    Create a booking directly through the API.
    """
    if not cal_client.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Cal.com integration not configured"
        )
    
    # Validate datetime format
    try:
        datetime.fromisoformat(request.start_time.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid start_time format. Use ISO format: YYYY-MM-DDTHH:MM:SSZ"
        )
    
    booking = await cal_client.create_booking(
        event_type_id=request.event_type_id,
        start_time=request.start_time,
        name=request.name,
        email=request.email,
        phone=request.phone,
        notes=request.notes,
        timezone=request.timezone
    )
    
    if not booking:
        raise HTTPException(
            status_code=500,
            detail="Failed to create booking"
        )
    
    return booking


@router.post("/send-link-sms")
async def send_link_sms(request: SendLinkSMSRequest):
    """
    Send a booking link via SMS.
    
    Requires Twilio to be configured.
    """
    if not cal_client.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Cal.com integration not configured"
        )
    
    # Import Twilio client
    try:
        from twilio.rest import Client
        import os
        
        twilio_client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail="Twilio not configured"
        )
    
    success = await cal_client.send_booking_link_sms(
        phone=request.phone,
        name=request.name,
        email=request.email,
        booking_url=request.booking_url,
        twilio_client=twilio_client
    )
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to send SMS"
        )
    
    return {"message": "Booking link sent via SMS"}
