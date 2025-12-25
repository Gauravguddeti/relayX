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

# Import authentication
from auth import get_current_user_id
import auth_routes
import admin_routes
import admin_auth
import cal_routes
import campaign_routes

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

# Include authentication routes
auth_routes.init_supabase(None)  # Will be set after db initialization
app.include_router(auth_routes.router)

# Include admin routes
app.include_router(admin_routes.router)

# Include Cal.com routes
app.include_router(cal_routes.router)

# Include campaign routes
app.include_router(campaign_routes.router)

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
    max_tokens: int = Field(default=100, ge=50, le=500)
    is_active: bool = Field(default=True)
    user_id: Optional[str] = Field(None, description="User/client ID this agent belongs to")


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
    max_tokens: int = Field(default=100, ge=50, le=300)


# ==================== ADMIN AUTH ====================

from pydantic import BaseModel as AuthBaseModel

class AdminLoginRequest(AuthBaseModel):
    username: str
    password: str

class AdminLoginResponse(AuthBaseModel):
    success: bool
    token: Optional[str] = None
    message: str

@app.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest):
    """Admin login endpoint with double-hashed password verification"""
    try:
        if request.username == admin_auth.ADMIN_USERNAME:
            if admin_auth.verify_password_double(request.password, admin_auth.ADMIN_PASSWORD_HASH):
                token = admin_auth.create_admin_session(request.username)
                return AdminLoginResponse(
                    success=True,
                    token=token,
                    message="Login successful"
                )
        
        return AdminLoginResponse(
            success=False,
            message="Invalid credentials"
        )
    except Exception as e:
        logger.error(f"Admin login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/admin/logout")
async def admin_logout(session: dict = Depends(admin_auth.verify_admin_token)):
    """Admin logout endpoint"""
    # Token is automatically verified by dependency
    return {"success": True, "message": "Logged out successfully"}

@app.get("/admin/verify")
async def verify_admin(session: dict = Depends(admin_auth.verify_admin_token)):
    """Verify admin session"""
    return {"success": True, "username": session["username"]}

# ==================== DASHBOARD ====================

@app.get("/")
async def root_redirect():
    """Redirect root to admin login"""
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "admin-login.html"))

@app.get("/admin")
async def admin_dashboard():
    """Serve the admin dashboard"""
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "admin.html"))


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


@app.get("/dashboard/stats")
async def get_dashboard_stats(
    user_id: str = Depends(get_current_user_id),
    db: SupabaseDB = Depends(get_db)
):
    """Get aggregated dashboard statistics for the current user"""
    try:
        # Fetch all user's calls with analysis in a single query
        response = db.client.table("calls")\
            .select("id, status, created_at, call_analysis")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(100)\
            .execute()
        
        calls = response.data if response.data else []
        
        # Calculate stats
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_calls = 0
        interested_count = 0
        not_interested_count = 0
        confidence_sum = 0.0
        confidence_count = 0
        
        for call in calls:
            # Count today's calls
            if call.get("created_at"):
                call_date = datetime.fromisoformat(call["created_at"].replace("Z", "+00:00"))
                if call_date >= today:
                    today_calls += 1
            
            # Process analysis data
            if call.get("status") == "completed" and call.get("call_analysis"):
                analysis = call["call_analysis"]
                
                # Check outcome
                outcome = analysis.get("outcome", "").lower()
                if "interested" in outcome and "not" not in outcome:
                    interested_count += 1
                elif "not interested" in outcome:
                    not_interested_count += 1
                
                # Add confidence score
                if analysis.get("confidence_score"):
                    confidence_sum += float(analysis["confidence_score"])
                    confidence_count += 1
        
        return {
            "totalCalls": len(calls),
            "interestedCalls": interested_count,
            "notInterestedCalls": not_interested_count,
            "avgConfidence": confidence_sum / confidence_count if confidence_count > 0 else 0,
            "todayCalls": today_calls
        }
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return {
            "totalCalls": 0,
            "interestedCalls": 0,
            "notInterestedCalls": 0,
            "avgConfidence": 0,
            "todayCalls": 0
        }


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
        log_file = "logs/voice_gateway.log"
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                # Read last 50 lines
                lines = f.readlines()
                logs = ''.join(lines[-50:])
        else:
            logs = "Voice gateway log file not found"
        return {"logs": logs, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"logs": f"Error fetching logs: {str(e)}", "timestamp": datetime.now().isoformat()}


