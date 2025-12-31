-- Add Multi-Column Vector Storage for Intelligent Embeddings
-- Adds support for content-specific embedding strategies:
-- - table_embedding: Table structure embeddings (512-dim)
-- - visual_embedding: Vision embeddings for images/diagrams (512-dim, CLIP)
-- - numerical_embedding: Numerical/statistical embeddings (256-dim)
-- - code_embedding: Code embeddings (768-dim, CodeBERT)
-- - embedding_strategy: Track which strategy was used
-- - embedding_metadata: Store ContentAnalyzer results

-- Add new vector columns to document_chunks table
ALTER TABLE document_chunks
    ADD COLUMN IF NOT EXISTS table_embedding vector(512),
    ADD COLUMN IF NOT EXISTS visual_embedding vector(512),
    ADD COLUMN IF NOT EXISTS numerical_embedding vector(256),
    ADD COLUMN IF NOT EXISTS code_embedding vector(768);

-- Add embedding metadata columns
ALTER TABLE document_chunks
    ADD COLUMN IF NOT EXISTS embedding_strategy VARCHAR(50),
    ADD COLUMN IF NOT EXISTS embedding_metadata JSONB;

-- Make primary embedding column nullable (for multi-strategy support)
-- Note: This is safe as we're making it MORE flexible
ALTER TABLE document_chunks
    ALTER COLUMN embedding DROP NOT NULL;

-- Create vector indexes for each embedding type
-- Index for table embeddings
CREATE INDEX IF NOT EXISTS idx_chunks_table_embedding
    ON document_chunks
    USING ivfflat (table_embedding vector_cosine_ops)
    WITH (lists = 100);

-- Index for visual embeddings
CREATE INDEX IF NOT EXISTS idx_chunks_visual_embedding
    ON document_chunks
    USING ivfflat (visual_embedding vector_cosine_ops)
    WITH (lists = 100);

-- Index for numerical embeddings
CREATE INDEX IF NOT EXISTS idx_chunks_numerical_embedding
    ON document_chunks
    USING ivfflat (numerical_embedding vector_l2_ops)  -- L2 distance for numerical
    WITH (lists = 100);

-- Index for code embeddings
CREATE INDEX IF NOT EXISTS idx_chunks_code_embedding
    ON document_chunks
    USING ivfflat (code_embedding vector_cosine_ops)
    WITH (lists = 100);

-- Index for embedding_strategy (for fast filtering by strategy type)
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_strategy
    ON document_chunks (embedding_strategy);

-- Add comments to document the columns
COMMENT ON COLUMN document_chunks.embedding IS
    'Primary vector embedding (384 dimensions) using sentence-transformers/all-MiniLM-L6-v2 for text semantic search';

COMMENT ON COLUMN document_chunks.table_embedding IS
    'Table structure embedding (512 dimensions) for table-heavy documents, captures structural and numerical patterns';

COMMENT ON COLUMN document_chunks.visual_embedding IS
    'Vision embedding (512 dimensions) using CLIP for images, diagrams, and charts';

COMMENT ON COLUMN document_chunks.numerical_embedding IS
    'Numerical embedding (256 dimensions) for statistical data in Excel/CSV files';

COMMENT ON COLUMN document_chunks.code_embedding IS
    'Code embedding (768 dimensions) using CodeBERT for programming code semantic search';

COMMENT ON COLUMN document_chunks.embedding_strategy IS
    'Embedding strategy used: text_semantic, table_structure, vision, numerical, code, or hybrid';

COMMENT ON COLUMN document_chunks.embedding_metadata IS
    'Metadata from ContentAnalyzer: content_type, confidence, reasoning, analysis results';

-- Add check constraint for valid strategy values
ALTER TABLE document_chunks
    ADD CONSTRAINT check_embedding_strategy
    CHECK (
        embedding_strategy IS NULL OR
        embedding_strategy IN (
            'text_semantic',
            'table_structure',
            'vision',
            'numerical',
            'code',
            'hybrid'
        )
    );

-- Migration complete
-- Note: Existing rows will have NULL for new columns, which is expected
-- New uploads will populate appropriate columns based on content analysis
