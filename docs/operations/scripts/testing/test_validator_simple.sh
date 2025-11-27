#!/bin/bash

echo "================================================================================"
echo "TEST: Project Estimator Meta-Validation Layer"
echo "================================================================================"
echo ""
echo "📋 Test Case: Simple Dashboard (Should NOT include Scraping/ML teams)"
echo ""

# Create a minimal test request
cat > /tmp/test_scope.txt << 'EOF'
Build a web dashboard to visualize our company's internal sales data from PostgreSQL.

Key Features:
- Display sales data in interactive charts (bar, line, pie charts)
- Filter by date range, product category, and sales rep
- Show summary statistics and trends
- Export reports to Excel
- User authentication and role-based access

The data is already in our PostgreSQL database. We need a responsive web application.
EOF

echo "⏳ Submitting Project Estimator request..."
echo ""

# Submit request using curl with FormData
response=$(curl -s -X POST "http://localhost:8000/api/v1/project-estimator/generate-agentic" \
  -F "user_prompt=$(cat /tmp/test_scope.txt)" \
  -F "project_type=full_service" \
  -F "scenario=baseline" \
  -F "senior_rate=150" \
  -F "mid_rate=100" \
  -F "junior_rate=60" \
  -F "qa_rate=80" \
  -F "devops_rate=120" \
  --max-time 300)

if echo "$response" | jq -e . >/dev/null 2>&1; then
    echo "✅ Workflow completed!"
    echo ""
    
    # Extract validation report
    echo "================================================================================"
    echo "🔍 VALIDATION REPORT"
    echo "================================================================================"
    echo ""
    
    validation_status=$(echo "$response" | jq -r '.validation_report.validation_status // "N/A"')
    alignment_score=$(echo "$response" | jq -r '.validation_report.alignment_score // 0')
    summary=$(echo "$response" | jq -r '.validation_report.summary // "N/A"')
    
    echo "Status: $validation_status"
    echo "Alignment Score: $alignment_score/100"
    echo "Summary: $summary"
    echo ""
    
    # Check for issues
    issues_count=$(echo "$response" | jq '.validation_report.issues | length')
    if [ "$issues_count" -gt 0 ]; then
        echo "Issues Found: $issues_count"
        echo "$response" | jq -r '.validation_report.issues[] | "\n  Severity: \(.severity)\n  Category: \(.category)\n  Description: \(.description)\n  Affected: \(.affected_item)"'
    else
        echo "✅ No issues found - outputs are well-aligned!"
    fi
    
    echo ""
    echo "================================================================================"
    echo "📊 TEAM ANALYSIS"
    echo "================================================================================"
    echo ""
    
    # Extract teams
    teams_count=$(echo "$response" | jq '.team_plan.teams | length')
    echo "Total Teams: $teams_count"
    echo ""
    
    echo "$response" | jq -r '.team_plan.teams[] | "  - \(.team_name)\n    Allocation: \(.allocation * 100)%\n    Responsibilities: \(.responsibilities | tostring | .[0:100])...\n"'
    
    echo "🔍 Validation Checks:"
    echo ""
    
    # Check for scraping team
    if echo "$response" | jq -e '.team_plan.teams[] | select(.team_name | test("scrap"; "i"))' > /dev/null; then
        echo "❌ FAIL: Scraping Team included (not needed for this project)"
    else
        echo "✅ PASS: No Scraping Team (correct - no scraping needed)"
    fi
    
    # Check for ML team
    if echo "$response" | jq -e '.team_plan.teams[] | select(.team_name | test("ml|machine learning"; "i"))' > /dev/null; then
        echo "❌ FAIL: ML Engineering Team included (not needed)"
    else
        echo "✅ PASS: No ML Engineering Team (correct - no ML needed)"
    fi
    
    # Check for backend team
    if echo "$response" | jq -e '.team_plan.teams[] | select(.team_name | test("backend|api"; "i"))' > /dev/null; then
        echo "✅ PASS: Backend Team included (correct - API needed)"
    else
        echo "⚠️  WARNING: No Backend Team (may be needed)"
    fi
    
    # Check for frontend team
    if echo "$response" | jq -e '.team_plan.teams[] | select(.team_name | test("frontend|ui"; "i"))' > /dev/null; then
        echo "✅ PASS: Frontend Team included (correct - dashboard UI needed)"
    else
        echo "⚠️  WARNING: No Frontend Team (dashboard needs UI)"
    fi
    
    echo ""
    echo "================================================================================"
    echo "📄 DOCUMENTS GENERATED"
    echo "================================================================================"
    echo ""
    
    brd_url=$(echo "$response" | jq -r '.brd_url // "Not generated"')
    excel_url=$(echo "$response" | jq -r '.excel_url // "Not generated"')
    
    echo "BRD: $brd_url"
    echo "Excel: $excel_url"
    
    echo ""
    echo "================================================================================"
    echo "✅ TEST COMPLETE"
    echo "================================================================================"
else
    echo "❌ Request failed or returned invalid JSON"
    echo "Response: $response"
fi

