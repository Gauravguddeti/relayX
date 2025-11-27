from shared.database import get_db
from dotenv import load_dotenv

load_dotenv()

db = get_db()

# Get recent calls
calls = db.client.table('calls').select('id, status, direction, to_number, created_at').order('created_at', desc=True).limit(10).execute()

print("\nRecent Calls:")
print("-" * 100)
for c in calls.data:
    print(f"{c['id'][:8]}... | {c['status']:12} | {c['direction']:8} | {c.get('to_number', 'N/A'):15} | {c['created_at']}")

# Find stuck calls (in-progress or initiated)
stuck_calls = [c for c in calls.data if c['status'] in ['in-progress', 'initiated']]
if stuck_calls:
    print(f"\n⚠️  Found {len(stuck_calls)} stuck call(s)")
    for call in stuck_calls:
        print(f"Fixing call: {call['id']} (status: {call['status']})")
        # initiated calls that never progressed should be no-answer
        new_status = 'no-answer' if call['status'] == 'initiated' else 'completed'
        db.client.table('calls').update({"status": new_status}).eq("id", call['id']).execute()
        print(f"✅ Updated to '{new_status}'")
else:
    print("\n✅ No stuck calls found")
