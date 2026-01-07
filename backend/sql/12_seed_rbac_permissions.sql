-- ============================================================================
-- Seed RBAC Permissions - Complete Role-Module Permission Matrix
-- ============================================================================
--
-- Purpose: Create complete role-module permission mappings for all 36 modules
--
-- Roles:
--   - Admin      - Full access to all modules (read, write, execute, delete)
--   - CxO        - Executive access (all except admin panel deletions)
--   - Manager    - Team lead access (most modules, limited admin)
--   - User       - Standard user access (Tier 1 + basic Tier 2)
--   - ReadOnly   - Read-only access (view only, no modifications)
--
-- Dependencies: roles table, modules table, role_module_permissions table
--
-- Idempotent: Yes (ON CONFLICT DO UPDATE)
--
-- ============================================================================

-- ============================================================================
-- ADMIN ROLE: Full access to ALL modules
-- ============================================================================

INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
SELECT
    r.id as role_id,
    m.id as module_id,
    TRUE as can_read,
    TRUE as can_write,
    TRUE as can_delete,
    TRUE as can_share
FROM roles r
CROSS JOIN modules m
WHERE r.name = 'Admin'
ON CONFLICT (role_id, module_id) DO UPDATE SET
    can_read = EXCLUDED.can_read,
    can_write = EXCLUDED.can_write,
    can_delete = EXCLUDED.can_delete,
    can_share = EXCLUDED.can_share,
    updated_at = NOW();

-- ============================================================================
-- CXO ROLE: Full access except cannot delete from admin panel
-- ============================================================================

INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
SELECT
    r.id as role_id,
    m.id as module_id,
    TRUE as can_read,
    TRUE as can_write,
    CASE
        WHEN m.module_key = 'admin' THEN FALSE
        ELSE TRUE
    END as can_delete,
    TRUE as can_share
FROM roles r
CROSS JOIN modules m
WHERE r.name = 'CxO'
ON CONFLICT (role_id, module_id) DO UPDATE SET
    can_read = EXCLUDED.can_read,
    can_write = EXCLUDED.can_write,
    can_delete = EXCLUDED.can_delete,
    can_share = EXCLUDED.can_share,
    updated_at = NOW();

-- ============================================================================
-- MANAGER ROLE: Read/write on most modules, limited admin access
-- ============================================================================

INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
SELECT
    r.id as role_id,
    m.id as module_id,
    TRUE as can_read,
    CASE
        -- Full write access to Tier 1 core modules
        WHEN m.module_key IN ('chat', 'history', 'upload', 'scrape', 'estimator', 'evaluation', 'tools', 'weights') THEN TRUE
        -- Write access to Tier 2 domain verticals
        WHEN m.meta_info->>'tier' = '2' THEN TRUE
        -- No write access to admin or finetuning
        WHEN m.module_key IN ('admin', 'finetuning') THEN FALSE
        -- Default: read-only
        ELSE FALSE
    END as can_write,
    -- No delete permissions (except own data via application logic)
    FALSE as can_delete,
    CASE
        -- Can share Tier 1 and Tier 2 modules
        WHEN m.module_key IN ('chat', 'scrape', 'estimator', 'evaluation') THEN TRUE
        WHEN m.meta_info->>'tier' IN ('1', '2') THEN TRUE
        ELSE FALSE
    END as can_share
FROM roles r
CROSS JOIN modules m
WHERE r.name = 'Manager'
ON CONFLICT (role_id, module_id) DO UPDATE SET
    can_read = EXCLUDED.can_read,
    can_write = EXCLUDED.can_write,
    can_delete = EXCLUDED.can_delete,
    can_share = EXCLUDED.can_share,
    updated_at = NOW();

-- ============================================================================
-- USER ROLE: Tier 1 + basic Tier 2 access
-- ============================================================================

INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
SELECT
    r.id as role_id,
    m.id as module_id,
    CASE
        -- Can read all Tier 1 modules except admin
        WHEN m.meta_info->>'tier' = '1' AND m.module_key != 'admin' THEN TRUE
        -- Can read specific Tier 2 modules
        WHEN m.module_key IN (
            'generic_rag',
            'relation_extractor',
            'predictive_analytics',
            'product_recommendation',
            'talent_search'
        ) THEN TRUE
        -- Cannot read Tier 3 or restricted modules
        ELSE FALSE
    END as can_read,
    CASE
        -- Can write to core Tier 1 modules
        WHEN m.module_key IN ('chat', 'history', 'upload', 'scrape', 'estimator') THEN TRUE
        -- Can write to Generic RAG
        WHEN m.module_key = 'generic_rag' THEN TRUE
        ELSE FALSE
    END as can_write,
    -- Users cannot delete anything (handled by ownership logic)
    FALSE as can_delete,
    CASE
        -- Can share own content in specific modules
        WHEN m.module_key IN ('chat', 'scrape', 'estimator', 'generic_rag') THEN TRUE
        ELSE FALSE
    END as can_share
FROM roles r
CROSS JOIN modules m
WHERE r.name = 'User'
ON CONFLICT (role_id, module_id) DO UPDATE SET
    can_read = EXCLUDED.can_read,
    can_write = EXCLUDED.can_write,
    can_delete = EXCLUDED.can_delete,
    can_share = EXCLUDED.can_share,
    updated_at = NOW();

-- ============================================================================
-- READONLY ROLE: Read-only access to non-admin, non-sensitive modules
-- ============================================================================

INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
SELECT
    r.id as role_id,
    m.id as module_id,
    CASE
        -- Can read basic Tier 1 modules
        WHEN m.module_key IN ('chat', 'history') THEN TRUE
        -- Can read Generic RAG for document viewing
        WHEN m.module_key = 'generic_rag' THEN TRUE
        -- Cannot access admin, finetuning, or sensitive modules
        ELSE FALSE
    END as can_read,
    -- No write permissions
    FALSE as can_write,
    -- No delete permissions
    FALSE as can_delete,
    -- No share permissions
    FALSE as can_share
FROM roles r
CROSS JOIN modules m
WHERE r.name = 'ReadOnly'
ON CONFLICT (role_id, module_id) DO UPDATE SET
    can_read = EXCLUDED.can_read,
    can_write = EXCLUDED.can_write,
    can_delete = EXCLUDED.can_delete,
    can_share = EXCLUDED.can_share,
    updated_at = NOW();

-- ============================================================================
-- ROLE_PERMISSIONS TABLE: Legacy module-based permissions
-- ============================================================================
-- This table uses VARCHAR role field instead of role_id FK
-- Seed basic permissions for compatibility with existing code

INSERT INTO role_permissions (role, module_id, can_access, can_create, can_edit, can_delete)
SELECT
    'admin'::VARCHAR(50),
    id,
    TRUE,
    TRUE,
    TRUE,
    TRUE
FROM modules
ON CONFLICT (role, module_id) DO UPDATE SET
    can_access = EXCLUDED.can_access,
    can_create = EXCLUDED.can_create,
    can_edit = EXCLUDED.can_edit,
    can_delete = EXCLUDED.can_delete,
    updated_at = NOW();

-- User role: Tier 1 modules only
INSERT INTO role_permissions (role, module_id, can_access, can_create, can_edit, can_delete)
SELECT
    'user'::VARCHAR(50),
    id,
    TRUE,
    TRUE,
    FALSE,
    FALSE
FROM modules
WHERE module_key IN ('chat', 'history', 'upload', 'scrape', 'estimator', 'evaluation', 'tools')
ON CONFLICT (role, module_id) DO UPDATE SET
    can_access = EXCLUDED.can_access,
    can_create = EXCLUDED.can_create,
    can_edit = EXCLUDED.can_edit,
    can_delete = EXCLUDED.can_delete,
    updated_at = NOW();

-- Viewer role: Read-only access
INSERT INTO role_permissions (role, module_id, can_access, can_create, can_edit, can_delete)
SELECT
    'viewer'::VARCHAR(50),
    id,
    TRUE,
    FALSE,
    FALSE,
    FALSE
