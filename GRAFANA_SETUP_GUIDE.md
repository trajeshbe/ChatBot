# Grafana Setup Guide for Audit Logging

**Quick Setup**: Follow these steps to see your audit logging dashboard in Grafana.

---

## Step 1: Access Grafana

1. Open your browser and go to:
   ```
   http://localhost:3000
   ```

2. **Login credentials**:
   - Username: `admin`
   - Password: `admin`

   (You may be asked to change the password - you can skip this)

---

## Step 2: Configure Datasources

### 2.1: Configure Prometheus (Metrics)

1. In Grafana, click the **☰ menu** (top left)
2. Go to **Connections** → **Data sources**
3. Click on the existing **prometheus** datasource
4. Set the **URL** to:
   ```
   http://prometheus:9090
   ```
5. Scroll down and click **Save & test**
6. You should see: ✅ "Data source is working"

### 2.2: Add Loki (Logs)

1. Click **Add new data source** (top right)
2. Search for and select **Loki**
3. Configure:
   - **Name**: `loki`
   - **URL**: `http://loki:3100`
4. Click **Save & test**
5. You should see: ✅ "Data source successfully connected"

### 2.3: Add Tempo (Traces) - Optional

1. Click **Add new data source**
2. Search for and select **Tempo**
3. Configure:
   - **Name**: `tempo`
   - **URL**: `http://tempo:3200`
4. Click **Save & test**
5. You should see: ✅ "Data source is working"

---

## Step 3: Import the Audit Logging Dashboard

### Method 1: Via Grafana UI (Recommended)

1. Click the **☰ menu** (top left)
2. Go to **Dashboards**
3. Click **New** → **Import**
4. Click **Upload JSON file**
5. Select the file:
   ```
   observability/grafana/dashboards/audit-logs-dashboard.json
   ```
6. On the import page:
   - **Dashboard name**: Keep as "Comprehensive Audit Logs Dashboard"
   - **Prometheus datasource**: Select `prometheus`
   - **Loki datasource**: Select `loki`
7. Click **Import**

### Method 2: Via API

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -u admin:admin \
  http://localhost:3000/api/dashboards/db \
  -d @observability/grafana/dashboards/audit-logs-dashboard.json
```

---

## Step 4: View the Dashboard

1. Click the **☰ menu** (top left)
2. Go to **Dashboards**
3. You should see **"Comprehensive Audit Logs Dashboard"**
4. Click on it to view

**Or use direct URL**:
```
http://localhost:3000/d/audit-logs-comprehensive
```

---

## Step 5: Verify Data is Flowing

### Check Prometheus Metrics

1. In Grafana, click **☰ menu** → **Explore**
2. Select **prometheus** datasource
3. Run this query:
   ```promql
   audit_requests_total
   ```
4. You should see metrics data

**If no data**: The audit middleware may not have recorded any metrics yet. Generate some activity:
```bash
# Make a few API requests
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/documents
```

Then refresh Grafana.

### Check Loki Logs

1. In Grafana **Explore**, select **loki** datasource
2. Run this query:
   ```logql
   {job="backend"} |= "AUDIT_EVENT"
   ```
3. You should see audit log entries

**If no data**: Check that logs are being generated:
```bash
docker-compose logs backend | grep "AUDIT_EVENT"
```

---

## Troubleshooting

### Issue: "Data source is not working"

**Prometheus**:
```bash
# Check if Prometheus is running
docker-compose ps prometheus

# Test Prometheus endpoint
curl http://localhost:9090/api/v1/status/config
```

**Loki**:
```bash
# Check if Loki is running
docker-compose ps loki

# Test Loki endpoint
curl http://localhost:3100/ready
```

**Solution**: If containers are not running, start them:
```bash
docker-compose up -d prometheus loki tempo
```

### Issue: "No data in dashboard panels"

**Check 1**: Is Prometheus scraping the backend?
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.scrapePool=="backend")'
```

**Check 2**: Are audit metrics being exported?
```bash
# Check backend metrics endpoint
curl http://localhost:8000/metrics | grep audit_
```

**If no audit metrics**: The `/metrics` endpoint might not be configured. We can fix this.

**Check 3**: Time range - make sure dashboard time range is set to "Last 6 hours" or "Last 24 hours"

### Issue: "Panel has error: 'Failed to query data'"

**Check the datasource URLs**:
1. Go to **Connections** → **Data sources**
2. Click on **prometheus**
3. Make sure URL is: `http://prometheus:9090`
4. Click **Save & test**

Do the same for **loki**: `http://loki:3100`

---

## Quick Verification Steps

Run this script to verify everything:

