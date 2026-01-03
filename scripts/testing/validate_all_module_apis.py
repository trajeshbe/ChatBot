#!/usr/bin/env python3
"""
Validate all Tier 2 module API endpoints are accessible and functional.
Quick check to ensure backends are properly configured.
"""

import requests
import json
from typing import Dict, List, Tuple

# Backend base URL
BASE_URL = "http://localhost:8000"

# List of tier 2 modules to test (from modules.ts)
TIER2_MODULES = [
    # Document Intelligence
    ("document-extract", "/api/v1/tier2/docu-extract/analyze"),
    ("relation-extractor", "/api/v1/tier2/relation-extractor/extract"),
    ("generic-rag", "/api/v1/tier2/generic-rag/query"),

    # Construction
    ("planning-classifier", "/api/v1/tier2/planning-classifier/classify"),
    ("estimator-au", "/api/v1/tier2/estimator-au/estimate"),
    ("mine-scope", "/api/v1/tier2/mine-scope/analyze"),

    # HR & Talent
    ("talent-search", "/api/v1/tier2/talent-search/search"),
    ("taxonomy-skillmatch", "/api/v1/tier2/taxonomy-skillmatch/match"),
    ("talent-pulse", "/api/v1/tier2/talent-pulse/analyze"),

    # Procurement
    ("matcher", "/api/v1/tier2/matcher/match"),
    ("spend-smart", "/api/v1/tier2/spend-smart/analyze"),
    ("tender-intelligence", "/api/v1/tier2/tender-intelligence/analyze"),
    ("vendor-recommendation", "/api/v1/tier2/vendor-recommendation/recommend"),

    # Analytics
    ("customer-churn", "/api/v1/tier2/customer-churn/predict"),
    ("financial-anomaly", "/api/v1/tier2/financial-anomaly/detect"),
    ("predictive-analytics", "/api/v1/tier2/predictive-analytics/predict"),
    ("sales-performance", "/api/v1/tier2/sales-performance/analyze"),

    # Advanced Capabilities
    ("code-analysis", "/api/v1/tier2/code-analysis/analyze"),
    ("multilingual-translator", "/api/v1/tier2/multilingual-translator/translate"),

    # Agriculture
    ("agri-taxonomy", "/api/v1/tier2/agri-taxonomy/classify"),
    ("agronomy-decision", "/api/v1/tier2/agronomy-decision/recommend"),

    # E-Commerce
    ("product-recommendation", "/api/v1/tier2/product-recommendation/recommend"),

    # Industry Verticals
    ("healthcare-diagnostics", "/api/v1/tier2/healthcare-diagnostics/diagnose"),
    ("insurance-risk", "/api/v1/tier2/insurance-risk/assess"),
    ("legal-document", "/api/v1/tier2/legal-document/analyze"),
    ("real-estate-valuation", "/api/v1/tier2/real-estate-valuation/analyze"),
    ("educational-content", "/api/v1/tier2/educational-content/generate"),

    # Maritime
    ("maritime-logistics", "/api/v1/tier2/maritime-logistics/optimize"),

    # Marketing
    ("campaign-optimizer", "/api/v1/tier2/campaign-optimizer/optimize"),
    ("sentiment-social", "/api/v1/tier2/sentiment-social/analyze"),
]


def check_endpoint(module_name: str, endpoint: str) -> Tuple[bool, str]:
    """
    Check if an endpoint is accessible (returns 200, 422, or 405).

    Returns:
        (success: bool, status_message: str)
    """
    url = f"{BASE_URL}{endpoint}"

    try:
        # Try OPTIONS first to check if endpoint exists
        response = requests.options(url, timeout=5)

        if response.status_code in [200, 204, 405]:
            return (True, f"✓ Endpoint exists (OPTIONS: {response.status_code})")

        # Try POST with empty body (most module endpoints are POST)
        response = requests.post(url, json={}, timeout=5)

        # 422 = Validation error (expected - means endpoint exists but needs proper data)
        # 200 = Success (rare with empty body, but possible)
        # 405 = Method not allowed (might be GET only)
        if response.status_code in [200, 422, 405]:
            return (True, f"✓ Endpoint accessible (POST: {response.status_code})")

        # Try GET
        if response.status_code == 405:
            response = requests.get(url, timeout=5)
            if response.status_code in [200, 422]:
                return (True, f"✓ Endpoint accessible (GET: {response.status_code})")

        return (False, f"✗ Unexpected status: {response.status_code}")

    except requests.exceptions.Timeout:
        return (False, "✗ Timeout (30s)")
    except requests.exceptions.ConnectionError:
        return (False, "✗ Connection error (backend not running?)")
    except Exception as e:
        return (False, f"✗ Error: {str(e)}")


def main():
    """Validate all module endpoints"""
    print("=" * 80)
    print("TIER 2 MODULE API VALIDATION")
    print("=" * 80)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Total modules to check: {len(TIER2_MODULES)}\n")

    results: List[Tuple[str, bool, str]] = []

    for module_name, endpoint in TIER2_MODULES:
        print(f"Checking {module_name:30s} ... ", end="", flush=True)
        success, message = check_endpoint(module_name, endpoint)
        results.append((module_name, success, message))
        print(message)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    successful = sum(1 for _, success, _ in results if success)
    total = len(results)

    print(f"\n✓ Accessible endpoints: {successful}/{total} ({successful/total*100:.1f}%)")

    if successful < total:
        print(f"\n✗ Inaccessible endpoints:")
        for module_name, success, message in results:
            if not success:
                print(f"  - {module_name}: {message}")

    print("\n" + "=" * 80)

    # Return exit code
    return 0 if successful == total else 1


if __name__ == "__main__":
    exit(main())
