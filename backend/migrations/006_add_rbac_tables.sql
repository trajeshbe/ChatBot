-- Migration 006: Add RBAC Tables
-- Description: Create Role-Based Access Control tables for enterprise security
-- Date: 2025-11-27
-- Dependencies: 005_add_tool_usage_tracking.sql

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- ROLES TABLE
-- ============================================================================
-- Stores user roles (Admin, Manager, User, etc.)
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    parent_role_id UUID REFERENCES roles(id) ON DELETE SET NULL,
    description TEXT,
    is_system_role BOOLEAN DEFAULT FALSE,  -- Cannot be deleted if true
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for role hierarchy queries
CREATE INDEX idx_roles_parent ON roles(parent_role_id);
CREATE INDEX idx_roles_name ON roles(name);

-- ============================================================================
-- DEPARTMENTS TABLE
-- ============================================================================
-- Stores organizational departments and teams
CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    parent_department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for department hierarchy
CREATE INDEX idx_departments_parent ON departments(parent_department_id);
CREATE INDEX idx_departments_name ON departments(name);
CREATE INDEX idx_departments_active ON departments(is_active);

-- ============================================================================
-- MODULES TABLE
-- ============================================================================
-- Stores application modules/features that can be accessed
CREATE TABLE IF NOT EXISTS modules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,  -- Unique identifier for code
    description TEXT,
    icon VARCHAR(50),  -- Lucide icon name
    route VARCHAR(100),  -- Frontend route
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for module queries
CREATE INDEX idx_modules_code ON modules(code);
CREATE INDEX idx_modules_active ON modules(is_active);
CREATE INDEX idx_modules_order ON modules(display_order);

-- ============================================================================
-- ROLE-MODULE PERMISSIONS TABLE
-- ============================================================================
-- Defines what permissions each role has for each module
CREATE TABLE IF NOT EXISTS role_module_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    module_id UUID NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    can_read BOOLEAN DEFAULT FALSE,
    can_write BOOLEAN DEFAULT FALSE,
    can_delete BOOLEAN DEFAULT FALSE,
    can_share BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(role_id, module_id)
);

-- Indexes for permission checks
CREATE INDEX idx_permissions_role ON role_module_permissions(role_id);
CREATE INDEX idx_permissions_module ON role_module_permissions(module_id);
CREATE INDEX idx_permissions_read ON role_module_permissions(can_read);

-- ============================================================================
-- USER-ROLE ASSIGNMENTS TABLE
-- ============================================================================
-- Assigns roles to users (users can have multiple roles)
CREATE TABLE IF NOT EXISTS user_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_by UUID REFERENCES users(id) ON DELETE SET NULL,
    expires_at TIMESTAMP WITH TIME ZONE,  -- Optional expiration
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(user_id, role_id, department_id)
);

-- Indexes for user role queries
CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_role ON user_roles(role_id);
CREATE INDEX idx_user_roles_department ON user_roles(department_id);
CREATE INDEX idx_user_roles_active ON user_roles(is_active);
CREATE INDEX idx_user_roles_assigned_by ON user_roles(assigned_by);

-- ============================================================================
-- UPDATE TRIGGERS
-- ============================================================================
-- Auto-update updated_at timestamp on roles
CREATE OR REPLACE FUNCTION update_roles_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER roles_update_timestamp
    BEFORE UPDATE ON roles
    FOR EACH ROW
    EXECUTE FUNCTION update_roles_timestamp();

-- Auto-update updated_at timestamp on departments
CREATE OR REPLACE FUNCTION update_departments_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER departments_update_timestamp
    BEFORE UPDATE ON departments
    FOR EACH ROW
    EXECUTE FUNCTION update_departments_timestamp();

-- Auto-update updated_at timestamp on modules
CREATE OR REPLACE FUNCTION update_modules_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER modules_update_timestamp
    BEFORE UPDATE ON modules
    FOR EACH ROW
    EXECUTE FUNCTION update_modules_timestamp();

-- Auto-update updated_at timestamp on permissions
CREATE OR REPLACE FUNCTION update_permissions_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER permissions_update_timestamp
    BEFORE UPDATE ON role_module_permissions
    FOR EACH ROW
    EXECUTE FUNCTION update_permissions_timestamp();

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE roles IS 'User roles for RBAC system';
COMMENT ON TABLE departments IS 'Organizational departments and teams';
COMMENT ON TABLE modules IS 'Application modules/features';
COMMENT ON TABLE role_module_permissions IS 'Permissions mapping roles to modules';
COMMENT ON TABLE user_roles IS 'User role assignments';

COMMENT ON COLUMN roles.is_system_role IS 'System roles cannot be deleted';
COMMENT ON COLUMN role_module_permissions.can_read IS 'Permission to view/read';
COMMENT ON COLUMN role_module_permissions.can_write IS 'Permission to create/edit';
COMMENT ON COLUMN role_module_permissions.can_delete IS 'Permission to delete';
COMMENT ON COLUMN role_module_permissions.can_share IS 'Permission to share with others';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Run these to verify migration success:
-- SELECT COUNT(*) FROM roles;
-- SELECT COUNT(*) FROM departments;
-- SELECT COUNT(*) FROM modules;
-- SELECT COUNT(*) FROM role_module_permissions;
-- SELECT COUNT(*) FROM user_roles;
