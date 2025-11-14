#!/bin/bash

echo "=========================================="
echo "  Check Upload Endpoint Logs"
echo "=========================================="
echo ""

echo "Checking last 200 lines of backend logs for upload activity..."
echo ""

docker compose logs backend --tail=200 2>&1 | grep -i "upload\|document\|processing\|error\|exception" | grep -v "opentelemetry\|tempo:4317" | tail -50