```bash
#!/bin/bash
echo "=== Grafana Setup Verification ==="
echo ""

# 1. Check Grafana
echo "1. Grafana:"
curl -s http://localhost:3000/api/health | jq -r '.version' && echo "   ✓ Grafana is running" || echo "   ✗ Grafana is not accessible"
echo ""

# 2. Check Prometheus
echo "2. Prometheus:"
curl -s http://localhost:9090/api/v1/status/config > /dev/null && echo "   ✓ Prometheus is running" || echo "   ✗ Prometheus is not accessible"
echo ""

# 3. Check Loki
echo "3. Loki:"
curl -s http://localhost:3100/ready && echo "   ✓ Loki is running" || echo "   ✗ Loki is not accessible"
echo ""

# 4. Check Tempo (optional)
echo "4. Tempo:"
curl -s http://localhost:3200/ready && echo "   ✓ Tempo is running" || echo "   ✗ Tempo is not accessible"
echo ""

# 5. Check datasources in Grafana
echo "5. Grafana Datasources:"
curl -s -u admin:admin http://localhost:3000/api/datasources | jq -r '.[] | "   - \(.name) (\(.type)) - \(.url)"'
echo ""

# 6. Check audit metrics
echo "6. Audit Metrics:"
METRICS=$(curl -s http://localhost:8000/metrics | grep -c "audit_" || echo "0")
echo "   Found $METRICS audit metric families"
echo ""

# 7. Check audit logs
echo "7. Audit Logs:"
LOGS=$(docker-compose logs backend --tail=100 2>&1 | grep -c "AUDIT_EVENT" || echo "0")
echo "   Found $LOGS AUDIT_EVENT log entries"
echo ""

echo "=== Setup Complete ==="
```

Save this as `verify_grafana_setup.sh` and run:
```bash
bash verify_grafana_setup.sh
```

---

## What You Should See

Once everything is configured, your **Comprehensive Audit Logs Dashboard** will show:

### Panel 1: Requests by User Role (Pie Chart)
- Shows distribution of requests by user role
- Currently might show "unknown" for unauthenticated requests

### Panel 2: Total Audit Events (Gauge)
- Total number of API requests logged
- Should show increasing numbers

### Panel 3: User Actions Over Time (Time Series)
- Line graph showing action types over time
- Should show spikes when you use the API

### Panel 4: Request Latency by Endpoint (Time Series)
- P95 latency for each endpoint
- Should show most endpoints under 100ms

### Panel 5: HTTP Status Codes (Stacked Bars)
- Green: 2xx (success)
- Orange: 4xx (client errors)
- Red: 5xx (server errors)

### Panel 6: Failed Requests (Table)
- Top 10 failed requests with error details

### Panel 7: Audit Log Stream (Logs Panel)
- Real-time stream of audit events from Loki
- Click on any log entry to see full JSON

---

## Next Steps

After setup:

1. **Generate some activity**:
   ```bash
   # Upload a document
   curl -X POST http://localhost:8000/api/v1/upload \
     -F "file=@test_document.txt"

   # Query documents
   curl http://localhost:8000/api/v1/documents

   # Make a chat query
   curl -X POST http://localhost:8000/api/v1/query \
     -H "Content-Type: application/json" \
     -d '{"query": "test", "session_id": "test-session"}'
   ```

2. **Refresh the dashboard** - you should see the metrics update

3. **Explore the data**:
   - Click on any panel title → **Edit**
   - See the PromQL/LogQL queries
   - Modify and experiment

4. **Set up alerts** (optional):
   - Click on a panel → **Alert** tab
   - Create alert rules for security events

---

## Alternative: View Audit Data Without Grafana

If you prefer not to use Grafana right now, you can still access audit data:

### 1. View Logs Directly
```bash
docker-compose logs backend | grep "AUDIT_EVENT" | tail -20
```

### 2. Query PostgreSQL
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT action, status_code, latency_ms, ip_address, created_at
   FROM audit_logs
   ORDER BY created_at DESC
   LIMIT 10;"
```

### 3. Query Prometheus Directly
```bash
# Total requests
curl -s 'http://localhost:9090/api/v1/query?query=audit_requests_total' | jq .

# Request rate
curl -s 'http://localhost:9090/api/v1/query?query=rate(audit_requests_total[5m])' | jq .
```

### 4. Query Loki Directly
```bash
curl -G -s 'http://localhost:3100/loki/api/v1/query' \
  --data-urlencode 'query={job="backend"} |= "AUDIT_EVENT"' \
  --data-urlencode 'limit=10' | jq .
```

---

## Need Help?

If you still have issues:

1. **Check all containers are running**:
   ```bash
   docker-compose ps
   ```

2. **Check container logs**:
   ```bash
   docker-compose logs grafana
   docker-compose logs prometheus
   docker-compose logs loki
   ```

3. **Restart the observability stack**:
   ```bash
   docker-compose restart grafana prometheus loki tempo
   ```

4. **Full restart** (if needed):
   ```bash
   docker-compose down
   docker-compose up -d
   ```

---

**Quick Summary**:
1. Login to Grafana: `http://localhost:3000` (admin/admin)
2. Configure Prometheus datasource URL: `http://prometheus:9090`
3. Add Loki datasource: `http://loki:3100`
4. Import dashboard: Upload `observability/grafana/dashboards/audit-logs-dashboard.json`
5. View dashboard: `http://localhost:3000/d/audit-logs-comprehensive`

---

**Document Version**: 1.0
**Last Updated**: 2025-11-28
