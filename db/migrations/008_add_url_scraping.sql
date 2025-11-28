-- Add source_url column to knowledge_base table
-- This migration adds URL scraping support to the knowledge base

-- Add the source_url column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'knowledge_base' 
        AND column_name = 'source_url'
    ) THEN
        ALTER TABLE knowledge_base 
        ADD COLUMN source_url TEXT;
        
        -- Create index for URL lookups
        CREATE INDEX IF NOT EXISTS idx_kb_source_url 
        ON knowledge_base(source_url) 
        WHERE source_url IS NOT NULL;
        
        -- Add comment
        COMMENT ON COLUMN knowledge_base.source_url IS 'Original URL if content was scraped from the web';
        
        RAISE NOTICE 'Added source_url column to knowledge_base table';
    ELSE
        RAISE NOTICE 'Column source_url already exists in knowledge_base table';
    END IF;
END $$;
