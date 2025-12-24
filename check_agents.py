import asyncio
import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(__file__))
from shared.database import SupabaseDB

async def main():
    db = SupabaseDB()
    agents = await db.list_agents(is_active=None)  # Get all agents regardless of active status
    
    print("\n=== AGENTS IN DATABASE ===\n")
    for agent in agents:
        print(f"ID: {agent['id']}")
        print(f"Name: {agent['name']}")
        print(f"Active: {agent.get('is_active', True)}")
        print(f"Template: {agent.get('template_source', 'N/A')}")
        print(f"Created: {agent.get('created_at', 'N/A')}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
