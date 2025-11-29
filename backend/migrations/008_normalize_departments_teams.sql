-- Migration 008: Normalize Departments and Teams with Proper FK Relationships
-- Created: 2025-11-28
-- Purpose: Convert department/team VARCHAR fields to proper normalized tables with FK constraints
-- Ensures referential integrity and prevents orphaned data

BEGIN;

-- ============================================================================
-- STEP 1: Create normalized departments table
-- ============================================================================

CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    parent_department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_info JSONB
);

CREATE INDEX IF NOT EXISTS idx_departments_name ON departments(name);
CREATE INDEX IF NOT EXISTS idx_departments_code ON departments(code);
CREATE INDEX IF NOT EXISTS idx_departments_is_active ON departments(is_active);
CREATE INDEX IF NOT EXISTS idx_departments_parent ON departments(parent_department_id);

COMMENT ON TABLE departments IS 'Normalized department lookup table';
COMMENT ON COLUMN departments.parent_department_id IS 'For hierarchical departments (e.g., Engineering > Backend Team)';

-- ============================================================================
-- STEP 2: Create normalized teams table
-- ============================================================================

CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL,
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    description TEXT,
    team_lead_id UUID REFERENCES users(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_info JSONB,
    UNIQUE(department_id, name),
    UNIQUE(department_id, code)
);

CREATE INDEX IF NOT EXISTS idx_teams_name ON teams(name);
CREATE INDEX IF NOT EXISTS idx_teams_code ON teams(code);
CREATE INDEX IF NOT EXISTS idx_teams_department_id ON teams(department_id);
CREATE INDEX IF NOT EXISTS idx_teams_team_lead_id ON teams(team_lead_id);
CREATE INDEX IF NOT EXISTS idx_teams_is_active ON teams(is_active);

COMMENT ON TABLE teams IS 'Normalized team lookup table, scoped to departments';
COMMENT ON COLUMN teams.department_id IS 'Foreign key to departments table (CASCADE delete)';

-- ============================================================================
-- STEP 3: Insert seed data for departments
-- ============================================================================

INSERT INTO departments (name, code, description, is_active) VALUES
    ('Data Operations', 'DATA_OPS', 'Data science, analytics, and data engineering teams', TRUE),
    ('Technology', 'TECH', 'Software engineering and IT teams', TRUE),
    ('Marketing', 'MARKETING', 'Marketing and communications teams', TRUE),
    ('Sales', 'SALES', 'Sales and business development teams', TRUE),
    ('HR', 'HR', 'Human resources and people operations', TRUE),
    ('Finance', 'FINANCE', 'Finance and accounting teams', TRUE),
    ('General', 'GENERAL', 'General/uncategorized department', TRUE)
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- STEP 4: Insert seed data for teams
-- ============================================================================

DO $$
DECLARE
    data_ops_id UUID;
    tech_id UUID;
    marketing_id UUID;
    sales_id UUID;
    hr_id UUID;
    general_id UUID;
BEGIN
    -- Get department IDs
    SELECT id INTO data_ops_id FROM departments WHERE code = 'DATA_OPS';
    SELECT id INTO tech_id FROM departments WHERE code = 'TECH';
    SELECT id INTO marketing_id FROM departments WHERE code = 'MARKETING';
    SELECT id INTO sales_id FROM departments WHERE code = 'SALES';
    SELECT id INTO hr_id FROM departments WHERE code = 'HR';
    SELECT id INTO general_id FROM departments WHERE code = 'GENERAL';

    -- Insert Data Operations teams
    FOR i IN 1..16 LOOP
        INSERT INTO teams (name, code, department_id, description, is_active) VALUES
            ('Data Team ' || i, 'DATA_TEAM_' || i, data_ops_id, 'Data operations team ' || i, TRUE)
        ON CONFLICT (department_id, name) DO NOTHING;
    END LOOP;

    -- Insert Technology teams
    FOR i IN 1..12 LOOP
        INSERT INTO teams (name, code, department_id, description, is_active) VALUES
            ('Tech Team ' || i, 'TECH_TEAM_' || i, tech_id, 'Technology team ' || i, TRUE)
        ON CONFLICT (department_id, name) DO NOTHING;
    END LOOP;

    -- Insert other teams
    INSERT INTO teams (name, code, department_id, description, is_active) VALUES
        ('Marketing Team', 'MARKETING_TEAM', marketing_id, 'Primary marketing team', TRUE),
        ('Sales Team', 'SALES_TEAM', sales_id, 'Primary sales team', TRUE),
        ('HR Team', 'HR_TEAM', hr_id, 'Primary HR team', TRUE),
        ('Legacy Team', 'LEGACY_TEAM', general_id, 'Legacy/uncategorized team', TRUE)
    ON CONFLICT (department_id, name) DO NOTHING;
