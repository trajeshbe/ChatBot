-- Migration 007: Add Project Tracking with Role/Dept/Team/Username Hierarchy
-- Created: 2025-11-28
-- Purpose: Enable hierarchical file organization and complete traceability
-- MinIO Path: {role}/{department}/{team}/{username}/{project}/{folder}/{file}
-- Related: LIBRARY_AND_PROJECT_MANAGEMENT_IMPLEMENTATION.md

BEGIN;

-- ============================================================================
-- STEP 1: Add team field to users table
-- ============================================================================

ALTER TABLE users
ADD COLUMN IF NOT EXISTS team VARCHAR(100);

CREATE INDEX IF NOT EXISTS idx_users_team ON users(team);
CREATE INDEX IF NOT EXISTS idx_users_department ON users(department);

COMMENT ON COLUMN users.team IS 'Team within department (e.g., Tech Team 1, Data Team 5)';

-- ============================================================================
-- STEP 2: Add team field to projects table
-- ============================================================================

ALTER TABLE projects
ADD COLUMN IF NOT EXISTS team VARCHAR(100);

CREATE INDEX IF NOT EXISTS idx_projects_team ON projects(team);

COMMENT ON COLUMN projects.team IS 'Team this project belongs to';

-- ============================================================================
-- STEP 3: Add project tracking columns to documents table
-- ============================================================================

