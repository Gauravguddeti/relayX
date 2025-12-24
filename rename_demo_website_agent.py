"""
Update Demo Website Agent name to relayX sales nihal
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(__file__))
from shared.database import SupabaseDB

AGENT_ID = "ccbb0ac5-4b62-45b0-b2ae-f81bbcebe8c1"  # Demo Website Agent

async def main():
    db = SupabaseDB()
    
    print("Renaming Demo Website Agent to relayX sales nihal...")
    
    agent = await db.update_agent(
        agent_id=AGENT_ID,
        name="relayX sales nihal"
    )
    
    print(f"✅ Renamed agent: {agent['name']}")
    print(f"   ID: {agent['id']}")
    print(f"   Active: {agent['is_active']}")

if __name__ == "__main__":
    asyncio.run(main())
