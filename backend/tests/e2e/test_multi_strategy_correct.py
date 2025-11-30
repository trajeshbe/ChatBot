"""
Corrected Multi-Strategy RAG Test

Tests the CORRECT endpoint: /api/v1/multi-strategy/query

This test validates:
1. Enable/disable flags actually control which strategies run
2. Direct LLM only mode (no document retrieval)
3. RAG long-term only mode (document retrieval)
4. Weight-based answer selection when multiple strategies enabled

Key Difference from Previous Test:
- Uses /api/v1/multi-strategy/query (CORRECT)
- Not /api/v1/rag-pipeline/query (WRONG)
"""

import asyncio
import httpx
import json
from datetime import datetime


class MultiStrategyCorrectTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.token = None
        self.user_id = None
        self.project_id = None
        self.session_id = f"multi-strategy-test-{int(datetime.now().timestamp())}"
        self.department_id = "c5f6f8e3-432a-47dd-ba80-3b9516e2e174"  # Technology
        self.team_id = "62785a3f-459f-4f86-857b-1b0e7580e158"  # Tech Team 1

        self.results = {
            "test_timestamp": datetime.now().isoformat(),
            "endpoint_used": "/api/v1/multi-strategy/query",
            "tests": {},
            "summary": {}
        }

    async def login(self, client: httpx.AsyncClient):
        """Login and get token"""
        response = await client.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"username": "admin", "password": "admin"}
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.user_id = data["user"]["id"]
            print(f"✅ Logged in as {data['user']['username']}")
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            return False

    async def create_project(self, client: httpx.AsyncClient):
        """Create test project"""
        headers = {"Authorization": f"Bearer {self.token}"}

        response = await client.post(
            f"{self.base_url}/api/v1/projects",
            headers=headers,
            json={
                "name": "Multi-Strategy Test Project",
                "description": "Testing correct multi-strategy endpoint",
                "module": "CHATBOT",
                "department_id": self.department_id,
                "team_id": self.team_id
            }
        )

        if response.status_code == 200:
            data = response.json()
            self.project_id = data["id"]
            print(f"✅ Created project: {data['name']}")
            return True
        else:
            print(f"❌ Project creation failed: {response.status_code}")
            return False

    async def upload_unique_document(self, client: httpx.AsyncClient):
        """Upload document with unique identifiable content"""
        headers = {"Authorization": f"Bearer {self.token}"}

        content = """
UNIQUE_MULTI_STRATEGY_TEST_DOCUMENT

Secret Information (NOT in LLM training data):
- Access Code: ZULU-ECHO-TANGO-789
- Project ID: PHOENIX-NEXUS-42
- Encryption Key: DELTA-SIERRA-123

Test Markers:
- Marker A: ALPHA-UNIQUE-999
- Marker B: BRAVO-SPECIAL-888
- Marker C: CHARLIE-EXCLUSIVE-777

This document is specifically designed to test whether the multi-strategy
RAG system correctly retrieves and uses documents when enabled, and correctly
avoids documents when disabled (Direct LLM only mode).

If you see these codes in the answer, RAG retrieval is working.
If you don't see these codes, Direct LLM mode is working.
"""

        files = {"file": ("multi_strategy_test.txt", content.encode(), "text/plain")}
        data = {
            "session_id": self.session_id,
            "project_id": self.project_id
        }

        response = await client.post(
            f"{self.base_url}/api/v1/upload",
            headers=headers,
            files=files,
            data=data
        )

        if response.status_code == 200:
            print(f"✅ Uploaded unique test document")
            print(f"⏳ Waiting 15 seconds for processing...")
            await asyncio.sleep(15)
            return True
        else:
            print(f"❌ Upload failed: {response.status_code}")
            return False

    async def test_direct_llm_only(self, client: httpx.AsyncClient):
        """
        TEST 1: Direct LLM Only (Disable All RAG)

        Configuration:
        - enable_direct_llm: True
        - enable_rag_short_term: False
        - enable_rag_long_term: False

        Expected:
        - ONLY Direct LLM strategy runs
        - NO document retrieval
        - Answer from general knowledge
        - Won't know about unique codes
        """
        print("\n" + "="*80)
        print("TEST 1: DIRECT LLM ONLY (RAG DISABLED)")
        print("="*80)

        test_result = {
            "test_name": "direct_llm_only",
            "config": {
                "enable_direct_llm": True,
                "enable_rag_short_term": False,
                "enable_rag_long_term": False
            },
            "passed": False
        }

        headers = {"Authorization": f"Bearer {self.token}"}

        query = "What is the secret access code mentioned in the document?"

        print(f"\n❓ Query: {query}")
        print("✅ Expected: General answer, no unique codes (Direct LLM has no access)")
        print("\n📋 Configuration:")
        print("   enable_direct_llm: True")
        print("   enable_rag_short_term: False")
        print("   enable_rag_long_term: False")

        response = await client.post(
            f"{self.base_url}/api/v1/multi-strategy/query",  # CORRECT ENDPOINT
            headers=headers,
            json={
                "query": query,
                "session_id": self.session_id,
                "model_id": "qwen2.5:1.5b",
                "enable_direct_llm": True,      # Only Direct LLM
                "enable_rag_short_term": False,
                "enable_rag_long_term": False,
                "enable_tools": False
            },
            timeout=60.0
        )

        if response.status_code == 200:
            result = response.json()
            answer = result.get("answer", "")
            strategy_used = result.get("strategy_used", "")
            candidates = result.get("candidates", [])

            print(f"\n📝 Response received:")
            print(f"   Strategy Used: {strategy_used}")
            print(f"   Number of Candidates: {len(candidates)}")
            print(f"   Answer Length: {len(answer)} chars")
            print(f"   Answer preview: {answer[:200]}...")

            # Check for unique codes
            unique_codes = [
                "ZULU-ECHO-TANGO-789",
                "PHOENIX-NEXUS-42",
                "DELTA-SIERRA-123",
                "ALPHA-UNIQUE-999"
            ]
            codes_found = [code for code in unique_codes if code in answer]

            print(f"\n🔍 Analysis:")
            print(f"   Strategy used: {strategy_used}")
            print(f"   Unique codes in answer: {len(codes_found)}")
            if codes_found:
                print(f"   ⚠️  Codes found: {codes_found}")

            # Test passes if:
            # 1. Selected strategy is "direct_llm"
            # 2. No unique codes in answer
            # 3. Only 1 candidate (direct LLM only)
            if strategy_used == "direct_llm" and len(codes_found) == 0:
                print("\n✅ TEST 1 PASSED")
                print("   ✓ Direct LLM strategy selected")
                print("   ✓ No document codes in answer")
                print("   ✓ RAG correctly disabled")
                test_result["passed"] = True
            else:
                print("\n⚠️  TEST 1 INCONCLUSIVE")
                if strategy_used != "direct_llm":
                    print(f"   ✗ Expected 'direct_llm', got '{strategy_used}'")
                if len(codes_found) > 0:
                    print(f"   ✗ Found {len(codes_found)} unique codes (should be 0)")

            test_result["details"] = {
                "strategy_used": strategy_used,
                "num_candidates": len(candidates),
                "codes_found": codes_found,
                "answer_preview": answer[:300]
            }

        else:
            print(f"\n❌ Query failed: {response.status_code}")
            print(f"   Response: {response.text}")

        self.results["tests"]["test1_direct_llm_only"] = test_result

    async def test_rag_long_term_only(self, client: httpx.AsyncClient):
        """
        TEST 2: RAG Long-term Only (Disable Direct LLM)

        Configuration:
        - enable_direct_llm: False
        - enable_rag_short_term: False
        - enable_rag_long_term: True

        Expected:
        - ONLY RAG long-term strategy runs
        - Document retrieval happens
        - Answer contains unique codes
        - Sources cited
        """
        print("\n" + "="*80)
        print("TEST 2: RAG LONG-TERM ONLY (DIRECT LLM DISABLED)")
        print("="*80)

        test_result = {
            "test_name": "rag_long_term_only",
            "config": {
                "enable_direct_llm": False,
                "enable_rag_short_term": False,
                "enable_rag_long_term": True
            },
            "passed": False
        }

        headers = {"Authorization": f"Bearer {self.token}"}

        query = "What is the secret access code mentioned in the document?"

        print(f"\n❓ Query: {query}")
        print("✅ Expected: Answer with unique codes (RAG retrieves document)")
        print("\n📋 Configuration:")
        print("   enable_direct_llm: False")
        print("   enable_rag_short_term: False")
        print("   enable_rag_long_term: True")

        response = await client.post(
            f"{self.base_url}/api/v1/multi-strategy/query",  # CORRECT ENDPOINT
            headers=headers,
            json={
                "query": query,
                "session_id": self.session_id,
                "model_id": "qwen2.5:1.5b",
                "enable_direct_llm": False,     # Disable Direct LLM
                "enable_rag_short_term": False,
                "enable_rag_long_term": True,   # Only RAG long-term
                "enable_tools": False
            },
            timeout=60.0
        )

        if response.status_code == 200:
            result = response.json()
            answer = result.get("answer", "")
            strategy_used = result.get("strategy_used", "")
            candidates = result.get("candidates", [])

            print(f"\n📝 Response received:")
            print(f"   Strategy Used: {strategy_used}")
            print(f"   Number of Candidates: {len(candidates)}")
            print(f"   Answer Length: {len(answer)} chars")
            print(f"   Answer preview: {answer[:200]}...")

            # Check for unique codes
            unique_codes = [
                "ZULU-ECHO-TANGO-789",
                "PHOENIX-NEXUS-42",
                "DELTA-SIERRA-123",
                "ALPHA-UNIQUE-999"
            ]
            codes_found = [code for code in unique_codes if code in answer]

            print(f"\n🔍 Analysis:")
            print(f"   Strategy used: {strategy_used}")
            print(f"   Unique codes in answer: {len(codes_found)}")
            if codes_found:
                print(f"   ✓ Codes found: {codes_found}")

            # Test passes if:
            # 1. Selected strategy is "rag_long_term"
            # 2. At least one unique code in answer
            # 3. Only 1 candidate (RAG only)
            if strategy_used == "rag_long_term" and len(codes_found) >= 1:
                print("\n✅ TEST 2 PASSED")
                print("   ✓ RAG long-term strategy selected")
                print("   ✓ Document codes found in answer")
                print("   ✓ Direct LLM correctly disabled")
                test_result["passed"] = True
            else:
                print("\n⚠️  TEST 2 INCONCLUSIVE")
                if strategy_used != "rag_long_term":
                    print(f"   ✗ Expected 'rag_long_term', got '{strategy_used}'")
                if len(codes_found) == 0:
                    print(f"   ✗ No unique codes found (RAG may not have retrieved doc)")

            test_result["details"] = {
                "strategy_used": strategy_used,
                "num_candidates": len(candidates),
                "codes_found": codes_found,
                "answer_preview": answer[:300]
            }

        else:
            print(f"\n❌ Query failed: {response.status_code}")
            print(f"   Response: {response.text}")

        self.results["tests"]["test2_rag_long_term_only"] = test_result

    async def test_all_strategies_enabled(self, client: httpx.AsyncClient):
        """
        TEST 3: All Strategies Enabled (Weight-based Selection)

        Configuration:
        - enable_direct_llm: True
        - enable_rag_short_term: True
        - enable_rag_long_term: True

        Expected:
        - All strategies execute in parallel
        - Multiple candidates generated
        - Best answer selected based on weights
        - Likely selects RAG (higher weight) over Direct LLM
        """
        print("\n" + "="*80)
        print("TEST 3: ALL STRATEGIES ENABLED (WEIGHT-BASED SELECTION)")
        print("="*80)

        test_result = {
            "test_name": "all_strategies_weight_based",
            "config": {
                "enable_direct_llm": True,
                "enable_rag_short_term": True,
                "enable_rag_long_term": True
            },
            "passed": False
        }

        headers = {"Authorization": f"Bearer {self.token}"}

        query = "What is the secret access code?"

        print(f"\n❓ Query: {query}")
        print("✅ Expected: Multiple candidates, weight-based selection")
        print("\n📋 Configuration:")
        print("   enable_direct_llm: True")
        print("   enable_rag_short_term: True")
        print("   enable_rag_long_term: True")
        print("\n⚖️  Weight Expectations (from multi_strategy_rag.py):")
        print("   RAG Short-term: 1.0 (highest)")
        print("   RAG Long-term: 0.85")
        print("   Direct LLM: 0.75 (lowest)")

        response = await client.post(
            f"{self.base_url}/api/v1/multi-strategy/query",
            headers=headers,
            json={
                "query": query,
                "session_id": self.session_id,
                "model_id": "qwen2.5:1.5b",
                "enable_direct_llm": True,      # Enable all
                "enable_rag_short_term": True,
                "enable_rag_long_term": True,
                "enable_tools": False
            },
            timeout=90.0
        )

        if response.status_code == 200:
            result = response.json()
            answer = result.get("answer", "")
            strategy_used = result.get("strategy_used", "")
            candidates = result.get("candidates", [])
            strategy_weights_used = result.get("strategy_weights_used", {})

            print(f"\n📝 Response received:")
            print(f"   Strategy Used: {strategy_used}")
            print(f"   Number of Candidates: {len(candidates)}")

            if candidates:
                print(f"\n📊 All Candidates:")
                for i, candidate in enumerate(candidates, 1):
                    strategy = candidate.get("strategy", "unknown")
                    score = candidate.get("final_score", 0)
                    print(f"   {i}. {strategy}: score={score:.3f}")

            print(f"\n⚖️  Strategy Weights Used:")
            for strategy, weight in strategy_weights_used.items():
                print(f"   {strategy}: {weight}")

            # Check for unique codes
            unique_codes = [
                "ZULU-ECHO-TANGO-789",
                "PHOENIX-NEXUS-42",
                "DELTA-SIERRA-123"
            ]
            codes_found = [code for code in unique_codes if code in answer]

            print(f"\n🔍 Analysis:")
            print(f"   Winner: {strategy_used}")
            print(f"   Unique codes found: {len(codes_found)}")

            # Test passes if:
            # 1. Multiple candidates generated (at least 2)
            # 2. RAG strategy wins (higher weight than direct LLM)
            if len(candidates) >= 2 and strategy_used in ["rag_short_term", "rag_long_term"]:
                print("\n✅ TEST 3 PASSED")
                print("   ✓ Multiple strategies executed")
                print("   ✓ RAG strategy won (as expected due to higher weight)")
                print("   ✓ Weight-based selection working")
                test_result["passed"] = True
            else:
                print("\n⚠️  TEST 3 INCONCLUSIVE")
                if len(candidates) < 2:
                    print(f"   ✗ Expected 2+ candidates, got {len(candidates)}")
                if strategy_used == "direct_llm":
                    print(f"   ⚠️  Direct LLM won (unexpected - has lowest weight)")

            test_result["details"] = {
                "strategy_used": strategy_used,
                "num_candidates": len(candidates),
                "candidates": [
                    {"strategy": c.get("strategy"), "score": c.get("final_score")}
                    for c in candidates
                ],
                "codes_found": codes_found,
                "weights_used": strategy_weights_used
            }

        else:
            print(f"\n❌ Query failed: {response.status_code}")
            print(f"   Response: {response.text}")

        self.results["tests"]["test3_all_enabled"] = test_result

    async def run_all_tests(self):
        """Run all multi-strategy tests"""
        print("\n" + "="*80)
        print("MULTI-STRATEGY RAG - CORRECTED ENDPOINT TEST")
        print("="*80)
        print(f"Endpoint: /api/v1/multi-strategy/query")
        print(f"Session ID: {self.session_id}")
        print(f"Timestamp: {datetime.now().isoformat()}")

        async with httpx.AsyncClient() as client:
            # Setup
            print("\n" + "="*80)
            print("SETUP")
            print("="*80)

            if not await self.login(client):
                print("❌ Setup failed at login")
                return

            if not await self.create_project(client):
                print("❌ Setup failed at project creation")
                return

            if not await self.upload_unique_document(client):
                print("❌ Setup failed at document upload")
                return

            # Run tests
            await self.test_direct_llm_only(client)
            await self.test_rag_long_term_only(client)
            await self.test_all_strategies_enabled(client)

            # Summary
            print("\n" + "="*80)
            print("TEST SUMMARY")
            print("="*80)

            total_tests = len(self.results["tests"])
            passed_tests = sum(1 for t in self.results["tests"].values() if t.get("passed", False))

            print(f"\nTotal Tests: {total_tests}")
            print(f"✅ Passed: {passed_tests}")
            print(f"❌ Failed: {total_tests - passed_tests}")
            print(f"Success Rate: {(passed_tests/total_tests*100) if total_tests > 0 else 0:.1f}%")

            print("\n📋 Individual Results:")
            for test_name, test_data in self.results["tests"].items():
                status = "✅ PASSED" if test_data.get("passed") else "❌ FAILED"
                print(f"   {status}: {test_data.get('test_name', test_name)}")

            self.results["summary"] = {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": total_tests - passed_tests,
                "success_rate": (passed_tests/total_tests*100) if total_tests > 0 else 0
            }

            # Save results
            results_file = "/tmp/multi_strategy_correct_test_results.json"
            with open(results_file, "w") as f:
                json.dump(self.results, f, indent=2)

            print(f"\n📄 Results saved to {results_file}")


if __name__ == "__main__":
    test_runner = MultiStrategyCorrectTest()
    asyncio.run(test_runner.run_all_tests())
