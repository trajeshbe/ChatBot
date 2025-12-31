-- Migration: 003_fix_query_cache_default.sql
-- Description: Add DEFAULT uuid_generate_v4() to query_cache.id column
-- Date: 2025-11-15
--
-- This fixes the error: "null value in column 'id' of relation 'query_cache' violates not-null constraint"
-- The issue occurs when raw SQL INSERT statements don't include the id column,
-- relying on the database DEFAULT which was missing.

-- Add DEFAULT constraint to the id column
ALTER TABLE query_cache
ALTER COLUMN id SET DEFAULT uuid_generate_v4();

-- Verify the change
DO $$
BEGIN
    RAISE NOTICE 'Migration 003 completed: query_cache.id now has DEFAULT uuid_generate_v4()';
END $$;
