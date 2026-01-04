-- Migration: 026_add_export_wizard_tables.sql
-- Description: Add Export Wizard tables for POC-to-Production export functionality
-- Author: Claude Code
-- Date: 2026-01-03
-- Implements: Phase 1 - Core Export Engine

-- ============================================================================
-- Export Jobs Table
-- ============================================================================

CREATE TYPE deployment_type AS ENUM (
    'docker_compose',
    'docker_compose_ha',
    'kubernetes',
    'aws_cloudformation',
    'aws_terraform',
    'azure_arm',
    'azure_bicep',
    'gcp_deployment_manager',
    'gcp_terraform'
);

CREATE TYPE export_status AS ENUM (
    'pending',
    'in_progress',
    'completed',
    'failed',
    'cancelled'
);

CREATE TYPE license_tier AS ENUM (
    'starter',         -- $50K/year
    'professional',    -- $100K/year
    'enterprise'       -- $250K/year
);

CREATE TABLE export_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Job metadata
    job_name VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(255) NOT NULL,
    module_name VARCHAR(255) NOT NULL,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,

    -- Export configuration
    deployment_type deployment_type NOT NULL,
    license_tier license_tier NOT NULL DEFAULT 'professional',

    -- Customer information
    customer_name VARCHAR(255) NOT NULL,
    customer_email VARCHAR(255),
    license_expiry TIMESTAMP,
    max_users INTEGER,

    -- Export options (JSON)
    options JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Example:
    -- {
    --   "include_embeddings": true,
    --   "include_monitoring": true,
    --   "include_backups": true,
    --   "white_label": true,
    --   "custom_branding": {...},
    --   "security_level": "advanced",
    --   "enable_telemetry": false,
    --   "include_source_code": false
    -- }

    -- Job status
    status export_status DEFAULT 'pending' NOT NULL,
    progress_percentage FLOAT DEFAULT 0.0 NOT NULL,
    current_step VARCHAR(255),

    -- Timing
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Results (FK constraint added later to avoid circular dependency)
    export_package_id UUID,
    package_path TEXT,
    package_size_bytes BIGINT,

    -- Statistics (JSON)
    stats JSONB,
    -- Example:
    -- {
    --   "documents_exported": 145,
    --   "embeddings_exported": 4500,
    --   "total_chunks": 4500,
    --   "configuration_items": 45,
    --   "processing_time_seconds": 245
    -- }

    -- Error tracking
    error_message TEXT,
    error_details JSONB,

    -- Audit
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for export_jobs
CREATE INDEX idx_export_jobs_tenant_id ON export_jobs(tenant_id);
CREATE INDEX idx_export_jobs_status ON export_jobs(status);
CREATE INDEX idx_export_jobs_created_at ON export_jobs(created_at DESC);
CREATE INDEX idx_export_jobs_module_name ON export_jobs(module_name);

-- Trigger for updated_at
CREATE TRIGGER update_export_jobs_updated_at
    BEFORE UPDATE ON export_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Export Packages Table
-- ============================================================================

CREATE TABLE export_packages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Package metadata
    package_name VARCHAR(255) NOT NULL UNIQUE,
    version VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,

    -- Source information
    tenant_id VARCHAR(255) NOT NULL,
    module_name VARCHAR(255) NOT NULL,
    export_job_id UUID NOT NULL REFERENCES export_jobs(id) ON DELETE CASCADE,

    -- Package details
    deployment_type deployment_type NOT NULL,
    package_path TEXT NOT NULL,
    package_size_bytes BIGINT NOT NULL,
    checksum_sha256 VARCHAR(64) NOT NULL,

    -- Contents manifest (JSON)
    manifest JSONB NOT NULL,
    -- Example:
    -- {
    --   "documents": [...],
    --   "embeddings_count": 4500,
    --   "configuration_files": [...],
    --   "infrastructure_files": [...],
    --   "docker_images": [...],
    --   "scripts": [...]
    -- }

    -- License information
    license_key TEXT NOT NULL,  -- RSA-4096 signed
    license_tier license_tier NOT NULL,
    license_issued_at TIMESTAMP DEFAULT NOW(),
    license_expires_at TIMESTAMP,

    -- Customer information
    customer_name VARCHAR(255) NOT NULL,
    customer_email VARCHAR(255),
    max_users INTEGER,

    -- Download tracking
    download_count INTEGER DEFAULT 0 NOT NULL,
    last_downloaded_at TIMESTAMP,

    -- Deployment tracking
    deployed BOOLEAN DEFAULT FALSE NOT NULL,
    deployment_url VARCHAR(512),
    deployed_at TIMESTAMP,

    -- Metadata
    notes TEXT,
    tags JSONB  -- ["production", "customer-acme", "v1.0"]
);

