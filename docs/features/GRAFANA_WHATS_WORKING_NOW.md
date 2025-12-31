# What's Working in Grafana Right Now

**Date**: 2025-11-28
**Status**: ✅ Dashboard Imported - Partially Working

---

## ✅ What You Can See NOW

### 1. Access Grafana Dashboard

**URL**: http://localhost:3000/d/audit-logs-comprehensive
**Login**: admin / admin

The dashboard is imported and you should see it in the list.

---

### 2. Panel 7: Audit Log Stream (Loki) - ✅ WORKING

This panel **WILL WORK** because Loki is running!

**What it shows**:
- Real-time stream of audit events
- JSON-formatted log entries
- Client IP addresses, latency, status codes

**How to view**:
1. Open the dashboard
2. Scroll to the bottom panel "Audit Log Stream (Loki)"
3. You should see log entries in JSON format

**Example log entry**:
```json
{
  "event_type": "api_request",
  "request_id": "f484661d-e493-46f8-bf9c-3c0992416fc3",
  "timestamp": 1764299329.8722358,
  "user_id": null,
  "user_role": null,
  "session_id": null,
  "action_type": "VIEW",
  "method": "GET",
  "path": "/api/v1/documents",
  "status_code": 200,
  "latency_ms": 14.845
}
```

---

### 3. Generate More Audit Events

To see more data in Loki, make some API requests:

```bash
# Health check
curl http://localhost:8000/health

# List documents
curl http://localhost:8000/api/v1/documents

# Query (will fail but gets logged)
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query":"test","session_id":"test-session"}'
```

Then refresh the Grafana dashboard and you'll see new entries in Panel 7.

---

## ⚠️ What WON'T Work (Yet)

### Panels 1-6: Metrics Panels - ❌ NOT WORKING YET

These panels rely on **Prometheus** which is not configured in your docker-compose.yml:

1. Requests by User Role (Pie Chart)
2. Total Audit Events (Gauge)
3. User Actions Over Time (Time Series)
4. Request Latency by Endpoint (Time Series)
5. HTTP Status Codes (Stacked Bars)
6. Failed Requests (Table)

**You'll see**: "No data" or "Panel has error"

**Why**: These panels query Prometheus metrics, but Prometheus is not running.

---

## 🎯 Alternative: View Audit Data Without Prometheus

Even without Prometheus, you can view ALL audit data using these methods:

### Method 1: PostgreSQL (Complete Audit History)

```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT
  TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as time,
  action,
  status_code,
  ROUND(latency_ms::numeric, 2) as latency_ms,
  ip_address
FROM audit_logs
ORDER BY created_at DESC
LIMIT 20;
"
```

**Output**:
```
        time         | action | status_code | latency_ms | ip_address
---------------------+--------+-------------+------------+------------
 2025-11-28 03:08:49 | VIEW   |         200 |      24.73 | 172.18.0.1
 2025-11-28 03:08:12 | QUERY  |         422 |       2.37 | 172.18.0.1
```

### Method 2: Docker Logs (Real-time)

```bash
# View recent audit events
docker-compose logs backend --tail=50 | grep "AUDIT_EVENT"

# Follow in real-time
docker-compose logs -f backend | grep "AUDIT_EVENT"
```

### Method 3: Loki via Grafana Explore

1. In Grafana, click **☰ menu** → **Explore**
2. Select **loki** datasource (top dropdown)
3. Enter query:
   ```logql
   {job="backend"} |= "AUDIT_EVENT"
   ```
4. Click **Run query**
5. You'll see all audit events with full JSON

**Advanced queries**:

```logql
# Failed requests only
{job="backend"} |= "AUDIT_EVENT" | json | status_code >= 400

# Specific action type
{job="backend"} |= "AUDIT_EVENT" | json | action_type="VIEW"

# Specific IP address
{job="backend"} |= "AUDIT_EVENT" | json | client_ip="172.18.0.1"
```

