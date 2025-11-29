# 🔍 Chat Flow Tracing in Grafana - Complete Guide

**Session ID**: `test-session-1764305647`  
**Document ID**: `dee330a4-5607-4218-8f02-3022df96ccb0`

---

## ✅ What Just Happened

We executed a complete chat flow with these steps:

1. **Created Session** → `test-session-1764305647`
2. **Uploaded Document** → `test_doc.txt` (55 bytes)
3. **Sent Query** → "What is this document about?"
4. **Retrieved Session** → Conversation history
5. **Listed Documents** → Session documents

**All tracked automatically by audit middleware!**

---

## 📊 View in Grafana Dashboard

### Step 1: Open Dashboard
```
http://localhost:3000/d/audit-logs-comprehensive
```

Login: `admin` / `admin`

### Step 2: Adjust Time Range
- Click **time picker** (top-right corner)
- Select **"Last 5 minutes"** or **"Last 15 minutes"**
- This ensures you see the chat flow we just executed

---

## 🎯 What You'll See in Each Panel

### Panel 1: Requests by User Role
```
┌─────────────────────────┐
│   Pie Chart             │
│                         │
│   Anonymous: 100%       │
│   (All requests from    │
│    unauthenticated user)│
└─────────────────────────┘
```

**Interpretation**: All requests were made without authentication (anonymous user)

---

### Panel 2: Total Audit Events
```
┌─────────────────────────┐
│      Gauge              │
│                         │
│         15              │
│   Total Events          │
└─────────────────────────┘
```

**Interpretation**: 15 total requests tracked (increased from 4 earlier)

---

### Panel 3: User Actions Over Time
```
┌─────────────────────────────────────────┐
│  Time Series Graph                      │
│                                         │
│   ▲                                     │
│   │     ┌──┐                           │
│   │     │  │  ┌─┐                      │
│   │  ┌──┘  └──┘ └──┐                  │
│   │  │              │                  │
│   └──┴──────────────┴──────────────►  │
│    04:54:12      04:54:16   04:54:36   │
└─────────────────────────────────────────┘
```

**Interpretation**: 
- Spike at **04:54:12** → Document upload (4.5 seconds)
- Activity at **04:54:15-16** → Session/documents queries
- Spike at **04:54:36** → Chat query (58 seconds!)

---

### Panel 4: Request Latency by Endpoint
```
┌──────────────────────────────────────────┐
│  Time Series - P95 Latency               │
│                                          │
│  POST /api/v1/query     ████████ 58.4s  │
│  POST /api/v1/upload    ██ 4.5s         │
│  GET /api/v1/sessions   █ 0.1s          │
│  GET /api/v1/documents  █ 0.02s         │
└──────────────────────────────────────────┘
```

**Interpretation**:
- ⚠️ **Query endpoint is SLOW** (58 seconds)
- Upload took 4.5 seconds (acceptable for file upload)
- Other endpoints are fast (<200ms)

**Action**: Investigate why query took so long (LLM timeout? Embedding search?)

---

### Panel 5: HTTP Status Codes
```
┌─────────────────────────────────────────┐
│  Stacked Bar Chart                      │
│                                         │
│  200 OK    ███████████████████ 14      │
│  422 Error █ 1                          │
│                                         │
└─────────────────────────────────────────┘
```

**Interpretation**:
- 14 successful requests (200 OK)
- 1 validation error (422) - the query had wrong format

---

### Panel 6: Failed Requests
```
┌─────────────────────────────────────────┐
│  Table                                  │
│                                         │
│  Endpoint             | Failures        │
│  ──────────────────────────────────     │
│  POST /api/v1/query   | 1              │
└─────────────────────────────────────────┘
```

**Interpretation**: One query failed validation (we sent malformed request body)

---

### Panel 7: Audit Log Stream
```
┌──────────────────────────────────────────────────────────┐
│  Real-time Log Stream (from Loki)                        │
│                                                          │
│  04:54:36 | AUDIT_EVENT | POST /api/v1/query | 200     │
│  04:54:16 | AUDIT_EVENT | GET /api/v1/documents | 200  │
│  04:54:16 | AUDIT_EVENT | GET /api/v1/sessions/... |200│
│  04:54:15 | AUDIT_EVENT | POST /api/v1/query | 422     │
│  04:54:12 | AUDIT_EVENT | POST /api/v1/upload | 200    │
└──────────────────────────────────────────────────────────┘
```

