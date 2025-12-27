import asyncio
from shared.database import SupabaseDB

async def check_kiosk():
    db = SupabaseDB()
    
    # Get Kiosk agent
    result = db.client.table("agents").select("*").eq("name", "Kisok").execute()
    
    if result.data:
        agent = result.data[0]
        print("=" * 80)
        print("KIOSK AGENT FROM DATABASE:")
        print("=" * 80)
        print(f"ID: {agent['id']}")
        print(f"Name: {agent['name']}")
        print(f"User ID: {agent['user_id']}")
        print("\n" + "=" * 80)
        print("PROMPT_TEXT (full):")
        print("=" * 80)
        print(agent['prompt_text'])
        print("\n" + "=" * 80)
        print(f"Prompt length: {len(agent['prompt_text'])} characters")
        print("=" * 80)
        
        # Check what the parser would extract
        lines = agent['prompt_text'].split('\n')
        
        # Find system prompt section
        found_start = False
        start_idx = 0
        for i, line in enumerate(lines):
            if 'What we do:' in line:
                start_idx = i + 2
                found_start = True
                break
        
        end_idx = len(lines)
        for i, line in enumerate(lines):
            if 'Remember: Your goal' in line:
                end_idx = i
                break
        
        if found_start:
            extracted = '\n'.join(lines[start_idx:end_idx]).strip()
            print("\n" + "=" * 80)
            print("EXTRACTED SYSTEM PROMPT (what parser should find):")
            print("=" * 80)
            print(extracted)
            print("\n" + "=" * 80)
            print(f"Extracted length: {len(extracted)} characters")
            print("=" * 80)
    else:
        print("Kiosk agent not found!")

asyncio.run(check_kiosk())
