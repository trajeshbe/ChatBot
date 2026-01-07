-- Migration 027: Phase 1 Comprehensive Platform Enhancements
-- Date: 2026-01-07
-- Purpose: Implement Phase 1 requirements for platform enhancement
--
-- Requirements Implemented:
-- - Requirement 1: Dynamic Embedding Dimensions (project-scoped configuration)
-- - Requirement 3: Prefect → Core DB Configuration (separate schema)
-- - Requirement 5: Default Global Project (created during installation)
-- - Requirement 6: Admin User Defaults (pwd: admin, Technology, Team11)
-- - Requirement 8: Agent Runtime API from Database (system_config table)
--
-- Related Files:
-- - backend/app/config/embedding_configs.py (34 production-grade embeddings)
-- - docs/implementation/COMPREHENSIVE_ENHANCEMENT_STRATEGY_2026-01-07.md

BEGIN;

-- ============================================================================
-- STEP 1: Add embedding configuration to projects table
-- ============================================================================

-- Add embedding config columns to projects
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS primary_embedding_config VARCHAR(100) DEFAULT 'all_minilm_l6_v2_384',
ADD COLUMN IF NOT EXISTS code_embedding_config VARCHAR(100),
ADD COLUMN IF NOT EXISTS visual_embedding_config VARCHAR(100),
ADD COLUMN IF NOT EXISTS table_embedding_config VARCHAR(100),
ADD COLUMN IF NOT EXISTS numerical_embedding_config VARCHAR(100),
ADD COLUMN IF NOT EXISTS embedding_api_keys JSONB DEFAULT '{}';

CREATE INDEX IF NOT EXISTS idx_projects_primary_embedding ON projects(primary_embedding_config);

COMMENT ON COLUMN projects.primary_embedding_config IS 'Primary embedding model config ID from embedding_configs.py (default: 384-dim MiniLM)';
COMMENT ON COLUMN projects.code_embedding_config IS 'Code-specific embedding model config ID (optional, uses code_embedding column)';
COMMENT ON COLUMN projects.visual_embedding_config IS 'Vision/image embedding model config ID (optional, uses visual_embedding column)';
COMMENT ON COLUMN projects.table_embedding_config IS 'Table structure embedding model config ID (optional, uses table_embedding column)';
COMMENT ON COLUMN projects.numerical_embedding_config IS 'Numerical data embedding model config ID (optional, uses numerical_embedding column)';
COMMENT ON COLUMN projects.embedding_api_keys IS 'Encrypted API keys for embedding providers (OpenAI, Cohere, etc.)';

-- ============================================================================
-- STEP 2: Create system_config table for database-driven configuration
-- ============================================================================

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
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    meta_info JSONB
);

CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(config_key);
CREATE INDEX IF NOT EXISTS idx_system_config_category ON system_config(category);
CREATE INDEX IF NOT EXISTS idx_system_config_active ON system_config(is_active);

COMMENT ON TABLE system_config IS 'System-wide configuration stored in database instead of hardcoded values';
COMMENT ON COLUMN system_config.config_type IS 'Data type: string, integer, boolean, json, url, api_key';
COMMENT ON COLUMN system_config.is_encrypted IS 'Whether value is encrypted (for API keys, secrets)';

-- ============================================================================
-- STEP 3: Create models registry table for unified LLM model management
-- ============================================================================

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
COMMENT ON COLUMN models.is_default IS 'Default model for new agent tasks (only one per provider should be true)';

-- ============================================================================
-- STEP 4: Create Prefect schema for database consolidation
-- ============================================================================

-- Create separate schema for Prefect instead of separate database
CREATE SCHEMA IF NOT EXISTS prefect;

COMMENT ON SCHEMA prefect IS 'Prefect workflow orchestration tables (consolidated into main database)';

-- Grant permissions to postgres user
GRANT ALL ON SCHEMA prefect TO postgres;
GRANT ALL ON ALL TABLES IN SCHEMA prefect TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA prefect TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA prefect GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA prefect GRANT ALL ON SEQUENCES TO postgres;

