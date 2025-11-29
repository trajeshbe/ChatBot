#!/bin/bash

# Grafana Audit Dashboard - Automated Setup Script
# This script will configure Grafana datasources and import the audit dashboard

set -e

echo "=========================================="
echo "🔧 Grafana Audit Dashboard Setup"
echo "=========================================="
echo ""

# Grafana credentials
GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASS="admin"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper function
check_service() {
    SERVICE=$1
    URL=$2
    echo -n "Checking $SERVICE... "
    if curl -s -f "$URL" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Running${NC}"
        return 0
    else
        echo -e "${RED}✗ Not accessible${NC}"
        return 1
    fi
}

# Step 1: Check prerequisites
echo "Step 1: Checking prerequisites..."
echo ""

check_service "Grafana" "$GRAFANA_URL/api/health" || {
    echo -e "${RED}ERROR: Grafana is not running${NC}"
    echo "Start with: docker-compose up -d grafana"
    exit 1
}

check_service "Prometheus" "http://localhost:9090/api/v1/status/config" || {
    echo -e "${YELLOW}WARNING: Prometheus is not running${NC}"
    echo "Continuing anyway, but metrics won't work until Prometheus is started"
}

check_service "Loki" "http://localhost:3100/ready" || {
    echo -e "${YELLOW}WARNING: Loki is not running${NC}"
    echo "Continuing anyway, but logs won't work until Loki is started"
}

echo ""

# Step 2: Configure Prometheus datasource
echo "Step 2: Configuring Prometheus datasource..."

PROM_DS_ID=$(curl -s -u $GRAFANA_USER:$GRAFANA_PASS \
  "$GRAFANA_URL/api/datasources" | \
  jq -r '.[] | select(.type=="prometheus") | .id')

if [ -n "$PROM_DS_ID" ]; then
    echo "Updating existing Prometheus datasource (ID: $PROM_DS_ID)..."
    curl -s -X PUT \
      -u $GRAFANA_USER:$GRAFANA_PASS \
      -H "Content-Type: application/json" \
      "$GRAFANA_URL/api/datasources/$PROM_DS_ID" \
      -d '{
        "id": '"$PROM_DS_ID"',
        "name": "prometheus",
        "type": "prometheus",
        "url": "http://prometheus:9090",
        "access": "proxy",
        "isDefault": true,
        "jsonData": {}
      }' > /dev/null
    echo -e "${GREEN}✓ Prometheus datasource updated${NC}"
else
    echo "Creating new Prometheus datasource..."
    curl -s -X POST \
      -u $GRAFANA_USER:$GRAFANA_PASS \
      -H "Content-Type: application/json" \
      "$GRAFANA_URL/api/datasources" \
      -d '{
        "name": "prometheus",
        "type": "prometheus",
        "url": "http://prometheus:9090",
        "access": "proxy",
        "isDefault": true,
        "jsonData": {}
      }' > /dev/null
    echo -e "${GREEN}✓ Prometheus datasource created${NC}"
fi

echo ""

# Step 3: Configure Loki datasource
echo "Step 3: Configuring Loki datasource..."

LOKI_DS_ID=$(curl -s -u $GRAFANA_USER:$GRAFANA_PASS \
  "$GRAFANA_URL/api/datasources" | \
  jq -r '.[] | select(.type=="loki") | .id')

if [ -n "$LOKI_DS_ID" ]; then
    echo "Loki datasource already exists (ID: $LOKI_DS_ID)"
    echo -e "${GREEN}✓ Loki datasource already configured${NC}"
else
    echo "Creating new Loki datasource..."
    curl -s -X POST \
      -u $GRAFANA_USER:$GRAFANA_PASS \
      -H "Content-Type: application/json" \
      "$GRAFANA_URL/api/datasources" \
      -d '{
        "name": "loki",
        "type": "loki",
        "url": "http://loki:3100",
        "access": "proxy",
        "jsonData": {}
      }' > /dev/null
    echo -e "${GREEN}✓ Loki datasource created${NC}"
fi

echo ""

# Step 4: Configure Tempo datasource (optional)
echo "Step 4: Configuring Tempo datasource..."

TEMPO_DS_ID=$(curl -s -u $GRAFANA_USER:$GRAFANA_PASS \
  "$GRAFANA_URL/api/datasources" | \
  jq -r '.[] | select(.type=="tempo") | .id')

if [ -n "$TEMPO_DS_ID" ]; then
    echo "Tempo datasource already exists (ID: $TEMPO_DS_ID)"
    echo -e "${GREEN}✓ Tempo datasource already configured${NC}"
