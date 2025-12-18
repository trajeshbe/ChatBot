-- Migration 020: Add missing fields to finetuning_jobs for Celery integration
-- Date: 2025-12-17
-- Description: Add queued_at and learning_rate fields for better tracking

-- Add queued_at timestamp to track when job was submitted to queue
ALTER TABLE finetuning_jobs
ADD COLUMN IF NOT EXISTS queued_at TIMESTAMP WITH TIME ZONE;

-- Add learning_rate to track current learning rate during training
ALTER TABLE finetuning_jobs
ADD COLUMN IF NOT EXISTS learning_rate FLOAT;

-- Add comment for queued_at
COMMENT ON COLUMN finetuning_jobs.queued_at IS 'Timestamp when job was submitted to Celery queue';

-- Add comment for learning_rate
COMMENT ON COLUMN finetuning_jobs.learning_rate IS 'Current learning rate during training';