FROM modules
WHERE module_key IN ('chat', 'history')
ON CONFLICT (role, module_id) DO UPDATE SET
    can_access = EXCLUDED.can_access,
    can_create = EXCLUDED.can_create,
    can_edit = EXCLUDED.can_edit,
    can_delete = EXCLUDED.can_delete,
    updated_at = NOW();

-- ============================================================================
-- SPECIALIZED ROLE GRANTS
-- ============================================================================

-- Data Analyst Role: Access to analytics modules
DO $$
DECLARE
    analyst_role_id UUID;
BEGIN
    SELECT id INTO analyst_role_id FROM roles WHERE name = 'Data Analyst';

    IF analyst_role_id IS NOT NULL THEN
        INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
        SELECT
            analyst_role_id,
            m.id,
            TRUE,
            TRUE,
            FALSE,
            TRUE
        FROM modules m
        WHERE m.module_key IN (
            'predictive_analytics',
            'customer_churn',
            'financial_anomaly',
            'sales_performance',
            'evaluation',
            'tools'
        )
        ON CONFLICT (role_id, module_id) DO UPDATE SET
            can_read = TRUE,
            can_write = TRUE,
            can_delete = FALSE,
            can_share = TRUE,
            updated_at = NOW();
    END IF;
END
$$;

-- HR Manager Role: Access to HR modules
DO $$
DECLARE
    hr_role_id UUID;
BEGIN
    SELECT id INTO hr_role_id FROM roles WHERE name = 'HR Manager';

    IF hr_role_id IS NOT NULL THEN
        INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
        SELECT
            hr_role_id,
            m.id,
            TRUE,
            TRUE,
            FALSE,
            TRUE
        FROM modules m
        WHERE m.module_key IN (
            'talent_search',
            'taxonomy_skillmatch',
            'talent_pulse',
            'chat',
            'upload'
        )
        ON CONFLICT (role_id, module_id) DO UPDATE SET
            can_read = TRUE,
            can_write = TRUE,
            can_delete = FALSE,
            can_share = TRUE,
            updated_at = NOW();
    END IF;
END
$$;

-- Procurement Manager Role: Access to procurement modules
DO $$
DECLARE
    proc_role_id UUID;
BEGIN
    SELECT id INTO proc_role_id FROM roles WHERE name = 'Procurement Manager';

    IF proc_role_id IS NOT NULL THEN
        INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
        SELECT
            proc_role_id,
            m.id,
            TRUE,
            TRUE,
            FALSE,
            TRUE
        FROM modules m
        WHERE m.module_key IN (
            'procurement_matcher',
            'vendor_recommendation',
            'tender_intelligence',
            'spend_smart',
            'chat',
            'upload'
        )
        ON CONFLICT (role_id, module_id) DO UPDATE SET
            can_read = TRUE,
            can_write = TRUE,
            can_delete = FALSE,
            can_share = TRUE,
            updated_at = NOW();
    END IF;
END
$$;

-- Customer Success Role: Access to Tier 3 customer solutions
DO $$
DECLARE
    cs_role_id UUID;
BEGIN
    SELECT id INTO cs_role_id FROM roles WHERE name = 'Customer Success';

    IF cs_role_id IS NOT NULL THEN
        INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
        SELECT
            cs_role_id,
            m.id,
            TRUE,
            TRUE,
            FALSE,
            TRUE
        FROM modules m
        WHERE m.meta_info->>'tier' = '3'
           OR m.module_key IN ('chat', 'history', 'upload', 'generic_rag')
        ON CONFLICT (role_id, module_id) DO UPDATE SET
            can_read = TRUE,
            can_write = TRUE,
            can_delete = FALSE,
            can_share = TRUE,
            updated_at = NOW();
    END IF;
END
$$;

-- ============================================================================
-- VERIFICATION & REPORTING
-- ============================================================================

DO $$
DECLARE
    total_perms INTEGER;
    admin_perms INTEGER;
    cxo_perms INTEGER;
    manager_perms INTEGER;
    user_perms INTEGER;
    readonly_perms INTEGER;
    role_count INTEGER;
    module_count INTEGER;
