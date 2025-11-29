# Audit Logging - Quick Reference Guide

> **Quick access guide for the comprehensive audit logging system**

---

## 🚀 Access Grafana Dashboard

### Dashboard URL
```
http://localhost:3000/d/audit-logs-comprehensive
```

### Default Login
- **Username**: `admin`
- **Password**: `admin`

---

## 📊 What You'll See in the Dashboard

The dashboard has **7 panels** showing different aspects of audit data:

1. **Requests by User Role** - Who's using the system (admin/user/anonymous)
2. **Total Audit Events** - Total number of tracked requests
3. **User Actions Over Time** - Activity trends
4. **Request Latency** - Performance monitoring
5. **HTTP Status Codes** - Success/error rates
6. **Failed Requests** - Top problematic endpoints
7. **Audit Log Stream** - Real-time log feed

---

## ✅ Quick Start - See Data NOW

The system just started, so you need to **generate some activity** first:

```bash
# Run these commands to create audit events:
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/documents
curl http://localhost:8000/api/v1/sessions
curl http://localhost:8000/api/v1/health

# Wait 15 seconds for Prometheus to scrape
sleep 15

# Now open Grafana and you'll see data!
```

**Then**:
1. Open http://localhost:3000
2. Login with `admin` / `admin`
3. Click on "Dashboards" → "Comprehensive Audit Logs Dashboard"
4. You should now see metrics!

---

## 🔍 Verify Everything is Working

```bash
# 1. Check services are running
docker-compose ps | grep -E "prometheus|promtail|loki|grafana"

# 2. Check backend has metrics
curl http://localhost:8000/metrics | grep audit_

# 3. Check Prometheus has data
curl -s 'http://localhost:9090/api/v1/query?query=audit_requests_total' | jq '.data.result | length'
# Should return a number > 0

# 4. Check Loki has logs (may take 1-2 minutes)
curl -G -s 'http://localhost:3100/loki/api/v1/query' \
  --data-urlencode 'query={job="backend"} |= "AUDIT_EVENT"' | jq '.data.result | length'
```

---

## 🗄️ View Data Directly in PostgreSQL

```bash
# Connect to database
docker-compose exec postgres psql -U postgres -d ragchatbot

# See recent audit events
SELECT 
    TO_CHAR(created_at, 'HH24:MI:SS') as time,
    action, 
    status_code,
    ROUND(latency_ms::numeric, 2) as latency_ms
FROM audit_logs 
ORDER BY created_at DESC 
LIMIT 10;
```

**For 30+ useful SQL queries**, see: `docs/SQL_AUDIT_QUERIES_REFERENCE.md`

---

## 🐛 Troubleshooting

### "No data" in Grafana Dashboard

**Most common cause**: No API requests made yet!

**Solution**: 
```bash
# Generate test events
for i in {1..10}; do 
  curl -s http://localhost:8000/api/v1/documents > /dev/null
  curl -s http://localhost:8000/health > /dev/null
done

# Wait 15 seconds
sleep 15

# Refresh Grafana dashboard
```

### Prometheus panels show "No data"

1. Check Prometheus is scraping:
   ```bash
   curl http://localhost:9090/targets
   ```
   Look for `backend` target with state "UP"

2. Check backend /metrics endpoint:
   ```bash
   curl http://localhost:8000/metrics | head -20
   ```

3. Restart Prometheus:
   ```bash
   docker-compose restart prometheus
   ```

### Logs panel is empty

Promtail can take 30-60 seconds to start shipping logs to Loki.

**Solution**: Wait a bit longer, or check Promtail status:
```bash
docker-compose logs promtail | tail -20
```

---

## 📚 All Documentation

| Document | Purpose |
|----------|---------|
| `AUDIT_LOGGING_QUICK_REFERENCE.md` | This file - quick start |
| `COMPREHENSIVE_AUDIT_LOGGING_COMPLETE.md` | Full implementation details |
| `SQL_AUDIT_QUERIES_REFERENCE.md` | 30+ SQL query examples |
| `OBSERVABILITY_TOOLS_FOR_AUDIT_LOGGING.md` | How Grafana/Tempo/Loki help |
| `COMPREHENSIVE_AUDIT_LOGGING_TEST_RESULTS.md` | Test results (8/8 passed) |

All in `docs/features/` and `docs/`

---

## 🔗 Quick Links

- **Grafana Dashboard**: http://localhost:3000/d/audit-logs-comprehensive
- **Prometheus**: http://localhost:9090
- **Backend Metrics**: http://localhost:8000/metrics
- **API Docs**: http://localhost:8000/docs

---

**Last Updated**: 2025-11-28  
**Status**: ✅ All services operational
