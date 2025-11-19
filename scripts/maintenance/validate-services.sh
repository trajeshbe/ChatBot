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
ollama_models=$(docker exec rag-ollama ollama list 2>/dev/null | tail -n +2 | wc -l 2>/dev/null || echo "0")
# Ensure it's a valid integer by stripping any non-numeric characters
ollama_models=$(echo "$ollama_models" | tr -cd '0-9' | head -c 10)
# Default to 0 if empty
[ -z "$ollama_models" ] && ollama_models=0
if [ "$ollama_models" -ge 1 ]; then
    echo -e "${GREEN}✅ OK${NC} - $ollama_models models installed"
    ((success_count++))
else
    echo -e "${YELLOW}⚠️  WARNING${NC} - No models found (run scripts/setup/setup-ollama-models.sh)"
    ((fail_count++))
fi

echo ""
echo "=== Web Scraping Features ==="

# Web scraper capabilities
echo -n "Checking Web Scraper... "
scraper_response=$(curl -s http://localhost:8000/api/v1/scraper/capabilities 2>/dev/null)
if echo "$scraper_response" | grep -q "web_scraping_enabled"; then
    enabled=$(echo "$scraper_response" | grep -o '"web_scraping_enabled":[^,}]*' | grep -o 'true\|false')
    if [ "$enabled" = "true" ]; then
        echo -e "${GREEN}✅ OK${NC} - Web scraping enabled"
        ((success_count++))
    else
        echo -e "${YELLOW}⚠️  WARNING${NC} - Web scraping disabled"
        ((fail_count++))
    fi
else
    echo -e "${RED}❌ FAILED${NC} - Cannot fetch scraper status"
    ((fail_count++))
fi

# Playwright integration (test from inside container per PLAYWRIGHT_INVESTIGATION.md)
echo -n "Checking Playwright... "
playwright_test=$(docker exec rag-backend curl -s http://localhost:8000/api/v1/test/playwright-minimal 2>/dev/null)
if echo "$playwright_test" | grep -q '"success":true'; then
    browser_version=$(echo "$playwright_test" | grep -o '"browser_version":"[^"]*"' | cut -d'"' -f4)
    echo -e "${GREEN}✅ OK${NC} - Chromium $browser_version"
    ((success_count++))
else
    echo -e "${YELLOW}⚠️  WARNING${NC} - Playwright not available (browser automation disabled)"
    # Not incrementing fail_count as this is optional
fi

echo ""
echo "=== Available Models ==="

# Get models from API
models_response=$(curl -s http://localhost:8000/api/v1/models/ 2>/dev/null)
if [ -n "$models_response" ]; then
    # Check if jq is available
    if command -v jq &> /dev/null; then
        echo "$models_response" | jq -r '.[] | "  • \(.name) (\(.provider))"' 2>/dev/null
        model_count=$(echo "$models_response" | jq '. | length' 2>/dev/null || echo "?")
    else
        # Fallback without jq
        echo "  (Install jq for better formatting: apt-get install jq)"
        echo "$models_response" | grep -o '"name":"[^"]*"' | sed 's/"name":"//g' | sed 's/"//g' | sed 's/^/  • /'
        model_count=$(echo "$models_response" | grep -o '"name"' | wc -l)
    fi
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
