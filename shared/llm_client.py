"""
LLM Client for Ollama (local) or Groq (cloud)
Handles communication with LLM
"""
from typing import List, Dict, Optional, AsyncGenerator
import httpx
from loguru import logger
import os
from groq import AsyncGroq


class LLMClient:
    """Client for interacting with LLM (local Ollama or cloud Groq)"""
    
    def __init__(self, base_url: str = None, model: str = None):
        self.use_cloud = os.getenv("USE_CLOUD_LLM", "true").lower() == "true"
        
        if self.use_cloud:
            # Use Groq API (FREE, fast)
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment")
            self.client = AsyncGroq(api_key=api_key)
            self.model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
            logger.info(f"Using Groq API | Model: {self.model}")
        else:
            # Use local Ollama
            self.base_url = (base_url or os.getenv("LLM_BASE_URL", "http://localhost:11434")).rstrip("/")
            self.model = model or os.getenv("LLM_MODEL", "llama3:8b")
            logger.info(f"Using Ollama: {self.base_url} | Model: {self.model}")
        
        self.timeout = 60.0
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 150,
        stream: bool = False
    ) -> str:
        """
        Generate a response from the LLM
        
        Args:
            messages: List of conversation messages [{"role": "user", "content": "..."}, ...]
            system_prompt: System prompt to set context
            temperature: Creativity (0.0 to 1.0)
            max_tokens: Max response length
            stream: Whether to stream response (for future use)
        
        Returns:
            Generated text response
        """
        try:
            # Build the full message list
            full_messages = []
            
            if system_prompt:
                full_messages.append({"role": "system", "content": system_prompt})
            
            # Only send last 8 messages to prevent latency spikes as conversation grows
            # This keeps context while maintaining fast response times (~250-500ms)
            recent_messages = messages[-8:] if len(messages) > 8 else messages
            full_messages.extend(recent_messages)
            
            if self.use_cloud:
                # Use Groq API
                logger.debug(f"Sending to Groq: {len(messages)} messages")
                try:
                    chat_completion = await self.client.chat.completions.create(
                        messages=full_messages,  # type: ignore
                        model=self.model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    assistant_message = chat_completion.choices[0].message.content or ""
                    logger.info(f"Groq Response: {assistant_message[:100]}...")
                    return assistant_message.strip()
                except Exception as e:
                    logger.error(f"🔴 GROQ API ERROR (External Service): {type(e).__name__} - {e}")
                    logger.error("This is NOT a system issue. Groq API is down or rate-limited.")
                    raise Exception(f"GROQ_API_FAILURE: {e}") from e
            else:
                # Use local Ollama
                payload = {
                    "model": self.model,
                    "messages": full_messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    }
                }
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    logger.debug(f"Sending to Ollama: {len(messages)} messages")
                    response = await client.post(
                        f"{self.base_url}/api/chat",
                        json=payload
                    )
                    response.raise_for_status()
                    
                    result = response.json()
                    assistant_message = result.get("message", {}).get("content", "")
                    
                    logger.info(f"Ollama Response: {assistant_message[:100]}...")
                    return assistant_message.strip()
                
        except httpx.TimeoutException:
            logger.error("LLM request timed out")
            return "I apologize, I'm having trouble processing right now. Could you repeat that?"
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM HTTP error: {e.response.status_code} - {e.response.text}")
            return "I'm experiencing technical difficulties. Let me try again."
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return "Sorry, I didn't catch that. Could you say that again?"
    
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 150,
    ) -> AsyncGenerator[str, None]:
        """
        Stream response from LLM (for future use)
        """
        try:
            full_messages = []
            if system_prompt:
                full_messages.append({"role": "system", "content": system_prompt})
            full_messages.extend(messages)
            
            payload = {
                "model": self.model,
                "messages": full_messages,
                "stream": True,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=payload
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            import json
                            data = json.loads(line)
                            if "message" in data:
                                content = data["message"].get("content", "")
                                if content:
                                    yield content
        except Exception as e:
            logger.error(f"LLM streaming error: {e}")
            yield "Sorry, I'm having trouble right now."
    
    async def health_check(self) -> bool:
        """Check if LLM is reachable"""
        try:
            if self.use_cloud:
                # Groq is always available if we have an API key
                return True
            else:
                # Check local Ollama
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{self.base_url}/api/tags")
                    return response.status_code == 200
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return False
    
    async def list_models(self) -> List[str]:
        """List available models"""
        try:
            if self.use_cloud:
                # Return Groq models
                return ["llama-3.1-8b-instant", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"]
            else:
                # List local Ollama models
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{self.base_url}/api/tags")
                    response.raise_for_status()
                    data = response.json()
                    return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []


# Global instance
llm_client = None

def get_llm_client() -> LLMClient:
    """Get or create global LLM client"""
    global llm_client
    if llm_client is None:
        llm_client = LLMClient()
    return llm_client
