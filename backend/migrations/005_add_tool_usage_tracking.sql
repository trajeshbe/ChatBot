-- Migration: Add Tool Usage Tracking Tables
-- Purpose: Track usage statistics for all tools/services in the system
-- Date: 2025-11-23

-- Tool Usage Statistics Table
-- Records every tool invocation with performance metrics
CREATE TABLE IF NOT EXISTS tool_usage_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Tool identification
    tool_category VARCHAR(50) NOT NULL,  -- e.g., 'document_processing', 'web_scraping', 'rag_service', 'llm_service', 'mcp_tool'
    tool_name VARCHAR(100) NOT NULL,     -- e.g., 'docling', 'playwright', 'cross_encoder_reranker', 'gpt-4'
    tool_version VARCHAR(50),            -- Tool version if applicable

    -- Session/User context
    session_id VARCHAR(255),             -- Associated session
    user_id UUID REFERENCES users(id),   -- Associated user

    -- Operation details
    operation VARCHAR(100),              -- e.g., 'parse_pdf', 'scrape_url', 'rerank_chunks', 'generate_response'
    input_size INTEGER,                  -- Input size (bytes, tokens, chunks, etc.)
    output_size INTEGER,                 -- Output size

    -- Performance metrics
    latency_ms FLOAT NOT NULL,           -- Execution time in milliseconds
    success BOOLEAN NOT NULL DEFAULT TRUE, -- Whether operation succeeded
    error_message TEXT,                  -- Error details if failed

    -- Resource usage
    tokens_used INTEGER,                 -- For LLM tools
    cost_usd DECIMAL(10, 6),            -- Estimated cost in USD (for paid APIs)

    -- Quality metrics (optional)
    quality_score FLOAT,                 -- Quality/confidence score if available
    metadata JSONB,                      -- Additional tool-specific metadata

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for efficient queries
CREATE INDEX idx_tool_usage_category ON tool_usage_stats(tool_category);
CREATE INDEX idx_tool_usage_name ON tool_usage_stats(tool_name);
CREATE INDEX idx_tool_usage_session ON tool_usage_stats(session_id);
CREATE INDEX idx_tool_usage_user ON tool_usage_stats(user_id);
CREATE INDEX idx_tool_usage_created_at ON tool_usage_stats(created_at DESC);
CREATE INDEX idx_tool_usage_success ON tool_usage_stats(success);

-- Composite indexes for common queries
CREATE INDEX idx_tool_usage_category_name_date ON tool_usage_stats(tool_category, tool_name, created_at DESC);
CREATE INDEX idx_tool_usage_session_date ON tool_usage_stats(session_id, created_at DESC);


-- Aggregated Tool Usage Summary (Materialized View - refreshed periodically)
-- Provides quick access to aggregated statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS tool_usage_summary AS
SELECT
    tool_category,
    tool_name,

    -- Usage counts
    COUNT(*) as total_invocations,
    COUNT(*) FILTER (WHERE success = TRUE) as successful_invocations,
    COUNT(*) FILTER (WHERE success = FALSE) as failed_invocations,

    -- Performance metrics
    AVG(latency_ms) as avg_latency_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY latency_ms) as median_latency_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency_ms,
    MIN(latency_ms) as min_latency_ms,
    MAX(latency_ms) as max_latency_ms,

    -- Resource usage
    SUM(tokens_used) as total_tokens_used,
    SUM(cost_usd) as total_cost_usd,

    -- Quality metrics
    AVG(quality_score) as avg_quality_score,

    -- Time range
    MIN(created_at) as first_used,
    MAX(created_at) as last_used,

    -- Success rate
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE success = TRUE) / NULLIF(COUNT(*), 0),
        2
    ) as success_rate_pct

FROM tool_usage_stats
GROUP BY tool_category, tool_name;

-- Index on materialized view
CREATE INDEX idx_tool_summary_category ON tool_usage_summary(tool_category);
CREATE INDEX idx_tool_summary_name ON tool_usage_summary(tool_name);
CREATE INDEX idx_tool_summary_invocations ON tool_usage_summary(total_invocations DESC);

-- Function to refresh the materialized view
CREATE OR REPLACE FUNCTION refresh_tool_usage_summary()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY tool_usage_summary;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE tool_usage_stats IS 'Records every tool/service invocation with performance and quality metrics';
COMMENT ON COLUMN tool_usage_stats.tool_category IS 'High-level category: document_processing, web_scraping, rag_service, llm_service, mcp_tool';
COMMENT ON COLUMN tool_usage_stats.tool_name IS 'Specific tool name: docling, playwright, cross_encoder_reranker, gpt-4, etc.';
COMMENT ON COLUMN tool_usage_stats.operation IS 'Specific operation performed: parse_pdf, scrape_url, rerank_chunks, etc.';
COMMENT ON COLUMN tool_usage_stats.cost_usd IS 'Estimated cost in USD for paid API calls (OpenAI, Anthropic, etc.)';
COMMENT ON MATERIALIZED VIEW tool_usage_summary IS 'Aggregated tool usage statistics for quick dashboard queries';
