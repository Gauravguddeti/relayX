from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from loguru import logger
from shared.database import get_db, SupabaseDB
from moderation import moderate_content

router = APIRouter()

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

# ==================== ROUTES ====================

@router.post("/agents", response_model=dict)
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


@router.get("/agents", response_model=List[dict])
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


@router.get("/agents/{agent_id}", response_model=dict)
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


@router.patch("/agents/{agent_id}", response_model=dict)
@router.put("/agents/{agent_id}", response_model=dict)
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
