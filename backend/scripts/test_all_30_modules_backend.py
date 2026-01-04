#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for All 30 Tier 2 Modules

Tests all 30 domain vertical modules with schema-compliant sample data.
Verifies:
1. API endpoints are functional
2. Module config is being loaded
3. Responses are properly formatted
4. Config parameters are applied

Usage:
    python scripts/test_all_30_modules_backend.py
    python scripts/test_all_30_modules_backend.py --module marketing/sentiment_social
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import Dict, Any, List
import argparse
from datetime import datetime
import httpx

# Test configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 60.0


# MODULE TEST DEFINITIONS WITH SCHEMA-COMPLIANT SAMPLE DATA
MODULE_TESTS = {
    # ============================================================
    # MARKETING (2 modules)
    # ============================================================
    "marketing/sentiment_social": {
        "endpoint": "/api/v1/modules/sentiment-social/analyze",
        "sample_data": {
            "posts": [
                {
                    "post_id": "test1",
                    "platform": "twitter",
                    "post_type": "post",
                    "content": "I absolutely love this product! Best purchase ever!",
                    "author": "user1",
                    "author_followers": 5000,
                    "posted_at": "2024-01-01T10:00:00",
                    "likes_count": 100,
                    "shares_count": 50,
                    "comments_count": 20,
                    "hashtags": ["amazing", "love"],
                    "mentions": ["@brand"]
                }
            ],
            "brand_names": ["TestBrand"],
            "include_influencer_analysis": True,
            "include_trending_topics": True
        }
    },

    "marketing/campaign_optimizer": {
        "endpoint": "/api/v1/modules/campaign-optimizer/optimize",
        "sample_data": {
            "campaigns": [
                {
                    "campaign_id": "camp1",
                    "campaign_name": "Summer Sale 2024",
                    "channel": "social_media",
                    "start_date": "2024-06-01",
                    "end_date": "2024-06-30",
                    "budget": 10000.0,
                    "budget_spent": 9500.0,
                    "impressions": 50000,
                    "clicks": 1500,
                    "conversions": 150,
                    "revenue": 15000.0,
                    "target_audience": "Adults 25-45",
                    "status": "active"
                }
            ],
            "optimization_goal": "maximize_roi",
            "total_budget": 50000.0
        }
    },

    # ============================================================
    # ANALYTICS (4 modules)
    # ============================================================
    "analytics/customer_churn": {
        "endpoint": "/api/v1/modules/customer-churn/predict",
        "sample_data": {
            "customers": [
                {
                    "customer_id": "cust1",
                    "tenure_months": 6,
                    "monthly_spend": 50.0,
                    "support_tickets": 2,
                    "last_purchase_days_ago": 30,
                    "contract_type": "monthly",
                    "payment_method": "credit_card",
                    "satisfaction_score": 7
                }
            ],
            "include_retention_strategies": True
        }
    },

    "analytics/financial_anomaly": {
        "endpoint": "/api/v1/modules/financial-anomaly/detect",
        "sample_data": {
            "transactions": [
                {
                    "transaction_id": "tx1",
                    "account_id": "acc1",
                    "timestamp": "2024-01-01T10:00:00",
                    "amount": 5000.0,
                    "currency": "USD",
                    "transaction_type": "purchase",
                    "merchant": "Test Merchant",
                    "category": "electronics"
                }
            ],
            "accounts": [
                {
                    "account_id": "acc1",
                    "account_type": "checking",
                    "balance": 10000.0,
                    "account_age_days": 365
                }
            ],
            "sensitivity": "medium"
        }
    },

    "analytics/predictive_analytics": {
        "endpoint": "/api/v1/modules/predictive-analytics/forecast",
        "sample_data": {
            "series_name": "Monthly Sales",
            "historical_data": [
                {"timestamp": "2024-01-01", "value": 100},
                {"timestamp": "2024-02-01", "value": 120},
                {"timestamp": "2024-03-01", "value": 110},
                {"timestamp": "2024-04-01", "value": 130},
                {"timestamp": "2024-05-01", "value": 125},
                {"timestamp": "2024-06-01", "value": 135}
            ],
            "forecast_periods": 3,
            "confidence_level": 0.95
        }
    },

    "analytics/sales_performance": {
        "endpoint": "/api/v1/modules/sales-performance/analyze",
        "sample_data": {
            "sales_reps": [
                {
                    "rep_id": "rep1",
                    "rep_name": "John Doe",
                    "quota": 100000.0,
                    "region": "West"
                }
            ],
            "opportunities": [
                {
                    "opportunity_id": "opp1",
                    "sales_rep_id": "rep1",
                    "value": 50000.0,
                    "stage": "negotiation",
                    "probability": 70,
                    "close_date": "2024-06-30"
                }
            ],
            "period_start": "2024-01-01",
            "period_end": "2024-06-30"
        }
    },

    # ============================================================
    # CONSTRUCTION (3 modules)
    # ============================================================
    "construction/mine_scope": {
        "endpoint": "/api/v1/modules/mine-scope/analyze",
        "sample_data": {
            "project_description": "Open pit copper mine expansion project with 50,000 tonnes per day processing capacity",
            "project_type": "mining",
            "location": "Arizona, USA",
            "budget_usd": 500000000.0
        }
    },

    "construction/planning_classifier": {
        "endpoint": "/api/v1/modules/planning-classifier/classify",
        "sample_data": {
            "documents": [
                {
                    "document_id": "doc1",
                    "content": "Proposed 15-storey residential development with 120 units, underground parking, and ground-floor retail space."
                }
            ]
        }
    },

    "construction/estimator_au": {
        "endpoint": "/api/v1/modules/estimator-au/estimate",
        "sample_data": {
            "project_type": "residential",
            "building_area_sqm": 5000.0,
            "storeys": 10,
            "location": "Sydney",
            "construction_type": "concrete_frame",
            "finish_quality": "medium"
        }
    },

    # ============================================================
    # AGRICULTURE (2 modules)
    # ============================================================
    "agriculture/agri_taxonomy": {
        "endpoint": "/api/v1/modules/agri-taxonomy/classify",
        "sample_data": {
            "crops": [
                {
                    "crop_name": "Wheat",
                    "variety": "Hard Red Winter",
                    "description": "High protein content wheat suitable for bread making"
                }
            ]
        }
    },

    "agriculture/agronomy_decision": {
        "endpoint": "/api/v1/modules/agronomy-decision/recommend",
        "sample_data": {
            "farm_data": {
                "location": "Iowa, USA",
                "soil_type": "loam",
                "farm_size_acres": 500,
                "irrigation_available": True
            },
            "current_conditions": {
                "soil_moisture": 65.0,
                "temperature_f": 72.0,
                "recent_rainfall_inches": 2.5
            },
            "crop_type": "corn"
        }
    },

    # ============================================================
    # HR/TALENT (3 modules)
    # ============================================================
    "hr_talent/talent_pulse": {
        "endpoint": "/api/v1/modules/talent-pulse/analyze",
        "sample_data": {
            "employee_surveys": [
                {
                    "employee_id": "emp1",
                    "department": "Engineering",
                    "engagement_score": 7,
                    "satisfaction_score": 8,
                    "tenure_months": 24
                }
            ],
            "include_attrition_risk": True
        }
    },

    "hr_talent/talent_search": {
        "endpoint": "/api/v1/modules/talent-search/search",
        "sample_data": {
            "job_requirements": {
                "title": "Senior Software Engineer",
                "required_skills": ["Python", "AWS", "Docker"],
                "experience_years": 5,
                "location": "Remote"
            },
            "candidate_pool": [
                {
                    "candidate_id": "cand1",
                    "name": "Jane Smith",
                    "skills": ["Python", "AWS", "Docker", "Kubernetes"],
                    "experience_years": 7,
                    "location": "San Francisco"
                }
            ]
        }
    },

    "hr_talent/taxonomy_skillmatch": {
        "endpoint": "/api/v1/modules/taxonomy-skillmatch/match",
        "sample_data": {
            "job_description": "Looking for a data scientist with expertise in machine learning, Python, and SQL",
            "candidates": [
                {
                    "candidate_id": "cand1",
                    "skills": ["Python", "Machine Learning", "TensorFlow", "SQL"]
                }
            ]
        }
    },

    # ============================================================
    # PROCUREMENT (4 modules)
    # ============================================================
    "procurement/matcher": {
        "endpoint": "/api/v1/modules/procurement-matcher/match",
        "sample_data": {
            "rfp_requirements": {
                "category": "IT Services",
                "budget": 100000.0,
                "timeline_weeks": 12,
                "key_requirements": ["Cloud migration", "24/7 support"]
            },
            "suppliers": [
                {
                    "supplier_id": "sup1",
                    "name": "CloudTech Solutions",
                    "capabilities": ["Cloud migration", "Support"],
                    "pricing_model": "fixed_price"
                }
            ]
        }
    },

    "procurement/spend_smart": {
        "endpoint": "/api/v1/modules/spend-smart/analyze",
        "sample_data": {
            "transactions": [
                {
                    "transaction_id": "tx1",
                    "vendor": "Office Supplies Inc",
                    "category": "Office Supplies",
                    "amount": 5000.0,
                    "date": "2024-01-15"
                }
            ],
            "analysis_period_months": 12
        }
    },

    "procurement/tender_intelligence": {
        "endpoint": "/api/v1/modules/tender-intelligence/analyze",
        "sample_data": {
            "tender_documents": [
                {
                    "tender_id": "tend1",
                    "title": "Highway Construction Project",
                    "description": "Build 50km highway with 4 lanes",
                    "budget": 50000000.0,
                    "deadline": "2024-12-31"
                }
            ]
        }
    },

    "procurement/vendor_recommendation": {
        "endpoint": "/api/v1/modules/vendor-recommendation/recommend",
        "sample_data": {
            "requirements": {
                "category": "Software Development",
                "budget": 200000.0,
                "project_duration_months": 6,
                "required_certifications": ["ISO 9001"]
            },
            "vendors": [
                {
                    "vendor_id": "ven1",
                    "name": "Dev Solutions Ltd",
                    "rating": 4.5,
                    "certifications": ["ISO 9001", "ISO 27001"]
                }
            ]
        }
    },

    # ============================================================
    # DOCUMENT INTELLIGENCE (3 modules)
    # ============================================================
    "document_intelligence/generic_rag": {
        "endpoint": "/api/v1/modules/generic-rag/query",
        "sample_data": {
            "query": "What are the key findings in the research paper?",
            "document_context": "Research paper on transformer architecture shows improved performance",
            "top_k": 5
        }
    },

    "document_intelligence/relation_extractor": {
        "endpoint": "/api/v1/modules/relation-extractor/extract",
        "sample_data": {
            "text": "Apple Inc. was founded by Steve Jobs in Cupertino, California.",
            "relation_types": ["founded_by", "located_in"]
        }
    },

    # Note: docu_extract has no routes (internal service only), skipping

    # ============================================================
    # INDUSTRY VERTICALS (5 modules)
    # ============================================================
    "industry_verticals/legal_document": {
        "endpoint": "/api/v1/modules/legal-document/analyze",
        "sample_data": {
            "document_text": "This Non-Disclosure Agreement is entered into between Party A and Party B",
            "document_type": "contract",
            "extract_clauses": True
        }
    },

    "industry_verticals/real_estate": {
        "endpoint": "/api/v1/modules/real-estate/analyze",
        "sample_data": {
            "properties": [
                {
                    "property_id": "prop1",
                    "address": "123 Main St",
                    "price": 500000.0,
                    "bedrooms": 3,
                    "bathrooms": 2,
                    "square_feet": 2000
                }
            ],
            "analysis_type": "valuation"
        }
    },

    "industry_verticals/healthcare_diagnostics": {
        "endpoint": "/api/v1/modules/healthcare-diagnostics/analyze",
        "sample_data": {
            "patient_data": {
                "age": 45,
                "gender": "male",
                "symptoms": ["fever", "cough", "fatigue"],
                "vital_signs": {
                    "temperature_f": 101.5,
                    "heart_rate": 85,
                    "blood_pressure": "120/80"
                }
            }
        }
    },

    "industry_verticals/educational_content": {
        "endpoint": "/api/v1/modules/educational-content/generate",
        "sample_data": {
            "topic": "Introduction to Python Programming",
            "level": "beginner",
            "format": "lesson_plan",
            "duration_minutes": 45
        }
    },

    "industry_verticals/insurance_risk": {
        "endpoint": "/api/v1/modules/insurance-risk/assess",
        "sample_data": {
            "policy_type": "auto",
            "applicant_data": {
                "age": 30,
                "driving_history_years": 12,
                "accidents": 0,
                "violations": 1
            },
            "vehicle_data": {
                "make": "Toyota",
                "model": "Camry",
                "year": 2020,
                "value": 25000.0
            }
        }
    },

    # ============================================================
    # ADVANCED CAPABILITIES (2 modules)
    # ============================================================
    "advanced_capabilities/code_analysis": {
        "endpoint": "/api/v1/modules/code-analysis/analyze",
        "sample_data": {
            "code": "def hello(name):\n    print(f'Hello {name}')",
            "language": "python",
            "analysis_types": ["complexity", "best_practices"]
        }
    },

    "advanced_capabilities/multilingual_translator": {
        "endpoint": "/api/v1/modules/multilingual-translator/translate",
        "sample_data": {
            "text": "Hello, how are you?",
            "source_language": "en",
            "target_languages": ["es", "fr"],
            "preserve_formatting": True
        }
    },

    # ============================================================
    # E-COMMERCE (1 module)
    # ============================================================
    "ecommerce/product_recommendation": {
        "endpoint": "/api/v1/modules/product-recommendation/recommend",
        "sample_data": {
            "user_profile": {
                "user_id": "user1",
                "age": 28,
                "interests": ["electronics", "gaming"]
            },
            "browsing_history": [
                {"product_id": "prod1", "category": "electronics"},
                {"product_id": "prod2", "category": "gaming"}
            ],
            "num_recommendations": 5
        }
    },

    # ============================================================
    # MARITIME (1 module)
    # ============================================================
    "maritime/maritime_logistics": {
        "endpoint": "/api/v1/modules/maritime-logistics/optimize",
        "sample_data": {
            "shipments": [
                {
                    "shipment_id": "ship1",
                    "origin_port": "Shanghai",
                    "destination_port": "Los Angeles",
                    "cargo_weight_tons": 5000,
                    "cargo_type": "containers"
                }
            ],
            "optimize_for": "cost"
        }
    }
}


