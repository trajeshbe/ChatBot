"""
Module Registry - Centralized mapping of modules to their code files.

This registry maps each Tier 2 and Tier 3 module to all files needed for standalone deployment:
- Backend service/routes/schemas
- Frontend components
- Tier 1 dependencies (RAG, LLM, etc.)
- Python packages
- NPM packages
- Sample data

Author: Claude Code
Date: 2026-01-04
Phase: Module-Specific Export Enhancement
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ModuleFiles:
    """Files and dependencies for a module."""

    # Backend Python files
    backend: List[str] = field(default_factory=list)

    # Frontend TypeScript/React files
    frontend: List[str] = field(default_factory=list)

    # Additional Tier 1 services this module depends on
    # (These will be auto-discovered but can be explicitly listed)
    tier1_dependencies: List[str] = field(default_factory=list)

    # Python package names (will be resolved to versions from requirements.txt)
    python_packages: List[str] = field(default_factory=list)

    # NPM package names (will be resolved to versions from package.json)
    npm_packages: List[str] = field(default_factory=list)

    # Sample data files for testing
    sample_data: List[str] = field(default_factory=list)

    # Module category (for organization)
    category: str = ""

    # Human-readable module name
    display_name: str = ""


# ============================================================================
# TIER 2 MODULE REGISTRY
# ============================================================================

TIER2_MODULES: Dict[str, ModuleFiles] = {

    # ========================================================================
    # DOCUMENT INTELLIGENCE (3 modules)
    # ========================================================================

    "generic-rag": ModuleFiles(
        category="document_intelligence",
        display_name="Generic RAG",
        backend=[
            "app/tier_2/document_intelligence/generic_rag_service.py",
            "app/tier_2/document_intelligence/generic_rag_routes.py",
            "app/tier_2/document_intelligence/generic_rag_schemas.py",
        ],
        frontend=[
            "src/components/tier2/document_intelligence/GenericRAGPanel.tsx",
        ],
        python_packages=["sentence-transformers", "faiss-cpu"],
        sample_data=[
            "sample_data/tier2_domain_verticals/document_intelligence/generic_rag_sample.txt",
        ]
    ),

    "relation-extractor": ModuleFiles(
        category="document_intelligence",
        display_name="Relation Extractor",
        backend=[
            "app/tier_2/document_intelligence/relation_extractor_service.py",
            "app/tier_2/document_intelligence/relation_extractor_routes.py",
            "app/tier_2/document_intelligence/relation_extractor_schemas.py",
        ],
        frontend=[
            "src/components/tier2/document_intelligence/RelationExtractorPanel.tsx",
        ],
        python_packages=["spacy"],
        sample_data=[]
    ),

    # ========================================================================
    # CONSTRUCTION (4 modules)
    # ========================================================================

    "construction": ModuleFiles(
        category="construction",
        display_name="Building Metrics",
        backend=[
            "app/tier_2/construction/building_metrics_service.py",
            "app/tier_2/construction/building_metrics_routes.py",
            "app/tier_2/construction/building_metrics_schemas.py",
        ],
        frontend=[
            "src/components/tier2/construction/BuildingMetricsPanel.tsx",
        ],
        python_packages=[],
        sample_data=[]
    ),

    "planning-classifier": ModuleFiles(
        category="construction",
        display_name="Planning Classifier",
        backend=[
            "app/tier_2/construction/planning_classifier_service.py",
            "app/tier_2/construction/planning_classifier_routes.py",
            "app/tier_2/construction/planning_classifier_schemas.py",
        ],
        frontend=[
            "src/components/tier2/construction/PlanningClassifierPanel.tsx",
        ],
        python_packages=["pillow"],
        sample_data=[
            "sample_data/tier2_domain_verticals/construction/planning_application_sample.txt",
            "sample_data/tier2_domain_verticals/construction/planning_entities_expected.json",
        ]
    ),

    "mine-scope": ModuleFiles(
        category="construction",
        display_name="Mine Scope Analysis",
        backend=[
            "app/tier_2/construction/mine_scope_service.py",
            "app/tier_2/construction/mine_scope_routes.py",
            "app/tier_2/construction/mine_scope_schemas.py",
        ],
        frontend=[
            "src/components/tier2/construction/MineScopePanel.tsx",
        ],
        python_packages=[],
        sample_data=[]
    ),

    "estimator-au": ModuleFiles(
        category="construction",
        display_name="AU Cost Estimator",
        backend=[
            "app/tier_2/construction/estimator_au_service.py",
            "app/tier_2/construction/estimator_au_routes.py",
            "app/tier_2/construction/estimator_au_schemas.py",
        ],
        frontend=[
            "src/components/tier2/construction/EstimatorAUPanel.tsx",
        ],
        python_packages=["pandas"],
        sample_data=[]
    ),

    # ========================================================================
    # PROCUREMENT (4 modules)
    # ========================================================================

    "matcher": ModuleFiles(
        category="procurement",
        display_name="PO-Invoice Matcher",
        backend=[
            "app/tier_2/procurement/matcher_service.py",
            "app/tier_2/procurement/matcher_routes.py",
            "app/tier_2/procurement/matcher_schemas.py",
        ],
        frontend=[
            "src/components/tier2/procurement/ProcurementMatcherPanel.tsx",
        ],
        python_packages=["pandas", "fuzzywuzzy", "python-Levenshtein"],
        sample_data=[
            "sample_data/tier2_domain_verticals/procurement_matcher/rfp_construction_materials.txt",
            "sample_data/tier2_domain_verticals/procurement_matcher/supplier_profiles.json",
        ]
    ),

    "vendor-recommendation": ModuleFiles(
        category="procurement",
        display_name="Vendor Recommendation",
        backend=[
            "app/tier_2/procurement/vendor_recommendation_service.py",
            "app/tier_2/procurement/vendor_recommendation_routes.py",
            "app/tier_2/procurement/vendor_recommendation_schemas.py",
        ],
        frontend=[
            "src/components/tier2/procurement/VendorRecommendationPanel.tsx",
        ],
        python_packages=["pandas", "scikit-learn"],
        sample_data=[]
    ),

    "tender-intelligence": ModuleFiles(
        category="procurement",
        display_name="Tender Intelligence",
        backend=[
            "app/tier_2/procurement/tender_intelligence_service.py",
            "app/tier_2/procurement/tender_intelligence_routes.py",
            "app/tier_2/procurement/tender_intelligence_schemas.py",
        ],
        frontend=[
            "src/components/tier2/procurement/TenderIntelligencePanel.tsx",
        ],
        python_packages=["pandas"],
        sample_data=[]
    ),

    "spend-smart": ModuleFiles(
        category="procurement",
        display_name="Spend Analytics",
        backend=[
            "app/tier_2/procurement/spend_smart_service.py",
            "app/tier_2/procurement/spend_smart_routes.py",
            "app/tier_2/procurement/spend_smart_schemas.py",
        ],
        frontend=[
            "src/components/tier2/procurement/SpendSmartPanel.tsx",
        ],
        python_packages=["pandas", "numpy"],
        sample_data=[]
    ),

    # ========================================================================
    # HR & TALENT (3 modules)
    # ========================================================================

    "talent-search": ModuleFiles(
        category="hr_talent",
        display_name="Talent Search",
        backend=[
            "app/tier_2/hr_talent/talent_search_service.py",
            "app/tier_2/hr_talent/talent_search_routes.py",
            "app/tier_2/hr_talent/talent_search_schemas.py",
        ],
        frontend=[
            "src/components/tier2/hr_talent/TalentSearchPanel.tsx",
        ],
        python_packages=["pandas"],
        sample_data=[
            "sample_data/tier2_domain_verticals/hr_talent/job_posting_sample.json",
            "sample_data/tier2_domain_verticals/hr_talent/candidate_resume_sample.txt",
        ]
    ),

    "taxonomy-skillmatch": ModuleFiles(
        category="hr_talent",
        display_name="Skill Taxonomy",
        backend=[
            "app/tier_2/hr_talent/taxonomy_skillmatch_service.py",
            "app/tier_2/hr_talent/taxonomy_skillmatch_routes.py",
            "app/tier_2/hr_talent/taxonomy_skillmatch_schemas.py",
        ],
        frontend=[
            "src/components/tier2/hr_talent/TaxonomySkillmatchPanel.tsx",
        ],
        python_packages=[],
        sample_data=[]
    ),

    "talent-pulse": ModuleFiles(
        category="hr_talent",
        display_name="Employee Engagement",
        backend=[
            "app/tier_2/hr_talent/talent_pulse_service.py",
            "app/tier_2/hr_talent/talent_pulse_routes.py",
            "app/tier_2/hr_talent/talent_pulse_schemas.py",
        ],
        frontend=[
            "src/components/tier2/hr_talent/TalentPulsePanel.tsx",
        ],
        python_packages=["textblob"],
        sample_data=[]
    ),

    # ========================================================================
    # AGRICULTURE (2 modules)
    # ========================================================================

    "agri-taxonomy": ModuleFiles(
        category="agriculture",
        display_name="Crop Taxonomy",
        backend=[
            "app/tier_2/agriculture/agri_taxonomy_service.py",
            "app/tier_2/agriculture/agri_taxonomy_routes.py",
            "app/tier_2/agriculture/agri_taxonomy_schemas.py",
        ],
        frontend=[
            "src/components/tier2/agriculture/AgriTaxonomyPanel.tsx",
        ],
        python_packages=[],
        sample_data=[]
    ),

    "agronomy-decision": ModuleFiles(
        category="agriculture",
        display_name="Agronomy Decisions",
        backend=[
            "app/tier_2/agriculture/agronomy_decision_service.py",
            "app/tier_2/agriculture/agronomy_decision_routes.py",
            "app/tier_2/agriculture/agronomy_decision_schemas.py",
        ],
        frontend=[
            "src/components/tier2/agriculture/AgronomyDecisionPanel.tsx",
        ],
        python_packages=[],
        sample_data=[]
    ),

    # ========================================================================
    # MARKETING (2 modules)
    # ========================================================================

    "sentiment-social": ModuleFiles(
        category="marketing",
        display_name="Social Sentiment",
        backend=[
            "app/tier_2/marketing/sentiment_social_service.py",
            "app/tier_2/marketing/sentiment_social_routes.py",
            "app/tier_2/marketing/sentiment_social_schemas.py",
        ],
        frontend=[
            "src/components/tier2/marketing/SentimentSocialPanel.tsx",
        ],
        python_packages=["textblob", "vaderSentiment"],
        sample_data=[]
    ),

    "campaign-optimizer": ModuleFiles(
        category="marketing",
        display_name="Campaign Optimizer",
        backend=[
            "app/tier_2/marketing/campaign_optimizer_service.py",
            "app/tier_2/marketing/campaign_optimizer_routes.py",
            "app/tier_2/marketing/campaign_optimizer_schemas.py",
        ],
        frontend=[
            "src/components/tier2/marketing/CampaignOptimizerPanel.tsx",
        ],
        python_packages=["pandas", "scikit-learn"],
        sample_data=[]
    ),

    # ========================================================================
    # E-COMMERCE (1 module)
    # ========================================================================

    "product-recommendation": ModuleFiles(
        category="ecommerce",
        display_name="Product Recommendations",
        backend=[
            "app/tier_2/ecommerce/product_recommendation_service.py",
            "app/tier_2/ecommerce/product_recommendation_routes.py",
            "app/tier_2/ecommerce/product_recommendation_schemas.py",
        ],
        frontend=[
            "src/components/tier2/ecommerce/ProductRecommendationPanel.tsx",
        ],
        python_packages=["pandas", "scikit-learn"],
        sample_data=[]
    ),

    # ========================================================================
    # MARITIME (1 module)
    # ========================================================================

    "maritime-logistics": ModuleFiles(
        category="maritime",
        display_name="Logistics Optimizer",
        backend=[
            "app/tier_2/maritime/maritime_logistics_service.py",
            "app/tier_2/maritime/maritime_logistics_routes.py",
            "app/tier_2/maritime/maritime_logistics_schemas.py",
        ],
        frontend=[
            "src/components/tier2/maritime/MaritimeReportPanel.tsx",
        ],
        python_packages=["pandas"],
        sample_data=[]
    ),

    # ========================================================================
    # ANALYTICS (4 modules)
    # ========================================================================

    "predictive-analytics": ModuleFiles(
        category="analytics",
        display_name="Predictive Analytics",
        backend=[
            "app/tier_2/analytics/predictive_analytics_service.py",
            "app/tier_2/analytics/predictive_analytics_routes.py",
            "app/tier_2/analytics/predictive_analytics_schemas.py",
        ],
        frontend=[
            "src/components/tier2/analytics/PredictiveAnalyticsPanel.tsx",
        ],
        python_packages=["pandas", "scikit-learn", "statsmodels"],
        sample_data=[]
    ),

    "customer-churn": ModuleFiles(
        category="analytics",
        display_name="Churn Predictor",
        backend=[
            "app/tier_2/analytics/customer_churn_service.py",
            "app/tier_2/analytics/customer_churn_routes.py",
            "app/tier_2/analytics/customer_churn_schemas.py",
        ],
        frontend=[
            "src/components/tier2/analytics/CustomerChurnPanel.tsx",
        ],
        python_packages=["pandas", "scikit-learn"],
        sample_data=[]
    ),

    "sales-performance": ModuleFiles(
        category="analytics",
        display_name="Sales Performance",
        backend=[
            "app/tier_2/analytics/sales_performance_service.py",
            "app/tier_2/analytics/sales_performance_routes.py",
            "app/tier_2/analytics/sales_performance_schemas.py",
        ],
        frontend=[
            "src/components/tier2/analytics/SalesPerformancePanel.tsx",
        ],
        python_packages=["pandas", "numpy"],
        sample_data=[]
    ),

    "financial-anomaly": ModuleFiles(
        category="analytics",
        display_name="Financial Anomaly",
        backend=[
            "app/tier_2/analytics/financial_anomaly_service.py",
            "app/tier_2/analytics/financial_anomaly_routes.py",
            "app/tier_2/analytics/financial_anomaly_schemas.py",
        ],
        frontend=[
            "src/components/tier2/analytics/FinancialAnomalyPanel.tsx",
        ],
        python_packages=["pandas", "numpy", "scikit-learn"],
        sample_data=[]
    ),

    # ========================================================================
    # INDUSTRY VERTICALS (5 modules)
    # ========================================================================

    "healthcare-diagnostics": ModuleFiles(
        category="industry_verticals",
        display_name="Healthcare Diagnostics",
        backend=[
            "app/tier_2/industry_verticals/healthcare_diagnostics_service.py",
            "app/tier_2/industry_verticals/healthcare_diagnostics_routes.py",
            "app/tier_2/industry_verticals/healthcare_diagnostics_schemas.py",
        ],
        frontend=[
            "src/components/tier2/industry_verticals/HealthcareDiagnosticsPanel.tsx",
        ],
        python_packages=[],
        sample_data=[]
    ),

    "legal-document": ModuleFiles(
        category="industry_verticals",
        display_name="Legal Document Analyzer",
        backend=[
            "app/tier_2/industry_verticals/legal_document_service.py",
            "app/tier_2/industry_verticals/legal_document_routes.py",
            "app/tier_2/industry_verticals/legal_document_schemas.py",
        ],
        frontend=[
            "src/components/tier2/industry_verticals/LegalDocumentPanel.tsx",
        ],
        python_packages=[],
        sample_data=[]
    ),

    "real-estate-valuation": ModuleFiles(
        category="industry_verticals",
        display_name="Real Estate Valuation",
        backend=[
            "app/tier_2/industry_verticals/real_estate_service.py",
            "app/tier_2/industry_verticals/real_estate_routes.py",
            "app/tier_2/industry_verticals/real_estate_schemas.py",
        ],
        frontend=[
            "src/components/tier2/industry_verticals/RealEstatePanel.tsx",
        ],
        python_packages=["pandas"],
        sample_data=[]
    ),

    "insurance-risk": ModuleFiles(
        category="industry_verticals",
        display_name="Insurance Risk Assessor",
        backend=[
            "app/tier_2/industry_verticals/insurance_risk_service.py",
            "app/tier_2/industry_verticals/insurance_risk_routes.py",
            "app/tier_2/industry_verticals/insurance_risk_schemas.py",
        ],
        frontend=[
            "src/components/tier2/industry_verticals/InsuranceRiskPanel.tsx",
        ],
        python_packages=["pandas"],
        sample_data=[]
    ),

    "educational-content": ModuleFiles(
        category="industry_verticals",
        display_name="Educational Content",
        backend=[
            "app/tier_2/industry_verticals/educational_content_service.py",
            "app/tier_2/industry_verticals/educational_content_routes.py",
            "app/tier_2/industry_verticals/educational_content_schemas.py",
        ],
        frontend=[
            "src/components/tier2/industry_verticals/EducationalContentPanel.tsx",
        ],
        python_packages=[],
        sample_data=[]
    ),

    # ========================================================================
    # ADVANCED CAPABILITIES (2 modules)
    # ========================================================================

    "multilingual-translator": ModuleFiles(
        category="advanced_capabilities",
        display_name="Multilingual Translator",
        backend=[
            "app/tier_2/advanced_capabilities/multilingual_translator_service.py",
            "app/tier_2/advanced_capabilities/multilingual_translator_routes.py",
            "app/tier_2/advanced_capabilities/multilingual_translator_schemas.py",
        ],
        frontend=[
            "src/components/tier2/advanced_capabilities/MultilingualTranslatorPanel.tsx",
        ],
        python_packages=[],
        sample_data=[]
    ),

    "code-analysis": ModuleFiles(
        category="advanced_capabilities",
        display_name="Code Analysis & Review",
        backend=[
            "app/tier_2/advanced_capabilities/code_analysis_service.py",
            "app/tier_2/advanced_capabilities/code_analysis_routes.py",
            "app/tier_2/advanced_capabilities/code_analysis_schemas.py",
        ],
        frontend=[
            "src/components/tier2/advanced_capabilities/CodeAnalysisPanel.tsx",
        ],
        python_packages=["ast", "pylint"],
        sample_data=[]
    ),
}


# ============================================================================
# TIER 3 CUSTOMER POC MODULES
# ============================================================================

TIER3_MODULES: Dict[str, ModuleFiles] = {
    "british_council": ModuleFiles(
        category="customer_solutions",
        display_name="British Council Course Recommender",
        backend=[
            "app/tier_3/customer_solutions/british_council_service.py",
            "app/api/routes/british_council_routes.py",
            "app/schemas/british_council_schemas.py",
            "app/services/british_council/course_recommender.py",
            "app/services/british_council/profile_analyzer.py",
        ],
        frontend=[
            "src/components/BritishCouncilRecommender.tsx",
        ],
        python_packages=[],
        sample_data=[
            "sample_data/tier3_customer_pocs/british_council/course_catalog_sample.json",
            "sample_data/tier3_customer_pocs/british_council/learner_profile_sample.json",
        ]
    ),

    "cru": ModuleFiles(
        category="customer_solutions",
        display_name="CRU Mining Intelligence",
        backend=[
            "app/tier_3/customer_solutions/cru_service.py",
            "app/api/routes/cru_routes.py",
            "app/schemas/cru_schemas.py",
            "app/services/cru/cru_query_service.py",
            "app/services/cru/multi_pipeline_router.py",
        ],
        frontend=[
            "src/components/CRUMiningIntelligence.tsx",
        ],
        python_packages=[],
        sample_data=[
            "sample_data/tier3_customer_pocs/cru/mining_market_report_sample.txt",
            "sample_data/tier3_customer_pocs/cru/expected_extraction_fields.json",
        ]
    ),

    "grant_thornton": ModuleFiles(
        category="customer_solutions",
        display_name="Grant Thornton Financial Analysis",
        backend=[
            "app/tier_3/customer_solutions/gt_motive_service.py",
            "app/api/routes/grant_thornton_routes.py",
            "app/schemas/grant_thornton_schemas.py",
            "app/services/grant_thornton/agent_service.py",
            "app/services/grant_thornton/calculation_engine.py",
            "app/services/grant_thornton/embedding_service.py",
            "app/services/grant_thornton/excel_exporter.py",
            "app/services/grant_thornton/extraction_pipeline.py",
            "app/services/grant_thornton/pdf_parser.py",
            "app/services/grant_thornton/retrieval_service.py",
            "app/services/grant_thornton/vector_store.py",
            "app/services/grant_thornton/config.py",
        ],
        frontend=[
            "src/components/GrantThorntonExtraction.tsx",
        ],
        python_packages=["openpyxl", "pandas"],
        sample_data=[
            "sample_data/tier3_customer_pocs/grant_thornton/credit_analysis_benchmarks.json",
        ]
    ),

    "solera": ModuleFiles(
        category="customer_solutions",
        display_name="Solera Claims Processing",
        backend=[
            "app/tier_3/customer_solutions/solera_service.py",
        ],
        frontend=[
            "src/components/SoleraClaimsProcessing.tsx",
        ],
        python_packages=["pillow"],
        sample_data=[]
    ),

    "construction_monitor": ModuleFiles(
        category="customer_solutions",
        display_name="Construction Monitor",
        backend=[
            "app/tier_3/customer_solutions/construction_monitor_service.py",
        ],
        frontend=[
            "src/components/ConstructionExtraction.tsx",
        ],
        python_packages=[],
        sample_data=[
            "sample_data/tier3_customer_pocs/construction_monitor/planning_application_sample.txt",
            "sample_data/tier3_customer_pocs/construction_monitor/planning_entities_expected.json",
        ]
    ),
}


# Combined registry
ALL_MODULES = {**TIER2_MODULES, **TIER3_MODULES}


def get_module_files(module_name: str) -> Optional[ModuleFiles]:
    """
    Get file mappings for a module.

    Args:
        module_name: Module identifier (e.g., "matcher", "british_council")

    Returns:
        ModuleFiles object or None if module not found
    """
    return ALL_MODULES.get(module_name)


def get_module_category(module_name: str) -> Optional[str]:
    """Get category for a module."""
    files = get_module_files(module_name)
    return files.category if files else None


def is_tier2_module(module_name: str) -> bool:
    """Check if module is Tier 2."""
    return module_name in TIER2_MODULES


def is_tier3_module(module_name: str) -> bool:
    """Check if module is Tier 3."""
    return module_name in TIER3_MODULES


def list_all_modules() -> List[str]:
    """Get list of all registered module names."""
    return list(ALL_MODULES.keys())


def get_modules_by_category(category: str) -> List[str]:
    """Get all modules in a category."""
    return [
        name for name, files in ALL_MODULES.items()
        if files.category == category
    ]
