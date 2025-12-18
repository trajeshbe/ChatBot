-- Migration: Add dataset_id foreign key to finetuning_jobs
-- Purpose: Link fine-tuning jobs to their training datasets for dataset-linked MinIO paths
-- Date: 2025-12-18

-- Add dataset_id column
ALTER TABLE finetuning_jobs
ADD COLUMN IF NOT EXISTS dataset_id UUID;

-- Add foreign key constraint
ALTER TABLE finetuning_jobs
ADD CONSTRAINT fk_finetuning_jobs_dataset_id
FOREIGN KEY (dataset_id)
REFERENCES finetuning_datasets(id)
ON DELETE SET NULL;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_finetuning_jobs_dataset_id
ON finetuning_jobs(dataset_id);

-- Add comment
COMMENT ON COLUMN finetuning_jobs.dataset_id IS 'Foreign key to finetuning_datasets - links job to training dataset for organizational MinIO paths';