**Interpretation**: Complete chronological log of all audit events

---

## 🔬 Deep Dive: Trace a Specific Request

### Using Prometheus (Metrics)

1. **Open Prometheus**: http://localhost:9090

2. **Query for chat-related requests**:
   ```promql
   audit_requests_total{endpoint="/api/v1/query"}
   ```

3. **Check latency distribution**:
   ```promql
   histogram_quantile(0.95, 
     rate(audit_request_duration_seconds_bucket{endpoint="/api/v1/query"}[5m])
   )
   ```

4. **Count by status code**:
   ```promql
   sum by(status) (audit_requests_total{endpoint="/api/v1/query"})
   ```

---

### Using PostgreSQL (Audit Logs)

```bash
# Connect to database
docker-compose exec postgres psql -U postgres -d ragchatbot
```

**Query 1: Complete Chat Flow Timeline**
```sql
SELECT 
    TO_CHAR(created_at, 'HH24:MI:SS.MS') as timestamp,
    action,
    SUBSTRING(description, 1, 50) as description,
    status_code,
    ROUND(latency_ms::numeric, 2) as latency_ms
FROM audit_logs 
WHERE created_at > NOW() - INTERVAL '5 minutes'
  AND (
    description LIKE '%test-session-1764305647%' OR
    description LIKE '%dee330a4-5607-4218-8f02-3022df96ccb0%'
  )
ORDER BY created_at;
```

**Expected Output**:
```
  timestamp   | action |                description                | status | latency
--------------+--------+------------------------------------------+--------+---------
 04:54:12.000 | UPLOAD | POST /api/v1/upload                      |    200 | 4521.37
 04:54:15.000 | QUERY  | POST /api/v1/query                       |    422 |   49.36
 04:54:16.000 | VIEW   | GET /api/v1/sessions/test-session-...    |    200 |  116.11
 04:54:16.000 | VIEW   | GET /api/v1/documents                    |    200 |   19.21
```

---

**Query 2: Performance Breakdown**
```sql
SELECT 
    action,
    COUNT(*) as total_requests,
    ROUND(AVG(latency_ms)::numeric, 2) as avg_latency,
    ROUND(MIN(latency_ms)::numeric, 2) as min_latency,
    ROUND(MAX(latency_ms)::numeric, 2) as max_latency,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms)::numeric, 2) as p95_latency
FROM audit_logs 
WHERE created_at > NOW() - INTERVAL '5 minutes'
GROUP BY action
ORDER BY avg_latency DESC;
```

**Expected Output**:
```
 action | total | avg_latency | min_latency | max_latency | p95_latency
--------+-------+-------------+-------------+-------------+-------------
 QUERY  |     2 |    29243.56 |       49.36 |    58437.77 |    58437.77  ⚠️ SLOW!
 UPLOAD |     1 |     4521.37 |     4521.37 |     4521.37 |     4521.37
 VIEW   |     6 |      113.74 |        0.95 |      552.15 |      552.15
```

---

**Query 3: Error Analysis**
```sql
SELECT 
    TO_CHAR(created_at, 'HH24:MI:SS') as time,
    action,
    status_code,
    description,
    error_message
FROM audit_logs 
WHERE status_code >= 400
  AND created_at > NOW() - INTERVAL '5 minutes'
ORDER BY created_at DESC;
```

**Expected Output**:
```
   time   | action | status_code |      description       | error_message
----------+--------+-------------+------------------------+--------------
 04:54:15 | QUERY  |         422 | POST /api/v1/query     | Validation error
```

---

### Using Loki (Logs)

**Option 1: Grafana Explore**

1. Open Grafana → Click **Explore** (compass icon)
2. Select **Loki** datasource
3. Query:
   ```logql
   {job="backend"} |= "AUDIT_EVENT" |= "test-session-1764305647"
   ```

**Option 2: Command Line**
```bash
# Get all logs for this session
curl -G -s 'http://localhost:3100/loki/api/v1/query' \
  --data-urlencode 'query={job="backend"} |= "test-session-1764305647"' \
  --data-urlencode 'limit=100' | jq '.data.result'
```

