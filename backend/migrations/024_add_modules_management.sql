-- Migration: Add Module Management System
-- Purpose: Enable/disable modules and control user access via RBAC
-- Date: 2026-01-01

-- =====================================================
-- 1. MODULES TABLE - Master list of all Tier 2 and Tier 3 modules
-- =====================================================
CREATE TABLE IF NOT EXISTS modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id VARCHAR(100) UNIQUE NOT NULL,  -- e.g., 'british-council', 'grant-thornton'
    module_name VARCHAR(255) NOT NULL,        -- e.g., 'British Council POC'
    module_type VARCHAR(20) NOT NULL,         -- 'tier2' or 'tier3'
    tier INTEGER NOT NULL,                    -- 2 or 3
    description TEXT,
    category VARCHAR(100),                    -- e.g., 'Education', 'Finance', 'Construction'
    tier_2_dependencies TEXT[],               -- Array of Tier 2 module IDs this depends on
    is_enabled BOOLEAN DEFAULT true,          -- Global enable/disable flag
    is_beta BOOLEAN DEFAULT false,            -- Mark as beta/experimental
    requires_special_permission BOOLEAN DEFAULT false,  -- Requires explicit role permission
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_modules_module_id ON modules(module_id);
CREATE INDEX IF NOT EXISTS idx_modules_type ON modules(module_type);
CREATE INDEX IF NOT EXISTS idx_modules_tier ON modules(tier);
CREATE INDEX IF NOT EXISTS idx_modules_enabled ON modules(is_enabled);

