"""
Redis Cache Client for RelayX
Provides fast in-memory caching for conversation context, agent configs, and responses
"""
from typing import Optional, Dict, Any, List
import json
import os
from loguru import logger
import redis.asyncio as redis


class CacheClient:
    """Redis-based caching client for performance optimization"""
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize Redis cache client
        
        Args:
            redis_url: Redis connection URL (defaults to REDIS_URL env var)
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.client: Optional[redis.Redis] = None
        self.enabled = True
        
        # Cache TTLs (in seconds)
        self.CONVERSATION_TTL = 3600  # 1 hour
        self.AGENT_CONFIG_TTL = 7200  # 2 hours
        self.RESPONSE_CACHE_TTL = 1800  # 30 minutes
        
        logger.info(f"Cache client initialized with Redis URL: {self.redis_url}")
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # Test connection
            await self.client.ping()
            logger.info("✅ Redis cache connected successfully")
        except Exception as e:
            logger.warning(f"⚠️ Redis unavailable, caching disabled: {e}")
            self.enabled = False
            self.client = None
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis cache disconnected")
    
    # ==================== CONVERSATION CONTEXT CACHING ====================
    
    async def cache_conversation_history(self, call_id: str, messages: List[Dict[str, str]]):
        """
        Cache conversation history for fast retrieval
        
        Args:
            call_id: Call identifier
            messages: List of conversation messages
        """
        if not self.enabled or not self.client:
            return
        
        try:
            key = f"conversation:{call_id}"
            value = json.dumps(messages)
            await self.client.setex(key, self.CONVERSATION_TTL, value)
            logger.debug(f"Cached conversation history for {call_id}: {len(messages)} messages")
        except Exception as e:
            logger.warning(f"Failed to cache conversation: {e}")
    
    async def get_conversation_history(self, call_id: str) -> Optional[List[Dict[str, str]]]:
        """
        Retrieve cached conversation history
        
        Returns:
            List of messages if cached, None otherwise
        """
        if not self.enabled or not self.client:
            return None
        
        try:
            key = f"conversation:{call_id}"
            value = await self.client.get(key)
            if value:
                messages = json.loads(value)
                logger.debug(f"Cache HIT: conversation:{call_id} ({len(messages)} messages)")
                return messages
            logger.debug(f"Cache MISS: conversation:{call_id}")
            return None
        except Exception as e:
            logger.warning(f"Failed to get cached conversation: {e}")
            return None
    
    # ==================== AGENT CONFIG CACHING ====================
    
    async def cache_agent_config(self, agent_id: str, config: Dict[str, Any]):
        """
        Cache agent configuration
        
        Args:
            agent_id: Agent identifier
            config: Agent configuration dict
        """
        if not self.enabled or not self.client:
            return
        
        try:
            key = f"agent:{agent_id}"
            value = json.dumps(config)
            await self.client.setex(key, self.AGENT_CONFIG_TTL, value)
            logger.debug(f"Cached agent config for {agent_id}")
        except Exception as e:
            logger.warning(f"Failed to cache agent config: {e}")
    
    async def get_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached agent configuration
        
        Returns:
            Agent config dict if cached, None otherwise
        """
        if not self.enabled or not self.client:
            return None
        
        try:
            key = f"agent:{agent_id}"
            value = await self.client.get(key)
            if value:
                config = json.loads(value)
                logger.debug(f"Cache HIT: agent:{agent_id}")
                return config
            logger.debug(f"Cache MISS: agent:{agent_id}")
            return None
        except Exception as e:
            logger.warning(f"Failed to get cached agent config: {e}")
            return None
    
    # ==================== RESPONSE CACHING ====================
    
    async def cache_response(self, prompt_hash: str, response: str):
        """
        Cache common responses to save LLM calls
        
        Args:
            prompt_hash: Hash of the prompt (use hashlib.md5)
            response: The LLM response to cache
        """
        if not self.enabled or not self.client:
            return
        
        try:
            key = f"response:{prompt_hash}"
            await self.client.setex(key, self.RESPONSE_CACHE_TTL, response)
            logger.debug(f"Cached response for prompt hash {prompt_hash[:8]}...")
        except Exception as e:
            logger.warning(f"Failed to cache response: {e}")
    
    async def get_cached_response(self, prompt_hash: str) -> Optional[str]:
        """
        Retrieve cached response
        
        Returns:
            Cached response if exists, None otherwise
        """
        if not self.enabled or not self.client:
            return None
        
        try:
            key = f"response:{prompt_hash}"
            value = await self.client.get(key)
            if value:
                logger.debug(f"Cache HIT: response:{prompt_hash[:8]}... (saved LLM call!)")
                return value
            return None
        except Exception as e:
            logger.warning(f"Failed to get cached response: {e}")
            return None
    
    # ==================== STATISTICS ====================
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.enabled or not self.client:
            return {"enabled": False}
        
        try:
            info = await self.client.info("stats")
            return {
                "enabled": True,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": info.get("keyspace_hits", 0) / max(1, info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0)) * 100
            }
        except Exception as e:
            logger.warning(f"Failed to get cache stats: {e}")
            return {"enabled": True, "error": str(e)}


# Global cache client instance
_cache_client: Optional[CacheClient] = None


def get_cache_client() -> CacheClient:
    """Get or create cache client singleton"""
    global _cache_client
    if _cache_client is None:
        _cache_client = CacheClient()
    return _cache_client
