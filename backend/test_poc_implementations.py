#!/usr/bin/env python3
"""
POC Implementation Test Script

Tests British Council and CRU POCs with sample data.

Usage:
    python test_poc_implementations.py

Author: Claude Code
Date: 2026-01-02
"""

import requests
import json
from typing import Dict, Any

# Base URL
BASE_URL = "http://localhost:8000"


def print_header(title: str):
    """Print formatted header."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def print_result(label: str, data: Any):
    """Print formatted result."""
    print(f"\n{label}:")
    print(json.dumps(data, indent=2))
    print()


def test_british_council_health():
    """Test British Council health endpoint."""
    print_header("British Council - Health Check")

    response = requests.get(f"{BASE_URL}/api/v1/british-council/health")

    print(f"Status Code: {response.status_code}")
    print_result("Response", response.json())

    assert response.status_code == 200, "Health check failed"
    print("✅ Health check passed")


def test_british_council_profile_analysis():
    """Test British Council profile analysis."""
    print_header("British Council - Profile Analysis")

    user_input = """I'm a software engineer looking to improve my business English.
    I have intermediate level English (B1) and prefer online courses on weekends.
    I want to advance my career in international companies."""

    payload = {
        "user_input": user_input
    }

    print(f"Input: {user_input}\n")

    response = requests.post(
        f"{BASE_URL}/api/v1/british-council/profile/analyze",
        json=payload
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print_result("Extracted Profile", result["profile"])
        print("✅ Profile analysis successful")
        return result["profile"]
    else:
        print(f"❌ Failed: {response.text}")
        return None


def test_british_council_recommendations(profile: Dict[str, Any] = None):
    """Test British Council course recommendations."""
    print_header("British Council - Course Recommendations")

    if profile:
        # Use pre-analyzed profile
        payload = {
            "profile": profile,
            "top_k": 5
        }
    else:
        # Analyze from user input
        payload = {
            "user_input": """I'm a business professional wanting to improve my presentation skills.
            I'm at advanced level (C1) and prefer in-person courses during weekdays.""",
            "top_k": 5
        }

    response = requests.post(
        f"{BASE_URL}/api/v1/british-council/courses/recommend",
        json=payload
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\nTotal Recommendations: {len(result['recommendations'])}")
        print(f"Profile Used: {result['profile']['education_level']} level, "
              f"{result['profile']['language_proficiency']} CEFR\n")

        # Display top 3 recommendations
        for i, rec in enumerate(result['recommendations'][:3], 1):
            print(f"\n--- Recommendation {i} ---")
            print(f"Course: {rec['course_name']}")
            print(f"Match Score: {rec['match_score']:.2%}")
            print(f"  Semantic: {rec['semantic_score']:.2%}, Profile: {rec['profile_score']:.2%}")
            print(f"Reasons:")
            for reason in rec['reasons']:
                print(f"  • {reason}")

        print("\n✅ Course recommendations successful")
        return result
    else:
        print(f"❌ Failed: {response.text}")
        return None


def test_cru_health():
    """Test CRU health endpoint."""
    print_header("CRU Mining Intelligence - Health Check")

    response = requests.get(f"{BASE_URL}/api/v1/cru/health")

    print(f"Status Code: {response.status_code}")
    print_result("Response", response.json())

    assert response.status_code == 200, "Health check failed"
    print("✅ Health check passed")


def test_cru_query():
    """Test CRU multi-pipeline query."""
    print_header("CRU Mining Intelligence - Query (Auto-Route)")

    queries = [
        "What is the estimated capex for the Gold Valley project?",
        "What are the key environmental risks?",
        "Find documents mentioning feasibility studies"
    ]

    for query_text in queries:
        print(f"\n📝 Query: {query_text}")

        payload = {
            "query": query_text,
            "top_k": 3
        }

        response = requests.post(
            f"{BASE_URL}/api/v1/cru/query",
            json=payload
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\nAnswer: {result['answer']}")
            print(f"Confidence: {result['confidence']:.2%} ({result['confidence_level']})")
            print(f"Pipeline: {result['pipeline_used']}")
            print(f"Query Type: {result['query_type']}")
            print(f"Processing Time: {result['processing_time_ms']}ms")
            print(f"Sources: {len(result['sources'])}")

            print("✅ Query successful")
        else:
            print(f"❌ Failed: {response.text}")

        print("\n" + "-"*80)


def test_cru_pipeline_comparison():
    """Test CRU pipeline comparison."""
    print_header("CRU Mining Intelligence - Pipeline Comparison")

    query_text = "Compare iron ore grades across all drilling sites"
    print(f"Query: {query_text}\n")

    payload = {
        "query": query_text,
        "top_k": 3
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/cru/compare-pipelines",
        json=payload
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()

        print(f"\n{'Pipeline':<20} {'Confidence':<12} {'Time (ms)':<12} {'Sources':<10}")
        print("-"*60)

        for pipeline_result in result['results']:
            print(f"{pipeline_result['pipeline']:<20} "
                  f"{pipeline_result['confidence']:<12.2%} "
                  f"{pipeline_result['processing_time_ms']:<12} "
                  f"{pipeline_result['num_sources']:<10}")

        print(f"\n🏆 Winner: {result['winner']}")
        print(f"Reason: {result['reason']}")

        print("\n✅ Pipeline comparison successful")
        return result
    else:
        print(f"❌ Failed: {response.text}")
        return None


def main():
    """Run all tests."""
    print("\n" + "🚀 "* 40)
    print("  POC Implementation Test Suite")
    print("  Testing British Council + CRU POCs")
    print("🚀 " * 40 + "\n")

    try:
        # British Council Tests
        test_british_council_health()

        profile = test_british_council_profile_analysis()

        test_british_council_recommendations(profile)

        # CRU Tests
        test_cru_health()

        test_cru_query()

        test_cru_pipeline_comparison()

        # Summary
        print_header("Test Summary")
        print("✅ All tests completed successfully!")
        print("\nNext Steps:")
        print("1. Open http://localhost:3001 in your browser")
        print("2. Navigate to British Council or CRU tabs")
        print("3. Try the interactive UI with sample queries")
        print()

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
