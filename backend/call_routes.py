from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from loguru import logger
from shared.database import get_db, SupabaseDB
from twilio.rest import Client as TwilioClient
import os
import httpx
import base64

router = APIRouter()

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
VOICE_GATEWAY_URL = os.getenv("VOICE_GATEWAY_URL", "https://your-ngrok-url.ngrok.io")

if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
    logger.warning("Twilio credentials not fully configured")
    twilio_client = None
else:
    twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ==================== MODELS ====================

class OutboundCallRequest(BaseModel):
    agent_id: str = Field(..., description="ID of the agent to use")
    to_number: str = Field(..., description="Phone number to call (E.164 format)")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class CallResponse(BaseModel):
    id: str
    agent_id: str
    to_number: str
    from_number: str
    status: str
    twilio_call_sid: Optional[str] = None
    created_at: datetime


class CallUpdate(BaseModel):
    status: Optional[str] = None

# ==================== HELPER FUNCTIONS ====================

async def initiate_twilio_call(call_id: str, to_number: str, db: SupabaseDB):
    """Background task to initiate Twilio call"""
    try:
        if not twilio_client:
            logger.error("Twilio client not initialized")
            return

        # Get ngrok URL from voice gateway
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                vg_response = await client.get("http://localhost:8001/info")
                vg_data = vg_response.json()
                gateway_url = vg_data.get("ngrok_url", VOICE_GATEWAY_URL)
        except:
            gateway_url = VOICE_GATEWAY_URL
            logger.warning(f"Could not get ngrok URL, using configured: {gateway_url}")
        
        # Construct TwiML URL for voice gateway
        twiml_url = f"{gateway_url}/twiml/{call_id}"
        
        logger.info(f"Initiating Twilio call to {to_number} with TwiML: {twiml_url}")
        
        # Make the call with recording enabled
        call = twilio_client.calls.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            url=twiml_url,
            status_callback=f"{gateway_url}/callbacks/status/{call_id}",
            status_callback_event=["initiated", "ringing", "answered", "completed", "busy", "no-answer", "failed", "canceled"],
            status_callback_method="POST",
            method="POST",  # Use POST for TwiML URL
            record=True,  # Enable call recording
            recording_status_callback=f"{gateway_url}/callbacks/recording/{call_id}",
            recording_status_callback_method="POST"
        )
        
        logger.info(f"✅ Call created - SID: {call.sid} | TwiML will be requested from: {twiml_url}")
        
        # Update call record with Twilio SID
        await db.update_call(
            call_id,
            twilio_call_sid=call.sid,
            status="initiated"
        )
        
        logger.info(f"Twilio call created successfully: {call.sid}")
        
    except Exception as e:
        logger.error(f"Error initiating Twilio call for {call_id}: {e}", exc_info=True)
        await db.update_call(
            call_id,
            status="failed",
            error_message=str(e)
        )

# ==================== ROUTES ====================

from auth import get_current_user_id