-- Indexes for export_packages
CREATE INDEX idx_export_packages_tenant_id ON export_packages(tenant_id);
CREATE INDEX idx_export_packages_module_name ON export_packages(module_name);
CREATE INDEX idx_export_packages_created_at ON export_packages(created_at DESC);
CREATE INDEX idx_export_packages_export_job_id ON export_packages(export_job_id);

-- ============================================================================
-- Export Templates Table
-- ============================================================================

CREATE TABLE export_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Template metadata
    name VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),  -- "finance", "healthcare", "retail", etc.

    -- Template configuration
    deployment_type deployment_type NOT NULL,
    license_tier license_tier NOT NULL,

    -- Default options (JSON)
    default_options JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Infrastructure settings (JSON)
    infrastructure_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Example:
    -- {
    --   "replicas": 3,
    --   "resource_limits": {...},
    --   "auto_scaling": {...}
    -- }

    -- Usage tracking
    usage_count INTEGER DEFAULT 0 NOT NULL,

    -- Metadata
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for export_templates
CREATE INDEX idx_export_templates_category ON export_templates(category);
CREATE INDEX idx_export_templates_is_active ON export_templates(is_active);

-- Trigger for updated_at
CREATE TRIGGER update_export_templates_updated_at
    BEFORE UPDATE ON export_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Deployment Instances Table
-- ============================================================================

CREATE TABLE deployment_instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Instance metadata
    instance_name VARCHAR(255) NOT NULL,
    export_package_id UUID NOT NULL REFERENCES export_packages(id) ON DELETE CASCADE,

    -- Deployment details
    deployment_type deployment_type NOT NULL,
    deployment_url VARCHAR(512),
    environment VARCHAR(50),  -- "production", "staging", "dev"

    -- Infrastructure information
    cloud_provider VARCHAR(50),  -- "aws", "azure", "gcp", "on-prem"
    region VARCHAR(100),
    cluster_info JSONB,

    -- Health status
    status VARCHAR(50) DEFAULT 'unknown' NOT NULL,
    last_health_check TIMESTAMP,
    health_data JSONB,
    -- Example:
    -- {
    --   "api_healthy": true,
    --   "database_healthy": true,
    --   "vector_db_healthy": true,
    --   "uptime_seconds": 345600,
    --   "version": "1.0.0"
    -- }

    -- Telemetry (if enabled)
    telemetry_enabled BOOLEAN DEFAULT FALSE NOT NULL,
    telemetry_data JSONB,
    -- Example:
    -- {
    --   "total_queries": 15420,
    --   "active_users": 45,
    --   "avg_response_time_ms": 342,
    --   "error_rate": 0.02
    -- }

    -- Timing
    deployed_at TIMESTAMP DEFAULT NOW() NOT NULL,
    last_updated_at TIMESTAMP,
    decommissioned_at TIMESTAMP,

    -- Contact
    contact_email VARCHAR(255),
    contact_name VARCHAR(255)
);

-- Indexes for deployment_instances
CREATE INDEX idx_deployment_instances_package_id ON deployment_instances(export_package_id);
CREATE INDEX idx_deployment_instances_status ON deployment_instances(status);
CREATE INDEX idx_deployment_instances_environment ON deployment_instances(environment);
CREATE INDEX idx_deployment_instances_deployed_at ON deployment_instances(deployed_at DESC);

-- ============================================================================
-- Export Audit Log Table
-- ============================================================================

CREATE TABLE export_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Event metadata
    event_type VARCHAR(100) NOT NULL,
    -- "export_initiated", "export_completed", "export_failed",
    -- "package_downloaded", "deployment_created", etc.

    timestamp TIMESTAMP DEFAULT NOW() NOT NULL,

    -- Related entities
    export_job_id UUID,
    export_package_id UUID,
    deployment_instance_id UUID,

    -- User information
    user_id VARCHAR(255),
    user_email VARCHAR(255),
    ip_address VARCHAR(45),

    -- Event details (JSON)
    details JSONB,
    -- Example:
    -- {
    --   "action": "initiated_export",
    --   "module": "british_council",
    --   "deployment_type": "kubernetes",
    --   "options": {...}
    -- }

    -- Status
    status VARCHAR(50) NOT NULL,  -- "success", "failure", "warning"
    error_message TEXT
);

-- Indexes for export_audit_logs
CREATE INDEX idx_export_audit_logs_event_type ON export_audit_logs(event_type);
CREATE INDEX idx_export_audit_logs_timestamp ON export_audit_logs(timestamp DESC);
CREATE INDEX idx_export_audit_logs_export_job_id ON export_audit_logs(export_job_id);
CREATE INDEX idx_export_audit_logs_export_package_id ON export_audit_logs(export_package_id);
CREATE INDEX idx_export_audit_logs_user_id ON export_audit_logs(user_id);

