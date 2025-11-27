#!/bin/bash

echo "================================================================================"
echo "END-TO-END TEST: Project Estimator with Sample Files + Meta-Validation"
echo "================================================================================"
echo ""

# Create sample files
echo "📁 Creating sample files..."
echo ""

# 1. Create sample BRD (PowerPoint/PDF substitute - using text file for simplicity)
cat > /tmp/sample_brd.txt << 'BRDSAMPLE'
BUSINESS REQUIREMENTS DOCUMENT - SAMPLE

Project: E-Commerce Platform Development

1. Executive Summary
   - Build modern e-commerce platform
   - Target: B2C online retail
   - Timeline: 16 weeks

2. Team Structure
   - Backend Team (40%)
   - Frontend Team (30%)
   - QA Team (15%)
   - DevOps Team (15%)

3. Key Deliverables
   - User authentication system
   - Product catalog management
   - Shopping cart and checkout
   - Payment gateway integration
   - Admin dashboard
BRDSAMPLE

# 2. Create sample cost estimate (Excel substitute - CSV)
cat > /tmp/sample_cost.csv << 'COSTSAMPLE'
Team,Role,Hours,Rate,Total
Backend Engineering,Senior,320,150,48000
Backend Engineering,Mid,240,100,24000
Frontend Engineering,Senior,200,150,30000
Frontend Engineering,Mid,160,100,16000
QA Team,QA Lead,120,80,9600
DevOps Team,Senior DevOps,100,120,12000
COSTSAMPLE

# 3. Create sample data (JSON)
cat > /tmp/sample_data.json << 'DATASAMPLE'
{
  "products": [
    {"id": 1, "name": "Product A", "price": 99.99, "category": "Electronics"},
    {"id": 2, "name": "Product B", "price": 49.99, "category": "Books"},
    {"id": 3, "name": "Product C", "price": 149.99, "category": "Clothing"}
  ],
  "orders": [
    {"order_id": 1001, "customer_id": 501, "total": 199.98, "status": "completed"},
    {"order_id": 1002, "customer_id": 502, "total": 49.99, "status": "pending"}
  ],
  "customers": 5000,
  "monthly_transactions": 15000,
  "avg_order_value": 75.50
}
DATASAMPLE

echo "✅ Sample files created:"
echo "   - BRD: /tmp/sample_brd.txt"
echo "   - Cost Estimate: /tmp/sample_cost.csv"
echo "   - Sample Data: /tmp/sample_data.json"
echo ""

# 4. Create project scope
cat > /tmp/project_scope.txt << 'SCOPESAMPLE'
Build a web dashboard to visualize our company's internal sales data from PostgreSQL.

Key Features:
- Display sales data in interactive charts (bar, line, pie charts)
- Filter by date range, product category, and sales rep
- Show summary statistics (total sales, top products, trends)
- Export reports to Excel
- User authentication and role-based access (Admin, Manager, Viewer)

Technical Requirements:
- Backend: RESTful API to query PostgreSQL database
- Frontend: Responsive web application with modern UI
- Database: Already exists with sales data (products, orders, customers)
- Scale: 5000 customers, ~15K transactions/month
- Users: ~50 concurrent users expected

The data is already in our PostgreSQL database. We need a responsive web application that non-technical users can easily navigate.
SCOPESAMPLE

echo "📋 Project Scope:"
cat /tmp/project_scope.txt | head -10
echo "   ..."
echo ""

# 5. Submit request to backend API
echo "🚀 Submitting end-to-end test to Project Estimator API..."
echo ""

response=$(curl -s -X POST "http://localhost:8000/api/v1/project-estimator/generate-agentic" \
  -F "user_prompt=@/tmp/project_scope.txt" \
  -F "project_type=full_service" \
  -F "scenario=baseline" \
  -F "senior_rate=150" \
  -F "mid_rate=100" \
  -F "junior_rate=60" \
  -F "qa_rate=80" \
  -F "devops_rate=120" \
  -F "brd_files=@/tmp/sample_brd.txt" \
  -F "cost_files=@/tmp/sample_cost.csv" \
  -F "sample_data_files=@/tmp/sample_data.json" \
  --max-time 300 2>&1)

echo "⏳ Workflow executing... (this may take 2-3 minutes)"
echo ""

