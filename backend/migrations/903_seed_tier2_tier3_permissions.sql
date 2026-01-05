-- Migration 903: Seed Role-Module Permissions for Tier 2 and Tier 3 Modules
-- Created: 2026-01-05
-- Purpose: Grant appropriate role access to all 16 Tier 2/3 modules
-- Dependencies: 902_migrate_modules_schema.sql

BEGIN;

-- ============================================================================
-- STEP 1: Grant Admin role full access to ALL modules (Tier 1, 2, and 3)
-- ============================================================================
INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
SELECT
    r.id AS role_id,
    m.id AS module_id,
    TRUE AS can_read,
    TRUE AS can_write,
    TRUE AS can_delete,
    TRUE AS can_share
FROM roles r
CROSS JOIN modules m
WHERE r.name = 'Admin'
  AND NOT EXISTS (
      SELECT 1 FROM role_module_permissions rmp
      WHERE rmp.role_id = r.id AND rmp.module_id = m.id
  )
ON CONFLICT (role_id, module_id) DO UPDATE
SET can_read = TRUE, can_write = TRUE, can_delete = TRUE, can_share = TRUE;

-- ============================================================================
-- STEP 2: Grant CxO role access to analytics and reporting modules
-- ============================================================================
-- CxO gets read access to all, write to analytics/reporting modules
INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
SELECT
    r.id AS role_id,
    m.id AS module_id,
    TRUE AS can_read,
    CASE
        WHEN m.category IN ('Analytics', 'Finance') OR m.module_key IN ('evaluation', 'tools', 'predictive-analytics', 'financial-anomaly') THEN TRUE
        ELSE FALSE
    END AS can_write,
    FALSE AS can_delete,
    TRUE AS can_share
FROM roles r
CROSS JOIN modules m
WHERE r.name = 'CxO'
  AND m.module_key NOT IN ('admin')  -- No admin access for CxO
  AND NOT EXISTS (
      SELECT 1 FROM role_module_permissions rmp
      WHERE rmp.role_id = r.id AND rmp.module_id = m.id
  )
ON CONFLICT (role_id, module_id) DO UPDATE
SET can_read = TRUE,
    can_write = CASE
        WHEN modules.category IN ('Analytics', 'Finance') OR modules.module_key IN ('evaluation', 'tools', 'predictive-analytics', 'financial-anomaly') THEN TRUE
        ELSE FALSE
    END,
    can_share = TRUE;

-- ============================================================================
-- STEP 3: Grant Manager role access to most operational modules
-- ============================================================================
-- Manager gets access to Tier 1 and Tier 2 modules, limited Tier 3
INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
SELECT
    r.id AS role_id,
    m.id AS module_id,
    TRUE AS can_read,
    CASE
        WHEN m.module_key = 'admin' THEN FALSE
        WHEN m.tier = 3 THEN FALSE  -- No write to Tier 3 (customer POCs)
        ELSE TRUE
    END AS can_write,
    CASE
        WHEN m.module_key IN ('upload', 'scrape') THEN TRUE
        ELSE FALSE
    END AS can_delete,
    CASE
        WHEN m.module_key = 'admin' THEN FALSE
        ELSE TRUE
    END AS can_share
FROM roles r
CROSS JOIN modules m
WHERE r.name = 'Manager'
  AND m.module_key NOT IN ('admin')  -- Managers can't access admin panel
  AND NOT EXISTS (
      SELECT 1 FROM role_module_permissions rmp
      WHERE rmp.role_id = r.id AND rmp.module_id = m.id
  )
ON CONFLICT (role_id, module_id) DO UPDATE
SET can_read = TRUE,
    can_write = CASE
        WHEN modules.tier = 3 THEN FALSE
        ELSE TRUE
    END;

-- ============================================================================
-- STEP 4: Grant User role access to core features and selected Tier 2 modules
-- ============================================================================
-- User gets limited access to Tier 1 core + safe Tier 2 modules
INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
SELECT
    r.id AS role_id,
    m.id AS module_id,
    TRUE AS can_read,
    CASE
        WHEN m.module_key IN ('chat', 'upload', 'scrape', 'estimator') THEN TRUE
        WHEN m.tier = 2 AND m.category IN ('Core', 'Language', 'Education') THEN TRUE
        ELSE FALSE
    END AS can_write,
    FALSE AS can_delete,
    CASE
        WHEN m.module_key IN ('chat', 'estimator') THEN TRUE
        ELSE FALSE
    END AS can_share
FROM roles r
CROSS JOIN modules m
WHERE r.name = 'User'
  AND m.module_key NOT IN ('admin', 'weights')  -- Users can't access admin or weights config
  AND (
      m.tier IS NULL  -- Tier 1 core modules (except admin/weights)
      OR (m.tier = 2 AND m.category IN ('Core', 'Language', 'Education', 'Analytics'))  -- Selected Tier 2
  )
  AND NOT EXISTS (
      SELECT 1 FROM role_module_permissions rmp
      WHERE rmp.role_id = r.id AND rmp.module_id = m.id
  )
ON CONFLICT (role_id, module_id) DO UPDATE
SET can_read = TRUE;

-- ============================================================================
-- STEP 5: Grant ReadOnly role view-only access to non-sensitive modules
-- ============================================================================
-- ReadOnly gets view-only access to most modules
INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
SELECT
    r.id AS role_id,
    m.id AS module_id,
    TRUE AS can_read,
    FALSE AS can_write,
    FALSE AS can_delete,
    FALSE AS can_share
FROM roles r
CROSS JOIN modules m
WHERE r.name = 'ReadOnly'
  AND m.module_key NOT IN ('admin', 'weights')  -- No access to admin or weights config
  AND NOT EXISTS (
      SELECT 1 FROM role_module_permissions rmp
      WHERE rmp.role_id = r.id AND rmp.module_id = m.id
  )
ON CONFLICT (role_id, module_id) DO UPDATE
SET can_read = TRUE, can_write = FALSE, can_delete = FALSE, can_share = FALSE;

-- ============================================================================
-- STEP 6: Verify permissions distribution
-- ============================================================================
SELECT
    r.name AS role_name,
    COUNT(DISTINCT m.id) AS total_modules,
    SUM(CASE WHEN m.tier IS NULL THEN 1 ELSE 0 END) AS tier1_modules,
    SUM(CASE WHEN m.tier = 2 THEN 1 ELSE 0 END) AS tier2_modules,
    SUM(CASE WHEN m.tier = 3 THEN 1 ELSE 0 END) AS tier3_modules,
    SUM(CASE WHEN rmp.can_read THEN 1 ELSE 0 END) AS can_read,
    SUM(CASE WHEN rmp.can_write THEN 1 ELSE 0 END) AS can_write,
    SUM(CASE WHEN rmp.can_delete THEN 1 ELSE 0 END) AS can_delete,
    SUM(CASE WHEN rmp.can_share THEN 1 ELSE 0 END) AS can_share
FROM roles r
LEFT JOIN role_module_permissions rmp ON r.id = rmp.role_id
LEFT JOIN modules m ON rmp.module_id = m.id
GROUP BY r.name
ORDER BY r.name;

COMMIT;

-- Expected result:
-- Admin: 26 modules (full access to all tiers)
-- CxO: ~24 modules (no admin, limited write)
-- Manager: ~24 modules (no admin, no write to Tier 3)
-- User: ~15 modules (core + selected Tier 2, read-heavy)
-- ReadOnly: ~24 modules (view-only, no admin/weights)
