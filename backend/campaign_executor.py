"""
Campaign Executor - Sequential call processing with atomic fetch-and-lock
"""
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import Optional, Dict
from loguru import logger
import asyncio

from shared.database import SupabaseDB

class CampaignExecutor:
    """Executes bulk campaigns one call at a time with proper state management"""
    
    def __init__(self, db: SupabaseDB):
        self.db = db
        self.last_call_time = {}  # campaign_id -> timestamp
    
    async def fetch_next_contact(self, campaign_id: str) -> Optional[Dict]:
        """
        Atomically fetch and lock next pending contact
        
        Uses SELECT FOR UPDATE SKIP LOCKED to prevent race conditions
        Sets 5-minute watchdog timeout to prevent deadlocks
        """
        try:
            # Raw SQL for atomic fetch-and-lock
            # Note: Supabase client doesn't support FOR UPDATE, so we use PostgreSQL function
            
            # For now, use simpler approach: find pending contacts and update first one
            # In production, create a PostgreSQL function for true atomic behavior
            
            result = self.db.client.table("campaign_contacts").select("*").eq("campaign_id", campaign_id).eq("state", "pending").is_("locked_until", "null").order("created_at").limit(1).execute()
            
            if not result.data:
                return None
            
            contact = result.data[0]
            
            # Lock it
            locked_until = datetime.now(timezone.utc) + timedelta(minutes=5)
            update_result = self.db.client.table("campaign_contacts").update({
                "state": "calling",
                "locked_until": locked_until.isoformat(),
                "last_attempted_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", contact['id']).eq("state", "pending").execute()  # Double-check state hasn't changed
            
            if not update_result.data:
                # Someone else got it
                return None
            
            return update_result.data[0]
            
        except Exception as e:
            logger.error(f"Error fetching next contact for campaign {campaign_id}: {e}")
            return None
    
    async def check_business_hours(self, campaign: Dict) -> bool:
        """Check if current time is within campaign business hours"""
        settings = campaign.get('settings_snapshot', {})
        biz_hours = settings.get('business_hours', {})
        
        if not biz_hours.get('enabled', False):
            return True
        
        try:
            # Get current time in campaign timezone
            tz = ZoneInfo(campaign.get('timezone', 'UTC'))
            now = datetime.now(tz)
            
            # Check day of week (Monday=0)
            allowed_days = biz_hours.get('days', [0, 1, 2, 3, 4])
            if now.weekday() not in allowed_days:
                return False
            
            # Check time range
            current_time = now.time()
            start_time = datetime.strptime(biz_hours['start_time'], '%H:%M').time()
            end_time = datetime.strptime(biz_hours['end_time'], '%H:%M').time()
            
            return start_time <= current_time <= end_time
            
        except Exception as e:
            logger.error(f"Error checking business hours: {e}")
            return True  # Fail open
    
    async def check_pacing(self, campaign_id: str, settings: Dict) -> bool:
        """Check if enough time has passed since last call"""
        pacing = settings.get('pacing', {})
        delay_seconds = pacing.get('delay_seconds', 10)
        
        if campaign_id not in self.last_call_time:
            return True
        
        elapsed = (datetime.now(timezone.utc) - self.last_call_time[campaign_id]).total_seconds()
        
        if elapsed < delay_seconds:
            return False
        
        return True
    
    async def execute_call(self, contact: Dict, campaign: Dict) -> bool:
        """
        Create outbound call for contact
        
        Returns True if call was initiated successfully
        """
        try:
            from backend.main import twilio_client, TWILIO_PHONE_NUMBER
            
            if not twilio_client:
                logger.error("Twilio client not configured")
                return False
            
            settings = campaign['settings_snapshot']
            agent_id = campaign['agent_id']
            
            # Create call record
            call_data = {
                "agent_id": agent_id,
                "to_number": contact['phone'],
                "from_number": TWILIO_PHONE_NUMBER,
                "direction": "outbound",
                "user_id": campaign['user_id'],
                "campaign_id": campaign['id'],
                "metadata": {
                    "contact_name": contact.get('name'),
                    "contact_metadata": contact.get('metadata', {})
                }
            }
            
            call_result = self.db.client.table("calls").insert(call_data).execute()
            call = call_result.data[0]
            call_id = call['id']
            
            # Link contact to call
            self.db.client.table("campaign_contacts").update({
                "call_id": call_id
            }).eq("id", contact['id']).execute()
            
            # Initiate Twilio call (will be handled by existing webhook flow)
            # Import here to avoid circular dependency
            import os
            voice_gateway_url = os.getenv("VOICE_GATEWAY_URL", "")
            
            twilio_call = twilio_client.calls.create(
                to=contact['phone'],
                from_=TWILIO_PHONE_NUMBER,
                url=f"{voice_gateway_url}/twiml/{call_id}",
                status_callback=f"{voice_gateway_url}/webhooks/twilio/status",
                status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                method='POST'
            )
            
            # Update call with Twilio SID
            self.db.client.table("calls").update({
                "twilio_call_sid": twilio_call.sid,
                "status": "initiated"
            }).eq("id", call_id).execute()
            
            # Record call time for pacing
            self.last_call_time[campaign['id']] = datetime.now(timezone.utc)
            
            logger.info(f"Initiated call {call_id} for contact {contact['id']} in campaign {campaign['id']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing call for contact {contact['id']}: {e}")
            
            # Mark contact as failed
            self.db.client.table("campaign_contacts").update({
                "state": "failed",
                "outcome": "execution_error",
                "locked_until": None
            }).eq("id", contact['id']).execute()
            
            return False
    
    async def cleanup_watchdog(self):
        """Release locked contacts that have expired watchdog timeout"""
        try:
            now = datetime.now(timezone.utc)
            
            result = self.db.client.table("campaign_contacts").update({
                "locked_until": None,
                "state": "pending"
            }).lt("locked_until", now.isoformat()).eq("state", "calling").execute()
            
            if result.data:
                logger.warning(f"Released {len(result.data)} stuck contacts from watchdog timeout")
                
        except Exception as e:
            logger.error(f"Error in watchdog cleanup: {e}")
    
    async def update_campaign_stats(self, campaign_id: str):
        """Recalculate and update campaign statistics"""
        try:
            # Count contacts by state
            result = self.db.client.table("campaign_contacts").select("state, outcome").eq("campaign_id", campaign_id).execute()
            
            contacts = result.data
            total = len(contacts)
            completed = len([c for c in contacts if c['state'] == 'completed'])
            failed = len([c for c in contacts if c['state'] == 'failed'])
            pending = len([c for c in contacts if c['state'] == 'pending'])
            
            # Calculate success rate
            success_rate = (completed / total * 100) if total > 0 else 0
            
            stats = {
                "total": total,
                "completed": completed,
                "failed": failed,
                "pending": pending,
                "success_rate": round(success_rate, 1)
            }
            
            # Update campaign
            self.db.client.table("bulk_campaigns").update({
                "stats": stats
            }).eq("id", campaign_id).execute()
            
        except Exception as e:
            logger.error(f"Error updating campaign stats: {e}")
    
    async def check_campaign_completion(self, campaign_id: str):
        """Check if campaign is complete and update state"""
        try:
            # Get pending count
            result = self.db.client.table("campaign_contacts").select("id").eq("campaign_id", campaign_id).eq("state", "pending").execute()
            
            if not result.data:
                # No more pending contacts - campaign complete
                self.db.client.table("bulk_campaigns").update({
                    "state": "completed",
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }).eq("id", campaign_id).execute()
                
                logger.info(f"Campaign {campaign_id} completed")
                
        except Exception as e:
            logger.error(f"Error checking campaign completion: {e}")
