-- Migration: Create default Global project
-- Purpose: Ensure a Global project exists for documents not assigned to specific projects
-- Date: 2025-12-01

-- Create default Global project if it doesn't exist
-- Assign to first admin user if exists, otherwise leave NULL for system-wide access
INSERT INTO projects (id, name, description, owner_id, created_at, updated_at)
SELECT
    gen_random_uuid(),
    'Global',
    'Default global project for documents not assigned to specific projects',
    (SELECT id FROM users WHERE role = 'admin' ORDER BY created_at LIMIT 1),  -- Assign to first admin
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM projects WHERE name = 'Global'
);

-- Update orphaned documents (with NULL project_id) to belong to Global project
-- This ensures all existing documents are associated with a project
UPDATE documents
SET project_id = (SELECT id FROM projects WHERE name = 'Global' LIMIT 1)
WHERE project_id IS NULL;

-- Ensure all document chunks also have the correct project_id
-- (in case document_chunks table has project_id field)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'document_chunks' AND column_name = 'project_id'
    ) THEN
        UPDATE document_chunks dc
        SET project_id = d.project_id
        FROM documents d
        WHERE dc.document_id = d.id
        AND dc.project_id IS NULL;
    END IF;
END $$;

-- Add all users as members of the Global project
-- This ensures every user has access to Global by default
INSERT INTO project_members (id, project_id, user_id, role, joined_at)
SELECT
    uuid_generate_v4(),
    (SELECT id FROM projects WHERE name = 'Global' LIMIT 1),
    u.id,
    'member',
    NOW()
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM project_members pm
    WHERE pm.project_id = (SELECT id FROM projects WHERE name = 'Global' LIMIT 1)
    AND pm.user_id = u.id
);

-- Create index on documents.project_id for faster filtering
CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents(project_id);

-- Create index on document_chunks.project_id if column exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'document_chunks' AND column_name = 'project_id'
    ) THEN
        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_document_chunks_project_id ON document_chunks(project_id)';
    END IF;
END $$;