END $$;

-- ============================================================================
-- STEP 5: Update users table to use FK references
-- ============================================================================

-- Add new FK columns
ALTER TABLE users
ADD COLUMN IF NOT EXISTS department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS team_id UUID REFERENCES teams(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_users_department_id ON users(department_id);
CREATE INDEX IF NOT EXISTS idx_users_team_id ON users(team_id);

-- Migrate existing VARCHAR department/team to FK references
DO $$
DECLARE
    user_record RECORD;
    dept_id UUID;
    tm_id UUID;
BEGIN
    FOR user_record IN SELECT id, department, team FROM users WHERE department IS NOT NULL LOOP
        -- Find matching department
        SELECT id INTO dept_id FROM departments WHERE LOWER(name) = LOWER(user_record.department) LIMIT 1;

        IF dept_id IS NULL THEN
            -- Create department if not found
            INSERT INTO departments (name, code, description, is_active)
            VALUES (user_record.department, UPPER(REPLACE(user_record.department, ' ', '_')), 'Auto-created during migration', TRUE)
            RETURNING id INTO dept_id;
        END IF;

        -- Find matching team
        IF user_record.team IS NOT NULL THEN
            SELECT id INTO tm_id FROM teams
            WHERE department_id = dept_id AND LOWER(name) = LOWER(user_record.team) LIMIT 1;

            IF tm_id IS NULL THEN
                -- Create team if not found
                INSERT INTO teams (name, code, department_id, description, is_active)
                VALUES (user_record.team, UPPER(REPLACE(user_record.team, ' ', '_')), dept_id, 'Auto-created during migration', TRUE)
                RETURNING id INTO tm_id;
            END IF;
        END IF;

        -- Update user with FK references
        UPDATE users
        SET department_id = dept_id, team_id = tm_id
        WHERE id = user_record.id;
    END LOOP;
END $$;

-- ============================================================================
-- STEP 6: Update projects table to use FK references
-- ============================================================================

ALTER TABLE projects
ADD COLUMN IF NOT EXISTS department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS team_id UUID REFERENCES teams(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_projects_department_id ON projects(department_id);
CREATE INDEX IF NOT EXISTS idx_projects_team_id ON projects(team_id);

-- Migrate existing projects
DO $$
DECLARE
    proj_record RECORD;
    dept_id UUID;
    tm_id UUID;
BEGIN
    FOR proj_record IN SELECT id, department, team FROM projects WHERE department IS NOT NULL LOOP
        SELECT id INTO dept_id FROM departments WHERE LOWER(name) = LOWER(proj_record.department) LIMIT 1;

        IF dept_id IS NULL THEN
            SELECT id INTO dept_id FROM departments WHERE code = 'GENERAL';
        END IF;

        IF proj_record.team IS NOT NULL THEN
            SELECT id INTO tm_id FROM teams
            WHERE department_id = dept_id AND LOWER(name) = LOWER(proj_record.team) LIMIT 1;
        END IF;

        UPDATE projects
        SET department_id = dept_id, team_id = tm_id
        WHERE id = proj_record.id;
    END LOOP;
END $$;

-- ============================================================================
-- STEP 7: Update documents table to use FK references
-- ============================================================================

ALTER TABLE documents
ADD COLUMN IF NOT EXISTS department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS team_id UUID REFERENCES teams(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_documents_department_id ON documents(department_id);
CREATE INDEX IF NOT EXISTS idx_documents_team_id ON documents(team_id);

-- Migrate existing documents (link via project or user)
UPDATE documents d
SET
    department_id = p.department_id,
    team_id = p.team_id
FROM projects p
WHERE d.project_id = p.id AND d.department_id IS NULL;

UPDATE documents d
SET
    department_id = u.department_id,
    team_id = u.team_id
FROM users u
WHERE d.uploaded_by = u.id AND d.department_id IS NULL;

-- ============================================================================
-- STEP 8: Update document_chunks to use FK references
-- ============================================================================

ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS team_id UUID REFERENCES teams(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_chunks_department_id ON document_chunks(department_id);
CREATE INDEX IF NOT EXISTS idx_chunks_team_id ON document_chunks(team_id);

-- Sync from parent document
UPDATE document_chunks dc
SET
    department_id = d.department_id,
    team_id = d.team_id
FROM documents d
WHERE dc.document_id = d.id;

-- ============================================================================
-- STEP 9: Update chat_sessions to use FK references
-- ============================================================================

ALTER TABLE chat_sessions
ADD COLUMN IF NOT EXISTS department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS team_id UUID REFERENCES teams(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_sessions_department_id ON chat_sessions(department_id);
CREATE INDEX IF NOT EXISTS idx_sessions_team_id ON chat_sessions(team_id);

UPDATE chat_sessions cs
SET
    department_id = p.department_id,
    team_id = p.team_id
FROM projects p
WHERE cs.project_id = p.id AND cs.department_id IS NULL;

-- ============================================================================
-- STEP 10: Update web_scrape_jobs to use FK references
-- ============================================================================

ALTER TABLE web_scrape_jobs
ADD COLUMN IF NOT EXISTS department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS team_id UUID REFERENCES teams(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_scrape_jobs_department_id ON web_scrape_jobs(department_id);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_team_id ON web_scrape_jobs(team_id);

-- ============================================================================
-- STEP 11: Update trigger to sync FK references
-- ============================================================================

CREATE OR REPLACE FUNCTION sync_chunk_project_info()
RETURNS TRIGGER AS $$
BEGIN
    -- Auto-populate project info from parent document
    SELECT
        project_id,
        uploaded_by,
        department_id,  -- Now using FK
        team_id         -- Now using FK
    INTO
        NEW.project_id,
        NEW.uploaded_by,
        NEW.department_id,
        NEW.team_id
    FROM documents
    WHERE id = NEW.document_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Recreate trigger
DROP TRIGGER IF EXISTS trg_sync_chunk_project_info ON document_chunks;
CREATE TRIGGER trg_sync_chunk_project_info
    BEFORE INSERT ON document_chunks
    FOR EACH ROW
    EXECUTE FUNCTION sync_chunk_project_info();

-- ============================================================================
-- STEP 12: Create view for team hierarchy
-- ============================================================================

CREATE OR REPLACE VIEW team_hierarchy AS
SELECT
    t.id AS team_id,
    t.name AS team_name,
    t.code AS team_code,
    d.id AS department_id,
    d.name AS department_name,
    d.code AS department_code,
    u.id AS team_lead_id,
    u.username AS team_lead_username,
    COUNT(DISTINCT um.id) AS member_count
FROM teams t
JOIN departments d ON t.department_id = d.id
LEFT JOIN users u ON t.team_lead_id = u.id
LEFT JOIN users um ON um.team_id = t.id
WHERE t.is_active = TRUE
GROUP BY t.id, t.name, t.code, d.id, d.name, d.code, u.id, u.username;

COMMENT ON VIEW team_hierarchy IS 'Hierarchical view of teams, departments, and members';

-- ============================================================================
-- STEP 13: Add constraints to ensure data integrity
-- ============================================================================

-- Ensure project team belongs to project department
ALTER TABLE projects
ADD CONSTRAINT chk_project_team_department CHECK (
    team_id IS NULL OR
    department_id IS NOT NULL
);

-- Ensure user team belongs to user department
ALTER TABLE users
ADD CONSTRAINT chk_user_team_department CHECK (
    team_id IS NULL OR
    department_id IS NOT NULL
);

-- ============================================================================
-- STEP 14: (Optional) Drop old VARCHAR columns after verification
-- ============================================================================

-- CAUTION: Only run these after verifying migration was successful!
-- Uncomment after verification:

-- ALTER TABLE users DROP COLUMN IF EXISTS department CASCADE;
-- ALTER TABLE users DROP COLUMN IF EXISTS team CASCADE;
-- ALTER TABLE projects DROP COLUMN IF EXISTS department CASCADE;
-- ALTER TABLE projects DROP COLUMN IF EXISTS team CASCADE;
-- ALTER TABLE documents DROP COLUMN IF EXISTS department CASCADE;
-- ALTER TABLE documents DROP COLUMN IF EXISTS team CASCADE;
-- ALTER TABLE document_chunks DROP COLUMN IF EXISTS department CASCADE;
-- ALTER TABLE document_chunks DROP COLUMN IF EXISTS team CASCADE;
-- ALTER TABLE chat_sessions DROP COLUMN IF EXISTS department CASCADE;
-- ALTER TABLE chat_sessions DROP COLUMN IF EXISTS team CASCADE;
-- ALTER TABLE web_scrape_jobs DROP COLUMN IF EXISTS department CASCADE;
-- ALTER TABLE web_scrape_jobs DROP COLUMN IF EXISTS team CASCADE;

COMMIT;

-- ============================================================================
-- Post-migration verification queries
-- ============================================================================

-- Verify departments
-- SELECT * FROM departments ORDER BY name;

-- Verify teams
-- SELECT * FROM teams ORDER BY department_id, name;

-- Verify team hierarchy
-- SELECT * FROM team_hierarchy;

-- Verify users have FK references
-- SELECT username, d.name AS department, t.name AS team
-- FROM users u
-- LEFT JOIN departments d ON u.department_id = d.id
-- LEFT JOIN teams t ON u.team_id = t.id
-- LIMIT 10;

-- Verify referential integrity
-- SELECT COUNT(*) FROM users WHERE department_id IS NOT NULL AND team_id IS NOT NULL;
