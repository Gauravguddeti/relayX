#!/usr/bin/env python3
"""Fix calls stuck in initiated/ringing/in-progress status."""

import sys
sys.path.append('/app')

from shared.database import get_db
from datetime import datetime, timedelta

def main():
    db = get_db()
    
    # Find calls stuck for more than 5 minutes
    five_minutes_ago = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
    
    stuck_calls = db.client.table('calls').select('id, status, started_at').in_(
        'status', ['initiated', 'ringing', 'in-progress']
    ).lt('created_at', five_minutes_ago).execute()
    
    if not stuck_calls.data:
        print("No stuck calls found.")
        return
    
    print(f"Found {len(stuck_calls.data)} stuck calls:")
    
    for call in stuck_calls.data:
        print(f"  {call['id']} - {call['status']}")
        
        # Mark as failed with ended_at timestamp
        db.client.table('calls').update({
            'status': 'failed',
            'ended_at': datetime.utcnow().isoformat()
        }).eq('id', call['id']).execute()
    
    print(f"\n✅ Fixed {len(stuck_calls.data)} stuck calls")

if __name__ == '__main__':
    main()
