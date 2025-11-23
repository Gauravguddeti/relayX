-- RelayX Database Schema for Supabase
-- Run this in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Agents Table
-- Stores AI agent configurations with system prompts
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    system_prompt TEXT NOT NULL,
    voice_settings JSONB DEFAULT '{}', -- TTS voice settings
    llm_model VARCHAR(100) DEFAULT 'llama3:8b',
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 150,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Calls Table
-- Stores call metadata and status
CREATE TABLE IF NOT EXISTS calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    to_number VARCHAR(20) NOT NULL,
    from_number VARCHAR(20) NOT NULL,
    twilio_call_sid VARCHAR(255) UNIQUE,
    status VARCHAR(50) DEFAULT 'initiated', -- initiated, ringing, in-progress, completed, failed, no-answer, busy
    direction VARCHAR(20) DEFAULT 'outbound', -- outbound, inbound
    duration INTEGER, -- in seconds
    started_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Transcripts Table
-- Stores conversation turns (user and AI messages)
CREATE TABLE IF NOT EXISTS transcripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id UUID NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    speaker VARCHAR(20) NOT NULL, -- 'user' or 'agent'
    text TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    audio_duration FLOAT, -- duration of this turn in seconds
    confidence_score FLOAT, -- STT confidence if applicable
    metadata JSONB DEFAULT '{}'
);

-- Call Analysis Table (for post-call analysis feature)
-- Will be implemented after core calling functionality works
CREATE TABLE IF NOT EXISTS call_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id UUID NOT NULL UNIQUE REFERENCES calls(id) ON DELETE CASCADE,
    summary TEXT,
    key_points TEXT[], -- array of key points
    user_sentiment VARCHAR(50), -- very_negative, negative, neutral, positive, very_positive
    outcome VARCHAR(50), -- interested, not_interested, call_later, needs_more_info, wrong_number, other
    next_action TEXT,
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_calls_agent_id ON calls(agent_id);
CREATE INDEX IF NOT EXISTS idx_calls_twilio_sid ON calls(twilio_call_sid);
CREATE INDEX IF NOT EXISTS idx_calls_status ON calls(status);
CREATE INDEX IF NOT EXISTS idx_calls_created_at ON calls(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_transcripts_call_id ON transcripts(call_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_timestamp ON transcripts(timestamp);
CREATE INDEX IF NOT EXISTS idx_call_analysis_call_id ON call_analysis(call_id);

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_calls_updated_at BEFORE UPDATE ON calls
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert a default agent for testing
INSERT INTO agents (name, system_prompt, voice_settings, llm_model) 
VALUES (
    'Sales Assistant',
    'You are a helpful and friendly AI sales assistant. Your goal is to understand the customer''s needs and explain how our product can help them. Be concise, professional, and empathetic. Keep your responses under 2-3 sentences. Ask clarifying questions when needed.',
    '{"speaker": "p326", "language": "en"}',
    'llama3:8b'
) ON CONFLICT DO NOTHING;

COMMENT ON TABLE agents IS 'AI agent configurations with system prompts and settings';
COMMENT ON TABLE calls IS 'Call records with metadata and status tracking';
COMMENT ON TABLE transcripts IS 'Conversation history for each call (turn-by-turn)';
COMMENT ON TABLE call_analysis IS 'Post-call AI analysis results';
