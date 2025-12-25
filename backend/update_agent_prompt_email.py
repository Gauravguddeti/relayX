"""
Update agent prompt to make email optional and use phone number for scheduling.
"""
import asyncio
import os
from shared.database import SupabaseDB


async def update_prompt():
    """Update the prompt for scheduling demos without requiring email."""
    
    # Initialize database
    db = SupabaseDB(
        url=os.getenv("SUPABASE_URL"),
        key=os.getenv("SUPABASE_ANON_KEY")
    )
    
    # Get all agents
    agents = await db.list_agents(is_active=True)
    
    for agent in agents:
        agent_id = agent['id']
        agent_name = agent['name']
        current_prompt = agent.get('prompt_text', '')
        
        # Add scheduling instructions to the prompt
        scheduling_addendum = """

📅 SCHEDULING INSTRUCTIONS:
- When a user agrees to a demo or follow-up call, capture the date and time naturally
- Email is OPTIONAL - if they don't provide it, use their phone number 
- Never block scheduling on missing email - proceed with phone number only
- Phrases to listen for: "tomorrow at 4", "next Tuesday morning", "Monday afternoon"
- Confirm the time: "Great! I'll have someone reach out tomorrow at 4 PM. Sound good?"
- DO NOT repeatedly ask for email if they don't provide it
- Close the call gracefully after confirming the appointment
"""
        
        # Only add if not already present
        if "SCHEDULING INSTRUCTIONS" not in current_prompt:
            updated_prompt = current_prompt + scheduling_addendum
            
            await db.update_agent(
                agent_id,
                prompt_text=updated_prompt
            )
            
            print(f"✅ Updated agent '{agent_name}' with scheduling instructions")
        else:
            print(f"⏭️  Agent '{agent_name}' already has scheduling instructions")


async def main():
    print("Updating agent prompts to make email optional...\n")
    await update_prompt()
    print("\n✅ All agents updated!")


if __name__ == "__main__":
    asyncio.run(main())
