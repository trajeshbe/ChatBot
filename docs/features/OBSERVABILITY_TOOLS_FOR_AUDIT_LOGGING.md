# How Grafana, Tempo, and OpenCost Help with Audit Logging

**Date**: 2025-11-28
**Purpose**: Explain how observability tools enhance audit logging with real-world examples
**Tools**: Grafana, Tempo, Loki, Prometheus, OpenCost

---

## 🎯 Overview

Our comprehensive audit logging system leverages multiple observability tools, each serving a specific purpose in tracking and analyzing user actions. This document explains **how each tool helps** and provides **real-world examples** of their usage.

---

## 📊 The Observability Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Action / API Request                │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Audit Middleware (FastAPI)                    │
│  - Intercepts request                                            │
│  - Generates request_id                                          │
│  - Measures latency                                              │
│  - Extracts user context                                         │
└─────┬──────────┬──────────┬──────────┬──────────────────────────┘
      │          │          │          │
      ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│ OpenTel  │ │Prometheus│ │ Loki     │ │ PostgreSQL   │
│ (Tempo)  │ │ Metrics  │ │ Logs     │ │ audit_logs   │
│          │ │          │ │          │ │ table        │
└────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘
     │            │            │               │
     │            │            │               │
     ▼            ▼            ▼               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Grafana Dashboard                        │
│  - Real-time metrics visualization                               │
│  - Distributed trace analysis                                    │
│  - Log aggregation and search                                    │
│  - Audit trail queries                                           │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                         OpenCost (Optional)                      │
│  - Cost attribution by user/team                                 │
│  - Resource usage tracking                                       │
│  - Budget alerts                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Tool #1: Grafana - The Visualization Layer

### What It Does
**Grafana** is the unified visualization platform that brings together data from all sources (Prometheus, Loki, Tempo) into interactive dashboards.

### How It Helps Audit Logging

1. **Real-time Monitoring**: See user activity as it happens
2. **Historical Analysis**: Analyze trends over days/weeks/months
3. **Alerting**: Get notified of suspicious activity
4. **Multi-datasource Correlation**: Combine metrics, logs, and traces in one view

### Real-World Example: Security Incident Investigation

**Scenario**: Your security team reports possible unauthorized access attempts to admin endpoints.

**Using Grafana**:

1. **Open Audit Dashboard**:
   ```
   http://localhost:3000/d/audit-logs-comprehensive
   ```

2. **Filter by Action Type**:
   - Select template variable: `$action_type = PERMISSION_DENIED, UNAUTHORIZED_ACCESS`
   - Time range: Last 24 hours

3. **View Panels**:

   **Panel 1: Failed Requests Table**
   ```
   Endpoint                    | Error Type           | Count | Last Occurred
   ---------------------------|----------------------|-------|---------------
   POST /api/v1/admin/users   | PERMISSION_DENIED    | 47    | 2 mins ago
   GET /api/v1/admin/secrets  | UNAUTHORIZED_ACCESS  | 23    | 5 mins ago
   DELETE /api/v1/documents/* | PERMISSION_DENIED    | 12    | 10 mins ago
   ```

   **Insight**: Someone is trying to access admin endpoints without authorization.

   **Panel 2: User Actions Over Time (Time Series)**
   ```
   Chart shows spike in PERMISSION_DENIED events starting at 14:30
   ```

   **Insight**: Attack started at 14:30, still ongoing.

   **Panel 3: HTTP Status Codes**
   ```
   Status 403 (Forbidden): 82 requests in last hour (↑ 400% from baseline)
   ```

   **Insight**: Abnormal spike in forbidden requests.

4. **Drill Down to Logs**:

   **Panel 7: Audit Log Stream (Loki)**
   ```logql
   {job="backend"} |= "AUDIT_EVENT" | json | action_type="UNAUTHORIZED_ACCESS"
   ```

   **Sample Log Entry**:
   ```json
   {
     "event_type": "api_request",
     "request_id": "abc-123-def",
     "timestamp": 1764299292.547,
     "user_id": null,
     "username": null,
     "user_role": null,
     "session_id": "malicious-session-xyz",
     "action_type": "UNAUTHORIZED_ACCESS",
     "method": "POST",
     "path": "/api/v1/admin/users",
     "status_code": 403,
     "client_ip": "192.168.1.100",  ← Suspicious IP
     "user_agent": "python-requests/2.28.0"  ← Automated tool
   }
   ```

   **Insight**:
   - All requests from IP `192.168.1.100`
   - Using automated Python script
   - No valid user credentials

