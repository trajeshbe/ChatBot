-- ============================================================================
-- Enterprise RAG Chatbot - Complete Database Schema
-- ============================================================================
-- File: 02_complete_schema.sql
-- Created: 2026-01-07
-- Purpose: Comprehensive schema with all 50 tables in correct dependency order
-- Version: 2.0.0
--
-- Description:
--   This file contains ALL table definitions for the Enterprise RAG Chatbot
--   system, organized in correct dependency order (tables with no FKs first,
--   then tables that reference them).
--
-- Table Count: 50 tables
-- Embedding Dimension: VECTOR(384) for primary embeddings
-- Additional Embeddings: VECTOR(512), VECTOR(256), VECTOR(768) for specialized content
--
-- Usage:
--   psql -U postgres -d ragchatbot -f backend/sql/02_complete_schema.sql
--
-- Note: This file does NOT include seed data. For data, see:
--   - backend/sql/03_seed_data.sql
--   - backend/migrations/007_seed_rbac_data.sql
-- ============================================================================

BEGIN;

-- ============================================================================
-- EXTENSIONS
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================================
-- ENUMS
-- ============================================================================
-- User role enum (legacy, used by old user_role column)
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('admin', 'user', 'viewer', 'api_user');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Action types enum for audit logging
DO $$ BEGIN
    CREATE TYPE action_type AS ENUM (
        'query', 'upload', 'scrape', 'delete', 'login', 'logout',
        'create', 'update', 'view'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- LAYER 1: TABLES WITH NO FOREIGN KEY DEPENDENCIES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: departments
-- Purpose: Organizational departments (top-level org structure)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    parent_department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_info JSONB
);

CREATE INDEX IF NOT EXISTS idx_departments_name ON departments(name);
CREATE INDEX IF NOT EXISTS idx_departments_code ON departments(code);
CREATE INDEX IF NOT EXISTS idx_departments_is_active ON departments(is_active);
CREATE INDEX IF NOT EXISTS idx_departments_parent ON departments(parent_department_id);

COMMENT ON TABLE departments IS 'Organizational departments (top-level org structure)';
COMMENT ON COLUMN departments.parent_department_id IS 'For hierarchical departments';

-- ----------------------------------------------------------------------------
-- Table: roles
-- Purpose: User roles for RBAC system (Admin, Manager, User, etc.)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    parent_role_id UUID REFERENCES roles(id) ON DELETE SET NULL,
    description TEXT,
    is_system_role BOOLEAN DEFAULT FALSE,  -- Cannot be deleted if true
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_roles_parent ON roles(parent_role_id);
CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);

COMMENT ON TABLE roles IS 'User roles for RBAC system';
COMMENT ON COLUMN roles.is_system_role IS 'System roles cannot be deleted';

-- ----------------------------------------------------------------------------
-- Table: modules
-- Purpose: Application modules/features that can be accessed
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS modules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    module_key VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(100) UNIQUE NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,  -- Unique identifier for code
    module_name VARCHAR(255) NOT NULL,
    description TEXT,
    icon VARCHAR(50),  -- Lucide icon name
    route VARCHAR(100),  -- Frontend route
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_info JSONB
);

CREATE INDEX IF NOT EXISTS idx_modules_code ON modules(code);
CREATE INDEX IF NOT EXISTS idx_modules_module_key ON modules(module_key);
CREATE INDEX IF NOT EXISTS idx_modules_active ON modules(is_active);
CREATE INDEX IF NOT EXISTS idx_modules_is_active ON modules(is_active);
CREATE INDEX IF NOT EXISTS idx_modules_order ON modules(display_order);
CREATE INDEX IF NOT EXISTS idx_modules_display_order ON modules(display_order);

COMMENT ON TABLE modules IS 'Application modules/features that can be accessed';

-- ----------------------------------------------------------------------------
-- Table: conversations
-- Purpose: Chat conversations (legacy, still used for conversation tracking)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255),
    summary TEXT,
    project_id UUID,  -- FK added later after projects table exists
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE conversations IS 'Chat conversations (legacy structure)';

-- ============================================================================
-- LAYER 2: TABLES THAT DEPEND ON LAYER 1 (departments, roles, modules)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: teams
-- Purpose: Teams within departments (sub-org structure)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL,
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    description TEXT,
    team_lead_id UUID,  -- FK to users, added after users table exists
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_info JSONB,
    UNIQUE(department_id, name),
    UNIQUE(department_id, code)
);

CREATE INDEX IF NOT EXISTS idx_teams_name ON teams(name);
CREATE INDEX IF NOT EXISTS idx_teams_code ON teams(code);
CREATE INDEX IF NOT EXISTS idx_teams_department_id ON teams(department_id);
CREATE INDEX IF NOT EXISTS idx_teams_team_lead_id ON teams(team_lead_id);
CREATE INDEX IF NOT EXISTS idx_teams_is_active ON teams(is_active);

COMMENT ON TABLE teams IS 'Teams within departments (sub-org structure)';
COMMENT ON COLUMN teams.department_id IS 'Foreign key to departments (CASCADE delete)';

-- ----------------------------------------------------------------------------
-- Table: role_module_permissions
-- Purpose: Defines what permissions each role has for each module
-- ----------------------------------------------------------------------------
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

CREATE INDEX IF NOT EXISTS idx_permissions_role ON role_module_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_permissions_module ON role_module_permissions(module_id);
CREATE INDEX IF NOT EXISTS idx_permissions_read ON role_module_permissions(can_read);

COMMENT ON TABLE role_module_permissions IS 'Permissions mapping roles to modules';
COMMENT ON COLUMN role_module_permissions.can_read IS 'Permission to view/read';
COMMENT ON COLUMN role_module_permissions.can_write IS 'Permission to create/edit';
COMMENT ON COLUMN role_module_permissions.can_delete IS 'Permission to delete';
COMMENT ON COLUMN role_module_permissions.can_share IS 'Permission to share with others';

-- ----------------------------------------------------------------------------
-- Table: role_permissions
-- Purpose: Module-based RBAC permissions (alternative permission structure)
-- ----------------------------------------------------------------------------
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

COMMENT ON TABLE role_permissions IS 'Module-based RBAC permissions';

-- ----------------------------------------------------------------------------
-- Table: scraping_configs
-- Purpose: Domain-specific scraping policies, rate limits, and API configurations
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS scraping_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain VARCHAR(255) NOT NULL UNIQUE,

    -- Compliance settings
    allow_scraping BOOLEAN DEFAULT FALSE,
    robots_txt_compliant BOOLEAN DEFAULT TRUE,
    robots_txt_url VARCHAR(512),
    robots_txt_checked_at TIMESTAMP WITH TIME ZONE,

    -- Rate limiting
    rate_limit_enabled BOOLEAN DEFAULT TRUE,
    rate_limit_requests_per_minute INTEGER DEFAULT 10,
    rate_limit_delay_seconds FLOAT DEFAULT 2.0,
    max_concurrent_requests INTEGER DEFAULT 1,

    -- API configuration (for sites with official APIs)
    use_api BOOLEAN DEFAULT FALSE,
    api_endpoint VARCHAR(512),
    api_key_encrypted TEXT,  -- Encrypted API key
    api_documentation_url VARCHAR(512),

    -- Terms of Service compliance
    terms_checked BOOLEAN DEFAULT FALSE,
    terms_url VARCHAR(512),
    terms_checked_at TIMESTAMP WITH TIME ZONE,
    terms_notes TEXT,

    -- Permission tracking
    permission_granted BOOLEAN DEFAULT FALSE,
    permission_contact VARCHAR(255),  -- Email/contact who granted permission
    permission_granted_at TIMESTAMP WITH TIME ZONE,
    permission_expires_at TIMESTAMP WITH TIME ZONE,
    permission_document_url VARCHAR(512),

    -- Scraping method preferences
    preferred_method VARCHAR(50) DEFAULT 'auto',  -- 'api', 'playwright', 'requests', 'auto'
    user_agent VARCHAR(512),
    custom_headers JSONB,

    -- Notes and metadata
    notes TEXT,
    created_by UUID,  -- FK to users, added later
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_scraped_at TIMESTAMP WITH TIME ZONE,

    -- Status tracking
    status VARCHAR(50) DEFAULT 'active',  -- 'active', 'blocked', 'suspended', 'deprecated'
    block_reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_scraping_configs_domain ON scraping_configs(domain);
