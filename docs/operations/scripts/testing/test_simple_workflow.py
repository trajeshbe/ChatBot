#!/usr/bin/env python3
"""
Simple test to trigger a workflow and generate state file for Phase 6 endpoint testing
"""

import requests
import time
import json

print("=" * 80)
print("🧪 SIMPLE WORKFLOW TEST - Generate State File for Phase 6")
print("=" * 80)
print()

BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{BASE_URL}/api/v1/project-estimator/generate-agentic"

# Minimal project scope
project_scope = """
Create a simple web dashboard to display sales metrics.

Features:
- Interactive charts (bar, line, pie)
- Filter by date range
- Export to Excel

Tech stack: React + Python backend
"""

print("📋 Test Configuration:")
print(f"   Endpoint: {API_ENDPOINT}")
print(f"   Scope: {len(project_scope)} characters")
print()

# Prepare minimal request (no sample files to speed up workflow)
data = {
    'project_scope': project_scope,
    'session_id': f'phase6_test_{int(time.time())}',
    'model_id': 'gpt-4-turbo',
    'project_type': 'full_service'
}

print("🚀 Submitting workflow request...")
print("   (This may take 1-2 minutes without sample files)")
print()

try:
    start_time = time.time()
    response = requests.post(API_ENDPOINT, data=data, timeout=300)
    elapsed = time.time() - start_time

    print(f"📡 Response Status: {response.status_code}")
    print(f"⏱️  Time Elapsed: {elapsed:.1f} seconds")
    print()

    if response.status_code == 200:
        result = response.json()
        print("✅ Workflow completed successfully!")
        print()

        # Extract job_id
        job_id = None
        if 'brd_url' in result:
            import re
            match = re.search(r'BRD_(\d+)\.docx', result['brd_url'])
            if match:
                job_id = match.group(1)
                print(f"📍 Extracted job_id: {job_id}")
                print()

        if job_id:
            print("✅ STATE FILE SHOULD BE GENERATED")
            print(f"   Expected path: /app/uploads/project_estimator/state_{job_id}.json")
            print()
            print("🔍 Now you can test the Phase 6 endpoints:")
            print(f"   JSON: GET {BASE_URL}/api/v1/project-estimator/{job_id}/eda-report")
            print(f"   Excel: GET {BASE_URL}/api/v1/project-estimator/{job_id}/eda-report/excel")
            print()

            # Save job_id to file for next test
            with open('/tmp/phase6_job_id.txt', 'w') as f:
                f.write(job_id)
            print(f"💾 Saved job_id to /tmp/phase6_job_id.txt")
            print()
            exit(0)
        else:
            print("⚠️  Could not extract job_id from response")
            print("Response keys:", list(result.keys()))
            exit(1)
    else:
        print(f"❌ Workflow failed with status {response.status_code}")
        print(f"Response: {response.text[:500]}")
        exit(1)

except requests.exceptions.Timeout:
    print("❌ Timeout exceeded (5 minutes)")
    exit(1)
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)
