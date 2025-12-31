-- Fix Embedding Dimension Mismatch
-- Changes embedding columns from vector(1536) to vector(384)
-- to match sentence-transformers/all-MiniLM-L6-v2 model

-- Drop existing vector indexes
DROP INDEX IF EXISTS idx_document_chunks_embedding;
DROP INDEX IF EXISTS idx_query_cache_embedding;

-- Alter document_chunks table embedding column
-- Note: This will delete existing embeddings if any exist
ALTER TABLE document_chunks
    DROP COLUMN IF EXISTS embedding;

ALTER TABLE document_chunks
    ADD COLUMN embedding vector(384);

-- Alter query_cache table embedding column
-- Note: This will delete existing cached queries
ALTER TABLE query_cache
    DROP COLUMN IF EXISTS query_embedding;

ALTER TABLE query_cache
    ADD COLUMN query_embedding vector(384);

-- Recreate vector indexes with correct dimensions
CREATE INDEX idx_document_chunks_embedding
    ON document_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX idx_query_cache_embedding
    ON query_cache
    USING ivfflat (query_embedding vector_cosine_ops)
    WITH (lists = 100);

-- Add comment to track the change
COMMENT ON COLUMN document_chunks.embedding IS 'Vector embedding (384 dimensions) using sentence-transformers/all-MiniLM-L6-v2';
COMMENT ON COLUMN query_cache.query_embedding IS 'Vector embedding (384 dimensions) using sentence-transformers/all-MiniLM-L6-v2';
