# SQL Audit Queries - Reference Guide

**Purpose**: Useful SQL queries for analyzing audit logs in PostgreSQL
**Table**: `audit_logs`
**Database**: `ragchatbot`

---

## 🚀 Quick Start

### Access Database

```bash
# Via docker-compose
docker-compose exec postgres psql -U postgres -d ragchatbot

# Direct connection (if postgres port is exposed)
psql -h localhost -p 5433 -U postgres -d ragchatbot
```

---

## 📊 Basic Queries

### 1. Recent Audit Activity

```sql
-- View last 20 audit events
SELECT
    TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as time,
    action,
    status_code,
    ROUND(latency_ms::numeric, 2) as latency_ms,
    ip_address
FROM audit_logs
ORDER BY created_at DESC
LIMIT 20;
```

### 2. Activity Count by Action Type

```sql
-- Count events by action type
SELECT
    action,
    COUNT(*) as count,
    ROUND(AVG(latency_ms)::numeric, 2) as avg_latency
FROM audit_logs
GROUP BY action
ORDER BY count DESC;
```

### 3. Hourly Activity Pattern

```sql
-- Activity by hour of day
SELECT
    EXTRACT(HOUR FROM created_at) as hour,
    COUNT(*) as events,
    ROUND(AVG(latency_ms)::numeric, 2) as avg_latency
FROM audit_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour;
```

---

## 🔍 User Activity Analysis

### 4. Activity by User

```sql
-- Top active users
SELECT
    user_id,
    COUNT(*) as total_actions,
    COUNT(DISTINCT DATE(created_at)) as active_days,
    MIN(created_at) as first_seen,
    MAX(created_at) as last_seen
FROM audit_logs
WHERE user_id IS NOT NULL
GROUP BY user_id
ORDER BY total_actions DESC
LIMIT 10;
```

### 5. User Activity Timeline

```sql
-- Detailed timeline for a specific user
SELECT
    TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as time,
    action,
    status_code,
    ROUND(latency_ms::numeric, 2) as latency,
    ip_address,
    user_agent
FROM audit_logs
WHERE user_id = '<user-uuid>'
ORDER BY created_at DESC
LIMIT 50;
```

### 6. User Behavior Summary

```sql
-- Summary of user actions
SELECT
    action,
    COUNT(*) as count,
    COUNT(*) FILTER (WHERE status_code < 400) as success,
    COUNT(*) FILTER (WHERE status_code >= 400) as failed,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status_code < 400) / COUNT(*)::numeric, 2) as success_rate
FROM audit_logs
WHERE user_id = '<user-uuid>'
  AND created_at > NOW() - INTERVAL '30 days'
GROUP BY action
ORDER BY count DESC;
```

---

## 🚨 Security & Error Analysis

### 7. Failed Requests

```sql
-- All failed requests (4xx, 5xx)
SELECT
    TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as time,
    action,
    status_code,
    error_message,
    ip_address,
    user_id
FROM audit_logs
WHERE status_code >= 400
ORDER BY created_at DESC
LIMIT 50;
```

### 8. Failed Login Attempts

```sql
-- Failed login attempts by IP
SELECT
    ip_address,
    COUNT(*) as attempts,
    MIN(created_at) as first_attempt,
    MAX(created_at) as last_attempt,
    ARRAY_AGG(DISTINCT user_agent) as user_agents
FROM audit_logs
WHERE action = 'LOGIN_FAILED'
  AND created_at > NOW() - INTERVAL '24 hours'
GROUP BY ip_address
ORDER BY attempts DESC;
```

### 9. Unauthorized Access Attempts

```sql
-- Unauthorized access by IP and endpoint
SELECT
    ip_address,
    description,
    COUNT(*) as attempts,
    MAX(created_at) as last_attempt
FROM audit_logs
WHERE action IN ('UNAUTHORIZED_ACCESS', 'PERMISSION_DENIED')
  AND created_at > NOW() - INTERVAL '7 days'
GROUP BY ip_address, description
ORDER BY attempts DESC;
```

