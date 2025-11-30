#!/bin/bash
echo "=== COMPREHENSIVE AUDIT LOGGING TEST ==="
echo ""

# Test 1: Generate audit events
echo "Test 1: Generating audit events..."
curl -s http://localhost:8000/health > /dev/null
curl -s http://localhost:8000/api/v1/documents > /dev/null
echo "✓ Audit events generated"
echo ""

sleep 2

# Test 2: Check logs
echo "Test 2: Checking structured logs..."
LOG_COUNT=$(docker-compose logs backend --tail=100 2>&1 | grep -c "AUDIT_EVENT")
echo "✓ Found $LOG_COUNT AUDIT_EVENT logs"
echo ""

# Test 3: Check database
echo "Test 3: Checking PostgreSQL storage..."
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c \
  "SELECT COUNT(*) as recent_audits FROM audit_logs WHERE created_at > NOW() - INTERVAL '10 minutes';"
echo ""

# Test 4: Check action types
echo "Test 4: Checking ActionType enum..."
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c \
  "SELECT COUNT(*) as total_action_types FROM pg_enum WHERE enumtypid = 'actiontype'::regtype;"
echo ""

# Test 5: Sample audit logs
echo "Test 5: Sample recent audit logs..."
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c \
  "SELECT action, status_code, ROUND(latency_ms::numeric, 2) as latency, ip_address 
   FROM audit_logs 
   WHERE created_at > NOW() - INTERVAL '10 minutes' 
   ORDER BY created_at DESC LIMIT 5;"
echo ""

# Test 6: Check documentation
echo "Test 6: Checking documentation..."
if [ -f "docs/features/COMPREHENSIVE_AUDIT_LOGGING_COMPLETE.md" ]; then
    echo "✓ Implementation doc exists ($(wc -l < docs/features/COMPREHENSIVE_AUDIT_LOGGING_COMPLETE.md) lines)"
fi
if [ -f "docs/future_enhancements/AUDIT_LOGGING_ENHANCEMENTS.md" ]; then
    echo "✓ Future enhancements doc exists ($(wc -l < docs/future_enhancements/AUDIT_LOGGING_ENHANCEMENTS.md) lines)"
fi
echo ""

# Test 7: Check Grafana dashboard
echo "Test 7: Checking Grafana dashboard..."
if [ -f "observability/grafana/dashboards/audit-logs-dashboard.json" ]; then
    PANELS=$(jq '.panels | length' observability/grafana/dashboards/audit-logs-dashboard.json 2>/dev/null)
    echo "✓ Grafana dashboard exists with $PANELS panels"
fi
echo ""

echo "=== ALL TESTS COMPLETE ==="
