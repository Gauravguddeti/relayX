"""
Scheduled events routes - manages calendar events linked to calls.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from auth_routes import get_current_user_id
from shared.database import db
from shared.cal_client import cal_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["events"])


class ScheduledEvent(BaseModel):
    """Scheduled event model."""
    id: Optional[str] = None
    user_id: str
    call_id: Optional[str] = None
    campaign_id: Optional[str] = None
    event_type: str
    title: str
    scheduled_at: str
    duration_minutes: int = 30
    timezone: str = "America/New_York"
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    cal_booking_id: Optional[int] = None
    cal_booking_uid: Optional[str] = None
    status: str = "scheduled"
    notes: Optional[str] = None


@router.get("/upcoming")
async def get_upcoming_events(
    user_id: str = Depends(get_current_user_id),
    limit: int = 10
):
    """
    Get upcoming scheduled events for the current user.
    Combines both Cal.com bookings and manually created events.
    """
    try:
        # Get events from database using Supabase
        from datetime import datetime
        
        result = db.client.table("scheduled_events").select(
            "id, call_id, campaign_id, event_type, title, scheduled_at, "
            "duration_minutes, timezone, contact_name, contact_email, contact_phone, "
            "status, notes, created_automatically, cal_booking_id"
        ).eq("user_id", user_id).eq("status", "scheduled").gte(
            "scheduled_at", datetime.now().isoformat()
        ).order("scheduled_at", desc=False).limit(limit).execute()
        
        events = result.data if result.data else []
        
        # Format events for frontend
        formatted_events = []
        for event in events:
            formatted_events.append({
                "id": event.get("id"),
                "call_id": event.get("call_id"),
                "campaign_id": event.get("campaign_id"),
                "type": event.get("event_type"),
                "title": event.get("title"),
                "scheduled_at": event.get("scheduled_at"),
                "contact_name": event.get("contact_name"),
                "phone_number": event.get("contact_phone"),
                "notes": event.get("notes"),
                "status": event.get("status"),
                "created_automatically": event.get("created_automatically", False)
            })
        
        logger.info(f"Retrieved {len(formatted_events)} upcoming events for user {user_id}")
        return {"events": formatted_events}
        
    except Exception as e:
        logger.error(f"Error fetching upcoming events: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"events": []}


@router.post("/create")
async def create_scheduled_event(
    event: ScheduledEvent,
    user_id: str = Depends(get_current_user_id)
):
    """
    Create a scheduled event manually.
    Optionally creates a Cal.com booking if configured.
    """
    try:
        # Validate user_id matches
        if event.user_id != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Create Cal.com booking if configured and email provided
        cal_booking_id = None
        cal_booking_uid = None
        
        if cal_client.is_configured() and event.contact_email:
            try:
                # Get first available event type
                event_types = await cal_client.get_event_types()
                if event_types:
                    event_type_id = event_types[0]["id"]
                    
                    # Create Cal.com booking
                    booking = await cal_client.create_booking(
                        event_type_id=event_type_id,
                        start_time=event.scheduled_at,
                        name=event.contact_name or "Contact",
                        email=event.contact_email,
                        phone=event.contact_phone,
                        notes=event.notes,
                        timezone=event.timezone
                    )
                    
                    if booking:
                        cal_booking_id = booking.get("id")
                        cal_booking_uid = booking.get("uid")
                        logger.info(f"Created Cal.com booking: {cal_booking_uid}")
            except Exception as e:
                logger.warning(f"Failed to create Cal.com booking: {e}")
        
        # Insert into database using Supabase
        event_data = {
            "user_id": user_id,
            "call_id": event.call_id,
            "campaign_id": event.campaign_id,
            "event_type": event.event_type,
            "title": event.title,
            "scheduled_at": event.scheduled_at,
            "duration_minutes": event.duration_minutes,
            "timezone": event.timezone,
            "contact_name": event.contact_name,
            "contact_email": event.contact_email,
            "contact_phone": event.contact_phone,
            "cal_booking_id": cal_booking_id,
            "cal_booking_uid": cal_booking_uid,
            "status": event.status,
            "notes": event.notes,
            "created_automatically": False
        }
        
        result = db.client.table("scheduled_events").insert(event_data).execute()
        
        event_id = result.data[0]["id"] if result.data else None
        
        logger.info(f"Created scheduled event: {event_id}")
        return {"success": True, "event_id": event_id}
        
    except Exception as e:
        logger.error(f"Error creating scheduled event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{event_id}")
async def delete_scheduled_event(
    event_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a scheduled event (only if owned by current user)."""
    try:
        # Verify ownership using Supabase
        result = db.client.table("scheduled_events").select("user_id").eq("id", event_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Event not found")
        
        if result.data[0]["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Delete event
        db.client.table("scheduled_events").delete().eq("id", event_id).execute()
        
        logger.info(f"Deleted scheduled event: {event_id}")
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting scheduled event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def init_db(database):
    """Initialize the database connection for scheduled events."""
    global db
    db = database
    logger.info("Scheduled events routes initialized")
