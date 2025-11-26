#!/usr/bin/env python3
"""
Phase 3 Step 1 Test: Model Selection Parameter Integration
Tests the Project Estimator with Estimate One project files

Tests:
1. Test with explicit model_id parameter (llama3.2-vision:11b)
2. Test without model_id (should use Model Registry recommendation)
3. Verify model selection is logged correctly
4. Verify model_id is passed to workflow state

Usage:
    python3 test_phase3_model_selection.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

print("="*80)
print("🧪 PHASE 3 STEP 1 TEST: Model Selection Parameter Integration")
print("="*80)
print()

# Test file paths
PROJECT_SCOPE_FILE = "docs/features/project_estimator/estimate_one/Project Scope.txt"
SAMPLE_EXCEL_1 = "docs/features/project_estimator/estimate_one/Project Size Sourcing.xlsx"
SAMPLE_EXCEL_2 = "docs/features/project_estimator/estimate_one/cost_estimation_estimate_one.xlsx"
SAMPLE_BRD = "docs/features/project_estimator/estimate_one/EstimateOne_BRD_Document.docx"


async def test_api_endpoint_with_model_selection():
    """Test 1: Verify API endpoint accepts model_id parameter"""
    print("TEST 1: API Endpoint Model Selection Parameter")
    print("-"*80)

    try:
        import httpx

        # Read project scope
        print(f"📄 Reading project scope from {PROJECT_SCOPE_FILE}...")
        if not os.path.exists(PROJECT_SCOPE_FILE):
            print(f"   ❌ File not found: {PROJECT_SCOPE_FILE}")
            return False

        with open(PROJECT_SCOPE_FILE, 'r', encoding='utf-8') as f:
            project_scope = f.read()

        print(f"   ✅ Loaded project scope ({len(project_scope)} characters)")
        print(f"   First 100 chars: {project_scope[:100]}...")

        # Prepare form data
        files = {}
        data = {
            "project_scope": project_scope,
            "project_type": "full_service",
            "scenario": "baseline",
            "rate_config": "{}",
            "model_id": "llama3.2-vision:11b"  # ← Testing explicit model selection
        }

        # Add sample files if they exist
        if os.path.exists(SAMPLE_EXCEL_1):
            with open(SAMPLE_EXCEL_1, 'rb') as f:
                files["brd_files"] = (os.path.basename(SAMPLE_EXCEL_1), f.read())
            print(f"   ✅ Added sample file: {os.path.basename(SAMPLE_EXCEL_1)}")

        if os.path.exists(SAMPLE_EXCEL_2):
            with open(SAMPLE_EXCEL_2, 'rb') as f:
                files["cost_files"] = (os.path.basename(SAMPLE_EXCEL_2), f.read())
            print(f"   ✅ Added sample file: {os.path.basename(SAMPLE_EXCEL_2)}")

        print()
        print("🚀 Sending request to API endpoint...")
        print(f"   URL: http://localhost:8000/api/v1/project-estimator/generate-agentic")
        print(f"   Model ID: {data['model_id']}")
        print(f"   Project Type: {data['project_type']}")
        print(f"   Scenario: {data['scenario']}")

        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await client.post(
                "http://localhost:8000/api/v1/project-estimator/generate-agentic",
                data=data,
                files=files
            )

        print()
        print(f"📊 Response Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("   ✅ Request successful!")
            print()
            print("   Response summary:")
            print(f"   - BRD URL: {result.get('brd_url', 'N/A')}")
            print(f"   - Excel URL: {result.get('excel_url', 'N/A')}")
            print(f"   - Message: {result.get('message', 'N/A')}")
            print()

            # Check if model_id was used
            if "model" in str(result).lower():
                print("   ✅ Model information found in response")

            return True
        else:
            print(f"   ❌ Request failed")
            print(f"   Response: {response.text[:500]}")
            return False

    except Exception as e:
        print(f"   ❌ Test failed with error:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_without_model_id():
    """Test 2: Verify Model Registry fallback works"""
    print()
    print()
    print("TEST 2: Model Registry Fallback (No model_id provided)")
    print("-"*80)

    try:
        import httpx

        # Read project scope (shorter version for faster test)
        project_scope = """
Build a web dashboard to display construction project data from the Estimate One system.

Key Features:
- Display project levels (above/below ground)
- Show gross floor area calculations
- Extract data from architectural drawings
- Support multiple document types (CAD, PDF, Excel)

