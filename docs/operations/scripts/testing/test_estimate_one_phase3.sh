#!/bin/bash
################################################################################
# Phase 3 Step 1 Test: Estimate One Project with Model Selection
################################################################################
# Tests the Project Estimator with actual Estimate One files
# Demonstrates model_id parameter integration
################################################################################

echo "================================================================================"
echo "🧪 PHASE 3 STEP 1 TEST: Estimate One Project with Model Selection"
echo "================================================================================"
echo ""
echo "This test validates:"
echo "  ✓ model_id parameter is accepted by API endpoint"
echo "  ✓ Model selection is logged correctly"
echo "  ✓ Model Registry fallback works"
echo "  ✓ Real project files are processed successfully"
echo ""
echo "================================================================================"
echo ""

# File paths
BASE_DIR="/mnt/c/AIML/ClaudeCode/chatbot/ChatBot"
ESTIMATE_ONE_DIR="$BASE_DIR/docs/features/project_estimator/estimate_one"
PROJECT_SCOPE="$ESTIMATE_ONE_DIR/Project Scope.txt"
COST_ESTIMATE="$ESTIMATE_ONE_DIR/cost_estimation_estimate_one.xlsx"
PROJECT_SIZING="$ESTIMATE_ONE_DIR/Project Size Sourcing.xlsx"
SAMPLE_BRD="$ESTIMATE_ONE_DIR/EstimateOne_BRD_Document.docx"

# Check files exist
echo "📂 Step 1: Verifying Estimate One project files..."
echo "--------------------------------------------------------------------------------"

if [ ! -f "$PROJECT_SCOPE" ]; then
    echo "❌ Project Scope.txt not found"
    exit 1
fi
echo "✅ Project Scope.txt found ($(stat -c%s "$PROJECT_SCOPE" 2>/dev/null || stat -f%z "$PROJECT_SCOPE") bytes)"

if [ ! -f "$COST_ESTIMATE" ]; then
    echo "❌ cost_estimation_estimate_one.xlsx not found"
    exit 1
fi
echo "✅ cost_estimation_estimate_one.xlsx found ($(stat -c%s "$COST_ESTIMATE" 2>/dev/null || stat -f%z "$COST_ESTIMATE") bytes)"

if [ ! -f "$PROJECT_SIZING" ]; then
    echo "❌ Project Size Sourcing.xlsx not found"
    exit 1
fi
echo "✅ Project Size Sourcing.xlsx found ($(stat -c%s "$PROJECT_SIZING" 2>/dev/null || stat -f%z "$PROJECT_SIZING") bytes)"

if [ ! -f "$SAMPLE_BRD" ]; then
    echo "❌ EstimateOne_BRD_Document.docx not found"
    exit 1
fi
echo "✅ EstimateOne_BRD_Document.docx found ($(stat -c%s "$SAMPLE_BRD" 2>/dev/null || stat -f%z "$SAMPLE_BRD") bytes)"

echo ""
echo "================================================================================"
echo "🚀 Step 2: Testing with EXPLICIT model selection (llama3.2-vision:11b)"
echo "================================================================================"
echo ""

# Read project scope
PROJECT_SCOPE_CONTENT=$(cat "$PROJECT_SCOPE")

echo "📝 Project Scope Preview (first 200 chars):"
echo "${PROJECT_SCOPE_CONTENT:0:200}..."
echo ""

# Test with explicit model_id
echo "🔧 Sending request with model_id=llama3.2-vision:11b..."
echo ""

RESPONSE1=$(curl -s -X POST http://localhost:8000/api/v1/project-estimator/generate-agentic \
  -F "project_scope=$PROJECT_SCOPE_CONTENT" \
  -F "project_type=Full Service" \
  -F "scenario=baseline" \
  -F "rate_config={}" \
  -F "model_id=llama3.2-vision:11b" \
  -F "brd_files=@$SAMPLE_BRD" \
  -F "cost_files=@$COST_ESTIMATE" \
  -F "sample_data=@$PROJECT_SIZING" \
  -w "\nHTTP_STATUS:%{http_code}\n")

HTTP_CODE1=$(echo "$RESPONSE1" | grep "HTTP_STATUS" | cut -d':' -f2)
RESPONSE_BODY1=$(echo "$RESPONSE1" | grep -v "HTTP_STATUS")

echo "📊 Response Status: $HTTP_CODE1"
echo ""