### 10. Rate Limit Violations

```sql
-- Rate limit exceeded events
SELECT
    ip_address,
    COUNT(*) as violations,
    MIN(created_at) as first_violation,
    MAX(created_at) as last_violation
FROM audit_logs
WHERE action = 'RATE_LIMIT_EXCEEDED'
  AND created_at > NOW() - INTERVAL '1 hour'
GROUP BY ip_address
ORDER BY violations DESC;
```

---

## ⚡ Performance Analysis

### 11. Slow Requests (P95, P99)

```sql
-- Performance percentiles by endpoint
SELECT
    action,
    COUNT(*) as requests,
    ROUND(AVG(latency_ms)::numeric, 2) as avg_latency,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY latency_ms)::numeric, 2) as p50_latency,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms)::numeric, 2) as p95_latency,
    ROUND(PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY latency_ms)::numeric, 2) as p99_latency,
    ROUND(MAX(latency_ms)::numeric, 2) as max_latency
FROM audit_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY action
ORDER BY p95_latency DESC;
```

### 12. Requests Taking > 1 Second

```sql
-- Find slow requests
SELECT
    TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as time,
    action,
    ROUND(latency_ms::numeric, 2) as latency_ms,
    status_code,
    ip_address
FROM audit_logs
WHERE latency_ms > 1000
ORDER BY latency_ms DESC
LIMIT 20;
```

### 13. Average Latency Trend Over Time

```sql
-- Hourly latency trend
SELECT
    DATE_TRUNC('hour', created_at) as hour,
    action,
    COUNT(*) as requests,
    ROUND(AVG(latency_ms)::numeric, 2) as avg_latency
FROM audit_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY hour, action
ORDER BY hour DESC, action;
```

---

## 📈 Traffic Analysis

### 14. Requests Per Hour

```sql
-- Traffic by hour
SELECT
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as requests,
    COUNT(DISTINCT ip_address) as unique_ips,
    COUNT(DISTINCT user_id) as unique_users
FROM audit_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour DESC;
```

### 15. Top IP Addresses

```sql
-- Most active IPs
SELECT
    ip_address,
    COUNT(*) as requests,
    COUNT(DISTINCT action) as unique_actions,
    MIN(created_at) as first_seen,
    MAX(created_at) as last_seen
FROM audit_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY ip_address
ORDER BY requests DESC
LIMIT 20;
```

### 16. User Agent Analysis

```sql
-- User agents breakdown
SELECT
    user_agent,
    COUNT(*) as requests,
    COUNT(DISTINCT ip_address) as unique_ips
FROM audit_logs
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY user_agent
ORDER BY requests DESC;
```

---

## 🎯 Business Intelligence

### 17. Daily Active Users (DAU)

```sql
-- Daily active users over last 30 days
SELECT
    DATE(created_at) as date,
    COUNT(DISTINCT user_id) as daily_active_users,
    COUNT(*) as total_actions
FROM audit_logs
WHERE created_at > NOW() - INTERVAL '30 days'
  AND user_id IS NOT NULL
GROUP BY date
ORDER BY date DESC;
```

### 18. Feature Usage

```sql
-- Most used features/endpoints
SELECT
    action,
    COUNT(*) as usage_count,
    COUNT(DISTINCT user_id) as unique_users,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER()::numeric, 2) as percentage
FROM audit_logs
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY action
ORDER BY usage_count DESC;
```

### 19. Session Duration

```sql
-- Average session duration by session
SELECT
    session_id,
    MIN(created_at) as session_start,
    MAX(created_at) as session_end,
    EXTRACT(EPOCH FROM (MAX(created_at) - MIN(created_at)))/60 as duration_minutes,
    COUNT(*) as actions
FROM audit_logs
WHERE session_id IS NOT NULL
  AND created_at > NOW() - INTERVAL '7 days'
GROUP BY session_id
HAVING COUNT(*) > 1
ORDER BY duration_minutes DESC
LIMIT 20;
```

