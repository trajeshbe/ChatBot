#!/bin/bash

# ============================================================================
# Export Wizard Manual Test Script
# ============================================================================
#
# Purpose: Test Export Wizard API endpoints manually
#
# Usage: bash backend/tests/test_export_wizard_manual.sh
#
# Requirements:
#   - Backend server running on http://localhost:8000
#   - curl and jq installed
#
# Date: 2026-01-07
# Related: Requirement #10 - Export Wizard Enhancement
#
# ============================================================================

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

API_URL="http://localhost:8000"
PASS=0
FAIL=0

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Export Wizard API - Manual Test Suite                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# Helper Functions
# ============================================================================

test_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASS++))
}

test_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAIL++))
}

test_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

test_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# ============================================================================
# Test 1: Health Check
# ============================================================================

echo ">>> [1/6] Testing Export Wizard Health Check"
echo ""

HEALTH_RESPONSE=$(curl -s "${API_URL}/api/v1/export-wizard/health")

if echo "$HEALTH_RESPONSE" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
    test_pass "Health check endpoint responding"
    echo "$HEALTH_RESPONSE" | jq '.'
else
    test_fail "Health check failed"
    echo "$HEALTH_RESPONSE"
fi

echo ""

# ============================================================================
# Test 2: List Tier 2 Modules
# ============================================================================

echo ">>> [2/6] Testing List Tier 2 Modules"
echo ""

TIER2_RESPONSE=$(curl -s "${API_URL}/api/v1/export-wizard/modules/tier/2")

if echo "$TIER2_RESPONSE" | jq -e '.tier == 2' > /dev/null 2>&1; then
    MODULE_COUNT=$(echo "$TIER2_RESPONSE" | jq '.modules | length')
    test_pass "Tier 2 modules endpoint working ($MODULE_COUNT modules found)"

    # Show first 3 modules
    echo "$TIER2_RESPONSE" | jq '.modules[0:3] | .[] | {name, code, category}'
else
    test_fail "Failed to list Tier 2 modules"
    echo "$TIER2_RESPONSE"
fi

echo ""

# ============================================================================
# Test 3: List Tier 3 Modules
# ============================================================================

echo ">>> [3/6] Testing List Tier 3 Modules"
echo ""

TIER3_RESPONSE=$(curl -s "${API_URL}/api/v1/export-wizard/modules/tier/3")

if echo "$TIER3_RESPONSE" | jq -e '.tier == 3' > /dev/null 2>&1; then
    MODULE_COUNT=$(echo "$TIER3_RESPONSE" | jq '.modules | length')
    test_pass "Tier 3 modules endpoint working ($MODULE_COUNT modules found)"

    # Show all Tier 3 modules
    echo "$TIER3_RESPONSE" | jq '.modules | .[] | {name, code}'
else
    test_fail "Failed to list Tier 3 modules"
    echo "$TIER3_RESPONSE"
fi

echo ""

# ============================================================================
# Test 4: Create Export Package (Optional - requires user confirmation)
# ============================================================================

echo ">>> [4/6] Testing Create Export Package (Optional)"
echo ""

read -p "Do you want to create a test export package? This will take 2-5 minutes. (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    test_info "Creating export package for 'Relation Extractor' (Tier 2)..."

    # Get first Tier 2 module
    FIRST_MODULE=$(echo "$TIER2_RESPONSE" | jq -r '.modules[0].name')

    if [ -z "$FIRST_MODULE" ] || [ "$FIRST_MODULE" == "null" ]; then
        test_warn "No Tier 2 modules available, skipping export test"
    else
        test_info "Using module: $FIRST_MODULE"

        EXPORT_RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/export-wizard/export" \
            -H "Content-Type: application/json" \
            -d "{\"module_name\": \"$FIRST_MODULE\", \"module_tier\": 2}")

        if echo "$EXPORT_RESPONSE" | jq -e '.export_id' > /dev/null 2>&1; then
            EXPORT_ID=$(echo "$EXPORT_RESPONSE" | jq -r '.export_id')
            test_pass "Export job created (ID: $EXPORT_ID)"
            echo "$EXPORT_RESPONSE" | jq '.'

            # Store export ID for next tests
            echo "$EXPORT_ID" > /tmp/export_wizard_test_id.txt
        else
            test_fail "Failed to create export job"
            echo "$EXPORT_RESPONSE"
        fi
    fi
