#!/bin/bash

echo "Checking backend logs for errors..."
echo "=================================="
docker compose logs backend --tail 100 | grep -i "error\|exception\|traceback" || echo "No obvious errors in last 100 lines"

echo ""
echo "Full backend startup logs:"
echo "=================================="
docker compose logs backend --tail 50
