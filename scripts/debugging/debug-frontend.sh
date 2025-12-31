#!/bin/bash

echo "================================"
echo "Frontend Diagnostics"
echo "================================"
echo ""

echo "1. Checking container status..."
docker compose ps frontend
echo ""

echo "2. Checking if port 3001 is accessible..."
curl -I http://localhost:3001 2>&1 | head -5
echo ""

echo "3. Checking frontend logs (last 30 lines)..."
docker compose logs frontend --tail 30
echo ""

echo "4. Checking if node_modules exist..."
docker compose exec frontend ls -la /app/node_modules 2>&1 | head -5
echo ""

echo "5. Checking frontend package.json..."
docker compose exec frontend cat /app/package.json 2>&1 | grep -A 5 "scripts"
echo ""

echo "================================"
echo "Diagnostics complete!"
echo "================================"
