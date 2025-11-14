-- Migration: Add RBAC, Session Management, and Audit Logging
-- Version: 001
-- Date: 2025-11-14
-- Description: Adds comprehensive user management, RBAC, session tracking, and audit logging

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- User Roles Enum
CREATE TYPE user_role AS ENUM ('admin', 'user', 'viewer', 'api_user');

-- Action Types Enum (for audit logging)
CREATE TYPE action_type AS ENUM (
    'query', 'upload', 'scrape', 'delete', 'login', 'logout',
    'create', 'update', 'view'
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    hashed_password VARCHAR(255) NOT NULL,
    role user_role DEFAULT 'user' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    meta_info JSONB
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- API Keys table
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

-- Chat Sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    meta_info JSONB
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_active ON chat_sessions(is_active);

-- Session Documents (Short-term memory)
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

-- Conversation Messages (replaces old messages table)
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

-- Audit Logs
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

-- Usage Metrics
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

-- Document Permissions
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

-- Session Context (Short-term memory settings)
CREATE TABLE IF NOT EXISTS session_contexts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID UNIQUE NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    preferred_model VARCHAR(100),
    context_window_size INTEGER DEFAULT 10,
    temperature DOUBLE PRECISION DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 1024,
    active_document_ids JSONB,
    conversation_summary TEXT,
    conversation_embedding vector(384),
    tags JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_info JSONB
);

CREATE INDEX IF NOT EXISTS idx_session_contexts_session ON session_contexts(session_id);

-- Create default admin user (password: admin123 - CHANGE IN PRODUCTION!)
-- Password hash is bcrypt hash of "admin123"
INSERT INTO users (username, email, full_name, role, hashed_password, is_active, is_verified)
VALUES (
    'admin',
    'admin@example.com',
    'System Administrator',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU3bKuYjh/5u',
    TRUE,
    TRUE
)
ON CONFLICT (username) DO NOTHING;

-- Create default API user for anonymous access
INSERT INTO users (username, email, full_name, role, hashed_password, is_active, is_verified)
VALUES (
    'anonymous',
    'anonymous@example.com',
    'Anonymous User',
    'user',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU3bKuYjh/5u',
    TRUE,
    TRUE
)
ON CONFLICT (username) DO NOTHING;

-- Add triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chat_sessions_updated_at BEFORE UPDATE ON chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_session_contexts_updated_at BEFORE UPDATE ON session_contexts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE users IS 'User accounts with RBAC support';
COMMENT ON TABLE chat_sessions IS 'Chat sessions with user tracking';
COMMENT ON TABLE session_documents IS 'Short-term memory: documents associated with active sessions';
COMMENT ON TABLE conversation_messages IS 'Messages within chat sessions';
COMMENT ON TABLE audit_logs IS 'Comprehensive audit trail for all user actions';
COMMENT ON TABLE usage_metrics IS 'Aggregated usage metrics for analytics';
COMMENT ON TABLE document_permissions IS 'Fine-grained document access control';
COMMENT ON TABLE session_contexts IS 'Session-specific context and preferences (short-term memory)';

-- Grant permissions (adjust as needed for your environment)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