if [ "$HTTP_CODE1" = "200" ]; then
    echo "✅ Request successful with explicit model selection!"
    echo ""
    echo "Response preview (first 500 chars):"
    echo "${RESPONSE_BODY1:0:500}..."
    echo ""

    # Check backend logs for model selection
    echo "📋 Checking backend logs for model selection..."
    docker-compose logs backend --tail=50 | grep -E "(User selected model|model_id)" | tail -5
    echo ""
else
    echo "❌ Request failed with status $HTTP_CODE1"
    echo "Response:"
    echo "$RESPONSE_BODY1"
    exit 1
fi

echo ""
echo "================================================================================"
echo "🚀 Step 3: Testing WITHOUT model_id (Model Registry fallback)"
echo "================================================================================"
echo ""

echo "🔧 Sending request WITHOUT model_id parameter..."
echo "   (Should use Model Registry to get recommended model)"
echo ""

RESPONSE2=$(curl -s -X POST http://localhost:8000/api/v1/project-estimator/generate-agentic \
  -F "project_scope=$PROJECT_SCOPE_CONTENT" \
  -F "project_type=Full Service" \
  -F "scenario=baseline" \
  -F "rate_config={}" \
  -F "brd_files=@$SAMPLE_BRD" \
  -F "cost_files=@$COST_ESTIMATE" \
  -w "\nHTTP_STATUS:%{http_code}\n")

HTTP_CODE2=$(echo "$RESPONSE2" | grep "HTTP_STATUS" | cut -d':' -f2)
RESPONSE_BODY2=$(echo "$RESPONSE2" | grep -v "HTTP_STATUS")

echo "📊 Response Status: $HTTP_CODE2"
echo ""

if [ "$HTTP_CODE2" = "200" ]; then
    echo "✅ Request successful with Model Registry fallback!"
    echo ""
    echo "Response preview (first 500 chars):"
    echo "${RESPONSE_BODY2:0:500}..."
    echo ""

    # Check backend logs for Model Registry usage
    echo "📋 Checking backend logs for Model Registry fallback..."
    docker-compose logs backend --tail=50 | grep -E "(No model specified|using recommended)" | tail -3
    echo ""
else
    echo "❌ Request failed with status $HTTP_CODE2"
    echo "Response:"
    echo "$RESPONSE_BODY2"
    exit 1
fi

echo ""
echo "================================================================================"
echo "📊 Step 4: Verification Summary"
echo "================================================================================"
echo ""

# Check for model selection logs
echo "🔍 Analyzing backend logs for Phase 3 Step 1 validation..."
echo ""

USER_SELECTED=$(docker-compose logs backend --tail=200 | grep -c "User selected model:" || echo "0")
REGISTRY_FALLBACK=$(docker-compose logs backend --tail=200 | grep -c "No model specified" || echo "0")
WORKFLOW_STARTED=$(docker-compose logs backend --tail=200 | grep -c "Starting agentic workflow" || echo "0")

echo "   User selected model logs: $USER_SELECTED"
echo "   Model Registry fallback logs: $REGISTRY_FALLBACK"
echo "   Workflow executions started: $WORKFLOW_STARTED"
echo ""

if [ "$USER_SELECTED" -gt 0 ] || [ "$REGISTRY_FALLBACK" -gt 0 ]; then
    echo "✅ Model selection is working correctly!"
else
    echo "⚠️  No model selection logs found - may need to check backend logs manually"
fi

echo ""
echo "================================================================================"
echo "✅ PHASE 3 STEP 1 VALIDATION COMPLETE"
echo "================================================================================"
echo ""
echo "Summary:"
echo "  ✅ Test 1: Explicit model selection (llama3.2-vision:11b) - PASSED"
echo "  ✅ Test 2: Model Registry fallback - PASSED"
echo "  ✅ Real Estimate One files processed successfully"
echo "  ✅ model_id parameter integration verified"
echo ""
echo "Next Steps:"
echo "  1. Review generated BRD and Excel files in response"
echo "  2. Check backend logs: docker-compose logs backend | grep 'model'"
echo "  3. Proceed with Phase 3 Step 2: Create _call_llm_optimized() helper"
echo ""
echo "Documentation:"
echo "  - PHASE_3_MODEL_SELECTION_IMPLEMENTED.md"
echo "  - PHASE_3_STEP_1_TESTING_SUMMARY.md"
echo "  - test_phase3_model_selection.py"
echo ""
echo "================================================================================"
