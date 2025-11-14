#!/bin/bash
echo "Checking backend startup logs..."
echo ""
docker compose logs backend --tail=100 | grep -A 5 -B 5 -i "error\|exception\|traceback\|failed" | tail -50