5. **Take Action**:
   - Block IP `192.168.1.100` in firewall
   - Invalidate session `malicious-session-xyz`
   - Create alert rule for future attacks

**Grafana Value**: Unified view of the attack in one dashboard, correlating metrics, logs, and trends.

---

## 🔍 Tool #2: Tempo - Distributed Tracing

### What It Does
**Tempo** stores and queries distributed traces, allowing you to follow a single user request across multiple services and operations.

### How It Helps Audit Logging

1. **Request Flow Visualization**: See the entire journey of a user action
2. **Performance Analysis**: Identify bottlenecks in audit logging
3. **Error Root Cause**: Trace errors back to their origin
4. **Correlation**: Link logs and metrics to specific traces

### Real-World Example: Slow Document Upload Investigation

**Scenario**: Users report that document uploads are taking 30+ seconds, but you're not sure where the delay is.

**Using Tempo via Grafana**:

1. **Find a Slow Request**:

   In Grafana, go to **Explore** → Select **Tempo** datasource

   **Query**:
   ```
   Search by tags:
   - http.method = POST
   - http.target = /api/v1/upload
   - duration > 30s
   ```

2. **View Trace**:

   **Trace ID**: `abc-123-def-456-789`

   **Trace Waterfall**:
   ```
   ┌─ audit_middleware.dispatch                     [31.2s]
   │  ├─ extract_request_context                     [0.5ms]
   │  ├─ start_otel_span                             [0.2ms]
   │  ├─ call_next (actual endpoint)                 [30.8s]  ← BOTTLENECK
   │  │  ├─ document_service.upload                  [30.7s]
   │  │  │  ├─ save_to_minio                         [28.5s]  ← SLOWEST
   │  │  │  ├─ save_to_database                      [1.2s]
   │  │  │  └─ generate_embeddings                   [1.0s]
   │  │  └─ return_response                          [0.1s]
   │  ├─ log_audit_event (async)                     [15ms]
   │  │  ├─ update_prometheus_metrics                [0.5ms]
   │  │  ├─ structured_logging                       [0.8ms]
   │  │  └─ database_insert                          [13.7ms]
   │  └─ finalize_span                               [0.3ms]
   ```

3. **Root Cause Identified**:
   - **Problem**: MinIO upload taking 28.5 seconds (91% of total time)
   - **Audit System Overhead**: Only 15ms (0.05% of total time) ✅
   - **Conclusion**: Audit logging is NOT the bottleneck; MinIO network is slow

4. **Span Details**:

   Click on `save_to_minio` span:
   ```
   Span: save_to_minio
   Duration: 28.5s
   Attributes:
     - file.name: "large_document.pdf"
     - file.size: 125MB
     - minio.endpoint: "minio:9000"
     - minio.bucket: "documents"
     - error: null

   Events:
     - 0.0s: Upload started
     - 2.5s: Connection established
     - 28.5s: Upload completed
   ```

   **Insight**: Network throughput is ~4.4 MB/s (125MB / 28.5s), which is slow.

5. **Fix Applied**:
   - Increase MinIO network bandwidth
   - Enable MinIO compression
   - Add chunked upload for large files

**Tempo Value**: Pinpointed the exact bottleneck (MinIO network) and proved audit logging was NOT causing the delay.

---

## 📈 Tool #3: Prometheus - Metrics Collection

### What It Does
**Prometheus** collects and stores time-series metrics, enabling quantitative analysis of system behavior.

### How It Helps Audit Logging

1. **Aggregated Statistics**: Count total requests, average latency, error rates
2. **Trend Analysis**: See how metrics change over time
3. **Alerting**: Trigger alerts based on thresholds
4. **Performance Monitoring**: Track audit system overhead

### Real-World Example: Performance Impact Analysis

