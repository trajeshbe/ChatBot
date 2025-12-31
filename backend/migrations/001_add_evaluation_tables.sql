-- Migration: Add Evaluation System Tables
-- Description: Creates tables for configurable RAG evaluation system
-- Date: 2025-11-14
-- Version: 001

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Evaluation Configurations Table
CREATE TABLE IF NOT EXISTS evaluation_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,

    -- Toggle switches for evaluation methods
    enable_ragas BOOLEAN DEFAULT FALSE,
    enable_llm_as_judge BOOLEAN DEFAULT FALSE,
    enable_deepeval BOOLEAN DEFAULT FALSE,
    enable_semantic_similarity BOOLEAN DEFAULT FALSE,
    enable_bertscore BOOLEAN DEFAULT FALSE,
    enable_citation_accuracy BOOLEAN DEFAULT TRUE,
    enable_toxicity BOOLEAN DEFAULT TRUE,
    enable_bias_detection BOOLEAN DEFAULT TRUE,
    enable_hallucination BOOLEAN DEFAULT TRUE,
    enable_answer_relevancy BOOLEAN DEFAULT TRUE,
    enable_context_precision BOOLEAN DEFAULT FALSE,
    enable_context_recall BOOLEAN DEFAULT FALSE,
    enable_faithfulness BOOLEAN DEFAULT TRUE,

    -- Configuration parameters
    llm_judge_model VARCHAR(100) DEFAULT 'gpt-4-turbo-preview',
    use_cache BOOLEAN DEFAULT TRUE,
    async_evaluation BOOLEAN DEFAULT TRUE,
    batch_size INTEGER DEFAULT 10,
    min_score_threshold FLOAT DEFAULT 0.7,
    cache_ttl_seconds INTEGER DEFAULT 3600,

    -- Auto-evaluation settings
    auto_evaluate BOOLEAN DEFAULT FALSE,
    evaluation_sampling_rate FLOAT DEFAULT 1.0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_info JSONB
);

-- Indexes for evaluation_configs
CREATE INDEX IF NOT EXISTS idx_evaluation_configs_user_id ON evaluation_configs(user_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_configs_session_id ON evaluation_configs(session_id);

-- Evaluation Results Table
CREATE TABLE IF NOT EXISTS evaluation_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    message_id UUID REFERENCES conversation_messages(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Query and response data
    query TEXT NOT NULL,
    response TEXT NOT NULL,
    num_contexts INTEGER,

    -- Evaluation scores (JSON for flexibility)
    scores JSONB NOT NULL,
    overall_score FLOAT,

    -- Performance metrics
    evaluation_time_ms FLOAT,
    enabled_methods JSONB,

    -- Metadata and errors
    meta_info JSONB,
    errors JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for evaluation_results
CREATE INDEX IF NOT EXISTS idx_evaluation_results_session_id ON evaluation_results(session_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_results_message_id ON evaluation_results(message_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_results_overall_score ON evaluation_results(overall_score);
CREATE INDEX IF NOT EXISTS idx_evaluation_results_created_at ON evaluation_results(created_at);

-- Evaluation Cache Table
CREATE TABLE IF NOT EXISTS evaluation_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    result JSONB NOT NULL,
    ttl_seconds INTEGER DEFAULT 3600,
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for evaluation_cache
CREATE INDEX IF NOT EXISTS idx_evaluation_cache_key ON evaluation_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_evaluation_cache_created_at ON evaluation_cache(created_at);

-- Human Feedback Table
CREATE TABLE IF NOT EXISTS human_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    message_id UUID REFERENCES conversation_messages(id) ON DELETE CASCADE,
    evaluation_id UUID REFERENCES evaluation_results(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Feedback data
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    thumbs_up BOOLEAN,
    feedback_text TEXT,

    -- Specific criteria ratings
    accuracy_rating INTEGER CHECK (accuracy_rating >= 1 AND accuracy_rating <= 5),
    helpfulness_rating INTEGER CHECK (helpfulness_rating >= 1 AND helpfulness_rating <= 5),
    clarity_rating INTEGER CHECK (clarity_rating >= 1 AND clarity_rating <= 5),

    -- Issues flagged
    has_hallucination BOOLEAN DEFAULT FALSE,
    has_bias BOOLEAN DEFAULT FALSE,
    has_toxicity BOOLEAN DEFAULT FALSE,
    is_irrelevant BOOLEAN DEFAULT FALSE,

    -- Metadata
    feedback_type VARCHAR(50),
    ip_address VARCHAR(45),
    user_agent VARCHAR(512),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_info JSONB
);

-- Indexes for human_feedback
CREATE INDEX IF NOT EXISTS idx_human_feedback_session_id ON human_feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_human_feedback_message_id ON human_feedback(message_id);
CREATE INDEX IF NOT EXISTS idx_human_feedback_evaluation_id ON human_feedback(evaluation_id);
CREATE INDEX IF NOT EXISTS idx_human_feedback_created_at ON human_feedback(created_at);

-- Evaluation Benchmarks Table
CREATE TABLE IF NOT EXISTS evaluation_benchmarks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Benchmark data
    query TEXT NOT NULL,
    ground_truth_answer TEXT NOT NULL,
    context_chunks JSONB NOT NULL,

    -- Expected scores (for validation)
    expected_scores JSONB,

    -- Benchmark metadata
    dataset_name VARCHAR(100),
    difficulty VARCHAR(50),
    category VARCHAR(100),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_info JSONB
);

-- Indexes for evaluation_benchmarks
CREATE INDEX IF NOT EXISTS idx_evaluation_benchmarks_dataset_name ON evaluation_benchmarks(dataset_name);
CREATE INDEX IF NOT EXISTS idx_evaluation_benchmarks_difficulty ON evaluation_benchmarks(difficulty);
CREATE INDEX IF NOT EXISTS idx_evaluation_benchmarks_category ON evaluation_benchmarks(category);

-- Create updated_at trigger for evaluation_configs
CREATE OR REPLACE FUNCTION update_evaluation_configs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER evaluation_configs_updated_at
BEFORE UPDATE ON evaluation_configs
FOR EACH ROW
EXECUTE FUNCTION update_evaluation_configs_updated_at();

-- Create trigger to update last_accessed for evaluation_cache
CREATE OR REPLACE FUNCTION update_evaluation_cache_last_accessed()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_accessed = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER evaluation_cache_last_accessed
BEFORE UPDATE ON evaluation_cache
FOR EACH ROW
EXECUTE FUNCTION update_evaluation_cache_last_accessed();

-- Cleanup old cache entries (optional cleanup function)
CREATE OR REPLACE FUNCTION cleanup_evaluation_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM evaluation_cache
    WHERE created_at < NOW() - INTERVAL '1 hour' * (ttl_seconds / 3600);
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE evaluation_configs IS 'User-specific evaluation configuration with toggleable metrics';
COMMENT ON TABLE evaluation_results IS 'Stores comprehensive evaluation results for RAG responses';
COMMENT ON TABLE evaluation_cache IS 'Cache for evaluation results to improve performance';
COMMENT ON TABLE human_feedback IS 'Human feedback on RAG responses for continuous improvement';
COMMENT ON TABLE evaluation_benchmarks IS 'Benchmark datasets for evaluation metrics validation';
