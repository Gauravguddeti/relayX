"""Test the events API endpoint"""
import asyncio
import os
from shared.database import SupabaseDB
from datetime import datetime

async def test_api():
    db = SupabaseDB(
        url=os.getenv("SUPABASE_URL"),
        key=os.getenv("SUPABASE_ANON_KEY")
    )
    
    user_id = "6bc4291b-cd1e-49d1-98a8-31c12bbdb7f2"
    limit = 10
    
    print(f"Testing API query for user_id: {user_id}")
    print(f"Current time: {datetime.now().isoformat()}\n")
    
    # Simulate the API query
    result = db.client.table("scheduled_events").select(
        "id, call_id, campaign_id, event_type, title, scheduled_at, "
        "duration_minutes, timezone, contact_name, contact_email, contact_phone, "
        "status, notes, created_automatically, cal_booking_id"
    ).eq("user_id", user_id).eq("status", "scheduled").gte(
        "scheduled_at", datetime.now().isoformat()
    ).order("scheduled_at", desc=False).limit(limit).execute()
    
    events = result.data if result.data else []
    
    print(f"Found {len(events)} events:\n")
    for event in events:
        print(f"  - {event['title']} at {event['scheduled_at']}")
        print(f"    ID: {event['id']}")
        print(f"    Type: {event['event_type']}")
        print(f"    Status: {event['status']}")
        print()

asyncio.run(test_api())