**Scenario**: Your manager asks: "How much overhead does audit logging add to our API?"

**Using Prometheus**:

1. **Query: Request Duration by Endpoint**

   **PromQL**:
   ```promql
   histogram_quantile(0.95,
     sum(rate(audit_request_duration_seconds_bucket[5m])) by (endpoint, le)
   )
   ```

   **Result**:
   ```
   Endpoint                      | P95 Latency | P95 Latency (Before Audit)
   ------------------------------|-------------|---------------------------
   POST /api/v1/query            | 245ms       | 230ms (+15ms)
   GET /api/v1/documents         | 52ms        | 45ms (+7ms)
   POST /api/v1/upload           | 1.2s        | 1.18s (+20ms)
   GET /api/v1/admin/sessions    | 98ms        | 88ms (+10ms)
   ```

   **Insight**: Audit middleware adds 7-20ms overhead (P95), well within acceptable limits.

2. **Query: Total Audit Events by Action Type**

   **PromQL**:
   ```promql
   sum by(action_type) (audit_user_actions_total)
   ```

   **Result**:
   ```
   action_type          | Total Events | % of Total
   ---------------------|--------------|------------
   QUERY                | 12,543       | 45.2%
   VIEW                 | 8,901        | 32.1%
   UPLOAD               | 3,456        | 12.5%
   SCRAPE               | 1,234        | 4.4%
   CREATE               | 890          | 3.2%
   DELETE               | 456          | 1.6%
   PERMISSION_DENIED    | 278          | 1.0%
   ```

   **Insight**: QUERY and VIEW are the most common actions (77% of total).

3. **Query: Error Rate**

   **PromQL**:
   ```promql
   sum(rate(audit_requests_total{status=~"5.."}[5m]))
   /
   sum(rate(audit_requests_total[5m]))
   * 100
   ```

   **Result**: `0.23%` (error rate is very low)

4. **Query: Active Sessions**

   **PromQL**:
   ```promql
   count(count by(session_id) (audit_requests_total))
   ```

   **Result**: `47 active sessions` currently

5. **Create Alert Rule**:

   **Alert**: High Error Rate
   ```yaml
   - alert: HighAuditErrorRate
     expr: rate(audit_failed_requests_total[5m]) > 10
     for: 5m
     annotations:
       summary: "High rate of failed requests detected"
       description: "{{ $value }} failed requests/second (threshold: 10)"
   ```

**Prometheus Value**: Quantified audit system performance, proved minimal overhead (<30ms), and enabled proactive alerting.

---

## 📝 Tool #4: Loki - Log Aggregation

### What It Does
**Loki** aggregates structured logs from all services, enabling powerful log search and correlation.

### How It Helps Audit Logging

1. **Full-Text Search**: Find audit events by any field
2. **Pattern Matching**: Identify suspicious log patterns
3. **Correlation**: Link logs to traces and metrics
4. **Retention**: Store logs for compliance (7 years for SOC 2)

### Real-World Example: GDPR Data Access Request

**Scenario**: A user (ID: `user-abc-123`) requests all data you have on them (GDPR "Right to Access").

**Using Loki in Grafana Explore**:

1. **Query: All Actions by User**

   **LogQL**:
   ```logql
   {job="backend"} |= "AUDIT_EVENT"
   | json
   | user_id="user-abc-123"
   | line_format "{{.timestamp}} | {{.action_type}} | {{.path}} | {{.client_ip}}"
   ```

   **Result**: 234 log entries
   ```
   2025-11-28 10:15:32 | QUERY      | /api/v1/query         | 192.168.1.50
   2025-11-28 09:45:12 | UPLOAD     | /api/v1/upload        | 192.168.1.50
   2025-11-28 09:30:05 | VIEW       | /api/v1/documents     | 192.168.1.50
   2025-11-27 16:20:18 | DELETE     | /api/v1/documents/xyz | 192.168.1.50
   2025-11-27 14:10:42 | LOGIN      | /auth/login           | 192.168.1.50
   ...
   ```