else
    echo "Creating new Tempo datasource..."
    curl -s -X POST \
      -u $GRAFANA_USER:$GRAFANA_PASS \
      -H "Content-Type: application/json" \
      "$GRAFANA_URL/api/datasources" \
      -d '{
        "name": "tempo",
        "type": "tempo",
        "url": "http://tempo:3200",
        "access": "proxy",
        "jsonData": {}
      }' > /dev/null 2>&1
    echo -e "${GREEN}✓ Tempo datasource created${NC}"
fi

echo ""

# Step 5: Import the audit dashboard
echo "Step 5: Importing Audit Logs Dashboard..."

DASHBOARD_FILE="observability/grafana/dashboards/audit-logs-dashboard.json"

if [ ! -f "$DASHBOARD_FILE" ]; then
    echo -e "${RED}ERROR: Dashboard file not found: $DASHBOARD_FILE${NC}"
    exit 1
fi

# Read the dashboard JSON and wrap it for import
DASHBOARD_JSON=$(cat "$DASHBOARD_FILE")

# Create the import payload
IMPORT_PAYLOAD=$(jq -n \
  --argjson dashboard "$DASHBOARD_JSON" \
  '{
    dashboard: $dashboard,
    overwrite: true,
    inputs: [
      {
        name: "DS_PROMETHEUS",
        type: "datasource",
        pluginId: "prometheus",
        value: "prometheus"
      },
      {
        name: "DS_LOKI",
        type: "datasource",
        pluginId: "loki",
        value: "loki"
      }
    ]
  }')

# Import the dashboard
IMPORT_RESULT=$(curl -s -X POST \
  -u $GRAFANA_USER:$GRAFANA_PASS \
  -H "Content-Type: application/json" \
  "$GRAFANA_URL/api/dashboards/import" \
  -d "$IMPORT_PAYLOAD")

# Check if import was successful
if echo "$IMPORT_RESULT" | jq -e '.uid' > /dev/null 2>&1; then
    DASHBOARD_UID=$(echo "$IMPORT_RESULT" | jq -r '.uid')
    DASHBOARD_URL=$(echo "$IMPORT_RESULT" | jq -r '.url')
    echo -e "${GREEN}✓ Dashboard imported successfully${NC}"
    echo "  Dashboard UID: $DASHBOARD_UID"
    echo "  Dashboard URL: $GRAFANA_URL$DASHBOARD_URL"
else
    echo -e "${YELLOW}⚠ Dashboard import may have failed${NC}"
    echo "Result: $IMPORT_RESULT"
fi

echo ""

# Step 6: Verify setup
echo "Step 6: Verifying setup..."
echo ""

echo "Datasources configured:"
curl -s -u $GRAFANA_USER:$GRAFANA_PASS \
  "$GRAFANA_URL/api/datasources" | \
  jq -r '.[] | "  - \(.name) (\(.type)) - URL: \(.url)"'

echo ""

# Step 7: Generate test data
echo "Step 7: Generating test audit events..."
echo ""

echo "Making test API requests to generate audit data..."
curl -s http://localhost:8000/health > /dev/null && echo "  ✓ Health check"
curl -s http://localhost:8000/api/v1/documents > /dev/null && echo "  ✓ List documents"
curl -s -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query":"test"}' > /dev/null 2>&1 && echo "  ✓ Query endpoint (test)"

echo ""

# Wait a moment for data to be collected
echo "Waiting 5 seconds for metrics to be scraped..."
sleep 5

echo ""

# Step 8: Final instructions
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Access your Audit Logs Dashboard:"
echo ""
echo "  🔗 Dashboard URL:"
echo "     http://localhost:3000/d/audit-logs-comprehensive"
echo ""
echo "  🔐 Login credentials:"
echo "     Username: admin"
echo "     Password: admin"
echo ""
echo "What you should see:"
echo "  1. Requests by User Role (Pie Chart)"
echo "  2. Total Audit Events (Gauge)"
echo "  3. User Actions Over Time (Time Series)"
echo "  4. Request Latency by Endpoint (Time Series)"
echo "  5. HTTP Status Codes (Stacked Bars)"
echo "  6. Failed Requests (Table)"
echo "  7. Audit Log Stream (Logs Panel - from Loki)"
echo ""
echo "If panels show 'No data':"
echo "  - Wait 30-60 seconds for Prometheus to scrape metrics"
echo "  - Make more API requests to generate data"
echo "  - Check time range (use 'Last 6 hours' or 'Last 24 hours')"
echo ""
echo "Troubleshooting:"
echo "  - Run: bash verify_grafana_setup.sh"
echo "  - Check logs: docker-compose logs grafana"
echo "  - Restart: docker-compose restart grafana prometheus loki"
echo ""
echo "=========================================="
