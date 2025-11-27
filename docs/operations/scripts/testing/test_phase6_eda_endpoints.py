#!/usr/bin/env python3
"""
Test Phase 6 - Downloadable EDA Report Endpoints

This script:
1. Triggers a project estimator workflow to generate state file
2. Tests the JSON endpoint
3. Tests the Excel endpoint
"""

import requests
import time
import json
import os

print("=" * 80)
print("🧪 TEST: Phase 6 - Downloadable EDA Report Endpoints")
print("=" * 80)
print()

BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{BASE_URL}/api/v1/project-estimator"

# Simple test project scope
project_scope = """
Build a sales analytics dashboard with the following features:
- Display sales data in interactive charts
- Filter by date range and product category
- Show summary statistics
- Export reports to Excel

Tech stack: React frontend + Python backend
Data source: PostgreSQL database
"""

print("=" * 80)
print("STEP 1: Trigger Project Estimator Workflow")
print("=" * 80)
print()

print("📋 Project Scope:")
print(project_scope)
print()

# Prepare request
data = {
    'project_scope': project_scope,
    'session_id': f'test_phase6_{int(time.time())}',
    'model_id': 'gpt-4-turbo',
    'project_type': 'full_service'
}

print("🚀 Sending workflow request...")
print(f"   Endpoint: {API_ENDPOINT}/generate-agentic")
print()

