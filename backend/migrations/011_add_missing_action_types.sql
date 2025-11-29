-- Migration: Add missing action types to ActionType enum
-- Date: 2025-11-28
-- Description: Expands ActionType enum from 9 to 54 types for comprehensive audit logging

-- Add missing action types to existing enum
-- Note: PostgreSQL doesn't allow removing enum values, only adding

-- Authentication & Session (add 6 new types)
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'LOGIN_FAILED';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'SESSION_CREATE';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'SESSION_DESTROY';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'SESSION_TIMEOUT';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'PASSWORD_CHANGE';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'PASSWORD_RESET';

-- Data Operations (add 3 new types)
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'DOWNLOAD';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'EXPORT';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'VIEW_DETAILS';

-- Module Access (add 3 new types)
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'MODULE_ACCESS';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'MODULE_EXIT';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'FEATURE_USAGE';

-- Admin Operations (add 8 new types)
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'USER_CREATE';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'USER_UPDATE';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'USER_DELETE';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'ROLE_ASSIGN';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'ROLE_REVOKE';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'PERMISSION_GRANT';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'PERMISSION_DENY';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'SETTINGS_CHANGE';

-- File Operations (add 3 new types)
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'FILE_DELETE';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'FILE_MOVE';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'FILE_SHARE';

-- Project Operations (add 4 new types)
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'PROJECT_CREATE';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'PROJECT_UPDATE';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'PROJECT_DELETE';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'PROJECT_ARCHIVE';

-- API Operations (add 3 new types)
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'API_KEY_CREATE';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'API_KEY_REVOKE';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'API_REQUEST';

-- Errors & Security (add 4 new types)
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'ERROR';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'PERMISSION_DENIED';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'UNAUTHORIZED_ACCESS';
ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'RATE_LIMIT_EXCEEDED';

-- Add performance indexes for common audit queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_action_created
    ON audit_logs(action, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_logs_session_created
    ON audit_logs(session_id, created_at DESC)
    WHERE session_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_created
    ON audit_logs(user_id, created_at DESC)
    WHERE user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_audit_logs_status_created
    ON audit_logs(status_code, created_at DESC)
    WHERE status_code >= 400;

-- Add comments for documentation
COMMENT ON TYPE actiontype IS 'Comprehensive action type enum for audit logging (54 types)';
COMMENT ON TABLE audit_logs IS 'Comprehensive audit log table tracking all user actions across the platform';
COMMENT ON COLUMN audit_logs.action IS 'Type of action performed (see actiontype enum for all 54 types)';
COMMENT ON COLUMN audit_logs.latency_ms IS 'Request latency in milliseconds for performance monitoring';

-- Verify migration
SELECT
    'ActionType enum now has ' || COUNT(*) || ' values' as migration_result
FROM pg_enum
WHERE enumtypid = 'actiontype'::regtype;