-- ============================================================================
-- STEP 5: Create default "Global" project
-- ============================================================================

DO $$
DECLARE
    global_project_id UUID;
    admin_user_id UUID;
    tech_dept_id UUID;
BEGIN
    -- Get admin user ID
    SELECT id INTO admin_user_id FROM users WHERE username = 'admin' OR role = 'admin' LIMIT 1;

    -- Get Technology department ID (use Technology as default instead of General)
    SELECT id INTO tech_dept_id FROM departments WHERE name = 'Technology' LIMIT 1;

    -- Create Global project if it doesn't exist
    INSERT INTO projects (
        id,
        name,
        description,
        owner_id,
        department_id,
        status,
        primary_embedding_config,
        meta_info
    ) VALUES (
        uuid_generate_v4(),
        'Global',
        'Default global project for all users. Documents uploaded here are accessible across the organization.',
        admin_user_id,
        tech_dept_id,
        'active',
        'all_minilm_l6_v2_384',  -- Default 384-dim embedding
        jsonb_build_object(
            'is_global', true,
            'created_by', 'system',
            'auto_assign_users', true,
            'purpose', 'Default shared workspace'
        )
    )
    ON CONFLICT DO NOTHING
    RETURNING id INTO global_project_id;

    RAISE NOTICE 'Global project created or already exists: %', global_project_id;
END $$;

-- ============================================================================
-- STEP 6: Update admin user defaults
-- ============================================================================

DO $$
DECLARE
    tech_dept_id UUID;
    team11_id UUID;
    admin_user_id UUID;
BEGIN
    -- Get Technology department ID
    SELECT id INTO tech_dept_id FROM departments WHERE name = 'Technology' LIMIT 1;

    -- Get Team11 ID (ITM11 in Technology department)
    SELECT id INTO team11_id FROM teams
    WHERE code = 'ITM11' AND department_id = tech_dept_id
    LIMIT 1;

    -- If Team11 doesn't exist, create it
    IF team11_id IS NULL THEN
        INSERT INTO teams (name, code, department_id, description, is_active)
        VALUES ('ITM11', 'ITM11', tech_dept_id, 'Default admin team', TRUE)
        RETURNING id INTO team11_id;

        RAISE NOTICE 'Created ITM11 team: %', team11_id;
    END IF;

    -- Update admin user with defaults
    -- Note: Password hash for "admin" (bcrypt): $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU0k0Y8r0w8a
    UPDATE users
    SET
        department_id = tech_dept_id,
        hashed_password = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU0k0Y8r0w8a',  -- pwd: admin
        is_active = TRUE,
        is_verified = TRUE,
        updated_at = NOW()
    WHERE username = 'admin'
    RETURNING id INTO admin_user_id;

    -- Assign admin user to Team11 via user_teams junction table
    IF admin_user_id IS NOT NULL AND team11_id IS NOT NULL THEN
        INSERT INTO user_teams (id, user_id, team_id, is_primary, assigned_by)
        VALUES (uuid_generate_v4(), admin_user_id, team11_id, TRUE, admin_user_id)
        ON CONFLICT (user_id, team_id) DO UPDATE SET is_primary = TRUE;

        RAISE NOTICE 'Admin user updated: % (dept: %, team: %)', admin_user_id, tech_dept_id, team11_id;
    END IF;
END $$;

-- ============================================================================
-- STEP 7: Seed system_config with initial configuration
-- ============================================================================

-- Insert system configuration values
INSERT INTO system_config (config_key, config_value, config_type, category, description, is_active) VALUES
-- Agent Runtime Configuration
('agent.runtime.default_model', 'qwen2.5-coder:7b', 'string', 'agent', 'Default LLM model for agent runtime tasks', TRUE),
('agent.runtime.api_base_url', 'http://ollama:11434', 'url', 'agent', 'Agent runtime API base URL (Ollama endpoint)', TRUE),
('agent.runtime.max_iterations', '15', 'integer', 'agent', 'Default max iterations for agent tasks', TRUE),
('agent.runtime.timeout_seconds', '300', 'integer', 'agent', 'Default timeout for agent tasks (seconds)', TRUE),

