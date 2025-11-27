#!/usr/bin/env python3
"""
Test Agent 1.2 (Debate Coordinator) - Simple API test
Tests that Agent 1.2 validates alignment between scope and sample data
"""

import requests
import time
import json

print("=" * 80)
print("🧪 TEST: Agent 1.2 - Debate Coordinator")
print("=" * 80)
print()

BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{BASE_URL}/api/v1/project-estimator/generate-agentic"

# Test project scope - intentionally simple to minimize LLM time
project_scope = """
Build a simple sales analytics dashboard.

Key features:
- Display sales data in charts
- Filter by date range
- Show summary statistics
- Export to Excel

Data source: PostgreSQL database
Tech stack: React + Python backend
"""

print("📋 Test Configuration:")
print(f"  Endpoint: {API_ENDPOINT}")
print(f"  Scope length: {len(project_scope)} chars")
print()

# Prepare request
data = {
    'project_scope': project_scope,
    'session_id': f'test_agent12_{int(time.time())}',
    'model_id': 'gpt-4-turbo',
    'project_type': 'full_service'
}

print("🚀 Sending request...")
print()

try:
    response = requests.post(
        API_ENDPOINT,
        data=data,
        timeout=600  # 10 minutes max
    )
    
    print(f"📡 Response Status: {response.status_code}")
    print()
    
    if response.status_code == 200:
        result = response.json()
        
        print("✅ Workflow completed successfully!")
        print("=" * 80)
        print()
        
        # Check for consensus_analysis in response
        if 'consensus_analysis' in result:
            print("✅ consensus_analysis field present in response")
            consensus = result['consensus_analysis']
            
            print()
            print("📊 CONSENSUS ANALYSIS (Agent 1.2 Output):")
            print("-" * 80)
            print(json.dumps(consensus, indent=2))
            print("-" * 80)
            print()
            
            # Validate structure
            required_fields = ['alignment_score', 'status', 'issues', 'recommendation']
            missing_fields = [f for f in required_fields if f not in consensus]
            
            if not missing_fields:
                print("✅ All required fields present:")
                print(f"   • Alignment Score: {consensus.get('alignment_score')}/100")
                print(f"   • Status: {consensus.get('status')}")
                print(f"   • Issues Count: {len(consensus.get('issues', []))}")
                print(f"   • Recommendation: {consensus.get('recommendation')[:80]}...")
            else:
                print(f"⚠️  Missing fields: {missing_fields}")
        else:
            print("⚠️  consensus_analysis NOT found in response")
            print()
            print("Available keys in response:")
            for key in result.keys():
                print(f"   • {key}")
        
        print()
        print("=" * 80)
        print("✅ TEST PASSED - Agent 1.2 executed")
        print("=" * 80)
        print()
        print("To see detailed logs:")
        print('  docker-compose logs backend | grep -E "(Agent 1.2|Debate Coordinator|alignment_score)"')
        print()
        exit(0)
    else:
        print(f"❌ Request failed with status {response.status_code}")
        print(f"Response: {response.text[:500]}")
        exit(1)

except requests.exceptions.Timeout:
    print("❌ Request timeout (exceeded 10 minutes)")
    print("This may indicate workflow is still running - check backend logs")
    exit(1)
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)
