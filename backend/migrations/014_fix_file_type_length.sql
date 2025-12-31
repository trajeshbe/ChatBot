-- Migration: Fix file_type column length for long MIME types
-- Date: 2025-11-30
-- Issue: Microsoft Office files have very long MIME types (e.g., application/vnd.openxmlformats-officedocument.wordprocessingml.document = 74 chars)
-- Previous: VARCHAR(50)
-- Updated: VARCHAR(255)

ALTER TABLE documents
ALTER COLUMN file_type TYPE VARCHAR(255);

-- Verify change
SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns
WHERE table_name = 'documents' AND column_name = 'file_type';
