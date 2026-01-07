-- ============================================================================
-- PostgreSQL Extensions
-- ============================================================================
--
-- Purpose: Install required PostgreSQL extensions for the application
--
-- Extensions:
--   1. uuid-ossp  - UUID generation functions
--   2. vector     - pgvector for embedding storage and similarity search
--
-- Dependencies: None (must be first)
--
-- Idempotent: Yes (CREATE EXTENSION IF NOT EXISTS)
--
-- ============================================================================

-- UUID Generation (uuid_generate_v4())
CREATE EXTENSION IF NOT EXISTS "uuid-ossp"
    SCHEMA public
    VERSION '1.1';

COMMENT ON EXTENSION "uuid-ossp" IS 'UUID generation functions (uuid_generate_v4)';

-- pgvector for Embedding Storage
CREATE EXTENSION IF NOT EXISTS vector
    SCHEMA public;

COMMENT ON EXTENSION vector IS 'Vector similarity search for embeddings (VECTOR data type, cosine similarity)';

-- Verify installations
DO $$
DECLARE
    uuid_ext_version TEXT;
    vector_ext_version TEXT;
BEGIN
    -- Check uuid-ossp
    SELECT extversion INTO uuid_ext_version
    FROM pg_extension
    WHERE extname = 'uuid-ossp';

    IF uuid_ext_version IS NULL THEN
        RAISE EXCEPTION 'uuid-ossp extension not installed';
    END IF;

    -- Check vector
    SELECT extversion INTO vector_ext_version
    FROM pg_extension
    WHERE extname = 'vector';

    IF vector_ext_version IS NULL THEN
        RAISE EXCEPTION 'vector extension not installed';
    END IF;

    RAISE NOTICE '✓ uuid-ossp version: %', uuid_ext_version;
    RAISE NOTICE '✓ vector version: %', vector_ext_version;
END
$$;
