#!/usr/bin/env python3
"""
Test script to verify query classifier fix
Tests that word boundary matching prevents false positives
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_query(query_text, expected_classification=None):
    """Test a query and check its classification"""
    print(f"\n{'='*80}")
    print(f"Testing Query: \"{query_text}\"")
    print(f"{'='*80}")

    response = requests.post(
        f"{BASE_URL}/api/v1/query",
        json={
            "query": query_text,
            "session_id": "test_classifier_fix",
            "model": "gpt-4o-mini"
        },
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Query successful")
        print(f"Classification: {data.get('query_classification', 'N/A')}")
        print(f"Sources found: {len(data.get('sources', []))}")
        print(f"Answer preview: {data.get('answer', '')[:200]}...")

        if expected_classification:
            actual = data.get('query_classification', {}).get('query_type', 'unknown')
            if actual == expected_classification:
                print(f"✅ PASS: Classification matches expected ({expected_classification})")
            else:
                print(f"❌ FAIL: Expected {expected_classification}, got {actual}")
    else:
        print(f"✗ Query failed: {response.status_code}")
        print(f"Error: {response.text}")

def main():
    print("\n" + "="*80)
    print("QUERY CLASSIFIER FIX VERIFICATION")
    print("="*80)
    print("\nTesting that word boundaries prevent false positives...")

    # Test 1: The bug case - should NOT match "hi" in "Architecture"
    test_query(
        "Give me the number of floors in the Architecture Diagram",
        expected_classification="document_specific"  # Should search documents
    )

    # Test 2: Valid ai_personal - standalone "hi"
    test_query(
        "hi",
        expected_classification="ai_personal"
    )

    # Test 3: Valid ai_personal - "hello"
    test_query(
        "hello",
        expected_classification="ai_personal"
    )

    # Test 4: Another potential false positive - "this document"
    test_query(
        "What is this document about?",
        expected_classification="document_specific"  # Should search documents, not match "hi" in "this"
    )

    # Test 5: Another false positive - "while"
    test_query(
        "Explain while loops in programming",
        expected_classification=None  # Should NOT match "hi" in "while"
    )

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
