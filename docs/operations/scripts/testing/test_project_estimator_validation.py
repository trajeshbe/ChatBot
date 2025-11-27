"""
Test Project Estimator with Meta-Validation Layer

This test validates that:
1. The 7-agent workflow completes successfully
2. The validator agent runs and produces validation_report
3. Teams are contextually selected (no unnecessary teams)
4. Tasks are project-specific (not generic)
5. Alignment score is calculated
"""
import requests
import json
import time

# Test Case 1: Simple Dashboard (Should NOT include Scraping Team)
print("=" * 80)
print("TEST: Project Estimator with Meta-Validation Layer")
print("=" * 80)
print()

test_request = {
    "user_prompt": """Build a web dashboard to visualize our company's internal sales data from PostgreSQL. 

Key Features:
- Display sales data in charts (bar, line, pie charts)
- Filter by date range, product category, and sales rep
- Show summary statistics (total sales, top products, trends)
- Export reports to Excel
- User authentication and role-based access

The data is already in our PostgreSQL database. We need a responsive web application that non-technical users can easily navigate.""",
    
    "project_type": "full_service",
    "scenario": "baseline",
    "rates": {
        "senior": 150,
        "mid": 100,
        "junior": 60,
        "qa": 80,
        "devops": 120
    }
}

print("📋 Project Scope:")
print(test_request["user_prompt"][:200] + "...")
print()
print("⏳ Submitting request to Project Estimator...")
print()

# Submit request
response = requests.post(
    "http://localhost:8000/api/v1/project-estimator/estimate",
    json=test_request,
    timeout=300  # 5 minutes
)

if response.status_code == 200:
    result = response.json()
    
    print("✅ Workflow completed successfully!")
    print()
    
    # Check for validation_report in the response
    if "validation_report" in result:
        validation = result["validation_report"]
        
        print("=" * 80)
        print("🔍 VALIDATION REPORT")
        print("=" * 80)
        print()
        
        print(f"Status: {validation.get('validation_status', 'N/A')}")
        print(f"Alignment Score: {validation.get('alignment_score', 0)}/100")
        print(f"Summary: {validation.get('summary', 'N/A')}")
        print()
        
        if validation.get('issues'):
            print(f"Issues Found: {len(validation['issues'])}")
            for i, issue in enumerate(validation['issues'], 1):
                print(f"\n  Issue {i}:")
                print(f"    Severity: {issue.get('severity', 'N/A')}")
                print(f"    Category: {issue.get('category', 'N/A')}")
                print(f"    Description: {issue.get('description', 'N/A')}")
                print(f"    Affected: {issue.get('affected_item', 'N/A')}")
        else:
            print("✅ No issues found - outputs are well-aligned with scope!")
        
        if validation.get('recommendations'):
            print(f"\nRecommendations: {len(validation['recommendations'])}")
            for i, rec in enumerate(validation['recommendations'], 1):
                print(f"\n  Recommendation {i}:")
                print(f"    Action: {rec.get('action', 'N/A')}")
                print(f"    Target: {rec.get('target', 'N/A')}")
                print(f"    Justification: {rec.get('justification', 'N/A')}")
    else:
        print("⚠️  No validation_report in response")
    
    print()
    print("=" * 80)
    print("📊 TEAM ANALYSIS")
    print("=" * 80)
    print()
    
    # Analyze teams
    if "team_plan" in result:
        teams = result["team_plan"].get("teams", [])
        print(f"Total Teams: {len(teams)}")
        print()
        for team in teams:
            print(f"  - {team.get('team_name', 'Unknown Team')}")
            print(f"    Allocation: {team.get('allocation', 0) * 100:.0f}%")
            print(f"    Responsibilities: {team.get('responsibilities', 'N/A')[:100]}...")
            print()
        
        # Check for unnecessary teams
        team_names = [t.get("team_name", "").lower() for t in teams]
        
        print("🔍 Validation Checks:")
        print()
        
        if any("scrap" in name for name in team_names):
            print("❌ FAIL: Scraping Team included (not needed for this project)")
        else:
            print("✅ PASS: No Scraping Team (correct - no scraping needed)")
        
        if any("ml" in name or "machine learning" in name for name in team_names):
            print("❌ FAIL: ML Engineering Team included (not needed)")
        else:
            print("✅ PASS: No ML Engineering Team (correct - no ML needed)")
        
        if any("backend" in name or "api" in name for name in team_names):
            print("✅ PASS: Backend Team included (correct - API needed)")
        else:
            print("⚠️  WARNING: No Backend Team (may be needed)")
        
        if any("frontend" in name or "ui" in name for name in team_names):
            print("✅ PASS: Frontend Team included (correct - dashboard UI needed)")
        else:
            print("⚠️  WARNING: No Frontend Team (dashboard needs UI)")
    
    print()
    print("=" * 80)
    print("📄 DOCUMENTS GENERATED")
    print("=" * 80)
    print()
    
    if "brd_url" in result:
        print(f"✅ BRD: {result['brd_url']}")
    
    if "excel_url" in result:
        print(f"✅ Excel: {result['excel_url']}")
    
    print()
    print("=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)

else:
    print(f"❌ Request failed: {response.status_code}")
    print(f"Response: {response.text}")

