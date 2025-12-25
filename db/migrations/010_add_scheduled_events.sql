-- Migration: Add scheduled_events table for linking calls to calendar events
-- This enables automatic event creation from call analysis

CREATE TABLE IF NOT EXISTS scheduled_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    call_id UUID REFERENCES calls(id) ON DELETE CASCADE,
    campaign_id UUID, -- No FK constraint since campaigns table may not exist
    
    -- Event details
    event_type VARCHAR(50) NOT NULL, -- 'demo', 'followup', 'call', 'meeting'
    title VARCHAR(255) NOT NULL,
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_minutes INTEGER DEFAULT 30,
    timezone VARCHAR(100) DEFAULT 'America/New_York',
    
    -- Contact information
    contact_name VARCHAR(255),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    
    -- Cal.com integration
    cal_booking_id INTEGER, -- Cal.com booking ID
    cal_booking_uid VARCHAR(255), -- Cal.com booking UID
    cal_event_type_id INTEGER, -- Cal.com event type ID
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'scheduled', -- 'scheduled', 'completed', 'cancelled', 'no_show'
    created_automatically BOOLEAN DEFAULT false, -- True if created from call analysis
    
    -- Additional data
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_scheduled_events_user_id ON scheduled_events(user_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_events_call_id ON scheduled_events(call_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_events_campaign_id ON scheduled_events(campaign_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_events_scheduled_at ON scheduled_events(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_scheduled_events_status ON scheduled_events(status);
CREATE INDEX IF NOT EXISTS idx_scheduled_events_cal_booking_id ON scheduled_events(cal_booking_id);

-- Add unique constraint to prevent duplicate Cal.com bookings
CREATE UNIQUE INDEX IF NOT EXISTS idx_scheduled_events_cal_booking_uid 
ON scheduled_events(cal_booking_uid) 
WHERE cal_booking_uid IS NOT NULL;

-- Add constraint to ensure call_id is set (campaign_id is optional)
ALTER TABLE scheduled_events 
ADD CONSTRAINT check_event_source 
CHECK (call_id IS NOT NULL);

COMMENT ON TABLE scheduled_events IS 'Stores scheduled events created automatically from calls or manually by users';
COMMENT ON COLUMN scheduled_events.created_automatically IS 'True if event was created automatically from call intelligence';
COMMENT ON COLUMN scheduled_events.cal_booking_id IS 'Links to Cal.com booking for two-way sync';
