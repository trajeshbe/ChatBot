-- Migration 024: Tier 2 Module Management and Document Extraction Results
-- Created: 2026-01-01
-- Description: Add tables for module registry, activations, and extraction results

-- Module Registry: Track all tier_2 and tier_3 modules
CREATE TABLE IF NOT EXISTS skill_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id VARCHAR(100) UNIQUE NOT NULL,  -- e.g., "docu-extract"
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50) NOT NULL,
    tier INTEGER NOT NULL CHECK (tier IN (2, 3)),  -- 2 = vertical, 3 = customer
    category VARCHAR(100),  -- e.g., "document_intelligence", "construction"
    status VARCHAR(50) DEFAULT 'disabled' CHECK (status IN ('enabled', 'disabled', 'error')),
    routes_prefix VARCHAR(255),
    dependencies JSONB,  -- List of tier_1 services required
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_skill_modules_tier ON skill_modules(tier);
CREATE INDEX idx_skill_modules_category ON skill_modules(category);
CREATE INDEX idx_skill_modules_status ON skill_modules(status);

-- Module Activations: Track which modules are enabled for which projects/users
CREATE TABLE IF NOT EXISTS module_activations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id VARCHAR(100) NOT NULL REFERENCES skill_modules(module_id),
    project_id UUID REFERENCES projects(id),  -- NULL = global activation
    user_id UUID REFERENCES users(id),  -- NULL = available to all users
    enabled BOOLEAN DEFAULT TRUE,
    activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activated_by UUID REFERENCES users(id),
    deactivated_at TIMESTAMP,
    deactivated_by UUID REFERENCES users(id),
    UNIQUE(module_id, project_id, user_id)
);

CREATE INDEX idx_module_activations_module ON module_activations(module_id);
CREATE INDEX idx_module_activations_project ON module_activations(project_id);
CREATE INDEX idx_module_activations_enabled ON module_activations(enabled);

-- Document Extractions: Track extraction requests and status
CREATE TABLE IF NOT EXISTS document_extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id),
    session_id VARCHAR(255),
    project_id UUID REFERENCES projects(id),
    user_id UUID REFERENCES users(id),
    module_id VARCHAR(100) DEFAULT 'docu-extract',
    extraction_mode VARCHAR(50) DEFAULT 'auto' CHECK (extraction_mode IN ('auto', 'text', 'vision', 'hybrid')),
    model_used VARCHAR(100),
    status VARCHAR(50) DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed')),
    fields_extracted INTEGER,
    total_fields INTEGER DEFAULT 18,
    extraction_confidence FLOAT,
    processing_time_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_document_extractions_document ON document_extractions(document_id);
CREATE INDEX idx_document_extractions_session ON document_extractions(session_id);
CREATE INDEX idx_document_extractions_status ON document_extractions(status);
CREATE INDEX idx_document_extractions_module ON document_extractions(module_id);

-- Extraction Results: Store the 18-field extraction data
CREATE TABLE IF NOT EXISTS extraction_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    extraction_id UUID NOT NULL REFERENCES document_extractions(id) ON DELETE CASCADE,
    
    -- Project Metadata (11 fields)
    project_name TEXT,
    address TEXT,
    project_status VARCHAR(50),
    storeys INTEGER,
    gross_floor_area FLOAT,
    site_area FLOAT,
    zoning VARCHAR(100),
    heritage_designation TEXT,
    architect VARCHAR(255),
    developer VARCHAR(255),
    planning_consultant VARCHAR(255),
    
    -- Building Information (7 fields)
    residential_units INTEGER,
    unit_types JSONB,  -- Array of strings
    commercial_uses JSONB,  -- Array of strings
    amenities JSONB,  -- Array of strings
    parking_levels INTEGER,
    parking_spaces INTEGER,
    public_realm_features JSONB,  -- Array of strings
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_extraction_results_extraction ON extraction_results(extraction_id);
CREATE INDEX idx_extraction_results_project_name ON extraction_results(project_name);

-- Seed default docu-extract module
INSERT INTO skill_modules (module_id, name, description, version, tier, category, status, routes_prefix, dependencies)
VALUES (
    'docu-extract',
    'Document Intelligence Extraction',
    'Extract 18 structured fields from planning documents and architectural drawings using GPT-4o Vision',
    '1.0.0',
    2,
    'document_intelligence',
    'enabled',
    '/api/v1/modules/docu-extract',
    '["llm_service", "vision_service", "document_service", "hybrid_extraction_service", "ocr_service"]'::jsonb
)
ON CONFLICT (module_id) DO NOTHING;

-- Activate globally for all projects
INSERT INTO module_activations (module_id, project_id, user_id, enabled, activated_by)
SELECT 
    'docu-extract',
    NULL,  -- Global activation
    NULL,  -- Available to all users
    TRUE,
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1)
ON CONFLICT (module_id, project_id, user_id) WHERE project_id IS NULL AND user_id IS NULL DO NOTHING;
