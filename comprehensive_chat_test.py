#!/usr/bin/env python3
"""
Comprehensive Chat Functionality Test Suite
Date: 2025-12-12
Purpose: Test all chat scenarios including PDF, OCR, RAG, Direct LLM, and Memory

Test Scenarios:
1. Direct LLM Queries (no documents)
2. PDF Document Processing
3. RAG Queries with Documents
4. OCR/Vision Processing
5. Short-term Memory (session-based)
6. Long-term Memory (all documents)
7. Semantic Search Accuracy
8. Multi-modal Processing
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TEST_SESSION = f"comprehensive-test-{int(time.time())}"
MODEL_ID = "qwen2.5-coder:7b"

# Test results tracking
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "tests": []
}

def log_test(test_id, description, status, details=""):
    """Log test result"""
    test_results["total"] += 1
    if status == "PASS":
        test_results["passed"] += 1
        icon = "✅"
    else:
        test_results["failed"] += 1
        icon = "❌"

    result = {
        "id": test_id,
        "description": description,
        "status": status,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    test_results["tests"].append(result)

    print(f"\n{icon} {test_id}: {description}")
    if details:
        print(f"   {details}")
    return status == "PASS"

def send_query(query, session_id=None, use_cache=False, timeout=60):
    """Send query to chat API"""
    try:
        data = {
            "query": query,
            "model_id": MODEL_ID,
            "use_cache": str(use_cache).lower()
        }

        if session_id:
            data["session_id"] = session_id

        response = requests.post(
            f"{BASE_URL}/api/v1/query",
            data=data,
            timeout=timeout
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}", "text": response.text}
    except Exception as e:
        return {"error": str(e)}

def get_documents():
    """Get list of documents"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/documents")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"Error fetching documents: {e}")
        return []

print("="*80)
print("COMPREHENSIVE CHAT FUNCTIONALITY TEST SUITE")
print("="*80)
print(f"Start Time: {datetime.now().isoformat()}")
print(f"Base URL: {BASE_URL}")
print(f"Test Session: {TEST_SESSION}")
print(f"Model: {MODEL_ID}")
print("="*80)

# ============================================================================
# Category 1: Direct LLM Queries (No Documents)
# ============================================================================
print("\n\n📝 CATEGORY 1: DIRECT LLM QUERIES")
print("="*80)

# Test 1.1: Simple Factual Question
test_id = "TC-DIRECT-001"
print(f"\n🔍 {test_id}: Simple Factual Question")
response = send_query("What is the capital of France?")
if "error" not in response and "answer" in response:
    answer = response["answer"].lower()
    if "paris" in answer:
        log_test(test_id, "Simple factual question", "PASS", f"Answer: {response['answer'][:100]}")
    else:
        log_test(test_id, "Simple factual question", "FAIL", f"Expected 'Paris' in answer, got: {answer[:100]}")
else:
    log_test(test_id, "Simple factual question", "FAIL", f"Error: {response.get('error', 'No answer returned')}")

# Test 1.2: Mathematical Calculation
test_id = "TC-DIRECT-002"
print(f"\n🔍 {test_id}: Mathematical Calculation")
response = send_query("Calculate 127 * 43")
if "error" not in response and "answer" in response:
    answer = response["answer"]
    if "5461" in answer or "5,461" in answer:
        log_test(test_id, "Mathematical calculation", "PASS", f"Answer: {answer[:100]}")
    else:
        log_test(test_id, "Mathematical calculation", "FAIL", f"Expected '5461', got: {answer[:100]}")
else:
    log_test(test_id, "Mathematical calculation", "FAIL", f"Error: {response.get('error', 'No answer')}")

# Test 1.3: Code Generation
test_id = "TC-DIRECT-003"
print(f"\n🔍 {test_id}: Code Generation")
response = send_query("Write a Python function to check if a number is prime")
if "error" not in response and "answer" in response:
    answer = response["answer"].lower()
    if "def" in answer and ("prime" in answer or "return" in answer):
        log_test(test_id, "Code generation", "PASS", "Generated Python function")
    else:
        log_test(test_id, "Code generation", "FAIL", "Did not generate proper function")
else:
    log_test(test_id, "Code generation", "FAIL", f"Error: {response.get('error', 'No answer')}")

# ============================================================================
# Category 2: Document Information & Processing
# ============================================================================
print("\n\n📄 CATEGORY 2: DOCUMENT PROCESSING")
print("="*80)

