-- Migration: Add department_id and team_id foreign keys to projects
-- Purpose: Enable hierarchical MinIO path construction and proper organizational structure
-- Related: MINIO_PATH_RECOMMENDATION.md - Support path structure: {dept}/{team}/{project}/{user}/documents/{file}

-- Add department_id foreign key column
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS department_id UUID;

-- Add team_id foreign key column
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS team_id UUID;

-- Add foreign key constraints
ALTER TABLE projects
ADD CONSTRAINT projects_department_id_fkey
FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL;

ALTER TABLE projects
ADD CONSTRAINT projects_team_id_fkey
FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE SET NULL;

-- Add indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_projects_department ON projects(department_id);
CREATE INDEX IF NOT EXISTS idx_projects_team ON projects(team_id);

-- Add comments for documentation
COMMENT ON COLUMN projects.department_id IS 'Foreign key to departments table for organizational hierarchy';
COMMENT ON COLUMN projects.team_id IS 'Foreign key to teams table for organizational hierarchy';

-- Note: Keeping the existing 'department' VARCHAR column for backward compatibility
-- It will be deprecated in future releases in favor of department_id FK