-- ============================================================================
-- Seed Data: Export Templates
-- ============================================================================

-- Template 1: Quick Start (Docker Compose)
INSERT INTO export_templates (name, display_name, description, category, deployment_type, license_tier, default_options, infrastructure_config)
VALUES (
    'quick_start_docker',
    'Quick Start - Docker Compose',
    'Single-server deployment for development and small teams',
    'development',
    'docker_compose',
    'starter',
    '{
        "include_embeddings": true,
        "include_monitoring": false,
        "include_backups": false,
        "white_label": false,
        "security_level": "basic",
        "enable_telemetry": true
    }'::jsonb,
    '{
        "replicas": 1,
        "resource_limits": {
            "backend_memory": "2GB",
            "postgres_memory": "1GB"
        }
    }'::jsonb
);

-- Template 2: Production (Kubernetes)
INSERT INTO export_templates (name, display_name, description, category, deployment_type, license_tier, default_options, infrastructure_config)
VALUES (
    'production_kubernetes',
    'Production - Kubernetes',
    'High-availability multi-node deployment for production workloads',
    'production',
    'kubernetes',
    'professional',
    '{
        "include_embeddings": true,
        "include_monitoring": true,
        "include_backups": true,
        "white_label": true,
        "security_level": "advanced",
        "enable_telemetry": false
    }'::jsonb,
    '{
        "replicas": 3,
        "resource_limits": {
            "backend_cpu": "2000m",
            "backend_memory": "4GB",
            "postgres_cpu": "1000m",
            "postgres_memory": "2GB"
        },
        "auto_scaling": {
            "enabled": true,
            "min_replicas": 3,
            "max_replicas": 10,
            "target_cpu_percent": 70
        }
    }'::jsonb
);

-- Template 3: Enterprise (AWS)
INSERT INTO export_templates (name, display_name, description, category, deployment_type, license_tier, default_options, infrastructure_config)
VALUES (
    'enterprise_aws',
    'Enterprise - AWS CloudFormation',
    'Enterprise-grade deployment on AWS with full compliance features',
    'enterprise',
    'aws_cloudformation',
    'enterprise',
    '{
        "include_embeddings": true,
        "include_monitoring": true,
        "include_backups": true,
        "white_label": true,
        "security_level": "enterprise",
        "enable_telemetry": false,
        "include_source_code": true
    }'::jsonb,
    '{
        "replicas": 5,
        "resource_limits": {
            "backend_instance_type": "m5.xlarge",
            "postgres_instance_type": "r5.large"
        },
        "auto_scaling": {
            "enabled": true,
            "min_replicas": 5,
            "max_replicas": 20,
            "target_cpu_percent": 60
        },
        "backup": {
            "enabled": true,
            "retention_days": 30,
            "point_in_time_recovery": true
        },
        "compliance": {
            "soc2": true,
            "hipaa": true,
            "gdpr": true
        }
    }'::jsonb
);

-- ============================================================================
-- Add Foreign Key Constraints (after both tables exist)
-- ============================================================================

-- Add FK from export_jobs to export_packages
ALTER TABLE export_jobs
ADD CONSTRAINT fk_export_jobs_export_package_id
FOREIGN KEY (export_package_id) REFERENCES export_packages(id) ON DELETE SET NULL;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE export_jobs IS 'Tracks POC export jobs from initiation to completion';
COMMENT ON TABLE export_packages IS 'Metadata for exported packages ready for customer deployment';
COMMENT ON TABLE export_templates IS 'Predefined templates for common export configurations';
COMMENT ON TABLE deployment_instances IS 'Tracks deployed instances and their health status';
COMMENT ON TABLE export_audit_logs IS 'Audit trail for all export wizard operations';

COMMENT ON COLUMN export_jobs.options IS 'Export options: embeddings, monitoring, backups, branding, security level, telemetry';
COMMENT ON COLUMN export_jobs.stats IS 'Export statistics: documents exported, embeddings, chunks, config items, processing time';
COMMENT ON COLUMN export_packages.manifest IS 'Complete manifest of package contents: documents, embeddings, config, infrastructure, images, scripts';
COMMENT ON COLUMN export_packages.license_key IS 'RSA-4096 digitally signed license key';
COMMENT ON COLUMN deployment_instances.health_data IS 'Health check data: API, database, vector DB status, uptime, version';
COMMENT ON COLUMN deployment_instances.telemetry_data IS 'Usage telemetry: queries, users, response times, error rates';

-- ============================================================================
-- Migration Complete
-- ============================================================================

-- Verify tables were created
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
    AND tablename IN ('export_jobs', 'export_packages', 'export_templates', 'deployment_instances', 'export_audit_logs')
ORDER BY tablename;

COMMENT ON SCHEMA public IS 'Export Wizard tables added in migration 026';
