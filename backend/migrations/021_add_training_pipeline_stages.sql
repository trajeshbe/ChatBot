-- Add training pipeline stage tracking to finetuning_jobs
-- Migration: 021_add_training_pipeline_stages.sql
-- Date: 2025-12-19

-- Add training_stage column to track current pipeline stage
ALTER TABLE finetuning_jobs
ADD COLUMN IF NOT EXISTS training_stage VARCHAR(50) DEFAULT 'queued';

-- Add stage_details column to store stage-specific metadata (JSON)
ALTER TABLE finetuning_jobs
ADD COLUMN IF NOT EXISTS stage_details JSONB DEFAULT '{}'::jsonb;

-- Add stage_started_at to track when current stage began
ALTER TABLE finetuning_jobs
ADD COLUMN IF NOT EXISTS stage_started_at TIMESTAMP WITH TIME ZONE;

-- Add stage_completed_at to track when current stage finished
ALTER TABLE finetuning_jobs
ADD COLUMN IF NOT EXISTS stage_completed_at TIMESTAMP WITH TIME ZONE;

-- Add index on training_stage for filtering
CREATE INDEX IF NOT EXISTS idx_finetuning_jobs_training_stage
ON finetuning_jobs(training_stage);

-- Create enum-like constraint for valid training stages
ALTER TABLE finetuning_jobs
ADD CONSTRAINT check_valid_training_stage
CHECK (training_stage IN (
    'queued',           -- Job queued, waiting for GPU
    'setup',            -- Container started, initializing
    'tokenizer_load',   -- Loading tokenizer
    'model_download',   -- Downloading model from HuggingFace
    'model_load',       -- Loading model into GPU memory
    'dataset_prep',     -- Preparing and tokenizing dataset
    'training',         -- Actively training
    'checkpoint_save',  -- Saving and uploading checkpoints
    'completed',        -- Training finished successfully
    'failed'            -- Training failed at some stage
));

-- Comment on columns
COMMENT ON COLUMN finetuning_jobs.training_stage IS 'Current stage in the training pipeline (queued, setup, tokenizer_load, model_download, model_load, dataset_prep, training, checkpoint_save, completed, failed)';
COMMENT ON COLUMN finetuning_jobs.stage_details IS 'Stage-specific metadata (e.g., download progress, current file, substep info)';
COMMENT ON COLUMN finetuning_jobs.stage_started_at IS 'Timestamp when current stage started';
COMMENT ON COLUMN finetuning_jobs.stage_completed_at IS 'Timestamp when current stage completed';

-- Update existing jobs to have default stage
UPDATE finetuning_jobs
SET training_stage = CASE
    WHEN status = 'queued' THEN 'queued'
    WHEN status = 'running' THEN 'training'
    WHEN status = 'completed' THEN 'completed'
    WHEN status = 'failed' THEN 'failed'
    ELSE 'queued'
END
WHERE training_stage IS NULL;
