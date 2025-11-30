#!/bin/bash
echo "=== Testing Grafana Panel 7 (Loki Audit Logs) ==="
echo ""

# Generate audit events
echo "1. Generating audit events..."
curl -s http://localhost:8000/health > /dev/null && echo "   ✓ Health check"
curl -s http://localhost:8000/api/v1/documents > /dev/null && echo "   ✓ List documents"
echo ""

# Wait for logs
echo "2. Waiting 2 seconds for logs..."
sleep 2

# Check Loki directly
echo "3. Checking Loki for audit events..."
RESULT=$(curl -G -s 'http://localhost:3100/loki/api/v1/query' \
  --data-urlencode 'query={job="backend"} |= "AUDIT_EVENT"' \
  --data-urlencode 'limit=3' | jq -r '.data.result[0].values[]?[1]' 2>/dev/null | head -3)

if [ -n "$RESULT" ]; then
    echo "   ✅ SUCCESS! Found audit events in Loki:"
    echo ""
    echo "$RESULT" | while read line; do
        echo "   $line" | jq -C '.' 2>/dev/null || echo "   $line"
    done
else
    echo "   ⚠️  No audit events found in Loki yet"
    echo "   This might be because:"
    echo "   - Promtail is not running (sends logs to Loki)"
    echo "   - Or logs haven't been ingested yet"
fi

echo ""
echo "4. Checking Docker logs directly..."
DOCKER_LOGS=$(docker-compose logs backend --tail=5 2>&1 | grep -c "AUDIT_EVENT" || echo "0")
echo "   Found $DOCKER_LOGS AUDIT_EVENT entries in Docker logs"

echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "1. Open Grafana:"
echo "   http://localhost:3000/d/audit-logs-comprehensive"
echo ""
echo "2. Login: admin / admin"
echo ""
echo "3. Scroll to Panel 7 (bottom): 'Audit Log Stream'"
echo ""
echo "4. If you see audit events in Loki above, they should"
echo "   appear in Panel 7 of Grafana!"
echo ""
echo "5. If Panel 7 is empty, check:"
echo "   - Time range (set to 'Last 6 hours')"
echo "   - Promtail container: docker-compose ps promtail"
echo ""
