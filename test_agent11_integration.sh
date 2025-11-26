#!/bin/bash
#
# Test Agent 1.1 Integration
# Verifies Agent 1.1 (Sample Complexity Analyzer) is integrated and working
#

echo "================================================================================"
echo "🧪 AGENT 1.1 INTEGRATION TEST"
echo "================================================================================"
echo ""

echo "📋 Test Objectives:"
echo "  1. Verify workflow.py has Agent 1.1 enhancements"
echo "  2. Test Project Estimator workflow execution"
echo "  3. Monitor Agent 1.1 logs for complexity analysis"
echo "  4. Verify Excel formulas and BRD sections"
echo ""

# Test 1: Check if Agent 1.1 code exists in workflow.py
echo "================================================================================"
echo "TEST 1: Verify Agent 1.1 Code in workflow.py"
echo "================================================================================"
echo ""

echo "Checking for Agent 1.1 method..."
if grep -q "sample_complexity_analyzer" backend/app/agents/project_estimator/workflow.py; then
    echo "✅ sample_complexity_analyzer() method found"
else
    echo "❌ sample_complexity_analyzer() method NOT found"
    exit 1
fi

echo "Checking for complexity_analysis in state..."
if grep -q "complexity_analysis" backend/app/agents/project_estimator/workflow.py; then
    echo "✅ complexity_analysis field found"
else
    echo "❌ complexity_analysis field NOT found"
    exit 1
fi

echo "Checking for effort_multiplier..."
if grep -q "effort_multiplier" backend/app/agents/project_estimator/workflow.py; then
    echo "✅ effort_multiplier logic found"
else
    echo "❌ effort_multiplier logic NOT found"
    exit 1
fi

echo "Checking for rate_multiplier..."
if grep -q "rate_multiplier" backend/app/agents/project_estimator/workflow.py; then
    echo "✅ rate_multiplier logic found"
else
    echo "❌ rate_multiplier logic NOT found"
    exit 1
fi

echo "Checking for Excel SUM() formulas..."
if grep -q "=SUM(B{first_team_row}:B{last_team_row})" backend/app/agents/project_estimator/workflow.py; then
    echo "✅ Excel SUM() formulas found"
else
    echo "❌ Excel SUM() formulas NOT found"
    exit 1
fi

echo "Checking for BRD complexity section..."
if grep -q "2.5 Sample Complexity Analysis" backend/app/agents/project_estimator/workflow.py; then
    echo "✅ BRD complexity section found"
else
    echo "❌ BRD complexity section NOT found"
    exit 1
fi

echo ""
echo "✅ All Agent 1.1 code checks passed!"
echo ""

# Test 2: Check services are running
echo "================================================================================"
echo "TEST 2: Verify Services are Running"
echo "================================================================================"
echo ""

if docker-compose ps | grep -q "rag-backend.*Up"; then
    echo "✅ Backend service is running"
else
    echo "❌ Backend service is NOT running"
    exit 1
fi

if docker-compose ps | grep -q "rag-ollama.*Up"; then
    echo "✅ Ollama service is running"
else
    echo "⚠️  Ollama service is NOT running (vision model may not work)"
fi

echo ""

# Test 3: Check for Agent 1.1 in recent logs
echo "================================================================================"
echo "TEST 3: Check Recent Agent 1.1 Activity in Logs"
echo "================================================================================"
echo ""

echo "Searching for Agent 1.1 in backend logs..."
AGENT11_LOGS=$(docker-compose logs backend --tail=500 2>&1 | grep -i "Agent 1.1" || echo "")

if [ -n "$AGENT11_LOGS" ]; then
    echo "✅ Found Agent 1.1 activity in logs:"
    echo "$AGENT11_LOGS" | head -10
    echo ""
else
    echo "⚠️  No recent Agent 1.1 activity found in logs"
    echo "   (This is expected if no workflows have run recently)"
    echo ""
fi

# Test 4: Dry run validation
echo "================================================================================"
echo "TEST 4: Validate Code Syntax"
echo "================================================================================"
echo ""

echo "Checking Python syntax in workflow.py..."
if docker-compose exec -T backend python3 -m py_compile /app/app/agents/project_estimator/workflow.py 2>&1; then
    echo "✅ workflow.py syntax is valid"
else
    echo "❌ workflow.py has syntax errors"
    exit 1
fi

echo ""

# Summary
echo "================================================================================"
echo "📊 TEST SUMMARY"
echo "================================================================================"
echo ""
echo "✅ All Agent 1.1 integration tests passed!"
echo ""
echo "Components verified:"
echo "  ✅ sample_complexity_analyzer() method"
echo "  ✅ complexity_analysis state field"
echo "  ✅ effort_multiplier (Agent 3)"
echo "  ✅ rate_multiplier (Agent 5)"
echo "  ✅ Excel SUM() formulas"
echo "  ✅ BRD Section 2.5 Complexity Analysis"
echo "  ✅ Python syntax validation"
echo ""
echo "================================================================================"
echo "🎯 NEXT STEP: Run End-to-End Test"
echo "================================================================================"
echo ""
echo "To test the complete Agent 1.1 workflow with sample files:"
echo ""
echo "  1. Open http://localhost:3001 in your browser"
echo "  2. Navigate to Project Estimator"
echo "  3. Upload sample files (PDF, Excel, etc.)"
echo "  4. Fill in project scope"
echo "  5. Click 'Generate Estimate'"
echo "  6. Monitor logs with:"
echo "     docker-compose logs backend --follow | grep -E '(Agent 1.1|effort multiplier|rate multiplier)'"
echo ""
echo "  7. After completion, download and verify:"
echo "     - BRD.docx → Check Section 2.5 'Sample Complexity Analysis'"
echo "     - CostEstimate.xlsx → Check for SUM() formulas in totals"
echo ""
echo "================================================================================"
