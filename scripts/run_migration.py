"""
Run database migration for system prompts
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def run_migration():
    """Execute the system prompts migration"""
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_KEY")
        return False
    
    print(f"🔄 Connecting to Supabase...")
    client = create_client(url, key)
    
    # Read migration file
    migration_path = os.path.join(os.path.dirname(__file__), "migrations", "004_simplify_prompts.sql")
    with open(migration_path, "r") as f:
        sql = f.read()
    
    print(f"📝 Running migration: 004_simplify_prompts.sql")
    
    try:
        # Execute via Supabase REST API (SQL editor)
        print("⚠️  Note: Please run this SQL manually in Supabase SQL Editor:")
        print("-" * 60)
        print(sql)
        print("-" * 60)
        print("\n📋 Steps:")
        print("1. Go to https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Go to SQL Editor")
        print("4. Paste the SQL above")
        print("5. Click Run")
        print("\n✅ Migration file ready!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    run_migration()
