-- Migration: Seed Role-Module Permissions
-- Date: 2025-12-01
-- Purpose: Populate the role_module_permissions table with default permission mappings
-- This enables the RBAC system to actually control access to modules based on roles

-- ============================================================================
-- ADMIN ROLE: Full access to all modules
-- ============================================================================
INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
SELECT
    r.id as role_id,
    m.id as module_id,
    true as can_read,
    true as can_write,
    true as can_delete,
    true as can_share
FROM roles r
CROSS JOIN modules m
WHERE r.name = 'Admin'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- CXO ROLE: Full access except cannot delete from admin panel
-- ============================================================================
INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
SELECT
    r.id as role_id,
    m.id as module_id,
    true as can_read,
    true as can_write,
    CASE
        WHEN m.module_key = 'admin' THEN false
        ELSE true
    END as can_delete,
    true as can_share
FROM roles r
CROSS JOIN modules m
WHERE r.name = 'CxO'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- MANAGER ROLE: Read/write on most modules, no delete on admin
-- ============================================================================
INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
SELECT
    r.id as role_id,
    m.id as module_id,
    true as can_read,
    CASE
        WHEN m.module_key IN ('chat', 'history', 'upload', 'scrape', 'estimator', 'evaluation', 'tools', 'weights') THEN true
        WHEN m.module_key = 'admin' THEN false
        ELSE true
    END as can_write,
    CASE
        WHEN m.module_key = 'admin' THEN false
        ELSE false
    END as can_delete,
    CASE
        WHEN m.module_key IN ('chat', 'scrape', 'estimator', 'evaluation') THEN true
        ELSE false
    END as can_share
FROM roles r
CROSS JOIN modules m
WHERE r.name = 'Manager'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- USER ROLE: Read/write on core features, share on specific modules
-- ============================================================================
INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
SELECT
    r.id as role_id,
    m.id as module_id,
    CASE
        -- Users can read everything except admin
        WHEN m.module_key = 'admin' THEN false
        ELSE true
    END as can_read,
    CASE
        -- Users can write to their core features
        WHEN m.module_key IN ('chat', 'history', 'upload', 'scrape') THEN true
        ELSE false
    END as can_write,
    false as can_delete,  -- Users cannot delete anything
    CASE
        -- Users can share chat, scrape, and estimator results
        WHEN m.module_key IN ('chat', 'scrape', 'estimator') THEN true
        ELSE false
    END as can_share
FROM roles r
CROSS JOIN modules m
WHERE r.name = 'User'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- READONLY ROLE: Read-only access to non-admin modules
-- ============================================================================
INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
SELECT
    r.id as role_id,
    m.id as module_id,
    true as can_read,
    false as can_write,
    false as can_delete,
    false as can_share
FROM roles r
CROSS JOIN modules m
WHERE r.name = 'ReadOnly'
    AND m.module_key != 'admin'  -- ReadOnly cannot even see admin panel
ON CONFLICT DO NOTHING;

-- ============================================================================
-- VERIFICATION QUERY
-- ============================================================================
-- Run this to verify the permissions were created:
-- SELECT
--     r.name as role,
--     m.module_key as module,
--     p.can_read,
--     p.can_write,
--     p.can_delete,
--     p.can_share
-- FROM role_module_permissions p
-- JOIN roles r ON p.role_id = r.id
-- JOIN modules m ON p.module_id = m.id
-- ORDER BY r.name, m.module_key;
