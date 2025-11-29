#!/bin/bash
echo "=== Testing Prometheus & Promtail Setup ==="
echo ""

# Generate some audit events
echo "1. Generating audit events..."
curl -s http://localhost:8000/health > /dev/null && echo "   ✓ Health check"
curl -s http://localhost:8000/api/v1/documents > /dev/null && echo "   ✓ List documents"
echo ""

# Wait for metrics
echo "2. Waiting 3 seconds for metrics..."
sleep 3

# Test /metrics endpoint
echo "3. Testing /metrics endpoint..."
METRICS_COUNT=$(curl -s http://localhost:8000/metrics | grep -c "audit_" || echo "0")
if [ "$METRICS_COUNT" -gt 0 ]; then
    echo "   ✅ SUCCESS! Found $METRICS_COUNT audit metric families"
    echo ""
    echo "   Sample metrics:"
    curl -s http://localhost:8000/metrics | grep "^audit_" | head -10 | sed 's/^/   /'
else
    echo "   ⚠️  No audit metrics found yet"
fi
echo ""

# Test Prometheus is scraping
echo "4. Testing Prometheus scraping..."
sleep 15  # Wait for first scrape
PROM_STATUS=$(curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | select(.scrapePool=="backend") | .health' 2>/dev/null || echo "unknown")
if [ "$PROM_STATUS" = "up" ]; then
    echo "   ✅ Prometheus is scraping backend (status: $PROM_STATUS)"
else
    echo "   ⚠️  Prometheus scraping status: $PROM_STATUS"
fi
echo ""

# Test Promtail is sending logs to Loki
echo "5. Testing Promtail → Loki pipeline..."
LOKI_LOGS=$(curl -G -s 'http://localhost:3100/loki/api/v1/query' \
  --data-urlencode 'query={job="backend"} |= "AUDIT_EVENT"' \
  --data-urlencode 'limit=1' | jq -r '.data.result | length' 2>/dev/null || echo "0")
if [ "$LOKI_LOGS" -gt 0 ]; then
    echo "   ✅ SUCCESS! Audit events found in Loki"
else
    echo "   ⚠️  No audit events in Loki yet (Promtail may need more time)"
fi
echo ""

echo "=========================================="
echo "Summary:"
echo "=========================================="
echo ""
echo "Services Status:"
docker-compose ps --format "  - {{.Service}}: {{.Status}}" | grep -E "prometheus|promtail|loki|grafana"
echo ""

echo "Access URLs:"
echo "  - Grafana Dashboard: http://localhost:3000/d/audit-logs-comprehensive"
echo "  - Prometheus: http://localhost:9090"
echo "  - Backend Metrics: http://localhost:8000/metrics"
echo ""

echo "Next: Open Grafana and refresh the dashboard!"
echo ""
