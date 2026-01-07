-- ============================================================================
-- Seed Teams
-- ============================================================================
--
-- Purpose: Create teams within departments
--
-- Teams Distribution:
--   - Data Operations: 16 teams (DATA_TEAM_1 to DATA_TEAM_16)
--   - Technology: 11 teams (ITM1 to ITM11)
--   - Marketing: 1 team (MKT_TEAM_1)
--   - Total: 28 teams
--
-- Dependencies: departments table (must exist)
--
-- Idempotent: Yes (ON CONFLICT DO NOTHING)
--
-- ============================================================================

DO $$
DECLARE
    data_ops_id UUID;
    tech_id UUID;
    marketing_id UUID;
BEGIN
    -- Get department IDs
    SELECT id INTO data_ops_id FROM departments WHERE code = 'DATA_OPS';
    SELECT id INTO tech_id FROM departments WHERE code = 'TECH';
    SELECT id INTO marketing_id FROM departments WHERE code = 'MARKETING';

    -- Verify departments exist
    IF data_ops_id IS NULL OR tech_id IS NULL OR marketing_id IS NULL THEN
        RAISE EXCEPTION 'Required departments not found. Run 03_seed_departments.sql first.';
    END IF;

    -- ========================================================================
    -- Data Operations Teams (16 teams)
    -- ========================================================================
    FOR i IN 1..16 LOOP
        INSERT INTO teams (name, code, department_id, description, is_active, created_at, updated_at)
        VALUES (
            'Data Team ' || i,
            'DATA_TEAM_' || i,
            data_ops_id,
            'Data operations team ' || i,
            TRUE,
            NOW(),
            NOW()
        )
        ON CONFLICT (department_id, code) DO NOTHING;
    END LOOP;

    -- ========================================================================
    -- Technology Teams (11 teams: ITM1 to ITM11)
    -- ========================================================================
    FOR i IN 1..11 LOOP
        INSERT INTO teams (name, code, department_id, description, is_active, created_at, updated_at)
        VALUES (
            'Technology Team ' || i || ' (ITM' || i || ')',
            'ITM' || i,
            tech_id,
            'Technology/IT team ' || i,
            TRUE,
            NOW(),
            NOW()
        )
        ON CONFLICT (department_id, code) DO NOTHING;
    END LOOP;

    -- ========================================================================
    -- Marketing Team (1 team)
    -- ========================================================================
    INSERT INTO teams (name, code, department_id, description, is_active, created_at, updated_at)
    VALUES (
        'Marketing Team 1',
        'MKT_TEAM_1',
        marketing_id,
        'Primary marketing team',
        TRUE,
        NOW(),
        NOW()
    )
    ON CONFLICT (department_id, code) DO NOTHING;

    -- Verification
    RAISE NOTICE '✓ Data Operations teams seeded: 16 teams';
    RAISE NOTICE '✓ Technology teams seeded: 11 teams (ITM1-ITM11)';
    RAISE NOTICE '✓ Marketing teams seeded: 1 team';
    RAISE NOTICE '✓ Total teams seeded: 28 teams';
END
$$;

-- Final verification
SELECT
    d.name AS department,
    COUNT(t.id) AS team_count
FROM departments d
LEFT JOIN teams t ON d.id = t.department_id
GROUP BY d.name
ORDER BY team_count DESC;
