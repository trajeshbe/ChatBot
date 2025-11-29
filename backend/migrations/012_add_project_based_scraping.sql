-- Migration: Add Project-Based Scraping Support
-- Created: 2025-11-29
-- Description: Adds project, user, department, and team tracking to web scraping
--              Aligns scraping with the same organizational structure as file uploads

-- Add organizational and project tracking columns to web_scrape_jobs
ALTER TABLE web_scrape_jobs
ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES modules(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS scraped_by UUID REFERENCES users(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS department VARCHAR(255),
ADD COLUMN IF NOT EXISTS team VARCHAR(255);

-- Add indexes for performance and filtering
CREATE INDEX IF NOT EXISTS idx_web_scrape_jobs_project_id
ON web_scrape_jobs(project_id);

CREATE INDEX IF NOT EXISTS idx_web_scrape_jobs_scraped_by
ON web_scrape_jobs(scraped_by);

CREATE INDEX IF NOT EXISTS idx_web_scrape_jobs_department
ON web_scrape_jobs(department);

CREATE INDEX IF NOT EXISTS idx_web_scrape_jobs_team
ON web_scrape_jobs(team);

-- Add composite index for project-based queries
CREATE INDEX IF NOT EXISTS idx_web_scrape_jobs_project_status
ON web_scrape_jobs(project_id, status);

-- Add comments to document the new columns
COMMENT ON COLUMN web_scrape_jobs.project_id IS 'Link to project/module for organization';
COMMENT ON COLUMN web_scrape_jobs.scraped_by IS 'User who initiated the scraping job';
COMMENT ON COLUMN web_scrape_jobs.department IS 'Department name for organizational filtering';
COMMENT ON COLUMN web_scrape_jobs.team IS 'Team name for organizational filtering';

-- Update documents table to support project-based scraping (if not already present)
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES modules(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS department VARCHAR(255),
ADD COLUMN IF NOT EXISTS team VARCHAR(255),
ADD COLUMN IF NOT EXISTS uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL;

-- Add indexes on documents for project-based filtering
CREATE INDEX IF NOT EXISTS idx_documents_project_id
ON documents(project_id);

CREATE INDEX IF NOT EXISTS idx_documents_department
ON documents(department);

CREATE INDEX IF NOT EXISTS idx_documents_team
ON documents(team);

CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by
ON documents(uploaded_by);

-- Add composite index for efficient project document queries
CREATE INDEX IF NOT EXISTS idx_documents_project_source
ON documents(project_id, source_type);

-- Add comments
COMMENT ON COLUMN documents.project_id IS 'Link to project/module for organization';
COMMENT ON COLUMN documents.department IS 'Department name for organizational filtering';
COMMENT ON COLUMN documents.team IS 'Team name for organizational filtering';
COMMENT ON COLUMN documents.uploaded_by IS 'User who uploaded/scraped the document';