# Check if response is valid JSON
if echo "$response" | jq -e . >/dev/null 2>&1; then
    echo "✅ Response received!"
    echo ""
    
    # Extract key information
    echo "================================================================================"
    echo "📊 WORKFLOW RESULTS"
    echo "================================================================================"
    echo ""
    
    # Check for validation report
    if echo "$response" | jq -e '.validation_report' >/dev/null 2>&1; then
        echo "🔍 VALIDATION REPORT:"
        echo "   Status: $(echo "$response" | jq -r '.validation_report.validation_status // "N/A"')"
        echo "   Alignment Score: $(echo "$response" | jq -r '.validation_report.alignment_score // 0')/100"
        echo "   Summary: $(echo "$response" | jq -r '.validation_report.summary // "N/A"')"
        echo ""
        
        issues_count=$(echo "$response" | jq '.validation_report.issues | length' 2>/dev/null || echo "0")
        if [ "$issues_count" -gt 0 ]; then
            echo "   Issues Found: $issues_count"
            echo "$response" | jq -r '.validation_report.issues[] | "     - [\(.severity)] \(.description)"'
        else
            echo "   ✅ No issues - well-aligned with project scope!"
        fi
        echo ""
    else
        echo "⚠️  No validation_report found in response"
        echo ""
    fi
    
    # Check teams
    if echo "$response" | jq -e '.team_plan.teams' >/dev/null 2>&1; then
        teams_count=$(echo "$response" | jq '.team_plan.teams | length')
        echo "👥 TEAMS IDENTIFIED: $teams_count"
        echo "$response" | jq -r '.team_plan.teams[] | "   - \(.team_name) (\(.allocation * 100)%)"'
        echo ""
        
        # Validation checks
        echo "🔍 VALIDATION CHECKS:"
        
        has_scraping=$(echo "$response" | jq -r '.team_plan.teams[] | select(.team_name | test("scrap"; "i")) | .team_name' | head -1)
        if [ -n "$has_scraping" ]; then
            echo "   ❌ FAIL: Scraping Team found (not needed for dashboard)"
        else
            echo "   ✅ PASS: No Scraping Team (correct)"
        fi
        
        has_ml=$(echo "$response" | jq -r '.team_plan.teams[] | select(.team_name | test("ml|machine learning"; "i")) | .team_name' | head -1)
        if [ -n "$has_ml" ]; then
            echo "   ❌ FAIL: ML Team found (not needed for simple dashboard)"
        else
            echo "   ✅ PASS: No ML Team (correct)"
        fi
        
        has_backend=$(echo "$response" | jq -r '.team_plan.teams[] | select(.team_name | test("backend|api"; "i")) | .team_name' | head -1)
        if [ -n "$has_backend" ]; then
            echo "   ✅ PASS: Backend Team found (correct - API needed)"
        else
            echo "   ⚠️  WARNING: No Backend Team (may be needed)"
        fi
        
        has_frontend=$(echo "$response" | jq -r '.team_plan.teams[] | select(.team_name | test("frontend|ui"; "i")) | .team_name' | head -1)
        if [ -n "$has_frontend" ]; then
            echo "   ✅ PASS: Frontend Team found (correct - dashboard UI needed)"
        else
            echo "   ⚠️  WARNING: No Frontend Team (dashboard needs UI)"
        fi
        
        echo ""
    fi
    
    # Check documents
    echo "📄 DOCUMENTS GENERATED:"
    brd_url=$(echo "$response" | jq -r '.brd_url // "Not generated"')
    excel_url=$(echo "$response" | jq -r '.excel_url // "Not generated"')
    
    echo "   BRD: $brd_url"
    echo "   Excel: $excel_url"
    echo ""
    
    # Check for errors
    if echo "$response" | jq -e '.errors' >/dev/null 2>&1; then
        errors=$(echo "$response" | jq -r '.errors[]' 2>/dev/null)
        if [ -n "$errors" ]; then
            echo "⚠️  ERRORS:"
            echo "$errors" | while read -r error; do
                echo "   - $error"
            done
            echo ""
        fi
    fi
    
    echo "================================================================================"
    echo "✅ END-TO-END TEST COMPLETE"
    echo "================================================================================"
    echo ""
    echo "Next Steps:"
    echo "1. Check backend logs for detailed validation output:"
    echo "   docker-compose logs backend | grep -E '(Validator|alignment_score)'"
    echo ""
    echo "2. Download and review the generated documents:"
    echo "   - BRD: $brd_url"
    echo "   - Excel: $excel_url"
    
else
    echo "❌ Request failed or returned invalid response"
    echo ""
    echo "Response:"
    echo "$response" | head -50
    echo ""
    echo "Check backend logs:"
    echo "   docker-compose logs backend --tail=100"
fi

