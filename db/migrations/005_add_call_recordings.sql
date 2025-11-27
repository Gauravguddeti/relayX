-- Add recording URL to calls table
ALTER TABLE calls ADD COLUMN IF NOT EXISTS recording_url TEXT;
ALTER TABLE calls ADD COLUMN IF NOT EXISTS recording_duration INTEGER; -- Recording length in seconds

-- Add index for faster queries
CREATE INDEX IF NOT EXISTS idx_calls_recording_url ON calls(recording_url) WHERE recording_url IS NOT NULL;
