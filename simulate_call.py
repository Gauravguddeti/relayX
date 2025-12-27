"""
Simulate a complete call conversation with RAG
Shows how KB context is injected into LLM prompts
"""
import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "voice_gateway"))
sys.path.append(os.path.join(os.path.dirname(__file__), "shared"))

from shared.database import SupabaseDB
from shared.llm_client import LLMClient
from dotenv import load_dotenv

load_dotenv()


async def retrieve_relevant_knowledge(agent_id: str, user_query: str, db: SupabaseDB) -> str:
    """RAG: Search KB for relevant info"""
    try:
        knowledge = await db.get_agent_knowledge(agent_id)
        if not knowledge:
            return ""
        
        query_words = set(user_query.lower().split())
        relevant_entries = []
        
        for entry in knowledge:
            content = (entry.get("title", "") + " " + entry.get("content", "")).lower()
            matches = sum(1 for word in query_words if word in content and len(word) > 3)
            
            if matches > 0:
                relevant_entries.append({"entry": entry, "score": matches})
        
        relevant_entries.sort(key=lambda x: x["score"], reverse=True)
        top_entries = relevant_entries[:2]
        
        if not top_entries:
            return ""
        
        kb_context = "\n\nRELEVANT KNOWLEDGE BASE:\n"
        for item in top_entries:
            entry = item["entry"]
            kb_context += f"- {entry.get('title', 'Info')}: {entry.get('content', '')[:200]}\n"
        
        return kb_context
    except Exception as e:
        print(f"❌ RAG error: {e}")
        return ""


async def simulate_call():
    """Simulate a full call conversation with RAG"""
    print("=" * 80)
    print("SIMULATED CALL WITH RAG")
    print("=" * 80)
    
    db = SupabaseDB()
    llm = LLMClient()
    
    # Get Landing Page Demo Agent
    print("\n📞 Connecting to agent...")
    result = db.client.table("agents").select("*").execute()
    agents = result.data
    
    agent = next((a for a in agents if 'landing' in a['name'].lower() or 'demo' in a['name'].lower()), agents[0])
    agent_id = agent['id']
    agent_name = agent['name']
    
    print(f"✅ Connected to: {agent_name}")
    print(f"   Agent ID: {agent_id[:8]}...")
    
    system_prompt = agent.get('resolved_system_prompt') or agent.get('system_prompt', 'You are a helpful assistant.')
    print(f"   Base System Prompt: {system_prompt[:100]}...")
    
    # Simulate conversation
    conversation_history = []
    
    print("\n" + "=" * 80)
    print("CONVERSATION STARTS")
    print("=" * 80)
    
    # Turn 1: Greeting
    print("\n🤖 AI: Hello! Thanks for calling. How can I help you today?")
    conversation_history.append({"role": "assistant", "content": "Hello! Thanks for calling. How can I help you today?"})
    
    # Turn 2: User asks about features
    user_message_1 = "What features does RelayX offer?"
    print(f"\n👤 User: {user_message_1}")
    
    print("\n🔍 [RAG Retrieval]")
    kb_context_1 = await retrieve_relevant_knowledge(agent_id, user_message_1, db)
    if kb_context_1:
        print(f"   ✅ Retrieved KB context ({len(kb_context_1)} chars)")
        print(f"   KB Preview: {kb_context_1[:150]}...")
    else:
        print("   ⚠️ No KB context found")
    
    print("\n📝 [Building System Prompt]")
    full_system_prompt_1 = f"{system_prompt}{kb_context_1}"
    print(f"   Total prompt length: {len(full_system_prompt_1)} chars")
    print(f"   Prompt preview: {full_system_prompt_1[:200]}...")
    
    print("\n🤖 [Calling LLM...]")
    messages_1 = conversation_history + [{"role": "user", "content": user_message_1}]
    
    try:
        ai_response_1 = await llm.generate_response(
            messages=messages_1,
            system_prompt=full_system_prompt_1,
            temperature=0.7,
            max_tokens=150
        )
        print(f"✅ LLM Response: {ai_response_1}")
        conversation_history.append({"role": "user", "content": user_message_1})
        conversation_history.append({"role": "assistant", "content": ai_response_1})
    except Exception as e:
        print(f"❌ LLM Error: {e}")
        ai_response_1 = "I apologize, I'm having technical difficulties."
    
    # Turn 3: User asks follow-up
    user_message_2 = "How does the AI calling work?"
    print(f"\n👤 User: {user_message_2}")
    
    print("\n🔍 [RAG Retrieval]")
    kb_context_2 = await retrieve_relevant_knowledge(agent_id, user_message_2, db)
    if kb_context_2:
        print(f"   ✅ Retrieved KB context ({len(kb_context_2)} chars)")
        print(f"   KB Preview: {kb_context_2[:150]}...")
    else:
        print("   ⚠️ No KB context found")
    
    print("\n📝 [Building System Prompt]")
    full_system_prompt_2 = f"{system_prompt}{kb_context_2}"
    
    # Use last 8 messages (context window)
    recent_history = conversation_history[-8:] if len(conversation_history) > 8 else conversation_history
    print(f"   Using last {len(recent_history)} messages for context")
    
    print("\n🤖 [Calling LLM...]")
    messages_2 = recent_history + [{"role": "user", "content": user_message_2}]
    
    try:
        ai_response_2 = await llm.generate_response(
            messages=messages_2,
            system_prompt=full_system_prompt_2,
            temperature=0.7,
            max_tokens=150
        )
        print(f"✅ LLM Response: {ai_response_2}")
        conversation_history.append({"role": "user", "content": user_message_2})
        conversation_history.append({"role": "assistant", "content": ai_response_2})
    except Exception as e:
        print(f"❌ LLM Error: {e}")
        ai_response_2 = "I apologize, I'm having technical difficulties."
    
    # Turn 4: User asks about pricing
    user_message_3 = "What's the pricing?"
    print(f"\n👤 User: {user_message_3}")
    
    print("\n🔍 [RAG Retrieval]")
    kb_context_3 = await retrieve_relevant_knowledge(agent_id, user_message_3, db)
    if kb_context_3:
        print(f"   ✅ Retrieved KB context ({len(kb_context_3)} chars)")
    else:
        print("   ⚠️ No KB context found")
    
    print("\n📝 [Building System Prompt]")
    full_system_prompt_3 = f"{system_prompt}{kb_context_3}"
    
    recent_history = conversation_history[-8:] if len(conversation_history) > 8 else conversation_history
    
    print("\n🤖 [Calling LLM...]")
    messages_3 = recent_history + [{"role": "user", "content": user_message_3}]
    
    try:
        ai_response_3 = await llm.generate_response(
            messages=messages_3,
            system_prompt=full_system_prompt_3,
            temperature=0.7,
            max_tokens=150
        )
        print(f"✅ LLM Response: {ai_response_3}")
        conversation_history.append({"role": "user", "content": user_message_3})
        conversation_history.append({"role": "assistant", "content": ai_response_3})
    except Exception as e:
        print(f"❌ LLM Error: {e}")
    
    print("\n" + "=" * 80)
    print("CALL SUMMARY")
    print("=" * 80)
    print(f"Total turns: {len(conversation_history) // 2}")
    print(f"Context window: 8 messages")
    print(f"Max tokens per response: 150")
    print(f"RAG retrievals: 3")
    print("\n✅ Call simulation complete!")


if __name__ == "__main__":
    asyncio.run(simulate_call())