-- Embedding Configuration
('embedding.default_provider', 'sentence-transformers', 'string', 'embedding', 'Default embedding provider', TRUE),
('embedding.default_dimension', '384', 'integer', 'embedding', 'Default embedding dimension', TRUE),
('embedding.cache_enabled', 'true', 'boolean', 'embedding', 'Enable Redis embedding cache', TRUE),

-- Ollama Auto-Discovery
('ollama.auto_discovery_enabled', 'true', 'boolean', 'ollama', 'Auto-discover Ollama models and register in UI', TRUE),
('ollama.sync_interval_seconds', '60', 'integer', 'ollama', 'Interval for Ollama model sync (seconds)', TRUE),
('ollama.api_base_url', 'http://ollama:11434', 'url', 'ollama', 'Ollama API base URL', TRUE),

-- Prefect Configuration
('prefect.database_schema', 'prefect', 'string', 'prefect', 'PostgreSQL schema for Prefect tables', TRUE),
('prefect.enabled', 'true', 'boolean', 'prefect', 'Enable Prefect workflow orchestration', TRUE),

-- RAG Configuration
('rag.default_top_k', '5', 'integer', 'rag', 'Default number of documents to retrieve', TRUE),
('rag.similarity_threshold', '0.7', 'string', 'rag', 'Minimum similarity score for retrieval', TRUE),

-- System Configuration
('system.installation_date', NOW()::TEXT, 'string', 'system', 'System installation timestamp', TRUE),
('system.version', '2.0.0', 'string', 'system', 'Platform version', TRUE),
('system.default_project', 'Global', 'string', 'system', 'Default project name for new users', TRUE)

ON CONFLICT (config_key) DO UPDATE SET
    config_value = EXCLUDED.config_value,
    description = EXCLUDED.description,
    updated_at = NOW();

-- ============================================================================
-- STEP 8: Seed models registry with initial LLM models
-- ============================================================================

-- Insert popular Ollama models
INSERT INTO models (model_id, display_name, provider, model_type, context_length, max_tokens, supports_functions, supports_vision, is_default) VALUES
-- Code Models
('qwen2.5-coder:7b', 'Qwen 2.5 Coder 7B', 'ollama', 'code', 32768, 8192, FALSE, FALSE, TRUE),
('codellama:7b', 'CodeLlama 7B', 'ollama', 'code', 16384, 4096, FALSE, FALSE, FALSE),
('deepseek-coder:6.7b', 'DeepSeek Coder 6.7B', 'ollama', 'code', 16384, 4096, FALSE, FALSE, FALSE),

-- Text Models
('llama3.2:3b', 'Llama 3.2 3B', 'ollama', 'text', 128000, 8192, FALSE, FALSE, FALSE),
('mistral:7b', 'Mistral 7B', 'ollama', 'text', 32768, 8192, FALSE, FALSE, FALSE),
('phi3:mini', 'Phi-3 Mini', 'ollama', 'text', 128000, 4096, FALSE, FALSE, FALSE),

-- Vision Models
('llava:7b', 'LLaVA 7B', 'ollama', 'vision', 4096, 2048, FALSE, TRUE, FALSE),
('bakllava:7b', 'BakLLaVA 7B', 'ollama', 'vision', 4096, 2048, FALSE, TRUE, FALSE)

ON CONFLICT (model_id) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    provider = EXCLUDED.provider,
    updated_at = NOW();

