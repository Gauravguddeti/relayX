"""
Test RAG (Retrieval Augmented Generation) functionality
"""
import asyncio
import sys
import os

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), "voice_gateway"))
sys.path.append(os.path.join(os.path.dirname(__file__), "shared"))

from shared.database import SupabaseDB
from dotenv import load_dotenv

load_dotenv()


async def retrieve_relevant_knowledge(agent_id: str, user_query: str, db: SupabaseDB) -> str:
    """RAG: Search KB for relevant info"""
    try:
        # Fetch all KB entries for this agent
        knowledge = await db.get_agent_knowledge(agent_id)
        
        if not knowledge:
            print(f"❌ No KB entries found for agent {agent_id}")
            return ""
        
        print(f"📚 Found {len(knowledge)} KB entries")
        print("\n--- All KB Entries ---")
        for i, entry in enumerate(knowledge, 1):
            print(f"{i}. {entry.get('title', 'Untitled')}: {entry.get('content', '')[:100]}...")
        
        # Simple keyword-based relevance scoring
        query_words = set(user_query.lower().split())
        relevant_entries = []
        
        print(f"\n🔍 Searching for: {user_query}")
        print(f"Keywords: {query_words}")
        
        for entry in knowledge:
            # Search in title and content
            content = (entry.get("title", "") + " " + entry.get("content", "")).lower()
            
            # Count matching words
            matches = sum(1 for word in query_words if word in content and len(word) > 3)
            
            if matches > 0:
                relevant_entries.append({
                    "entry": entry,
                    "score": matches
                })
                print(f"  ✓ Match ({matches} keywords): {entry.get('title', 'Untitled')}")
        
        # Sort by relevance and take top 2
        relevant_entries.sort(key=lambda x: x["score"], reverse=True)
        top_entries = relevant_entries[:2]
        
        if not top_entries:
            print("❌ No relevant KB entries found")
            return ""
        
        # Format KB context for LLM
        kb_context = "\n\nRELEVANT KNOWLEDGE BASE:\n"
        for item in top_entries:
            entry = item["entry"]
            kb_context += f"- {entry.get('title', 'Info')}: {entry.get('content', '')[:200]}\n"
        
        print("\n✅ KB Context to inject into LLM:")
        print(kb_context)
        
        return kb_context
        
    except Exception as e:
        print(f"❌ RAG retrieval error: {e}")
        import traceback
        traceback.print_exc()
        return ""


async def test_rag():
    """Test RAG with sample queries"""
    print("=" * 60)
    print("RAG (Retrieval Augmented Generation) Test")
    print("=" * 60)
    
    db = SupabaseDB()
    
    # Get all agents
    print("\n1️⃣ Fetching all agents...")
    result = db.client.table("agents").select("id,name").execute()
    agents = result.data
    
    if not agents:
        print("❌ No agents found in database")
        return
    
    print(f"Found {len(agents)} agents:")
    for i, agent in enumerate(agents, 1):
        print(f"{i}. {agent['name']} (ID: {agent['id'][:8]}...)")
    
    # Use Landing Page Demo agent for testing
    test_agent = next((a for a in agents if 'landing' in a['name'].lower() or 'demo' in a['name'].lower()), agents[0])
    agent_id = test_agent['id']
    agent_name = test_agent['name']
    
    print(f"\n2️⃣ Testing RAG with agent: {agent_name}")
    print("-" * 60)
    
    # Test different queries
    test_queries = [
        "What is RelayX?",
        "How does your AI calling system work?",
        "What features do you offer?",
        "Tell me about pricing",
        "How can I integrate with your API?",
    ]
    
    for query in test_queries:
        print(f"\n{'=' * 60}")
        print(f"Query: {query}")
        print("=" * 60)
        kb_context = await retrieve_relevant_knowledge(agent_id, query, db)
        
        if kb_context:
            print(f"\n📝 Retrieved {len(kb_context)} characters of KB context")
        else:
            print("\n⚠️ No KB context found for this query")
        
        print()
    
    print("\n" + "=" * 60)
    print("✅ RAG Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_rag())