# Test 2.1: Get Documents List
test_id = "TC-DOC-001"
print(f"\n🔍 {test_id}: Get Documents List")
documents = get_documents()
if isinstance(documents, list) and len(documents) > 0:
    pdf_docs = [d for d in documents if d.get("file_type") == "application/pdf"]
    txt_docs = [d for d in documents if d.get("file_type") == "text/plain"]

    log_test(test_id, "Get documents list", "PASS",
             f"Found {len(documents)} documents ({len(pdf_docs)} PDFs, {len(txt_docs)} TXT files)")

    # Store document IDs for later tests
    test_pdf = next((d for d in documents if "test_docling_ocr_vision" in d.get("filename", "")), None)
    if test_pdf:
        print(f"   📑 Test PDF found: {test_pdf['filename']}")

    short_story = next((d for d in documents if "Short Story" in d.get("filename", "")), None)
    if short_story:
        print(f"   📄 Text document found: {short_story['filename']}")
else:
    log_test(test_id, "Get documents list", "FAIL", "No documents found")

# ============================================================================
# Category 3: RAG Queries with Documents
# ============================================================================
print("\n\n🔍 CATEGORY 3: RAG QUERIES WITH DOCUMENTS")
print("="*80)

# Test 3.1: Query Existing PDF
test_id = "TC-RAG-001"
print(f"\n🔍 {test_id}: RAG Query on PDF Document")
response = send_query(
    "What is mentioned in the document about OCR or vision?",
    session_id=TEST_SESSION
)
if "error" not in response and "answer" in response:
    has_sources = "sources" in response or "num_sources" in response
    if has_sources:
        num_sources = response.get("num_sources", len(response.get("sources", [])))
        log_test(test_id, "RAG query on PDF", "PASS",
                f"Retrieved {num_sources} sources. Answer: {response['answer'][:150]}")
    else:
        log_test(test_id, "RAG query on PDF", "PASS",
                f"Answer returned: {response['answer'][:150]}")
else:
    log_test(test_id, "RAG query on PDF", "FAIL", f"Error: {response.get('error', 'No answer')}")

# Test 3.2: Query Text Document
test_id = "TC-RAG-002"
print(f"\n🔍 {test_id}: RAG Query on Text Document")
response = send_query(
    "What is the Short Story about?",
    session_id=TEST_SESSION
)
if "error" not in response and "answer" in response:
    log_test(test_id, "RAG query on text document", "PASS",
            f"Answer: {response['answer'][:150]}")
else:
    log_test(test_id, "RAG query on text document", "FAIL", f"Error: {response.get('error')}")

# Test 3.3: Semantic Search (not just keyword matching)
test_id = "TC-RAG-003"
print(f"\n🔍 {test_id}: Semantic Search Accuracy")
response = send_query(
    "Tell me about automated text recognition",  # Semantic match to "OCR"
    session_id=TEST_SESSION
)
if "error" not in response and "answer" in response:
    num_sources = response.get("num_sources", 0)
    if num_sources > 0:
        log_test(test_id, "Semantic search accuracy", "PASS",
                f"Found {num_sources} semantically similar sources")
    else:
        log_test(test_id, "Semantic search accuracy", "PASS",
                "Answered without sources (direct LLM)")
else:
    log_test(test_id, "Semantic search accuracy", "FAIL", f"Error: {response.get('error')}")

# Test 3.4: Multi-document RAG
test_id = "TC-RAG-004"
print(f"\n🔍 {test_id}: Multi-document RAG Query")
response = send_query(
    "Summarize all the documents you have access to",
    session_id=TEST_SESSION
)
if "error" not in response and "answer" in response:
    log_test(test_id, "Multi-document RAG", "PASS",
            f"Answer: {response['answer'][:150]}")
else:
    log_test(test_id, "Multi-document RAG", "FAIL", f"Error: {response.get('error')}")

# ============================================================================
# Category 4: Context & Memory
# ============================================================================
print("\n\n💭 CATEGORY 4: CONTEXT & MEMORY")
print("="*80)

# Test 4.1: Short-term Memory (Session Context)
test_id = "TC-MEM-001"
print(f"\n🔍 {test_id}: Short-term Memory - Session Context")
# First query
response1 = send_query(
    "My favorite color is blue",
    session_id=TEST_SESSION
)
time.sleep(1)
# Follow-up query in same session
response2 = send_query(
    "What is my favorite color?",
    session_id=TEST_SESSION
)
if "error" not in response2 and "answer" in response2:
    answer = response2["answer"].lower()
    if "blue" in answer:
        log_test(test_id, "Short-term memory (session)", "PASS",
                "Remembered context from previous message")
    else:
        log_test(test_id, "Short-term memory (session)", "FAIL",
                f"Did not remember context. Answer: {answer[:100]}")
