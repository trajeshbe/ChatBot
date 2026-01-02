#!/usr/bin/env python3
"""
Test Generic RAG functionality with sample data from documented use cases.

This script tests what CURRENTLY WORKS in the platform - generic RAG queries
against the sample data. It documents the gap between current capabilities
and the specialized functionality required by each module.

Usage:
    python scripts/testing/use_cases/test_generic_rag_with_sample_data.py
"""

import os
import sys
import json
import requests
import time
from pathlib import Path
from typing import Dict, List, Optional

# Configuration
API_BASE = os.getenv('API_URL', 'http://localhost:8000')
SAMPLE_DATA_DIR = Path(__file__).parent.parent.parent.parent / 'sample_data'

class UseCaseTestResult:
    def __init__(self, module_name: str, test_name: str):
        self.module_name = module_name
        self.test_name = test_name
        self.passed = False
        self.generic_rag_works = False
        self.specialized_feature_works = False
        self.gap_description = ""
        self.current_output = None
        self.expected_output = None

class GenericRAGTester:
    """Test current generic RAG functionality with sample data."""

    def __init__(self, api_base: str = API_BASE):
        self.api_base = api_base
        self.session_id = None
        self.results: List[UseCaseTestResult] = []

    def create_session(self) -> str:
        """Create a new chat session."""
        session_id = f"test_session_{int(time.time())}"
        print(f"✓ Created test session: {session_id}")
        return session_id

    def upload_document(self, file_path: Path, session_id: str) -> bool:
        """Upload a document to the platform."""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f)}
                data = {'session_id': session_id}
                response = requests.post(
                    f'{self.api_base}/api/v1/upload',
                    files=files,
                    data=data,
                    timeout=60
                )

            if response.status_code == 200:
                print(f"  ✓ Uploaded: {file_path.name}")
                return True
            else:
                print(f"  ✗ Upload failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"  ✗ Upload error: {str(e)}")
            return False

    def query_rag(self, question: str, session_id: str) -> Optional[Dict]:
        """Query the RAG system."""
        try:
            payload = {
                'query': question,
                'session_id': session_id,
                'use_rag': True
            }
            response = requests.post(
                f'{self.api_base}/api/v1/query',
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"  ✗ Query failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"  ✗ Query error: {str(e)}")
            return None

    # ==================== CONSTRUCTION MONITOR TESTS ====================

    def test_construction_monitor(self) -> List[UseCaseTestResult]:
        """Test Construction Monitor sample data."""
        print("\n" + "="*80)
        print("CONSTRUCTION MONITOR - Planning Application NER/REL")
        print("="*80)

        session_id = self.create_session()
        results = []

        # Upload planning application
        doc_path = SAMPLE_DATA_DIR / 'tier3_customer_pocs/construction_monitor/planning_application_sample.txt'
        if not self.upload_document(doc_path, session_id):
            return results

        # Wait for processing
        time.sleep(3)

        # Test 1: Generic text extraction (SHOULD WORK)
        test1 = UseCaseTestResult("Construction Monitor", "Extract application reference")
        print("\n[Test 1] Generic RAG: Extract application reference number")
        response = self.query_rag("What is the planning application reference number?", session_id)

        if response and '2024/0245/FUL' in response.get('answer', ''):
            test1.passed = True
            test1.generic_rag_works = True
            test1.current_output = response.get('answer')
            print(f"  ✓ PASS: Generic RAG found reference number")
            print(f"  Answer: {response.get('answer')[:200]}")
        else:
            test1.passed = False
            print(f"  ✗ FAIL: Could not extract reference number")

        test1.gap_description = "Generic RAG can extract simple facts, but cannot perform NER tagging of entities"
        results.append(test1)

        # Test 2: Named Entity Recognition (WILL NOT WORK - Feature Missing)
        test2 = UseCaseTestResult("Construction Monitor", "NER - Extract all organizations")
        print("\n[Test 2] Specialized NER: Extract all ORGANIZATION entities")

        # What we would call if NER service existed:
        # entities = ner_service.extract(text, entity_types=['ORGANIZATION'])

        test2.passed = False
        test2.generic_rag_works = False
        test2.specialized_feature_works = False
        test2.expected_output = {
            "entities": ["Barrat Homes Ltd", "Westminster City Council", "Smith Planning Consultants"]
        }
        test2.gap_description = "No NER model deployed. Generic RAG cannot identify and tag entity types."
        print(f"  ✗ FEATURE MISSING: NER service not implemented")
        print(f"  Expected: {test2.expected_output}")
        print(f"  Current: Generic text search only")
        results.append(test2)

        # Test 3: Relationship Extraction (WILL NOT WORK - Feature Missing)
        test3 = UseCaseTestResult("Construction Monitor", "REL - Extract applicant relationship")
        print("\n[Test 3] Specialized REL: Extract APPLICANT_FOR relationships")

        test3.passed = False
        test3.specialized_feature_works = False
        test3.expected_output = {
            "relationships": [
                {"head": "Barrat Homes Ltd", "relation": "APPLICANT_FOR", "tail": "2024/0245/FUL"}
            ]
        }
        test3.gap_description = "No REL model. Cannot extract structured relationships between entities."
        print(f"  ✗ FEATURE MISSING: REL service not implemented")
        print(f"  Expected: {test3.expected_output}")
        results.append(test3)

        return results

    # ==================== BRITISH COUNCIL TESTS ====================

    def test_british_council(self) -> List[UseCaseTestResult]:
        """Test British Council profile matching."""
        print("\n" + "="*80)
        print("BRITISH COUNCIL - Profile-Course Matching")
        print("="*80)

        session_id = self.create_session()
        results = []

        # Upload learner profiles and course catalog
        learner_path = SAMPLE_DATA_DIR / 'tier3_customer_pocs/british_council/learner_profile_sample.json'
        course_path = SAMPLE_DATA_DIR / 'tier3_customer_pocs/british_council/course_catalog_sample.json'

        if not self.upload_document(learner_path, session_id):
            return results
        if not self.upload_document(course_path, session_id):
            return results

        time.sleep(3)

        # Test 1: Generic information retrieval (SHOULD WORK)
        test1 = UseCaseTestResult("British Council", "Extract learner information")
        print("\n[Test 1] Generic RAG: Find learner named Ahmed")
        response = self.query_rag("What is Ahmed Hassan's English level?", session_id)

        if response and 'B1' in response.get('answer', ''):
            test1.passed = True
            test1.generic_rag_works = True
            test1.current_output = response.get('answer')
            print(f"  ✓ PASS: Found Ahmed's English level")
        else:
            print(f"  ✗ FAIL: Could not find information")

        test1.gap_description = "Can retrieve facts, but cannot match profiles to courses based on multiple criteria"
        results.append(test1)

        # Test 2: Profile-Course Matching (WILL NOT WORK - Feature Missing)
        test2 = UseCaseTestResult("British Council", "Match learner to suitable courses")
        print("\n[Test 2] Specialized Matching: Find best courses for Ahmed Hassan")

        test2.passed = False
        test2.specialized_feature_works = False
        test2.expected_output = {
            "learner_id": "BC2024001",
            "recommended_courses": [
                {
                    "course_id": "ACAD_ENG_PREP_2024",
                    "match_score": 0.92,
                    "reasons": [
                        "Level match: B1 → B1-B2 required",
                        "Goal alignment: Academic preparation",
                        "Budget fit: £950 within £500-£1000",
                        "Schedule: Online evening matches availability"
                    ]
                }
            ]
        }
        test2.gap_description = "No matching algorithm. Cannot score courses based on level, goals, budget, schedule."
        print(f"  ✗ FEATURE MISSING: Profile matching service not implemented")
        print(f"  Expected output:")
        print(f"  {json.dumps(test2.expected_output, indent=2)}")
        results.append(test2)

        return results

    # ==================== GRANT THORNTON TESTS ====================

    def test_grant_thornton(self) -> List[UseCaseTestResult]:
        """Test Grant Thornton financial analysis."""
        print("\n" + "="*80)
        print("GRANT THORNTON - Credit Profile Analysis")
        print("="*80)

        session_id = self.create_session()
        results = []

        # Upload financial ratios CSV
        ratios_path = SAMPLE_DATA_DIR / 'tier3_customer_pocs/grant_thornton/company_financial_ratios.csv'
        benchmarks_path = SAMPLE_DATA_DIR / 'tier3_customer_pocs/grant_thornton/credit_analysis_benchmarks.json'

        if not self.upload_document(ratios_path, session_id):
            return results
        if not self.upload_document(benchmarks_path, session_id):
            return results

        time.sleep(3)

        # Test 1: Generic data retrieval (SHOULD WORK)
        test1 = UseCaseTestResult("Grant Thornton", "Find company current ratio")
        print("\n[Test 1] Generic RAG: What is TechGlobal Inc's current ratio?")
        response = self.query_rag("What is TechGlobal Inc's current ratio?", session_id)

        if response and '2.45' in response.get('answer', ''):
            test1.passed = True
            test1.generic_rag_works = True
            test1.current_output = response.get('answer')
            print(f"  ✓ PASS: Found current ratio")
        else:
            print(f"  ✗ FAIL: Could not find ratio")

        test1.gap_description = "Can retrieve values, but cannot calculate credit ratings or compare to benchmarks"
        results.append(test1)

        # Test 2: Credit Rating Calculation (WILL NOT WORK - Feature Missing)
        test2 = UseCaseTestResult("Grant Thornton", "Calculate credit rating")
        print("\n[Test 2] Specialized Analysis: Calculate TechGlobal Inc's credit rating")

        test2.passed = False
        test2.specialized_feature_works = False
        test2.expected_output = {
            "company": "TechGlobal Inc",
            "credit_rating": "AA",
            "z_score": 3.85,
            "risk_category": "Safe Zone",
            "strengths": [
                "Strong liquidity (Current Ratio: 2.45 > 2.0 benchmark)",
                "Low leverage (Debt-to-Equity: 0.32 < 0.5 benchmark)",
                "Excellent interest coverage (12.5x > 8x benchmark)"
            ],
            "recommendation": "Low credit risk, approve for lending"
        }
        test2.gap_description = "No financial calculation engine. Cannot compute Z-score, assign ratings, or benchmark."
        print(f"  ✗ FEATURE MISSING: Financial analysis service not implemented")
        print(f"  Expected output:")
        print(f"  {json.dumps(test2.expected_output, indent=2)}")
        results.append(test2)

        return results

    # ==================== CRU TESTS ====================

    def test_cru_mining(self) -> List[UseCaseTestResult]:
        """Test CRU mining market intelligence extraction."""
        print("\n" + "="*80)
        print("CRU - Mining Market Intelligence Extraction")
        print("="*80)

        session_id = self.create_session()
        results = []

        # Upload mining report
        report_path = SAMPLE_DATA_DIR / 'tier3_customer_pocs/cru/mining_market_report_sample.txt'
        if not self.upload_document(report_path, session_id):
            return results

        time.sleep(3)

        # Test 1: Generic fact extraction (SHOULD WORK)
        test1 = UseCaseTestResult("CRU", "Extract current copper price")
        print("\n[Test 1] Generic RAG: What is the current copper spot price?")
        response = self.query_rag("What is the current copper spot price?", session_id)

        if response and '8,450' in response.get('answer', ''):
            test1.passed = True
            test1.generic_rag_works = True
            test1.current_output = response.get('answer')
            print(f"  ✓ PASS: Found copper price")
        else:
            print(f"  ✗ FAIL: Could not find price")

        test1.gap_description = "Can extract isolated facts, but cannot structure data for tables/charts"
        results.append(test1)

        # Test 2: Structured Data Extraction (WILL NOT WORK - Feature Missing)
        test2 = UseCaseTestResult("CRU", "Extract production data table")
        print("\n[Test 2] Specialized Extraction: Extract all country production data as structured table")

        test2.passed = False
        test2.specialized_feature_works = False
        test2.expected_output = {
            "production_data": [
                {"country": "Chile", "production": 1420000, "change_yoy": "+2.3%"},
                {"country": "Peru", "production": 580000, "change_yoy": "+5.1%"},
                {"country": "DRC", "production": 425000, "change_yoy": "+8.5%"}
            ]
        }
        test2.gap_description = "No structured extraction templates. Cannot extract multi-row tables or time-series data."
        print(f"  ✗ FEATURE MISSING: Structured extraction service not implemented")
        print(f"  Expected: Structured table with 3 rows × 3 columns")
        results.append(test2)

        return results

    # ==================== PROCUREMENT MATCHER TESTS ====================

    def test_procurement_matcher(self) -> List[UseCaseTestResult]:
        """Test Procurement Matcher RFP-supplier matching."""
        print("\n" + "="*80)
        print("PROCUREMENT MATCHER - RFP-Supplier Matching")
        print("="*80)

        session_id = self.create_session()
        results = []

        # Upload RFP and supplier profiles
        rfp_path = SAMPLE_DATA_DIR / 'tier2_domain_verticals/procurement_matcher/rfp_construction_materials.txt'
        suppliers_path = SAMPLE_DATA_DIR / 'tier2_domain_verticals/procurement_matcher/supplier_profiles.json'

        if not self.upload_document(rfp_path, session_id):
            return results
        if not self.upload_document(suppliers_path, session_id):
            return results

        time.sleep(3)

        # Test 1: Generic information retrieval (SHOULD WORK)
        test1 = UseCaseTestResult("Procurement Matcher", "Extract RFP value")
        print("\n[Test 1] Generic RAG: What is the estimated contract value?")
        response = self.query_rag("What is the estimated contract value for the construction materials RFP?", session_id)

        if response and '4.5' in response.get('answer', '') or '5.2' in response.get('answer', ''):
            test1.passed = True
            test1.generic_rag_works = True
            test1.current_output = response.get('answer')
            print(f"  ✓ PASS: Found contract value")
        else:
            print(f"  ✗ FAIL: Could not find value")

        test1.gap_description = "Can find facts, but cannot match requirements to supplier capabilities"
        results.append(test1)

        # Test 2: Supplier Matching with Scoring (WILL NOT WORK - Feature Missing)
        test2 = UseCaseTestResult("Procurement Matcher", "Match suppliers to RFP")
        print("\n[Test 2] Specialized Matching: Rank suppliers by suitability for RFP")

        test2.passed = False
        test2.specialized_feature_works = False
        test2.expected_output = {
            "rfp_id": "RFP-2024-CM-00128",
            "ranked_suppliers": [
                {
                    "supplier_id": "SUP-UK-002",
                    "company_name": "EcoStruct Materials PLC",
                    "overall_score": 0.89,
                    "scores": {
                        "price": 0.85,
                        "technical": 0.92,
                        "delivery": 0.95,
                        "sustainability": 0.98,
                        "experience": 0.87
                    },
                    "strengths": [
                        "Local (8km from site)",
                        "Premium sustainability credentials (EPD, FSC, Passivhaus)",
                        "96% on-time delivery",
                        "Relevant project: Oxford Passive House Development"
                    ],
                    "gaps": [
                        "Limited concrete supply capability",
                        "Smaller scale than required"
                    ]
                }
            ]
        }
        test2.gap_description = "No matching algorithm. Cannot score suppliers on multiple weighted criteria."
        print(f"  ✗ FEATURE MISSING: Supplier matching service not implemented")
        print(f"  Expected: Ranked list with detailed scoring")
        results.append(test2)

        return results

    # ==================== MAIN TEST RUNNER ====================

    def run_all_tests(self):
        """Run all use case tests."""
        print("\n")
        print("="*80)
        print(" SAMPLE DATA USE CASE TESTING")
        print(" Testing Current Generic RAG vs. Required Specialized Features")
        print("="*80)

        all_results = []

        # Run each module's tests
        all_results.extend(self.test_construction_monitor())
        all_results.extend(self.test_british_council())
        all_results.extend(self.test_grant_thornton())
        all_results.extend(self.test_cru_mining())
        all_results.extend(self.test_procurement_matcher())

        # Print summary
        self.print_summary(all_results)

        return all_results

    def print_summary(self, results: List[UseCaseTestResult]):
        """Print test summary report."""
        print("\n" + "="*80)
        print(" TEST SUMMARY")
        print("="*80)

        total = len(results)
        generic_rag_working = sum(1 for r in results if r.generic_rag_works)
        specialized_working = sum(1 for r in results if r.specialized_feature_works)

        print(f"\nTotal Tests: {total}")
        print(f"Generic RAG Working: {generic_rag_working}/{total} ({generic_rag_working/total*100:.0f}%)")
        print(f"Specialized Features Working: {specialized_working}/{total} ({specialized_working/total*100:.0f}%)")

        print("\n" + "-"*80)
        print("FUNCTIONALITY GAPS BY MODULE")
        print("-"*80)

        by_module = {}
        for result in results:
            if result.module_name not in by_module:
                by_module[result.module_name] = []
            by_module[result.module_name].append(result)

        for module, tests in by_module.items():
            print(f"\n{module}:")
            for test in tests:
                status = "✓" if test.passed else "✗"
                feature_status = "WORKS" if test.specialized_feature_works else "MISSING"
                print(f"  {status} {test.test_name}")
                print(f"     Generic RAG: {'Yes' if test.generic_rag_works else 'No'}")
                print(f"     Specialized Feature: {feature_status}")
                if test.gap_description:
                    print(f"     Gap: {test.gap_description}")

        print("\n" + "="*80)
        print(" CONCLUSION")
        print("="*80)
        print("\nCurrent Platform Capability:")
        print("  ✓ Generic RAG: Can answer simple factual questions from documents")
        print("  ✓ Document upload and text extraction")
        print("  ✓ Vector search and similarity matching")

        print("\nMissing Specialized Capabilities (required by documented use cases):")
        print("  ✗ Named Entity Recognition (NER) - Construction Monitor, Procurement")
        print("  ✗ Relationship Extraction (REL) - Construction Monitor")
        print("  ✗ Profile Matching Algorithms - British Council, Talent Search")
        print("  ✗ Financial Calculation Engine - Grant Thornton, Credit Analyzer")
        print("  ✗ Structured Data Extraction - CRU, Mine Scope, Maritime Reports")
        print("  ✗ Multi-criteria Scoring - Procurement Matcher, Tender Intelligence")
        print("  ✗ Specialized UI Components - All modules need custom interfaces")

        print("\nImplementation Priority:")
        print("  P0: NER/REL pipeline (Construction Monitor)")
        print("  P0: Matching algorithms (British Council, Procurement)")
        print("  P1: Financial analysis (Grant Thornton)")
        print("  P1: Structured extraction (CRU)")
        print("  P2: Specialized UIs for all modules")

        print("\n" + "="*80)


if __name__ == '__main__':
    tester = GenericRAGTester()
    results = tester.run_all_tests()

    # Exit with appropriate code
    all_specialized_working = all(r.specialized_feature_works for r in results)
    sys.exit(0 if all_specialized_working else 1)
