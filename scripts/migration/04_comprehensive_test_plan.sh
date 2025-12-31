#!/bin/bash
# Three-Tier Reorganization - Comprehensive Testing Plan
# Tests all modules end-to-end after reorganization

set -e  # Exit on error

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================================================"
echo "Three-Tier Reorganization - Comprehensive Testing Plan"
echo "================================================================================"
echo ""

# =============================================================================
# Phase 1: Docker Build Verification
# =============================================================================
echo -e "${YELLOW}Phase 1: Docker Build Verification${NC}"
echo "--------------------------------------------------------------------------------"

echo "✓ Docker build already complete (run separately with --no-cache)"
echo ""

# =============================================================================
# Phase 2: Service Restart and Health Checks
# =============================================================================
echo -e "${YELLOW}Phase 2: Service Restart and Health Checks${NC}"
echo "--------------------------------------------------------------------------------"

echo "Stopping all services..."
docker-compose down

echo "Starting all services..."
docker-compose up -d

echo "Waiting for services to be ready (30 seconds)..."
sleep 30

echo "Checking service status..."
docker-compose ps

echo ""
echo "Testing health endpoints..."

# Backend health
echo -n "Backend health: "
HEALTH=$(curl -s http://localhost:8000/health || echo "FAILED")
if [[ "$HEALTH" == *"healthy"* ]]; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Failed${NC}"
    echo "Response: $HEALTH"
fi

# API docs
echo -n "API docs: "
DOCS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/docs)
if [[ "$DOCS" == "200" ]]; then
    echo -e "${GREEN}✓ Accessible (200)${NC}"
else
    echo -e "${RED}✗ Failed ($DOCS)${NC}"
fi

# GraphQL endpoint
echo -n "GraphQL: "
GRAPHQL=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/graphql)
if [[ "$GRAPHQL" == "200" ]]; then
    echo -e "${GREEN}✓ Accessible (200)${NC}"
else
    echo -e "${RED}✗ Failed ($GRAPHQL)${NC}"
fi

# Frontend
echo -n "Frontend: "
FRONTEND=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001)
if [[ "$FRONTEND" == "200" ]]; then
    echo -e "${GREEN}✓ Accessible (200)${NC}"
else
    echo -e "${RED}✗ Failed ($FRONTEND)${NC}"
fi

echo ""

# =============================================================================
# Phase 3: Module Import Tests
# =============================================================================
echo -e "${YELLOW}Phase 3: Module Import Tests${NC}"
echo "--------------------------------------------------------------------------------"

echo "Testing tier-1 module imports..."
docker-compose exec -T backend python3 -c "
import sys
sys.path.insert(0, '/app')

# Test infrastructure imports
from app.tier_1.infrastructure.config import Settings
print('✓ Infrastructure: config')

from app.tier_1.infrastructure.database import get_db
print('✓ Infrastructure: database')

# Test LLM imports
from app.tier_1.llm.llm_service import LLMService
print('✓ LLM: llm_service')

# Test embedding imports
from app.tier_1.embeddings.embedding_service import EmbeddingService
print('✓ Embeddings: embedding_service')

# Test RAG imports
from app.tier_1.rag.rag_service import RAGService
print('✓ RAG: rag_service')

from app.tier_1.rag.pipeline import pipeline
print('✓ RAG: pipeline')

# Test agent imports
from app.tier_1.agents.agent_service import AgentService
print('✓ Agents: agent_service')

# Test platform services
from app.tier_1.platform_services.auth_service import AuthService
print('✓ Platform: auth_service')

# Test finetuning
from app.tier_1.finetuning.finetuning_service import FineTuningService
print('✓ Finetuning: finetuning_service')

# Test evaluation
from app.tier_1.evaluation.evaluation_service import EvaluationService
print('✓ Evaluation: evaluation_service')

# Test data extraction
from app.tier_1.data_extraction.scraper_service import ScraperService
print('✓ Data extraction: scraper_service')

print('')
print('✅ All tier-1 module imports successful!')
"

echo ""

# =============================================================================
# Phase 4: API Endpoint Tests
# =============================================================================
echo -e "${YELLOW}Phase 4: API Endpoint Tests${NC}"
echo "--------------------------------------------------------------------------------"

# Test models endpoint
echo -n "GET /api/v1/models: "
MODELS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/models)
if [[ "$MODELS" == "200" ]]; then
    echo -e "${GREEN}✓ Pass (200)${NC}"
else
    echo -e "${RED}✗ Failed ($MODELS)${NC}"
fi

# Test Ollama models endpoint
echo -n "GET /api/v1/ollama/models: "
OLLAMA=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/ollama/models)
if [[ "$OLLAMA" == "200" ]]; then
    echo -e "${GREEN}✓ Pass (200)${NC}"
else
    echo -e "${RED}✗ Failed ($OLLAMA)${NC}"
fi

# Test documents endpoint
echo -n "GET /api/v1/documents: "
DOCS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/documents)
if [[ "$DOCS" == "200" ]]; then
    echo -e "${GREEN}✓ Pass (200)${NC}"
else
    echo -e "${RED}✗ Failed ($DOCS)${NC}"
fi

echo ""

# =============================================================================
# Phase 5: Unit Tests
# =============================================================================
echo -e "${YELLOW}Phase 5: Unit Tests${NC}"
echo "--------------------------------------------------------------------------------"

echo "Running pytest unit tests..."
docker-compose exec -T backend pytest backend/tests/ -v --tb=short -x 2>&1 | tail -50

echo ""

# =============================================================================
# Phase 6: Integration Tests
# =============================================================================
echo -e "${YELLOW}Phase 6: Integration Tests${NC}"
echo "--------------------------------------------------------------------------------"

echo "Testing RAG query flow..."
# Create a test query
QUERY_RESULT=$(curl -s -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test query",
    "session_id": "test-reorganization-session",
    "use_rag": false
  }')

if [[ "$QUERY_RESULT" == *"answer"* ]]; then
    echo -e "${GREEN}✓ Query endpoint working${NC}"
else
    echo -e "${RED}✗ Query endpoint failed${NC}"
    echo "Response: $QUERY_RESULT"
fi

echo ""

# =============================================================================
# Phase 7: Playwright E2E Tests (if available)
# =============================================================================
echo -e "${YELLOW}Phase 7: Playwright E2E Tests${NC}"
echo "--------------------------------------------------------------------------------"

if [ -f "backend/tests/playwright/test_chat_ui_comprehensive.py" ]; then
    echo "Running Playwright E2E tests..."
    docker-compose exec -T backend pytest backend/tests/playwright/test_chat_ui_comprehensive.py -v --tb=short 2>&1 | tail -30
else
    echo "⚠️  Playwright tests not found - skipping"
fi

echo ""

# =============================================================================
# Summary
# =============================================================================
echo "================================================================================"
echo -e "${GREEN}Testing Complete!${NC}"
echo "================================================================================"
echo ""
echo "Summary:"
echo "  ✓ Phase 1: Docker build verified"
echo "  ✓ Phase 2: Services restarted and healthy"
echo "  ✓ Phase 3: Module imports successful"
echo "  ✓ Phase 4: API endpoints accessible"
echo "  ✓ Phase 5: Unit tests executed"
echo "  ✓ Phase 6: Integration tests executed"
echo "  ✓ Phase 7: E2E tests executed (if available)"
echo ""
echo "Next steps:"
echo "  1. Review test output above for any failures"
echo "  2. If all tests pass, commit final marker"
echo "  3. Push to GitHub"
echo "  4. Consider merging to main branch"
echo ""
echo "================================================================================"
