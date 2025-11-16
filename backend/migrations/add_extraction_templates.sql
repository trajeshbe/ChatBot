-- Migration: Add extraction templates and related tables
-- Phase 2: Template System & Field Mapping
-- Date: 2025-11-16

-- Create extraction_templates table
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

-- Create index on active templates
CREATE INDEX IF NOT EXISTS idx_extraction_templates_active
ON extraction_templates(is_active)
WHERE is_active = TRUE;

-- Create index on template type
CREATE INDEX IF NOT EXISTS idx_extraction_templates_type
ON extraction_templates(template_type);

-- Create extraction_jobs table
CREATE TABLE IF NOT EXISTS extraction_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_name VARCHAR(255) NOT NULL,
    template_id UUID REFERENCES extraction_templates(id) ON DELETE CASCADE,

    -- Job configuration
    urls JSONB NOT NULL,                 -- Array of URLs to scrape
    scraper_config JSONB,                -- Scraper configuration

    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, processing, completed, failed
    progress_percentage INTEGER DEFAULT 0,
    urls_total INTEGER DEFAULT 0,
    urls_processed INTEGER DEFAULT 0,
    records_extracted INTEGER DEFAULT 0,

    -- Quality metrics
    quality_score FLOAT,
    validation_errors JSONB,

    -- Output configuration
    output_format VARCHAR(50) NOT NULL,  -- excel, csv, json, xml, parquet
    output_file_path VARCHAR(512),       -- MinIO path to result file
    delivery_method VARCHAR(50),         -- download, email, webhook, storage
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

-- Create indexes for extraction_jobs
CREATE INDEX IF NOT EXISTS idx_extraction_jobs_template
ON extraction_jobs(template_id);

CREATE INDEX IF NOT EXISTS idx_extraction_jobs_status
ON extraction_jobs(status);

CREATE INDEX IF NOT EXISTS idx_extraction_jobs_created
ON extraction_jobs(created_at DESC);

-- Create extraction_results table (stores extracted data)
CREATE TABLE IF NOT EXISTS extraction_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES extraction_jobs(id) ON DELETE CASCADE,

    -- Source information
    source_url VARCHAR(1024) NOT NULL,
    source_index INTEGER,                -- Order in the URL list

    -- Extracted data
    extracted_data JSONB NOT NULL,       -- Extracted fields as JSON
    raw_content TEXT,                    -- Raw scraped content

    -- Quality metrics
    extraction_confidence FLOAT,         -- 0-1 confidence score
    validation_errors JSONB,             -- Field-level validation errors

    -- Metadata
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for extraction_results
CREATE INDEX IF NOT EXISTS idx_extraction_results_job
ON extraction_results(job_id);

CREATE INDEX IF NOT EXISTS idx_extraction_results_url
ON extraction_results(source_url);

-- Create extraction_job_schedules table
CREATE TABLE IF NOT EXISTS extraction_job_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_name VARCHAR(255) NOT NULL,
    template_id UUID REFERENCES extraction_templates(id) ON DELETE CASCADE,

    -- Schedule configuration
    schedule_type VARCHAR(50) NOT NULL,  -- one_time, recurring, event_triggered
    cron_expression VARCHAR(100),        -- For recurring jobs
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

-- Create indexes for extraction_job_schedules
CREATE INDEX IF NOT EXISTS idx_extraction_schedules_template
ON extraction_job_schedules(template_id);

CREATE INDEX IF NOT EXISTS idx_extraction_schedules_active
ON extraction_job_schedules(is_active)
WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_extraction_schedules_next_run
ON extraction_job_schedules(next_run_at)
WHERE is_active = TRUE;

-- Add triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_extraction_templates_updated_at
    BEFORE UPDATE ON extraction_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_extraction_jobs_updated_at
    BEFORE UPDATE ON extraction_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_extraction_schedules_updated_at
    BEFORE UPDATE ON extraction_job_schedules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add sample template for testing
INSERT INTO extraction_templates (name, description, template_type, schema_definition, fields)
VALUES (
    'Company Data Extraction',
    'Extract company information from websites',
    'json',
    '{"version": "1.0", "type": "company_data"}',
    '[
        {
            "name": "company_name",
            "type": "string",
            "required": true,
            "source_hint": {
                "type": "css",
                "selector": ".company-name, h1.title"
            },
            "validation": {
                "min_length": 2,
                "max_length": 200
            }
        },
        {
            "name": "revenue",
            "type": "number",
            "required": false,
            "source_hint": {
                "type": "llm",
                "prompt": "Extract the annual revenue of the company"
            },
            "transformation": "extract_number",
            "validation": {
                "min_value": 0
            }
        },
        {
            "name": "founded_year",
            "type": "integer",
            "required": false,
            "source_hint": {
                "type": "regex",
                "pattern": "Founded in (\\\\d{4})"
            },
            "validation": {
                "min_value": 1800,
                "max_value": 2025
            }
        }
    ]'::JSONB
);

COMMENT ON TABLE extraction_templates IS 'Templates for data extraction with field definitions';
COMMENT ON TABLE extraction_jobs IS 'Extraction job execution records';
COMMENT ON TABLE extraction_results IS 'Individual extraction results per URL';
COMMENT ON TABLE extraction_job_schedules IS 'Scheduled extraction jobs';
