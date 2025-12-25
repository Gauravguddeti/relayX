"""
Campaign Scheduler - Background worker for sequential call execution
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timezone
from typing import Dict
from loguru import logger
import asyncio

from shared.database import SupabaseDB
from campaign_executor import CampaignExecutor

class CampaignScheduler:
    """Background scheduler for processing bulk campaigns"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.db = SupabaseDB()
        self.executor = CampaignExecutor(self.db)
        self.running = False
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        # Schedule campaign processor every 30 seconds
        self.scheduler.add_job(
            self.process_campaigns,
            trigger=IntervalTrigger(seconds=30),
            id='campaign_processor',
            name='Process running campaigns',
            replace_existing=True
        )
        
        # Schedule watchdog cleanup every 5 minutes
        self.scheduler.add_job(
            self.executor.cleanup_watchdog,
            trigger=IntervalTrigger(minutes=5),
            id='watchdog_cleanup',
            name='Clean up stuck contacts',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.running = True
        logger.info("Campaign scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.running:
            return
        
        self.scheduler.shutdown()
        self.running = False
        logger.info("Campaign scheduler stopped")
    
    async def process_campaigns(self):
        """Main processing loop - finds and executes next calls"""
        try:
            # Find campaigns that need processing
            campaigns = await self.find_active_campaigns()
            
            for campaign in campaigns:
                try:
                    await self.process_campaign(campaign)
                except Exception as e:
                    logger.error(f"Error processing campaign {campaign['id']}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in campaign processor: {e}")
    
    async def find_active_campaigns(self):
        """Find campaigns in running or pending state"""
        try:
            # Get running campaigns
            result = self.db.client.table("bulk_campaigns").select("*").in_("state", ["running", "pending"]).execute()
            
            campaigns = result.data or []
            
            # Transition pending -> running
            for campaign in campaigns:
                if campaign['state'] == 'pending':
                    # Check if scheduled_start_time has passed
                    if campaign.get('scheduled_start_time'):
                        scheduled = datetime.fromisoformat(campaign['scheduled_start_time'].replace('Z', '+00:00'))
                        if scheduled > datetime.now(timezone.utc):
                            continue  # Not time yet
                    
                    # Start it
                    self.db.client.table("bulk_campaigns").update({
                        "state": "running"
                    }).eq("id", campaign['id']).execute()
                    
                    campaign['state'] = 'running'
                    logger.info(f"Campaign {campaign['id']} transitioned to running")
            
            return [c for c in campaigns if c['state'] == 'running']
            
        except Exception as e:
            logger.error(f"Error finding active campaigns: {e}")
            return []
    
    async def process_campaign(self, campaign: Dict):
        """Process one call for a campaign"""
        campaign_id = campaign['id']
        
        # Check if we have an active call already
        active_calls = self.db.client.table("campaign_contacts").select("id").eq("campaign_id", campaign_id).eq("state", "calling").execute()
        
        if active_calls.data:
            # Still processing previous call, wait
            logger.debug(f"Campaign {campaign_id} has active call, waiting...")
            return
        
        # Check business hours
        if not await self.executor.check_business_hours(campaign):
            logger.debug(f"Campaign {campaign_id} outside business hours")
            return
        
        # Check pacing
        if not await self.executor.check_pacing(campaign_id, campaign['settings_snapshot']):
            logger.debug(f"Campaign {campaign_id} waiting for pacing delay")
            return
        
        # Fetch next contact
        contact = await self.executor.fetch_next_contact(campaign_id)
        
        if not contact:
            # No more pending contacts
            await self.executor.check_campaign_completion(campaign_id)
            return
        
        # Execute call
        success = await self.executor.execute_call(contact, campaign)
        
        if success:
            logger.info(f"Campaign {campaign_id}: Executed call to {contact['phone']}")
        else:
            logger.error(f"Campaign {campaign_id}: Failed to execute call to {contact['phone']}")
        
        # Update stats
        await self.executor.update_campaign_stats(campaign_id)

# Global scheduler instance
_scheduler = None

def get_scheduler() -> CampaignScheduler:
    """Get or create global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = CampaignScheduler()
    return _scheduler

def start_scheduler():
    """Start the global scheduler"""
    scheduler = get_scheduler()
    scheduler.start()

def stop_scheduler():
    """Stop the global scheduler"""
    global _scheduler
    if _scheduler:
        _scheduler.stop()
