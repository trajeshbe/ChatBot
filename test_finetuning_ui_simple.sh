#!/bin/bash

# Simple Fine-Tuning UI E2E Test Script
# Runs Playwright tests from within Docker container with proper configuration

set -e

echo "========================================="
echo "Fine-Tuning UI E2E Test Runner"
echo "========================================="
echo ""

# Configuration
FRONTEND_URL="http://frontend:3000"
HEADLESS="true"
SLOW_MO="500"  # Slow down for debugging

echo "Configuration:"
echo "  Frontend URL: $FRONTEND_URL"
echo "  Headless: $HEADLESS"
echo "  Slow Motion: ${SLOW_MO}ms"
echo ""

# Check if frontend is accessible
echo "Checking frontend connectivity..."
FRONTEND_STATUS=$(docker-compose exec -T backend bash -c "curl -s -o /dev/null -w '%{http_code}' http://frontend:3000/" || echo "FAILED")

if [ "$FRONTEND_STATUS" = "200" ]; then
    echo "✓ Frontend is accessible (HTTP 200)"
else
    echo "✗ Frontend not accessible (HTTP $FRONTEND_STATUS)"
    echo "Please ensure frontend container is running: docker-compose ps frontend"
    exit 1
fi
echo ""

# Check if backend is accessible
echo "Checking backend connectivity..."
BACKEND_STATUS=$(docker-compose exec -T backend bash -c "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health" || echo "FAILED")

if [ "$BACKEND_STATUS" = "200" ]; then
    echo "✓ Backend is accessible (HTTP 200)"
else
    echo "✗ Backend not accessible (HTTP $BACKEND_STATUS)"
    echo "Please ensure backend container is running: docker-compose ps backend"
    exit 1
fi
echo ""

# Create test results directory
echo "Setting up test results directory..."
docker-compose exec -T backend bash -c "mkdir -p /app/tests/playwright/test_results"
echo "✓ Test results directory created"
echo ""

# Run Playwright tests
echo "========================================="
echo "Running Playwright Tests..."
echo "========================================="
echo ""

docker-compose exec -T backend bash -c "
    cd /app/tests/playwright && \
    FRONTEND_URL=$FRONTEND_URL \
    HEADLESS=$HEADLESS \
    SLOW_MO=$SLOW_MO \
    python -m pytest test_finetuning_e2e_workflow.py \
        -v \
        --tb=short \
        -s \
        --maxfail=1
"

TEST_EXIT_CODE=$?

echo ""
echo "========================================="
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✓ Tests Passed!"
else
    echo "✗ Tests Failed (exit code: $TEST_EXIT_CODE)"
fi
echo "========================================="
echo ""

# Check for test report
REPORT_PATH="backend/tests/playwright/test_results/FINETUNING_E2E_TEST_REPORT.md"
if [ -f "$REPORT_PATH" ]; then
    echo "Test report available at: $REPORT_PATH"
    echo ""
    echo "Report Preview:"
    head -50 "$REPORT_PATH"
else
    echo "No test report generated"
fi

echo ""
echo "Screenshots available in: backend/tests/playwright/test_results/"
ls -lh backend/tests/playwright/test_results/*.png 2>/dev/null || echo "No screenshots found"

exit $TEST_EXIT_CODE
