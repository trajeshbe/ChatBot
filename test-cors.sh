#!/bin/bash

echo "=== Testing CORS Configuration ==="
echo ""

echo "1. Testing OPTIONS preflight request (CORS check):"
curl -X OPTIONS http://localhost:8000/api/v1/query \
  -H "Origin: http://localhost:3001" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -i

echo ""
echo ""
echo "2. Testing actual POST request with CORS:"
curl -X POST http://localhost:8000/api/v1/query \
  -H "Origin: http://localhost:3001" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "query=hello&use_cache=false" \
  -i

echo ""
echo ""
echo "3. Checking backend health:"
curl http://localhost:8000/health

echo ""
echo ""
echo "4. Checking backend logs for CORS configuration:"
docker compose logs backend --tail 50 | grep -i "cors\|startup\|origin"
