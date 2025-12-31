-- =====================================================
-- Usage Metrics Aggregation Script
-- =====================================================
-- Purpose: Aggregate data from conversation_messages and audit_logs
--          into the usage_metrics table for dashboard display
--
-- Usage: Run this script manually or via cron to update metrics
-- Command: psql -U postgres -d ragchatbot -f aggregate_usage_metrics.sql
-- =====================================================

-- Delete existing metrics to avoid duplicates (or use UPSERT)
TRUNCATE usage_metrics;

-- Aggregate daily metrics from conversation_messages and audit_logs
INSERT INTO usage_metrics (
    id,
    user_id,
    date,
    model_id,
    total_queries,
    total_tokens,
    total_cost_usd,
    avg_latency_ms,
    documents_uploaded,
    pages_scraped,
    cache_hits,
    cache_misses,
    created_at
)
WITH daily_queries AS (
    -- Aggregate conversation messages by date and model
    -- Count assistant messages (each represents one query response)
    SELECT
        DATE(cm.created_at) as metric_date,
        cm.model_id,
        COUNT(*) as query_count,  -- Each assistant message = 1 query
        SUM(cm.total_tokens) as total_tokens,
        SUM(cm.cost_usd) as total_cost,
        AVG(cm.latency_ms) as avg_latency
    FROM conversation_messages cm
    WHERE cm.created_at IS NOT NULL
      AND cm.role = 'assistant'  -- Only count assistant messages (they have model_id and metrics)
      AND cm.model_id IS NOT NULL
    GROUP BY DATE(cm.created_at), cm.model_id
),
daily_uploads AS (
    -- Count document uploads by date
    SELECT
        DATE(al.created_at) as metric_date,
        COUNT(*) as upload_count
    FROM audit_logs al
    WHERE al.action = 'UPLOAD'
      AND al.created_at IS NOT NULL
    GROUP BY DATE(al.created_at)
),
daily_scrapes AS (
    -- Count web scraping by date
    SELECT
        DATE(al.created_at) as metric_date,
        COUNT(*) as scrape_count
    FROM audit_logs al
    WHERE al.action = 'SCRAPE'
      AND al.created_at IS NOT NULL
    GROUP BY DATE(al.created_at)
)
SELECT
    gen_random_uuid() as id,
    NULL::uuid as user_id,  -- Set to NULL for aggregate metrics
    dq.metric_date as date,
    dq.model_id,
    COALESCE(dq.query_count, 0) as total_queries,
    COALESCE(dq.total_tokens, 0)::integer as total_tokens,
    COALESCE(dq.total_cost, 0.0) as total_cost_usd,
    COALESCE(dq.avg_latency, 0.0) as avg_latency_ms,
    COALESCE(du.upload_count, 0)::integer as documents_uploaded,
    COALESCE(ds.scrape_count, 0)::integer as pages_scraped,
    0 as cache_hits,    -- TODO: Track from Redis or semantic cache
    0 as cache_misses,  -- TODO: Track from Redis or semantic cache
    NOW() as created_at
FROM daily_queries dq
LEFT JOIN daily_uploads du ON dq.metric_date = du.metric_date
LEFT JOIN daily_scrapes ds ON dq.metric_date = ds.metric_date
ORDER BY dq.metric_date DESC, dq.model_id;

-- Display summary
SELECT
    'Usage Metrics Aggregated' as status,
    COUNT(*) as total_metrics_created,
    MIN(date) as earliest_date,
    MAX(date) as latest_date
FROM usage_metrics;
