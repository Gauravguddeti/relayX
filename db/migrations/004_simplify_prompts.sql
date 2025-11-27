-- Migration: Simplify prompt system (remove complexity)
-- Date: 2025-11-27

-- Step 1: Rename system_prompts to templates (simpler, clearer name)
ALTER TABLE IF EXISTS system_prompts RENAME TO templates;

-- Step 2: Remove versioning/history (unnecessary complexity for MVP)
DROP TABLE IF EXISTS system_prompt_history;

-- Step 3: Simplify templates table structure
ALTER TABLE templates 
  DROP COLUMN IF EXISTS version,
  DROP COLUMN IF EXISTS created_by,
  DROP COLUMN IF EXISTS changed_by,
  DROP COLUMN IF EXISTS created_at,
  DROP COLUMN IF EXISTS updated_at;

-- Keep only essential fields
ALTER TABLE templates 
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

-- Step 4: Migrate agents table to snapshot model
-- First, copy system_prompt_id data to system_prompt text (snapshot)
UPDATE agents
SET system_prompt = (
  SELECT content 
  FROM templates 
  WHERE templates.id = agents.system_prompt_id
)
WHERE system_prompt_id IS NOT NULL 
  AND (system_prompt IS NULL OR system_prompt = '');

-- Add template_source to track which template was used (for badge display)
ALTER TABLE agents 
  ADD COLUMN IF NOT EXISTS template_source TEXT;

-- Update template_source from existing system_prompt_id
UPDATE agents
SET template_source = (
  SELECT name 
  FROM templates 
  WHERE templates.id = agents.system_prompt_id
)
WHERE system_prompt_id IS NOT NULL;

-- Rename system_prompt to prompt_text (clearer name)
ALTER TABLE agents 
  RENAME COLUMN system_prompt TO prompt_text;

-- Remove the FK relationship (agents now store snapshots, not references)
ALTER TABLE agents 
  DROP COLUMN IF EXISTS system_prompt_id;

-- Step 5: Clean up templates table (keep only starter templates)
-- Remove unlocked templates created by users
DELETE FROM templates WHERE is_locked = FALSE;

-- Simplify locked templates (keep as starter blueprints)
COMMENT ON TABLE templates IS 'Starter templates for agent creation. These are blueprints that get copied to agents as snapshots.';
COMMENT ON COLUMN agents.prompt_text IS 'Agent prompt snapshot. Edits apply only to this agent.';
COMMENT ON COLUMN agents.template_source IS 'Name of template this agent was created from, for display badge only.';
