"""
Redis Cache Client for RelayX
<<<<<<< HEAD
Provides fast in-memory caching for conversation context, agent configs, and responses
"""
=======
Handles conversation context caching and LLM response caching
"""
import redis.asyncio as redis
>>>>>>> 848cd500ec5fb6f0c0e50fd188bf8819910cd701
from typing import Optional, Dict, Any, List
import json
import os
from loguru import logger
<<<<<<< HEAD
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
=======
import hashlib


class CacheClient:
    """Redis-based caching for conversation context and LLM responses"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.client: Optional[redis.Redis] = None
        self.enabled = False
        
    async def connect(self):
        """Initialize Redis connection"""
        try:
            self.client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            await self.client.ping()
            self.enabled = True
            logger.info(f"✅ Redis cache connected: {self.redis_url}")
        except Exception as e:
            logger.warning(f"Redis cache unavailable (continuing without cache): {e}")
            self.enabled = False
    
    async def close(self):
>>>>>>> 848cd500ec5fb6f0c0e50fd188bf8819910cd701
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis cache disconnected")
    
    # ==================== CONVERSATION CONTEXT CACHING ====================
    
<<<<<<< HEAD
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
=======
    async def save_conversation_context(
        self, 
        call_id: str, 
        messages: List[Dict[str, str]], 
        ttl: int = 3600
    ) -> bool:
        """
        Save conversation messages for a call
        TTL: 1 hour default (calls don't last that long, but good for debugging)
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            key = f"conv:{call_id}"
            value = json.dumps(messages)
            await self.client.setex(key, ttl, value)
            logger.debug(f"💾 Cached conversation: {call_id} ({len(messages)} messages)")
            return True
        except Exception as e:
            logger.debug(f"Cache save failed: {e}")
            return False
    
    async def get_conversation_context(self, call_id: str) -> Optional[List[Dict[str, str]]]:
        """Retrieve cached conversation messages"""
>>>>>>> 848cd500ec5fb6f0c0e50fd188bf8819910cd701
        if not self.enabled or not self.client:
            return None
        
        try:
<<<<<<< HEAD
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
=======
            key = f"conv:{call_id}"
            data = await self.client.get(key)
            if data:
                messages = json.loads(data)
                logger.debug(f"📥 Retrieved cached conversation: {call_id} ({len(messages)} messages)")
                return messages
            return None
        except Exception as e:
            logger.debug(f"Cache retrieval failed: {e}")
            return None
    
    async def append_message(
        self, 
        call_id: str, 
        message: Dict[str, str], 
        ttl: int = 3600
    ) -> bool:
        """Append a message to existing conversation context"""
        messages = await self.get_conversation_context(call_id) or []
        messages.append(message)
        return await self.save_conversation_context(call_id, messages, ttl)
    
    # ==================== LLM RESPONSE CACHING ====================
    
    def _hash_prompt(self, prompt: str, system_prompt: str = "") -> str:
        """Generate cache key from prompt"""
        combined = f"{system_prompt}||{prompt}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    async def cache_llm_response(
        self, 
        prompt: str, 
        system_prompt: str, 
        response: str, 
        ttl: int = 86400
    ) -> bool:
        """
        Cache LLM response for identical prompts
        TTL: 24 hours (common greetings/responses can be reused)
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            hash_key = self._hash_prompt(prompt, system_prompt)
            key = f"llm:{hash_key}"
            await self.client.setex(key, ttl, response)
            logger.debug(f"💾 Cached LLM response: {hash_key}")
            return True
        except Exception as e:
            logger.debug(f"Cache save failed: {e}")
            return False
    
    async def get_cached_llm_response(
        self, 
        prompt: str, 
        system_prompt: str = ""
    ) -> Optional[str]:
        """Retrieve cached LLM response"""
        if not self.enabled or not self.client:
            return None
        
        try:
            hash_key = self._hash_prompt(prompt, system_prompt)
            key = f"llm:{hash_key}"
            response = await self.client.get(key)
            if response:
                logger.debug(f"⚡ Cache HIT for LLM: {hash_key}")
                return response
            logger.debug(f"Cache MISS for LLM: {hash_key}")
            return None
        except Exception as e:
            logger.debug(f"Cache retrieval failed: {e}")
>>>>>>> 848cd500ec5fb6f0c0e50fd188bf8819910cd701
            return None
    
    # ==================== AGENT CONFIG CACHING ====================
    
<<<<<<< HEAD
    async def cache_agent_config(self, agent_id: str, config: Dict[str, Any]):
        """
        Cache agent configuration
        
        Args:
            agent_id: Agent identifier
            config: Agent configuration dict
        """
        if not self.enabled or not self.client:
            return
=======
    async def cache_agent_config(self, agent_id: str, config: Dict[str, Any], ttl: int = 300) -> bool:
        """Cache agent configuration (5 min TTL - agents change infrequently)"""
        if not self.enabled or not self.client:
            return False
>>>>>>> 848cd500ec5fb6f0c0e50fd188bf8819910cd701
        
        try:
            key = f"agent:{agent_id}"
            value = json.dumps(config)
<<<<<<< HEAD
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
=======
            await self.client.setex(key, ttl, value)
            logger.debug(f"💾 Cached agent config: {agent_id}")
            return True
        except Exception as e:
            logger.debug(f"Cache save failed: {e}")
            return False
    
    async def get_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached agent config"""
>>>>>>> 848cd500ec5fb6f0c0e50fd188bf8819910cd701
        if not self.enabled or not self.client:
            return None
        
        try:
            key = f"agent:{agent_id}"
<<<<<<< HEAD
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
=======
            data = await self.client.get(key)
            if data:
                logger.debug(f"⚡ Cache HIT for agent: {agent_id}")
                return json.loads(data)
            return None
        except Exception as e:
            logger.debug(f"Cache retrieval failed: {e}")
            return None
    
    async def invalidate_agent_config(self, agent_id: str) -> bool:
        """Invalidate cached agent config when updated"""
        if not self.enabled or not self.client:
            return False
        
        try:
            key = f"agent:{agent_id}"
            await self.client.delete(key)
            logger.debug(f"🗑️ Invalidated agent cache: {agent_id}")
            return True
        except Exception as e:
            logger.debug(f"Cache invalidation failed: {e}")
            return False
    
    # ==================== UTILITIES ====================
>>>>>>> 848cd500ec5fb6f0c0e50fd188bf8819910cd701
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.enabled or not self.client:
            return {"enabled": False}
        
        try:
            info = await self.client.info("stats")
            return {
                "enabled": True,
<<<<<<< HEAD
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
=======
                "total_commands": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": round(
                    info.get("keyspace_hits", 0) / 
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100,
                    2
                )
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"enabled": True, "error": str(e)}


# Global cache instance
_cache_instance: Optional[CacheClient] = None


async def get_cache_client() -> CacheClient:
    """Get or create cache client singleton"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheClient()
        await _cache_instance.connect()
    return _cache_instance
>>>>>>> 848cd500ec5fb6f0c0e50fd188bf8819910cd701
