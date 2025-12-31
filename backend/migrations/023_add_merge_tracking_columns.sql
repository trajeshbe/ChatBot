-- Migration: Add LoRA Adapter Merge Tracking Columns
-- Date: 2025-12-22
-- JIRA: FINETUNE-002
-- Purpose: Track merge status and paths for fine-tuned models

-- Add merge tracking columns to finetuned_models table
ALTER TABLE finetuned_models
ADD COLUMN IF NOT EXISTS merged_model_path TEXT,
ADD COLUMN IF NOT EXISTS merge_duration_seconds INTEGER,
ADD COLUMN IF NOT EXISTS merge_requested_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS merge_error_message TEXT;

-- Create index for faster merge status queries
-- Note: We reuse the existing 'status' column for merge tracking
-- Status values: 'adapter_only', 'merging', 'merged', 'deployed', 'merge_failed'
CREATE INDEX IF NOT EXISTS idx_finetuned_models_status ON finetuned_models(status);

-- Add comment for documentation
COMMENT ON COLUMN finetuned_models.merged_model_path IS 'Path to merged model in MinIO or workspace (/workspace/finetuning/{job_id}/output/merged_model)';
COMMENT ON COLUMN finetuned_models.merge_duration_seconds IS 'Duration of merge operation in seconds (typically 300-900 for 1.5B models)';
COMMENT ON COLUMN finetuned_models.merge_requested_at IS 'Timestamp when merge was requested by user';
COMMENT ON COLUMN finetuned_models.merge_error_message IS 'Error message if merge failed';