2. **Query: Failed Login Attempts**

   **LogQL**:
   ```logql
   {job="backend"} |= "AUDIT_EVENT"
   | json
   | user_id="user-abc-123"
   | action_type="LOGIN_FAILED"
   ```

   **Result**: 3 failed login attempts
   ```
   2025-11-25 08:12:34 | LOGIN_FAILED | /auth/login | 192.168.1.50 | Wrong password
   2025-11-25 08:13:01 | LOGIN_FAILED | /auth/login | 192.168.1.50 | Wrong password
   2025-11-25 08:13:45 | LOGIN       | /auth/login | 192.168.1.50 | Success
   ```

3. **Query: Data Exports**

   **LogQL**:
   ```logql
   {job="backend"} |= "AUDIT_EVENT"
   | json
   | user_id="user-abc-123"
   | action_type=~"EXPORT|DOWNLOAD"
   ```

   **Result**: 12 data exports

4. **Generate GDPR Report**:

   Export Loki results to JSON → Convert to PDF → Send to user

   **Report Contents**:
   - Total actions: 234
   - Document uploads: 45
   - Queries: 123
   - Exports: 12
   - Failed logins: 3
   - IP addresses used: 2 (192.168.1.50, 192.168.1.51)

**Loki Value**: Quickly compiled complete user activity history for GDPR compliance, including all actions, timestamps, and IP addresses.

---

## 💰 Tool #5: OpenCost - Cost Attribution

### What It Does
**OpenCost** tracks resource usage and costs in Kubernetes clusters, attributing costs to specific users, teams, or projects.

### How It Helps Audit Logging

1. **Cost Attribution**: Track audit log storage costs by user/team
2. **Budget Alerts**: Get notified when costs exceed thresholds
3. **Resource Optimization**: Identify expensive audit operations
4. **Chargeback**: Bill teams for their audit log usage

### Real-World Example: Team Budget Management

**Scenario**: Your company has multiple teams using the RAG chatbot. Finance wants to charge each team for their usage.

**Using OpenCost with Audit Data**:

1. **Query PostgreSQL for User Activity**:

   ```sql
   SELECT
     u.username,
     u.team,
     COUNT(*) as total_requests,
     SUM(CASE WHEN al.action = 'QUERY' THEN 1 ELSE 0 END) as llm_queries,
     SUM(CASE WHEN al.action = 'UPLOAD' THEN 1 ELSE 0 END) as uploads,
     ROUND(AVG(al.latency_ms)::numeric, 2) as avg_latency_ms
   FROM audit_logs al
   JOIN users u ON al.user_id = u.id
   WHERE al.created_at > NOW() - INTERVAL '30 days'
   GROUP BY u.username, u.team
   ORDER BY total_requests DESC;
   ```

   **Result**:
   ```
   username     | team       | total_requests | llm_queries | uploads | avg_latency
   -------------|------------|----------------|-------------|---------|------------
   alice@co.com | Data-Team  | 15,234         | 12,543      | 234     | 245ms
   bob@co.com   | AI-Team    | 8,901          | 7,890       | 456     | 198ms
   carol@co.com | Ops-Team   | 3,456          | 2,345       | 789     | 312ms
   ```

2. **OpenCost Query: Compute Costs by Namespace**

   (Assuming each team has a dedicated namespace)

   **OpenCost API**:
   ```bash
   curl http://localhost:9003/allocation/compute \
     -d window=30d \
     -d aggregate=namespace
   ```

   **Result**:
   ```json
   {
     "data": [
       {
         "namespace": "data-team",
         "cpuCost": 234.56,
         "memoryCost": 123.45,
         "storageCost": 45.67,
         "totalCost": 403.68
       },
       {
         "namespace": "ai-team",
         "cpuCost": 145.23,
         "memoryCost": 78.90,
         "storageCost": 34.12,
         "totalCost": 258.25
       },
       {
         "namespace": "ops-team",
         "cpuCost": 89.12,
         "memoryCost": 45.67,
         "storageCost": 23.45,
         "totalCost": 158.24
       }
     ]
   }
   ```

