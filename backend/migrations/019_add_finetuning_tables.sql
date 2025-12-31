-- Migration: 019_add_finetuning_tables.sql
-- Description: Add comprehensive fine-tuning tables for PEFT, SFT, RLHF, and RLFG support
-- Date: 2025-12-14
-- Reference: docs/features/MODEL_FINETUNING_IMPLEMENTATION_PLAN.md

-- ============================================================================
-- Table 1: finetuning_datasets
-- Stores uploaded datasets for fine-tuning
-- ============================================================================

CREATE TABLE IF NOT EXISTS finetuning_datasets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Dataset metadata
    name VARCHAR(255) NOT NULL,
    description TEXT,
    uploaded_by UUID REFERENCES users(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- File info
    filename VARCHAR(255) NOT NULL,
    file_size BIGINT,
    file_type VARCHAR(50),  -- "csv", "json", "jsonl", "parquet"
    minio_path VARCHAR(512),

    -- Dataset statistics
    num_samples INT,
    num_train_samples INT,
    num_val_samples INT,

    -- Schema/format
    format_type VARCHAR(100),  -- "qa", "classification", "instruction", "preference", "summarization"
    columns JSONB,
    -- Example for QA:
    -- {
    --   "question_column": "question",
    --   "answer_column": "answer"
    -- }

    -- Validation
    is_valid BOOLEAN DEFAULT FALSE,
    validation_errors JSONB,

    -- Preview
    sample_rows JSONB,

    -- Processing status
    preprocessing_status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed
    preprocessed_path VARCHAR(512),

    -- Project association
    project_id UUID REFERENCES projects(id),

    -- Indexes
    CONSTRAINT finetuning_datasets_name_project_unique UNIQUE (name, project_id)
);

CREATE INDEX idx_finetuning_datasets_uploaded_by ON finetuning_datasets(uploaded_by);
CREATE INDEX idx_finetuning_datasets_project ON finetuning_datasets(project_id);
CREATE INDEX idx_finetuning_datasets_format_type ON finetuning_datasets(format_type);

COMMENT ON TABLE finetuning_datasets IS 'Stores uploaded datasets for model fine-tuning';
COMMENT ON COLUMN finetuning_datasets.format_type IS 'Dataset format: qa, classification, instruction, preference, summarization';
COMMENT ON COLUMN finetuning_datasets.columns IS 'JSON mapping of dataset columns to expected fields';
COMMENT ON COLUMN finetuning_datasets.sample_rows IS 'Preview of first 5 rows for validation';

-- ============================================================================
-- Table 2: finetuning_jobs
-- Stores fine-tuning job configurations and status
-- ============================================================================

CREATE TABLE IF NOT EXISTS finetuning_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Job metadata
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Model configuration
    base_model VARCHAR(255) NOT NULL,  -- e.g., "Qwen/Qwen2.5-7B-Instruct"
    quantization VARCHAR(50),  -- "4bit", "8bit", "none"

    -- Fine-tuning configuration
    finetuning_method VARCHAR(50) NOT NULL,  -- "peft", "sft", "rlhf-ppo", "rlhf-grpo"
    training_objective VARCHAR(100) NOT NULL,  -- "qa", "classification", "summarization", "instruction"

    -- Dataset
    dataset_id UUID REFERENCES finetuning_datasets(id),
    train_split FLOAT DEFAULT 0.8,

    -- Hyperparameters (JSONB for flexibility)
    hyperparameters JSONB,
    -- Example for PEFT:
    -- {
    --   "learning_rate": 2e-4,
    --   "num_epochs": 3,
    --   "batch_size": 4,
    --   "gradient_accumulation_steps": 4,
    --   "lora_r": 16,
    --   "lora_alpha": 32,
    --   "lora_dropout": 0.05,
    --   "target_modules": ["q_proj", "v_proj"],
    --   "warmup_steps": 100,
    --   "max_seq_length": 2048
    -- }

    -- Training status
    status VARCHAR(50) DEFAULT 'pending',  -- pending, queued, running, completed, failed, cancelled
    progress FLOAT DEFAULT 0.0,  -- 0.0 to 1.0

    -- Training metrics (updated during training)
    current_epoch INT,
    current_step INT,
    total_steps INT,
    train_loss FLOAT,
    eval_loss FLOAT,

    -- Results
    final_model_name VARCHAR(255),
    mlflow_run_id VARCHAR(255),
    minio_checkpoint_path VARCHAR(512),

    -- Training logs
    logs TEXT,
    error_message TEXT,

    -- Resource usage
    gpu_type VARCHAR(100),
    gpu_count INT DEFAULT 1,
    training_time_seconds INT,
    training_start_time TIMESTAMP WITH TIME ZONE,
    training_end_time TIMESTAMP WITH TIME ZONE,

    -- Project association
    project_id UUID REFERENCES projects(id),
    department VARCHAR(255),
    team VARCHAR(255),

    -- Celery task tracking
    celery_task_id VARCHAR(255),

    CONSTRAINT finetuning_jobs_progress_range CHECK (progress >= 0.0 AND progress <= 1.0)
);

