-- Migration 007: Seed RBAC Data
-- Description: Insert initial roles, departments, modules, and default permissions
-- Date: 2025-11-27
-- Dependencies: 006_add_rbac_tables.sql

-- ============================================================================
-- SEED ROLES
-- ============================================================================
INSERT INTO roles (name, parent_role_id, description, is_system_role) VALUES
    ('Admin', NULL, 'Full system access - can manage all resources and users', TRUE),
    ('CxO', NULL, 'Executive level access - high-level analytics and reporting', TRUE),
    ('Manager', NULL, 'Department manager - can manage team resources', TRUE),
    ('User', NULL, 'Standard user - can use application features', TRUE),
    ('ReadOnly', NULL, 'Read-only access - cannot modify data', TRUE)
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- SEED DEPARTMENTS
-- ============================================================================
-- Top-level departments
INSERT INTO departments (name, parent_department_id, description) VALUES
    ('Enterprise', NULL, 'Top-level organization'),
    ('Data Operations', NULL, 'Data research and operations teams'),
    ('Technology', NULL, 'Technology and IT teams'),
    ('Support Functions', NULL, 'Support, marketing, sales, and HR')
ON CONFLICT (name) DO NOTHING;

-- Data Operations sub-departments
INSERT INTO departments (name, parent_department_id, description)
SELECT 'Data Team ' || num, d.id, 'Data operations team ' || num
FROM generate_series(1, 16) AS num
CROSS JOIN departments d
WHERE d.name = 'Data Operations'
ON CONFLICT (name) DO NOTHING;

-- Technology sub-departments
INSERT INTO departments (name, parent_department_id, description)
SELECT 'Tech Team ' || num, d.id, 'Technology team ' || num
FROM generate_series(1, 12) AS num
CROSS JOIN departments d
WHERE d.name = 'Technology'
ON CONFLICT (name) DO NOTHING;

-- Support Functions sub-departments
INSERT INTO departments (name, parent_department_id, description)
SELECT dept, d.id, dept || ' department'
FROM (VALUES ('Marketing'), ('Sales'), ('HR')) AS depts(dept)
CROSS JOIN departments d
WHERE d.name = 'Support Functions'
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- SEED MODULES
-- ============================================================================
INSERT INTO modules (name, code, description, icon, route, display_order) VALUES
    ('RAG Chat', 'rag_chat', 'AI-powered document Q&A with chat interface', 'MessageSquare', '/chat', 1),
    ('File Upload', 'file_upload', 'Upload and manage documents', 'Upload', '/upload', 2),
    ('Web Scraping', 'web_scraping', 'Extract data from websites', 'Globe', '/scrape', 3),
    ('Data Extraction', 'data_extraction', 'Extract structured data from documents', 'FileSpreadsheet', '/extract', 4),
    ('Project Estimator', 'project_estimator', 'AI-powered project cost estimation', 'Calculator', '/estimator', 5),
    ('Evaluation Metrics', 'evaluation', 'RAG system performance metrics and analytics', 'BarChart3', '/evaluation', 6),
    ('Tool Usage Dashboard', 'tools_dashboard', 'Monitor tool and agent usage statistics', 'Wrench', '/tools', 7),
    ('Weights Configuration', 'weights_config', 'Configure RAG retrieval weights and parameters', 'Sliders', '/weights', 8),
    ('Admin Panel', 'admin_panel', 'System administration and user management', 'Settings', '/admin', 9),
    ('Audit Logs', 'audit_logs', 'View system audit trail and activity logs', 'Shield', '/admin/audit', 10)
ON CONFLICT (code) DO NOTHING;

-- ============================================================================
-- SEED ROLE-MODULE PERMISSIONS
-- ============================================================================

-- Admin Role: Full access to everything
INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
SELECT
    r.id,
    m.id,
    TRUE,
    TRUE,
    TRUE,
    TRUE
FROM roles r
CROSS JOIN modules m
WHERE r.name = 'Admin'
ON CONFLICT (role_id, module_id) DO NOTHING;

-- CxO Role: Read access to all, write to some
INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
SELECT
    r.id,
    m.id,
    TRUE,
    CASE
        WHEN m.code IN ('rag_chat', 'evaluation', 'tools_dashboard') THEN TRUE
        ELSE FALSE
    END,
    FALSE,
    TRUE
FROM roles r
CROSS JOIN modules m
WHERE r.name = 'CxO'
ON CONFLICT (role_id, module_id) DO NOTHING;

-- Manager Role: Access to most features, no admin
INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
SELECT
    r.id,
    m.id,
    TRUE,
    CASE
        WHEN m.code NOT IN ('admin_panel', 'audit_logs') THEN TRUE
        ELSE FALSE
    END,
    CASE
        WHEN m.code IN ('file_upload', 'web_scraping', 'data_extraction') THEN TRUE
        ELSE FALSE
    END,
    TRUE
FROM roles r
CROSS JOIN modules m
WHERE r.name = 'Manager'
  AND m.code NOT IN ('admin_panel', 'audit_logs')
ON CONFLICT (role_id, module_id) DO NOTHING;

