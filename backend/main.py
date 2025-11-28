"""
FastAPI Backend for RelayX AI Caller
Handles API endpoints for agents, calls, and Twilio webhooks
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta, timezone
import sys
import os
from loguru import logger
from collections import defaultdict
import time

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from shared.database import get_db, SupabaseDB
from shared.llm_client import get_llm_client, LLMClient
from twilio.rest import Client as TwilioClient
from dotenv import load_dotenv
import subprocess
import httpx

# Load environment variables
load_dotenv()

# Configure logger
logger.add("logs/backend.log", rotation="1 day", retention="7 days", level="INFO")

# Initialize FastAPI
app = FastAPI(
    title="RelayX AI Caller API",
    description="Backend for AI-powered outbound calling system",
    version="1.0.0"
)

# Mount static files for dashboard
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Twilio client
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
VOICE_GATEWAY_URL = os.getenv("VOICE_GATEWAY_URL", "https://your-ngrok-url.ngrok.io")

if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
    logger.warning("Twilio credentials not fully configured")
    twilio_client = None
else:
    twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    logger.info("Twilio client initialized")


# ==================== MODELS ====================

class AgentCreate(BaseModel):
    name: str = Field(..., description="Agent name")
    prompt_text: str = Field(..., description="Agent prompt snapshot")
    template_source: Optional[str] = Field(None, description="Name of template this agent was created from (for badge display)")
    voice_settings: dict = Field(default_factory=dict, description="Voice configuration")
    llm_model: str = Field(default="llama3:8b", description="LLM model to use")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=150, ge=50, le=500)
    is_active: bool = Field(default=True)


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    prompt_text: Optional[str] = None
    template_source: Optional[str] = None
    voice_settings: Optional[dict] = None
    llm_model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    is_active: Optional[bool] = None


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


class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=255, description="Template name")
    description: Optional[str] = Field(None, max_length=500, description="Brief description")
    content: str = Field(..., min_length=50, max_length=2000, description="Template prompt content")
    category: str = Field(default="custom", description="Category: receptionist, sales, reminder, support, custom")


class PreviewRequest(BaseModel):
    prompt_text: str = Field(..., min_length=10, max_length=2000, description="Prompt to test")
    sample_user_input: str = Field(..., min_length=1, max_length=500, description="Sample user input")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=150, ge=50, le=300)


# ==================== DASHBOARD ====================

@app.get("/dashboard")
async def dashboard():
    """Serve the web dashboard"""
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "dashboard.html"))


@app.get("/prompts")
async def prompts_page():
    """Serve the system prompts editor page"""
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "prompts.html"))


@app.get("/stats")
async def get_stats(db: SupabaseDB = Depends(get_db)):
    """Get system statistics for dashboard"""
    try:
        agents = await db.list_agents()
        calls = await db.list_calls()
        
        # Cleanup stale calls (older than 10 minutes in active status)
        from datetime import timezone
        stale_threshold = datetime.now(timezone.utc) - timedelta(minutes=10)
        for call in calls:
            if call.get("status") in ["initiated", "in-progress"]:
                try:
                    call_time_str = call.get("created_at")
                    if call_time_str:
                        # Parse ISO format with timezone
                        call_time = datetime.fromisoformat(call_time_str.replace("Z", "+00:00"))
                        if call_time < stale_threshold:
                            await db.update_call(call["id"], status="failed")
                            logger.info(f"Auto-cleaned stale call: {call['id']}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup stale call {call.get('id')}: {e}")
        
        # Get active calls from voice gateway
        import httpx
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                vg_response = await client.get("http://localhost:8001/")
                vg_data = vg_response.json()
                active_calls = vg_data.get("active_calls", 0)
        except:
            active_calls = 0
        
        return {
            "total_agents": len(agents),
            "total_calls": len(calls),
            "active_calls": active_calls,
            "calls_completed": len([c for c in calls if c.get("status") == "completed"]),
            "calls_failed": len([c for c in calls if c.get("status") == "failed"]),
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {"total_agents": 0, "total_calls": 0, "active_calls": 0}


@app.get("/info")
async def get_info(db: SupabaseDB = Depends(get_db)):
    """Get backend info including ngrok URL"""
    try:
        # Get today's calls count
        calls = await db.list_calls()
        today = datetime.now().strftime("%Y-%m-%d")
        today_calls = [c for c in calls if c.get("started_at") and str(c.get("started_at")).startswith(today)]
        
        # Get ngrok URL from voice gateway
        ngrok_url = VOICE_GATEWAY_URL
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                vg_response = await client.get("http://localhost:8001/info")
                vg_data = vg_response.json()
                ngrok_url = vg_data.get("ngrok_url", VOICE_GATEWAY_URL)
        except:
            pass
        
        return {
            "service": "RelayX Backend",
            "status": "running",
            "today_calls": len(today_calls),
            "ngrok_url": ngrok_url,
            "public_url": ngrok_url
        }
        
    except Exception as e:
        logger.warning(f"Could not get info: {e}")
        return {
            "service": "RelayX Backend",
            "status": "running",
            "today_calls": 0,
            "ngrok_url": VOICE_GATEWAY_URL,
            "public_url": VOICE_GATEWAY_URL
        }


@app.get("/api-credits")
async def get_api_credits(db: SupabaseDB = Depends(get_db)):
    """Get real-time API credit usage from Groq"""
    import httpx
    credits = {
        "groq": {
            "status": "unknown",
            "requests_limit": 30,
            "requests_remaining": "?",
            "tokens_limit": 8000,
            "tokens_remaining": "?"
        }
    }
    
    try:
        # Get today's calls for usage estimation
        calls = await db.list_calls()
        today = datetime.now().strftime("%Y-%m-%d")
        today_calls = [c for c in calls if c.get("started_at") and str(c.get("started_at")).startswith(today)]
        
        # Estimate Groq usage (tokens and requests)
        # Approximate: 500 tokens per call (STT + LLM combined)
        estimated_tokens_used = len(today_calls) * 500
        groq_tokens_remaining = max(0, 8000 - estimated_tokens_used)
        groq_requests_remaining = max(0, 30 - len(today_calls))
        
        credits["groq"]["status"] = "estimated"
        credits["groq"]["tokens_remaining"] = groq_tokens_remaining
        credits["groq"]["requests_remaining"] = groq_requests_remaining
        credits["groq"]["today_calls"] = len(today_calls)
        
        logger.debug(f"API Credits - Groq: {groq_tokens_remaining} tokens")
        
    except Exception as e:
        logger.warning(f"Could not estimate API credits: {e}")
        credits["groq"]["status"] = "error"
    
    return credits


# ==================== HEALTH CHECK ====================

@app.get("/logs")
async def get_logs():
    """Get recent voice gateway logs (legacy endpoint)"""
    try:
        result = subprocess.run(
            ["docker", "logs", "relayx-voice-gateway", "--tail", "50"],
            capture_output=True,
            text=True,
            timeout=5
        )
        logs = result.stdout + result.stderr
        return {"logs": logs, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"logs": f"Error fetching logs: {str(e)}", "timestamp": datetime.now().isoformat()}


@app.get("/api/logs/backend")
async def get_backend_logs():
    """Get recent backend logs"""
    try:
        result = subprocess.run(
            ["docker", "logs", "relayx-backend", "--tail", "100"],
            capture_output=True,
            text=True,
            timeout=5
        )
        logs = result.stdout + result.stderr
        return {"logs": logs, "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        logger.error(f"Error fetching backend logs: {e}")
        return {"logs": f"Error fetching logs: {str(e)}", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/logs/voice-gateway")
async def get_voice_gateway_logs():
    """Get recent voice gateway logs"""
    try:
        result = subprocess.run(
            ["docker", "logs", "relayx-voice-gateway", "--tail", "100"],
            capture_output=True,
            text=True,
            timeout=5
        )
        logs = result.stdout + result.stderr
        return {"logs": logs, "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        logger.error(f"Error fetching voice gateway logs: {e}")
        return {"logs": f"Error fetching logs: {str(e)}", "timestamp": datetime.now(timezone.utc).isoformat()}


# ==================== PERMISSIONS ====================

# Simple role-based access control
ADMIN_USERS = ["admin", "system"]  # TODO: Load from database or config

def is_admin(user_id: str) -> bool:
    """Check if user has admin privileges"""
    return user_id in ADMIN_USERS


def check_prompt_permission(user_id: str, prompt_owner_id: str, is_locked: bool) -> bool:
    """
    Check if user can edit a prompt.
    Rules:
    - Admins can edit anything
    - Users can only edit their own non-locked prompts
    - No one can edit locked templates (system templates)
    """
    if is_locked:
        return False  # Locked templates cannot be edited by anyone
    if is_admin(user_id):
        return True
    return user_id == prompt_owner_id


# ==================== RATE LIMITING ====================

# In-memory rate limiter (per user_id)
rate_limit_store = defaultdict(list)

def check_rate_limit(user_id: str, limit: int = 5, window_seconds: int = 60) -> bool:
    """
    Check if user has exceeded rate limit.
    Args:
        user_id: User identifier
        limit: Max requests allowed in window
        window_seconds: Time window in seconds
    Returns:
        True if within limit, False if exceeded
    """
    now = time.time()
    cutoff = now - window_seconds
    
    # Remove old timestamps outside the window
    rate_limit_store[user_id] = [ts for ts in rate_limit_store[user_id] if ts > cutoff]
    
    # Check if limit exceeded
    if len(rate_limit_store[user_id]) >= limit:
        return False
    
    # Add current timestamp
    rate_limit_store[user_id].append(now)
    return True


def get_rate_limit_reset(user_id: str, window_seconds: int = 60) -> int:
    """Get seconds until rate limit resets for user"""
    if not rate_limit_store[user_id]:
        return 0
    oldest_timestamp = min(rate_limit_store[user_id])
    reset_time = oldest_timestamp + window_seconds
    return max(0, int(reset_time - time.time()))


# ==================== CONTENT MODERATION ====================

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
    
    import re
    
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


# ==================== ROUTES ====================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "RelayX Backend",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check(db: SupabaseDB = Depends(get_db), llm: LLMClient = Depends(get_llm_client)):
    """Comprehensive health check"""
    health_status = {
        "backend": "healthy",
        "database": "unknown",
        "llm": "unknown",
        "twilio": "configured" if twilio_client else "not configured"
    }
    
    # Check LLM
    try:
        llm_healthy = await llm.health_check()
        health_status["llm"] = "healthy" if llm_healthy else "unhealthy"
    except Exception as e:
        health_status["llm"] = f"error: {str(e)}"
    
    # Check database (simple check)
    try:
        await db.list_agents()
        health_status["database"] = "healthy"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
    
    return health_status


# ==================== AGENTS ====================

@app.post("/agents", response_model=dict)
async def create_agent(agent: AgentCreate, db: SupabaseDB = Depends(get_db)):
    """Create a new AI agent with prompt snapshot"""
    try:
        # Content moderation on prompt_text
        moderation = await moderate_content(agent.prompt_text)
        if moderation["flagged"]:
            logger.warning(f"Agent creation blocked - prompt flagged for: {moderation['categories']}")
            raise HTTPException(
                status_code=400,
                detail=f"Prompt contains disallowed content — edit required. Detected: {', '.join(moderation['categories'])}"
            )
        
        result = await db.create_agent(
            name=agent.name,
            prompt_text=agent.prompt_text,
            template_source=agent.template_source,
            voice_settings=agent.voice_settings,
            llm_model=agent.llm_model,
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
            is_active=agent.is_active
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents", response_model=List[dict])
async def list_agents(is_active: Optional[bool] = None, db: SupabaseDB = Depends(get_db)):
    """List all agents"""
    try:
        agents = await db.list_agents(is_active=is_active)
        return agents
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_id}", response_model=dict)
async def get_agent(agent_id: str, db: SupabaseDB = Depends(get_db)):
    """Get agent by ID"""
    try:
        agent = await db.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/agents/{agent_id}", response_model=dict)
@app.put("/agents/{agent_id}", response_model=dict)
async def update_agent(agent_id: str, updates: AgentUpdate, db: SupabaseDB = Depends(get_db)):
    """Update agent prompt and configuration"""
    try:
        # Filter out None values
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        # Content moderation if prompt_text is being updated
        if "prompt_text" in update_data and update_data["prompt_text"]:
            moderation = await moderate_content(update_data["prompt_text"])
            if moderation["flagged"]:
                logger.warning(f"Agent update blocked for {agent_id} - prompt flagged for: {moderation['categories']}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Prompt contains disallowed content — edit required. Detected: {', '.join(moderation['categories'])}"
                )
        
        result = await db.update_agent(agent_id, **update_data)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CALLS ====================

@app.post("/calls/outbound", response_model=CallResponse)
async def create_outbound_call(
    call_request: OutboundCallRequest,
    background_tasks: BackgroundTasks,
    db: SupabaseDB = Depends(get_db)
):
    """
    Initiate an outbound call
    
    This endpoint:
    1. Validates the agent exists
    2. Creates a call record in the database
    3. Triggers Twilio to call the number
    4. Returns the call record
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
        
        # Create call record with explicit direction
        call_record = await db.create_call(
            agent_id=call_request.agent_id,
            to_number=call_request.to_number,
            from_number=TWILIO_PHONE_NUMBER,
            direction="outbound",
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


async def initiate_twilio_call(call_id: str, to_number: str, db: SupabaseDB):
    """Background task to initiate Twilio call"""
    try:
        # Get ngrok URL from voice gateway
        import httpx
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


@app.get("/calls/{call_id}", response_model=dict)
async def get_call(call_id: str, db: SupabaseDB = Depends(get_db)):
    """Get call details by ID"""
    try:
        call = await db.get_call(call_id)
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        return call
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/calls", response_model=List[dict])
async def list_calls(
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: SupabaseDB = Depends(get_db)
):
    """List calls with optional filters"""
    try:
        calls = await db.list_calls(agent_id=agent_id, status=status, limit=limit)
        return calls
    except Exception as e:
        logger.error(f"Error listing calls: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/calls/{call_id}/transcripts", response_model=List[dict])
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


@app.get("/calls/{call_id}/analysis", response_model=dict)
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


class CallUpdate(BaseModel):
    status: Optional[str] = None


@app.patch("/calls/{call_id}")
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


@app.get("/calls/{call_id}/recording")
async def get_call_recording(call_id: str, db: SupabaseDB = Depends(get_db)):
    """
    Get recording metadata for a call
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


@app.get("/calls/{call_id}/recording/stream")
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
        import base64
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
            from fastapi.responses import StreamingResponse
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


# ==================== STARTUP ====================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting RelayX Backend...")
    
    # Test database connection
    try:
        db = get_db()
        agents = await db.list_agents()
        logger.info(f"Database connected. Found {len(agents)} agents.")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
    
    # Test LLM connection
    try:
        llm = get_llm_client()
        healthy = await llm.health_check()
        if healthy:
            models = await llm.list_models()
            logger.info(f"LLM connected. Available models: {models}")
        else:
            logger.warning("LLM health check failed")
    except Exception as e:
        logger.error(f"LLM connection failed: {e}")
    
    logger.info("Backend startup complete")


# ==================== TEMPLATES & PREVIEW API ====================

@app.get("/api/templates")
async def get_templates(category: Optional[str] = None, db: SupabaseDB = Depends(get_db)):
    """Get all starter templates"""
    try:
        templates = await db.list_templates(category=category)
        return templates
    except Exception as e:
        logger.error(f"Error fetching templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/templates")
async def create_template(
    template: TemplateCreate,
    db: SupabaseDB = Depends(get_db)
):
    """Create a new template (for 'Save as template' checkbox)"""
    try:
        # Content moderation
        moderation = await moderate_content(template.content)
        if moderation["flagged"]:
            raise HTTPException(
                status_code=400,
                detail=f"Prompt contains disallowed content — edit required. Detected: {', '.join(moderation['categories'])}"
            )
        
        result = await db.create_template(
            name=template.name,
            content=template.content,
            description=template.description,
            category=template.category,
            is_locked=False  # User templates are not locked
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/preview")
async def preview_prompt(
    request: PreviewRequest,
    llm: LLMClient = Depends(get_llm_client)
):
    """Preview a prompt with sample input (with moderation and INTERNAL_SAFETY)"""
    try:
        # Content moderation on prompt
        moderation = await moderate_content(request.prompt_text)
        if moderation["flagged"]:
            logger.warning(f"Preview blocked - prompt flagged for: {moderation['categories']}")
            raise HTTPException(
                status_code=400,
                detail=f"Prompt contains disallowed content — edit required. Detected: {', '.join(moderation['categories'])}"
            )
        
        # Add INTERNAL_SAFETY prefix (always prepended server-side)
        INTERNAL_SAFETY = """SYSTEM OVERRIDE (HIGHEST PRIORITY):
You must follow all safety guidelines. Refuse harmful, illegal, or abusive requests.
Never share private information. Stay professional and helpful."""
        
        full_prompt = f"{INTERNAL_SAFETY}\n\n{request.prompt_text}"
        
        # Generate preview response (limited tokens for cost control)
        messages = [{"role": "user", "content": request.sample_user_input}]
        response = await llm.generate_response(
            messages=messages,
            system_prompt=full_prompt,
            temperature=request.temperature,
            max_tokens=min(request.max_tokens, 150)  # Cap at 150 tokens for preview
        )
        
        return {
            "preview_response": response,
            "prompt_used": full_prompt,
            "tokens_used": "~" + str(min(request.max_tokens, 150))
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")


# ==================== KNOWLEDGE BASE ENDPOINTS ====================

class KnowledgeCreate(BaseModel):
    agent_id: str
    title: str
    content: str
    source_file: Optional[str] = None
    file_type: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


@app.get("/api/agents/{agent_id}/knowledge")
async def get_agent_knowledge(agent_id: str, db: SupabaseDB = Depends(get_db)):
    """Get all knowledge base entries for an agent"""
    try:
        knowledge = await db.get_agent_knowledge(agent_id)
        return knowledge
    except Exception as e:
        logger.error(f"Error fetching knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/knowledge")
async def add_knowledge(
    knowledge: KnowledgeCreate,
    db: SupabaseDB = Depends(get_db)
):
    """Add knowledge base entry"""
    try:
        result = await db.add_knowledge(
            agent_id=knowledge.agent_id,
            title=knowledge.title,
            content=knowledge.content,
            source_file=knowledge.source_file,
            file_type=knowledge.file_type,
            metadata=knowledge.metadata
        )
        return result
    except Exception as e:
        logger.error(f"Error adding knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/knowledge/{knowledge_id}")
async def delete_knowledge(knowledge_id: str, db: SupabaseDB = Depends(get_db)):
    """Delete knowledge entry"""
    try:
        success = await db.delete_knowledge(knowledge_id)
        if not success:
            raise HTTPException(status_code=404, detail="Knowledge entry not found")
        return {"message": "Knowledge deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/knowledge/upload")
async def upload_knowledge_file(
    agent_id: str = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    db: SupabaseDB = Depends(get_db)
):
    """Upload a file and extract text for knowledge base"""
    try:
        # Determine file type
        filename = file.filename
        file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
        
        # Read file content
        file_content = await file.read()
        
        # Extract text from file
        content = ""
        if file_ext == 'txt':
            content = file_content.decode('utf-8')
        elif file_ext == 'pdf':
            # TODO: Add PDF parsing (pypdf2 or similar)
            raise HTTPException(status_code=400, detail="PDF support coming soon")
        elif file_ext in ['csv', 'json']:
            content = file_content.decode('utf-8')
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_ext}")
        
        # Save to knowledge base
        result = await db.add_knowledge(
            agent_id=agent_id,
            title=title,
            content=content,
            source_file=filename,
            file_type=file_ext,
            metadata={"file_size": len(file_content)}
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