@app.get("/api/logs/backend")
async def get_backend_logs():
    """Get recent backend logs"""
    try:
        # Try multiple possible log locations
        log_paths = ["logs/backend.log", "../logs/backend.log", "backend/logs/backend.log"]
        logs = ""
        
        for log_file in log_paths:
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    logs = ''.join(lines[-100:])
                break
        
        if not logs:
            logs = "Backend log file not found. Checked: " + ", ".join(log_paths)
            
        return {"logs": logs, "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        logger.error(f"Error fetching backend logs: {e}")
        return {"logs": f"Error fetching logs: {str(e)}", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/logs/voice-gateway")
async def get_voice_gateway_logs():
    """Get recent voice gateway logs"""
    try:
        # Try multiple possible log locations
        log_paths = [
            "logs/voice_gateway.log",
            "../logs/voice_gateway.log",
            "voice_gateway/logs/voice_gateway.log",
            "../voice_gateway/logs/voice_gateway.log"
        ]
        logs = ""
        
        for log_file in log_paths:
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    logs = ''.join(lines[-100:])
                break
        
        if not logs:
            logs = "Voice gateway log file not found. Checked: " + ", ".join(log_paths)
            
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


@app.post("/api/demo-call")
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
            is_active=agent.is_active,
            user_id=agent.user_id
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents", response_model=List[dict])
async def list_agents(
    is_active: Optional[bool] = None,
    user_id: Optional[str] = None,  # If provided, filter by user; if None, show all (admin mode)
    db: SupabaseDB = Depends(get_db)
):
    """List agents - filtered by user_id or all agents for admin"""
    try:
        # Build query
        query = db.client.table("agents").select("*")
        
        # Filter by user_id if provided
        if user_id:
            query = query.eq("user_id", user_id)
        
        # Filter by active status if specified
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        result = query.execute()
        agents = result.data or []
        
        # Fetch user info for each agent (since we can't join)
        if agents:
            user_ids = list(set(a.get("user_id") for a in agents if a.get("user_id")))
            if user_ids:
                users_result = db.client.table("users").select("id,name,email,company").in_("id", user_ids).execute()
                users_map = {u["id"]: u for u in (users_result.data or [])}
                
                # Add user info to agents
                for agent in agents:
                    uid = agent.get("user_id")
                    if uid and uid in users_map:
                        agent["user_name"] = users_map[uid].get("name")
                        agent["user_email"] = users_map[uid].get("email")
                        agent["user_company"] = users_map[uid].get("company")
        
        return agents
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_id}", response_model=dict)
async def get_agent(
    agent_id: str,
    user_id: Optional[str] = None,  # Optional user_id filter for security
    db: SupabaseDB = Depends(get_db)
):
    """Get agent by ID"""
    try:
        query = db.client.table("agents").select("*").eq("id", agent_id)
        
        # Filter by user_id if provided (non-admin mode)
        if user_id:
            query = query.eq("user_id", user_id)
        
        result = query.execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent = result.data[0]
        
        # Fetch user info
        if agent.get("user_id"):
            user_result = db.client.table("users").select("name,email,company").eq("id", agent["user_id"]).execute()
            if user_result.data:
                agent["user_name"] = user_result.data[0].get("name")
                agent["user_email"] = user_result.data[0].get("email")
                agent["user_company"] = user_result.data[0].get("company")
        
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/agents/{agent_id}", response_model=dict)
@app.put("/agents/{agent_id}", response_model=dict)
async def update_agent(
    agent_id: str,
    updates: AgentUpdate,
    user_id: Optional[str] = None,  # Optional user_id for security (admins can skip)
    db: SupabaseDB = Depends(get_db)
):
    """Update agent prompt and configuration"""
    try:
        # Verify agent exists (and optionally belongs to user)
        query = db.client.table("agents").select("id,user_id").eq("id", agent_id)
        if user_id:
            query = query.eq("user_id", user_id)
        
        agent_result = query.execute()
        if not agent_result.data:
            raise HTTPException(status_code=404, detail="Agent not found or access denied")
        
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


@app.get("/calls", response_model=List[dict])
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
@app.head("/calls/{call_id}/recording")
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
        
        # Initialize auth routes with supabase client
        auth_routes.init_supabase(db.client)
        logger.info("Auth routes initialized")
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
    
    # Start campaign scheduler
    try:
        from scheduler import start_scheduler
        start_scheduler()
        logger.info("Campaign scheduler started")
    except Exception as e:
        logger.error(f"Failed to start campaign scheduler: {e}")
    
    logger.info("Backend startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down RelayX Backend...")
    
    try:
        from scheduler import stop_scheduler
        stop_scheduler()
        logger.info("Campaign scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")


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
    source_url: Optional[str] = None  # New: URL source
    file_type: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class KnowledgeFromURL(BaseModel):
    agent_id: str
    url: str
    custom_title: Optional[str] = None  # Optional custom title override


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
            source_url=knowledge.source_url,
            file_type=knowledge.file_type,
            metadata=knowledge.metadata
        )
        return result
    except Exception as e:
        logger.error(f"Error adding knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/knowledge/from-url")
