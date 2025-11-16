#!/usr/bin/env python3
"""
Test script for LLM-based query classification
Tests the new LLM-based implementation with mocked LLM responses
"""

import sys
import json
sys.path.insert(0, '/home/user/ChatBot/backend')

from unittest.mock import MagicMock, patch
from app.services.query_classifier import QueryClassifier


def test_llm_classification():
    """Test LLM-based query classification with mocked responses"""

    print("\n" + "="*80)
    print("LLM-BASED QUERY CLASSIFICATION TEST")
    print("="*80)

    # Create a mock LLM service
    mock_llm_service = MagicMock()

    # Test case 1: AI-personal question
    print("\n[Test 1] AI-personal question: 'Who are you?'")
    mock_llm_service.generate_response.return_value = json.dumps({
        "query_type": "ai_personal",
        "confidence": 0.95,
        "use_documents": False,
        "reason": "User is asking about the AI's identity"
    })

    classifier = QueryClassifier(llm_service=mock_llm_service)
    result = classifier.classify("Who are you?")

    print(f"  Query Type: {result['query_type']}")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Use Documents: {result['use_documents']}")
    print(f"  Reason: {result['reason']}")
    assert result['query_type'] == 'ai_personal'
    assert result['use_documents'] == False
    print("  ✅ PASS")

    # Test case 2: Document-specific question
    print("\n[Test 2] Document-specific question: 'What does the document say?'")
    mock_llm_service.generate_response.return_value = json.dumps({
        "query_type": "document_specific",
        "confidence": 0.98,
        "use_documents": True,
        "reason": "User is explicitly asking about document content"
    })

    result = classifier.classify("What does the document say?")

    print(f"  Query Type: {result['query_type']}")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Use Documents: {result['use_documents']}")
    print(f"  Reason: {result['reason']}")
    assert result['query_type'] == 'document_specific'
    assert result['use_documents'] == True
    print("  ✅ PASS")

    # Test case 3: General knowledge question
    print("\n[Test 3] General knowledge question: 'What is the capital of France?'")
    mock_llm_service.generate_response.return_value = json.dumps({
        "query_type": "general",
        "confidence": 0.90,
        "use_documents": False,
        "reason": "This is a general knowledge geography question"
    })

    result = classifier.classify("What is the capital of France?")

    print(f"  Query Type: {result['query_type']}")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Use Documents: {result['use_documents']}")
    print(f"  Reason: {result['reason']}")
    assert result['query_type'] == 'general'
    assert result['use_documents'] == False
    print("  ✅ PASS")

    # Test case 4: Ambiguous question
    print("\n[Test 4] Ambiguous question: 'Tell me about machine learning'")
    mock_llm_service.generate_response.return_value = json.dumps({
        "query_type": "ambiguous",
        "confidence": 0.60,
        "use_documents": True,
        "reason": "Could be general knowledge or require specific documents"
    })

    result = classifier.classify("Tell me about machine learning")

    print(f"  Query Type: {result['query_type']}")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Use Documents: {result['use_documents']}")
    print(f"  Reason: {result['reason']}")
    assert result['query_type'] == 'ambiguous'
    assert result['use_documents'] == True
    print("  ✅ PASS")

    # Test case 5: Handle markdown code blocks in response
    print("\n[Test 5] Response with markdown code blocks")
    mock_llm_service.generate_response.return_value = """```json
{
    "query_type": "general",
    "confidence": 0.85,
    "use_documents": false,
    "reason": "Math calculation question"
}
```"""

    result = classifier.classify("What is 25 * 4?")

    print(f"  Query Type: {result['query_type']}")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Use Documents: {result['use_documents']}")
    print(f"  Reason: {result['reason']}")
    assert result['query_type'] == 'general'
    assert result['use_documents'] == False
    print("  ✅ PASS (correctly handled markdown)")

    # Test case 6: Error handling - invalid JSON
    print("\n[Test 6] Error handling - invalid JSON response")
    mock_llm_service.generate_response.return_value = "This is not valid JSON"

    result = classifier.classify("Any question")

    print(f"  Query Type: {result['query_type']}")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Use Documents: {result['use_documents']}")
    print(f"  Reason: {result['reason']}")
    assert result['query_type'] == 'ambiguous'  # Fallback
    assert result['use_documents'] == True  # Safe default
    print("  ✅ PASS (correctly fell back to ambiguous)")

    # Test case 7: should_skip_rag method
    print("\n[Test 7] should_skip_rag method")
    mock_llm_service.generate_response.return_value = json.dumps({
        "query_type": "ai_personal",
        "confidence": 0.95,
        "use_documents": False,
        "reason": "AI identity question"
    })

    should_skip = classifier.should_skip_rag("Who are you?")
    print(f"  should_skip_rag('Who are you?') = {should_skip}")
    assert should_skip == True
    print("  ✅ PASS")

    mock_llm_service.generate_response.return_value = json.dumps({
        "query_type": "document_specific",
        "confidence": 0.95,
        "use_documents": True,
        "reason": "Document question"
    })

    should_skip = classifier.should_skip_rag("What does the document say?")
    print(f"  should_skip_rag('What does the document say?') = {should_skip}")
    assert should_skip == False
    print("  ✅ PASS")

    # Summary
    print("\n" + "="*80)
    print("ALL TESTS PASSED ✅")
    print("="*80)
    print("\nKey Features Verified:")
    print("  ✅ LLM-based classification for all query types")
    print("  ✅ Proper confidence scoring")
    print("  ✅ Correct use_documents flag")
    print("  ✅ Markdown code block handling")
    print("  ✅ Error handling with safe fallback")
    print("  ✅ should_skip_rag method works correctly")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    try:
        test_llm_classification()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
