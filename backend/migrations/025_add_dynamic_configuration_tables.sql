-- Migration: Add Dynamic Configuration Tables
-- Date: 2026-01-03
-- Purpose: Enable UI-based configuration for all Domain Verticals and Customer Solutions

-- ============================================================================
-- 1. Module Configurations Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS module_configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    module_name VARCHAR(100) NOT NULL UNIQUE,  -- 'british_council', 'cru', 'talent_search', etc.
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    module_type VARCHAR(50) NOT NULL,  -- 'tier2_domain_vertical' or 'tier3_customer_solution'
    category VARCHAR(100),  -- 'procurement', 'hr_talent', 'agriculture', etc.

    -- Configuration JSON (JSONB for querying)
    config JSONB NOT NULL DEFAULT '{}',

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,

    -- Version tracking
    current_version INTEGER DEFAULT 1,

    CONSTRAINT unique_module_name UNIQUE(module_name)
);

CREATE INDEX idx_module_configs_name ON module_configurations(module_name);
CREATE INDEX idx_module_configs_type ON module_configurations(module_type);
CREATE INDEX idx_module_configs_category ON module_configurations(category);
CREATE INDEX idx_module_configs_active ON module_configurations(is_active);
CREATE INDEX idx_module_configs_config ON module_configurations USING GIN(config);

COMMENT ON TABLE module_configurations IS 'Base configuration for each Tier 2/3 module';
COMMENT ON COLUMN module_configurations.config IS 'JSONB containing llm, prompts, parameters, thresholds, scoring, features';

-- ============================================================================
-- 2. Module User Overrides Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS module_user_overrides (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    module_name VARCHAR(100) NOT NULL,

    -- Override configuration (only contains overridden fields)
    overrides JSONB NOT NULL DEFAULT '{}',

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,

    -- A/B Testing support
    variant_name VARCHAR(100),  -- 'control', 'variant_a', 'variant_b'
    experiment_id UUID,

    CONSTRAINT unique_user_module UNIQUE(user_id, module_name)
);

CREATE INDEX idx_user_overrides_user ON module_user_overrides(user_id);
CREATE INDEX idx_user_overrides_module ON module_user_overrides(module_name);
CREATE INDEX idx_user_overrides_variant ON module_user_overrides(variant_name);
CREATE INDEX idx_user_overrides_experiment ON module_user_overrides(experiment_id);

COMMENT ON TABLE module_user_overrides IS 'Per-user/customer configuration overrides for A/B testing and personalization';

-- ============================================================================
-- 3. Config Versions Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS config_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    module_name VARCHAR(100) NOT NULL,
    version INTEGER NOT NULL,

    -- Full configuration snapshot at this version
    config JSONB NOT NULL,

    -- Change tracking
    changed_by UUID REFERENCES users(id),
    changed_at TIMESTAMP DEFAULT NOW(),
    change_description TEXT,

    -- Diff from previous version (JSON patch format)
    diff JSONB,

    CONSTRAINT unique_module_version UNIQUE(module_name, version)
);

CREATE INDEX idx_versions_module ON config_versions(module_name);
CREATE INDEX idx_versions_version ON config_versions(version DESC);
CREATE INDEX idx_versions_changed_at ON config_versions(changed_at DESC);

COMMENT ON TABLE config_versions IS 'Version history for configuration changes (audit trail)';

-- ============================================================================
-- 4. Config Schemas Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS config_schemas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    schema_name VARCHAR(100) NOT NULL UNIQUE,
    schema_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    module_type VARCHAR(50),  -- NULL = global schema, or 'tier2_domain_vertical', etc.

    -- JSON Schema definition
    schema JSONB NOT NULL,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,

    CONSTRAINT unique_schema_name_version UNIQUE(schema_name, schema_version)
);

CREATE INDEX idx_schemas_name ON config_schemas(schema_name);
CREATE INDEX idx_schemas_type ON config_schemas(module_type);
CREATE INDEX idx_schemas_active ON config_schemas(is_active);

COMMENT ON TABLE config_schemas IS 'JSON schemas for validating module configurations';

