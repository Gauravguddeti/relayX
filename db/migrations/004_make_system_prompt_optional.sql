-- Make system_prompt column nullable since agents can now use system_prompt_id instead
-- This allows agents to use prompts from the system_prompts library

ALTER TABLE agents 
ALTER COLUMN system_prompt DROP NOT NULL;

-- Add a check constraint to ensure at least one is provided (either system_prompt or system_prompt_id)
-- Note: This is enforced in application logic, not DB constraint, for better error messages