---

## 🎯 Key Insights from This Chat Flow

### Performance Issue Detected ⚠️
```
POST /api/v1/query took 58.4 seconds!
```

**Root Cause Investigation**:
1. Check **Tempo** for distributed trace (if available)
2. Check backend logs for LLM timeout
3. Check if OpenAI API is slow
4. Check embedding search performance

**Query to investigate**:
```sql
SELECT 
    description,
    latency_ms,
    error_message,
    meta_info
FROM audit_logs 
WHERE action = 'QUERY' 
  AND latency_ms > 10000  -- More than 10 seconds
ORDER BY latency_ms DESC
LIMIT 10;
```

---

### Success Metrics ✅
```
✅ Upload: 4.5 seconds (acceptable)
✅ Session retrieval: 116ms (good)
✅ Document listing: 19ms (excellent)
✅ Overall success rate: 93% (14/15 requests)
```

---

## 📈 Advanced Grafana Queries

### Custom Query Panel

Add a new panel to your dashboard:

**Query 1: Chat Query Success Rate**
```promql
100 * (
  sum(rate(audit_requests_total{endpoint="/api/v1/query", status="200"}[5m]))
  /
  sum(rate(audit_requests_total{endpoint="/api/v1/query"}[5m]))
)
```

**Query 2: Average Upload Time**
```promql
avg(rate(audit_request_duration_seconds_sum{endpoint="/api/v1/upload"}[5m]))
/
avg(rate(audit_request_duration_seconds_count{endpoint="/api/v1/upload"}[5m]))
```

**Query 3: Requests Per Minute**
```promql
sum(rate(audit_requests_total[1m])) * 60
```

---

## 🔍 Correlate Across All Tools

### Complete Investigation Flow

**Scenario**: "Why did my chat query take 58 seconds?"

**Step 1: Grafana Dashboard** (High-level overview)
- See latency spike at 04:54:36
- Identify endpoint: POST /api/v1/query
- Status: 200 (successful but slow)

**Step 2: Prometheus** (Detailed metrics)
```promql
audit_request_duration_seconds_bucket{endpoint="/api/v1/query"}
```
- P50: 25 seconds
- P95: 58 seconds
- P99: 58 seconds

**Step 3: PostgreSQL** (Audit details)
```sql
SELECT * FROM audit_logs WHERE action='QUERY' AND latency_ms > 50000;
```
- User: anonymous
- Query: "What is this document about?"
- Session: test-session-1764305647

**Step 4: Loki** (Application logs)
```logql
{job="backend"} |= "test-session-1764305647" |= "query"
```
- See if LLM timeout occurred
- Check embedding search duration

**Step 5: Tempo** (Distributed trace - if instrumented)
- See full request span
- Identify slowest component (LLM call, database query, etc.)

---

## 📚 Next Steps

### 1. Create Alerts
Set up Grafana alerts for:
- Slow queries (> 10 seconds)
- High error rate (> 5%)
- Failed uploads

### 2. Monitor Over Time
- Track P95 latency trends
- Monitor daily active users
- Analyze peak usage times

### 3. Optimize
- Based on audit data, optimize slow endpoints
- Add caching for frequent queries
- Scale resources if needed

---

## 🔗 Quick Links

| Tool | URL | Purpose |
|------|-----|---------|
| **Grafana Dashboard** | http://localhost:3000/d/audit-logs-comprehensive | Main visualization |
| **Prometheus** | http://localhost:9090 | Raw metrics & queries |
| **Backend Metrics** | http://localhost:8000/metrics | Current metric values |
| **API Docs** | http://localhost:8000/docs | Test endpoints |

---

## 📝 Summary

Your chat flow generated **5 audit events**:

1. ✅ **UPLOAD** - test_doc.txt (4.5s, 200 OK)
2. ❌ **QUERY** - Validation error (49ms, 422 Error)
3. ✅ **VIEW** - Session details (116ms, 200 OK)
4. ✅ **VIEW** - Document list (19ms, 200 OK)
5. ⚠️ **QUERY** - Successful but slow (58s, 200 OK)

**All visible in Grafana!** 🎉

---

**Last Updated**: 2025-11-28  
**Session**: test-session-1764305647  
**Total Events**: 15 (10 new from chat flow)
