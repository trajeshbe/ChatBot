-- Migration: Add organizational fields to users
-- Date: 2025-11-28
-- Purpose: Add department_id, function to users and create user_teams junction table for many-to-many relationship

-- Add organizational fields to users table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS function VARCHAR(100);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_department ON users(department_id);
CREATE INDEX IF NOT EXISTS idx_users_function ON users(function);

-- Create user_teams junction table for many-to-many relationship
CREATE TABLE IF NOT EXISTS user_teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_by UUID REFERENCES users(id) ON DELETE SET NULL,
    is_primary BOOLEAN DEFAULT FALSE,  -- One team can be marked as primary
    UNIQUE(user_id, team_id)
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_user_teams_user ON user_teams(user_id);
CREATE INDEX IF NOT EXISTS idx_user_teams_team ON user_teams(team_id);
CREATE INDEX IF NOT EXISTS idx_user_teams_primary ON user_teams(user_id, is_primary) WHERE is_primary = TRUE;

-- Update existing users to have Technology department as default (optional)
-- This is just for demo purposes - you can remove or modify
UPDATE users u
SET department_id = (SELECT id FROM departments WHERE name = 'Technology' LIMIT 1)
WHERE u.department_id IS NULL;

-- Verify results
SELECT
    'Added organizational fields to ' || COUNT(*) || ' users'
FROM users;

SELECT
    'Created user_teams table'
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_teams');

-- Display sample data
SELECT
    u.username,
    u.function,
    d.name as department
FROM users u
LEFT JOIN departments d ON u.department_id = d.id
LIMIT 5;