-- User Role: Standard access to core features
INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
SELECT
    r.id,
    m.id,
    TRUE,
    CASE
        WHEN m.code IN ('rag_chat', 'file_upload', 'web_scraping', 'data_extraction', 'project_estimator') THEN TRUE
        ELSE FALSE
    END,
    CASE
        WHEN m.code IN ('file_upload') THEN TRUE
        ELSE FALSE
    END,
    CASE
        WHEN m.code IN ('rag_chat', 'project_estimator') THEN TRUE
        ELSE FALSE
    END
FROM roles r
CROSS JOIN modules m
WHERE r.name = 'User'
  AND m.code IN ('rag_chat', 'file_upload', 'web_scraping', 'data_extraction', 'project_estimator', 'evaluation', 'tools_dashboard')
ON CONFLICT (role_id, module_id) DO NOTHING;

-- ReadOnly Role: Read-only access to viewing features
INSERT INTO role_module_permissions (role_id, module_id, can_read, can_write, can_delete, can_share)
SELECT
    r.id,
    m.id,
    TRUE,
    FALSE,
    FALSE,
    FALSE
FROM roles r
CROSS JOIN modules m
WHERE r.name = 'ReadOnly'
  AND m.code NOT IN ('admin_panel', 'audit_logs')
ON CONFLICT (role_id, module_id) DO NOTHING;

-- ============================================================================
-- SYNC EXISTING USERS WITH RBAC (Backward Compatibility)
-- ============================================================================
-- Map existing users.role enum values to new RBAC roles
-- This ensures existing users automatically get RBAC permissions

DO $$
BEGIN
    -- Only sync if users table exists
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users') THEN

        -- Sync users with 'admin' enum role to Admin RBAC role
        INSERT INTO user_roles (user_id, role_id, assigned_at, is_active)
        SELECT
            u.id,
            r.id,
            NOW(),
            TRUE
        FROM users u
        CROSS JOIN roles r
        WHERE u.role::text = 'admin'
          AND r.name = 'Admin'
          AND NOT EXISTS (
              SELECT 1 FROM user_roles ur
              WHERE ur.user_id = u.id AND ur.role_id = r.id
          );

        -- Sync users with 'user' enum role to User RBAC role
        INSERT INTO user_roles (user_id, role_id, assigned_at, is_active)
        SELECT
            u.id,
            r.id,
            NOW(),
            TRUE
        FROM users u
        CROSS JOIN roles r
        WHERE u.role::text = 'user'
          AND r.name = 'User'
          AND NOT EXISTS (
              SELECT 1 FROM user_roles ur
              WHERE ur.user_id = u.id AND ur.role_id = r.id
          );

        -- Sync users with 'viewer' enum role to ReadOnly RBAC role
        INSERT INTO user_roles (user_id, role_id, assigned_at, is_active)
        SELECT
            u.id,
            r.id,
            NOW(),
            TRUE
        FROM users u
        CROSS JOIN roles r
        WHERE u.role::text = 'viewer'
          AND r.name = 'ReadOnly'
          AND NOT EXISTS (
              SELECT 1 FROM user_roles ur
              WHERE ur.user_id = u.id AND ur.role_id = r.id
          );

        -- Sync users with 'api_user' enum role to User RBAC role
        INSERT INTO user_roles (user_id, role_id, assigned_at, is_active)
        SELECT
            u.id,
            r.id,
            NOW(),
            TRUE
        FROM users u
        CROSS JOIN roles r
        WHERE u.role::text = 'api_user'
          AND r.name = 'User'
          AND NOT EXISTS (
              SELECT 1 FROM user_roles ur
              WHERE ur.user_id = u.id AND ur.role_id = r.id
          );

    END IF;
END $$;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Verify seed data
SELECT 'Roles created:' AS status, COUNT(*) AS count FROM roles
UNION ALL
SELECT 'Departments created:', COUNT(*) FROM departments
UNION ALL
SELECT 'Modules created:', COUNT(*) FROM modules
UNION ALL
SELECT 'Permissions created:', COUNT(*) FROM role_module_permissions
UNION ALL
SELECT 'Users created:', COUNT(*) FROM users WHERE EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')
UNION ALL
SELECT 'User roles assigned:', COUNT(*) FROM user_roles WHERE EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user_roles');

-- Show role permissions summary
SELECT
    r.name AS role_name,
    COUNT(*) AS modules_count,
    SUM(CASE WHEN rmp.can_read THEN 1 ELSE 0 END) AS can_read,
    SUM(CASE WHEN rmp.can_write THEN 1 ELSE 0 END) AS can_write,
    SUM(CASE WHEN rmp.can_delete THEN 1 ELSE 0 END) AS can_delete,
    SUM(CASE WHEN rmp.can_share THEN 1 ELSE 0 END) AS can_share
FROM roles r
LEFT JOIN role_module_permissions rmp ON r.id = rmp.role_id
GROUP BY r.name
ORDER BY r.name;

-- Show department hierarchy
SELECT
    COALESCE(p.name, 'ROOT') AS parent_department,
    d.name AS department_name,
    d.description
FROM departments d
LEFT JOIN departments p ON d.parent_department_id = p.id
ORDER BY COALESCE(p.name, 'ROOT'), d.name;
