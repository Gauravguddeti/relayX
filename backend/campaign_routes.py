"""
Campaign management routes for bulk scheduled calls
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import json
from loguru import logger

from shared.database import SupabaseDB
from contact_parser import ContactParser
from auth import get_current_user_id

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

# ============================================================================
# Models
# ============================================================================

class CampaignSettings(BaseModel):
    agent_id: str
    timezone: str = "UTC"
    scheduled_start_time: Optional[datetime] = None
    pacing_seconds: int = 10
    business_hours_enabled: bool = False
    business_hours_days: List[int] = [1, 2, 3, 4, 5]  # Monday-Friday
    business_hours_start: str = "09:00"
    business_hours_end: str = "17:00"
    max_retries: int = 3
    retry_backoff_hours: List[int] = [1, 4, 24]

class CampaignResponse(BaseModel):
    id: str
    name: str
    state: str
    agent_id: str
    timezone: str
    stats: Dict[str, Any]
    scheduled_start_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class ContactResponse(BaseModel):
    id: str
    phone: str
    name: Optional[str]
    metadata: Dict[str, Any]
    state: str
    outcome: Optional[str]
    retry_count: int
    last_attempted_at: Optional[datetime]

# ============================================================================
# Dependency
# ============================================================================

def get_db():
    return SupabaseDB()

# ============================================================================
# Routes
# ============================================================================

@router.post("/parse-preview", response_model=Dict[str, Any])
async def parse_preview(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id)
):
    """
    Parse uploaded file and return preview without creating campaign
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Parse contacts
        parser = ContactParser(default_country='US')
        contacts, errors = parser.parse_file(file_content, file.filename)
        
        if not contacts:
            raise HTTPException(
                status_code=400,
                detail=f"No valid contacts found. Errors: {', '.join(errors)}"
            )
        
        # Extract metadata fields (excluding phone and name)
        metadata_fields = set()
        for contact in contacts[:10]:  # Sample first 10
            if 'metadata' in contact:
                metadata_fields.update(contact['metadata'].keys())
        
        return {
            "total_contacts": len(contacts) + len(errors),
            "valid_contacts": len(contacts),
            "invalid_contacts": len(errors),
            "metadata_fields": sorted(list(metadata_fields)),
            "sample_contacts": contacts[:5],  # First 5 for preview
            "errors": errors[:10]  # First 10 errors
        }
        
    except Exception as e:
        logger.error(f"Failed to parse file: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/create", response_model=Dict[str, Any])
async def create_campaign(
    file: UploadFile = File(...),
    name: str = Form(...),
    agent_id: str = Form(...),
    timezone: str = Form("UTC"),
    scheduled_start_time: Optional[str] = Form(None),
    settings: str = Form("{}"),
    user_id: str = Depends(get_current_user_id),
    db: SupabaseDB = Depends(get_db)
):
    """
    Create a new campaign from uploaded contact file
    
    Steps:
    1. Parse and validate uploaded file
    2. Normalize phone numbers and deduplicate
    3. Validate agent exists
    4. Create campaign in draft state
    5. Insert contacts with flexible metadata
    """
    try:
        # Parse settings from JSON string
        settings_dict = json.loads(settings) if settings else {}
        
        # Validate agent exists
        agent = await db.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if agent.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Agent does not belong to user")
        
        # Read file content
        file_content = await file.read()
        
        # Parse contacts
        parser = ContactParser(default_country='US')  # TODO: Make configurable
        contacts, errors = parser.parse_file(file_content, file.filename)
        
        if not contacts:
            error_msg = "; ".join(errors) if errors else "No valid contacts found in file"
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Parse scheduled start time if provided
        parsed_start_time = None
        if scheduled_start_time:
            try:
                parsed_start_time = datetime.fromisoformat(scheduled_start_time.replace('Z', '+00:00'))
            except Exception as e:
                logger.warning(f"Invalid scheduled_start_time format: {e}")
        
        # Build settings snapshot from frontend settings
        pacing_seconds = settings_dict.get('pacing_seconds', 30)
        max_retries = settings_dict.get('max_retries', 2)
        business_hours = settings_dict.get('business_hours', None)
        
        settings_snapshot = {
            "agent_snapshot": {
                "id": agent['id'],
                "name": agent['name'],
                "prompt_text": agent.get('prompt_text', '')
            },
            "pacing": {
                "delay_seconds": pacing_seconds
            },
            "retry_policy": {
                "max_retries": max_retries,
                "backoff_hours": [1, 4, 24][:max_retries],
                "retryable_outcomes": ["no-answer", "busy", "failed"]
            }
        }
        
        # Add business hours if enabled
        if business_hours:
            settings_snapshot["business_hours"] = {
                "enabled": True,
                "days": business_hours.get('days', [1, 2, 3, 4, 5]),
                "start_time": business_hours.get('start', '09:00'),
                "end_time": business_hours.get('end', '17:00')
            }
        else:
            settings_snapshot["business_hours"] = {
                "enabled": False,
                "days": [],
                "start_time": "00:00",
                "end_time": "23:59"
            }
        
        # Determine initial state
        initial_state = "pending" if parsed_start_time else "draft"
        
        # Create campaign
        campaign_data = {
            "user_id": user_id,
            "agent_id": agent_id,
            "name": name,
            "state": initial_state,
            "timezone": timezone,
            "settings_snapshot": settings_snapshot,
            "scheduled_start_time": parsed_start_time.isoformat() if parsed_start_time else None,
            "stats": {
                "total": len(contacts),
                "completed": 0,
                "failed": 0,
                "pending": len(contacts),
                "calling": 0,
                "success_rate": 0
            }
        }
        
        result = db.client.table("bulk_campaigns").insert(campaign_data).execute()
        campaign = result.data[0]
        campaign_id = campaign['id']
        
        # Insert contacts
        contact_records = []
        for contact in contacts:
            contact_records.append({
                "campaign_id": campaign_id,
                "phone": contact['phone'],
                "name": contact.get('name'),
                "metadata": contact.get('metadata', {}),
                "state": "pending"
            })
        
        # Batch insert (Supabase handles large inserts well)
        db.client.table("campaign_contacts").insert(contact_records).execute()
        
        logger.info(f"Created campaign {campaign_id} with {len(contacts)} contacts")
        
        return {
            "campaign": campaign,
            "contacts_imported": len(contacts),
            "errors": errors if errors else []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=Dict[str, Any])
