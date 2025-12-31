-- Migration: Add default_project_id to users and update projects table
-- Date: 2025-11-28
-- Purpose: Enable "default" project for all users

-- Add department_id and team_id to projects table
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS team_id UUID REFERENCES teams(id) ON DELETE SET NULL;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_projects_department ON projects(department_id);
CREATE INDEX IF NOT EXISTS idx_projects_team ON projects(team_id);

-- Create default projects for existing users
INSERT INTO projects (id, name, description, owner_id, status, created_at, updated_at)
SELECT
    uuid_generate_v4(),
    'Default',
    'Default project for ' || username || '''s files',
    u.id,
    'active',
    NOW(),
    NOW()
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM projects p
    WHERE p.owner_id = u.id
    AND p.name = 'Default'
);

-- Add default_project_id to users table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS default_project_id UUID REFERENCES projects(id) ON DELETE SET NULL;

-- Update users to reference their default projects
UPDATE users u
SET default_project_id = p.id
FROM projects p
WHERE p.owner_id = u.id
AND p.name = 'Default'
AND u.default_project_id IS NULL;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_users_default_project ON users(default_project_id);

-- Create project members for default projects
INSERT INTO project_members (id, project_id, user_id, role, joined_at)
SELECT
    uuid_generate_v4(),
    p.id,
    p.owner_id,
    'owner',
    NOW()
FROM projects p
WHERE p.name = 'Default'
AND NOT EXISTS (
    SELECT 1 FROM project_members pm
    WHERE pm.project_id = p.id
    AND pm.user_id = p.owner_id
);

-- Verify results
SELECT
    'Created ' || COUNT(*) || ' default projects'
FROM projects
WHERE name = 'Default';

SELECT
    'Updated ' || COUNT(*) || ' users with default_project_id'
FROM users
WHERE default_project_id IS NOT NULL;