CREATE INDEX IF NOT EXISTS idx_scraping_configs_status ON scraping_configs(status);
CREATE INDEX IF NOT EXISTS idx_scraping_configs_allow_scraping ON scraping_configs(allow_scraping);

COMMENT ON TABLE scraping_configs IS 'Domain-specific scraping policies and rate limits';

-- ----------------------------------------------------------------------------
-- Table: domain_statistics
-- Purpose: Aggregate scraping stats per domain
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS domain_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain VARCHAR(255) NOT NULL UNIQUE,

    -- Request counts
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    blocked_requests INTEGER DEFAULT 0,

    -- Traffic stats
    total_bytes_downloaded BIGINT DEFAULT 0,
    avg_response_time_ms FLOAT,

    -- Rate limiting violations
    rate_limit_violations INTEGER DEFAULT 0,
    robots_txt_violations INTEGER DEFAULT 0,

    -- Time tracking
    first_scraped_at TIMESTAMP WITH TIME ZONE,
    last_scraped_at TIMESTAMP WITH TIME ZONE,
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE domain_statistics IS 'Aggregate scraping statistics per domain';

-- ----------------------------------------------------------------------------
-- Table: extraction_templates
-- Purpose: Templates for data extraction with field definitions
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS extraction_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_type VARCHAR(50) NOT NULL,  -- excel, csv, json, yaml
    template_file_path VARCHAR(512),     -- MinIO path to template file
    schema_definition JSONB NOT NULL,    -- Parsed template schema

    -- Fields definition
    fields JSONB NOT NULL,               -- Array of field definitions
    validation_rules JSONB,              -- Validation rules per field
    transformation_rules JSONB,          -- Transformation rules per field

    -- Metadata
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT template_name_version_unique UNIQUE(name, version)
);

CREATE INDEX IF NOT EXISTS idx_extraction_templates_active ON extraction_templates(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_extraction_templates_type ON extraction_templates(template_type);

COMMENT ON TABLE extraction_templates IS 'Templates for data extraction with field definitions';

-- ----------------------------------------------------------------------------
-- Table: saved_css_templates
-- Purpose: User-created CSS selector templates for reuse
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS saved_css_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Template identification
    name VARCHAR(255) UNIQUE NOT NULL,           -- Internal ID (lowercase, underscore-separated)
    display_name VARCHAR(255) NOT NULL,          -- User-friendly name shown in UI
    description TEXT,

    -- URL pattern matching
    url_pattern VARCHAR(512),                    -- Optional URL pattern for auto-detection

    -- Extraction configuration
    wait_for_selector VARCHAR(512),              -- CSS selector to wait for
    fields JSONB NOT NULL,                       -- Array of ExtractionField objects

    -- Pagination (optional)
    pagination_selector VARCHAR(512),            -- CSS selector for next page button
    max_pages INTEGER DEFAULT 1,

    -- Usage tracking
    use_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,

    -- Ownership (optional)
    created_by VARCHAR(255),

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_saved_css_templates_name ON saved_css_templates(name);
CREATE INDEX IF NOT EXISTS idx_saved_css_templates_active ON saved_css_templates(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_saved_css_templates_url_pattern ON saved_css_templates(url_pattern) WHERE url_pattern IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_saved_css_templates_use_count ON saved_css_templates(use_count DESC);

COMMENT ON TABLE saved_css_templates IS 'User-created CSS selector templates for web scraping';

-- ----------------------------------------------------------------------------
-- Table: system_config
-- Purpose: System-wide configuration stored in database
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS system_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(255) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    config_type VARCHAR(50) DEFAULT 'string',
    category VARCHAR(100),
    description TEXT,
    is_encrypted BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by UUID,  -- FK to users, added later
    meta_info JSONB
);

CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(config_key);
CREATE INDEX IF NOT EXISTS idx_system_config_category ON system_config(category);
CREATE INDEX IF NOT EXISTS idx_system_config_active ON system_config(is_active);

COMMENT ON TABLE system_config IS 'System-wide configuration (replaces hardcoded values)';
COMMENT ON COLUMN system_config.config_type IS 'Data type: string, integer, boolean, json, url, api_key';
COMMENT ON COLUMN system_config.is_encrypted IS 'Whether value is encrypted (for API keys, secrets)';

-- ----------------------------------------------------------------------------
-- Table: models
-- Purpose: Unified registry for all LLM models
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) DEFAULT 'text',
    context_length INTEGER,
    max_tokens INTEGER,
    supports_functions BOOLEAN DEFAULT FALSE,
    supports_vision BOOLEAN DEFAULT FALSE,
    supports_streaming BOOLEAN DEFAULT TRUE,
    cost_per_1k_input DECIMAL(10, 6),
    cost_per_1k_output DECIMAL(10, 6),
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    source VARCHAR(50) DEFAULT 'manual',
    auto_discovered_at TIMESTAMP WITH TIME ZONE,
    last_verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_info JSONB
);

CREATE INDEX IF NOT EXISTS idx_models_model_id ON models(model_id);
CREATE INDEX IF NOT EXISTS idx_models_provider ON models(provider);
CREATE INDEX IF NOT EXISTS idx_models_type ON models(model_type);
CREATE INDEX IF NOT EXISTS idx_models_is_active ON models(is_active);
CREATE INDEX IF NOT EXISTS idx_models_is_default ON models(is_default);
CREATE INDEX IF NOT EXISTS idx_models_source ON models(source);

COMMENT ON TABLE models IS 'Unified registry for all LLM models (OpenAI, Claude, Ollama, fine-tuned)';
COMMENT ON COLUMN models.provider IS 'Provider: openai, anthropic, ollama, vllm, finetuned';
COMMENT ON COLUMN models.model_type IS 'Type: text, code, vision, multimodal';
COMMENT ON COLUMN models.source IS 'Source: manual, auto_discovered, finetuned';

-- ============================================================================
-- LAYER 3: USERS TABLE (depends on departments, teams)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: users
-- Purpose: User accounts with RBAC support
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    hashed_password VARCHAR(255) NOT NULL,
    role user_role DEFAULT 'user' NOT NULL,  -- Legacy enum role
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,

    -- Organizational fields
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,

    -- Legacy VARCHAR fields (may be deprecated)
    department VARCHAR(100),
    team VARCHAR(100),

    meta_info JSONB
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_department_id ON users(department_id);
CREATE INDEX IF NOT EXISTS idx_users_team_id ON users(team_id);
CREATE INDEX IF NOT EXISTS idx_users_team ON users(team);
CREATE INDEX IF NOT EXISTS idx_users_department ON users(department);

COMMENT ON TABLE users IS 'User accounts with RBAC support';

-- Now add team_lead_id FK to teams table
ALTER TABLE teams ADD CONSTRAINT fk_teams_team_lead
    FOREIGN KEY (team_lead_id) REFERENCES users(id) ON DELETE SET NULL;

-- ============================================================================
-- LAYER 4: TABLES THAT DEPEND ON USERS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: projects
-- Purpose: Projects for organizing documents and resources
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Organizational fields (FKs)
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,

    -- Legacy VARCHAR fields
    department VARCHAR(100),
    team VARCHAR(100),

    -- Embedding configuration (Phase 1)
    primary_embedding_config VARCHAR(100) DEFAULT 'all_minilm_l6_v2_384',
    code_embedding_config VARCHAR(100),
    visual_embedding_config VARCHAR(100),
    table_embedding_config VARCHAR(100),
    numerical_embedding_config VARCHAR(100),
    embedding_api_keys JSONB DEFAULT '{}',

    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    archived_at TIMESTAMP WITH TIME ZONE,
    meta_info JSONB
);

CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON projects(owner_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_department ON projects(department);
CREATE INDEX IF NOT EXISTS idx_projects_team ON projects(team);
CREATE INDEX IF NOT EXISTS idx_projects_department_id ON projects(department_id);
CREATE INDEX IF NOT EXISTS idx_projects_team_id ON projects(team_id);
CREATE INDEX IF NOT EXISTS idx_projects_primary_embedding ON projects(primary_embedding_config);

COMMENT ON TABLE projects IS 'Projects for organizing documents and resources';
COMMENT ON COLUMN projects.primary_embedding_config IS 'Primary embedding model config ID (default: 384-dim MiniLM)';

-- Now add project_id FK to conversations table
ALTER TABLE conversations ADD CONSTRAINT fk_conversations_project
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_conversations_project_id ON conversations(project_id);

-- ----------------------------------------------------------------------------
-- Table: user_roles
-- Purpose: User role assignments (many-to-many)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_by UUID REFERENCES users(id) ON DELETE SET NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(user_id, role_id, department_id)
);

CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_department ON user_roles(department_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_active ON user_roles(is_active);
CREATE INDEX IF NOT EXISTS idx_user_roles_assigned_by ON user_roles(assigned_by);

COMMENT ON TABLE user_roles IS 'User role assignments';

-- ----------------------------------------------------------------------------
-- Table: user_teams
-- Purpose: User team assignments (many-to-many)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_by UUID REFERENCES users(id) ON DELETE SET NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    UNIQUE(user_id, team_id)
);

CREATE INDEX IF NOT EXISTS idx_user_teams_user ON user_teams(user_id);
CREATE INDEX IF NOT EXISTS idx_user_teams_team ON user_teams(team_id);
CREATE INDEX IF NOT EXISTS idx_user_teams_primary ON user_teams(user_id, is_primary) WHERE is_primary = TRUE;

COMMENT ON TABLE user_teams IS 'User team assignments (many-to-many)';

-- ----------------------------------------------------------------------------
-- Table: project_members
-- Purpose: Project member assignments
-- ----------------------------------------------------------------------------
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

COMMENT ON TABLE project_members IS 'Project member assignments';

-- ----------------------------------------------------------------------------
-- Table: api_keys
-- Purpose: API keys for programmatic access
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    key_prefix VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used TIMESTAMP WITH TIME ZONE,
    meta_info JSONB
);

CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);

COMMENT ON TABLE api_keys IS 'API keys for programmatic access';

-- ----------------------------------------------------------------------------
-- Table: api_credentials
-- Purpose: Encrypted API keys for LLM providers
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS api_credentials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider VARCHAR(50) UNIQUE NOT NULL,
    api_key_encrypted BYTEA NOT NULL,
    encryption_key_id VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT provider_not_empty CHECK (provider != ''),
    CONSTRAINT api_key_encrypted_not_empty CHECK (length(api_key_encrypted) > 0)
);

CREATE INDEX IF NOT EXISTS idx_api_credentials_provider ON api_credentials(provider);
CREATE INDEX IF NOT EXISTS idx_api_credentials_is_active ON api_credentials(is_active);

COMMENT ON TABLE api_credentials IS 'Encrypted API keys for LLM providers';

-- ----------------------------------------------------------------------------
-- Table: api_key_access_log
-- Purpose: Audit log for API key access
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS api_key_access_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider VARCHAR(50) NOT NULL,
    user_id UUID REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    ip_address VARCHAR(50),
    user_agent TEXT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT action_valid CHECK (action IN ('created', 'updated', 'accessed', 'deleted', 'validated', 'failed_validation'))
);

CREATE INDEX IF NOT EXISTS idx_api_key_access_log_provider ON api_key_access_log(provider);
CREATE INDEX IF NOT EXISTS idx_api_key_access_log_user_id ON api_key_access_log(user_id);
CREATE INDEX IF NOT EXISTS idx_api_key_access_log_created_at ON api_key_access_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_api_key_access_log_action ON api_key_access_log(action);

COMMENT ON TABLE api_key_access_log IS 'Audit log for API key access';

-- ----------------------------------------------------------------------------
-- Table: chat_sessions
-- Purpose: Chat sessions with user tracking
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    title VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    -- Organizational fields (FKs)
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,

    -- Legacy VARCHAR fields
    department VARCHAR(100),
    team VARCHAR(100),

    meta_info JSONB
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_active ON chat_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_project_id ON chat_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_sessions_department_id ON chat_sessions(department_id);
CREATE INDEX IF NOT EXISTS idx_sessions_team_id ON chat_sessions(team_id);
CREATE INDEX IF NOT EXISTS idx_sessions_department ON chat_sessions(department);
CREATE INDEX IF NOT EXISTS idx_sessions_team ON chat_sessions(team);

COMMENT ON TABLE chat_sessions IS 'Chat sessions with user tracking';

-- ----------------------------------------------------------------------------
-- Table: documents
-- Purpose: Uploaded/scraped documents
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_type VARCHAR(100),
    file_size BIGINT,
    source_type VARCHAR(50) NOT NULL,
    source_url TEXT,
    processing_status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    processed BOOLEAN DEFAULT FALSE,
    processing_error TEXT,
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Project tracking
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Organizational fields (FKs)
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,

    -- Legacy VARCHAR fields
    department VARCHAR(100),
    team VARCHAR(100),
    user_role VARCHAR(50),

    minio_path VARCHAR(1024),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_source_type ON documents(source_type);