---

## 🔐 Compliance & GDPR

### 20. User Data Access Report (GDPR)

```sql
-- Complete user activity report
SELECT
    TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as timestamp,
    action,
    resource_type,
    resource_id,
    status_code,
    ip_address,
    user_agent
FROM audit_logs
WHERE user_id = '<user-uuid>'
ORDER BY created_at DESC;
```

### 21. Data Export Activity

```sql
-- Track data export/download events
SELECT
    TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as time,
    user_id,
    action,
    resource_type,
    ip_address
FROM audit_logs
WHERE action IN ('EXPORT', 'DOWNLOAD', 'EXPORT_ALL')
  AND created_at > NOW() - INTERVAL '90 days'
ORDER BY created_at DESC;
```

### 22. Admin Actions Log

```sql
-- All admin-level actions
SELECT
    TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as time,
    user_id,
    action,
    description,
    status_code
FROM audit_logs
WHERE action IN (
    'USER_CREATE', 'USER_UPDATE', 'USER_DELETE',
    'ROLE_ASSIGN', 'ROLE_REVOKE',
    'PERMISSION_GRANT', 'PERMISSION_DENY',
    'SETTINGS_CHANGE'
)
ORDER BY created_at DESC;
```

---

## 🧹 Data Maintenance

### 23. Anonymize User Data (GDPR Right to be Forgotten)

```sql
-- Anonymize a user's audit data
UPDATE audit_logs
SET
    user_id = NULL,
    ip_address = '[ANONYMIZED]',
    user_agent = '[ANONYMIZED]',
    description = '[USER DATA REMOVED]'
WHERE user_id = '<user-uuid>';

-- Verify anonymization
SELECT COUNT(*) as anonymized_records
FROM audit_logs
WHERE description = '[USER DATA REMOVED]';
```

### 24. Archive Old Audit Logs

```sql
-- Create archive table (one-time)
CREATE TABLE IF NOT EXISTS audit_logs_archive (LIKE audit_logs INCLUDING ALL);

-- Move logs older than 90 days to archive
WITH moved_rows AS (
    DELETE FROM audit_logs
    WHERE created_at < NOW() - INTERVAL '90 days'
    RETURNING *
)
INSERT INTO audit_logs_archive
SELECT * FROM moved_rows;

-- Verify
SELECT
    'active' as table_name,
    COUNT(*) as record_count,
    MIN(created_at) as oldest,
    MAX(created_at) as newest
FROM audit_logs
UNION ALL
SELECT
    'archive' as table_name,
    COUNT(*) as record_count,
    MIN(created_at) as oldest,
    MAX(created_at) as newest
FROM audit_logs_archive;
```

### 25. Clean Up Test Data

```sql
-- Remove test/development audit entries
DELETE FROM audit_logs
WHERE ip_address IN ('127.0.0.1', '172.18.0.1')  -- Docker internal IPs
  AND user_agent LIKE '%curl%'
  AND created_at < NOW() - INTERVAL '7 days';
```

---

## 📊 Advanced Analytics

### 26. Error Rate by Time Window

```sql
-- Error rate per hour
SELECT
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as total_requests,
    COUNT(*) FILTER (WHERE status_code >= 400) as failed_requests,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status_code >= 400) / COUNT(*)::numeric, 2) as error_rate
FROM audit_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour DESC;
```

### 27. Suspicious Activity Detection

```sql
-- Detect potential malicious behavior
-- (high error rate from single IP)
SELECT
    ip_address,
    COUNT(*) as total_requests,
    COUNT(*) FILTER (WHERE status_code >= 400) as failed,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status_code >= 400) / COUNT(*)::numeric, 2) as fail_rate,
    ARRAY_AGG(DISTINCT action) as actions_attempted
FROM audit_logs
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY ip_address
HAVING
    COUNT(*) > 10  -- More than 10 requests
    AND COUNT(*) FILTER (WHERE status_code >= 400) > 5  -- More than 5 failures
ORDER BY fail_rate DESC;
```