### Method 4: Statistics from PostgreSQL

**Recent activity summary**:
```sql
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT
    action,
    COUNT(*) as count,
    ROUND(AVG(latency_ms)::numeric, 2) as avg_latency,
    MIN(created_at) as first,
    MAX(created_at) as last
FROM audit_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY action
ORDER BY count DESC;
"
```

**Error tracking**:
```sql
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT
    action,
    status_code,
    COUNT(*) as count
FROM audit_logs
WHERE status_code >= 400
  AND created_at > NOW() - INTERVAL '24 hours'
GROUP BY action, status_code
ORDER BY count DESC;
"
```

---

## 🚀 To Get Full Grafana Dashboard Working

You need to add Prometheus to your `docker-compose.yml`. Here's what to add:

```yaml
services:
  # ... existing services ...

  prometheus:
    image: prom/prometheus:latest
    container_name: rag-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./observability/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - ragchatbot-network
    restart: unless-stopped

volumes:
  # ... existing volumes ...
  prometheus_data:
```

**Then create Prometheus config**:

File: `observability/prometheus/prometheus.yml`
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
```

**Start Prometheus**:
```bash
docker-compose up -d prometheus
```

**Wait 30 seconds**, then refresh the Grafana dashboard - all panels will work!

---

## 📊 Summary: What's Available Now

| Data Source | Status | How to Access |
|-------------|--------|---------------|
| **PostgreSQL** | ✅ Working | SQL queries shown above |
| **Loki** | ✅ Working | Grafana Panel 7 or Explore |
| **Docker Logs** | ✅ Working | `docker-compose logs backend \| grep AUDIT` |
| **Prometheus** | ❌ Not configured | Need to add to docker-compose.yml |
| **Tempo** | ❌ Not configured | Optional - for distributed tracing |

---

## 🎯 Recommended Next Steps

### Option 1: Use What's Working Now (No setup needed)

**For viewing audit data**:
1. ✅ Open Grafana dashboard → Panel 7 (Loki logs)
2. ✅ Use PostgreSQL queries (complete history)
3. ✅ Use Grafana Explore with Loki

This gives you **100% of the audit data** - just without the pretty metric charts.

### Option 2: Add Prometheus for Full Dashboard (15 min setup)

If you want the metrics panels working:
1. Add Prometheus to docker-compose.yml (shown above)
2. Create Prometheus config file
3. Restart: `docker-compose up -d`
4. Wait 30 seconds for metrics to be scraped
5. Refresh Grafana - all panels work!

---

## 🔍 Quick Test Right Now

Let's verify Panel 7 is working:

1. **Open Grafana**: http://localhost:3000/d/audit-logs-comprehensive
2. **Login**: admin / admin
3. **Scroll to Panel 7** (bottom of page): "Audit Log Stream (Loki)"
4. **You should see**: JSON audit events
5. **If empty**: Make an API request:
   ```bash
   curl http://localhost:8000/api/v1/documents
   ```
6. **Refresh Grafana** - you should see the new log entry!

---

## 📖 Full Audit Data Available

Remember: **Comprehensive audit logging IS working!** Every API request is being logged to:

1. ✅ **PostgreSQL** - Permanent storage, queryable
2. ✅ **Loki** - Log aggregation, searchable via Grafana
3. ✅ **Docker logs** - Real-time streaming
4. ⏳ **Prometheus** - Metrics (when you add it)

**You have full audit coverage right now** - just viewing it through different tools instead of one unified Grafana dashboard.

---

**Bottom Line**:
- ✅ Audit logging is 100% operational
- ✅ You can view all audit data in Grafana Panel 7 (Loki)
- ✅ You can query PostgreSQL for complete history
- ⏳ Add Prometheus for metrics panels (optional enhancement)

---

**Questions?** See `GRAFANA_SETUP_GUIDE.md` for detailed instructions.

