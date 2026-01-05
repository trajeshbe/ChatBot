-- Migration 900: Update Departments to Production State
-- Created: 2026-01-05
-- Purpose: Fix department structure to match production (3 departments instead of 7)
-- Dependencies: 008_normalize_departments_teams.sql

BEGIN;

-- ============================================================================
-- STEP 1: Deactivate departments not in production
-- ============================================================================
UPDATE departments
SET is_active = FALSE
WHERE name NOT IN ('Data Operations', 'Technology', 'Support Functions');

-- ============================================================================
-- STEP 2: Ensure the 3 production departments exist
-- ============================================================================
INSERT INTO departments (name, description, is_active) VALUES
    ('Data Operations', 'Data research and operations teams', TRUE),
    ('Technology', 'Technology and IT teams', TRUE),
    ('Support Functions', 'Support, marketing, sales, and HR', TRUE)
ON CONFLICT (name) DO UPDATE
SET
    description = EXCLUDED.description,
    is_active = TRUE;

-- ============================================================================
-- STEP 3: Verify production department structure
-- ============================================================================
SELECT
    name,
    description,
    is_active,
    (SELECT COUNT(*) FROM teams WHERE department_id = departments.id) as team_count
FROM departments
WHERE is_active = TRUE
ORDER BY name;

COMMIT;

-- Expected result: 3 active departments (Data Operations, Support Functions, Technology)
