#!/bin/bash

echo "=============================================="
echo "  Backend Error Diagnostic"
echo "=============================================="
echo ""

echo "Checking if backend container is running..."
if docker ps | grep -q rag-backend; then
    echo "✓ Backend container is running"
else
    echo "✗ Backend container is not running"
    exit 1
fi

echo ""
echo "=== Last 50 Lines of Backend Logs ==="
docker compose logs backend --tail=50

echo ""
echo "=== Filtering for Errors ==="
docker compose logs backend --tail=100 | grep -i "error\|exception\|failed\|traceback" | tail -30

echo ""
echo "=== Checking Imports ==="
docker compose logs backend --tail=200 | grep -i "import\|enhanced\|audit" | tail -20

echo ""
echo "=== Backend Health Status ==="
curl -s http://localhost:8000/health 2>&1 || echo "Backend not responding"

echo ""