-- =====================================================
-- 2. ROLE_MODULE_PERMISSIONS TABLE - RBAC for modules
-- =====================================================
CREATE TABLE IF NOT EXISTS role_module_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    module_id UUID NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    can_access BOOLEAN DEFAULT true,
    can_execute BOOLEAN DEFAULT true,          -- Can submit queries to module
    can_view_results BOOLEAN DEFAULT true,     -- Can view module results
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    granted_by UUID REFERENCES users(id),
    UNIQUE(role_id, module_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_role_module_perms_role ON role_module_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_role_module_perms_module ON role_module_permissions(module_id);

-- =====================================================
-- 3. USER_MODULE_OVERRIDES TABLE - User-specific overrides
-- =====================================================
CREATE TABLE IF NOT EXISTS user_module_overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    module_id UUID NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    can_access BOOLEAN DEFAULT true,
    can_execute BOOLEAN DEFAULT true,
    can_view_results BOOLEAN DEFAULT true,
    override_reason TEXT,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    granted_by UUID REFERENCES users(id),
    expires_at TIMESTAMP WITH TIME ZONE,       -- Optional expiration
    UNIQUE(user_id, module_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_user_module_overrides_user ON user_module_overrides(user_id);
CREATE INDEX IF NOT EXISTS idx_user_module_overrides_module ON user_module_overrides(module_id);
CREATE INDEX IF NOT EXISTS idx_user_module_overrides_expires ON user_module_overrides(expires_at);

-- =====================================================
-- 4. MODULE_USAGE_LOGS TABLE - Track module usage
-- =====================================================
CREATE TABLE IF NOT EXISTS module_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id UUID NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_id VARCHAR(255),
    action VARCHAR(50) NOT NULL,               -- 'access', 'query', 'view_status'
    request_data JSONB,
    response_data JSONB,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    latency_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for analytics
CREATE INDEX IF NOT EXISTS idx_module_usage_module ON module_usage_logs(module_id);
CREATE INDEX IF NOT EXISTS idx_module_usage_user ON module_usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_module_usage_created ON module_usage_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_module_usage_success ON module_usage_logs(success);

-- =====================================================
-- 5. SEED DATA - Insert all Tier 3 customer POCs
-- =====================================================
INSERT INTO modules (module_id, module_name, module_type, tier, description, category, tier_2_dependencies, is_enabled)
VALUES
    ('british-council', 'British Council POC', 'tier3', 3, 'Educational content delivery and assessment platform', 'Education', ARRAY['educational-content', 'generic-rag', 'multilingual-translator'], true),
    ('cru', 'CRU POC', 'tier3', 3, 'Construction resource utilization and project optimization', 'Construction', ARRAY['construction-monitor', 'estimator-one-au', 'mine-scope'], true),
    ('grant-thornton', 'Grant Thornton POC', 'tier3', 3, 'Financial audit and compliance automation', 'Finance', ARRAY['financial-anomaly', 'legal-document', 'document-intelligence'], true),
    ('gt-motive', 'GT Motive POC', 'tier3', 3, 'Automotive damage assessment and repair estimation', 'Insurance', ARRAY['insurance-risk', 'document-intelligence', 'predictive-analytics'], true),
    ('solera', 'Solera POC', 'tier3', 3, 'Insurance claims workflow automation and fraud detection', 'Insurance', ARRAY['insurance-risk', 'document-intelligence', 'financial-anomaly'], true),
    ('construction-monitor', 'Construction Monitor POC', 'tier3', 3, 'Real-time project monitoring and progress tracking', 'Construction', ARRAY['estimator-one-au', 'mine-scope', 'document-intelligence'], true)
ON CONFLICT (module_id) DO NOTHING;

-- =====================================================
-- 6. SEED DATA - Insert Tier 2 domain verticals (placeholders)
-- =====================================================
INSERT INTO modules (module_id, module_name, module_type, tier, description, category, tier_2_dependencies, is_enabled)
VALUES
    ('document-intelligence', 'Document Intelligence', 'tier2', 2, 'Advanced document processing and analysis', 'Core', ARRAY[]::TEXT[], true),
    ('generic-rag', 'Generic RAG', 'tier2', 2, 'General-purpose retrieval-augmented generation', 'Core', ARRAY[]::TEXT[], true),
    ('predictive-analytics', 'Predictive Analytics', 'tier2', 2, 'Machine learning-based predictions and forecasting', 'Analytics', ARRAY[]::TEXT[], true),
    ('multilingual-translator', 'Multilingual Translator', 'tier2', 2, 'Multi-language translation and localization', 'Language', ARRAY[]::TEXT[], true),
    ('financial-anomaly', 'Financial Anomaly Detection', 'tier2', 2, 'Fraud detection and financial anomaly identification', 'Finance', ARRAY[]::TEXT[], true),
    ('legal-document', 'Legal Document Processing', 'tier2', 2, 'Contract analysis and legal document management', 'Legal', ARRAY[]::TEXT[], true),
    ('insurance-risk', 'Insurance Risk Assessment', 'tier2', 2, 'Risk scoring and insurance claims analysis', 'Insurance', ARRAY[]::TEXT[], true),
    ('estimator-one-au', 'EstimatorOne (AU)', 'tier2', 2, 'Australian construction cost estimation', 'Construction', ARRAY[]::TEXT[], true),
    ('mine-scope', 'Mine Scope Analysis', 'tier2', 2, 'Mining project scope and resource planning', 'Mining', ARRAY[]::TEXT[], true),
    ('educational-content', 'Educational Content Management', 'tier2', 2, 'Course content delivery and assessment', 'Education', ARRAY[]::TEXT[], true)
ON CONFLICT (module_id) DO NOTHING;

-- =====================================================
-- 7. GRANT DEFAULT PERMISSIONS - Admin role gets all modules
-- =====================================================
DO $$
DECLARE
    admin_role_id UUID;
    module_record RECORD;
BEGIN
    -- Get admin role ID
    SELECT id INTO admin_role_id FROM roles WHERE name = 'admin' LIMIT 1;

    IF admin_role_id IS NOT NULL THEN
        -- Grant access to all modules for admin role
        FOR module_record IN SELECT id FROM modules
        LOOP
            INSERT INTO role_module_permissions (role_id, module_id, can_access, can_execute, can_view_results)
            VALUES (admin_role_id, module_record.id, true, true, true)
            ON CONFLICT (role_id, module_id) DO NOTHING;
        END LOOP;
    END IF;
END $$;

-- =====================================================
-- 8. ADD MODULE PERMISSIONS TO EXISTING PERMISSIONS TABLE
-- =====================================================
-- Add new action types for module management
INSERT INTO permissions (resource, action, description)
VALUES
    ('module', 'view', 'View available modules'),
    ('module', 'execute', 'Execute module queries'),
    ('module', 'manage', 'Enable/disable modules and manage permissions'),
    ('module', 'view_usage', 'View module usage statistics'),
    ('module', 'grant_access', 'Grant module access to users/roles')
ON CONFLICT (resource, action) DO NOTHING;

-- Grant module management permissions to admin role
DO $$
DECLARE
    admin_role_id UUID;
    perm_id UUID;
BEGIN
    SELECT id INTO admin_role_id FROM roles WHERE name = 'admin' LIMIT 1;

    IF admin_role_id IS NOT NULL THEN
        FOR perm_id IN SELECT id FROM permissions WHERE resource = 'module'
        LOOP
            INSERT INTO role_permissions (role_id, permission_id)
            VALUES (admin_role_id, perm_id)
            ON CONFLICT (role_id, permission_id) DO NOTHING;
        END LOOP;
    END IF;
END $$;

-- =====================================================
-- 9. HELPER FUNCTIONS
-- =====================================================

-- Function to check if user can access a module
CREATE OR REPLACE FUNCTION can_user_access_module(p_user_id UUID, p_module_id VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    v_module_enabled BOOLEAN;
    v_has_access BOOLEAN := false;
    v_user_override BOOLEAN;
    v_role_permission BOOLEAN;
BEGIN
    -- Check if module is globally enabled
    SELECT is_enabled INTO v_module_enabled
    FROM modules
    WHERE module_id = p_module_id;

    IF v_module_enabled = false THEN
        RETURN false;
    END IF;

    -- Check user-specific override first (highest priority)
    SELECT can_access INTO v_user_override
    FROM user_module_overrides umo
    JOIN modules m ON umo.module_id = m.id
    WHERE umo.user_id = p_user_id
      AND m.module_id = p_module_id
      AND (umo.expires_at IS NULL OR umo.expires_at > NOW());

    IF v_user_override IS NOT NULL THEN
        RETURN v_user_override;
    END IF;

    -- Check role-based permissions
    SELECT COALESCE(bool_or(rmp.can_access), false) INTO v_role_permission
    FROM user_roles ur
    JOIN role_module_permissions rmp ON ur.role_id = rmp.role_id
    JOIN modules m ON rmp.module_id = m.id
    WHERE ur.user_id = p_user_id
      AND m.module_id = p_module_id;

    RETURN COALESCE(v_role_permission, false);
END;
$$ LANGUAGE plpgsql;

-- Function to log module usage
CREATE OR REPLACE FUNCTION log_module_usage()
RETURNS TRIGGER AS $$
BEGIN
    -- This can be called from application code via trigger or direct insert
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 10. COMMENTS FOR DOCUMENTATION
-- =====================================================
COMMENT ON TABLE modules IS 'Master registry of all Tier 2 and Tier 3 modules with enable/disable flags';
COMMENT ON TABLE role_module_permissions IS 'RBAC permissions mapping roles to modules';
COMMENT ON TABLE user_module_overrides IS 'User-specific module access overrides that bypass role permissions';
COMMENT ON TABLE module_usage_logs IS 'Audit trail of all module usage for analytics and compliance';
COMMENT ON FUNCTION can_user_access_module IS 'Check if a user can access a specific module considering all permission layers';

-- Migration complete