-- Insert OpenAI models
INSERT INTO models (model_id, display_name, provider, model_type, context_length, max_tokens, supports_functions, supports_vision, cost_per_1k_input, cost_per_1k_output) VALUES
('gpt-4o', 'GPT-4o', 'openai', 'multimodal', 128000, 16384, TRUE, TRUE, 0.00250, 0.01000),
('gpt-4o-mini', 'GPT-4o Mini', 'openai', 'multimodal', 128000, 16384, TRUE, TRUE, 0.00015, 0.00060),
('gpt-4-turbo', 'GPT-4 Turbo', 'openai', 'multimodal', 128000, 4096, TRUE, TRUE, 0.01000, 0.03000),
('gpt-3.5-turbo', 'GPT-3.5 Turbo', 'openai', 'text', 16385, 4096, TRUE, FALSE, 0.00050, 0.00150),
('o1', 'O1', 'openai', 'text', 200000, 100000, FALSE, FALSE, 0.01500, 0.06000),
('o1-mini', 'O1 Mini', 'openai', 'text', 128000, 65536, FALSE, FALSE, 0.00300, 0.01200)
ON CONFLICT (model_id) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    context_length = EXCLUDED.context_length,
    updated_at = NOW();

-- Insert Anthropic models
INSERT INTO models (model_id, display_name, provider, model_type, context_length, max_tokens, supports_functions, supports_vision, cost_per_1k_input, cost_per_1k_output) VALUES
('claude-3-5-sonnet-20241022', 'Claude 3.5 Sonnet', 'anthropic', 'multimodal', 200000, 8192, TRUE, TRUE, 0.00300, 0.01500),
('claude-3-5-haiku-20241022', 'Claude 3.5 Haiku', 'anthropic', 'text', 200000, 8192, TRUE, FALSE, 0.00080, 0.00400),
('claude-3-opus-20240229', 'Claude 3 Opus', 'anthropic', 'multimodal', 200000, 4096, TRUE, TRUE, 0.01500, 0.07500)
ON CONFLICT (model_id) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    context_length = EXCLUDED.context_length,
    updated_at = NOW();

-- ============================================================================
-- STEP 9: Create function to sync system config with application
-- ============================================================================

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

-- ============================================================================
-- STEP 10: Create view for active models
-- ============================================================================

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
-- STEP 11: Create trigger to update updated_at timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to system_config
DROP TRIGGER IF EXISTS trg_system_config_updated_at ON system_config;
CREATE TRIGGER trg_system_config_updated_at
    BEFORE UPDATE ON system_config
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

-- Apply trigger to models
DROP TRIGGER IF EXISTS trg_models_updated_at ON models;
CREATE TRIGGER trg_models_updated_at
    BEFORE UPDATE ON models
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

-- ============================================================================
-- STEP 12: Add helpful comments
-- ============================================================================

COMMENT ON COLUMN projects.primary_embedding_config IS 'Maps to config_id in embedding_configs.py (e.g., "all_minilm_l6_v2_384", "openai_3_large")';
COMMENT ON TABLE system_config IS 'Replaces hardcoded values in code. Read via get_system_config() or ORM query.';
COMMENT ON TABLE models IS 'Auto-populated by Ollama sync service. Manually add OpenAI/Claude models.';

COMMIT;

-- ============================================================================
-- Post-migration verification queries (commented out)
-- ============================================================================

-- Verify projects have embedding config
-- SELECT name, primary_embedding_config, department_id FROM projects;

-- Verify Global project exists
-- SELECT * FROM projects WHERE name = 'Global';

-- Verify admin user defaults
-- SELECT u.username, u.role, d.name AS department, t.name AS team
-- FROM users u
-- LEFT JOIN departments d ON u.department_id = d.id
-- LEFT JOIN teams t ON u.team_id = t.id
-- WHERE u.username = 'admin';

-- Verify system config
-- SELECT config_key, config_value, category FROM system_config ORDER BY category, config_key;

-- Verify models registry
-- SELECT * FROM active_models;

-- Verify Prefect schema
-- SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'prefect';

-- Get agent runtime configuration
-- SELECT get_system_config('agent.runtime.default_model');
-- SELECT get_system_config('agent.runtime.api_base_url');
