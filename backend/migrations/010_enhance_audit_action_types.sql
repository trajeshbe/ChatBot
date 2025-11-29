-- Migration: Enhance Audit Action Types
-- Version: 010
-- Date: 2025-11-28
-- Description: Expand ActionType enum to include comprehensive audit coverage

-- Drop existing action_type enum and recreate with all new types
ALTER TYPE action_type RENAME TO action_type_old;

CREATE TYPE action_type AS ENUM (
    -- Authentication & Session
    'login',
    'logout',
    'login_failed',
    'session_create',
    'session_destroy',
    'session_timeout',
    'password_change',
    'password_reset',

    -- Data Operations
    'query',
    'upload',
    'download',
    'scrape',
    'delete',
    'create',
    'update',
    'view',
    'export',

    -- Module Access
    'module_access',
    'module_exit',
    'feature_usage',

    -- Admin Operations
    'user_create',
    'user_update',
    'user_delete',
    'role_assign',
    'role_revoke',
    'permission_grant',
    'permission_deny',
    'settings_change',

    -- File Operations
    'file_delete',
    'file_move',
    'file_share',

    -- Project Operations
    'project_create',
    'project_update',
    'project_delete',
    'project_archive',

    -- API Operations
    'api_key_create',
    'api_key_revoke',
    'api_request',

    -- Errors & Security
    'error',
    'permission_denied',
    'unauthorized_access',
    'rate_limit_exceeded'
);

-- Update audit_logs table to use new enum
ALTER TABLE audit_logs
    ALTER COLUMN action TYPE action_type USING action::text::action_type;

-- Drop old enum
DROP TYPE action_type_old;

-- Add indexes for new action types
CREATE INDEX IF NOT EXISTS idx_audit_logs_action_category
    ON audit_logs(action) WHERE action IN ('login', 'logout', 'login_failed');

CREATE INDEX IF NOT EXISTS idx_audit_logs_security_events
    ON audit_logs(action) WHERE action IN ('permission_denied', 'unauthorized_access', 'rate_limit_exceeded');

CREATE INDEX IF NOT EXISTS idx_audit_logs_admin_actions
    ON audit_logs(action) WHERE action IN ('user_create', 'user_update', 'user_delete', 'role_assign', 'role_revoke');

-- Add comment
COMMENT ON TYPE action_type IS 'Comprehensive audit action types for all user operations';
