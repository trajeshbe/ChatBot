#!/usr/bin/env python3
"""
Automated script to add FileUpload component to all tier2 domain vertical panels.

This script systematically updates all panel components to include:
1. FileUpload import
2. FileUpload section in the UI
3. Appropriate metadata (company, usecase) for each vertical

Usage:
    python3 scripts/add_fileupload_to_panels.py
"""

import re
from pathlib import Path

# Mapping of panel files to their metadata
PANEL_METADATA = {
    # HR/Talent
    "tier2/hr_talent/TalentSearchPanel.tsx": {
        "company": "hr_talent",
        "usecase": "talent_search",
        "title": "📄 Upload Resumes & Job Descriptions",
        "description": "Upload resumes, CVs, job descriptions, or candidate profiles for intelligent matching."
    },
    "tier2/hr_talent/TalentPulsePanel.tsx": {
        "company": "hr_talent",
        "usecase": "talent_pulse",
        "title": "📊 Upload HR Data",
        "description": "Upload employee surveys, performance reviews, or engagement data for sentiment analysis."
    },
    "tier2/hr_talent/TaxonomySkillmatchPanel.tsx": {
        "company": "hr_talent",
        "usecase": "skill_matching",
        "title": "🎯 Upload Skill Taxonomies",
        "description": "Upload skill taxonomies, competency frameworks, or job requirement documents."
    },

    # Procurement
    "tier2/procurement/ProcurementMatcherPanel.tsx": {
        "company": "procurement",
        "usecase": "rfp_matching",
        "title": "📋 Upload RFP Documents",
        "description": "Upload RFPs, tenders, supplier profiles, or procurement specifications."
    },
    "tier2/procurement/TenderIntelligencePanel.tsx": {
        "company": "procurement",
        "usecase": "tender_analysis",
        "title": "🔍 Upload Tender Documents",
        "description": "Upload tender documents, bid submissions, or contract specifications."
    },
    "tier2/procurement/VendorRecommendationPanel.tsx": {
        "company": "procurement",
        "usecase": "vendor_matching",
        "title": "🏢 Upload Vendor Profiles",
        "description": "Upload vendor profiles, capability statements, or supplier catalogs."
    },
    "tier2/procurement/SpendSmartPanel.tsx": {
        "company": "procurement",
        "usecase": "spend_analysis",
        "title": "💰 Upload Spend Data",
        "description": "Upload purchase orders, invoices, or spend analytics reports."
    },

    # Document Intelligence
    "tier2/document_intelligence/GenericRAGPanel.tsx": {
        "company": "document_intelligence",
        "usecase": "generic_rag",
        "title": "📚 Upload Documents",
        "description": "Upload any documents for intelligent search and retrieval."
    },
    "tier2/document_intelligence/RelationExtractorPanel.tsx": {
        "company": "document_intelligence",
        "usecase": "relation_extraction",
        "title": "🔗 Upload Documents for Relation Extraction",
        "description": "Upload documents to extract entities and relationships."
    },

    # Industry Verticals
    "tier2/industry_verticals/LegalDocumentPanel.tsx": {
        "company": "legal",
        "usecase": "document_analysis",
        "title": "⚖️ Upload Legal Documents",
        "description": "Upload contracts, agreements, legal briefs, or case documents."
    },
    "tier2/industry_verticals/RealEstatePanel.tsx": {
        "company": "real_estate",
        "usecase": "property_analysis",
        "title": "🏠 Upload Property Documents",
        "description": "Upload property listings, inspection reports, or market analyses."
    },
    "tier2/industry_verticals/HealthcareDiagnosticsPanel.tsx": {
        "company": "healthcare",
        "usecase": "diagnostics",
        "title": "🏥 Upload Medical Documents",
        "description": "Upload medical records, lab results, or clinical guidelines."
    },
    "tier2/industry_verticals/InsuranceRiskPanel.tsx": {
        "company": "insurance",
        "usecase": "risk_assessment",
        "title": "🛡️ Upload Insurance Documents",
        "description": "Upload policy documents, claims, or risk assessment reports."
    },
    "tier2/industry_verticals/EducationalContentPanel.tsx": {
        "company": "education",
        "usecase": "content_analysis",
        "title": "🎓 Upload Educational Materials",
        "description": "Upload course materials, textbooks, or learning resources."
    },

    # Analytics
    "tier2/analytics/CustomerChurnPanel.tsx": {
        "company": "analytics",
        "usecase": "churn_prediction",
        "title": "📊 Upload Customer Data",
        "description": "Upload customer records, usage data, or interaction logs."
    },
    "tier2/analytics/FinancialAnomalyPanel.tsx": {
        "company": "analytics",
        "usecase": "anomaly_detection",
        "title": "💹 Upload Financial Data",
        "description": "Upload transaction logs, financial statements, or audit reports."
    },
    "tier2/analytics/PredictiveAnalyticsPanel.tsx": {
        "company": "analytics",
        "usecase": "predictive_modeling",
        "title": "🔮 Upload Historical Data",
        "description": "Upload historical datasets for predictive analysis."
    },
    "tier2/analytics/SalesPerformancePanel.tsx": {
        "company": "analytics",
        "usecase": "sales_analysis",
        "title": "💼 Upload Sales Data",
        "description": "Upload sales records, CRM exports, or performance reports."
    },

    # Construction
    "tier2/construction/EstimatorAUPanel.tsx": {
        "company": "construction",
        "usecase": "cost_estimation",
        "title": "🏗️ Upload Construction Documents",
        "description": "Upload building plans, specifications, or cost estimates."
    },
    "tier2/construction/PlanningClassifierPanel.tsx": {
        "company": "construction",
        "usecase": "planning_classification",
        "title": "📐 Upload Planning Applications",
        "description": "Upload planning applications, permits, or regulatory documents."
    },
    "tier2/construction/MineScopePanel.tsx": {
        "company": "construction",
        "usecase": "mining_scope",
        "title": "⛏️ Upload Mining Documents",
        "description": "Upload mine plans, geological surveys, or scope documents."
    },
    "tier2/construction/BuildingMetricsPanel.tsx": {
        "company": "construction",
        "usecase": "building_metrics",
        "title": "📏 Upload Building Data",
        "description": "Upload building metrics, performance data, or compliance reports."
    },

    # Marketing
    "tier2/marketing/CampaignOptimizerPanel.tsx": {
        "company": "marketing",
        "usecase": "campaign_optimization",
        "title": "📢 Upload Campaign Data",
        "description": "Upload campaign reports, performance metrics, or marketing materials."
    },
    "tier2/marketing/SentimentSocialPanel.tsx": {
        "company": "marketing",
        "usecase": "sentiment_analysis",
        "title": "💬 Upload Social Media Data",
        "description": "Upload social media posts, reviews, or customer feedback."
    },

    # E-commerce
    "tier2/ecommerce/ProductRecommendationPanel.tsx": {
        "company": "ecommerce",
        "usecase": "product_recommendations",
        "title": "🛒 Upload Product Catalogs",
        "description": "Upload product catalogs, user behavior data, or purchase histories."
    },

    # Maritime
    "tier2/maritime/MaritimeReportPanel.tsx": {
        "company": "maritime",
        "usecase": "maritime_logistics",
        "title": "🚢 Upload Maritime Documents",
        "description": "Upload shipping manifests, port reports, or logistics data."
    },

    # Agriculture
    "tier2/agriculture/AgriTaxonomyPanel.tsx": {
        "company": "agriculture",
        "usecase": "taxonomy_classification",
        "title": "🌾 Upload Agricultural Documents",
        "description": "Upload crop data, taxonomy documents, or agricultural reports."
    },
    "tier2/agriculture/AgronomyDecisionPanel.tsx": {
        "company": "agriculture",
        "usecase": "agronomy_decisions",
        "title": "🌱 Upload Agronomy Data",
        "description": "Upload soil reports, weather data, or crop management documents."
    },

    # Advanced Capabilities
    "tier2/advanced_capabilities/CodeAnalysisPanel.tsx": {
        "company": "advanced",
        "usecase": "code_analysis",
        "title": "💻 Upload Code Files",
        "description": "Upload source code files, documentation, or code review reports."
    },
    "tier2/advanced_capabilities/MultilingualTranslatorPanel.tsx": {
        "company": "advanced",
        "usecase": "translation",
        "title": "🌐 Upload Documents for Translation",
        "description": "Upload documents in any language for translation and analysis."
    },
}


