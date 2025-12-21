"""
Calendly integration routes for booking appointments.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import logging

from shared.calendly_client import calendly_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendly", tags=["calendly"])


class SchedulingLinkRequest(BaseModel):
    """Request to create a personalized scheduling link."""
    name: str
    email: EmailStr
    phone: Optional[str] = None
    notes: Optional[str] = None


class ScheduleEventRequest(BaseModel):
    """Request to schedule an event directly."""
    name: str
    email: EmailStr
    start_time: str  # ISO format datetime
    phone: Optional[str] = None
    notes: Optional[str] = None


class SendLinkSMSRequest(BaseModel):
    """Request to send scheduling link via SMS."""
    phone: str
    name: str
    email: EmailStr


@router.get("/status")
async def get_calendly_status():
    """Check if Calendly integration is configured."""
    is_configured = calendly_client.is_configured()
    
    if is_configured:
        user_info = await calendly_client.get_user_info()
        return {
            "configured": True,
            "user": user_info.get("resource") if user_info else None,
            "event_type_url": calendly_client.event_type_url
        }
    
    return {
        "configured": False,
        "message": "Calendly API token not configured"
    }


@router.get("/available-times")
async def get_available_times(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get available time slots for scheduling.
    
    Query params:
        - start_date: YYYY-MM-DD format (defaults to today)
        - end_date: YYYY-MM-DD format (defaults to 30 days from start)
    """
    if not calendly_client.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Calendly integration not configured"
        )
    
    times = await calendly_client.get_available_times(start_date, end_date)
    return {"available_times": times}


@router.post("/create-link")
async def create_scheduling_link(request: SchedulingLinkRequest):
    """
    Create a personalized scheduling link for a prospect.
    
    This pre-fills their name, email, and phone on the Calendly booking page.
    """
    if not calendly_client.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Calendly integration not configured"
        )
    
    link = await calendly_client.create_scheduling_link(
        name=request.name,
        email=request.email,
        phone=request.phone,
        notes=request.notes
    )
    
    if not link:
        raise HTTPException(
            status_code=500,
            detail="Failed to create scheduling link"
        )
    
    return {"scheduling_url": link}


@router.post("/schedule-event")
async def schedule_event(request: ScheduleEventRequest):
    """
    Schedule an event directly (requires appropriate Calendly permissions).
    """
    if not calendly_client.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Calendly integration not configured"
        )
    
    # Validate datetime format
    try:
        datetime.fromisoformat(request.start_time.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid start_time format. Use ISO format: YYYY-MM-DDTHH:MM:SSZ"
        )
    
    event = await calendly_client.schedule_event(
        name=request.name,
        email=request.email,
        start_time=request.start_time,
        phone=request.phone,
        notes=request.notes
    )
    
    if not event:
        raise HTTPException(
            status_code=500,
            detail="Failed to schedule event"
        )
    
    return event


@router.post("/send-link-sms")
async def send_link_sms(request: SendLinkSMSRequest):
    """
    Send a personalized scheduling link via SMS.
    
    Requires Twilio to be configured.
    """
    if not calendly_client.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Calendly integration not configured"
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
    
    success = await calendly_client.send_scheduling_link_sms(
        phone=request.phone,
        name=request.name,
        email=request.email,
        twilio_client=twilio_client
    )
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to send SMS"
        )
    
    return {"message": "Scheduling link sent via SMS"}
