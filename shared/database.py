"""
Supabase Database Client
Handles all database operations using Supabase Python SDK
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from supabase import create_client, Client
from loguru import logger
import os


class SupabaseDB:
    """Wrapper for Supabase database operations"""
    
    def __init__(self, url: str = None, key: str = None):
        self.url = url or os.getenv("SUPABASE_URL")
        self.key = key or os.getenv("SUPABASE_ANON_KEY")
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
        
        self.client: Client = create_client(self.url, self.key)
        logger.info(f"Supabase client initialized for {self.url}")
    
    # ==================== AGENTS ====================
    
    async def create_agent(self, name: str, prompt_text: str, template_source: str = None, **kwargs) -> Dict[str, Any]:
        """Create a new AI agent with prompt snapshot"""
        try:
            data = {
                "name": name,
                "prompt_text": prompt_text,
                "template_source": template_source,
                **kwargs
            }
            result = self.client.table("agents").insert(data).execute()
            logger.info(f"Created agent: {name}")
            return result.data[0]
        except Exception as e:
            logger.error(f"Error creating agent: {e}")
            raise
    
    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID"""
        try:
            result = self.client.table("agents").select("*").eq("id", agent_id).execute()
            if not result.data:
                return None
            
            agent = result.data[0]
            # prompt_text is already the snapshot, use it directly
            agent["resolved_system_prompt"] = agent.get("prompt_text") or "You are a helpful AI assistant."
            
            return agent
        except Exception as e:
            logger.error(f"Error fetching agent {agent_id}: {e}")
            raise
    
    async def list_agents(self, is_active: bool = True) -> List[Dict[str, Any]]:
        """List all agents"""
        try:
            query = self.client.table("agents").select("*")
            if is_active is not None:
                query = query.eq("is_active", is_active)
            result = query.execute()
            return result.data
        except Exception as e:
            logger.error(f"Error listing agents: {e}")
            raise
    
    async def update_agent(self, agent_id: str, **kwargs) -> Dict[str, Any]:
        """Update agent configuration"""
        try:
            result = self.client.table("agents").update(kwargs).eq("id", agent_id).execute()
            logger.info(f"Updated agent {agent_id}")
            return result.data[0]
        except Exception as e:
            logger.error(f"Error updating agent {agent_id}: {e}")
            raise
    
    # ==================== CALLS ====================
    
    async def create_call(
        self, 
        agent_id: str, 
        to_number: str, 
        from_number: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new call record"""
        try:
            data = {
                "agent_id": agent_id,
                "to_number": to_number,
                "from_number": from_number,
                "status": "initiated",
                **kwargs
            }
            result = self.client.table("calls").insert(data).execute()
            logger.info(f"Created call record: {result.data[0]['id']}")
            return result.data[0]
        except Exception as e:
            logger.error(f"Error creating call: {e}")
            raise
    
    async def get_call(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get call by ID"""
        try:
            result = self.client.table("calls").select("*, agents(*)").eq("id", call_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching call {call_id}: {e}")
            raise
    
    async def update_call(self, call_id: str, **kwargs) -> Dict[str, Any]:
        """Update call record"""
        try:
            # Convert datetime objects to ISO strings for JSON serialization
            from datetime import datetime
            for key, value in kwargs.items():
                if isinstance(value, datetime):
                    kwargs[key] = value.isoformat()
            
            result = self.client.table("calls").update(kwargs).eq("id", call_id).execute()
            logger.info(f"Updated call {call_id}: {list(kwargs.keys())}")
            return result.data[0]
        except Exception as e:
            logger.error(f"Error updating call {call_id}: {e}")
            raise
    
    async def update_call_by_sid(self, twilio_call_sid: str, **kwargs) -> Dict[str, Any]:
        """Update call by Twilio SID"""
        try:
            result = self.client.table("calls").update(kwargs).eq("twilio_call_sid", twilio_call_sid).execute()
            if result.data:
                logger.info(f"Updated call by SID {twilio_call_sid}: {kwargs}")
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"Error updating call by SID {twilio_call_sid}: {e}")
            raise
    
    async def list_calls(
        self, 
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List calls with optional filters"""
        try:
            query = self.client.table("calls").select("*, agents(name)")
            
            if agent_id:
                query = query.eq("agent_id", agent_id)
            if status:
                query = query.eq("status", status)
            
            query = query.order("created_at", desc=True).limit(limit)
            result = query.execute()
            
            # Flatten agent name for easier access
            calls = []
            for call in result.data:
                call_data = call.copy()
                if call_data.get('agents'):
                    call_data['agent_name'] = call_data['agents'].get('name')
                    del call_data['agents']
                calls.append(call_data)
            
            return calls
        except Exception as e:
            logger.error(f"Error listing calls: {e}")
            raise
    
    # ==================== TRANSCRIPT METHODS ====================
    
    async def save_transcript(
        self,
        call_id: str,
        speaker: str,
        text: str,
        audio_duration: Optional[float] = None,
        confidence_score: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Save a conversation turn to transcripts table"""
        try:
            data = {
                "call_id": call_id,
                "speaker": speaker,  # 'user' or 'agent'
                "text": text,
                "audio_duration": audio_duration,
                "confidence_score": confidence_score,
                "metadata": metadata or {}
            }
            result = self.client.table("transcripts").insert(data).execute()
            logger.info(f"Saved transcript for call {call_id}: {speaker}")
            return result.data[0]
        except Exception as e:
            logger.error(f"Error saving transcript: {e}")
            raise
    
    async def get_transcripts(self, call_id: str) -> List[Dict[str, Any]]:
        """Get all transcripts for a call"""
        try:
            result = self.client.table("transcripts") \
                .select("*") \
                .eq("call_id", call_id) \
                .order("timestamp") \
                .execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching transcripts for call {call_id}: {e}")
            raise
    
    async def save_call_analysis(
        self,
        call_id: str,
        summary: str,
        key_points: List[str],
        user_sentiment: str,
        outcome: str,
        next_action: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Save post-call analysis"""
        try:
            data = {
                "call_id": call_id,
                "summary": summary,
                "key_points": key_points,
                "user_sentiment": user_sentiment,
                "outcome": outcome,
                "next_action": next_action,
                "metadata": metadata or {}
            }
            # Upsert (insert or update if exists)
            result = self.client.table("call_analysis").upsert(data).execute()
            logger.info(f"Saved call analysis for call {call_id}: {outcome}")
            return result.data[0]
        except Exception as e:
            logger.error(f"Error saving call analysis: {e}")
            raise
    
    async def get_call_analysis(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get call analysis"""
        try:
            result = self.client.table("call_analysis") \
                .select("*") \
                .eq("call_id", call_id) \
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching call analysis for call {call_id}: {e}")
            raise
            query = self.client.table("calls").select("*, agents(name)")
            
            if agent_id:
                query = query.eq("agent_id", agent_id)
            if status:
                query = query.eq("status", status)
            
            result = query.order("created_at", desc=True).limit(limit).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error listing calls: {e}")
            raise
    
    # ==================== TRANSCRIPTS ====================
    
    async def add_transcript(
        self,
        call_id: str,
        speaker: str,  # 'user' or 'agent'
        text: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Add a transcript entry"""
        try:
            data = {
                "call_id": call_id,
                "speaker": speaker,
                "text": text,
                **kwargs
            }
            result = self.client.table("transcripts").insert(data).execute()
            return result.data[0]
        except Exception as e:
            logger.error(f"Error adding transcript for call {call_id}: {e}")
            raise
    
    async def get_transcripts(self, call_id: str) -> List[Dict[str, Any]]:
        """Get all transcripts for a call"""
        try:
            result = self.client.table("transcripts").select("*").eq("call_id", call_id).order("timestamp").execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching transcripts for call {call_id}: {e}")
            raise
    
    async def get_conversation_history(self, call_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation history formatted for LLM"""
        try:
            result = self.client.table("transcripts")\
                .select("speaker, text")\
                .eq("call_id", call_id)\
                .order("timestamp", desc=True)\
                .limit(limit)\
                .execute()
            
            # Reverse to get chronological order and format
            history = []
            for item in reversed(result.data):
                role = "assistant" if item["speaker"] == "agent" else "user"
                history.append({"role": role, "content": item["text"]})
            
            return history
        except Exception as e:
            logger.error(f"Error fetching conversation history for call {call_id}: {e}")
            raise
    
    # ==================== TEMPLATES ====================
    
    async def create_template(
        self,
        name: str,
        content: str,
        description: str = None,
        category: str = "custom",
        is_locked: bool = False
    ) -> Dict[str, Any]:
        """Create a new template (starter blueprint)"""
        try:
            data = {
                "name": name,
                "content": content,
                "description": description,
                "category": category,
                "is_locked": is_locked
            }
            result = self.client.table("templates").insert(data).execute()
            logger.info(f"Created template: {name}")
            return result.data[0]
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            raise
    
    async def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template by ID"""
        try:
            result = self.client.table("templates").select("*").eq("id", template_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching template {template_id}: {e}")
            raise
    
    async def list_templates(self, category: str = None) -> List[Dict[str, Any]]:
        """List all templates (starter blueprints)"""
        try:
            query = self.client.table("templates").select("*")
            if category:
                query = query.eq("category", category)
            result = query.order("name").execute()
            return result.data
        except Exception as e:
            logger.error(f"Error listing templates: {e}")
            raise
    
    async def delete_template(self, template_id: str) -> bool:
        """Delete template (only if not locked)"""
        try:
            self.client.table("templates").delete().eq("id", template_id).eq("is_locked", False).execute()
            logger.info(f"Deleted template {template_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting template {template_id}: {e}")
            raise
    
    # ==================== CALL ANALYSIS (Future) ====================
    
    async def save_call_analysis(
        self,
        call_id: str,
        summary: str,
        key_points: List[str],
        user_sentiment: str,
        outcome: str,
        next_action: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Save post-call analysis"""
        try:
            data = {
                "call_id": call_id,
                "summary": summary,
                "key_points": key_points,
                "user_sentiment": user_sentiment,
                "outcome": outcome,
                "next_action": next_action,
                **kwargs
            }
            result = self.client.table("call_analysis").insert(data).execute()
            logger.info(f"Saved analysis for call {call_id}")
            return result.data[0]
        except Exception as e:
            logger.error(f"Error saving call analysis for {call_id}: {e}")
            raise
    
    async def get_call_analysis(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get call analysis"""
        try:
            result = self.client.table("call_analysis").select("*").eq("call_id", call_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching call analysis for {call_id}: {e}")
            raise


# Global instance
    # ==================== KNOWLEDGE BASE ====================
    
    async def add_knowledge(self, agent_id: str, title: str, content: str, 
                           source_file: str = None, source_url: str = None,
                           file_type: str = None, metadata: dict = None) -> Dict[str, Any]:
        """Add knowledge base entry for an agent"""
        try:
            data = {
                "agent_id": agent_id,
                "title": title,
                "content": content,
                "source_file": source_file,
                "source_url": source_url,
                "file_type": file_type,
                "metadata": metadata or {},
                "is_active": True
            }
            result = self.client.table("knowledge_base").insert(data).execute()
            
            source_info = source_url or source_file or "manual entry"
            logger.info(f"Added knowledge entry: {title} from {source_info} for agent {agent_id}")
            return result.data[0]
        except Exception as e:
            logger.error(f"Error adding knowledge: {e}")
            raise
    
    async def get_agent_knowledge(self, agent_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all knowledge entries for an agent"""
        try:
            query = self.client.table("knowledge_base").select("*").eq("agent_id", agent_id)
            if active_only:
                query = query.eq("is_active", True)
            result = query.order("created_at", desc=True).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching knowledge: {e}")
            return []
    
    async def search_knowledge(self, agent_id: str, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Search knowledge base using full-text search"""
        try:
            # Use PostgreSQL full-text search (without config param for SDK compatibility)
            result = self.client.table("knowledge_base")\
                .select("*")\
                .eq("agent_id", agent_id)\
                .eq("is_active", True)\
                .text_search("content", query)\
                .limit(limit)\
                .execute()
            
            if result.data:
                return result.data
            
            # If no results from text search, try ILIKE fallback
            logger.info(f"No text search results, trying keyword match for: {query}")
            result = self.client.table("knowledge_base")\
                .select("*")\
                .eq("agent_id", agent_id)\
                .eq("is_active", True)\
                .ilike("content", f"%{query}%")\
                .limit(limit)\
                .execute()
            return result.data
            
        except Exception as e:
            logger.warning(f"Search failed, using fallback: {e}")
            # Fallback: simple keyword match
            try:
                result = self.client.table("knowledge_base")\
                    .select("*")\
                    .eq("agent_id", agent_id)\
                    .eq("is_active", True)\
                    .ilike("content", f"%{query}%")\
                    .limit(limit)\
                    .execute()
                return result.data
            except Exception as e2:
                logger.error(f"Fallback search also failed: {e2}")
                return []
    
    async def delete_knowledge(self, knowledge_id: str) -> bool:
        """Delete a knowledge entry"""
        try:
            self.client.table("knowledge_base").delete().eq("id", knowledge_id).execute()
            logger.info(f"Deleted knowledge entry: {knowledge_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting knowledge: {e}")
            return False
    
    async def update_knowledge(self, knowledge_id: str, **kwargs) -> Dict[str, Any]:
        """Update knowledge entry"""
        try:
            result = self.client.table("knowledge_base")\
                .update(kwargs)\
                .eq("id", knowledge_id)\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error updating knowledge: {e}")
            raise


db = None

def get_db() -> SupabaseDB:
    """Get or create global database instance"""
    global db
    if db is None:
        db = SupabaseDB()
    return db
