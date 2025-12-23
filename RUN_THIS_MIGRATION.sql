-- Run this SQL migration in your Supabase SQL editor

-- Step 1: Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT,
    phone TEXT,
    company TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Step 2: Create auth_tokens table
CREATE TABLE IF NOT EXISTS auth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    refresh_token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Step 3: Add indexes
CREATE INDEX IF NOT EXISTS idx_agents_user_id ON agents(user_id);
CREATE INDEX IF NOT EXISTS idx_calls_user_id ON calls(user_id);  
CREATE INDEX IF NOT EXISTS idx_knowledge_user_id ON knowledge_base(user_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_user_id ON auth_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_refresh_token ON auth_tokens(refresh_token);
CREATE INDEX IF NOT EXISTS idx_calls_created_at ON calls(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_calls_user_status ON calls(user_id, status);

-- Step 4: Create a test user (password is 'test123')
INSERT INTO users (email, password_hash, name) VALUES 
('test@relayx.ai', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aidancNT7wUy', 'Test User')
ON CONFLICT (email) DO NOTHING;

-- Step 5: Get the test user ID and assign existing data to them
DO $$
DECLARE
    test_user_id UUID;
BEGIN
    SELECT id INTO test_user_id FROM users WHERE email = 'test@relayx.ai';
    
    -- Update agents without user_id
    UPDATE agents SET user_id = test_user_id WHERE user_id IS NULL;
    
    -- Update calls without user_id  
    UPDATE calls SET user_id = test_user_id WHERE user_id IS NULL;
    
    -- Update knowledge_base without user_id
    UPDATE knowledge_base SET user_id = test_user_id WHERE user_id IS NULL;
END $$;

-- Step 6: Make user_id NOT NULL (after data migration)
ALTER TABLE agents ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE calls ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE knowledge_base ALTER COLUMN user_id SET NOT NULL;

SELECT 'Migration completed successfully!' as status;
