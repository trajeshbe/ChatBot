-- Migration 006: Add Modules, RolePermissions, and Projects tables
-- Created: 2025-11-28
-- Purpose: Support module-based RBAC and project management

BEGIN;

-- Create modules table
CREATE TABLE IF NOT EXISTS modules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    module_key VARCHAR(100) UNIQUE NOT NULL,
    module_name VARCHAR(255) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_info JSONB
);

CREATE INDEX IF NOT EXISTS idx_modules_module_key ON modules(module_key);
CREATE INDEX IF NOT EXISTS idx_modules_is_active ON modules(is_active);
CREATE INDEX IF NOT EXISTS idx_modules_display_order ON modules(display_order);

-- Create role_permissions table
CREATE TABLE IF NOT EXISTS role_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role VARCHAR(50) NOT NULL,
    module_id UUID NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    can_access BOOLEAN DEFAULT TRUE NOT NULL,
    can_create BOOLEAN DEFAULT FALSE,
    can_edit BOOLEAN DEFAULT FALSE,
    can_delete BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_info JSONB,
    UNIQUE(role, module_id)
);

CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON role_permissions(role);
CREATE INDEX IF NOT EXISTS idx_role_permissions_module_id ON role_permissions(module_id);

-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES users(id) ON DELETE SET NULL,
    department VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    archived_at TIMESTAMP WITH TIME ZONE,
    meta_info JSONB
);

CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON projects(owner_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_department ON projects(department);

-- Create project_members table
CREATE TABLE IF NOT EXISTS project_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_info JSONB,
    UNIQUE(project_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_project_members_project_id ON project_members(project_id);
CREATE INDEX IF NOT EXISTS idx_project_members_user_id ON project_members(user_id);

-- Insert default modules
INSERT INTO modules (module_key, module_name, description, icon, display_order) VALUES
('chat', 'Chat', 'RAG-powered chat interface', 'MessageSquare', 1),
('history', 'Chat History', 'View and manage chat conversations', 'History', 2),
('upload', 'Upload Files', 'Upload documents for RAG', 'Upload', 3),
('scrape', 'Web Scraping', 'Extract data from websites', 'Globe', 4),
('estimator', 'Project Estimator', 'Estimate project scope and effort', 'Calculator', 5),
('evaluation', 'Evaluation', 'RAG evaluation metrics', 'BarChart3', 6),
('tools', 'Tool Usage', 'Tool usage analytics', 'Wrench', 7),
('weights', 'Weights Config', 'RAG system configuration', 'Sliders', 8),
('admin', 'Admin', 'System administration', 'Shield', 9)
ON CONFLICT (module_key) DO NOTHING;

-- Grant all modules to admin role
INSERT INTO role_permissions (role, module_id, can_access, can_create, can_edit, can_delete)
SELECT
    'admin'::VARCHAR(50),
    id,
    TRUE,
    TRUE,
    TRUE,
    TRUE
FROM modules
ON CONFLICT (role, module_id) DO NOTHING;

-- Grant basic modules to user role
INSERT INTO role_permissions (role, module_id, can_access, can_create, can_edit, can_delete)
SELECT
    'user'::VARCHAR(50),
    id,
    TRUE,
    TRUE,
    FALSE,
    FALSE
FROM modules
WHERE module_key IN ('chat', 'history', 'upload', 'scrape', 'estimator')
ON CONFLICT (role, module_id) DO NOTHING;

-- Grant view-only modules to viewer role
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
ON CONFLICT (role, module_id) DO NOTHING;

COMMIT;