CREATE INDEX IF NOT EXISTS idx_documents_processing_status ON documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents(project_id);
CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by ON documents(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_documents_department ON documents(department);
CREATE INDEX IF NOT EXISTS idx_documents_team ON documents(team);
CREATE INDEX IF NOT EXISTS idx_documents_user_role ON documents(user_role);
CREATE INDEX IF NOT EXISTS idx_documents_minio_path ON documents(minio_path);
CREATE INDEX IF NOT EXISTS idx_documents_department_id ON documents(department_id);
CREATE INDEX IF NOT EXISTS idx_documents_team_id ON documents(team_id);
CREATE INDEX IF NOT EXISTS idx_documents_dept_team ON documents(department, team);
CREATE INDEX IF NOT EXISTS idx_documents_dept_team_user ON documents(department, team, uploaded_by);
CREATE INDEX IF NOT EXISTS idx_documents_role_dept ON documents(user_role, department);
CREATE INDEX IF NOT EXISTS idx_documents_project_user ON documents(project_id, uploaded_by);
CREATE INDEX IF NOT EXISTS idx_documents_user_date ON documents(uploaded_by, upload_date DESC);
CREATE INDEX IF NOT EXISTS idx_documents_project_date ON documents(project_id, upload_date DESC);
CREATE INDEX IF NOT EXISTS idx_documents_filename_trgm ON documents USING gin(filename gin_trgm_ops);

COMMENT ON TABLE documents IS 'Uploaded/scraped documents';

-- ----------------------------------------------------------------------------
-- Table: document_chunks
-- Purpose: Document chunks with vector embeddings
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,

    -- Primary embedding (384-dim)
    embedding VECTOR(384),

    -- Specialized embeddings (multi-column vector storage)
    table_embedding VECTOR(512),
    visual_embedding VECTOR(512),
    numerical_embedding VECTOR(256),
    code_embedding VECTOR(768),

    -- Embedding metadata
    embedding_strategy VARCHAR(50),
    embedding_metadata JSONB,

    -- Project tracking (denormalized)
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Organizational fields (FKs)
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,

    -- Legacy VARCHAR fields
    department VARCHAR(100),
    team VARCHAR(100),

    meta_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT check_embedding_strategy CHECK (
        embedding_strategy IS NULL OR
        embedding_strategy IN (
            'text_semantic',
            'table_structure',
            'vision',
            'numerical',
            'code',
            'hybrid'
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_chunks_table_embedding ON document_chunks USING ivfflat (table_embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_chunks_visual_embedding ON document_chunks USING ivfflat (visual_embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_chunks_numerical_embedding ON document_chunks USING ivfflat (numerical_embedding vector_l2_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_chunks_code_embedding ON document_chunks USING ivfflat (code_embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_strategy ON document_chunks(embedding_strategy);
CREATE INDEX IF NOT EXISTS idx_chunks_project_id ON document_chunks(project_id);
CREATE INDEX IF NOT EXISTS idx_chunks_uploaded_by ON document_chunks(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_chunks_department ON document_chunks(department);
CREATE INDEX IF NOT EXISTS idx_chunks_team ON document_chunks(team);
CREATE INDEX IF NOT EXISTS idx_chunks_department_id ON document_chunks(department_id);
CREATE INDEX IF NOT EXISTS idx_chunks_team_id ON document_chunks(team_id);
CREATE INDEX IF NOT EXISTS idx_chunks_dept_team ON document_chunks(department, team);
CREATE INDEX IF NOT EXISTS idx_chunks_project_user ON document_chunks(project_id, uploaded_by);

COMMENT ON TABLE document_chunks IS 'Document chunks with vector embeddings (384-dim primary + specialized)';
COMMENT ON COLUMN document_chunks.embedding IS 'Primary vector embedding (384-dim) for text semantic search';
COMMENT ON COLUMN document_chunks.table_embedding IS 'Table structure embedding (512-dim)';
COMMENT ON COLUMN document_chunks.visual_embedding IS 'Vision embedding (512-dim) using CLIP';
COMMENT ON COLUMN document_chunks.numerical_embedding IS 'Numerical embedding (256-dim)';
COMMENT ON COLUMN document_chunks.code_embedding IS 'Code embedding (768-dim) using CodeBERT';

-- ----------------------------------------------------------------------------
-- Table: document_permissions
-- Purpose: Fine-grained document access control
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS document_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role user_role,
    can_read BOOLEAN DEFAULT TRUE,
    can_write BOOLEAN DEFAULT FALSE,
    can_delete BOOLEAN DEFAULT FALSE,
    can_share BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    meta_info JSONB
);

CREATE INDEX IF NOT EXISTS idx_document_permissions_document ON document_permissions(document_id);
CREATE INDEX IF NOT EXISTS idx_document_permissions_user ON document_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_document_permissions_role ON document_permissions(role);

COMMENT ON TABLE document_permissions IS 'Fine-grained document access control';

-- ----------------------------------------------------------------------------
-- Table: query_cache
-- Purpose: Semantic cache for RAG queries
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS query_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_text TEXT NOT NULL,
    query_embedding VECTOR(384),
    response JSONB NOT NULL,
    model_id VARCHAR(100),
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_query_cache_embedding ON query_cache USING ivfflat (query_embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_query_cache_created_at ON query_cache(created_at DESC);

COMMENT ON TABLE query_cache IS 'Semantic cache for RAG queries';

-- ----------------------------------------------------------------------------
-- Table: web_scrape_jobs
-- Purpose: Web scraping job tracking
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS web_scrape_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    scrape_prompt TEXT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Project tracking
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    scraped_by UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Organizational fields (FKs)
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,

    -- Legacy VARCHAR fields
    department VARCHAR(100),
    team VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_web_scrape_jobs_status ON web_scrape_jobs(status);
CREATE INDEX IF NOT EXISTS idx_web_scrape_jobs_created_at ON web_scrape_jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_project_id ON web_scrape_jobs(project_id);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_scraped_by ON web_scrape_jobs(scraped_by);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_department ON web_scrape_jobs(department);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_team ON web_scrape_jobs(team);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_department_id ON web_scrape_jobs(department_id);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_team_id ON web_scrape_jobs(team_id);

COMMENT ON TABLE web_scrape_jobs IS 'Web scraping job tracking';

-- ----------------------------------------------------------------------------
-- Table: scraping_audit_log
-- Purpose: Audit log for scraping attempts
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS scraping_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_id UUID REFERENCES scraping_configs(id) ON DELETE SET NULL,
    domain VARCHAR(255) NOT NULL,
    url VARCHAR(1024) NOT NULL,

    -- Request details
    method VARCHAR(50),
    user_agent VARCHAR(512),

    -- Response details
    status_code INTEGER,
    success BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    response_time_ms FLOAT,
    bytes_downloaded INTEGER,

    -- Compliance tracking
    robots_txt_allowed BOOLEAN,
    rate_limit_respected BOOLEAN,
    permission_verified BOOLEAN,

    -- Metadata
    user_id UUID REFERENCES users(id),
    session_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scraping_audit_domain ON scraping_audit_log(domain);
CREATE INDEX IF NOT EXISTS idx_scraping_audit_created_at ON scraping_audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_scraping_audit_success ON scraping_audit_log(success);

COMMENT ON TABLE scraping_audit_log IS 'Audit log for all scraping attempts';

-- ----------------------------------------------------------------------------
-- Table: messages
-- Purpose: Chat messages (legacy)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    model VARCHAR(100),
    model_used VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);

COMMENT ON TABLE messages IS 'Chat messages (legacy structure)';

-- ----------------------------------------------------------------------------
-- Table: session_documents
-- Purpose: Short-term memory (session-scoped documents)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS session_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    priority INTEGER DEFAULT 0,
    expires_at TIMESTAMP WITH TIME ZONE,
    meta_info JSONB,
    UNIQUE(session_id, document_id)
);

CREATE INDEX IF NOT EXISTS idx_session_documents_session ON session_documents(session_id);
CREATE INDEX IF NOT EXISTS idx_session_documents_document ON session_documents(document_id);
CREATE INDEX IF NOT EXISTS idx_session_documents_priority ON session_documents(session_id, priority DESC);

COMMENT ON TABLE session_documents IS 'Short-term memory: documents associated with active sessions';

-- ----------------------------------------------------------------------------
-- Table: session_contexts
-- Purpose: Session-specific context and preferences
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS session_contexts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID UNIQUE NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    preferred_model VARCHAR(100),
    context_window_size INTEGER DEFAULT 10,
    temperature DOUBLE PRECISION DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 1024,
    active_document_ids JSONB,
    conversation_summary TEXT,
    conversation_embedding VECTOR(384),
    tags JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_info JSONB
);

CREATE INDEX IF NOT EXISTS idx_session_contexts_session ON session_contexts(session_id);

COMMENT ON TABLE session_contexts IS 'Session-specific context and preferences (short-term memory)';

-- ----------------------------------------------------------------------------
-- Table: conversation_messages
-- Purpose: Conversation messages with token tracking
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    model_id VARCHAR(100),
    model_name VARCHAR(255),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    latency_ms DOUBLE PRECISION,
    cost_usd DOUBLE PRECISION,
    sources JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_info JSONB
);

CREATE INDEX IF NOT EXISTS idx_conversation_messages_session ON conversation_messages(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_role ON conversation_messages(role);

COMMENT ON TABLE conversation_messages IS 'Messages within chat sessions with token tracking';

-- ----------------------------------------------------------------------------
-- Table: audit_logs
-- Purpose: Comprehensive audit trail
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_id UUID REFERENCES chat_sessions(id) ON DELETE SET NULL,
    action action_type NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    description TEXT,
    request_data JSONB,
    response_data JSONB,
    ip_address VARCHAR(45),
    user_agent VARCHAR(512),
    status_code INTEGER,
    error_message TEXT,
    latency_ms DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_info JSONB
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_session ON audit_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

COMMENT ON TABLE audit_logs IS 'Comprehensive audit trail for all user actions';

-- ----------------------------------------------------------------------------
-- Table: usage_metrics
-- Purpose: Aggregated usage metrics
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usage_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    model_id VARCHAR(100),
    total_queries INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd DOUBLE PRECISION DEFAULT 0.0,
    avg_latency_ms DOUBLE PRECISION DEFAULT 0.0,
    documents_uploaded INTEGER DEFAULT 0,
    pages_scraped INTEGER DEFAULT 0,
    cache_hits INTEGER DEFAULT 0,
    cache_misses INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_info JSONB,
    UNIQUE(user_id, date, model_id)
);

CREATE INDEX IF NOT EXISTS idx_usage_metrics_user ON usage_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_metrics_date ON usage_metrics(date DESC);
CREATE INDEX IF NOT EXISTS idx_usage_metrics_model ON usage_metrics(model_id);

COMMENT ON TABLE usage_metrics IS 'Aggregated usage metrics for analytics';

-- ----------------------------------------------------------------------------
-- Table: tool_usage_stats
-- Purpose: Tool/service usage tracking
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tool_usage_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Tool identification
    tool_category VARCHAR(50) NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    tool_version VARCHAR(50),

    -- Session/User context
    session_id VARCHAR(255),
    user_id UUID REFERENCES users(id),

    -- Operation details
    operation VARCHAR(100),
    input_size INTEGER,
    output_size INTEGER,

    -- Performance metrics
    latency_ms FLOAT NOT NULL,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT,

    -- Resource usage
    tokens_used INTEGER,
    cost_usd DECIMAL(10, 6),

    -- Quality metrics
    quality_score FLOAT,
    metadata JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tool_usage_category ON tool_usage_stats(tool_category);
CREATE INDEX IF NOT EXISTS idx_tool_usage_name ON tool_usage_stats(tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_usage_session ON tool_usage_stats(session_id);
CREATE INDEX IF NOT EXISTS idx_tool_usage_user ON tool_usage_stats(user_id);
CREATE INDEX IF NOT EXISTS idx_tool_usage_created_at ON tool_usage_stats(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tool_usage_success ON tool_usage_stats(success);
CREATE INDEX IF NOT EXISTS idx_tool_usage_category_name_date ON tool_usage_stats(tool_category, tool_name, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tool_usage_session_date ON tool_usage_stats(session_id, created_at DESC);

COMMENT ON TABLE tool_usage_stats IS 'Records every tool/service invocation';

-- ----------------------------------------------------------------------------
-- Table: agent_tasks
-- Purpose: Agent task execution tracking
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agent_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id VARCHAR(255) UNIQUE NOT NULL,

    -- Task details
    task_name VARCHAR(255),
    task_description TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    session_id VARCHAR(255),
    model VARCHAR(100) NOT NULL DEFAULT 'qwen2.5-coder:7b',

    -- Configuration
    max_iterations INTEGER DEFAULT 20,
    timeout_seconds INTEGER DEFAULT 600,

    -- Progress tracking
    current_iteration INTEGER DEFAULT 0,
    current_phase VARCHAR(50),

    -- Execution details
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds FLOAT,

    -- Results
    result TEXT,
    artifacts TEXT[],
    tools_used TEXT[],
    llm_calls INTEGER DEFAULT 0,

    -- MinIO paths for artifacts
    minio_input_path VARCHAR(512),
    minio_output_path VARCHAR(512),

    -- Error handling
    error TEXT,
    error_details JSONB,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_info JSONB,

    -- Project tracking
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    department VARCHAR(100),
    team VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_agent_tasks_task_id ON agent_tasks(task_id);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_session_id ON agent_tasks(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_status ON agent_tasks(status);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_created_at ON agent_tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_project_id ON agent_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_created_by ON agent_tasks(created_by);

COMMENT ON TABLE agent_tasks IS 'Tracks autonomous agent task execution';

-- ----------------------------------------------------------------------------
-- Table: prompt_library
-- Purpose: Reusable prompt templates
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS prompt_library (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Basic Information
    name VARCHAR(255) NOT NULL,
    description TEXT,
    prompt_text TEXT NOT NULL,

    -- Classification
    prompt_type VARCHAR(100) NOT NULL,
    category VARCHAR(100),
    module VARCHAR(100),
    tags JSONB DEFAULT '[]'::jsonb,

    -- Output Configuration
    expected_output_format VARCHAR(50) DEFAULT 'text',
    output_schema JSONB,

    -- Examples
    example_input TEXT,
    example_output TEXT,

    -- Ownership & Visibility
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    is_public BOOLEAN DEFAULT false,
    is_verified BOOLEAN DEFAULT false,

    -- Usage Metrics
    usage_count INTEGER DEFAULT 0,
    average_rating FLOAT DEFAULT 0.0,
    total_ratings INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,

    -- Versioning
    version INTEGER DEFAULT 1,
    parent_prompt_id UUID REFERENCES prompt_library(id) ON DELETE SET NULL,

    -- Metadata
    meta_info JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_prompt_library_created_by ON prompt_library(created_by);
CREATE INDEX IF NOT EXISTS idx_prompt_library_project_id ON prompt_library(project_id);
CREATE INDEX IF NOT EXISTS idx_prompt_library_prompt_type ON prompt_library(prompt_type);
CREATE INDEX IF NOT EXISTS idx_prompt_library_category ON prompt_library(category);
CREATE INDEX IF NOT EXISTS idx_prompt_library_module ON prompt_library(module);
CREATE INDEX IF NOT EXISTS idx_prompt_library_is_public ON prompt_library(is_public);
CREATE INDEX IF NOT EXISTS idx_prompt_library_tags ON prompt_library USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_prompt_library_usage_count ON prompt_library(usage_count DESC);
CREATE INDEX IF NOT EXISTS idx_prompt_library_average_rating ON prompt_library(average_rating DESC);

COMMENT ON TABLE prompt_library IS 'Reusable prompt templates';

-- ----------------------------------------------------------------------------
-- Table: prompt_ratings
-- Purpose: User ratings for prompts
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS prompt_ratings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prompt_id UUID REFERENCES prompt_library(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    feedback TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(prompt_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_prompt_ratings_prompt_id ON prompt_ratings(prompt_id);
CREATE INDEX IF NOT EXISTS idx_prompt_ratings_user_id ON prompt_ratings(user_id);

COMMENT ON TABLE prompt_ratings IS 'User ratings and feedback for prompts';

-- ----------------------------------------------------------------------------
-- Table: prompt_usage_log
-- Purpose: Analytics log for prompt usage
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS prompt_usage_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prompt_id UUID REFERENCES prompt_library(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_id UUID REFERENCES chat_sessions(id) ON DELETE SET NULL,

    -- Usage details
    actual_prompt_used TEXT,
    input_provided TEXT,
    output_generated TEXT,

    -- Performance
    execution_time_ms FLOAT,
    token_count INTEGER,

    -- Outcome
    was_successful BOOLEAN DEFAULT true,
    error_message TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_prompt_usage_log_prompt_id ON prompt_usage_log(prompt_id);
CREATE INDEX IF NOT EXISTS idx_prompt_usage_log_user_id ON prompt_usage_log(user_id);
CREATE INDEX IF NOT EXISTS idx_prompt_usage_log_created_at ON prompt_usage_log(created_at DESC);

COMMENT ON TABLE prompt_usage_log IS 'Analytics log for prompt usage patterns';

-- ----------------------------------------------------------------------------
-- Table: output_templates
-- Purpose: Reusable output format templates
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS output_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Basic Information
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Template Configuration
    template_type VARCHAR(50) NOT NULL,
    template_config JSONB NOT NULL,

    -- Template Content
    template_file_path VARCHAR(512),

    -- Ownership & Visibility
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    is_public BOOLEAN DEFAULT false,

    -- Usage Metrics
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    meta_info JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_output_templates_created_by ON output_templates(created_by);
CREATE INDEX IF NOT EXISTS idx_output_templates_project_id ON output_templates(project_id);
CREATE INDEX IF NOT EXISTS idx_output_templates_template_type ON output_templates(template_type);
CREATE INDEX IF NOT EXISTS idx_output_templates_is_public ON output_templates(is_public);

COMMENT ON TABLE output_templates IS 'Reusable output format templates';

-- ----------------------------------------------------------------------------
-- Table: extraction_jobs
-- Purpose: Extraction job execution records
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS extraction_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_name VARCHAR(255) NOT NULL,
    template_id UUID REFERENCES extraction_templates(id) ON DELETE CASCADE,

    -- Job configuration
    urls JSONB NOT NULL,
    scraper_config JSONB,

    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    progress_percentage INTEGER DEFAULT 0,
    urls_total INTEGER DEFAULT 0,
    urls_processed INTEGER DEFAULT 0,
    records_extracted INTEGER DEFAULT 0,

    -- Quality metrics
    quality_score FLOAT,
    validation_errors JSONB,

    -- Output configuration
    output_format VARCHAR(50) NOT NULL,
    output_file_path VARCHAR(512),
    delivery_method VARCHAR(50),
    delivery_config JSONB,
    delivery_status VARCHAR(50),

    -- Execution metadata
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    execution_time_ms FLOAT,
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_extraction_jobs_template ON extraction_jobs(template_id);
CREATE INDEX IF NOT EXISTS idx_extraction_jobs_status ON extraction_jobs(status);
CREATE INDEX IF NOT EXISTS idx_extraction_jobs_created ON extraction_jobs(created_at DESC);

COMMENT ON TABLE extraction_jobs IS 'Extraction job execution records';

-- ----------------------------------------------------------------------------
-- Table: extraction_results
-- Purpose: Individual extraction results per URL
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS extraction_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES extraction_jobs(id) ON DELETE CASCADE,

    -- Source information
    source_url VARCHAR(1024) NOT NULL,
    source_index INTEGER,

    -- Extracted data
    extracted_data JSONB NOT NULL,
    raw_content TEXT,

    -- Quality metrics
    extraction_confidence FLOAT,
    validation_errors JSONB,

    -- Metadata
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_extraction_results_job ON extraction_results(job_id);
CREATE INDEX IF NOT EXISTS idx_extraction_results_url ON extraction_results(source_url);

COMMENT ON TABLE extraction_results IS 'Individual extraction results per URL';

-- ----------------------------------------------------------------------------
-- Table: extraction_job_schedules
-- Purpose: Scheduled extraction jobs
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS extraction_job_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_name VARCHAR(255) NOT NULL,
    template_id UUID REFERENCES extraction_templates(id) ON DELETE CASCADE,

    -- Schedule configuration
    schedule_type VARCHAR(50) NOT NULL,
    cron_expression VARCHAR(100),
    next_run_at TIMESTAMP WITH TIME ZONE,

    -- Scraping configuration
    urls JSONB NOT NULL,
    scraper_config JSONB,

    -- Output configuration
    output_format VARCHAR(50) NOT NULL,
    delivery_method VARCHAR(50) NOT NULL,
    delivery_config JSONB,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP WITH TIME ZONE,
    last_run_status VARCHAR(50),
    last_job_id UUID REFERENCES extraction_jobs(id),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_extraction_schedules_template ON extraction_job_schedules(template_id);
CREATE INDEX IF NOT EXISTS idx_extraction_schedules_active ON extraction_job_schedules(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_extraction_schedules_next_run ON extraction_job_schedules(next_run_at) WHERE is_active = TRUE;

COMMENT ON TABLE extraction_job_schedules IS 'Scheduled extraction jobs';

-- ============================================================================
-- LAYER 5: EVALUATION TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: evaluation_configs
-- Purpose: User-specific evaluation configuration
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS evaluation_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,

    -- Toggle switches for evaluation methods
    enable_ragas BOOLEAN DEFAULT FALSE,
    enable_llm_as_judge BOOLEAN DEFAULT FALSE,
    enable_deepeval BOOLEAN DEFAULT FALSE,
    enable_semantic_similarity BOOLEAN DEFAULT FALSE,
    enable_bertscore BOOLEAN DEFAULT FALSE,
    enable_citation_accuracy BOOLEAN DEFAULT TRUE,
    enable_toxicity BOOLEAN DEFAULT TRUE,
    enable_bias_detection BOOLEAN DEFAULT TRUE,
    enable_hallucination BOOLEAN DEFAULT TRUE,
    enable_answer_relevancy BOOLEAN DEFAULT TRUE,
    enable_context_precision BOOLEAN DEFAULT FALSE,
    enable_context_recall BOOLEAN DEFAULT FALSE,
    enable_faithfulness BOOLEAN DEFAULT TRUE,

    -- Configuration parameters
    llm_judge_model VARCHAR(100) DEFAULT 'gpt-4-turbo-preview',
    use_cache BOOLEAN DEFAULT TRUE,
    async_evaluation BOOLEAN DEFAULT TRUE,
    batch_size INTEGER DEFAULT 10,
    min_score_threshold FLOAT DEFAULT 0.7,
    cache_ttl_seconds INTEGER DEFAULT 3600,

    -- Auto-evaluation settings
    auto_evaluate BOOLEAN DEFAULT FALSE,
    evaluation_sampling_rate FLOAT DEFAULT 1.0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_info JSONB
);

CREATE INDEX IF NOT EXISTS idx_evaluation_configs_user_id ON evaluation_configs(user_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_configs_session_id ON evaluation_configs(session_id);

COMMENT ON TABLE evaluation_configs IS 'User-specific evaluation configuration with toggleable metrics';

-- ----------------------------------------------------------------------------
-- Table: evaluation_results
-- Purpose: Stores comprehensive evaluation results
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS evaluation_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    message_id UUID REFERENCES conversation_messages(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Query and response data
    query TEXT NOT NULL,
    response TEXT NOT NULL,
    num_contexts INTEGER,

    -- Evaluation scores (JSON for flexibility)
    scores JSONB NOT NULL,
    overall_score FLOAT,

    -- Performance metrics
    evaluation_time_ms FLOAT,
    enabled_methods JSONB,

    -- Metadata and errors
    meta_info JSONB,
    errors JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evaluation_results_session_id ON evaluation_results(session_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_results_message_id ON evaluation_results(message_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_results_overall_score ON evaluation_results(overall_score);
CREATE INDEX IF NOT EXISTS idx_evaluation_results_created_at ON evaluation_results(created_at);

COMMENT ON TABLE evaluation_results IS 'Stores comprehensive evaluation results for RAG responses';

-- ----------------------------------------------------------------------------
-- Table: evaluation_cache
-- Purpose: Cache for evaluation results
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS evaluation_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    result JSONB NOT NULL,
    ttl_seconds INTEGER DEFAULT 3600,
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evaluation_cache_key ON evaluation_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_evaluation_cache_created_at ON evaluation_cache(created_at);

COMMENT ON TABLE evaluation_cache IS 'Cache for evaluation results to improve performance';

-- ----------------------------------------------------------------------------
-- Table: human_feedback
-- Purpose: Human feedback on RAG responses
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS human_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    message_id UUID REFERENCES conversation_messages(id) ON DELETE CASCADE,
    evaluation_id UUID REFERENCES evaluation_results(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Feedback data
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    thumbs_up BOOLEAN,
    feedback_text TEXT,

    -- Specific criteria ratings
    accuracy_rating INTEGER CHECK (accuracy_rating >= 1 AND accuracy_rating <= 5),
    helpfulness_rating INTEGER CHECK (helpfulness_rating >= 1 AND helpfulness_rating <= 5),
    clarity_rating INTEGER CHECK (clarity_rating >= 1 AND clarity_rating <= 5),

    -- Issues flagged
    has_hallucination BOOLEAN DEFAULT FALSE,
    has_bias BOOLEAN DEFAULT FALSE,
    has_toxicity BOOLEAN DEFAULT FALSE,
    is_irrelevant BOOLEAN DEFAULT FALSE,

    -- Metadata
    feedback_type VARCHAR(50),
    ip_address VARCHAR(45),
    user_agent VARCHAR(512),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_info JSONB
);

CREATE INDEX IF NOT EXISTS idx_human_feedback_session_id ON human_feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_human_feedback_message_id ON human_feedback(message_id);
CREATE INDEX IF NOT EXISTS idx_human_feedback_evaluation_id ON human_feedback(evaluation_id);
CREATE INDEX IF NOT EXISTS idx_human_feedback_created_at ON human_feedback(created_at);

COMMENT ON TABLE human_feedback IS 'Human feedback on RAG responses for continuous improvement';

-- ----------------------------------------------------------------------------
-- Table: evaluation_benchmarks
-- Purpose: Benchmark datasets for evaluation metrics validation
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS evaluation_benchmarks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Benchmark data
    query TEXT NOT NULL,
    ground_truth_answer TEXT NOT NULL,
    context_chunks JSONB NOT NULL,

    -- Expected scores (for validation)
    expected_scores JSONB,

    -- Benchmark metadata
    dataset_name VARCHAR(100),
    difficulty VARCHAR(50),
    category VARCHAR(100),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_info JSONB
);

CREATE INDEX IF NOT EXISTS idx_evaluation_benchmarks_dataset_name ON evaluation_benchmarks(dataset_name);
CREATE INDEX IF NOT EXISTS idx_evaluation_benchmarks_difficulty ON evaluation_benchmarks(difficulty);
CREATE INDEX IF NOT EXISTS idx_evaluation_benchmarks_category ON evaluation_benchmarks(category);

COMMENT ON TABLE evaluation_benchmarks IS 'Benchmark datasets for evaluation metrics validation';

-- ============================================================================
-- LAYER 6: FINE-TUNING TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: finetuning_datasets
-- Purpose: Stores uploaded datasets for fine-tuning
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS finetuning_datasets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Dataset metadata
    name VARCHAR(255) NOT NULL,
    description TEXT,
    uploaded_by UUID REFERENCES users(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- File info
    filename VARCHAR(255) NOT NULL,
    file_size BIGINT,
    file_type VARCHAR(50),
    minio_path VARCHAR(512),

    -- Dataset statistics
    num_samples INT,
    num_train_samples INT,
    num_val_samples INT,

    -- Schema/format
    format_type VARCHAR(100),
    columns JSONB,

    -- Validation
    is_valid BOOLEAN DEFAULT FALSE,
    validation_errors JSONB,

    -- Preview
    sample_rows JSONB,

    -- Processing status
    preprocessing_status VARCHAR(50) DEFAULT 'pending',
    preprocessed_path VARCHAR(512),

    -- Project association
    project_id UUID REFERENCES projects(id),

    CONSTRAINT finetuning_datasets_name_project_unique UNIQUE (name, project_id)
);

CREATE INDEX IF NOT EXISTS idx_finetuning_datasets_uploaded_by ON finetuning_datasets(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_finetuning_datasets_project ON finetuning_datasets(project_id);
CREATE INDEX IF NOT EXISTS idx_finetuning_datasets_format_type ON finetuning_datasets(format_type);

COMMENT ON TABLE finetuning_datasets IS 'Stores uploaded datasets for model fine-tuning';

-- ----------------------------------------------------------------------------
-- Table: finetuning_jobs
-- Purpose: Fine-tuning job configurations and status
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS finetuning_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Job metadata
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Model configuration
    base_model VARCHAR(255) NOT NULL,
    quantization VARCHAR(50),

    -- Fine-tuning configuration
    finetuning_method VARCHAR(50) NOT NULL,
    training_objective VARCHAR(100) NOT NULL,

    -- Dataset
    dataset_id UUID REFERENCES finetuning_datasets(id),
    train_split FLOAT DEFAULT 0.8,

    -- Hyperparameters
    hyperparameters JSONB,

    -- Training status
    status VARCHAR(50) DEFAULT 'pending',
    progress FLOAT DEFAULT 0.0,

    -- Training stage tracking (Phase 1)
    training_stage VARCHAR(50) DEFAULT 'queued',
    stage_details JSONB DEFAULT '{}'::jsonb,
    stage_started_at TIMESTAMP WITH TIME ZONE,
    stage_completed_at TIMESTAMP WITH TIME ZONE,

    -- Training metrics
    current_epoch INT,
    current_step INT,
    total_steps INT,
    train_loss FLOAT,
    eval_loss FLOAT,

    -- Results
    final_model_name VARCHAR(255),
    mlflow_run_id VARCHAR(255),
    minio_checkpoint_path VARCHAR(512),

    -- Training logs
    logs TEXT,
    error_message TEXT,

    -- Resource usage
    gpu_type VARCHAR(100),
    gpu_count INT DEFAULT 1,
    training_time_seconds INT,
    training_start_time TIMESTAMP WITH TIME ZONE,
    training_end_time TIMESTAMP WITH TIME ZONE,

    -- Project association
    project_id UUID REFERENCES projects(id),
    department VARCHAR(255),
    team VARCHAR(255),

    -- Celery task tracking
    celery_task_id VARCHAR(255),

    CONSTRAINT finetuning_jobs_progress_range CHECK (progress >= 0.0 AND progress <= 1.0),
    CONSTRAINT check_valid_training_stage CHECK (training_stage IN (
        'queued', 'setup', 'tokenizer_load', 'model_download', 'model_load',
        'dataset_prep', 'training', 'checkpoint_save', 'completed', 'failed'
    ))
);

CREATE INDEX IF NOT EXISTS idx_finetuning_jobs_status ON finetuning_jobs(status);
CREATE INDEX IF NOT EXISTS idx_finetuning_jobs_created_by ON finetuning_jobs(created_by);
CREATE INDEX IF NOT EXISTS idx_finetuning_jobs_project ON finetuning_jobs(project_id);
CREATE INDEX IF NOT EXISTS idx_finetuning_jobs_dataset ON finetuning_jobs(dataset_id);
CREATE INDEX IF NOT EXISTS idx_finetuning_jobs_method ON finetuning_jobs(finetuning_method);
CREATE INDEX IF NOT EXISTS idx_finetuning_jobs_created_at ON finetuning_jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_finetuning_jobs_training_stage ON finetuning_jobs(training_stage);

COMMENT ON TABLE finetuning_jobs IS 'Fine-tuning job configurations and execution status';

-- ----------------------------------------------------------------------------
-- Table: finetuned_models
-- Purpose: Model registry for fine-tuned models
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS finetuned_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Model metadata
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) DEFAULT 'v1.0.0',
    description TEXT,

    -- Source job
    job_id UUID REFERENCES finetuning_jobs(id),
    base_model VARCHAR(255) NOT NULL,
    finetuning_method VARCHAR(50),

    -- Model artifacts
    mlflow_model_uri VARCHAR(512),
    mlflow_run_id VARCHAR(255),
    minio_checkpoint_path VARCHAR(512),
    adapter_config JSONB,

    -- Evaluation metrics
    eval_metrics JSONB,

    -- Deployment
    status VARCHAR(50) DEFAULT 'registered',
    deployment_url VARCHAR(512),
    ollama_model_name VARCHAR(255),
    vllm_model_name VARCHAR(255),

    -- Usage tracking
    total_inferences INT DEFAULT 0,
    avg_latency_ms FLOAT,
    last_inference_at TIMESTAMP WITH TIME ZONE,

    -- Versioning and lineage
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    parent_model_id UUID REFERENCES finetuned_models(id),

    -- Deprecation
    deprecated_at TIMESTAMP WITH TIME ZONE,
    deprecated_by UUID REFERENCES users(id),
    deprecation_reason TEXT,

    -- Project association
    project_id UUID REFERENCES projects(id),

    -- Model tags
    tags JSONB,

    CONSTRAINT finetuned_models_name_version_unique UNIQUE (name, version)
);

CREATE INDEX IF NOT EXISTS idx_finetuned_models_status ON finetuned_models(status);
CREATE INDEX IF NOT EXISTS idx_finetuned_models_job ON finetuned_models(job_id);
CREATE INDEX IF NOT EXISTS idx_finetuned_models_project ON finetuned_models(project_id);
CREATE INDEX IF NOT EXISTS idx_finetuned_models_created_at ON finetuned_models(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_finetuned_models_ollama_name ON finetuned_models(ollama_model_name);
CREATE INDEX IF NOT EXISTS idx_finetuned_models_tags ON finetuned_models USING GIN (tags);

COMMENT ON TABLE finetuned_models IS 'Registry of fine-tuned models with deployment tracking';

-- ----------------------------------------------------------------------------
-- Table: training_metrics
-- Purpose: Time-series training progress monitoring
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS training_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES finetuning_jobs(id) ON DELETE CASCADE,

    -- Timestamp
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Training progress
    epoch INT,
    step INT,

    -- Loss metrics
    train_loss FLOAT,
    eval_loss FLOAT,
    gradient_norm FLOAT,

    -- Learning metrics
    learning_rate FLOAT,

    -- Resource metrics
    gpu_utilization FLOAT,
    gpu_memory_allocated BIGINT,
    gpu_memory_reserved BIGINT,
    gpu_temperature FLOAT,

    -- Performance metrics
    samples_per_second FLOAT,
    tokens_per_second FLOAT,
    batch_processing_time_ms FLOAT,

    -- Additional metrics
    custom_metrics JSONB,

    CONSTRAINT training_metrics_gpu_utilization_range CHECK (gpu_utilization >= 0.0 AND gpu_utilization <= 1.0)
);

CREATE INDEX IF NOT EXISTS idx_training_metrics_job_timestamp ON training_metrics(job_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_training_metrics_job_step ON training_metrics(job_id, step);

COMMENT ON TABLE training_metrics IS 'Time-series metrics collected during model training';

-- ----------------------------------------------------------------------------
-- Table: model_approvals
-- Purpose: Approval workflow for deploying fine-tuned models
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS model_approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES finetuned_models(id) ON DELETE CASCADE,

    -- Request details
    requested_by UUID REFERENCES users(id) ON DELETE SET NULL,
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    request_reason TEXT,

    -- Approval/rejection
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'pending',
    review_comments TEXT,

    -- Deployment constraints
    deployment_environment VARCHAR(100),
    max_concurrent_instances INTEGER,
    resource_limits JSONB,

    CONSTRAINT check_approval_status CHECK (status IN ('pending', 'approved', 'rejected'))
);

CREATE INDEX IF NOT EXISTS idx_model_approvals_model_id ON model_approvals(model_id);
CREATE INDEX IF NOT EXISTS idx_model_approvals_status ON model_approvals(status);
CREATE INDEX IF NOT EXISTS idx_model_approvals_requested_by ON model_approvals(requested_by);
CREATE INDEX IF NOT EXISTS idx_model_approvals_approved_by ON model_approvals(approved_by);

COMMENT ON TABLE model_approvals IS 'Approval workflow for deploying fine-tuned models to production';

-- ============================================================================
-- TRIGGERS AND FUNCTIONS
-- ============================================================================

-- Generic update_updated_at function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to all tables with updated_at
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chat_sessions_updated_at BEFORE UPDATE ON chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_session_contexts_updated_at BEFORE UPDATE ON session_contexts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scraping_configs_updated_at BEFORE UPDATE ON scraping_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_saved_css_templates_updated_at BEFORE UPDATE ON saved_css_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON system_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_models_updated_at BEFORE UPDATE ON models
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_evaluation_configs_updated_at BEFORE UPDATE ON evaluation_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_finetuning_jobs_updated_at BEFORE UPDATE ON finetuning_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_tasks_updated_at BEFORE UPDATE ON agent_tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prompt_library_updated_at BEFORE UPDATE ON prompt_library
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_output_templates_updated_at BEFORE UPDATE ON output_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_extraction_templates_updated_at BEFORE UPDATE ON extraction_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_extraction_jobs_updated_at BEFORE UPDATE ON extraction_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_extraction_schedules_updated_at BEFORE UPDATE ON extraction_job_schedules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Sync chunk project info from parent document
CREATE OR REPLACE FUNCTION sync_chunk_project_info()
RETURNS TRIGGER AS $$
BEGIN
    SELECT
        project_id,
        uploaded_by,
        department_id,
        team_id
    INTO
        NEW.project_id,
        NEW.uploaded_by,
        NEW.department_id,
        NEW.team_id
    FROM documents
    WHERE id = NEW.document_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_chunk_project_info
    BEFORE INSERT ON document_chunks
    FOR EACH ROW
    EXECUTE FUNCTION sync_chunk_project_info();

-- Calculate training duration for finetuning jobs
CREATE OR REPLACE FUNCTION calculate_training_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'running' AND OLD.status = 'pending' THEN
        NEW.training_start_time = NOW();
    ELSIF NEW.status IN ('completed', 'failed', 'cancelled') AND OLD.status = 'running' THEN
        NEW.training_end_time = NOW();
        NEW.training_time_seconds = EXTRACT(EPOCH FROM (NEW.training_end_time - NEW.training_start_time));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER finetuning_jobs_calculate_duration
    BEFORE UPDATE ON finetuning_jobs
    FOR EACH ROW
    EXECUTE FUNCTION calculate_training_duration();

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Get system configuration value
CREATE OR REPLACE FUNCTION get_system_config(p_config_key VARCHAR)
RETURNS TEXT AS $$
DECLARE
    config_val TEXT;
BEGIN
    SELECT config_value INTO config_val
    FROM system_config
    WHERE config_key = p_config_key AND is_active = TRUE
    LIMIT 1;

    RETURN config_val;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_system_config IS 'Helper function to retrieve system configuration values';

-- Build MinIO path for documents
CREATE OR REPLACE FUNCTION build_minio_path(
    p_role VARCHAR,
    p_department VARCHAR,
    p_team VARCHAR,
    p_username VARCHAR,
    p_project_name VARCHAR,
    p_folder VARCHAR,
    p_filename VARCHAR
) RETURNS VARCHAR AS $$
DECLARE
    v_path VARCHAR;
BEGIN
    v_path :=
        LOWER(REGEXP_REPLACE(p_role, '[^a-zA-Z0-9_-]', '', 'g')) || '/' ||
        LOWER(REGEXP_REPLACE(p_department, '\s+', '-', 'g')) || '/' ||
        LOWER(REGEXP_REPLACE(p_team, '\s+', '-', 'g')) || '/' ||
        LOWER(p_username) || '/' ||
        LOWER(REGEXP_REPLACE(p_project_name, '\s+', '-', 'g')) || '/' ||
        p_folder || '/' ||
        p_filename;

    RETURN v_path;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION build_minio_path IS 'Build hierarchical MinIO path: role/dept/team/username/project/folder/file';

-- ============================================================================
-- MATERIALIZED VIEWS
-- ============================================================================

-- Tool usage summary
CREATE MATERIALIZED VIEW IF NOT EXISTS tool_usage_summary AS
SELECT
    tool_category,
    tool_name,
    COUNT(*) as total_invocations,
    COUNT(*) FILTER (WHERE success = TRUE) as successful_invocations,
    COUNT(*) FILTER (WHERE success = FALSE) as failed_invocations,
    AVG(latency_ms) as avg_latency_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY latency_ms) as median_latency_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency_ms,
    MIN(latency_ms) as min_latency_ms,
    MAX(latency_ms) as max_latency_ms,
    SUM(tokens_used) as total_tokens_used,
    SUM(cost_usd) as total_cost_usd,
    AVG(quality_score) as avg_quality_score,
    MIN(created_at) as first_used,
    MAX(created_at) as last_used,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE success = TRUE) / NULLIF(COUNT(*), 0),
        2
    ) as success_rate_pct
FROM tool_usage_stats
GROUP BY tool_category, tool_name;

CREATE INDEX IF NOT EXISTS idx_tool_summary_category ON tool_usage_summary(tool_category);
CREATE INDEX IF NOT EXISTS idx_tool_summary_name ON tool_usage_summary(tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_summary_invocations ON tool_usage_summary(total_invocations DESC);

COMMENT ON MATERIALIZED VIEW tool_usage_summary IS 'Aggregated tool usage statistics';

-- Team hierarchy view
CREATE OR REPLACE VIEW team_hierarchy AS
SELECT
    t.id AS team_id,
    t.name AS team_name,
    t.code AS team_code,
    d.id AS department_id,
    d.name AS department_name,
    d.code AS department_code,
    u.id AS team_lead_id,
    u.username AS team_lead_username,
    COUNT(DISTINCT um.id) AS member_count
FROM teams t
JOIN departments d ON t.department_id = d.id
LEFT JOIN users u ON t.team_lead_id = u.id
LEFT JOIN users um ON um.team_id = t.id
WHERE t.is_active = TRUE
GROUP BY t.id, t.name, t.code, d.id, d.name, d.code, u.id, u.username;

COMMENT ON VIEW team_hierarchy IS 'Hierarchical view of teams, departments, and members';

-- Active models view
CREATE OR REPLACE VIEW active_models AS
SELECT
    model_id,
    display_name,
    provider,
    model_type,
    context_length,
    max_tokens,
    supports_functions,
    supports_vision,
    supports_streaming,
    cost_per_1k_input,
    cost_per_1k_output,
    is_default,
    source,
    CASE
        WHEN cost_per_1k_input = 0 OR cost_per_1k_input IS NULL THEN 'Free'
        WHEN cost_per_1k_input < 0.001 THEN 'Very Low'
        WHEN cost_per_1k_input < 0.005 THEN 'Low'
        WHEN cost_per_1k_input < 0.015 THEN 'Medium'
        ELSE 'High'
    END AS cost_tier
FROM models
WHERE is_active = TRUE
ORDER BY provider, model_type, display_name;

COMMENT ON VIEW active_models IS 'Active LLM models with cost tier classification';

-- ============================================================================
-- PREFECT SCHEMA
-- ============================================================================
-- Create separate schema for Prefect instead of separate database
CREATE SCHEMA IF NOT EXISTS prefect;

COMMENT ON SCHEMA prefect IS 'Prefect workflow orchestration tables (consolidated into main database)';

GRANT ALL ON SCHEMA prefect TO postgres;
GRANT ALL ON ALL TABLES IN SCHEMA prefect TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA prefect TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA prefect GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA prefect GRANT ALL ON SEQUENCES TO postgres;

COMMIT;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
-- Total Tables: 50
-- Total Indexes: 200+
-- Total Triggers: 20+
-- Total Functions: 3
-- Total Views: 3
-- Total Materialized Views: 1
-- ============================================================================
