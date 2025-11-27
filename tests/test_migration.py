import sys
sys.path.append('/app')
from shared.database import get_db
import asyncio

async def test_migration():
    db = get_db()
    
    # Test if system_prompts table exists and has templates
    try:
        prompts = await db.list_system_prompts(is_template=True)
        print(f"✅ Found {len(prompts)} templates:")
        for p in prompts:
            print(f"  - {p['name']} ({p['category']})")
        return True
    except Exception as e:
        print(f"❌ Migration not run yet: {e}")
        print("\n📋 Please run the SQL in Supabase SQL Editor:")
        print("1. Go to https://supabase.com/dashboard")
        print("2. Select your project: ddgmuyeresgwgojoegiw")
        print("3. Click 'SQL Editor' in left sidebar")
        print("4. Paste the SQL from: d:\\spec-driven-projects\\RelayX\\db\\migrations\\003_system_prompts.sql")
        print("5. Click 'Run'")
        return False

if __name__ == "__main__":
    asyncio.run(test_migration())
