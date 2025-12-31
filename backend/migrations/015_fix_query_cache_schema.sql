-- Migration: Fix query_cache table schema
-- Date: 2025-12-02
-- Description: Add missing columns to query_cache table for semantic caching

-- Add sources column (JSONB to store source documents)
ALTER TABLE query_cache ADD COLUMN IF NOT EXISTS sources JSONB DEFAULT '[]'::jsonb;

-- Add ttl_seconds column (Time-to-live in seconds)
ALTER TABLE query_cache ADD COLUMN IF NOT EXISTS ttl_seconds INTEGER DEFAULT 3600;

-- Add last_accessed column (rename from last_accessed_at for consistency with code)
-- First check if last_accessed exists, if not rename last_accessed_at
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'query_cache' AND column_name = 'last_accessed'
    ) THEN
        -- Rename last_accessed_at to last_accessed if it exists
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'query_cache' AND column_name = 'last_accessed_at'
        ) THEN
            ALTER TABLE query_cache RENAME COLUMN last_accessed_at TO last_accessed;
        ELSE
            -- Create last_accessed if neither exists
            ALTER TABLE query_cache ADD COLUMN last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        END IF;
    END IF;
END $$;

-- Create index on ttl_seconds for efficient cache cleanup
CREATE INDEX IF NOT EXISTS idx_query_cache_ttl ON query_cache(created_at, ttl_seconds);

-- Add comments for documentation
COMMENT ON COLUMN query_cache.sources IS 'Source documents used to generate the cached response';
COMMENT ON COLUMN query_cache.ttl_seconds IS 'Time-to-live in seconds for this cache entry';
COMMENT ON COLUMN query_cache.last_accessed IS 'Timestamp when this cache entry was last accessed';

-- Clean up expired cache entries (optional)
DELETE FROM query_cache
WHERE EXTRACT(EPOCH FROM (NOW() - created_at)) > COALESCE(ttl_seconds, 3600);