async def list_campaigns(
    state: Optional[str] = None,
    limit: int = 50,
    user_id: str = Depends(get_current_user_id),
    db: SupabaseDB = Depends(get_db)
):
    """List campaigns for the authenticated user"""
    try:
        query = db.client.table("bulk_campaigns").select("*, agent:agent_id(name)").eq("user_id", user_id).order("created_at", desc=True).limit(limit)
        
        if state:
            query = query.eq("state", state)
        
        result = query.execute()
        
        # Flatten agent data
        campaigns = []
        for campaign in (result.data or []):
            agent_data = campaign.pop('agent', None)
            if agent_data and isinstance(agent_data, dict):
                campaign['agent_name'] = agent_data.get('name')
            campaigns.append(campaign)
        
        return {"campaigns": campaigns}
        
    except Exception as e:
        logger.error(f"Error listing campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{campaign_id}", response_model=Dict[str, Any])
async def get_campaign(
    campaign_id: str,
    user_id: str = Depends(get_current_user_id),
    db: SupabaseDB = Depends(get_db)
):
    """Get campaign details"""
    try:
        result = db.client.table("bulk_campaigns").select("*").eq("id", campaign_id).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{campaign_id}/contacts", response_model=Dict[str, Any])
async def get_campaign_contacts(
    campaign_id: str,
    state: Optional[str] = None,
    limit: int = 1000,
    user_id: str = Depends(get_current_user_id),
    db: SupabaseDB = Depends(get_db)
):
    """Get contacts for a campaign"""
    try:
        # Verify campaign belongs to user
        campaign_result = db.client.table("bulk_campaigns").select("id").eq("id", campaign_id).eq("user_id", user_id).execute()
        
        if not campaign_result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Get contacts
        query = db.client.table("campaign_contacts").select("*").eq("campaign_id", campaign_id).order("created_at").limit(limit)
        
        if state:
            query = query.eq("state", state)
        
        result = query.execute()
        return {"contacts": result.data or []}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting contacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{campaign_id}/start")
async def start_campaign(
    campaign_id: str,
    user_id: str = Depends(get_current_user_id),
    db: SupabaseDB = Depends(get_db)
):
    """Start a campaign (draft -> pending)"""
    try:
        # Get campaign
        result = db.client.table("bulk_campaigns").select("*").eq("id", campaign_id).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        campaign = result.data[0]
        
        if campaign['state'] not in ['draft', 'paused']:
            raise HTTPException(status_code=400, detail=f"Cannot start campaign in state: {campaign['state']}")
        
        # Update to pending (scheduler will pick it up)
        update_data = {
            "state": "pending",
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        
        db.client.table("bulk_campaigns").update(update_data).eq("id", campaign_id).execute()
        
        logger.info(f"Campaign {campaign_id} started by user {user_id}")
        
        return {"message": "Campaign started", "campaign_id": campaign_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: str,
    user_id: str = Depends(get_current_user_id),
    db: SupabaseDB = Depends(get_db)
):
    """Pause a running campaign"""
    try:
        result = db.client.table("bulk_campaigns").select("state").eq("id", campaign_id).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        if result.data[0]['state'] not in ['running', 'pending']:
            raise HTTPException(status_code=400, detail="Campaign is not running")
        
        db.client.table("bulk_campaigns").update({"state": "paused"}).eq("id", campaign_id).execute()
        
        logger.info(f"Campaign {campaign_id} paused by user {user_id}")
        
        return {"message": "Campaign paused"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{campaign_id}")
async def update_campaign(
    campaign_id: str,
    update_data: Dict[str, Any],
    user_id: str = Depends(get_current_user_id),
    db: SupabaseDB = Depends(get_db)
):
    """Update campaign details (e.g., rename)"""
    try:
        # Verify campaign belongs to user
        result = db.client.table("bulk_campaigns").select("id").eq("id", campaign_id).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Build update data
        allowed_fields = {"name"}
        filtered_update = {k: v for k, v in update_data.items() if k in allowed_fields}
        
        if not filtered_update:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        # Update campaign
        db.client.table("bulk_campaigns").update(filtered_update).eq("id", campaign_id).execute()
        
        logger.info(f"Campaign {campaign_id} updated by user {user_id}: {filtered_update}")
        
        return {"message": "Campaign updated", "campaign_id": campaign_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    user_id: str = Depends(get_current_user_id),
    db: SupabaseDB = Depends(get_db)
):
    """Delete a campaign (only if draft or completed)"""
    try:
        result = db.client.table("bulk_campaigns").select("state").eq("id", campaign_id).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        state = result.data[0]['state']
        if state in ['running', 'pending']:
            raise HTTPException(status_code=400, detail="Cannot delete running campaign. Pause it first.")
        
        # Delete (cascade will delete contacts)
        db.client.table("bulk_campaigns").delete().eq("id", campaign_id).execute()
        
        logger.info(f"Campaign {campaign_id} deleted by user {user_id}")
        
        return {"message": "Campaign deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))