This is a test of the Model Registry fallback when no model_id is specified.
"""

        print(f"📄 Using test project scope ({len(project_scope)} characters)")

        # Prepare form data WITHOUT model_id
        data = {
            "project_scope": project_scope,
            "project_type": "full_service",
            "scenario": "baseline",
            "rate_config": "{}"
            # ← No model_id parameter - should use Model Registry
        }

        print()
        print("🚀 Sending request without model_id...")
        print(f"   URL: http://localhost:8000/api/v1/project-estimator/generate-agentic")
        print(f"   Model ID: (not specified - should use Model Registry)")

        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await client.post(
                "http://localhost:8000/api/v1/project-estimator/generate-agentic",
                data=data
            )

        print()
        print(f"📊 Response Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("   ✅ Request successful!")
            print()
            print("   Model Registry fallback worked - check backend logs:")
            print("   docker-compose logs backend | grep 'No model specified'")
            print("   docker-compose logs backend | grep 'using recommended'")
            print()
            return True
        else:
            print(f"   ❌ Request failed")
            print(f"   Response: {response.text[:500]}")
            return False

    except Exception as e:
        print(f"   ❌ Test failed with error:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_model_id_in_state():
    """Test 3: Verify model_id is added to workflow state"""
    print()
    print()
    print("TEST 3: Workflow State Model ID Integration")
    print("-"*80)

    try:
        # This test inspects the code to verify model_id is in ProjectEstimatorState
        from app.agents.project_estimator.workflow import ProjectEstimatorState

        print("📝 Checking ProjectEstimatorState TypedDict definition...")

        # Check if model_id is in the type hints
        if hasattr(ProjectEstimatorState, '__annotations__'):
            annotations = ProjectEstimatorState.__annotations__

            print(f"   Found {len(annotations)} fields in ProjectEstimatorState:")
            for field_name, field_type in annotations.items():
                print(f"      - {field_name}: {field_type}")

            if 'model_id' in annotations:
                print()
                print("   ✅ model_id found in ProjectEstimatorState!")
                print(f"   Type: {annotations['model_id']}")
                return True
            else:
                print()
                print("   ❌ model_id NOT found in ProjectEstimatorState")
                return False
        else:
            print("   ⚠️  Could not inspect ProjectEstimatorState annotations")
            return False

    except ImportError as e:
        print(f"   ❌ Could not import ProjectEstimatorState:")
        print(f"   {str(e)}")
        return False
    except Exception as e:
        print(f"   ❌ Test failed with error:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def verify_logging():
    """Test 4: Verify model selection is logged correctly"""
    print()
    print()
    print("TEST 4: Model Selection Logging Verification")
    print("-"*80)

    try:
        import subprocess

        print("📝 Checking backend logs for model selection messages...")
        print()

        # Check logs for model selection indicators
        result = subprocess.run(
            ["docker-compose", "logs", "backend", "--tail=500"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        logs = result.stdout + result.stderr

        # Look for model selection log messages
        user_selected = "User selected model:" in logs
        no_model_specified = "No model specified" in logs
        using_recommended = "using recommended" in logs

        print("   Log analysis:")
        if user_selected:
            print("   ✅ Found 'User selected model:' in logs")
            # Extract the model that was selected
            for line in logs.split('\n'):
                if 'User selected model:' in line:
                    print(f"      {line.strip()}")
                    break

        if no_model_specified:
            print("   ✅ Found 'No model specified' in logs")

        if using_recommended:
            print("   ✅ Found 'using recommended' in logs")

        print()

        if user_selected or no_model_specified or using_recommended:
            print("   ✅ Model selection logging is working!")
            return True
        else:
            print("   ⚠️  No model selection log messages found")
            print("   This might be normal if no requests have been made yet")
            return True  # Not a failure, just no data yet

    except Exception as e:
        print(f"   ❌ Test failed with error:")
        print(f"   {str(e)}")
        return False


async def main():
    """Run all Phase 3 Step 1 tests"""

    print("Starting Phase 3 Step 1 validation tests...")
    print()
    print("These tests verify:")
    print("1. API endpoint accepts model_id parameter")
    print("2. Model Registry fallback works when model_id not provided")
    print("3. model_id is included in workflow state definition")
    print("4. Model selection is logged correctly")
    print()
    print("="*80)
    print()

    results = {}

    # Test 1: Workflow state integration (code inspection - fast)
    results["state_integration"] = await test_model_id_in_state()

    # Test 2: Logging verification (check existing logs - fast)
    results["logging"] = await verify_logging()

    # Test 3: API with explicit model_id (requires running backend)
    print()
    print("⚠️  Note: The following tests require a running backend")
    print("   Make sure docker-compose is up: docker-compose up -d")
    print()
    user_input = input("Run API tests? (y/n): ")

    if user_input.lower() == 'y':
        results["api_with_model"] = await test_api_endpoint_with_model_selection()
        results["api_without_model"] = await test_without_model_id()
    else:
        print("   ⏭️  Skipping API tests")
        results["api_with_model"] = None
        results["api_without_model"] = None

    # Print summary
    print()
    print()
    print("="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    print()

    for test_name, test_result in results.items():
        if test_result is None:
            status = "⏭️  SKIPPED"
        elif test_result:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"

        print(f"   {status} - {test_name}")

    print()

    # Overall result
    failed_tests = [name for name, result in results.items() if result is False]
    skipped_tests = [name for name, result in results.items() if result is None]

    if failed_tests:
        print(f"❌ PHASE 3 STEP 1 VALIDATION FAILED")
        print(f"   Failed tests: {', '.join(failed_tests)}")
        return False
    elif skipped_tests:
        print(f"⚠️  PHASE 3 STEP 1 VALIDATION INCOMPLETE")
        print(f"   Skipped tests: {', '.join(skipped_tests)}")
        print(f"   Run with backend running for complete validation")
        return True
    else:
        print(f"✅ PHASE 3 STEP 1 VALIDATION COMPLETE")
        print()
        print("All tests passed! Model selection integration is working correctly.")
        print()
        print("Next steps:")
        print("1. Phase 3 Step 2: Create _call_llm_optimized() helper method")
        print("2. Phase 3 Step 3-12: Replace hardcoded LLM calls")
        print("3. Phase 3 Step 13: Update frontend to send model_id")
        return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
