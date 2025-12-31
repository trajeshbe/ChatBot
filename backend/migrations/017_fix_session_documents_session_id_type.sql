-- Migration: Fix session_documents.session_id type mismatch
-- Issue: session_id was UUID (pointing to chat_sessions.id)
--        but should be VARCHAR (pointing to chat_sessions.session_id)
-- Date: 2025-12-02

BEGIN;

-- Step 1: Add a temporary column to hold the new VARCHAR session_id values
ALTER TABLE session_documents
ADD COLUMN session_id_new VARCHAR(255);

-- Step 2: Populate the new column by looking up the session_id string from chat_sessions
-- Map: session_documents.session_id (UUID) -> chat_sessions.id -> chat_sessions.session_id (VARCHAR)
UPDATE session_documents sd
SET session_id_new = cs.session_id
FROM chat_sessions cs
WHERE sd.session_id::text = cs.id::text;

-- Step 3: Check if all rows were successfully mapped
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM session_documents WHERE session_id_new IS NULL) THEN
        RAISE EXCEPTION 'Some session_documents rows could not be mapped to chat_sessions.session_id';
    END IF;
END $$;

-- Step 4: Drop the old foreign key constraint
ALTER TABLE session_documents
DROP CONSTRAINT IF EXISTS session_documents_session_id_fkey;

-- Step 5: Drop the old session_id column
ALTER TABLE session_documents
DROP COLUMN session_id;

-- Step 6: Rename the new column to session_id
ALTER TABLE session_documents
RENAME COLUMN session_id_new TO session_id;

-- Step 7: Make the column NOT NULL
ALTER TABLE session_documents
ALTER COLUMN session_id SET NOT NULL;

-- Step 8: Add the corrected foreign key constraint
-- Now references chat_sessions.session_id (VARCHAR) instead of chat_sessions.id (UUID)
ALTER TABLE session_documents
ADD CONSTRAINT session_documents_session_id_fkey
FOREIGN KEY (session_id)
REFERENCES chat_sessions(session_id)
ON DELETE CASCADE;

-- Step 9: Add index for performance
CREATE INDEX IF NOT EXISTS idx_session_documents_session_id
ON session_documents(session_id);

COMMIT;