ALTER TABLE documents
ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS department VARCHAR(100),
ADD COLUMN IF NOT EXISTS team VARCHAR(100),
ADD COLUMN IF NOT EXISTS user_role VARCHAR(50),
ADD COLUMN IF NOT EXISTS minio_path VARCHAR(1024);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents(project_id);
CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by ON documents(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_documents_department ON documents(department);
CREATE INDEX IF NOT EXISTS idx_documents_team ON documents(team);
CREATE INDEX IF NOT EXISTS idx_documents_user_role ON documents(user_role);
CREATE INDEX IF NOT EXISTS idx_documents_minio_path ON documents(minio_path);

-- Add comments
COMMENT ON COLUMN documents.project_id IS 'Project this document belongs to';
COMMENT ON COLUMN documents.uploaded_by IS 'User who uploaded this document';
COMMENT ON COLUMN documents.department IS 'Department of the uploader';
COMMENT ON COLUMN documents.team IS 'Team of the uploader';
COMMENT ON COLUMN documents.user_role IS 'Role of uploader at upload time';
COMMENT ON COLUMN documents.minio_path IS 'Full hierarchical path: role/dept/team/username/project/folder/file';

-- ============================================================================
-- STEP 4: Add project tracking to document_chunks (denormalized for speed)
-- ============================================================================

ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS department VARCHAR(100),
ADD COLUMN IF NOT EXISTS team VARCHAR(100);

CREATE INDEX IF NOT EXISTS idx_chunks_project_id ON document_chunks(project_id);
CREATE INDEX IF NOT EXISTS idx_chunks_uploaded_by ON document_chunks(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_chunks_department ON document_chunks(department);
CREATE INDEX IF NOT EXISTS idx_chunks_team ON document_chunks(team);

COMMENT ON COLUMN document_chunks.project_id IS 'Project (denormalized for fast RAG queries)';
COMMENT ON COLUMN document_chunks.department IS 'Department (denormalized for access control)';
COMMENT ON COLUMN document_chunks.team IS 'Team (denormalized for team-scoped RAG)';

-- ============================================================================
-- STEP 5: Add project tracking to chat_sessions
-- ============================================================================

ALTER TABLE chat_sessions
ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS department VARCHAR(100),
ADD COLUMN IF NOT EXISTS team VARCHAR(100);

CREATE INDEX IF NOT EXISTS idx_sessions_project_id ON chat_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_sessions_department ON chat_sessions(department);
CREATE INDEX IF NOT EXISTS idx_sessions_team ON chat_sessions(team);

COMMENT ON COLUMN chat_sessions.project_id IS 'Project context for this chat session';
COMMENT ON COLUMN chat_sessions.department IS 'Department context';
COMMENT ON COLUMN chat_sessions.team IS 'Team context';

-- ============================================================================
-- STEP 6: Add project tracking to conversations
-- ============================================================================

ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS title VARCHAR(255),
ADD COLUMN IF NOT EXISTS summary TEXT;

CREATE INDEX IF NOT EXISTS idx_conversations_project_id ON conversations(project_id);

COMMENT ON COLUMN conversations.project_id IS 'Project context for this conversation';
COMMENT ON COLUMN conversations.title IS 'Auto-generated or user-defined conversation title';
COMMENT ON COLUMN conversations.summary IS 'Brief summary of conversation topics';

-- ============================================================================
-- STEP 7: Add project tracking to web_scrape_jobs
-- ============================================================================

ALTER TABLE web_scrape_jobs
ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS scraped_by UUID REFERENCES users(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS department VARCHAR(100),
ADD COLUMN IF NOT EXISTS team VARCHAR(100);

CREATE INDEX IF NOT EXISTS idx_scrape_jobs_project_id ON web_scrape_jobs(project_id);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_scraped_by ON web_scrape_jobs(scraped_by);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_department ON web_scrape_jobs(department);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_team ON web_scrape_jobs(team);

COMMENT ON COLUMN web_scrape_jobs.project_id IS 'Project this scrape job belongs to';
COMMENT ON COLUMN web_scrape_jobs.scraped_by IS 'User who initiated the scrape';

-- ============================================================================
-- STEP 8: Create default project for existing data (migration safety)
-- ============================================================================

DO $$
DECLARE
    legacy_project_id UUID;
    admin_user_id UUID;
BEGIN
    -- Try to get admin user
    SELECT id INTO admin_user_id FROM users WHERE role = 'admin' LIMIT 1;

    -- If no admin exists, use first user
    IF admin_user_id IS NULL THEN
        SELECT id INTO admin_user_id FROM users LIMIT 1;
    END IF;

    -- Create legacy project if it doesn't exist
    INSERT INTO projects (id, name, description, owner_id, department, team, status, meta_info)
    VALUES (
        uuid_generate_v4(),
        'Legacy/Uncategorized',
        'Auto-generated project for existing documents uploaded before project management was implemented',
        admin_user_id,
        'General',
        'Legacy',
        'active',
        '{"auto_generated": true, "legacy": true}'::jsonb
    )
    ON CONFLICT DO NOTHING
    RETURNING id INTO legacy_project_id;

    -- If project already exists, get its ID
    IF legacy_project_id IS NULL THEN
        SELECT id INTO legacy_project_id FROM projects WHERE name = 'Legacy/Uncategorized';
    END IF;

    -- Update existing documents without project_id
    UPDATE documents
    SET
        project_id = legacy_project_id,
        department = 'General',
        team = 'Legacy',
        user_role = 'user'
    WHERE project_id IS NULL;

    -- Update existing document_chunks without project_id
    UPDATE document_chunks dc
    SET
        project_id = d.project_id,
        uploaded_by = d.uploaded_by,
        department = d.department,
        team = d.team
    FROM documents d
    WHERE dc.document_id = d.id
    AND dc.project_id IS NULL;

    RAISE NOTICE 'Legacy project created and existing data migrated: %', legacy_project_id;
END $$;

-- ============================================================================
-- STEP 9: Create enriched file library view
-- ============================================================================

CREATE OR REPLACE VIEW file_library AS
SELECT
    d.id,
    d.filename,
    d.file_path,
    d.minio_path,
    d.file_type,
    d.file_size,
    d.upload_date,
    d.processed,
    d.source_type,
    d.source_url,

    -- Hierarchical organization
    d.user_role,
    d.department,
    d.team,

    -- Project info
    p.id AS project_id,
    p.name AS project_name,
    p.description AS project_description,
    p.status AS project_status,

    -- User info
    u.id AS uploaded_by_id,
    u.username AS uploaded_by_username,
    u.email AS uploaded_by_email,
    u.role AS current_user_role,

    -- Chunk stats
    COUNT(dc.id) AS chunk_count,
    BOOL_OR(dc.embedding IS NOT NULL) AS has_embeddings,

    -- Processing status
    CASE
        WHEN d.processing_error IS NOT NULL THEN 'failed'
        WHEN d.processed = FALSE THEN 'processing'
        WHEN d.processed = TRUE AND COUNT(dc.id) > 0 THEN 'completed'
        ELSE 'pending'
    END AS processing_status,

    -- Path components for easy filtering
    SPLIT_PART(d.minio_path, '/', 1) AS path_role,
    SPLIT_PART(d.minio_path, '/', 2) AS path_department,
    SPLIT_PART(d.minio_path, '/', 3) AS path_team,
    SPLIT_PART(d.minio_path, '/', 4) AS path_username,
    SPLIT_PART(d.minio_path, '/', 5) AS path_project,
    SPLIT_PART(d.minio_path, '/', 6) AS path_folder

FROM documents d
LEFT JOIN projects p ON d.project_id = p.id
LEFT JOIN users u ON d.uploaded_by = u.id
LEFT JOIN document_chunks dc ON d.id = dc.document_id
GROUP BY
    d.id, d.filename, d.file_path, d.minio_path, d.file_type,
    d.file_size, d.upload_date, d.processed, d.source_type, d.source_url,
    d.user_role, d.department, d.team,
    p.id, p.name, p.description, p.status,
    u.id, u.username, u.email, u.role;

COMMENT ON VIEW file_library IS 'Enriched view of all files with hierarchical organization and metadata';

-- ============================================================================
-- STEP 10: Create storage statistics functions
-- ============================================================================

CREATE OR REPLACE FUNCTION get_user_storage_stats(user_uuid UUID)
RETURNS TABLE(
    total_files BIGINT,
    total_size BIGINT,
    total_chunks BIGINT,
    by_project JSON,
    by_team JSON
) AS $$
BEGIN
    RETURN QUERY
    WITH project_stats AS (
        SELECT
            p.id,
            p.name,
            p.team,
            COUNT(d.id) AS file_count,
            COALESCE(SUM(d.file_size), 0) AS total_size,
            COUNT(dc.id) AS chunk_count
        FROM projects p
        LEFT JOIN documents d ON d.project_id = p.id AND d.uploaded_by = user_uuid
        LEFT JOIN document_chunks dc ON dc.document_id = d.id
        WHERE p.owner_id = user_uuid OR d.uploaded_by = user_uuid
        GROUP BY p.id, p.name, p.team
    ),
    team_stats AS (
        SELECT
            d.team,
            COUNT(d.id) AS file_count,
            COALESCE(SUM(d.file_size), 0) AS total_size
        FROM documents d
        WHERE d.uploaded_by = user_uuid
        GROUP BY d.team
    )
    SELECT
        (SELECT COUNT(*) FROM documents WHERE uploaded_by = user_uuid)::BIGINT,
        (SELECT COALESCE(SUM(file_size), 0) FROM documents WHERE uploaded_by = user_uuid)::BIGINT,
        (SELECT COUNT(*) FROM document_chunks WHERE uploaded_by = user_uuid)::BIGINT,
        (SELECT json_agg(row_to_json(project_stats.*)) FROM project_stats),
        (SELECT json_agg(row_to_json(team_stats.*)) FROM team_stats)
    ;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_user_storage_stats IS 'Get storage statistics for a specific user';

-- ============================================================================
-- STEP 11: Create department/team statistics view
-- ============================================================================

CREATE OR REPLACE VIEW department_team_statistics AS
SELECT
    d.department,
    d.team,

    -- File statistics
    COUNT(DISTINCT d.id) AS total_files,
    COALESCE(SUM(d.file_size), 0) AS total_storage_bytes,
    COUNT(DISTINCT CASE WHEN d.processed = TRUE THEN d.id END) AS processed_files,

    -- Project statistics
    COUNT(DISTINCT d.project_id) AS total_projects,

    -- User statistics
    COUNT(DISTINCT d.uploaded_by) AS unique_users,

    -- Activity
    MAX(d.upload_date) AS last_upload_date,
    MIN(d.upload_date) AS first_upload_date

FROM documents d
WHERE d.department IS NOT NULL
GROUP BY d.department, d.team
ORDER BY d.department, d.team;

COMMENT ON VIEW department_team_statistics IS 'Statistics grouped by department and team';

-- ============================================================================
-- STEP 12: Create project statistics view
-- ============================================================================

CREATE OR REPLACE VIEW project_statistics AS
SELECT
    p.id AS project_id,
    p.name AS project_name,
    p.department,
    p.team,
    p.status,
    p.created_at,
    p.updated_at,

    -- File statistics
    COUNT(DISTINCT d.id) AS total_files,
    COALESCE(SUM(d.file_size), 0) AS total_storage_bytes,
    COUNT(DISTINCT CASE WHEN d.processed = TRUE THEN d.id END) AS processed_files,
    COUNT(DISTINCT CASE WHEN d.processed = FALSE THEN d.id END) AS pending_files,

    -- Chunk statistics
    COUNT(DISTINCT dc.id) AS total_chunks,
    COUNT(DISTINCT CASE WHEN dc.embedding IS NOT NULL THEN dc.id END) AS embedded_chunks,

    -- Session statistics
    COUNT(DISTINCT cs.id) AS total_sessions,
    COUNT(DISTINCT conv.id) AS total_conversations,

    -- User statistics
    COUNT(DISTINCT d.uploaded_by) AS unique_uploaders,

    -- Recent activity
    MAX(d.upload_date) AS last_upload_date,
    MAX(cs.last_activity) AS last_session_activity

FROM projects p
LEFT JOIN documents d ON d.project_id = p.id
LEFT JOIN document_chunks dc ON dc.document_id = d.id
LEFT JOIN chat_sessions cs ON cs.project_id = p.id
LEFT JOIN conversations conv ON conv.project_id = p.id
GROUP BY p.id, p.name, p.department, p.team, p.status, p.created_at, p.updated_at;

COMMENT ON VIEW project_statistics IS 'Comprehensive statistics for each project';

-- ============================================================================
-- STEP 13: Create trigger to auto-populate chunk metadata
-- ============================================================================

CREATE OR REPLACE FUNCTION sync_chunk_project_info()
RETURNS TRIGGER AS $$
BEGIN
    -- Auto-populate project info from parent document
    SELECT
        project_id,
        uploaded_by,
        department,
        team
    INTO
        NEW.project_id,
        NEW.uploaded_by,
        NEW.department,
        NEW.team
    FROM documents
    WHERE id = NEW.document_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_chunk_project_info ON document_chunks;
CREATE TRIGGER trg_sync_chunk_project_info
    BEFORE INSERT ON document_chunks
    FOR EACH ROW
    EXECUTE FUNCTION sync_chunk_project_info();

COMMENT ON FUNCTION sync_chunk_project_info IS 'Auto-populate hierarchical metadata in chunks from parent document';

-- ============================================================================
-- STEP 14: Create indexes for hierarchical queries
-- ============================================================================

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_documents_dept_team ON documents(department, team);
CREATE INDEX IF NOT EXISTS idx_documents_dept_team_user ON documents(department, team, uploaded_by);
CREATE INDEX IF NOT EXISTS idx_documents_role_dept ON documents(user_role, department);
CREATE INDEX IF NOT EXISTS idx_documents_project_user ON documents(project_id, uploaded_by);
CREATE INDEX IF NOT EXISTS idx_documents_user_date ON documents(uploaded_by, upload_date DESC);
CREATE INDEX IF NOT EXISTS idx_documents_project_date ON documents(project_id, upload_date DESC);

-- Chunks hierarchical queries
CREATE INDEX IF NOT EXISTS idx_chunks_dept_team ON document_chunks(department, team);
CREATE INDEX IF NOT EXISTS idx_chunks_project_user ON document_chunks(project_id, uploaded_by);

-- Full-text search on filename (requires pg_trgm extension)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS idx_documents_filename_trgm ON documents USING gin(filename gin_trgm_ops);

-- ============================================================================
-- STEP 15: Create helper function to build MinIO paths
-- ============================================================================

CREATE OR REPLACE FUNCTION build_minio_path(
    p_role VARCHAR,
    p_department VARCHAR,
    p_team VARCHAR,
    p_username VARCHAR,
    p_project_name VARCHAR,
    p_folder VARCHAR,
    p_filename VARCHAR
) RETURNS VARCHAR AS $$
DECLARE
    v_path VARCHAR;
BEGIN
    -- Sanitize components (lowercase, replace spaces with hyphens)
    v_path :=
        LOWER(REGEXP_REPLACE(p_role, '[^a-zA-Z0-9_-]', '', 'g')) || '/' ||
        LOWER(REGEXP_REPLACE(p_department, '\s+', '-', 'g')) || '/' ||
        LOWER(REGEXP_REPLACE(p_team, '\s+', '-', 'g')) || '/' ||
        LOWER(p_username) || '/' ||
        LOWER(REGEXP_REPLACE(p_project_name, '\s+', '-', 'g')) || '/' ||
        p_folder || '/' ||
        p_filename;

    RETURN v_path;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION build_minio_path IS 'Build hierarchical MinIO path: role/dept/team/username/project/folder/file';

-- ============================================================================
-- Finalize migration
-- ============================================================================

COMMIT;

-- ============================================================================
-- Post-migration verification queries (run manually to verify)
-- ============================================================================

-- Verify all documents have projects
-- SELECT COUNT(*) AS docs_without_project FROM documents WHERE project_id IS NULL;

-- Verify hierarchical fields populated
-- SELECT COUNT(*) AS docs_without_hierarchy
-- FROM documents
-- WHERE department IS NULL OR team IS NULL OR user_role IS NULL;

-- Check file_library view
-- SELECT * FROM file_library LIMIT 5;

-- Check department/team statistics
-- SELECT * FROM department_team_statistics;

-- Check project statistics
-- SELECT * FROM project_statistics;

-- Test MinIO path builder
-- SELECT build_minio_path('admin', 'Technology', 'Tech Team 1', 'john.doe', 'ChatBot RAG', 'documents', 'requirements.pdf');
-- Expected: admin/technology/tech-team-1/john.doe/chatbot-rag/documents/requirements.pdf
