-- Migration: Add model preferences to projects
-- Purpose: Each project can have its own preferred LLM model

ALTER TABLE projects
ADD COLUMN IF NOT EXISTS preferred_model VARCHAR(100);

ALTER TABLE projects
ADD COLUMN IF NOT EXISTS model_config JSONB DEFAULT '{}'::jsonb;

COMMENT ON COLUMN projects.preferred_model IS 'Preferred LLM model for this project (e.g., gpt-4-turbo-preview, claude-3-5-sonnet)';
COMMENT ON COLUMN projects.model_config IS 'Additional model configuration (temperature, max_tokens, etc.)';

-- Create index for faster model lookups
CREATE INDEX IF NOT EXISTS idx_projects_preferred_model ON projects(preferred_model) WHERE preferred_model IS NOT NULL;
