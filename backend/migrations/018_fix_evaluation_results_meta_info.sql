-- Migration: Fix evaluation_results meta_info column
-- Description: Rename metadata column to meta_info for consistency
-- Date: 2025-12-06
-- Version: 018

-- Fix: Rename metadata to meta_info if it exists
-- This handles cases where the table was created with the old migration
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'evaluation_results'
        AND column_name = 'metadata'
    ) THEN
        ALTER TABLE evaluation_results RENAME COLUMN metadata TO meta_info;
        RAISE NOTICE 'Renamed evaluation_results.metadata to meta_info';
    ELSE
        RAISE NOTICE 'Column metadata does not exist, skipping rename';
    END IF;
END $$;

-- Verify the column exists (create if missing)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'evaluation_results'
        AND column_name = 'meta_info'
    ) THEN
        ALTER TABLE evaluation_results ADD COLUMN meta_info JSONB;
        RAISE NOTICE 'Created meta_info column';
    ELSE
        RAISE NOTICE 'Column meta_info already exists';
    END IF;
END $$;