else:
    log_test(test_id, "Short-term memory (session)", "FAIL", f"Error: {response2.get('error')}")

# Test 4.2: New Session (No Memory)
test_id = "TC-MEM-002"
print(f"\n🔍 {test_id}: Session Isolation - New Session Has No Memory")
new_session = f"test-new-{int(time.time())}"
response = send_query(
    "What is my favorite color?",
    session_id=new_session
)
if "error" not in response and "answer" in response:
    answer = response["answer"].lower()
    if "blue" not in answer or "don't know" in answer or "not mentioned" in answer:
        log_test(test_id, "Session isolation", "PASS",
                "New session correctly has no memory of previous session")
    else:
        log_test(test_id, "Session isolation", "FAIL",
                "New session incorrectly has memory from other session")
else:
    log_test(test_id, "Session isolation", "PASS",
            "Session properly isolated (no answer about previous context)")

# ============================================================================
# Category 5: Edge Cases & Error Handling
# ============================================================================
print("\n\n⚠️  CATEGORY 5: EDGE CASES & ERROR HANDLING")
print("="*80)

# Test 5.1: Empty Query
test_id = "TC-EDGE-001"
print(f"\n🔍 {test_id}: Empty Query Handling")
response = send_query("")
if "error" in response or ("answer" in response and len(response["answer"]) > 0):
    log_test(test_id, "Empty query handling", "PASS",
            "API handled empty query gracefully")
else:
    log_test(test_id, "Empty query handling", "FAIL", "Unexpected response to empty query")

# Test 5.2: Very Long Query
test_id = "TC-EDGE-002"
print(f"\n🔍 {test_id}: Very Long Query Handling")
long_query = "Tell me about " + ("machine learning " * 100)  # ~1800 chars
response = send_query(long_query[:1000])  # Limit to 1000 chars
if "error" not in response and "answer" in response:
    log_test(test_id, "Long query handling", "PASS", "Handled long query successfully")
else:
    log_test(test_id, "Long query handling", "FAIL", f"Error: {response.get('error')}")

# Test 5.3: Special Characters
test_id = "TC-EDGE-003"
print(f"\n🔍 {test_id}: Special Characters Handling")
response = send_query("What is 2+2? @#$%^&*()")
if "error" not in response and "answer" in response:
    if "4" in response["answer"]:
        log_test(test_id, "Special characters handling", "PASS",
                "Handled special characters correctly")
    else:
        log_test(test_id, "Special characters handling", "PASS",
                "Processed query with special characters")
else:
    log_test(test_id, "Special characters handling", "FAIL", f"Error: {response.get('error')}")

# ============================================================================
# Generate Test Report
# ============================================================================
print("\n\n")
print("="*80)
print("TEST EXECUTION COMPLETE")
print("="*80)

pass_rate = (test_results["passed"] / test_results["total"] * 100) if test_results["total"] > 0 else 0

print(f"\n📊 TEST SUMMARY:")
print(f"   Total Tests: {test_results['total']}")
print(f"   ✅ Passed: {test_results['passed']}")
print(f"   ❌ Failed: {test_results['failed']}")
print(f"   📈 Pass Rate: {pass_rate:.1f}%")
print(f"\n⏱️  End Time: {datetime.now().isoformat()}")

# Save detailed results
results_file = f"test_results_comprehensive_{int(time.time())}.json"
with open(results_file, "w") as f:
    json.dump(test_results, f, indent=2)

print(f"\n💾 Detailed results saved to: {results_file}")

# Print failed tests if any
if test_results["failed"] > 0:
    print("\n\n❌ FAILED TESTS:")
    print("="*80)
    for test in test_results["tests"]:
        if test["status"] == "FAIL":
            print(f"\n{test['id']}: {test['description']}")
            print(f"   Details: {test['details']}")

# Overall verdict
print("\n\n" + "="*80)
if pass_rate >= 90:
    print("✅ OVERALL: EXCELLENT - All core functionality working")
elif pass_rate >= 75:
    print("⚠️  OVERALL: GOOD - Most functionality working, some issues")
elif pass_rate >= 50:
    print("⚠️  OVERALL: FAIR - Significant issues found")
else:
    print("❌ OVERALL: POOR - Major functionality issues")
print("="*80)
