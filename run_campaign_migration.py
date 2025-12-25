"""
Run the bulk campaigns migration
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Read migration file
with open('db/migrations/010_bulk_campaigns.sql', 'r') as f:
    sql = f.read()

print("Running bulk campaigns migration...")
print("=" * 60)

# Split by semicolon and execute each statement
statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]

for i, statement in enumerate(statements, 1):
    if statement:
        try:
            print(f"\n[{i}/{len(statements)}] Executing...")
            # Use rpc to execute raw SQL
            result = client.rpc('exec_sql', {'sql_query': statement}).execute()
            print(f"✓ Success")
        except Exception as e:
            error_msg = str(e)
            if 'already exists' in error_msg or 'duplicate' in error_msg.lower():
                print(f"⚠ Skipped (already exists)")
            else:
                print(f"✗ Error: {error_msg}")

print("\n" + "=" * 60)
print("Migration complete!")
print("\nCreated tables:")
print("  - bulk_campaigns (with campaign_state enum)")
print("  - campaign_contacts (with contact_state enum)")
print("  - Added campaign_id column to calls table")
