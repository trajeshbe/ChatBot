-- Migration: Add API Credentials Management Tables
-- Created: 2025-11-20
-- Purpose: Enable database-backed secrets management for API keys

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table: api_credentials
-- Stores encrypted API keys for various providers (OpenAI, Anthropic, HuggingFace)
CREATE TABLE IF NOT EXISTS api_credentials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider VARCHAR(50) UNIQUE NOT NULL,  -- 'openai', 'anthropic', 'huggingface'
    api_key_encrypted BYTEA NOT NULL,      -- Encrypted API key using Fernet
    encryption_key_id VARCHAR(100),         -- For key rotation tracking
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT provider_not_empty CHECK (provider != ''),
    CONSTRAINT api_key_encrypted_not_empty CHECK (length(api_key_encrypted) > 0)
);

-- Table: api_key_access_log
-- Audit log for all API key access attempts
CREATE TABLE IF NOT EXISTS api_key_access_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider VARCHAR(50) NOT NULL,
    user_id UUID REFERENCES users(id),
    action VARCHAR(50) NOT NULL,  -- 'created', 'updated', 'accessed', 'deleted', 'validated'
    ip_address VARCHAR(50),
    user_agent TEXT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT action_valid CHECK (action IN ('created', 'updated', 'accessed', 'deleted', 'validated', 'failed_validation'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_api_credentials_provider ON api_credentials(provider);
CREATE INDEX IF NOT EXISTS idx_api_credentials_is_active ON api_credentials(is_active);
CREATE INDEX IF NOT EXISTS idx_api_key_access_log_provider ON api_key_access_log(provider);
CREATE INDEX IF NOT EXISTS idx_api_key_access_log_user_id ON api_key_access_log(user_id);
CREATE INDEX IF NOT EXISTS idx_api_key_access_log_created_at ON api_key_access_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_api_key_access_log_action ON api_key_access_log(action);

-- Function: Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_api_credentials_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-update updated_at on api_credentials changes
CREATE TRIGGER trigger_update_api_credentials_timestamp
    BEFORE UPDATE ON api_credentials
    FOR EACH ROW
    EXECUTE FUNCTION update_api_credentials_updated_at();

-- Comments for documentation
COMMENT ON TABLE api_credentials IS 'Stores encrypted API keys for LLM providers with audit tracking';
COMMENT ON COLUMN api_credentials.provider IS 'Provider identifier (openai, anthropic, huggingface)';
COMMENT ON COLUMN api_credentials.api_key_encrypted IS 'Fernet-encrypted API key stored as binary data';
COMMENT ON COLUMN api_credentials.encryption_key_id IS 'ID of encryption key used for rotation tracking';
COMMENT ON COLUMN api_credentials.last_used_at IS 'Timestamp of last successful API call using this key';

COMMENT ON TABLE api_key_access_log IS 'Audit log for all API key access and modifications';
COMMENT ON COLUMN api_key_access_log.action IS 'Type of action performed on the API key';
COMMENT ON COLUMN api_key_access_log.success IS 'Whether the operation succeeded';

-- Grant permissions (adjust based on your RBAC setup)
-- GRANT SELECT, INSERT, UPDATE ON api_credentials TO backend_user;
-- GRANT SELECT, INSERT ON api_key_access_log TO backend_user;