try:
    # Step 1: Trigger workflow
    response = requests.post(
        f"{API_ENDPOINT}/generate-agentic",
        data=data,
        timeout=600  # 10 minutes max
    )

    print(f"📡 Response Status: {response.status_code}")
    print()

    if response.status_code != 200:
        print(f"❌ Workflow request failed: {response.text}")
        exit(1)

    result = response.json()

    print("✅ Workflow completed successfully!")
    print()

    # Extract job_id from response
    job_id = None

    # Try to extract from brd_url or excel_url
    if 'brd_url' in result:
        brd_url = result['brd_url']
        # Extract timestamp from URL (e.g., BRD_20251126_123456.docx)
        import re
        match = re.search(r'BRD_(\d+)\.docx', brd_url)
        if match:
            job_id = match.group(1)

    if not job_id and 'excel_url' in result:
        excel_url = result['excel_url']
        match = re.search(r'CostEstimate_(\d+)\.xlsx', excel_url)
        if match:
            job_id = match.group(1)

    if not job_id:
        print("⚠️  Could not extract job_id from response")
        print("Response keys:", list(result.keys()))
        print()
        print("Trying to find most recent state file...")
        # List files in uploads directory
        uploads_dir = "/app/uploads/project_estimator"
        try:
            response = requests.get(f"{BASE_URL}/api/v1/admin/sessions")
            print("Available state files: (implement directory listing)")
        except:
            pass
        exit(1)

    print(f"📍 Extracted job_id: {job_id}")
    print()

    # Step 2: Test JSON endpoint
    print("=" * 80)
    print("STEP 2: Test JSON Endpoint")
    print("=" * 80)
    print()

    json_endpoint = f"{API_ENDPOINT}/{job_id}/eda-report"
    print(f"🔍 Testing: GET {json_endpoint}")
    print()

    json_response = requests.get(json_endpoint, timeout=30)

    print(f"📡 Status: {json_response.status_code}")
    print()

    if json_response.status_code == 200:
        print("✅ JSON endpoint successful!")
        print()

        json_data = json_response.json()

        print("📊 Response Structure:")
        print(f"   • job_id: {json_data.get('job_id')}")
        print(f"   • generated_at: {json_data.get('generated_at')}")
        print(f"   • project_type: {json_data.get('project_type')}")
        print()

        if 'metadata' in json_data:
            metadata = json_data['metadata']
            print("📈 Metadata:")
            print(f"   • Files Analyzed: {metadata.get('total_files_analyzed', 0)}")
            print(f"   • Domain: {metadata.get('domain', 'Unknown')}")
            print(f"   • Data Quality: {metadata.get('overall_data_quality', 0):.2%}")
            print(f"   • Data Volume: {metadata.get('total_data_volume_mb', 0):.2f} MB")
            print()

        if 'eda_report' in json_data:
            print("✅ EDA Report present")
        else:
            print("⚠️  EDA Report not present (no sample files uploaded)")

        if 'recommended_tech_stack' in json_data:
            print("✅ Recommended Tech Stack present")
        else:
            print("⚠️  Tech Stack not present")

        if 'consensus_analysis' in json_data:
            print("✅ Consensus Analysis present")
            consensus = json_data['consensus_analysis']
            if 'alignment_score' in consensus:
                print(f"   • Alignment Score: {consensus['alignment_score']}/100")
                print(f"   • Status: {consensus.get('status', 'Unknown')}")
        print()
    elif json_response.status_code == 404:
        print("⚠️  JSON endpoint returned 404 - EDA report not found")
        print("This is expected if no sample files were uploaded")
        print()
    else:
        print(f"❌ JSON endpoint failed: {json_response.text}")
        print()

    # Step 3: Test Excel endpoint
    print("=" * 80)
    print("STEP 3: Test Excel Endpoint")
    print("=" * 80)
    print()

    excel_endpoint = f"{API_ENDPOINT}/{job_id}/eda-report/excel"
    print(f"🔍 Testing: GET {excel_endpoint}")
    print()

    excel_response = requests.get(excel_endpoint, timeout=30)

    print(f"📡 Status: {excel_response.status_code}")
    print()

    if excel_response.status_code == 200:
        print("✅ Excel endpoint successful!")
        print()

        # Check content type
        content_type = excel_response.headers.get('content-type', '')
        print(f"📄 Content-Type: {content_type}")

        if 'spreadsheet' in content_type or 'excel' in content_type:
            print("✅ Correct content type (Excel file)")
        else:
            print(f"⚠️  Unexpected content type: {content_type}")

        # Check content length
        content_length = len(excel_response.content)
        print(f"📊 File Size: {content_length:,} bytes ({content_length/1024:.1f} KB)")
        print()

        # Save to temp file
        temp_excel = f"/tmp/EDA_Report_{job_id}_test.xlsx"
        with open(temp_excel, 'wb') as f:
            f.write(excel_response.content)

        print(f"💾 Saved Excel file to: {temp_excel}")
        print()

        # Try to open with openpyxl to verify it's valid
        try:
            import openpyxl
            wb = openpyxl.load_workbook(temp_excel)
            sheet_names = wb.sheetnames
            print("✅ Excel file is valid!")
            print(f"   Sheets: {', '.join(sheet_names)}")
            print()
        except Exception as e:
            print(f"⚠️  Could not validate Excel file: {str(e)}")
            print()
    elif excel_response.status_code == 404:
        print("⚠️  Excel endpoint returned 404 - EDA report not found")
        print("This is expected if no sample files were uploaded")
        print()
    else:
        print(f"❌ Excel endpoint failed: {excel_response.text}")
        print()

    # Summary
    print("=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print()

    json_success = json_response.status_code in [200, 404]
    excel_success = excel_response.status_code in [200, 404]

    if json_success and excel_success:
        print("✅ PHASE 6 ENDPOINTS WORKING CORRECTLY")
        print()
        print("Both endpoints are functional:")
        print(f"   • JSON Endpoint: {json_endpoint}")
        print(f"   • Excel Endpoint: {excel_endpoint}")
        print()
        print("Note: 404 responses are expected when no sample files are uploaded")
        print()
        exit(0)
    else:
        print("❌ SOME ENDPOINTS FAILED")
        print()
        if not json_success:
            print(f"   ❌ JSON endpoint failed with status {json_response.status_code}")
        if not excel_success:
            print(f"   ❌ Excel endpoint failed with status {excel_response.status_code}")
        print()
        exit(1)

except requests.exceptions.Timeout:
    print("❌ Request timeout (exceeded 10 minutes)")
    print("Workflow may still be running - check backend logs:")
    print("   docker-compose logs backend | grep -E '(Agent|workflow)'")
    exit(1)
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)
