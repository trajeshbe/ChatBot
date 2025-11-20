# Usage Metrics Dashboard Fix

**Date**: 2025-11-18
**Issue**: Usage Metrics Dashboard showed no data (empty metrics table)
**Status**: ✅ **FIXED**

---

## Problem Summary

### Issue Description
The Admin Dashboard's "Usage Metrics" tab was empty despite having:
- 41 audit log entries
- 74 conversation messages
- Functional frontend UI
- Working backend API endpoint

### Root Cause
The `usage_metrics` table exists but had **zero rows**. There was **no mechanism** to populate it from existing data sources (`conversation_messages` and `audit_logs`).

---

## Investigation Results

### Data Sources Available
```sql
-- 41 audit log entries (40 queries, 1 upload)
SELECT COUNT(*) FROM audit_logs;  -- 41

-- 74 conversation messages (user + assistant)
SELECT COUNT(*) FROM conversation_messages;  -- 74
```

### Usage Metrics Schema
The `usage_metrics` table expects daily aggregated data:
- `date`: Daily timestamp (DATE level aggregation)
- `model_id`: Model used (gpt-4-turbo, qwen2.5:1.5b, etc.)
- `total_queries`: Count of queries per day/model
- `total_tokens`: Sum of tokens used
- `total_cost_usd`: Sum of costs (always 0 for local models)
- `avg_latency_ms`: Average response latency
- `documents_uploaded`: Count from audit_logs (UPLOAD action)
- `pages_scraped`: Count from audit_logs (SCRAPE action)
- `cache_hits` / `cache_misses`: TODO - needs Redis tracking

---

## Solution Implemented

### Created SQL Aggregation Script
**File**: `backend/scripts/aggregate_usage_metrics.sql`

**What it does:**
1. Truncates existing usage_metrics table
2. Aggregates conversation_messages by date and model_id
3. Counts assistant messages (each = 1 query)
4. Sums tokens and costs
5. Averages latency
6. Joins with audit_logs to add document uploads and scraping counts
7. Inserts aggregated daily metrics

### Key SQL Logic
```sql
WITH daily_queries AS (
    SELECT
        DATE(cm.created_at) as metric_date,
        cm.model_id,
        COUNT(*) as query_count,  -- Each assistant message = 1 query
        SUM(cm.total_tokens) as total_tokens,
        SUM(cm.cost_usd) as total_cost,
        AVG(cm.latency_ms) as avg_latency
    FROM conversation_messages cm
    WHERE cm.role = 'assistant'  -- Only count assistant messages
      AND cm.model_id IS NOT NULL
    GROUP BY DATE(cm.created_at), cm.model_id
),
daily_uploads AS (
    SELECT DATE(al.created_at) as metric_date, COUNT(*) as upload_count
    FROM audit_logs al
    WHERE al.action = 'UPLOAD'
    GROUP BY DATE(al.created_at)
),
daily_scrapes AS (
    SELECT DATE(al.created_at) as metric_date, COUNT(*) as scrape_count
    FROM audit_logs al
    WHERE al.action = 'SCRAPE'
    GROUP BY DATE(al.created_at)
)
SELECT ... FROM daily_queries
LEFT JOIN daily_uploads ...
LEFT JOIN daily_scrapes ...
```

---

## Results After Fix

### Aggregated Metrics Created
```sql
SELECT date, model_id, total_queries, total_tokens, documents_uploaded
FROM usage_metrics ORDER BY date DESC;
```

| Date       | Model       | Queries | Tokens | Uploads |
|------------|-------------|---------|--------|---------|
| 2025-11-18 | gpt-4-turbo | 2       | 2,633  | 0       |
| 2025-11-18 | llama3.2:3b | 4       | 2,868  | 0       |
| 2025-11-18 | qwen2.5:1.5b| 9       | 3,478  | 0       |
| 2025-11-17 | gpt-4-turbo | 5       | 8,465  | 0       |
| 2025-11-16 | gpt-4-turbo | 9       | 23,727 | 1       |
| 2025-11-16 | qwen-1.5b-cpu| 8      | 10,134 | 1       |

**Total**: 6 daily metrics records spanning Nov 16-18, 2025

### Dashboard Now Shows
- **Summary Cards**: Total Queries (37), Total Tokens (51,305), Total Cost ($0.00), Avg Latency
- **Daily Table**: Breakdown by date and model with all metrics

---

## Running the Aggregation

### Manual Execution
```bash
# From host machine
docker cp backend/scripts/aggregate_usage_metrics.sql rag-postgres:/tmp/
docker-compose exec postgres psql -U postgres -d ragchatbot -f /tmp/aggregate_usage_metrics.sql
```

### Expected Output
```
TRUNCATE TABLE
INSERT 0 6
          status          | total_metrics_created | earliest_date | latest_date
--------------------------+-----------------------+---------------+--------------
 Usage Metrics Aggregated |                     6 | 2025-11-16    | 2025-11-18
```

---

## Future Enhancements

### Short Term
1. ✅ SQL aggregation script created and tested
2. 🔄 **TODO**: Add cron job or scheduled task to run daily
3. 🔄 **TODO**: Add Redis cache hit/miss tracking

### Medium Term
1. 🔄 **TODO**: Create `/api/v1/admin/refresh-metrics` endpoint to trigger aggregation
2. 🔄 **TODO**: Implement incremental aggregation (only new data since last run)
3. 🔄 **TODO**: Add user-level breakdowns (currently NULL for user_id)

### Long Term
1. 🔮 Real-time metrics updates (populate on each query)
2. 🔮 Cost tracking for OpenAI/Anthropic API calls
3. 🔮 Advanced analytics (trends, forecasts, anomaly detection)

---

## Maintenance

### When to Re-run Aggregation
- After significant usage activity
- Before checking metrics in admin dashboard
- After testing new features with multiple queries

### Automation Options
1. **Cron Job**: Run script daily at midnight
   ```bash
   0 0 * * * docker-compose exec postgres psql -U postgres -d ragchatbot -f /tmp/aggregate_usage_metrics.sql
   ```

2. **Backend Endpoint**: Add API endpoint to trigger on-demand
   ```python
   @app.post("/api/v1/admin/refresh-metrics")
   async def refresh_metrics():
       # Execute SQL script
       # Return summary
   ```

3. **Background Task**: Use Prefect/Celery to run daily

---

## Files Created/Modified

### Created
- **`backend/scripts/aggregate_usage_metrics.sql`** - Main aggregation script

### No Changes Required
- Frontend (`admin.tsx`) - Already has UI for metrics
- Backend endpoint (`/api/v1/admin/usage-metrics`) - Already functional
- Database schema - Table already exists

---

## Verification

```bash
# Check metrics count
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT COUNT(*) FROM usage_metrics;"

# View latest metrics
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT * FROM usage_metrics ORDER BY date DESC LIMIT 10;"

# Test admin dashboard
open http://localhost:3001/admin
# Navigate to "Usage Metrics" tab
```

---

## Conclusion

The Usage Metrics Dashboard is now **fully functional** with historical data populated. The dashboard provides valuable insights into:
- ✅ Query volume by model
- ✅ Token usage tracking
- ✅ Performance metrics (latency)
- ✅ Document upload tracking

**Decision**: **Keep the dashboard** - it adds significant value for monitoring usage and costs.

---

**Generated**: 2025-11-18
**Status**: ✅ Implemented and tested
**Recommendation**: Set up automated daily aggregation
