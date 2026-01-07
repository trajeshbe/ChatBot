-- ============================================================================
-- Seed Departments
-- ============================================================================
--
-- Purpose: Create organizational departments for the enterprise
--
-- Departments:
--   - Data Operations (DATA_OPS)  - Data science, analytics, engineering
--   - Technology (TECH)            - Software engineering and IT
--   - Marketing (MARKETING)        - Marketing and communications
--   - Sales (SALES)                - Sales and business development
--   - HR (HR)                      - Human resources
--   - Finance (FINANCE)            - Finance and accounting
--   - General (GENERAL)            - Uncategorized/general purpose
--
-- Dependencies: departments table
--
-- Idempotent: Yes (ON CONFLICT DO NOTHING)
--
-- ============================================================================

INSERT INTO departments (name, code, description, is_active, created_at, updated_at)
VALUES
    (
        'Data Operations',
        'DATA_OPS',
        'Data science, analytics, and data engineering teams',
        TRUE,
        NOW(),
        NOW()
    ),
    (
        'Technology',
        'TECH',
        'Software engineering and IT teams',
        TRUE,
        NOW(),
        NOW()
    ),
    (
        'Marketing',
        'MARKETING',
        'Marketing and communications teams',
        TRUE,
        NOW(),
        NOW()
    ),
    (
        'Sales',
        'SALES',
        'Sales and business development teams',
        TRUE,
        NOW(),
        NOW()
    ),
    (
        'HR',
        'HR',
        'Human resources and people operations',
        TRUE,
        NOW(),
        NOW()
    ),
    (
        'Finance',
        'FINANCE',
        'Finance and accounting teams',
        TRUE,
        NOW(),
        NOW()
    ),
    (
        'General',
        'GENERAL',
        'General/uncategorized department',
        TRUE,
        NOW(),
        NOW()
    )
ON CONFLICT (code) DO NOTHING;

-- Verification
DO $$
DECLARE
    dept_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO dept_count FROM departments;
    RAISE NOTICE '✓ Departments seeded: % departments', dept_count;
END
$$;