else
    test_info "Skipping export creation (user declined)"
    EXPORT_ID=""
fi

echo ""

# ============================================================================
# Test 5: Check Export Status (if export was created)
# ============================================================================

echo ">>> [5/6] Testing Export Status Check"
echo ""

if [ -f /tmp/export_wizard_test_id.txt ]; then
    EXPORT_ID=$(cat /tmp/export_wizard_test_id.txt)

    test_info "Checking status of export job: $EXPORT_ID"

    # Poll status a few times
    for i in {1..5}; do
        STATUS_RESPONSE=$(curl -s "${API_URL}/api/v1/export-wizard/status/${EXPORT_ID}")

        if echo "$STATUS_RESPONSE" | jq -e '.export_id' > /dev/null 2>&1; then
            STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status')
            PROGRESS=$(echo "$STATUS_RESPONSE" | jq -r '.progress')
            STEP=$(echo "$STATUS_RESPONSE" | jq -r '.current_step')

            echo -e "  Attempt $i: Status=${BLUE}$STATUS${NC}, Progress=${BLUE}${PROGRESS}%${NC}, Step=${BLUE}$STEP${NC}"

            if [ "$STATUS" == "completed" ]; then
                test_pass "Export completed successfully!"
                ZIP_PATH=$(echo "$STATUS_RESPONSE" | jq -r '.zip_path')
                echo "  ZIP Path: $ZIP_PATH"
                break
            elif [ "$STATUS" == "failed" ]; then
                test_fail "Export failed"
                ERROR=$(echo "$STATUS_RESPONSE" | jq -r '.error')
                echo "  Error: $ERROR"
                break
            else
                if [ $i -lt 5 ]; then
                    sleep 2
                else
                    test_info "Export still in progress (check manually later)"
                fi
            fi
        else
            test_fail "Failed to check export status"
            echo "$STATUS_RESPONSE"
            break
        fi
    done
else
    test_info "No export ID available, skipping status check"
fi

echo ""

# ============================================================================
# Test 6: Invalid Requests
# ============================================================================

echo ">>> [6/6] Testing Error Handling"
echo ""

# Test invalid tier
INVALID_TIER_RESPONSE=$(curl -s "${API_URL}/api/v1/export-wizard/modules/tier/999")
if echo "$INVALID_TIER_RESPONSE" | jq -e '.detail' > /dev/null 2>&1; then
    test_pass "Invalid tier properly rejected"
else
    test_fail "Invalid tier not handled correctly"
fi

# Test invalid module
INVALID_MODULE_RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/export-wizard/export" \
    -H "Content-Type: application/json" \
    -d '{"module_name": "NonExistentModule", "module_tier": 2}')

if echo "$INVALID_MODULE_RESPONSE" | jq -e '.detail' > /dev/null 2>&1; then
    test_pass "Invalid module properly rejected"
else
    test_fail "Invalid module not handled correctly"
fi

echo ""

# ============================================================================
# Summary
# ============================================================================

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Test Summary"
echo "════════════════════════════════════════════════════════════════"
echo -e "Passed:  ${GREEN}$PASS${NC}"
echo -e "Failed:  ${RED}$FAIL${NC}"
echo "════════════════════════════════════════════════════════════════"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ All API tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Check export package in /tmp/exports/ (if created)"
    echo "  2. Extract and run verify-export.sh"
    echo "  3. Test installation in clean Docker environment"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo ""
    echo "Please review the failed tests above and fix any issues."
    echo ""
    exit 1
fi