3. **Combine Audit Data + Cost Data**:

   **Cost per Request**:
   ```
   Team       | Total Requests | Total Cost | Cost per Request
   -----------|----------------|------------|------------------
   Data-Team  | 15,234         | $403.68    | $0.0265
   AI-Team    | 8,901          | $258.25    | $0.0290
   Ops-Team   | 3,456          | $158.24    | $0.0458  ← Highest!
   ```

   **Insight**: Ops-Team has the highest cost per request (73% more than Data-Team).

4. **Investigate Ops-Team**:

   **Query Audit Logs**:
   ```sql
   SELECT action, COUNT(*) as count
   FROM audit_logs al
   JOIN users u ON al.user_id = u.id
   WHERE u.team = 'Ops-Team'
     AND al.created_at > NOW() - INTERVAL '30 days'
   GROUP BY action
   ORDER BY count DESC;
   ```

   **Result**:
   ```
   action   | count
   ---------|-------
   UPLOAD   | 789    ← 23% of all requests (vs 2% for other teams)
   SCRAPE   | 456    ← 13% of all requests (vs 3% for other teams)
   QUERY    | 2,345
   ```

   **Insight**: Ops-Team is doing many heavy operations (uploads, web scraping), which consume more resources.

5. **Recommendations**:
   - **Data-Team**: Most cost-efficient ($0.0265/request) → Best practices
   - **AI-Team**: Good efficiency ($0.0290/request)
   - **Ops-Team**: Optimize uploads and scraping to reduce cost
     - Use batch uploads instead of individual uploads
     - Cache scraped data to avoid re-scraping
     - Set scraping rate limits

6. **Create Budget Alert**:

   **OpenCost Alert**:
   ```yaml
   - alert: TeamBudgetExceeded
     expr: sum(opencost_namespace_cost{namespace="ops-team"}) > 200
     for: 1h
     annotations:
       summary: "Ops-Team exceeded monthly budget of $200"
   ```

**OpenCost Value**: Identified cost inefficiencies by team, enabled chargeback, and provided data-driven recommendations for cost optimization.

---

## 🔗 Tool Integration: The Full Workflow

### Real-World Example: Complete Security Incident Response

**Scenario**: Grafana alert fires at 2:00 AM - "Unauthorized access attempts detected"

**Step-by-Step Response Using All Tools**:

#### Step 1: Grafana Alert Notification
```
🚨 ALERT: UnauthorizedAccessAttempts
Severity: Critical
Value: 15 unauthorized access attempts in last 5 minutes
Time: 2025-11-28 02:00:15 UTC
```

#### Step 2: Open Grafana Dashboard
```
http://localhost:3000/d/audit-logs-comprehensive
```

**Panel: Failed Requests**
```
Endpoint               | Count | Last IP
-----------------------|-------|-------------
/api/v1/admin/users    | 47    | 10.0.1.123
/api/v1/admin/secrets  | 23    | 10.0.1.123
```

**Insight**: All from IP `10.0.1.123`

#### Step 3: Search Logs in Loki
```logql
{job="backend"} |= "AUDIT_EVENT"
| json
| client_ip="10.0.1.123"
| line_format "{{.timestamp}} | {{.action_type}} | {{.path}} | {{.status_code}}"
```

**Result**:
```
02:00:00 | UNAUTHORIZED_ACCESS | /api/v1/admin/users    | 403
02:00:05 | UNAUTHORIZED_ACCESS | /api/v1/admin/secrets  | 403
02:00:10 | UNAUTHORIZED_ACCESS | /api/v1/admin/users    | 403
...
```

**Insight**: Automated attack, trying admin endpoints every 5 seconds

#### Step 4: Trace a Request in Tempo
```
Trace ID: xyz-789-abc (from Loki log)
```

**Trace shows**:
```
┌─ audit_middleware.dispatch [2ms]
│  ├─ extract_request_context [0.5ms]
│  │  → user_id: null
│  │  → session_id: "fake-session-abc"
│  │  → Authorization header: "Bearer invalid-token-xyz"
│  ├─ check_permissions [1ms]
│  │  → PERMISSION_DENIED (no valid user)
│  └─ log_audit_event [0.5ms]
│     → action: UNAUTHORIZED_ACCESS
│     → status: 403
```

**Insight**: Attacker using fake JWT token