CREATE INDEX idx_finetuning_jobs_status ON finetuning_jobs(status);
CREATE INDEX idx_finetuning_jobs_created_by ON finetuning_jobs(created_by);
CREATE INDEX idx_finetuning_jobs_project ON finetuning_jobs(project_id);
CREATE INDEX idx_finetuning_jobs_dataset ON finetuning_jobs(dataset_id);
CREATE INDEX idx_finetuning_jobs_method ON finetuning_jobs(finetuning_method);
CREATE INDEX idx_finetuning_jobs_created_at ON finetuning_jobs(created_at DESC);

COMMENT ON TABLE finetuning_jobs IS 'Fine-tuning job configurations and execution status';
COMMENT ON COLUMN finetuning_jobs.finetuning_method IS 'Method: peft (LoRA/QLoRA), sft, rlhf-ppo, rlhf-grpo';
COMMENT ON COLUMN finetuning_jobs.training_objective IS 'Training objective: qa, classification, summarization, instruction';
COMMENT ON COLUMN finetuning_jobs.hyperparameters IS 'JSON object containing all hyperparameters for the training run';

-- ============================================================================
-- Table 3: finetuned_models
-- Model registry for fine-tuned models
-- ============================================================================

CREATE TABLE IF NOT EXISTS finetuned_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Model metadata
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) DEFAULT 'v1.0.0',
    description TEXT,

    -- Source job
    job_id UUID REFERENCES finetuning_jobs(id),
    base_model VARCHAR(255) NOT NULL,
    finetuning_method VARCHAR(50),

    -- Model artifacts
    mlflow_model_uri VARCHAR(512),
    mlflow_run_id VARCHAR(255),
    minio_checkpoint_path VARCHAR(512),
    adapter_config JSONB,
    -- Example adapter config:
    -- {
    --   "peft_type": "LORA",
    --   "r": 16,
    --   "lora_alpha": 32,
    --   "target_modules": ["q_proj", "v_proj"],
    --   "modules_to_save": null
    -- }

    -- Evaluation metrics
    eval_metrics JSONB,
    -- Example:
    -- {
    --   "accuracy": 0.92,
    --   "perplexity": 3.45,
    --   "rouge_l": 0.67,
    --   "f1_score": 0.89,
    --   "bleu": 0.72
    -- }

    -- Deployment
    status VARCHAR(50) DEFAULT 'registered',  -- registered, deployed, archived, deprecated
    deployment_url VARCHAR(512),
    ollama_model_name VARCHAR(255),
    vllm_model_name VARCHAR(255),

    -- Usage tracking
    total_inferences INT DEFAULT 0,
    avg_latency_ms FLOAT,
    last_inference_at TIMESTAMP WITH TIME ZONE,

    -- Versioning and lineage
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    parent_model_id UUID REFERENCES finetuned_models(id),  -- For model lineage

    -- Deprecation
    deprecated_at TIMESTAMP WITH TIME ZONE,
    deprecated_by UUID REFERENCES users(id),
    deprecation_reason TEXT,

    -- Project association
    project_id UUID REFERENCES projects(id),

    -- Model tags for categorization
    tags JSONB,  -- e.g., ["production", "customer-support", "v2"]

    CONSTRAINT finetuned_models_name_version_unique UNIQUE (name, version)
);

CREATE INDEX idx_finetuned_models_status ON finetuned_models(status);
CREATE INDEX idx_finetuned_models_job ON finetuned_models(job_id);
CREATE INDEX idx_finetuned_models_project ON finetuned_models(project_id);
CREATE INDEX idx_finetuned_models_created_at ON finetuned_models(created_at DESC);
CREATE INDEX idx_finetuned_models_ollama_name ON finetuned_models(ollama_model_name);
CREATE INDEX idx_finetuned_models_tags ON finetuned_models USING GIN (tags);

COMMENT ON TABLE finetuned_models IS 'Registry of fine-tuned models with deployment and usage tracking';
COMMENT ON COLUMN finetuned_models.adapter_config IS 'PEFT adapter configuration (LoRA parameters, etc.)';
COMMENT ON COLUMN finetuned_models.eval_metrics IS 'Evaluation metrics from test set';
COMMENT ON COLUMN finetuned_models.parent_model_id IS 'Reference to parent model for tracking model lineage';

