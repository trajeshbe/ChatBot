"""
Test RAG vs Direct LLM Weight Settings

This test validates that weight configuration actually controls RAG behavior:
- Test 1: Direct LLM weight > 90% → Should use direct LLM (no document sources)
- Test 2: RAG Long-term weight > 90% → Should use RAG and retrieve documents

The idea is to verify that adjusting weights forces the system to prefer
one strategy over another.
"""

import asyncio
import httpx
import json
from datetime import datetime


class WeightsConfigTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.token = None
        self.user_id = None
        self.project_id = None
        self.session_id = f"weights-test-{int(datetime.now().timestamp())}"
        self.department_id = "c5f6f8e3-432a-47dd-ba80-3b9516e2e174"  # Technology
        self.team_id = "62785a3f-459f-4f86-857b-1b0e7580e158"  # Tech Team 1

        self.results = {
            "test_timestamp": datetime.now().isoformat(),
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
            print(f"   User ID: {self.user_id}")
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
                "name": "Weights Test Project",
                "description": "Testing RAG vs Direct LLM weights",
                "module": "CHATBOT",
                "department_id": self.department_id,
                "team_id": self.team_id
            }
        )

        if response.status_code == 200:
            data = response.json()
            self.project_id = data["id"]
            print(f"✅ Created project: {data['name']}")
            print(f"   Project ID: {self.project_id}")
            return True
        else:
            print(f"❌ Project creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    async def upload_test_document(self, client: httpx.AsyncClient):
        """Upload a document with unique, identifiable content"""
        headers = {"Authorization": f"Bearer {self.token}"}

        # Create document with very specific, unique content
        content = """
UNIQUE_DOCUMENT_MARKER_12345

This is a test document for weight configuration validation.

Key Information:
- The secret code is: ALPHA-BRAVO-CHARLIE-999
- The magic number is: 42
- The special keyword is: ZEPHYR-QUANTUM-DELTA

This document contains information that the LLM would NOT know from its
general training data. It's specifically designed to test whether RAG
retrieval is working when weights favor document-based answers.

Important Facts (NOT in LLM training data):
1. Project codename: NEBULA-X7
2. Access protocol: SIGMA-LAMBDA-9
3. Authentication sequence: THETA-OMEGA-15

If the system retrieves this document, it should be able to answer
questions about these unique markers. If it doesn't retrieve this document,
it will have to rely on general knowledge and won't know these codes.
"""

        files = {"file": ("unique_test_doc.txt", content.encode(), "text/plain")}
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
            doc_data = response.json()
            print(f"✅ Uploaded unique test document")
            print(f"   Document ID: {doc_data.get('id', 'N/A')}")
            print(f"   Waiting 15 seconds for document processing...")
            await asyncio.sleep(15)  # Wait for processing and embedding generation
            return True
        else:
            print(f"❌ Document upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    async def get_current_weights(self, client: httpx.AsyncClient):
        """Get current weight configuration"""
        headers = {"Authorization": f"Bearer {self.token}"}

        response = await client.get(
            f"{self.base_url}/api/v1/config/weights",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("data", {})
        else:
            print(f"⚠️  Failed to get weights: {response.status_code}")
            return None

    async def set_weights(self, client: httpx.AsyncClient, weight_config: dict):
        """Update weight configuration"""
        headers = {"Authorization": f"Bearer {self.token}"}

        response = await client.post(
            f"{self.base_url}/api/v1/config/weights",
            headers=headers,
            json=weight_config
        )

        if response.status_code == 200:
            return True
        else:
            print(f"⚠️  Failed to set weights: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    async def query_with_rag_pipeline(self, client: httpx.AsyncClient, query: str, session_id: str = None):
        """
        Query using RAG pipeline endpoint
        This should respect weight settings for strategy selection
        """
        headers = {"Authorization": f"Bearer {self.token}"}

        response = await client.post(
            f"{self.base_url}/api/v1/rag-pipeline/query",
            headers=headers,
            json={
                "query": query,
                "session_id": session_id or self.session_id,
                "model_name": "ollama/qwen2.5:1.5b",  # Use available model
                "use_cache": False  # Disable cache to ensure fresh results
            },
            timeout=60.0
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"   Query failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None

    async def test_direct_llm_high_weight(self, client: httpx.AsyncClient):
        """
        TEST 1: Direct LLM Weight > 90%

        Expected behavior:
        - System should prefer Direct LLM strategy
        - Answer should come from LLM general knowledge
        - Should NOT retrieve documents or very few sources
        - Answer should be general, not containing unique document markers
        """
        print("\n" + "="*80)
        print("TEST 1: DIRECT LLM HIGH WEIGHT (>90%)")
        print("="*80)

        test_result = {
            "test_name": "direct_llm_high_weight",
            "timestamp": datetime.now().isoformat(),
            "passed": False,
            "details": {}
        }

        # Save original weights
        original_weights = await self.get_current_weights(client)
        if not original_weights:
            print("❌ Failed to get original weights")
            self.results["tests"]["test1_direct_llm"] = test_result
            return

        print("\n📊 Original weights:")
        print(f"   RAG Long-term: {original_weights.get('strategy_weights', {}).get('rag_long_term', 'N/A')}")
        print(f"   Direct LLM: {original_weights.get('strategy_weights', {}).get('direct_llm', 'N/A')}")

        # Set Direct LLM weight to 0.95 (95%), RAG long-term to 0.10 (10%)
        new_weights = {
            "strategy_weights": {
                "rag_short_term": 0.05,
                "rag_hybrid": 0.05,
                "rag_long_term": 0.10,  # Very low - discourage RAG
                "direct_llm": 0.95,      # Very high - prefer Direct LLM
                "tool_navigation": 0.05,
                "tool_ocr": 0.05,
                "tool_docling": 0.05,
                "tool_web_scraping": 0.05
            }
        }

        print("\n🔧 Setting weights to favor Direct LLM:")
        print(f"   RAG Long-term: 0.10 (10%)")
        print(f"   Direct LLM: 0.95 (95%)")

        if not await self.set_weights(client, new_weights):
            print("❌ Failed to set weights")
            self.results["tests"]["test1_direct_llm"] = test_result
            return

        print("✅ Weights updated successfully")
        await asyncio.sleep(2)  # Let weights propagate

        # Query with question that has answer in document
        # If Direct LLM is working, it should NOT know about our unique codes
        query = "What is the secret code mentioned in the document?"

        print(f"\n❓ Query: {query}")
        print("   Expected: General answer or 'no information' (Direct LLM has no access to our unique code)")

        result = await self.query_with_rag_pipeline(client, query)

        if result:
            answer = result.get("answer", "")
            citations = result.get("citations", [])
            num_sources = len(citations)

            print(f"\n📝 Answer received:")
            print(f"   Length: {len(answer)} chars")
            print(f"   Sources cited: {num_sources}")
            print(f"   Answer preview: {answer[:200]}...")

            # Check if answer contains unique markers from document
            unique_markers = [
                "ALPHA-BRAVO-CHARLIE-999",
                "ZEPHYR-QUANTUM-DELTA",
                "NEBULA-X7",
                "SIGMA-LAMBDA-9",
                "THETA-OMEGA-15"
            ]

            markers_found = [marker for marker in unique_markers if marker in answer]

            print(f"\n🔍 Analysis:")
            print(f"   Unique markers in answer: {len(markers_found)}")
            if markers_found:
                print(f"   Markers found: {markers_found}")
            print(f"   Number of citations: {num_sources}")

            # Test passes if:
            # 1. Very few or no sources cited (Direct LLM should not retrieve docs)
            # 2. Answer doesn't contain our unique markers
            if num_sources <= 1 and len(markers_found) == 0:
                print("\n✅ TEST 1 PASSED")
                print("   ✓ Direct LLM weight setting works")
                print("   ✓ System did NOT retrieve document sources")
                print("   ✓ Answer is based on general knowledge")
                test_result["passed"] = True
            else:
                print("\n⚠️  TEST 1 INCONCLUSIVE")
                print(f"   - Expected 0-1 sources, got {num_sources}")
                print(f"   - Expected 0 unique markers, found {len(markers_found)}")
                if num_sources > 1:
                    print("   ⚠️  System still retrieved documents despite low RAG weight")

            test_result["details"] = {
                "weight_config": "direct_llm=0.95, rag_long_term=0.10",
                "query": query,
                "answer_length": len(answer),
                "num_sources": num_sources,
                "unique_markers_found": len(markers_found),
                "markers": markers_found,
                "answer_preview": answer[:300]
            }
        else:
            print("❌ Query failed")

        # Restore original weights
        print("\n🔄 Restoring original weights...")
        await self.set_weights(client, original_weights)

        self.results["tests"]["test1_direct_llm"] = test_result

    async def test_rag_long_term_high_weight(self, client: httpx.AsyncClient):
        """
        TEST 2: RAG Long-term Weight > 90%

        Expected behavior:
        - System should prefer RAG Long-term strategy
        - Should retrieve and use documents
        - Answer should contain information from uploaded document
        - Should cite sources
        - Answer should contain unique document markers
        """
        print("\n" + "="*80)
        print("TEST 2: RAG LONG-TERM HIGH WEIGHT (>90%)")
        print("="*80)

        test_result = {
            "test_name": "rag_long_term_high_weight",
            "timestamp": datetime.now().isoformat(),
            "passed": False,
            "details": {}
        }

        # Save original weights
        original_weights = await self.get_current_weights(client)
        if not original_weights:
            print("❌ Failed to get original weights")
            self.results["tests"]["test2_rag_long_term"] = test_result
            return

        print("\n📊 Original weights:")
        print(f"   RAG Long-term: {original_weights.get('strategy_weights', {}).get('rag_long_term', 'N/A')}")
        print(f"   Direct LLM: {original_weights.get('strategy_weights', {}).get('direct_llm', 'N/A')}")

        # Set RAG long-term weight to 0.95 (95%), Direct LLM to 0.05 (5%)
        new_weights = {
            "strategy_weights": {
                "rag_short_term": 0.90,
                "rag_hybrid": 0.90,
                "rag_long_term": 0.95,  # Very high - prefer RAG
                "direct_llm": 0.05,      # Very low - discourage Direct LLM
                "tool_navigation": 0.80,
                "tool_ocr": 0.80,
                "tool_docling": 0.80,
                "tool_web_scraping": 0.75
            }
        }

        print("\n🔧 Setting weights to favor RAG Long-term:")
        print(f"   RAG Long-term: 0.95 (95%)")
        print(f"   Direct LLM: 0.05 (5%)")

        if not await self.set_weights(client, new_weights):
            print("❌ Failed to set weights")
            self.results["tests"]["test2_rag_long_term"] = test_result
            return

        print("✅ Weights updated successfully")
        await asyncio.sleep(2)  # Let weights propagate

        # Query with question about unique content in document
        query = "What is the secret code mentioned in the document?"

        print(f"\n❓ Query: {query}")
        print("   Expected: Answer containing 'ALPHA-BRAVO-CHARLIE-999' from document")

        result = await self.query_with_rag_pipeline(client, query)

        if result:
            answer = result.get("answer", "")
            citations = result.get("citations", [])
            num_sources = len(citations)

            print(f"\n📝 Answer received:")
            print(f"   Length: {len(answer)} chars")
            print(f"   Sources cited: {num_sources}")
            print(f"   Answer preview: {answer[:200]}...")

            # Check if answer contains unique markers from document
            unique_markers = [
                "ALPHA-BRAVO-CHARLIE-999",
                "ZEPHYR-QUANTUM-DELTA",
                "NEBULA-X7",
                "SIGMA-LAMBDA-9",
                "THETA-OMEGA-15"
            ]

            markers_found = [marker for marker in unique_markers if marker in answer]

            print(f"\n🔍 Analysis:")
            print(f"   Unique markers in answer: {len(markers_found)}")
            if markers_found:
                print(f"   Markers found: {markers_found}")
            print(f"   Number of citations: {num_sources}")

            if citations:
                print(f"\n📚 Sources cited:")
                for i, citation in enumerate(citations[:3], 1):
                    print(f"   {i}. {citation.get('filename', 'Unknown')}")
                    excerpt = citation.get('excerpt', '')
                    if len(excerpt) > 100:
                        excerpt = excerpt[:100] + "..."
                    print(f"      Excerpt: {excerpt}")

            # Test passes if:
            # 1. Multiple sources cited (RAG should retrieve docs)
            # 2. Answer contains at least one unique marker
            if num_sources >= 1 and len(markers_found) >= 1:
                print("\n✅ TEST 2 PASSED")
                print("   ✓ RAG Long-term weight setting works")
                print("   ✓ System retrieved document sources")
                print("   ✓ Answer contains information from uploaded document")
                test_result["passed"] = True
            else:
                print("\n⚠️  TEST 2 INCONCLUSIVE")
                print(f"   - Expected 1+ sources, got {num_sources}")
                print(f"   - Expected 1+ unique markers, found {len(markers_found)}")
                if num_sources == 0:
                    print("   ⚠️  System did NOT retrieve documents despite high RAG weight")

            test_result["details"] = {
                "weight_config": "rag_long_term=0.95, direct_llm=0.05",
                "query": query,
                "answer_length": len(answer),
                "num_sources": num_sources,
                "unique_markers_found": len(markers_found),
                "markers": markers_found,
                "answer_preview": answer[:300],
                "citations": [
                    {
                        "filename": c.get("filename", ""),
                        "excerpt_preview": c.get("excerpt", "")[:100]
                    }
                    for c in citations[:3]
                ]
            }
        else:
            print("❌ Query failed")

        # Restore original weights
        print("\n🔄 Restoring original weights...")
        await self.set_weights(client, original_weights)

        self.results["tests"]["test2_rag_long_term"] = test_result

    async def run_all_tests(self):
        """Run all weight configuration tests"""
        print("\n" + "="*80)
        print("WEIGHTS CONFIGURATION TESTING - RAG vs Direct LLM")
        print("="*80)
        print(f"Session ID: {self.session_id}")
        print(f"Timestamp: {datetime.now().isoformat()}")

        async with httpx.AsyncClient() as client:
            # Setup
            print("\n" + "="*80)
            print("SETUP: AUTHENTICATION & PROJECT CREATION")
            print("="*80)

            if not await self.login(client):
                print("❌ Setup failed at login")
                return

            if not await self.create_project(client):
                print("❌ Setup failed at project creation")
                return

            if not await self.upload_test_document(client):
                print("❌ Setup failed at document upload")
                return

            # Run tests
            await self.test_direct_llm_high_weight(client)
            await self.test_rag_long_term_high_weight(client)

            # Summary
            print("\n" + "="*80)
            print("TEST SUMMARY - WEIGHTS CONFIGURATION")
            print("="*80)

            total_tests = len(self.results["tests"])
            passed_tests = sum(1 for t in self.results["tests"].values() if t.get("passed", False))

            print(f"\nTotal Tests: {total_tests}")
            print(f"✅ Passed: {passed_tests}")
            print(f"❌ Failed: {total_tests - passed_tests}")
            print(f"Success Rate: {(passed_tests/total_tests*100) if total_tests > 0 else 0:.1f}%")

            print("\n📋 Test Results:")
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
            results_file = "/tmp/weights_config_test_results.json"
            with open(results_file, "w") as f:
                json.dump(self.results, f, indent=2)

            print(f"\n📄 Results saved to {results_file}")


if __name__ == "__main__":
    test_runner = WeightsConfigTest()
    asyncio.run(test_runner.run_all_tests())
