#!/bin/bash
# Playwright RBAC Tests Execution Script
# This script runs the Playwright tests and generates comprehensive reports

set -e  # Exit on error

echo "========================================"
echo "Playwright RBAC Testing Suite"
echo "========================================"
echo ""

# Configuration
export FRONTEND_URL="${FRONTEND_URL:-http://localhost:3001}"
export ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
export ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin123}"
export HEADLESS="${HEADLESS:-true}"
export SLOW_MO="${SLOW_MO:-0}"
export SCREENSHOT_ON_FAILURE="${SCREENSHOT_ON_FAILURE:-true}"

echo "Configuration:"
echo "  Frontend URL: $FRONTEND_URL"
echo "  Admin User: $ADMIN_USERNAME"
echo "  Headless Mode: $HEADLESS"
echo "  Slow Motion: ${SLOW_MO}ms"
echo ""

# Check services
echo "Checking required services..."
if ! curl -s "$FRONTEND_URL" > /dev/null; then
    echo "ERROR: Frontend not accessible at $FRONTEND_URL"
    echo "Please start frontend: docker-compose up -d frontend"
    exit 1
fi
echo "✓ Frontend is accessible"

if ! curl -s "http://localhost:8000/health" > /dev/null; then
    echo "ERROR: Backend not accessible at http://localhost:8000"
    echo "Please start backend: docker-compose up -d backend"
    exit 1
fi
echo "✓ Backend is accessible"
echo ""

# Create results directory
mkdir -p backend/tests/playwright/test_results
echo "✓ Test results directory ready: backend/tests/playwright/test_results"
echo ""

# Run tests
echo "Running Playwright tests..."
echo "========================================"

if [ "$1" == "all" ] || [ -z "$1" ]; then
    echo "Running ALL tests..."
    pytest backend/tests/playwright/ -v --tb=short --override-ini="addopts="
elif [ "$1" == "users" ]; then
    echo "Running Users CRUD tests..."
    pytest backend/tests/playwright/test_users_crud.py -v --tb=short --override-ini="addopts="
elif [ "$1" == "roles" ]; then
    echo "Running Roles CRUD tests..."
    pytest backend/tests/playwright/test_roles_crud.py -v --tb=short --override-ini="addopts="
elif [ "$1" == "departments" ]; then
    echo "Running Departments tests..."
    pytest backend/tests/playwright/test_departments.py -v --tb=short --override-ini="addopts="
else
    echo "Running specific test: $1"
    pytest "backend/tests/playwright/$1" -v --tb=short --override-ini="addopts="
fi

echo ""
echo "========================================"
echo "Test Execution Complete!"
echo "========================================"
echo ""

# List generated reports
echo "Generated Reports:"
echo ""
if [ -f "backend/tests/playwright/test_results/users_crud_test_report.html" ]; then
    echo "✓ Users CRUD Report:"
    echo "  - HTML: backend/tests/playwright/test_results/users_crud_test_report.html"
    echo "  - JSON: backend/tests/playwright/test_results/users_crud_test_report.json"
fi

if [ -f "backend/tests/playwright/test_results/roles_crud_test_report.html" ]; then
    echo "✓ Roles CRUD Report:"
    echo "  - HTML: backend/tests/playwright/test_results/roles_crud_test_report.html"
    echo "  - JSON: backend/tests/playwright/test_results/roles_crud_test_report.json"
fi

if [ -f "backend/tests/playwright/test_results/departments_test_report.html" ]; then
    echo "✓ Departments Report:"
    echo "  - HTML: backend/tests/playwright/test_results/departments_test_report.html"
    echo "  - JSON: backend/tests/playwright/test_results/departments_test_report.json"
fi

echo ""
echo "Screenshots: backend/tests/playwright/test_results/*.png"
echo ""

# Count screenshots
SCREENSHOT_COUNT=$(ls -1 backend/tests/playwright/test_results/*.png 2>/dev/null | wc -l)
echo "Total Screenshots: $SCREENSHOT_COUNT"
echo ""

echo "========================================"
echo "How to View Reports:"
echo "========================================"
echo ""
echo "1. Open HTML report in browser:"
echo "   open backend/tests/playwright/test_results/users_crud_test_report.html"
echo ""
echo "2. Or start HTTP server:"
echo "   cd backend/tests/playwright/test_results"
echo "   python -m http.server 8080"
echo "   # Then navigate to: http://localhost:8080"
echo ""
echo "3. View JSON report:"
echo "   cat backend/tests/playwright/test_results/users_crud_test_report.json | jq ."
echo ""

echo "✅ Testing Complete!"
