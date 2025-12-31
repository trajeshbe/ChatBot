#!/usr/bin/env python3
"""
Quick test script for query classification
Tests the examples from the user's issue
"""

import sys
sys.path.insert(0, '/home/user/ChatBot/backend')

from app.services.query_classifier import query_classifier


def test_classification(query: str, expected_type: str = None):
    """Test a query and print classification"""
    result = query_classifier.classify(query)

    print(f"\n{'='*80}")
    print(f"Query: {query}")
    print(f"{'='*80}")
    print(f"Classification: {result['query_type']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Use Documents: {result['use_documents']}")
    print(f"Reason: {result['reason']}")

    if expected_type:
        status = "✅ PASS" if result['query_type'] == expected_type else "❌ FAIL"
        print(f"Expected: {expected_type} - {status}")

    return result


if __name__ == "__main__":
    print("\n" + "="*80)
    print("QUERY CLASSIFICATION TEST SUITE")
    print("="*80)

    # Test cases from user's issue
    test_cases = [
        # General knowledge (should NOT use documents)
        ("what is the length of the earth", "general"),
        ("how big is the sun", "general"),
        ("what is the capital of France", "general"),
        ("who invented the telephone", "general"),
        ("calculate 25 * 4", "general"),

        # AI personal (should NOT use documents)
        ("who are you", "ai_personal"),
        ("what can you do", "ai_personal"),
        ("tell me about yourself", "ai_personal"),

        # Document-specific (should use documents)
        ("tell about sri chaitanya school", "ambiguous"),  # Depends on context
        ("what does the document say about revenue", "document_specific"),
        ("summarize this PDF", "document_specific"),
        ("according to the uploaded file", "document_specific"),

        # Edge cases
        ("tell me about Python programming", "ambiguous"),  # Could be general or document
        ("what is machine learning", "general"),  # Tech term
    ]

    results = []
    passed = 0
    failed = 0

    for query, expected in test_cases:
        result = test_classification(query, expected)
        results.append((query, result))

        if result['query_type'] == expected:
            passed += 1
        else:
            failed += 1

    # Summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Total: {len(test_cases)}")
    print(f"Passed: {passed} ({passed/len(test_cases)*100:.1f}%)")
    print(f"Failed: {failed} ({failed/len(test_cases)*100:.1f}%)")

    print("\n" + "="*80)
    print("KEY FINDINGS:")
    print("="*80)

    general_count = sum(1 for _, r in results if r['query_type'] == 'general')
    doc_count = sum(1 for _, r in results if r['query_type'] == 'document_specific')
    personal_count = sum(1 for _, r in results if r['query_type'] == 'ai_personal')
    ambiguous_count = sum(1 for _, r in results if r['query_type'] == 'ambiguous')

    print(f"General Knowledge: {general_count} (skip RAG)")
    print(f"AI Personal: {personal_count} (skip RAG)")
    print(f"Document-Specific: {doc_count} (use RAG)")
    print(f"Ambiguous: {ambiguous_count} (use RAG)")

    skip_rag_count = sum(1 for _, r in results if not r['use_documents'])
    use_rag_count = sum(1 for _, r in results if r['use_documents'])

    print(f"\nTotal queries that SKIP RAG: {skip_rag_count}")
    print(f"Total queries that USE RAG: {use_rag_count}")
    print("="*80 + "\n")