@router.post("/calls/outbound", response_model=CallResponse)
async def create_outbound_call(
    call_request: OutboundCallRequest,
    background_tasks: BackgroundTasks,
    db: SupabaseDB = Depends(get_db)
):
    """
    Initiate an outbound call
    """
    try:
        # Validate agent
        agent = await db.get_agent(call_request.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if not agent.get("is_active"):
            raise HTTPException(status_code=400, detail="Agent is not active")
        
        # Check Twilio client
        if not twilio_client:
            raise HTTPException(status_code=500, detail="Twilio not configured")
        
        # Create call record with explicit direction and user_id from agent
        call_record = await db.create_call(
            agent_id=call_request.agent_id,
            to_number=call_request.to_number,
            from_number=TWILIO_PHONE_NUMBER,
            direction="outbound",
            user_id=agent.get("user_id"),  # Associate call with agent's owner
            metadata=call_request.metadata
        )
        
        call_id = call_record["id"]
        
        # Initiate Twilio call in background
        background_tasks.add_task(
            initiate_twilio_call,
            call_id=call_id,
            to_number=call_request.to_number,
            db=db
        )
        
        logger.info(f"Outbound call initiated: {call_id} to {call_request.to_number}")
        
        return CallResponse(**call_record)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating outbound call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/demo-call")
async def create_demo_call(
    request: dict,
    background_tasks: BackgroundTasks,
    db: SupabaseDB = Depends(get_db)
):
    """
    Trigger a demo call for landing page
    This uses the demo agent configured in environment
    """
    try:
        name = request.get("name")
        phone = request.get("phone")
        
        if not name or not phone:
            raise HTTPException(status_code=422, detail="Name and phone are required")
        
        # Get landing page agent ID from environment
        demo_agent_id = os.getenv("LANDING_PAGE_AGENT_ID")
        if not demo_agent_id:
            raise HTTPException(status_code=500, detail="Landing page agent not configured")
        
        # Validate agent
        agent = await db.get_agent(demo_agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Demo agent not found")
        
        # Check Twilio
        if not twilio_client:
            raise HTTPException(status_code=500, detail="Twilio not configured")
        
        # Create call record
        call_record = await db.create_call(
            agent_id=demo_agent_id,
            to_number=phone,
            from_number=TWILIO_PHONE_NUMBER,
            direction="outbound",
            metadata={"demo": True, "name": name, "source": "landing_page"}
        )
        
        call_id = call_record["id"]
        
        # Initiate call in background
        background_tasks.add_task(
            initiate_twilio_call,
            call_id=call_id,
            to_number=phone,
            db=db
        )
        
        logger.info(f"Demo call initiated: {call_id} to {phone} for {name}")
        
        return {"success": True, "call_id": call_id, "message": "Call initiated"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating demo call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calls/{call_id}", response_model=dict)
async def get_call(
    call_id: str,
    user_id: str = Depends(get_current_user_id),
    db: SupabaseDB = Depends(get_db)
):
    """Get call details by ID (user's calls only)"""
    try:
        result = db.client.table("calls").select("*").eq("id", call_id).eq("user_id", user_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Call not found")
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calls", response_model=List[dict])
async def list_calls(
    user_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: SupabaseDB = Depends(get_db)
):
    """List calls with optional filters (user's calls only)"""
    try:
        query = db.client.table("calls").select("*").order("created_at", desc=True).limit(limit)
        
        # Filter by user_id if provided
        if user_id:
            query = query.eq("user_id", user_id)
        
        if agent_id:
            query = query.eq("agent_id", agent_id)
        if status:
            query = query.eq("status", status)
        
        result = query.execute()
        return result.data or []
    except Exception as e:
        logger.error(f"Error listing calls: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calls/{call_id}/transcripts", response_model=List[dict])
async def get_call_transcripts(call_id: str, db: SupabaseDB = Depends(get_db)):
    """Get transcripts for a call"""
    try:
        # Verify call exists
        call = await db.get_call(call_id)
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        transcripts = await db.get_transcripts(call_id)
        return transcripts
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transcripts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calls/{call_id}/analysis", response_model=dict)
async def get_call_analysis(call_id: str, db: SupabaseDB = Depends(get_db)):
    """Get call analysis (summary, outcome, sentiment)"""
    try:
        # Verify call exists
        call = await db.get_call(call_id)
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        analysis = await db.get_call_analysis(call_id)
        if not analysis:
            return {"message": "No analysis available for this call"}
        
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching call analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/calls/{call_id}")
async def update_call(call_id: str, update: CallUpdate, db: SupabaseDB = Depends(get_db)):
    """Update call status"""
    try:
        call = await db.get_call(call_id)
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        update_data = {}
        if update.status:
            update_data["status"] = update.status
        
        await db.update_call(call_id, **update_data)
        updated_call = await db.get_call(call_id)
        return updated_call
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calls/{call_id}/recording")
@router.head("/calls/{call_id}/recording")
async def get_call_recording(call_id: str, db: SupabaseDB = Depends(get_db)):
    """
    Get recording metadata for a call (supports HEAD for existence check)
    """
    try:
        call = await db.get_call(call_id)
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        recording_url = call.get("recording_url")
        if not recording_url:
            return {"message": "No recording available for this call"}
        
        return {
            "has_recording": True,
            "recording_duration": call.get("recording_duration"),
            "call_id": call_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recording: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calls/{call_id}/recording/stream")
async def stream_call_recording(call_id: str, db: SupabaseDB = Depends(get_db)):
    """
    Stream recording audio with Twilio authentication
    Acts as a proxy to avoid browser auth prompts
    """
    try:
        call = await db.get_call(call_id)
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        recording_url = call.get("recording_url")
        if not recording_url:
            raise HTTPException(status_code=404, detail="No recording available")
        
        # Fetch recording from Twilio with authentication
        auth_string = f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                recording_url,
                headers={"Authorization": f"Basic {auth_b64}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail="Failed to fetch recording from Twilio")
            
            # Stream the audio back to the client
            return StreamingResponse(
                iter([response.content]),
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": f"inline; filename=recording_{call_id}.mp3",
                    "Accept-Ranges": "bytes"
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming recording: {e}")
        raise HTTPException(status_code=500, detail=str(e))