-- ============================================================================
-- Table 4: training_metrics
-- Time-series data for training progress monitoring
-- ============================================================================

CREATE TABLE IF NOT EXISTS training_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES finetuning_jobs(id) ON DELETE CASCADE,

    -- Timestamp
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Training progress
    epoch INT,
    step INT,

    -- Loss metrics
    train_loss FLOAT,
    eval_loss FLOAT,
    gradient_norm FLOAT,

    -- Learning metrics
    learning_rate FLOAT,

    -- Resource metrics
    gpu_utilization FLOAT,  -- 0.0 to 1.0
    gpu_memory_allocated BIGINT,  -- bytes
    gpu_memory_reserved BIGINT,  -- bytes
    gpu_temperature FLOAT,  -- celsius

    -- Performance metrics
    samples_per_second FLOAT,
    tokens_per_second FLOAT,
    batch_processing_time_ms FLOAT,

    -- Additional metrics (flexible)
    custom_metrics JSONB,
    -- Example:
    -- {
    --   "kl_divergence": 0.05,
    --   "reward": 0.85,
    --   "policy_loss": 0.12,
    --   "value_loss": 0.08
    -- }

    CONSTRAINT training_metrics_gpu_utilization_range CHECK (gpu_utilization >= 0.0 AND gpu_utilization <= 1.0)
);

CREATE INDEX idx_training_metrics_job_timestamp ON training_metrics(job_id, timestamp DESC);
CREATE INDEX idx_training_metrics_job_step ON training_metrics(job_id, step);

COMMENT ON TABLE training_metrics IS 'Time-series metrics collected during model training';
COMMENT ON COLUMN training_metrics.custom_metrics IS 'Flexible JSON field for method-specific metrics (e.g., RLHF rewards)';

-- ============================================================================
-- Grant permissions
-- ============================================================================

-- Grant permissions to application user (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ragchatbot_app') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON finetuning_datasets TO ragchatbot_app;
        GRANT SELECT, INSERT, UPDATE, DELETE ON finetuning_jobs TO ragchatbot_app;
        GRANT SELECT, INSERT, UPDATE, DELETE ON finetuned_models TO ragchatbot_app;
        GRANT SELECT, INSERT, UPDATE, DELETE ON training_metrics TO ragchatbot_app;
    END IF;
END
$$;

-- ============================================================================
-- Helper functions for fine-tuning
-- ============================================================================

-- Function to update job progress automatically
CREATE OR REPLACE FUNCTION update_finetuning_job_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER finetuning_jobs_update_timestamp
    BEFORE UPDATE ON finetuning_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_finetuning_job_timestamp();

-- Function to calculate training duration
CREATE OR REPLACE FUNCTION calculate_training_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'running' AND OLD.status = 'pending' THEN
        NEW.training_start_time = NOW();
    ELSIF NEW.status IN ('completed', 'failed', 'cancelled') AND OLD.status = 'running' THEN
        NEW.training_end_time = NOW();
        NEW.training_time_seconds = EXTRACT(EPOCH FROM (NEW.training_end_time - NEW.training_start_time));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER finetuning_jobs_calculate_duration
    BEFORE UPDATE ON finetuning_jobs
    FOR EACH ROW
    EXECUTE FUNCTION calculate_training_duration();

-- Function to auto-increment model inferences
CREATE OR REPLACE FUNCTION increment_model_inference_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE finetuned_models
    SET
        total_inferences = total_inferences + 1,
        last_inference_at = NOW()
    WHERE ollama_model_name = NEW.model_used
       OR vllm_model_name = NEW.model_used;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to track model usage (assuming messages table has model_used column)
CREATE TRIGGER track_finetuned_model_usage
    AFTER INSERT ON messages
    FOR EACH ROW
    WHEN (NEW.model_used IS NOT NULL)
    EXECUTE FUNCTION increment_model_inference_count();

-- ============================================================================
-- Insert default data for testing
-- ============================================================================

-- Insert sample base models configuration (for reference)
COMMENT ON TABLE finetuning_jobs IS 'Supported base models: Qwen/Qwen2.5-7B-Instruct, meta-llama/Llama-2-7b-hf, mistralai/Mistral-7B-Instruct-v0.2';

-- ============================================================================
-- Migration Complete
-- ============================================================================

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE 'Migration 019: Fine-tuning tables created successfully';
    RAISE NOTICE 'Tables created: finetuning_datasets, finetuning_jobs, finetuned_models, training_metrics';
    RAISE NOTICE 'Triggers created: update_timestamp, calculate_duration, track_model_usage';
END
$$;