def add_fileupload_to_panel(panel_path: Path, metadata: dict):
    """Add FileUpload component to a panel file."""

    if not panel_path.exists():
        print(f"❌ File not found: {panel_path}")
        return False

    content = panel_path.read_text()

    # Check if FileUpload is already imported
    if "import FileUpload from '../FileUpload'" in content or "import FileUpload from '../../FileUpload'" in content:
        print(f"✓ FileUpload already imported in {panel_path.name}")
        return False

    # Determine the correct import path (../ for one level up, ../../ for two levels up)
    levels_up = panel_path.relative_to(Path("frontend/src/components")).parts.count(".") + 1
    import_path = "../" * levels_up + "FileUpload"

    # Add import at the top (after other imports)
    import_pattern = r"(import.*from.*;\n)(\nexport|export)"

    import_addition = f"import FileUpload from '{import_path}'\n"

    # Check if we can find the right place to add import
    if re.search(import_pattern, content):
        content = re.sub(import_pattern, r"\1" + import_addition + r"\2", content, count=1)
    else:
        # Fallback: add after last import
        last_import_match = list(re.finditer(r"import.*from.*;\n", content))
        if last_import_match:
            pos = last_import_match[-1].end()
            content = content[:pos] + "\n" + import_addition + content[pos:]

    # Add FileUpload section in the return statement
    # Look for common patterns where we can insert the upload section

    # Pattern 1: Find a container div near the top of the return
    upload_section = f"""
        {{/* Document Upload Section */}}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <h3 className="text-lg font-semibold text-slate-800 mb-2">
            {metadata['title']}
          </h3>
          <p className="text-sm text-slate-600 mb-4">
            {metadata['description']}
          </p>
          <FileUpload
            hideProjectSelector={{true}}
            compact={{true}}
            metadata={{{{
              company: '{metadata['company']}',
              usecase: '{metadata['usecase']}'
            }}}}
          />
        </div>

"""

    # Try to find a good insertion point (after header, before main content)
    # Look for patterns like: </div>\n\n        {/* Main content or similar */}
    insertion_patterns = [
        (r"(</div>\s*}\s*)\n\s*(        {/\* (?:Main|Query|Input|Search))", r"\1" + upload_section + r"\2"),
        (r"(</div>\s*}\s*)\n\s*(        <div className=\"bg-white)", r"\1" + upload_section + r"\2"),
    ]

    inserted = False
    for pattern, replacement in insertion_patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content, count=1)
            inserted = True
            break

    if not inserted:
        print(f"⚠️  Could not find insertion point in {panel_path.name} - manual edit needed")
        return False

    panel_path.write_text(content)
    print(f"✅ Added FileUpload to {panel_path.name}")
    return True


def main():
    """Main execution function."""
    base_path = Path("/mnt/c/AIML/ClaudeCode/chatbot/ChatBot/frontend/src/components")

    print("🚀 Adding FileUpload to all tier2 domain vertical panels...\n")

    success_count = 0
    skip_count = 0
    fail_count = 0

    for panel_file, metadata in PANEL_METADATA.items():
        panel_path = base_path / panel_file
        result = add_fileupload_to_panel(panel_path, metadata)

        if result:
            success_count += 1
        elif result is False:
            skip_count += 1
        else:
            fail_count += 1

    print(f"\n📊 Summary:")
    print(f"   ✅ Successfully updated: {success_count}")
    print(f"   ⏭️  Skipped (already has FileUpload): {skip_count}")
    print(f"   ❌ Failed (manual edit needed): {fail_count}")
    print(f"\n🎯 Total panels processed: {len(PANEL_METADATA)}")


if __name__ == "__main__":
    main()
