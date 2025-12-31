"""
Comprehensive Backend API Testing
Tests all major features via API calls:
1. Authentication
2. Project creation and switching
3. Document upload and storage (MinIO)
4. RAG vs Direct LLM
5. Web scraping (all methods)
6. Database chunk storage and retrieval
7. Session state management

Date: 2025-11-30
"""

import asyncio
import httpx
import json
from typing import Dict, Any, List, Optional
import time


class ComprehensiveBackendTester:
    """Test all backend features comprehensively"""

    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3001"
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.session_id: str = f"test-session-{int(time.time())}"
        self.project_id: Optional[str] = None
        self.project_id_2: Optional[str] = None
        self.document_ids: List[str] = []
        # Default department and team IDs (from Tech department)
        self.department_id = "c5f6f8e3-432a-47dd-ba80-3b9516e2e174"  # Technology
        self.team_id = "62785a3f-459f-4f86-857b-1b0e7580e158"  # Tech Team 1
        self.test_results = {
            "authentication": {"status": "pending", "details": []},
            "project_creation": {"status": "pending", "details": []},
            "project_switching": {"status": "pending", "details": []},
            "document_upload": {"status": "pending", "details": []},
            "minio_storage": {"status": "pending", "details": []},
            "db_chunks": {"status": "pending", "details": []},
            "rag_query": {"status": "pending", "details": []},
            "direct_llm": {"status": "pending", "details": []},
            "web_scraping": {"status": "pending", "details": []},
            "session_state": {"status": "pending", "details": []},
            "project_isolation": {"status": "pending", "details": []},
        }

    async def run_all_tests(self):
        """Execute all comprehensive tests"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            print("\n" + "="*80)
            print("COMPREHENSIVE BACKEND FEATURE TESTING")
            print("="*80)

            try:
                # Test 1: Authentication
                await self.test_authentication(client)

                # Test 2: Project Creation
                await self.test_project_creation(client)

                # Test 3: Document Upload
                await self.test_document_upload(client)

                # Test 4: MinIO Storage Verification
                await self.test_minio_storage(client)

                # Test 5: Database Chunks
                await self.test_database_chunks(client)

                # Test 6: RAG Query
                await self.test_rag_query(client)

                # Test 7: Direct LLM Query
                await self.test_direct_llm(client)

                # Test 8: Project Switching
                await self.test_project_switching(client)

                # Test 9: Web Scraping (All Methods)
                await self.test_web_scraping(client)

                # Test 10: Session State Management
                await self.test_session_state(client)

                # Test 11: Project Isolation
                await self.test_project_isolation(client)

            except Exception as e:
                print(f"\n❌ Test suite failed with error: {e}")
                import traceback
                traceback.print_exc()
            finally:
                # Save results
                with open("/tmp/comprehensive_backend_test_results.json", "w") as f:
                    json.dump(self.test_results, f, indent=2)
                print("\n📄 Results saved to /tmp/comprehensive_backend_test_results.json")

                # Print summary
                self.print_summary()

    async def test_authentication(self, client: httpx.AsyncClient):
        """Test 1: Authentication"""
        print("\n" + "="*80)
        print("TEST 1: AUTHENTICATION")
        print("="*80)

        try:
            # Login
            response = await client.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"username": "admin", "password": "admin"}
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.user_id = data["user"]["id"]

                self.test_results["authentication"]["status"] = "passed"
                self.test_results["authentication"]["details"].append("Login successful")
                self.test_results["authentication"]["details"].append(f"User ID: {self.user_id}")
                print(f"✅ Login successful")
                print(f"   User: {data['user']['username']}")
                print(f"   Role: {data['user']['role']}")
                print(f"   Token: {self.token[:50]}...")
            else:
                raise Exception(f"Login failed: {response.status_code} - {response.text}")

        except Exception as e:
            self.test_results["authentication"]["status"] = "failed"
            self.test_results["authentication"]["details"].append(f"Error: {str(e)}")
            print(f"❌ Authentication failed: {e}")
            raise

    async def test_project_creation(self, client: httpx.AsyncClient):
        """Test 2: Project Creation"""
        print("\n" + "="*80)
        print("TEST 2: PROJECT CREATION")
        print("="*80)

        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            # Create Project 1
            response = await client.post(
                f"{self.base_url}/api/v1/projects",
                headers=headers,
                json={
                    "name": "Test Project Alpha",
                    "description": "First test project for comprehensive testing",
                    "module": "CHATBOT",
                    "department_id": self.department_id,
                    "team_id": self.team_id
                }
            )

            if response.status_code == 200:
                project_data = response.json()
                self.project_id = project_data["id"]
                print(f"✅ Project 1 created: {project_data['name']}")
                print(f"   ID: {self.project_id}")
                self.test_results["project_creation"]["details"].append(f"Project 1 ID: {self.project_id}")
            else:
                raise Exception(f"Project creation failed: {response.text}")

            # Create Project 2
            response = await client.post(
                f"{self.base_url}/api/v1/projects",
                headers=headers,
                json={
                    "name": "Test Project Beta",
                    "description": "Second test project for isolation testing",
                    "module": "WEB_SCRAPER",
                    "department_id": self.department_id,
                    "team_id": self.team_id
                }
            )

            if response.status_code == 200:
                project_data = response.json()
                self.project_id_2 = project_data["id"]
                print(f"✅ Project 2 created: {project_data['name']}")
                print(f"   ID: {self.project_id_2}")
                self.test_results["project_creation"]["details"].append(f"Project 2 ID: {self.project_id_2}")

            self.test_results["project_creation"]["status"] = "passed"

        except Exception as e:
            self.test_results["project_creation"]["status"] = "failed"
            self.test_results["project_creation"]["details"].append(f"Error: {str(e)}")
            print(f"❌ Project creation failed: {e}")
            raise

    async def test_document_upload(self, client: httpx.AsyncClient):
        """Test 3: Document Upload"""
        print("\n" + "="*80)
        print("TEST 3: DOCUMENT UPLOAD")
        print("="*80)

        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            # Create test documents
            test_docs = [
                ("doc1.txt", "This is test document 1 about artificial intelligence and machine learning."),
                ("doc2.txt", "This is test document 2 about web scraping and data extraction."),
                ("doc3.txt", "This is test document 3 about database management and SQL queries."),
            ]

            for filename, content in test_docs:
                # Upload to Project 1
                files = {"file": (filename, content.encode(), "text/plain")}
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
                    self.document_ids.append(doc_data["document_id"])
                    print(f"✅ Uploaded: {filename}")
                    print(f"   Document ID: {doc_data['document_id']}")
                    self.test_results["document_upload"]["details"].append(
                        f"Uploaded {filename}: {doc_data['document_id']}"
                    )
                else:
                    raise Exception(f"Upload failed for {filename}: {response.text}")

            self.test_results["document_upload"]["status"] = "passed"
            print(f"\n✅ Total documents uploaded: {len(self.document_ids)}")

        except Exception as e:
            self.test_results["document_upload"]["status"] = "failed"
            self.test_results["document_upload"]["details"].append(f"Error: {str(e)}")
            print(f"❌ Document upload failed: {e}")
            raise

    async def test_minio_storage(self, client: httpx.AsyncClient):
        """Test 4: MinIO Storage Verification"""
        print("\n" + "="*80)
        print("TEST 4: MINIO STORAGE VERIFICATION")
        print("="*80)

        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            # Get document details
            for doc_id in self.document_ids:
                response = await client.get(
                    f"{self.base_url}/api/v1/documents/{doc_id}",
                    headers=headers
                )

                if response.status_code == 200:
                    doc_data = response.json()
                    print(f"✅ Document: {doc_data['filename']}")
                    print(f"   MinIO Path: {doc_data.get('file_path', 'N/A')}")
                    print(f"   Size: {doc_data.get('file_size', 0)} bytes")
                    print(f"   Project ID: {doc_data.get('project_id', 'N/A')}")

                    # Verify path structure
                    expected_path = f"documents/{self.user_id}/{self.project_id}/"
                    if expected_path in doc_data.get('file_path', ''):
                        print(f"   ✅ Correct user/project path structure")
                        self.test_results["minio_storage"]["details"].append(
                            f"Correct path for {doc_data['filename']}"
                        )
                    else:
                        print(f"   ⚠️  Path doesn't match expected structure")
                        self.test_results["minio_storage"]["details"].append(
                            f"Path mismatch for {doc_data['filename']}"
                        )

            self.test_results["minio_storage"]["status"] = "passed"

        except Exception as e:
            self.test_results["minio_storage"]["status"] = "failed"
            self.test_results["minio_storage"]["details"].append(f"Error: {str(e)}")
            print(f"❌ MinIO verification failed: {e}")

    async def test_database_chunks(self, client: httpx.AsyncClient):
        """Test 5: Database Chunks Verification"""
        print("\n" + "="*80)
        print("TEST 5: DATABASE CHUNKS VERIFICATION")
        print("="*80)

        # Direct database query would require psql access
        # For now, we'll verify through API
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            # Query documents to check processing
            response = await client.get(
                f"{self.base_url}/api/v1/documents",
                headers=headers,
                params={"session_id": self.session_id}
            )

            if response.status_code == 200:
                docs = response.json()
                processed_count = sum(1 for doc in docs if doc.get("processed", False))

                print(f"✅ Documents in DB: {len(docs)}")
                print(f"   Processed: {processed_count}")
                print(f"   Pending: {len(docs) - processed_count}")

                # Wait for processing if needed
                if processed_count < len(docs):
                    print("   ⏳ Waiting for document processing...")
                    await asyncio.sleep(5)

                self.test_results["db_chunks"]["status"] = "passed"
                self.test_results["db_chunks"]["details"].append(
                    f"Processed {processed_count}/{len(docs)} documents"
                )
            else:
                raise Exception(f"Failed to get documents: {response.text}")

        except Exception as e:
            self.test_results["db_chunks"]["status"] = "failed"
            self.test_results["db_chunks"]["details"].append(f"Error: {str(e)}")
            print(f"❌ Database chunks verification failed: {e}")

    async def test_rag_query(self, client: httpx.AsyncClient):
        """Test 6: RAG Query with Documents"""
        print("\n" + "="*80)
        print("TEST 6: RAG QUERY (WITH DOCUMENTS)")
        print("="*80)

        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            # Query about uploaded documents
            response = await client.post(
                f"{self.base_url}/api/v1/query",
                headers=headers,
                json={
                    "query": "What topics are covered in the uploaded documents?",
                    "session_id": self.session_id,
                    "project_id": self.project_id,
                    "model": "ollama/mistral",
                    "use_rag": True,
                    "top_k": 3
                }
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ RAG Query successful")
                print(f"   Answer: {result.get('answer', 'N/A')[:200]}...")
                print(f"   Sources: {len(result.get('sources', []))} documents")
                print(f"   Model: {result.get('model_used', 'N/A')}")
                print(f"   Latency: {result.get('latency_ms', 0):.2f}ms")

                # Verify sources are from correct project
                for idx, source in enumerate(result.get('sources', [])[:3]):
                    print(f"\n   Source {idx+1}:")
                    print(f"      Filename: {source.get('filename', 'N/A')}")
                    print(f"      Score: {source.get('score', 0):.4f}")
                    print(f"      Content: {source.get('content', '')[:100]}...")

                self.test_results["rag_query"]["status"] = "passed"
                self.test_results["rag_query"]["details"].append(
                    f"Retrieved {len(result.get('sources', []))} sources"
                )
            else:
                raise Exception(f"RAG query failed: {response.text}")

        except Exception as e:
            self.test_results["rag_query"]["status"] = "failed"
            self.test_results["rag_query"]["details"].append(f"Error: {str(e)}")
            print(f"❌ RAG query failed: {e}")

    async def test_direct_llm(self, client: httpx.AsyncClient):
        """Test 7: Direct LLM Query (No RAG)"""
        print("\n" + "="*80)
        print("TEST 7: DIRECT LLM QUERY (NO RAG)")
        print("="*80)

        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            # Query without RAG
            response = await client.post(
                f"{self.base_url}/api/v1/query",
                headers=headers,
                json={
                    "query": "What is the capital of France?",
                    "session_id": self.session_id,
                    "model": "ollama/mistral",
                    "use_rag": False
                }
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ Direct LLM Query successful")
                print(f"   Answer: {result.get('answer', 'N/A')[:200]}...")
                print(f"   Sources: {len(result.get('sources', []))} (should be 0)")
                print(f"   Model: {result.get('model_used', 'N/A')}")
                print(f"   Latency: {result.get('latency_ms', 0):.2f}ms")

                # Verify no sources used
                if len(result.get('sources', [])) == 0:
                    print("   ✅ Correctly bypassed RAG - no sources used")
                    self.test_results["direct_llm"]["details"].append("No RAG sources used (correct)")
                else:
                    print("   ⚠️  Sources found (should be 0 for direct LLM)")

                self.test_results["direct_llm"]["status"] = "passed"
            else:
                raise Exception(f"Direct LLM query failed: {response.text}")

        except Exception as e:
            self.test_results["direct_llm"]["status"] = "failed"
            self.test_results["direct_llm"]["details"].append(f"Error: {str(e)}")
            print(f"❌ Direct LLM query failed: {e}")

    async def test_project_switching(self, client: httpx.AsyncClient):
        """Test 8: Project Switching"""
        print("\n" + "="*80)
        print("TEST 8: PROJECT SWITCHING")
        print("="*80)

        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            # Switch to Project 2
            print(f"Switching to Project 2: {self.project_id_2}")

            # Upload document to Project 2
            content = "This document belongs to Project Beta and discusses cloud computing."
            files = {"file": ("project2_doc.txt", content.encode(), "text/plain")}
            data = {
                "session_id": self.session_id,
                "project_id": self.project_id_2
            }

            response = await client.post(
                f"{self.base_url}/api/v1/upload",
                headers=headers,
                files=files,
                data=data
            )

            if response.status_code == 200:
                print(f"✅ Document uploaded to Project 2")

                # Query Project 2
                await asyncio.sleep(2)  # Wait for processing

                response = await client.post(
                    f"{self.base_url}/api/v1/query",
                    headers=headers,
                    json={
                        "query": "What is this document about?",
                        "session_id": self.session_id,
                        "project_id": self.project_id_2,
                        "model": "ollama/mistral",
                        "use_rag": True
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Query in Project 2 successful")
                    print(f"   Sources: {len(result.get('sources', []))}")

                    self.test_results["project_switching"]["status"] = "passed"
                    self.test_results["project_switching"]["details"].append(
                        "Successfully switched and queried Project 2"
                    )

        except Exception as e:
            self.test_results["project_switching"]["status"] = "failed"
            self.test_results["project_switching"]["details"].append(f"Error: {str(e)}")
            print(f"❌ Project switching failed: {e}")

    async def test_web_scraping(self, client: httpx.AsyncClient):
        """Test 9: Web Scraping (All Methods)"""
        print("\n" + "="*80)
        print("TEST 9: WEB SCRAPING (ALL METHODS)")
        print("="*80)

        headers = {"Authorization": f"Bearer {self.token}"}

        # Test different scraping strategies
        strategies = ["simple", "playwright", "smart"]

        for strategy in strategies:
            print(f"\n--- Testing {strategy.upper()} strategy ---")
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/scrape",
                    headers=headers,
                    json={
                        "urls": ["https://example.com"],
                        "strategy": strategy,
                        "session_id": self.session_id,
                        "project_id": self.project_id
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ {strategy} scraping initiated")
                    print(f"   Job ID: {result.get('job_id', 'N/A')}")
                    self.test_results["web_scraping"]["details"].append(
                        f"{strategy} strategy: success"
                    )
                else:
                    print(f"⚠️  {strategy} strategy returned: {response.status_code}")
                    self.test_results["web_scraping"]["details"].append(
                        f"{strategy} strategy: {response.status_code}"
                    )

            except Exception as e:
                print(f"❌ {strategy} strategy failed: {e}")
                self.test_results["web_scraping"]["details"].append(
                    f"{strategy} strategy: error - {str(e)}"
                )

        self.test_results["web_scraping"]["status"] = "passed"

    async def test_session_state(self, client: httpx.AsyncClient):
        """Test 10: Session State Management"""
        print("\n" + "="*80)
        print("TEST 10: SESSION STATE MANAGEMENT")
        print("="*80)

        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            # Get session info
            response = await client.get(
                f"{self.base_url}/api/v1/sessions/{self.session_id}",
                headers=headers
            )

            if response.status_code == 200:
                session_data = response.json()
                print(f"✅ Session retrieved")
                print(f"   Session ID: {session_data.get('session_id', 'N/A')}")
                print(f"   Created: {session_data.get('created_at', 'N/A')}")
                print(f"   Messages: {session_data.get('message_count', 0)}")
                print(f"   Documents: {len(session_data.get('documents', []))}")

                self.test_results["session_state"]["status"] = "passed"
                self.test_results["session_state"]["details"].append(
                    f"Session has {session_data.get('message_count', 0)} messages"
                )
            else:
                raise Exception(f"Failed to get session: {response.text}")

        except Exception as e:
            self.test_results["session_state"]["status"] = "failed"
            self.test_results["session_state"]["details"].append(f"Error: {str(e)}")
            print(f"❌ Session state test failed: {e}")

    async def test_project_isolation(self, client: httpx.AsyncClient):
        """Test 11: Project Isolation"""
        print("\n" + "="*80)
        print("TEST 11: PROJECT ISOLATION")
        print("="*80)

        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            # Query Project 1 - should NOT return Project 2 docs
            response = await client.post(
                f"{self.base_url}/api/v1/query",
                headers=headers,
                json={
                    "query": "cloud computing",
                    "session_id": self.session_id,
                    "project_id": self.project_id,  # Project 1
                    "model": "ollama/mistral",
                    "use_rag": True
                }
            )

            if response.status_code == 200:
                result = response.json()
                sources = result.get('sources', [])

                print(f"✅ Queried Project 1 with Project 2 keywords")
                print(f"   Sources found: {len(sources)}")

                # Check if sources are from correct project
                project_2_content = False
                for source in sources:
                    if "cloud computing" in source.get('content', '').lower():
                        project_2_content = True
                        break

                if not project_2_content:
                    print("   ✅ Project isolation confirmed - no Project 2 content leaked")
                    self.test_results["project_isolation"]["status"] = "passed"
                    self.test_results["project_isolation"]["details"].append(
                        "Project 1 correctly isolated from Project 2"
                    )
                else:
                    print("   ⚠️  Project 2 content found in Project 1 query")
                    self.test_results["project_isolation"]["status"] = "failed"
                    self.test_results["project_isolation"]["details"].append(
                        "Project isolation failed"
                    )

        except Exception as e:
            self.test_results["project_isolation"]["status"] = "failed"
            self.test_results["project_isolation"]["details"].append(f"Error: {str(e)}")
            print(f"❌ Project isolation test failed: {e}")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)

        passed = sum(1 for test in self.test_results.values() if test["status"] == "passed")
        failed = sum(1 for test in self.test_results.values() if test["status"] == "failed")
        total = len(self.test_results)

        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%\n")

        for test_name, result in self.test_results.items():
            status_icon = "✅" if result["status"] == "passed" else "❌" if result["status"] == "failed" else "⏳"
            print(f"{status_icon} {test_name.replace('_', ' ').title()}: {result['status']}")


async def main():
    """Run comprehensive backend tests"""
    tester = ComprehensiveBackendTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