### 28. Cohort Analysis

```sql
-- User cohorts by first action date
SELECT
    DATE_TRUNC('week', first_action) as cohort_week,
    COUNT(*) as users,
    ROUND(AVG(total_actions)::numeric, 2) as avg_actions_per_user
FROM (
    SELECT
        user_id,
        MIN(created_at) as first_action,
        COUNT(*) as total_actions
    FROM audit_logs
    WHERE user_id IS NOT NULL
    GROUP BY user_id
) user_stats
GROUP BY cohort_week
ORDER BY cohort_week DESC;
```

---

## 🔧 Utility Queries

### 29. Table Statistics

```sql
-- Audit logs table stats
SELECT
    COUNT(*) as total_records,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT session_id) as unique_sessions,
    COUNT(DISTINCT ip_address) as unique_ips,
    MIN(created_at) as oldest_record,
    MAX(created_at) as newest_record,
    pg_size_pretty(pg_total_relation_size('audit_logs')) as table_size
FROM audit_logs;
```

### 30. Index Usage

```sql
-- Check which indexes are being used
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE tablename = 'audit_logs'
ORDER BY idx_scan DESC;
```

---

## 🎯 Quick Copy-Paste Queries

### Last Hour Activity
```sql
SELECT action, COUNT(*) FROM audit_logs WHERE created_at > NOW() - INTERVAL '1 hour' GROUP BY action ORDER BY COUNT(*) DESC;
```

### Failed Requests Today
```sql
SELECT COUNT(*) FROM audit_logs WHERE status_code >= 400 AND created_at > CURRENT_DATE;
```

### Average Latency
```sql
SELECT ROUND(AVG(latency_ms)::numeric, 2) as avg_latency_ms FROM audit_logs WHERE created_at > NOW() - INTERVAL '1 hour';
```

### Top 5 Active IPs
```sql
SELECT ip_address, COUNT(*) as requests FROM audit_logs WHERE created_at > NOW() - INTERVAL '24 hours' GROUP BY ip_address ORDER BY requests DESC LIMIT 5;
```

---

## 📖 Tips & Best Practices

### Performance Tips
1. **Use time ranges**: Always filter by `created_at` for better performance
2. **Use indexes**: The table has indexes on `created_at`, `user_id`, `session_id`, `action`
3. **EXPLAIN ANALYZE**: Use `EXPLAIN ANALYZE` before running expensive queries
4. **Limit results**: Always use `LIMIT` for exploratory queries

### Example with EXPLAIN:
```sql
EXPLAIN ANALYZE
SELECT * FROM audit_logs
WHERE created_at > NOW() - INTERVAL '1 hour'
  AND action = 'QUERY';
```

### Materialized Views for Dashboards
```sql
-- Create materialized view for dashboard
CREATE MATERIALIZED VIEW audit_daily_summary AS
SELECT
    DATE(created_at) as date,
    action,
    COUNT(*) as requests,
    COUNT(DISTINCT user_id) as unique_users,
    ROUND(AVG(latency_ms)::numeric, 2) as avg_latency
FROM audit_logs
GROUP BY date, action;

-- Refresh daily
REFRESH MATERIALIZED VIEW audit_daily_summary;
```

---

## 🔗 Related Documentation

- **Audit Logging Implementation**: `docs/features/COMPREHENSIVE_AUDIT_LOGGING_COMPLETE.md`
- **Grafana Dashboard Guide**: `GRAFANA_SETUP_GUIDE.md`
- **Quick Reference**: `docs/features/AUDIT_LOGGING_QUICK_REFERENCE.md`

---

**Last Updated**: 2025-11-28
**Queries**: 30+ SQL queries for audit log analysis
**Difficulty**: Beginner to Advanced

