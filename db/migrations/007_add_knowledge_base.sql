-- Knowledge Base for RAG (Retrieval Augmented Generation)
-- Allows users to upload documents/data that agents can reference during calls

-- Knowledge Base Documents
CREATE TABLE IF NOT EXISTS knowledge_base (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    source_file VARCHAR(255), -- Original filename if uploaded
    source_url TEXT, -- Original URL if scraped from web
    file_type VARCHAR(50), -- pdf, txt, csv, json, url, etc.
    metadata JSONB DEFAULT '{}', -- tags, categories, domain, word_count, etc.
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add trigger for updated_at
CREATE TRIGGER update_knowledge_base_updated_at BEFORE UPDATE ON knowledge_base
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Index for faster searches
CREATE INDEX IF NOT EXISTS idx_kb_agent_id ON knowledge_base(agent_id);
CREATE INDEX IF NOT EXISTS idx_kb_active ON knowledge_base(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_kb_content_search ON knowledge_base USING gin(to_tsvector('english', content));
CREATE INDEX IF NOT EXISTS idx_kb_source_url ON knowledge_base(source_url) WHERE source_url IS NOT NULL;

COMMENT ON TABLE knowledge_base IS 'Documents and data that agents can reference during calls';
COMMENT ON COLUMN knowledge_base.content IS 'Searchable text content extracted from files or URLs';
COMMENT ON COLUMN knowledge_base.source_url IS 'Original URL if content was scraped from the web';
COMMENT ON COLUMN knowledge_base.metadata IS 'Additional info: tags, summary, category, domain, word_count, etc.';
