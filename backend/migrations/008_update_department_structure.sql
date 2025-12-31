-- Migration 008: Update Department Structure with Real Organization
-- Date: 2025-11-27
-- Purpose: Replace generic department names with actual organizational structure

BEGIN;

-- ============================================================================
-- STEP 1: Update Support Functions
-- ============================================================================

-- Update Marketing team
UPDATE departments
SET name = 'Marketing'
WHERE name = 'Marketing Team' AND parent_department_id = (
    SELECT id FROM departments WHERE name = 'Support Functions' AND parent_department_id = (
        SELECT id FROM departments WHERE name = 'Enterprise' AND parent_department_id IS NULL
    )
);

-- Update Sales team
UPDATE departments
SET name = 'Sales'
WHERE name = 'Sales Team' AND parent_department_id = (
    SELECT id FROM departments WHERE name = 'Support Functions' AND parent_department_id = (
        SELECT id FROM departments WHERE name = 'Enterprise' AND parent_department_id IS NULL
    )
);

-- Update HR team
UPDATE departments
SET name = 'HR'
WHERE name = 'HR Team' AND parent_department_id = (
    SELECT id FROM departments WHERE name = 'Support Functions' AND parent_department_id = (
        SELECT id FROM departments WHERE name = 'Enterprise' AND parent_department_id IS NULL
    )
);

-- ============================================================================
-- STEP 2: Update Technology Teams (Tech Team 1-12 → Team 1-12)
-- ============================================================================

UPDATE departments
SET name = 'Team 1'
WHERE name = 'Tech Team 1' AND parent_department_id = (
    SELECT id FROM departments WHERE name = 'Technology'
);

UPDATE departments
SET name = 'Team 2'
WHERE name = 'Tech Team 2' AND parent_department_id = (
    SELECT id FROM departments WHERE name = 'Technology'
);

UPDATE departments
SET name = 'Team 3'
WHERE name = 'Tech Team 3' AND parent_department_id = (
    SELECT id FROM departments WHERE name = 'Technology'
);

UPDATE departments
SET name = 'Team 4'
WHERE name = 'Tech Team 4' AND parent_department_id = (
    SELECT id FROM departments WHERE name = 'Technology'
);

UPDATE departments
SET name = 'Team 5'
WHERE name = 'Tech Team 5' AND parent_department_id = (
    SELECT id FROM departments WHERE name = 'Technology'
);

UPDATE departments
SET name = 'Team 6'
WHERE name = 'Tech Team 6' AND parent_department_id = (
    SELECT id FROM departments WHERE name = 'Technology'
);

UPDATE departments
SET name = 'Team 7'
WHERE name = 'Tech Team 7' AND parent_department_id = (
    SELECT id FROM departments WHERE name = 'Technology'
);

UPDATE departments
SET name = 'Team 8'
WHERE name = 'Tech Team 8' AND parent_department_id = (
    SELECT id FROM departments WHERE name = 'Technology'
);

UPDATE departments
SET name = 'Team 9'
WHERE name = 'Tech Team 9' AND parent_department_id = (
    SELECT id FROM departments WHERE name = 'Technology'
);

UPDATE departments
SET name = 'Team 10'
WHERE name = 'Tech Team 10' AND parent_department_id = (
    SELECT id FROM departments WHERE name = 'Technology'
);

UPDATE departments
SET name = 'Team 11'
WHERE name = 'Tech Team 11' AND parent_department_id = (
    SELECT id FROM departments WHERE name = 'Technology'
);

UPDATE departments
SET name = 'Team 12'
WHERE name = 'Tech Team 12' AND parent_department_id = (
    SELECT id FROM departments WHERE name = 'Technology'
);

-- ============================================================================
-- STEP 3: Update Data Operations Teams with Real Names
-- ============================================================================

-- Get Data Operations ID
DO $$
DECLARE
    data_ops_id UUID;
