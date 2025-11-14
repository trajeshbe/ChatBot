#!/bin/bash

echo "=============================================="
echo "  Enterprise RAG Chatbot - Service Validator"
echo "=============================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success_count=0
fail_count=0

check_service() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}

    echo -n "Checking $name... "

    response_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)

    if [ "$response_code" = "$expected_code" ] || [ "$response_code" = "200" ]; then
        echo -e "${GREEN}✅ OK${NC} (HTTP $response_code)"
        ((success_count++))
        return 0
    else
        echo -e "${RED}❌ FAILED${NC} (HTTP $response_code)"
        ((fail_count++))
        return 1
    fi
}

echo "=== Primary Interfaces ==="
check_service "Frontend UI          " "http://localhost:3001" "200"
check_service "Backend API Docs     " "http://localhost:8000/api/docs" "200"
check_service "GraphQL Playground   " "http://localhost:8000/graphql" "200"

# Health check with JSON validation
echo -n "Checking Backend Health... "
health_response=$(curl -s http://localhost:8000/health 2>/dev/null)
if echo "$health_response" | grep -q "healthy"; then
    echo -e "${GREEN}✅ OK${NC} - System Healthy"
    ((success_count++))
else
    echo -e "${RED}❌ FAILED${NC} - Not responding"
    ((fail_count++))
fi

echo ""
echo "=== Monitoring & Admin ==="
check_service "Grafana Dashboard    " "http://localhost:3000" "302"
check_service "MinIO Console        " "http://localhost:9001" "200"
check_service "Redis Insight        " "http://localhost:8002" "200"
check_service "Prefect UI           " "http://localhost:4200" "200"
check_service "Flink Dashboard      " "http://localhost:8081" "200"
check_service "Envoy Admin          " "http://localhost:9901" "200"

echo ""
echo "=== Backend Services ==="

# Redis connectivity
echo -n "Checking Redis... "
if docker exec rag-redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
    echo -e "${GREEN}✅ OK${NC} - Redis responding"
    ((success_count++))
else
    echo -e "${RED}❌ FAILED${NC} - Redis not accessible"
    ((fail_count++))
fi

# PostgreSQL connectivity
echo -n "Checking PostgreSQL... "
if docker exec rag-postgres psql -U postgres -c "SELECT 1;" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ OK${NC} - Database connected"
    ((success_count++))
else
    echo -e "${RED}❌ FAILED${NC} - Database not accessible"
    ((fail_count++))
fi

# Ollama models
echo -n "Checking Ollama Models... "
ollama_models=$(docker exec rag-ollama ollama list 2>/dev/null | grep -c "instruct" || echo "0")
if [ "$ollama_models" -ge 2 ]; then
    echo -e "${GREEN}✅ OK${NC} - $ollama_models models installed"
    ((success_count++))
else
    echo -e "${YELLOW}⚠️  WARNING${NC} - Only $ollama_models models found (expected 2+)"
    ((fail_count++))
fi

echo ""
echo "=== Available Models ==="

# Get models from API
models_response=$(curl -s http://localhost:8000/api/v1/models/ 2>/dev/null)
if [ -n "$models_response" ]; then
    echo "$models_response" | jq -r '.[] | "  • \(.name) (\(.provider))"' 2>/dev/null || echo "  Unable to parse models (jq not installed)"
    model_count=$(echo "$models_response" | jq '. | length' 2>/dev/null || echo "?")
    echo ""
    echo "Total models available: $model_count"
else
    echo -e "${RED}  Unable to fetch models from API${NC}"
fi

echo ""
echo "=== Ollama Local Models ==="
docker exec rag-ollama ollama list 2>/dev/null || echo "  Ollama not accessible"

echo ""
echo "=== Docker Services Status ==="
docker compose ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null

echo ""
echo "=============================================="
total=$((success_count + fail_count))
echo -e "Results: ${GREEN}$success_count passed${NC}, ${RED}$fail_count failed${NC} out of $total checks"

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}✅ All services are running correctly!${NC}"
    echo ""
    echo "🌐 Access your chatbot at: http://localhost:3001"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some services are not running. Check docker compose logs for details.${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check logs: docker compose logs [service-name]"
    echo "  2. Restart services: docker compose restart"
    echo "  3. Rebuild if needed: docker compose up -d --build"
    exit 1
fi
