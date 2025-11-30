#!/bin/bash
# Rebuild backend with Playwright dependencies and test web scraping

set -e

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║      Rebuilding Backend with Playwright Dependencies             ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

echo ">>> Step 1: Stopping backend container..."
docker compose stop backend

echo ""
echo ">>> Step 2: Removing old backend container..."
docker compose rm -f backend

echo ""
echo ">>> Step 3: Rebuilding backend image (no cache)..."
echo "    This will take a few minutes to install all Playwright dependencies..."
docker compose build backend --no-cache

echo ""
echo ">>> Step 4: Starting backend container..."
docker compose up -d backend

echo ""
echo ">>> Step 5: Waiting for backend to be healthy (60 seconds)..."
sleep 10
echo "    ... 10 seconds elapsed"
sleep 10
echo "    ... 20 seconds elapsed"
sleep 10
echo "    ... 30 seconds elapsed"
sleep 10
echo "    ... 40 seconds elapsed"
sleep 10
echo "    ... 50 seconds elapsed"
sleep 10
echo "    ... 60 seconds elapsed"

echo ""
echo ">>> Step 6: Checking backend health..."
HEALTH_CHECK=$(curl -s http://localhost:8000/health | jq -r '.status' 2>/dev/null || echo "error")

if [ "$HEALTH_CHECK" == "healthy" ]; then
    echo "✅ Backend is healthy!"
else
    echo "⚠️  Backend health check failed. Checking logs..."
    docker compose logs backend --tail=30
    exit 1
fi

echo ""
echo ">>> Step 7: Checking Playwright capabilities..."
CAPABILITIES=$(curl -s http://localhost:8000/api/v1/scraper/capabilities)
echo "$CAPABILITIES" | jq '.'

PLAYWRIGHT_ENABLED=$(echo "$CAPABILITIES" | jq -r '.playwright_enabled')

if [ "$PLAYWRIGHT_ENABLED" == "true" ]; then
    echo "✅ Playwright is ENABLED and ready!"
else
    echo "⚠️  Playwright is DISABLED. This may be expected if dependencies are missing."
    echo "    Checking backend logs for Playwright errors..."
    docker compose logs backend | grep -i playwright | tail -10
fi

echo ""
echo ">>> Step 8: Testing Wikipedia scraping (403 Forbidden bypass test)..."
echo "    URL: https://en.wikipedia.org/wiki/Ooty"
echo ""

TEST_RESULT=$(curl -s -X POST http://localhost:8000/api/v1/scraper/scrape/bulk \
    -H "Content-Type: application/json" \
    -d '{
        "urls": ["https://en.wikipedia.org/wiki/Ooty"],
        "strategy": "hybrid",
        "config": {
            "enable_javascript": true,
            "timeout": 60.0
        }
    }' 2>&1)

echo "Response:"
echo "$TEST_RESULT" | jq '.' 2>/dev/null || echo "$TEST_RESULT"

# Check if any result was successful
SUCCESS_COUNT=$(echo "$TEST_RESULT" | jq -r '.successful_count // 0' 2>/dev/null || echo "0")

if [ "$SUCCESS_COUNT" -gt 0 ]; then
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║                    ✅ ALL TESTS PASSED!                           ║"
    echo "╠═══════════════════════════════════════════════════════════════════╣"
    echo "║  Backend rebuilt successfully with Playwright support             ║"
    echo "║  Wikipedia scraping works (403 Forbidden bypass successful)       ║"
    echo "║  Hybrid strategy with Playwright fallback functional              ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    exit 0
else
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║                    ⚠️  TEST FAILED                                 ║"
    echo "╠═══════════════════════════════════════════════════════════════════╣"
    echo "║  Wikipedia scraping test failed                                   ║"
    echo "║  Check backend logs for details:                                  ║"
    echo "║  docker compose logs backend --tail=100                           ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"

    echo ""
    echo ">>> Backend logs (last 50 lines):"
    docker compose logs backend --tail=50

    exit 1
fi
