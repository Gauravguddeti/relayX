-- Bulk Campaigns System Migration
-- Creates tables for sequential bulk calling with flexible contact storage

-- Campaign state enum
CREATE TYPE campaign_state AS ENUM ('draft', 'pending', 'running', 'paused', 'completed', 'failed');

-- Contact state enum  
CREATE TYPE contact_state AS ENUM ('pending', 'calling', 'completed', 'failed', 'skipped');

-- Bulk campaigns table
CREATE TABLE bulk_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id),
    name TEXT NOT NULL,
    state campaign_state DEFAULT 'draft',
    timezone TEXT DEFAULT 'UTC',
    settings_snapshot JSONB NOT NULL DEFAULT '{
        "pacing": {"delay_seconds": 10},
        "business_hours": {"enabled": false, "days": [1,2,3,4,5], "start_time": "09:00", "end_time": "17:00"},
        "retry_policy": {"max_retries": 3, "backoff_hours": [1, 4, 24], "retryable_outcomes": ["no-answer", "busy", "failed"]}
    }',
    stats JSONB DEFAULT '{"total": 0, "completed": 0, "failed": 0, "pending": 0, "success_rate": 0}',
    scheduled_start_time TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Campaign contacts table with flexible metadata
CREATE TABLE campaign_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES bulk_campaigns(id) ON DELETE CASCADE,
    phone TEXT NOT NULL,
    name TEXT,
    metadata JSONB DEFAULT '{}',
    call_id UUID REFERENCES calls(id),
    state contact_state DEFAULT 'pending',
    retry_count INT DEFAULT 0,
    outcome TEXT,
    locked_until TIMESTAMPTZ,
    last_attempted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add campaign_id to calls table
ALTER TABLE calls ADD COLUMN IF NOT EXISTS campaign_id UUID REFERENCES bulk_campaigns(id);

-- Indexes for performance
CREATE INDEX idx_campaigns_user_state ON bulk_campaigns(user_id, state);
CREATE INDEX idx_campaigns_user_created ON bulk_campaigns(user_id, created_at DESC);
CREATE INDEX idx_campaigns_scheduled ON bulk_campaigns(scheduled_start_time) WHERE state = 'pending';
CREATE INDEX idx_contacts_campaign_state ON campaign_contacts(campaign_id, state);
CREATE INDEX idx_contacts_locked ON campaign_contacts(locked_until) WHERE locked_until IS NOT NULL;
CREATE INDEX idx_contacts_pending ON campaign_contacts(campaign_id, created_at) WHERE state = 'pending';
CREATE INDEX idx_calls_campaign ON calls(campaign_id) WHERE campaign_id IS NOT NULL;

-- Trigger for updated_at
CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON bulk_campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE bulk_campaigns IS 'Sequential bulk calling campaigns with state machine';
COMMENT ON TABLE campaign_contacts IS 'Contacts for bulk campaigns with flexible metadata storage';
COMMENT ON COLUMN campaign_contacts.metadata IS 'Flexible JSONB for variable fields like company, email, notes';
COMMENT ON COLUMN campaign_contacts.locked_until IS 'Watchdog timestamp to prevent deadlocks if webhook fails';
