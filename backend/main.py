"""
FastAPI Backend for RelayX AI Caller
Handles API endpoints for agents, calls, and Twilio webhooks
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import sys
import os
from loguru import logger

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from shared.database import get_db, SupabaseDB
from shared.llm_client import get_llm_client, LLMClient
from twilio.rest import Client as TwilioClient
from dotenv import load_dotenv
import subprocess

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
    system_prompt: str = Field(..., description="System prompt for the AI agent")
    voice_settings: dict = Field(default_factory=dict, description="TTS voice settings")
    llm_model: str = Field(default="llama3:8b", description="LLM model to use")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=150, ge=50, le=500)
    is_active: bool = Field(default=True)


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    system_prompt: Optional[str] = None
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


# ==================== DASHBOARD ====================

@app.get("/dashboard")
async def dashboard():
    """Serve the web dashboard"""
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "dashboard.html"))


@app.get("/stats")
async def get_stats(db: SupabaseDB = Depends(get_db)):
    """Get system statistics for dashboard"""
    try:
        agents = await db.list_agents()
        calls = await db.list_calls()
        
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
    """Get recent voice gateway logs"""
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
    """Create a new AI agent"""
    try:
        result = await db.create_agent(
            name=agent.name,
            system_prompt=agent.system_prompt,
            voice_settings=agent.voice_settings,
            llm_model=agent.llm_model,
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
            is_active=agent.is_active
        )
        return result
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
async def update_agent(agent_id: str, updates: AgentUpdate, db: SupabaseDB = Depends(get_db)):
    """Update agent configuration"""
    try:
        # Filter out None values
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No updates provided")
        
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
        
        # Create call record
        call_record = await db.create_call(
            agent_id=call_request.agent_id,
            to_number=call_request.to_number,
            from_number=TWILIO_PHONE_NUMBER,
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
        
        # Make the call
        call = twilio_client.calls.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            url=twiml_url,
            status_callback=f"{gateway_url}/callbacks/status/{call_id}",
            status_callback_event=["initiated", "ringing", "answered", "completed"],
            status_callback_method="POST",
            method="POST"  # Use POST for TwiML URL
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