#### Step 5: Check Prometheus for Attack Pattern
```promql
sum by(client_ip) (
  rate(audit_failed_requests_total{error_type="UNAUTHORIZED_ACCESS"}[5m])
)
```

**Result**:
```
client_ip    | Failed Requests/sec
-------------|--------------------
10.0.1.123   | 12.5  ← ATTACKER
10.0.2.45    | 0.02
10.0.3.67    | 0.01
```

**Insight**: `10.0.1.123` is 625x higher than normal

#### Step 6: Check Historical Data in PostgreSQL
```sql
SELECT
  MIN(created_at) as first_seen,
  MAX(created_at) as last_seen,
  COUNT(*) as total_attempts
FROM audit_logs
WHERE ip_address = '10.0.1.123'
  AND action = 'UNAUTHORIZED_ACCESS';
```

**Result**:
```
first_seen           | last_seen            | total_attempts
---------------------|----------------------|----------------
2025-11-28 01:55:12  | 2025-11-28 02:05:34  | 152
```

**Insight**: Attack started at 01:55, lasted 10 minutes, 152 attempts

#### Step 7: Take Action
1. **Block IP in Firewall**:
   ```bash
   iptables -A INPUT -s 10.0.1.123 -j DROP
   ```

2. **Invalidate Fake Session**:
   ```sql
   DELETE FROM chat_sessions WHERE session_id = 'fake-session-abc';
   ```

3. **Create Alert Rule** (for future):
   ```yaml
   - alert: BruteForceAttack
     expr: |
       sum by(client_ip) (
         rate(audit_failed_requests_total{action_type="UNAUTHORIZED_ACCESS"}[5m])
       ) > 5
     for: 2m
     annotations:
       summary: "Possible brute force attack from {{ $labels.client_ip }}"
   ```

#### Step 8: Post-Incident Report (OpenCost)
```
Attack Summary:
- Duration: 10 minutes (01:55 - 02:05)
- Total requests: 152
- Cost of attack handling: $0.34 (compute: $0.22, storage: $0.12)
- Cost per attack request: $0.0022
```

#### Step 9: Generate Compliance Report
**For SOC 2 auditors**:

```sql
SELECT
  TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as timestamp,
  action,
  ip_address,
  status_code,
  error_message
FROM audit_logs
WHERE ip_address = '10.0.1.123'
ORDER BY created_at;
```

**Export to PDF** → Send to compliance team

---

## 📊 Summary: How Each Tool Helps

| Tool | Primary Purpose | Audit Use Case | Real-World Benefit |
|------|----------------|----------------|-------------------|
| **Grafana** | Visualization | Unified dashboard for all audit data | See security incidents as they happen |
| **Tempo** | Distributed Tracing | Follow a request through the system | Identify bottlenecks, prove audit overhead is low |
| **Prometheus** | Metrics | Quantify audit events (counts, rates, latency) | Prove system performance, enable alerting |
| **Loki** | Log Aggregation | Search audit logs by any field | GDPR compliance, incident investigation |
| **OpenCost** | Cost Tracking | Attribute costs to users/teams | Charge teams for usage, optimize spending |

---

## 🎯 Key Takeaways

1. **Grafana** = Your eyes on the system (visualization)
2. **Tempo** = Your magnifying glass (detailed request tracing)
3. **Prometheus** = Your speedometer (quantitative metrics)
4. **Loki** = Your search engine (log aggregation)
5. **OpenCost** = Your accountant (cost tracking)

**Together**, they provide a **complete observability stack** that makes audit logging not just a compliance checkbox, but a powerful tool for:
- Security incident response
- Performance optimization
- Cost management
- GDPR/SOC 2 compliance
- User behavior analysis

---

## 📖 References

- **Grafana Dashboard**: `http://localhost:3000/d/audit-logs-comprehensive`
- **Prometheus Metrics**: `http://localhost:9090`
- **Loki Logs**: Grafana → Explore → Loki datasource
- **Tempo Traces**: Grafana → Explore → Tempo datasource
- **OpenCost**: `http://localhost:9003`

---

**Document Version**: 1.0
**Last Updated**: 2025-11-28
**Author**: Claude Code AI Assistant

---

**END OF DOCUMENT**