BEGIN
    SELECT id INTO data_ops_id FROM departments WHERE name = 'Data Operations';

    -- Update Data Team 1 → Air Business Distribution
    UPDATE departments
    SET name = 'Air Business Distribution'
    WHERE name = 'Data Team 1' AND parent_department_id = data_ops_id;

    -- Update Data Team 2 → ALF
    UPDATE departments
    SET name = 'ALF'
    WHERE name = 'Data Team 2' AND parent_department_id = data_ops_id;

    -- Update Data Team 3 → DMS Construction Data Research
    UPDATE departments
    SET name = 'DMS Construction Data Research'
    WHERE name = 'Data Team 3' AND parent_department_id = data_ops_id;

    -- Update Data Team 4 → DODs
    UPDATE departments
    SET name = 'DODs'
    WHERE name = 'Data Team 4' AND parent_department_id = data_ops_id;

    -- Update Data Team 5 → Glenigan FRO
    UPDATE departments
    SET name = 'Glenigan FRO'
    WHERE name = 'Data Team 5' AND parent_department_id = data_ops_id;

    -- Update Data Team 6 → Haymarket
    UPDATE departments
    SET name = 'Haymarket'
    WHERE name = 'Data Team 6' AND parent_department_id = data_ops_id;

    -- Update Data Team 7 → HSJ
    UPDATE departments
    SET name = 'HSJ'
    WHERE name = 'Data Team 7' AND parent_department_id = data_ops_id;

    -- Update Data Team 8 → HSJ On Medica
    UPDATE departments
    SET name = 'HSJ On Medica'
    WHERE name = 'Data Team 8' AND parent_department_id = data_ops_id;

    -- Update Data Team 9 → Informa Connect - Data Research
    UPDATE departments
    SET name = 'Informa Connect - Data Research'
    WHERE name = 'Data Team 9' AND parent_department_id = data_ops_id;

    -- Update Data Team 10 → Leadership
    UPDATE departments
    SET name = 'Leadership'
    WHERE name = 'Data Team 10' AND parent_department_id = data_ops_id;

    -- Update Data Team 11 → Leadscale
    UPDATE departments
    SET name = 'Leadscale'
    WHERE name = 'Data Team 11' AND parent_department_id = data_ops_id;

    -- Update Data Team 12 → LLI Data
    UPDATE departments
    SET name = 'LLI Data'
    WHERE name = 'Data Team 12' AND parent_department_id = data_ops_id;

    -- Update Data Team 13 → Political Engagement - Research Support
    UPDATE departments
    SET name = 'Political Engagement - Research Support'
    WHERE name = 'Data Team 13' AND parent_department_id = data_ops_id;

    -- Update Data Team 14 → Quality
    UPDATE departments
    SET name = 'Quality'
    WHERE name = 'Data Team 14' AND parent_department_id = data_ops_id;

    -- Update Data Team 15 → Tactical Data
    UPDATE departments
    SET name = 'Tactical Data'
    WHERE name = 'Data Team 15' AND parent_department_id = data_ops_id;

    -- Update Data Team 16 → Tactical Data Research
    UPDATE departments
    SET name = 'Tactical Data Research'
    WHERE name = 'Data Team 16' AND parent_department_id = data_ops_id;

END $$;

-- ============================================================================
-- Verification
-- ============================================================================

-- Show updated structure
SELECT
    d1.name AS division,
    d2.name AS department,
    COUNT(*) AS teams_or_functions
FROM departments d1
LEFT JOIN departments d2 ON d2.parent_department_id = d1.id
WHERE d1.parent_department_id = (
    SELECT id FROM departments WHERE name = 'Enterprise' AND parent_department_id IS NULL
)
GROUP BY d1.name, d2.name
ORDER BY d1.name, d2.name;

COMMIT;

-- Display final structure
SELECT
    CASE
        WHEN d.parent_department_id IS NULL THEN '└─ ' || d.name
        WHEN EXISTS (SELECT 1 FROM departments WHERE parent_department_id = d.id) THEN '  ├─ ' || d.name
        ELSE '    └─ ' || d.name
    END AS organizational_structure,
    d.is_active,
    d.created_at
FROM departments d
ORDER BY d.parent_department_id NULLS FIRST, d.name;