-- ============================================================================
-- 5. Config Templates Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS config_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Template configuration
    template JSONB NOT NULL,

    -- Categories and tags
    category VARCHAR(100),  -- 'education', 'finance', 'automotive', 'insurance', 'procurement'
    tags TEXT[],
    module_type VARCHAR(50),  -- 'tier2_domain_vertical' or 'tier3_customer_solution'

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    is_public BOOLEAN DEFAULT TRUE,
    usage_count INTEGER DEFAULT 0,

    CONSTRAINT unique_template_name UNIQUE(template_name)
);

CREATE INDEX idx_templates_category ON config_templates(category);
CREATE INDEX idx_templates_tags ON config_templates USING GIN(tags);
CREATE INDEX idx_templates_type ON config_templates(module_type);
CREATE INDEX idx_templates_public ON config_templates(is_public);

COMMENT ON TABLE config_templates IS 'Reusable configuration templates for quick module setup';

-- ============================================================================
-- 6. Config Audit Logs Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS config_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    module_name VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,  -- 'create', 'update', 'delete', 'override', 'restore'

    -- Change details
    changed_field_path VARCHAR(255),  -- 'llm.model', 'prompts.system.main'
    old_value JSONB,
    new_value JSONB,

    -- User context
    changed_by UUID REFERENCES users(id),
    changed_at TIMESTAMP DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,

    -- Additional context
    change_reason TEXT,
    metadata JSONB
);

CREATE INDEX idx_audit_module ON config_audit_logs(module_name);
CREATE INDEX idx_audit_user ON config_audit_logs(changed_by);
CREATE INDEX idx_audit_time ON config_audit_logs(changed_at DESC);
CREATE INDEX idx_audit_action ON config_audit_logs(action);

COMMENT ON TABLE config_audit_logs IS 'Detailed audit trail for all configuration changes';

-- ============================================================================
-- 7. Insert Default Global Schema
-- ============================================================================
INSERT INTO config_schemas (schema_name, schema_version, module_type, schema, is_active)
VALUES (
    'global_module_config',
    '1.0',
    NULL,  -- Global schema
    '{
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Global Module Configuration Schema",
        "type": "object",
        "properties": {
            "llm": {
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "enum": ["gpt-4o-mini", "gpt-4", "gpt-4-turbo", "claude-3-5-sonnet-20241022", "claude-3-opus", "claude-3-sonnet", "mistral-large", "llama3.1"],
                        "default": "gpt-4o-mini"
                    },
                    "temperature": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 2,
                        "default": 0.2
                    },
                    "max_tokens": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 128000,
                        "default": 1000
                    },
                    "top_p": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "default": 1.0
                    },
                    "frequency_penalty": {
                        "type": "number",
                        "minimum": -2.0,
                        "maximum": 2.0,
                        "default": 0.0
                    },
                    "presence_penalty": {
                        "type": "number",
                        "minimum": -2.0,
                        "maximum": 2.0,
                        "default": 0.0
                    }
                }
            },
            "prompts": {
                "type": "object",
                "properties": {
                    "system": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "string"
                        }
                    },
                    "user": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "string"
                        }
                    }
                }
            },
            "parameters": {
                "type": "object",
                "additionalProperties": true
            },
            "thresholds": {
                "type": "object",
                "additionalProperties": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1
                }
            },
            "scoring": {
                "type": "object",
                "properties": {
                    "weights": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1
                        }
                    }
                }
            },
            "features": {
                "type": "object",
                "additionalProperties": {
                    "type": "boolean"
                }
            },
            "retrieval": {
                "type": "object",
                "properties": {
                    "top_k": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100
                    },
                    "rerank_top_k": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 50
                    }
                }
            }
        }
    }'::jsonb,
    TRUE
)
ON CONFLICT (schema_name, schema_version) DO NOTHING;

-- ============================================================================
-- 8. Grant Permissions
-- ============================================================================
-- GRANT ALL ON module_configurations TO postgres;
-- GRANT ALL ON module_user_overrides TO postgres;
-- GRANT ALL ON config_versions TO postgres;
-- GRANT ALL ON config_schemas TO postgres;
-- GRANT ALL ON config_templates TO postgres;
-- GRANT ALL ON config_audit_logs TO postgres;

COMMENT ON SCHEMA public IS 'Dynamic configuration system for Tier 2 & 3 modules';