async def add_knowledge_from_url(
    data: KnowledgeFromURL,
    db: SupabaseDB = Depends(get_db)
):
    """
    Scrape URL and add to knowledge base
    
    This endpoint:
    1. Scrapes the provided URL
    2. Extracts clean text content
    3. Adds it to the agent's knowledge base
    """
    try:
        from shared.url_scraper import scrape_url_for_knowledge
        
        logger.info(f"Scraping URL for agent {data.agent_id}: {data.url}")
        
        # Scrape the URL
        success, title, content, metadata = await scrape_url_for_knowledge(data.url)
        
        if not success:
            error_msg = metadata.get("error", "Failed to scrape URL")
            raise HTTPException(status_code=400, detail=f"Scraping failed: {error_msg}")
        
        # Use custom title if provided
        final_title = data.custom_title or title
        
        # Add URL to metadata
        metadata["scraped_url"] = data.url
        
        # Add to knowledge base
        result = await db.add_knowledge(
            agent_id=data.agent_id,
            title=final_title,
            content=content,
            source_url=data.url,
            file_type="url",
            metadata=metadata
        )
        
        logger.info(f"✅ Added knowledge from URL: {data.url} ({metadata.get('word_count', 0)} words)")
        
        return {
            "success": True,
            "knowledge": result,
            "scraped_data": {
                "url": data.url,
                "title": title,
                "word_count": metadata.get("word_count", 0),
                "domain": metadata.get("domain", "")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scraping URL {data.url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge/preview-url")
async def preview_url(url: str):
    """
    Preview URL content before adding to knowledge base
    Returns: title, content preview, word count, domain
    """
    logger.info(f"Preview URL request: {url}")
    try:
        from shared.url_scraper import scrape_url_for_knowledge
        
        logger.info(f"Starting scrape for: {url}")
        success, title, content, metadata = await scrape_url_for_knowledge(url)
        
        logger.info(f"Scrape result - Success: {success}, Error: {metadata.get('error', 'None')}")
        
        if not success:
            error_msg = metadata.get("error", "Failed to scrape URL")
            logger.error(f"Scrape failed: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Return preview (first 500 chars)
        content_preview = content[:500] + "..." if len(content) > 500 else content
        
        logger.info(f"Preview success - Title: {title}, Words: {metadata.get('word_count', 0)}")
        
        return {
            "success": True,
            "url": url,
            "title": title,
            "content_preview": content_preview,
            "word_count": metadata.get("word_count", 0),
            "domain": metadata.get("domain", ""),
            "content_length": metadata.get("content_length", 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing URL {url}: {e}")
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