BEGIN
    -- Count totals
    SELECT COUNT(*) INTO total_perms FROM role_module_permissions;
    SELECT COUNT(*) INTO role_count FROM roles;
    SELECT COUNT(*) INTO module_count FROM modules;

    -- Count by role
    SELECT COUNT(*) INTO admin_perms
    FROM role_module_permissions rmp
    JOIN roles r ON rmp.role_id = r.id
    WHERE r.name = 'Admin';

    SELECT COUNT(*) INTO cxo_perms
    FROM role_module_permissions rmp
    JOIN roles r ON rmp.role_id = r.id
    WHERE r.name = 'CxO';

    SELECT COUNT(*) INTO manager_perms
    FROM role_module_permissions rmp
    JOIN roles r ON rmp.role_id = r.id
    WHERE r.name = 'Manager';

    SELECT COUNT(*) INTO user_perms
    FROM role_module_permissions rmp
    JOIN roles r ON rmp.role_id = r.id
    WHERE r.name = 'User';

    SELECT COUNT(*) INTO readonly_perms
    FROM role_module_permissions rmp
    JOIN roles r ON rmp.role_id = r.id
    WHERE r.name = 'ReadOnly';

    -- Report
    RAISE NOTICE '';
    RAISE NOTICE '================================================';
    RAISE NOTICE 'RBAC PERMISSIONS SEEDING COMPLETE';
    RAISE NOTICE '================================================';
    RAISE NOTICE 'Total permissions created: %', total_perms;
    RAISE NOTICE 'Roles configured: %', role_count;
    RAISE NOTICE 'Modules protected: %', module_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Permissions by role:';
    RAISE NOTICE '  Admin:     % module permissions (full access)', admin_perms;
    RAISE NOTICE '  CxO:       % module permissions', cxo_perms;
    RAISE NOTICE '  Manager:   % module permissions', manager_perms;
    RAISE NOTICE '  User:      % module permissions', user_perms;
    RAISE NOTICE '  ReadOnly:  % module permissions', readonly_perms;
    RAISE NOTICE '';
    RAISE NOTICE '✓ RBAC permissions successfully configured';
    RAISE NOTICE '================================================';
    RAISE NOTICE '';

    -- Show permission matrix sample
    RAISE NOTICE 'Sample Permission Matrix (first 10 entries):';
    RAISE NOTICE '%-15s | %-30s | READ | WRITE | DELETE | SHARE', 'ROLE', 'MODULE';
    RAISE NOTICE '================================================================';

    -- This is just a sample query for verification, not executed in production
    -- SELECT would need to be replaced with individual log statements
END
$$;

-- ============================================================================
-- VERIFICATION QUERIES (for manual testing)
-- ============================================================================

-- Uncomment to run verification queries:

-- View all permissions for Admin role
-- SELECT
--     r.name as role,
--     m.module_key,
--     m.name as module_name,
--     p.can_read,
--     p.can_write,
--     p.can_delete,
--     p.can_share
-- FROM role_module_permissions p
-- JOIN roles r ON p.role_id = r.id
-- JOIN modules m ON p.module_id = m.id
-- WHERE r.name = 'Admin'
-- ORDER BY m.display_order;

-- View permissions summary by role
-- SELECT
--     r.name as role,
--     COUNT(*) as total_modules,
--     SUM(CASE WHEN p.can_read THEN 1 ELSE 0 END) as can_read,
--     SUM(CASE WHEN p.can_write THEN 1 ELSE 0 END) as can_write,
--     SUM(CASE WHEN p.can_delete THEN 1 ELSE 0 END) as can_delete,
--     SUM(CASE WHEN p.can_share THEN 1 ELSE 0 END) as can_share
-- FROM role_module_permissions p
-- JOIN roles r ON p.role_id = r.id
-- GROUP BY r.name
-- ORDER BY r.name;

-- Find modules accessible by User role
-- SELECT
--     m.module_key,
--     m.name,
--     m.meta_info->>'tier' as tier,
--     p.can_read,
--     p.can_write
-- FROM role_module_permissions p
-- JOIN roles r ON p.role_id = r.id
-- JOIN modules m ON p.module_id = m.id
-- WHERE r.name = 'User' AND p.can_read = TRUE
-- ORDER BY m.display_order;