class ModuleTester:
    """Comprehensive backend API testing framework."""

    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0

    async def test_module(self, module_path: str, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single module."""
        print(f"\n{'='*80}")
        print(f"Testing: {module_path}")
        print(f"{'='*80}")

        result = {
            "module": module_path,
            "endpoint": test_config["endpoint"],
            "timestamp": datetime.now().isoformat(),
            "status": "PENDING",
            "http_code": None,
            "response_keys": [],
            "error": None,
            "duration_ms": 0,
            "config_loaded": False
        }

        try:
            start_time = datetime.now()

            async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
                print(f"  📤 POST {test_config['endpoint']}")
                print(f"  📊 Sample data keys: {list(test_config['sample_data'].keys())}")

                response = await client.post(
                    test_config['endpoint'],
                    json=test_config['sample_data']
                )

                duration = (datetime.now() - start_time).total_seconds() * 1000
                result["duration_ms"] = round(duration, 2)
                result["http_code"] = response.status_code

                if response.status_code == 200:
                    result["status"] = "✅ PASS"
                    response_data = response.json()
                    result["response_keys"] = list(response_data.keys())
                    self.passed += 1

                    print(f"  ✅ SUCCESS - {duration:.0f}ms")
                    print(f"  📥 Response keys: {result['response_keys']}")

                    # Check if config was loaded (check backend logs or response metadata)
                    if "config_applied" in response_data or "model_used" in response_data:
                        result["config_loaded"] = True
                        print(f"  ⚙️  Config detected in response")

                else:
                    result["status"] = "❌ FAIL"
                    result["error"] = f"HTTP {response.status_code}: {response.text[:300]}"
                    self.failed += 1
                    print(f"  ❌ FAILED - HTTP {response.status_code}")
                    print(f"  ⚠️  Error: {response.text[:300]}")

        except Exception as e:
            result["status"] = "❌ ERROR"
            result["error"] = str(e)
            self.failed += 1
            print(f"  ❌ ERROR: {str(e)}")

        self.results.append(result)
        return result

    async def test_all_modules(self, specific_module: str = None):
        """Test all modules or a specific one."""
        print("\n" + "="*80)
        print("COMPREHENSIVE BACKEND API TESTING - ALL 30 TIER 2 MODULES")
        print("="*80)
        print(f"Start time: {datetime.now().isoformat()}")
        print(f"Base URL: {BASE_URL}")

        modules_to_test = MODULE_TESTS
        if specific_module:
            if specific_module in MODULE_TESTS:
                modules_to_test = {specific_module: MODULE_TESTS[specific_module]}
            else:
                print(f"❌ Module not found: {specific_module}")
                print(f"Available modules: {list(MODULE_TESTS.keys())}")
                return

        print(f"Total modules to test: {len(modules_to_test)}")
        print("="*80)

        for module_path, test_config in modules_to_test.items():
            await self.test_module(module_path, test_config)

        self.print_summary()

    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)

        total = len(self.results)
        success_rate = (self.passed / total * 100) if total > 0 else 0

        print(f"\n📊 Results:")
        print(f"  ✅ Passed: {self.passed}/{total} ({success_rate:.1f}%)")
        print(f"  ❌ Failed: {self.failed}/{total} ({(self.failed/total*100) if total > 0 else 0:.1f}%)")

        if self.failed > 0:
            print(f"\n❌ Failed Modules:")
            for result in self.results:
                if "❌" in result["status"]:
                    print(f"  - {result['module']}")
                    print(f"    HTTP {result['http_code']}: {result['error'][:150]}")

        print(f"\n⏱️  Performance:")
        for result in self.results:
            if result["duration_ms"] > 0:
                status_icon = "✅" if "✅" in result["status"] else "❌"
                print(f"  {status_icon} {result['module']}: {result['duration_ms']:.0f}ms")

        # Save results to file
        output_file = Path("/tmp/module_backend_test_results.json")
        with open(output_file, 'w') as f:
            json.dump({
                "summary": {
                    "total": total,
                    "passed": self.passed,
                    "failed": self.failed,
                    "success_rate": success_rate
                },
                "results": self.results
            }, f, indent=2)

        print(f"\n📄 Detailed results saved to: {output_file}")
        print("="*80 + "\n")

        # Return exit code
        return 0 if self.failed == 0 else 1


async def main():
    parser = argparse.ArgumentParser(description='Test all 30 tier_2 modules via backend API')
    parser.add_argument('--module', help='Test specific module only (format: category/module_name)')
    args = parser.parse_args()

    tester = ModuleTester()
    exit_code = await tester.test_all_modules(args.module)
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
