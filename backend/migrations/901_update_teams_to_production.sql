-- Migration 901: Update Teams to Production State
-- Created: 2026-01-05
-- Purpose: Replace generic team names with actual production team names (28 teams)
-- Dependencies: 900_update_departments_to_production.sql

BEGIN;

-- ============================================================================
-- STEP 1: Delete generic teams created by migration 008
-- ============================================================================
DELETE FROM teams
WHERE name LIKE 'Data Team %'
   OR name LIKE 'Tech Team %'
   OR name IN ('Marketing Team', 'Sales Team', 'HR Team', 'Legacy Team');

-- ============================================================================
-- STEP 2: Insert actual production teams
-- ============================================================================
DO $$
DECLARE
    data_ops_id UUID;
    tech_id UUID;
    support_id UUID;
BEGIN
    -- Get department IDs
    SELECT id INTO data_ops_id FROM departments WHERE name = 'Data Operations' AND is_active = TRUE;
    SELECT id INTO tech_id FROM departments WHERE name = 'Technology' AND is_active = TRUE;
    SELECT id INTO support_id FROM departments WHERE name = 'Support Functions' AND is_active = TRUE;

    -- Data Operations Teams (16 teams)
    INSERT INTO teams (name, description, department_id, is_active) VALUES
        ('Air Business Distribution', NULL, data_ops_id, TRUE),
        ('ALF', NULL, data_ops_id, TRUE),
        ('DMS Construction Data Research', NULL, data_ops_id, TRUE),
        ('DODs', NULL, data_ops_id, TRUE),
        ('Glenigan FRO', NULL, data_ops_id, TRUE),
        ('Haymarket', NULL, data_ops_id, TRUE),
        ('HSJ', NULL, data_ops_id, TRUE),
        ('HSJ On Medica', NULL, data_ops_id, TRUE),
        ('Informa Connect - Data Research', NULL, data_ops_id, TRUE),
        ('Leadership', NULL, data_ops_id, TRUE),
        ('Leadscale', NULL, data_ops_id, TRUE),
        ('LLI Data', NULL, data_ops_id, TRUE),
        ('Political Engagement - Research Support', NULL, data_ops_id, TRUE),
        ('Quality', NULL, data_ops_id, TRUE),
        ('Tactical Data', NULL, data_ops_id, TRUE),
        ('Tactical Data Research', NULL, data_ops_id, TRUE)
    ON CONFLICT (department_id, name) DO NOTHING;

    -- Support Functions Teams (2 teams)
    INSERT INTO teams (name, description, department_id, is_active) VALUES
        ('Marketing', NULL, support_id, TRUE),
        ('Sales', NULL, support_id, TRUE)
    ON CONFLICT (department_id, name) DO NOTHING;

    -- Technology Teams (10 teams)
    INSERT INTO teams (name, description, department_id, is_active) VALUES
        ('Backend Development', 'API and server-side development', tech_id, TRUE),
        ('Frontend Development', 'UI/UX and client-side development', tech_id, TRUE),
        ('ITM1', NULL, tech_id, TRUE),
        ('ITM2', NULL, tech_id, TRUE),
        ('ITM6', NULL, tech_id, TRUE),
        ('ITM7', NULL, tech_id, TRUE),
        ('ITM9', NULL, tech_id, TRUE),
        ('ITM10', NULL, tech_id, TRUE),
        ('ITM11', NULL, tech_id, TRUE),
        ('ITM12', NULL, tech_id, TRUE)
    ON CONFLICT (department_id, name) DO NOTHING;

END $$;

-- ============================================================================
-- STEP 3: Verify production team structure
-- ============================================================================
SELECT
    d.name as department,
    COUNT(t.id) as team_count,
    string_agg(t.name, ', ' ORDER BY t.name) as teams
FROM departments d
LEFT JOIN teams t ON d.id = t.department_id AND t.is_active = TRUE
WHERE d.is_active = TRUE
GROUP BY d.name
ORDER BY d.name;

COMMIT;

-- Expected result:
-- Data Operations: 16 teams
-- Support Functions: 2 teams
-- Technology: 10 teams
-- Total: 28 teams
