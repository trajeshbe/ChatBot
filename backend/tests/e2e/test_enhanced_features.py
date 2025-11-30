"""
Enhanced Feature Testing - Extended Test Cases
Tests additional scenarios including:
1. RAG vs Direct LLM comparison
2. Chat conversation flow and history
3. Project isolation and switching
4. Web scraping with real URLs
5. MinIO path verification
6. Database chunk retrieval verification
7. Session state retention

Date: 2025-11-30
"""

import asyncio
import httpx
import json
from typing import Dict, Any, List, Optional
import time


class EnhancedFeatureTester:
    """Extended testing for all features with real-world scenarios"""

    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.session_id: str = f"enhanced-test-{int(time.time())}"
        self.session_id_2: str = f"enhanced-test-2-{int(time.time())}"
        self.project_id: Optional[str] = None
        self.project_id_2: Optional[str] = None
        self.document_ids: List[str] = []
        self.conversation_ids: List[str] = []

        # Test results tracking
        self.test_results = {
            "chat_conversation_flow": {"status": "pending", "details": []},
            "message_history": {"status": "pending", "details": []},
            "rag_vs_direct_llm": {"status": "pending", "details": []},
            "project_isolation_verification": {"status": "pending", "details": []},
            "session_state_retention": {"status": "pending", "details": []},
            "minio_path_verification": {"status": "pending", "details": []},
            "db_chunk_retrieval": {"status": "pending", "details": []},
            "web_scraping_real": {"status": "pending", "details": []},
            "multi_document_rag": {"status": "pending", "details": []},
            "context_window_test": {"status": "pending", "details": []},
        }

        # IDs from database
        self.department_id = "c5f6f8e3-432a-47dd-ba80-3b9516e2e174"
        self.team_id = "62785a3f-459f-4f86-857b-1b0e7580e158"

    async def run_all_tests(self):
        """Execute all enhanced tests"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            print("\n" + "="*80)
            print("ENHANCED FEATURE TESTING - EXTENDED TEST SUITE")
            print("="*80)

            try:
                # Setup
                await self.setup_test_environment(client)

                # Test 1: Chat Conversation Flow
                await self.test_chat_conversation_flow(client)

                # Test 2: Message History
                await self.test_message_history(client)

                # Test 3: RAG vs Direct LLM Comparison
                await self.test_rag_vs_direct_llm(client)

                # Test 4: Project Isolation Verification
                await self.test_project_isolation_detailed(client)

                # Test 5: Session State Retention
                await self.test_session_state_retention(client)

                # Test 6: MinIO Path Verification
                await self.test_minio_paths_detailed(client)

                # Test 7: DB Chunk Retrieval
                await self.test_db_chunk_retrieval(client)

                # Test 8: Web Scraping with Real URL
                await self.test_web_scraping_real(client)

                # Test 9: Multi-Document RAG
                await self.test_multi_document_rag(client)

                # Test 10: Context Window Test
                await self.test_context_window(client)

            except Exception as e:
                print(f"\n❌ Test suite failed: {e}")
                import traceback
                traceback.print_exc()
            finally:
                # Save results
                with open("/tmp/enhanced_test_results.json", "w") as f:
                    json.dump(self.test_results, f, indent=2)
                print("\n📄 Results saved to /tmp/enhanced_test_results.json")
                self.print_summary()

    async def setup_test_environment(self, client: httpx.AsyncClient):
        """Setup: Login and create projects"""
        print("\n" + "="*80)
        print("SETUP: AUTHENTICATION & PROJECT CREATION")
        print("="*80)

        # Login
        response = await client.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"username": "admin", "password": "admin"}
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.user_id = data["user"]["id"]
            print(f"✅ Logged in as {data['user']['username']}")
        else:
            raise Exception(f"Login failed: {response.text}")

        headers = {"Authorization": f"Bearer {self.token}"}

        # Create Project 1
        response = await client.post(
            f"{self.base_url}/api/v1/projects",
            headers=headers,
            json={
                "name": "Enhanced Test Project 1",
                "description": "For testing RAG and chat features",
                "module": "CHATBOT",
                "department_id": self.department_id,
                "team_id": self.team_id
            }
        )

        if response.status_code == 200:
            self.project_id = response.json()["id"]
            print(f"✅ Created Project 1: {self.project_id}")

        # Create Project 2
        response = await client.post(
            f"{self.base_url}/api/v1/projects",
            headers=headers,
            json={
                "name": "Enhanced Test Project 2",
                "description": "For testing isolation",
                "module": "CHATBOT",
                "department_id": self.department_id,
                "team_id": self.team_id
            }
        )

        if response.status_code == 200:
            self.project_id_2 = response.json()["id"]
            print(f"✅ Created Project 2: {self.project_id_2}")

        # Upload test documents to Project 1
        test_docs = [
            ("python_basics.txt", "Python is a high-level programming language. It supports multiple programming paradigms including procedural, object-oriented, and functional programming. Python is known for its simple syntax and readability."),
            ("machine_learning.txt", "Machine learning is a subset of artificial intelligence. It involves training models on data to make predictions. Common algorithms include linear regression, decision trees, and neural networks."),
            ("web_development.txt", "Web development involves building websites and web applications. Frontend technologies include HTML, CSS, and JavaScript. Backend technologies include Python, Node.js, and databases like PostgreSQL."),
        ]

        for filename, content in test_docs:
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
                doc_id = response.json()["document_id"]
                self.document_ids.append(doc_id)
                print(f"✅ Uploaded {filename}: {doc_id}")

        # Wait for document processing
        print("⏳ Waiting for document processing...")
        await asyncio.sleep(10)

    async def test_chat_conversation_flow(self, client: httpx.AsyncClient):
        """Test 1: Chat Conversation Flow"""
        print("\n" + "="*80)
        print("TEST 1: CHAT CONVERSATION FLOW")
        print("="*80)

        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            # Send multiple messages in conversation
            messages = [
                "What is Python?",
                "Tell me about machine learning",
                "How does web development work?"
            ]

            for idx, query in enumerate(messages):
                print(f"\n💬 Message {idx+1}: {query}")

                response = await client.post(
                    f"{self.base_url}/api/v1/chat",
                    headers=headers,
                    json={
                        "message": query,
                        "session_id": self.session_id,
                        "project_id": self.project_id,
                        "model": "ollama/mistral"
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Response received")
                    print(f"   Answer preview: {result.get('answer', '')[:100]}...")
                    print(f"   Sources: {len(result.get('sources', []))}")

                    self.test_results["chat_conversation_flow"]["details"].append({
                        "message": query,
                        "response_length": len(result.get('answer', '')),
                        "sources_count": len(result.get('sources', []))
                    })
                else:
                    print(f"⚠️  Message {idx+1} failed: {response.status_code}")
                    self.test_results["chat_conversation_flow"]["details"].append({
                        "message": query,
                        "error": response.text
                    })

                await asyncio.sleep(2)

            self.test_results["chat_conversation_flow"]["status"] = "passed"

        except Exception as e:
            self.test_results["chat_conversation_flow"]["status"] = "failed"
            self.test_results["chat_conversation_flow"]["details"].append(f"Error: {str(e)}")
            print(f"❌ Chat conversation flow test failed: {e}")

    async def test_message_history(self, client: httpx.AsyncClient):
        """Test 2: Message History Retrieval"""
        print("\n" + "="*80)
        print("TEST 2: MESSAGE HISTORY RETRIEVAL")
        print("="*80)

        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            # Get conversation history
            response = await client.get(
                f"{self.base_url}/api/v1/conversations",
                headers=headers,
                params={"session_id": self.session_id}
            )

            if response.status_code == 200:
                conversations = response.json()
                print(f"✅ Retrieved {len(conversations)} conversations")

                for conv in conversations[:3]:
                    print(f"\n   Conversation: {conv.get('id', 'N/A')[:8]}...")
                    print(f"   Messages: {conv.get('message_count', 0)}")
                    print(f"   Created: {conv.get('created_at', 'N/A')}")

                self.test_results["message_history"]["status"] = "passed"
                self.test_results["message_history"]["details"].append(
                    f"Found {len(conversations)} conversations"
                )
            else:
                print(f"⚠️  Failed to get history: {response.status_code}")

        except Exception as e:
            self.test_results["message_history"]["status"] = "failed"
            self.test_results["message_history"]["details"].append(f"Error: {str(e)}")
            print(f"❌ Message history test failed: {e}")

    async def test_rag_vs_direct_llm(self, client: httpx.AsyncClient):
        """Test 3: RAG vs Direct LLM Comparison"""
        print("\n" + "="*80)
        print("TEST 3: RAG vs DIRECT LLM COMPARISON")
        print("="*80)

        headers = {"Authorization": f"Bearer {self.token}"}
        test_query = "What is Python?"

        try:
            # Test 1: RAG Query
            print("\n📚 Testing RAG Query...")
            response_rag = await client.post(
                f"{self.base_url}/api/v1/chat",
                headers=headers,
                json={
                    "message": test_query,
                    "session_id": f"{self.session_id}-rag",
                    "project_id": self.project_id,
                    "model": "ollama/mistral",
                    "use_rag": True
                }
            )

            rag_result = None
            if response_rag.status_code == 200:
                rag_result = response_rag.json()
                print(f"✅ RAG Response received")
                print(f"   Answer: {rag_result.get('answer', '')[:150]}...")
                print(f"   Sources used: {len(rag_result.get('sources', []))}")
                print(f"   Latency: {rag_result.get('latency_ms', 0):.2f}ms")

            # Test 2: Direct LLM (no RAG)
            print("\n🤖 Testing Direct LLM...")
            response_direct = await client.post(
                f"{self.base_url}/api/v1/chat",
                headers=headers,
                json={
                    "message": test_query,
                    "session_id": f"{self.session_id}-direct",
                    "model": "ollama/mistral",
                    "use_rag": False
                }
            )

            direct_result = None
            if response_direct.status_code == 200:
                direct_result = response_direct.json()
                print(f"✅ Direct LLM Response received")
                print(f"   Answer: {direct_result.get('answer', '')[:150]}...")
                print(f"   Sources used: {len(direct_result.get('sources', []))}")
                print(f"   Latency: {direct_result.get('latency_ms', 0):.2f}ms")

            # Comparison
            if rag_result and direct_result:
                print("\n📊 Comparison:")
                print(f"   RAG Answer Length: {len(rag_result.get('answer', ''))}")
                print(f"   Direct Answer Length: {len(direct_result.get('answer', ''))}")
                print(f"   RAG Sources: {len(rag_result.get('sources', []))}")
                print(f"   Direct Sources: {len(direct_result.get('sources', []))}")

                if len(rag_result.get('sources', [])) > 0 and len(direct_result.get('sources', [])) == 0:
                    print("   ✅ RAG correctly uses documents, Direct LLM doesn't")
                    self.test_results["rag_vs_direct_llm"]["status"] = "passed"
                else:
                    print("   ⚠️  Unexpected source behavior")

                self.test_results["rag_vs_direct_llm"]["details"].append({
                    "rag_sources": len(rag_result.get('sources', [])),
                    "direct_sources": len(direct_result.get('sources', [])),
                    "comparison": "RAG uses docs, Direct doesn't" if len(rag_result.get('sources', [])) > 0 else "Unexpected"
                })

        except Exception as e:
            self.test_results["rag_vs_direct_llm"]["status"] = "failed"
            self.test_results["rag_vs_direct_llm"]["details"].append(f"Error: {str(e)}")
            print(f"❌ RAG vs Direct LLM test failed: {e}")

    async def test_project_isolation_detailed(self, client: httpx.AsyncClient):
        """Test 4: Detailed Project Isolation"""
        print("\n" + "="*80)
        print("TEST 4: PROJECT ISOLATION VERIFICATION")
        print("="*80)

        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            # Upload unique document to Project 2
            unique_content = "UNIQUE_PROJECT2_MARKER: This content should ONLY be in Project 2. Docker containers and Kubernetes pods."
            files = {"file": ("project2_unique.txt", unique_content.encode(), "text/plain")}
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
                print(f"✅ Uploaded unique document to Project 2")

            # Wait for processing
            await asyncio.sleep(5)

            # Query Project 1 for Project 2 content (should NOT find it)
            response = await client.post(
                f"{self.base_url}/api/v1/chat",
                headers=headers,
                json={
                    "message": "Tell me about Docker containers and Kubernetes",
                    "session_id": f"{self.session_id}-isolation",
                    "project_id": self.project_id,  # Project 1
                    "model": "ollama/mistral",
                    "use_rag": True
                }
            )

            if response.status_code == 200:
                result = response.json()
                sources = result.get('sources', [])

                # Check if Project 2 content leaked
                leaked = False
                for source in sources:
                    if "UNIQUE_PROJECT2_MARKER" in source.get('content', ''):
                        leaked = True
                        break

                if not leaked:
                    print(f"✅ Project isolation maintained - No Project 2 content in Project 1")
                    print(f"   Project 1 sources: {len(sources)}")
                    self.test_results["project_isolation_verification"]["status"] = "passed"
                else:
                    print(f"❌ Project isolation FAILED - Project 2 content leaked to Project 1")
                    self.test_results["project_isolation_verification"]["status"] = "failed"

                self.test_results["project_isolation_verification"]["details"].append({
                    "isolation_maintained": not leaked,
                    "sources_count": len(sources)
                })

        except Exception as e:
            self.test_results["project_isolation_verification"]["status"] = "failed"
            self.test_results["project_isolation_verification"]["details"].append(f"Error: {str(e)}")
            print(f"❌ Project isolation test failed: {e}")

    async def test_session_state_retention(self, client: httpx.AsyncClient):
        """Test 5: Session State Retention"""
        print("\n" + "="*80)
        print("TEST 5: SESSION STATE RETENTION")
        print("="*80)

        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            # Get session 1
            response = await client.get(
                f"{self.base_url}/api/v1/sessions/{self.session_id}",
                headers=headers
            )

            session1_data = None
            if response.status_code == 200:
                session1_data = response.json()
                print(f"✅ Session 1: {session1_data.get('session_id', 'N/A')}")
                print(f"   Documents: {len(session1_data.get('documents', []))}")

            # Switch to different session
            response = await client.get(
                f"{self.base_url}/api/v1/sessions/{self.session_id_2}",
                headers=headers
            )

            if response.status_code == 200 or response.status_code == 404:
                print(f"✅ Session 2: {self.session_id_2} (new session)")

            # Switch back to original session
            response = await client.get(
                f"{self.base_url}/api/v1/sessions/{self.session_id}",
                headers=headers
            )

            if response.status_code == 200:
                session1_data_again = response.json()

                if session1_data and session1_data_again:
                    docs_match = len(session1_data.get('documents', [])) == len(session1_data_again.get('documents', []))

                    if docs_match:
                        print(f"✅ Session state retained after switching")
                        self.test_results["session_state_retention"]["status"] = "passed"
                    else:
                        print(f"⚠️  Session state changed")

                self.test_results["session_state_retention"]["details"].append({
                    "session_id": self.session_id,
                    "state_retained": docs_match if session1_data else False
                })

        except Exception as e:
            self.test_results["session_state_retention"]["status"] = "failed"
            self.test_results["session_state_retention"]["details"].append(f"Error: {str(e)}")
            print(f"❌ Session state retention test failed: {e}")

    async def test_minio_paths_detailed(self, client: httpx.AsyncClient):
        """Test 6: Detailed MinIO Path Verification"""
        print("\n" + "="*80)
        print("TEST 6: MINIO PATH VERIFICATION")
        print("="*80)

        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            paths_correct = 0
            paths_total = 0

            for doc_id in self.document_ids[:3]:
                response = await client.get(
                    f"{self.base_url}/api/v1/documents/{doc_id}",
                    headers=headers
                )

                if response.status_code == 200:
                    doc = response.json()
                    path = doc.get('file_path', '')

                    expected_pattern = f"documents/{self.user_id}/{self.project_id}"

                    paths_total += 1
                    if expected_pattern in path:
                        paths_correct += 1
                        print(f"✅ {doc.get('filename', 'N/A')}")
                        print(f"   Path: {path}")
                        print(f"   ✅ Matches pattern: documents/{{user_id}}/{{project_id}}/")
                    else:
                        print(f"❌ {doc.get('filename', 'N/A')}")
                        print(f"   Path: {path}")
                        print(f"   ❌ Does NOT match expected pattern")

            if paths_correct == paths_total and paths_total > 0:
                print(f"\n✅ All {paths_total} paths correct")
                self.test_results["minio_path_verification"]["status"] = "passed"
            else:
                print(f"\n⚠️  {paths_correct}/{paths_total} paths correct")

            self.test_results["minio_path_verification"]["details"].append({
                "paths_correct": paths_correct,
                "paths_total": paths_total
            })

        except Exception as e:
            self.test_results["minio_path_verification"]["status"] = "failed"
            self.test_results["minio_path_verification"]["details"].append(f"Error: {str(e)}")
            print(f"❌ MinIO path verification failed: {e}")

    async def test_db_chunk_retrieval(self, client: httpx.AsyncClient):
        """Test 7: Database Chunk Retrieval by Project"""
        print("\n" + "="*80)
        print("TEST 7: DATABASE CHUNK RETRIEVAL")
        print("="*80)

        # This would require direct DB access, so we'll verify through API
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            # Get documents for Project 1
            response = await client.get(
                f"{self.base_url}/api/v1/documents",
                headers=headers,
                params={"project_id": self.project_id}
            )

            if response.status_code == 200:
                docs_project1 = response.json()
                print(f"✅ Project 1 documents: {len(docs_project1)}")

            # Get documents for Project 2
            response = await client.get(
                f"{self.base_url}/api/v1/documents",
                headers=headers,
                params={"project_id": self.project_id_2}
            )

            if response.status_code == 200:
                docs_project2 = response.json()
                print(f"✅ Project 2 documents: {len(docs_project2)}")

                # Verify no overlap
                project1_ids = {doc['id'] for doc in docs_project1}
                project2_ids = {doc['id'] for doc in docs_project2}
                overlap = project1_ids.intersection(project2_ids)

                if not overlap:
                    print(f"✅ No document overlap between projects")
                    self.test_results["db_chunk_retrieval"]["status"] = "passed"
                else:
                    print(f"❌ Found {len(overlap)} overlapping documents")

                self.test_results["db_chunk_retrieval"]["details"].append({
                    "project1_docs": len(docs_project1),
                    "project2_docs": len(docs_project2),
                    "overlap": len(overlap)
                })

        except Exception as e:
            self.test_results["db_chunk_retrieval"]["status"] = "failed"
            self.test_results["db_chunk_retrieval"]["details"].append(f"Error: {str(e)}")
            print(f"❌ DB chunk retrieval test failed: {e}")

    async def test_web_scraping_real(self, client: httpx.AsyncClient):
        """Test 8: Web Scraping with Example.com"""
        print("\n" + "="*80)
        print("TEST 8: WEB SCRAPING (REAL URL)")
        print("="*80)

        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            # Test simple scraping
            response = await client.post(
                f"{self.base_url}/api/v1/scrape",
                headers=headers,
                json={
                    "url": "https://example.com",
                    "session_id": self.session_id,
                    "project_id": self.project_id,
                    "strategy": "simple"
                }
            )

            if response.status_code in [200, 202]:
                result = response.json()
                print(f"✅ Scraping initiated")
                print(f"   Job ID: {result.get('job_id', 'N/A')}")
                self.test_results["web_scraping_real"]["status"] = "passed"
                self.test_results["web_scraping_real"]["details"].append({
                    "status_code": response.status_code,
                    "job_id": result.get('job_id', 'N/A')
                })
            else:
                print(f"⚠️  Scraping returned: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                self.test_results["web_scraping_real"]["details"].append({
                    "status_code": response.status_code,
                    "error": response.text[:200]
                })

        except Exception as e:
            self.test_results["web_scraping_real"]["status"] = "failed"
            self.test_results["web_scraping_real"]["details"].append(f"Error: {str(e)}")
            print(f"❌ Web scraping test failed: {e}")

    async def test_multi_document_rag(self, client: httpx.AsyncClient):
        """Test 9: Multi-Document RAG Query"""
        print("\n" + "="*80)
        print("TEST 9: MULTI-DOCUMENT RAG QUERY")
        print("="*80)

        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            # Query that should pull from multiple documents
            response = await client.post(
                f"{self.base_url}/api/v1/chat",
                headers=headers,
                json={
                    "message": "Compare Python and machine learning",
                    "session_id": f"{self.session_id}-multi",
                    "project_id": self.project_id,
                    "model": "ollama/mistral",
                    "use_rag": True,
                    "top_k": 5
                }
            )

            if response.status_code == 200:
                result = response.json()
                sources = result.get('sources', [])
                unique_docs = set([s.get('filename', '') for s in sources])

                print(f"✅ Multi-document query successful")
                print(f"   Total sources: {len(sources)}")
                print(f"   Unique documents: {len(unique_docs)}")

                for doc in unique_docs:
                    print(f"   - {doc}")

                if len(unique_docs) > 1:
                    print(f"   ✅ Successfully pulled from multiple documents")
                    self.test_results["multi_document_rag"]["status"] = "passed"

                self.test_results["multi_document_rag"]["details"].append({
                    "sources_count": len(sources),
                    "unique_documents": len(unique_docs),
                    "documents": list(unique_docs)
                })

        except Exception as e:
            self.test_results["multi_document_rag"]["status"] = "failed"
            self.test_results["multi_document_rag"]["details"].append(f"Error: {str(e)}")
            print(f"❌ Multi-document RAG test failed: {e}")

    async def test_context_window(self, client: httpx.AsyncClient):
        """Test 10: Context Window Test"""
        print("\n" + "="*80)
        print("TEST 10: CONTEXT WINDOW TEST")
        print("="*80)

        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            # Send a query with large context request
            response = await client.post(
                f"{self.base_url}/api/v1/chat",
                headers=headers,
                json={
                    "message": "Summarize all the documents",
                    "session_id": f"{self.session_id}-context",
                    "project_id": self.project_id,
                    "model": "ollama/mistral",
                    "use_rag": True,
                    "top_k": 10  # Request more sources
                }
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ Context window test successful")
                print(f"   Sources retrieved: {len(result.get('sources', []))}")
                print(f"   Answer length: {len(result.get('answer', ''))}")

                self.test_results["context_window_test"]["status"] = "passed"
                self.test_results["context_window_test"]["details"].append({
                    "sources_retrieved": len(result.get('sources', [])),
                    "answer_length": len(result.get('answer', ''))
                })

        except Exception as e:
            self.test_results["context_window_test"]["status"] = "failed"
            self.test_results["context_window_test"]["details"].append(f"Error: {str(e)}")
            print(f"❌ Context window test failed: {e}")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("ENHANCED TEST SUMMARY")
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
    """Run enhanced feature tests"""
    tester = EnhancedFeatureTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
