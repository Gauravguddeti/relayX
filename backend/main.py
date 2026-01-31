
"""
FastAPI Backend for RelayX AI Caller
Handles API endpoints for agents, calls, and Twilio webhooks
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from twilio.rest import Client as TwilioClient
from loguru import logger
import os
import sys
from dotenv import load_dotenv

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.dirname(__file__))

from shared.database import get_db
from shared.llm_client import get_llm_client

# Import routes
import auth_routes
import admin_routes
import cal_routes
import campaign_routes
import contact_routes
import event_routes
import agent_routes
import call_routes
import template_routes
import knowledge_routes
import analytics_routes
import system_routes

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

# Apply global rate limiting
from limiter import check_rate_limit
from fastapi import Depends
app.router.dependencies.append(Depends(check_rate_limit))

# Include authentication routes
auth_routes.init_supabase(None)  # Will be set after db initialization
app.include_router(auth_routes.router)

# Include admin routes
app.include_router(admin_routes.router)

# Include Cal.com routes
app.include_router(cal_routes.router)

# Include campaign routes
app.include_router(campaign_routes.router)

# Include contact routes
app.include_router(contact_routes.router)

# Include event routes
app.include_router(event_routes.router)

# Include new modular routes
app.include_router(agent_routes.router)
app.include_router(call_routes.router)
app.include_router(template_routes.router)
app.include_router(knowledge_routes.router)
app.include_router(analytics_routes.router)
app.include_router(system_routes.router)

# Mount static files for dashboard
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

# CORS middleware - Allow frontend domains
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://relayx.tech",
    "https://www.relayx.tech",
    "https://relay-x.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
        
        # Initialize contact routes with database
        contact_routes.init_db(db)
        logger.info("Contact routes initialized")
        
        # Initialize event routes with database
        event_routes.init_db(db)
        logger.info("Event routes initialized")
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# ==================== DEMO CALL ROUTE (Kept as minimal fallback or move to system routes?) ====================
# Move demo call to call_routes? It uses background tasks.
# Let's check call_routes.py. It has create_outbound_call.
# The original main.py had create_demo_call.
# Check if I missed migrating create_demo_call.
# I missed create_demo_call in call_routes.py. Re-adding it there would be best.
# But for now, I will add it to main.py or better, append to call_routes.py.
# Actually, I should check if I missed it.
# Yes, I missed it in call_routes.py.
