# Sample Data for Use Case Testing

This directory contains comprehensive sample data for testing the functionality of each documented module/use case in the Merit AIML platform.

## Directory Structure

```
sample_data/
├── tier3_customer_pocs/           # Tier 3: Customer POC modules
│   ├── british_council/           # Profile matching & course recommendation
│   ├── construction_monitor/      # Planning application NER/REL
│   ├── cru/                       # Mining market intelligence extraction
│   ├── grant_thornton/            # Financial ratio analysis
│   ├── gt_motive/                 # Vehicle damage assessment (vision)
│   └── solera/                    # Insurance claim processing (OCR + vision)
│
└── tier2_domain_verticals/        # Tier 2: Domain vertical modules
    ├── procurement_matcher/       # RFP-supplier matching with NER
    ├── tender_intelligence/       # Tender opportunity extraction
    ├── credit_profile_analyzer/   # Credit risk assessment
    ├── talent_search/             # Resume-job matching
    ├── email_campaign_analyzer/   # Email campaign intelligence
    ├── mine_scope/                # Mining report analysis
    ├── maritime_report/           # Maritime incident reporting
    ├── planning_classifier/       # Planning document classification
    ├── agri_taxonomy/             # Agricultural product taxonomy
    ├── agronomy_support/          # Crop disease diagnosis
    ├── bot_detect/                # Bot traffic detection
    ├── email_bounce/              # Email bounce intelligence
    ├── fashion_tagging/           # Fashion image tagging
    └── docu_extract/              # Document intelligence extraction
```

## Sample Data by Module

### Tier 3 Customer POCs

#### 1. British Council (Profile Matching)
**Files:**
- `learner_profile_sample.json` - Sample learner profiles with preferences, goals, budget
- `course_catalog_sample.json` - Course offerings with requirements, schedules, pricing

**Expected Functionality:**
- Match learner profiles to suitable courses based on:
  - English proficiency level
  - Learning goals and interests
  - Budget and schedule availability
  - Preferred study mode (online/hybrid/in-person)
- Generate personalized course recommendations with match scores
- Calculate ROI and success probability

**Current Implementation Gap:** 95% missing
- No profile matching algorithm
- No multi-criteria scoring system
- No recommendation engine

---

#### 2. Construction Monitor (Planning Application NER/REL)
**Files:**
- `planning_application_sample.txt` - Planning notice with entities and relationships
- `planning_entities_expected.json` - Ground truth for NER/REL extraction

**Expected Functionality:**
- Named Entity Recognition (NER) for:
  - ORGANIZATION (developers, councils, consultants)
  - LOCATION (project sites, addresses)
  - DATE (application dates, decision dates)
  - PERSON (planning officers, agents)
  - QUANTITY (units, dimensions, capacities)
- Relationship Extraction (REL):
  - APPLICANT_FOR (company → application)
  - PLANNING_OFFICER_FOR (officer → application)
  - LOCATION_OF (site → development)
- Timeline extraction and visualization
- Stakeholder network mapping

**Current Implementation Gap:** 100% missing
- No NER/REL models deployed
- No entity extraction pipeline
- No relationship mapping

---

#### 3. CRU (Mining Market Intelligence)
**Files:**
- `mining_market_report_sample.txt` - Comprehensive copper market analysis report
- `expected_extraction_fields.json` - Structured data extraction schema

**Expected Functionality:**
- Extract structured data from unstructured reports:
  - Price data (current, forecasts, ranges)
  - Production data by country and operation
  - Demand analysis by region and sector
  - Inventory levels across exchanges
  - Cost analysis (C1 costs, margins)
  - Market outlook and recommendations
- Time-series data extraction for charting
- Multi-table extraction (production, demand, inventory)
- Sentiment analysis on market outlook

**Current Implementation Gap:** 98% missing
- No specialized extraction templates
- No financial entity recognition
- No multi-table extraction
- No time-series parsing

---

#### 4. Grant Thornton (Credit Profile Analyzer)
**Files:**
- `company_financial_ratios.csv` - 15 companies with 20+ financial ratios
- `credit_analysis_benchmarks.json` - Industry benchmarks and rating criteria

**Expected Functionality:**
- Financial ratio analysis:
  - Liquidity ratios (current, quick)
  - Leverage ratios (debt-to-equity, interest coverage)
  - Profitability ratios (margins, ROE, ROA)
  - Efficiency ratios (turnover metrics)
  - Valuation ratios (P/E, P/B)
- Industry benchmark comparison
- Altman Z-score calculation and interpretation
- Credit rating assignment (AAA to CCC)
- Peer group analysis
- Trend analysis (if multi-year data available)
- Risk assessment and recommendations

**Current Implementation Gap:** 98% missing
- No financial calculation engine
- No benchmark comparison logic
- No credit scoring algorithm
- No industry-specific analysis

---

### Tier 2 Domain Verticals

#### 5. Procurement Matcher (RFP-Supplier Matching)
**Files:**
- `rfp_construction_materials.txt` - Detailed RFP for £4.5-5.2M construction materials
- `supplier_profiles.json` - 4 supplier profiles with capabilities, certifications, pricing

**Expected Functionality:**
- RFP requirement extraction:
  - Material requirements (quantities, specifications)
  - Technical requirements (certifications, standards)
  - Delivery requirements (schedule, logistics)
  - Sustainability requirements (recycled content, carbon footprint)
  - Evaluation criteria and weights
- Supplier capability matching:
  - Product category alignment
  - Capacity vs. requirement comparison
  - Geographic proximity calculation
  - Certification compliance checking
  - Sustainability score matching
- Match scoring with explanation:
  - Price competitiveness (40%)
  - Technical capability (30%)
  - Delivery & logistics (15%)
  - Sustainability (10%)
  - Experience (5%)
- Generate shortlist with rankings
- Identify gaps and risks

**Current Implementation Gap:** 95% missing
- No requirement extraction templates
- No capability matching algorithm
- No weighted scoring system
- No gap analysis

---

## Testing Strategy

### Phase 1: Document Upload & Processing
Test that the platform can:
1. ✅ Upload documents (PDF, TXT, JSON, CSV)
2. ✅ Extract text from documents
3. ✅ Chunk documents for vector storage
4. ✅ Generate embeddings
5. ✅ Store in vector database

**Status:** Currently functional for generic RAG

### Phase 2: Specialized Extraction (MISSING)
Test module-specific extraction:
1. ❌ NER/REL for Construction Monitor
2. ❌ Structured field extraction for CRU
3. ❌ Financial ratio parsing for Grant Thornton
4. ❌ Profile attribute extraction for British Council
5. ❌ RFP requirement extraction for Procurement Matcher

**Status:** Not implemented - requires custom extraction pipelines

### Phase 3: Analysis & Matching (MISSING)
Test business logic:
1. ❌ Profile-to-course matching (British Council)
2. ❌ Supplier-to-RFP matching (Procurement Matcher)
3. ❌ Credit rating calculation (Grant Thornton)
4. ❌ Entity relationship mapping (Construction Monitor)
5. ❌ Time-series data extraction (CRU)

**Status:** Not implemented - requires specialized algorithms

### Phase 4: UI/UX Specialized Workflows (MISSING)
Test module-specific UIs:
1. ❌ Multi-tab interfaces (4-5 tabs per module)
2. ❌ Data tables with sorting/filtering
3. ❌ Charts and visualizations
4. ❌ Match score displays with explanations
5. ❌ Workflow state management

**Status:** Not implemented - generic chat interface only

---

## How to Use This Sample Data

### Option 1: Test Generic RAG (Currently Works)
```bash
# Upload sample documents via UI
# Ask generic questions like:
# - "What is the total contract value for the construction materials RFP?"
# - "Which supplier is located closest to Reading?"
# - "What is TechGlobal Inc's current ratio?"
```

**Expected Result:** Generic text-based answers from RAG pipeline

### Option 2: Test Specialized Functionality (Requires Implementation)
```python
# Example: Test Construction Monitor NER/REL
from app.services.ner_service import NERService
from app.services.rel_service import RELService

ner_service = NERService()
rel_service = RELService()

with open('sample_data/tier3_customer_pocs/construction_monitor/planning_application_sample.txt') as f:
    text = f.read()

# Extract entities
entities = ner_service.extract(text)
# Expected: ORGANIZATION, LOCATION, DATE, PERSON, QUANTITY entities

# Extract relationships
relationships = rel_service.extract(text, entities)
# Expected: APPLICANT_FOR, PLANNING_OFFICER_FOR, LOCATION_OF relationships

# Compare with ground truth
with open('sample_data/tier3_customer_pocs/construction_monitor/planning_entities_expected.json') as f:
    expected = json.load(f)

# Calculate precision, recall, F1
evaluate_ner(entities, expected['expected_entities'])
evaluate_rel(relationships, expected['expected_relationships'])
```

**Current Status:** Services not implemented

---

## Test Scripts

Test scripts are located in `/scripts/testing/` directory:

- `test_construction_monitor.py` - Test NER/REL extraction
- `test_british_council_matching.py` - Test profile-course matching
- `test_cru_extraction.py` - Test structured data extraction
- `test_grant_thornton_analysis.py` - Test financial ratio analysis
- `test_procurement_matcher.py` - Test RFP-supplier matching

Run all tests:
```bash
cd /mnt/c/AIML/ClaudeCode/chatbot/ChatBot
python scripts/testing/run_all_use_case_tests.py
```

---

## Expected Outputs

### Construction Monitor
```json
{
  "entities": {
    "organizations": ["Barrat Homes Ltd", "Westminster City Council", "Smith Planning Consultants"],
    "locations": ["Plot 45-48, Riverside Development, Thames Embankment, London"],
    "dates": ["15 January 2024", "1 March 2024", "15 March 2024"],
    "persons": ["Sarah Johnson"],
    "quantities": ["150 residential units", "2.5 hectares", "12 storeys"]
  },
  "relationships": [
    {"head": "Barrat Homes Ltd", "relation": "APPLICANT_FOR", "tail": "2024/0245/FUL"},
    {"head": "Sarah Johnson", "relation": "PLANNING_OFFICER_FOR", "tail": "2024/0245/FUL"}
  ]
}
```

### British Council Matching
```json
{
  "learner_id": "BC2024001",
  "recommended_courses": [
    {
      "course_id": "ACAD_ENG_PREP_2024",
      "match_score": 0.92,
      "reasons": [
        "Level match: B1 Intermediate → B1-B2 required",
        "Goal alignment: Academic preparation",
        "Budget fit: £950 within £500-£1000 range",
        "Schedule match: Online, evening availability"
      ]
    }
  ]
}
```

### Grant Thornton Credit Rating
```json
{
  "company": "TechGlobal Inc",
  "credit_rating": "AA",
  "z_score": 3.85,
  "risk_category": "Safe Zone",
  "key_strengths": [
    "Strong liquidity (Current Ratio: 2.45)",
    "Low leverage (Debt-to-Equity: 0.32)",
    "Excellent interest coverage (12.5x)"
  ],
  "concerns": [],
  "recommendation": "Low credit risk, approve for lending"
}
```

---

## Implementation Priority

Based on documentation analysis and business value:

### P0 (Critical - 6 modules)
1. **Construction Monitor** - NER/REL for planning applications
2. **Procurement Matcher** - RFP-supplier matching
3. **British Council** - Profile-course recommendation
4. **Credit Profile Analyzer** - Financial ratio analysis
5. **CRU** - Mining market intelligence extraction
6. **Grant Thornton** - Credit risk assessment

### P1 (High Value - 8 modules)
7. Tender Intelligence
8. Talent Search (Resume matching)
9. Email Campaign Analyzer
10. Mine Scope
11. Maritime Report Generation
12. Planning Classifier
13. Document Intelligence (DocuExtract)
14. Fashion Tagging

### P2 (Specialized - remaining modules)
15. Agri Taxonomy
16. Agronomy Decision Support
17. Bot Detect Analyzer
18. Email Bounce Intelligence
19. GT Motive (Vehicle damage - requires vision AI)
20. Solera (Insurance claims - requires OCR + vision)

---

## Architecture Recommendations

To support these specialized use cases, the platform needs:

### 1. Plugin Architecture
```python
# Each module as a plugin
plugins/
├── construction_monitor/
│   ├── ner_model.py
│   ├── rel_model.py
│   ├── extraction_pipeline.py
│   └── ui_components.tsx
├── british_council/
│   ├── matching_algorithm.py
│   ├── scoring_engine.py
│   └── recommendation_ui.tsx
└── ...
```

### 2. Specialized Model Registry
```yaml
models:
  ner:
    - name: "en_core_web_trf"
      provider: "spacy"
      entities: [ORG, PERSON, GPE, DATE, QUANTITY]
    - name: "construction_ner_v1"
      provider: "custom_finetuned"
      entities: [DEVELOPER, PLANNING_OFFICER, SITE_ADDRESS, APPLICATION_DATE]

  financial:
    - name: "finbert"
      provider: "huggingface"
      task: "financial_sentiment"

  matching:
    - name: "sentence-transformers/all-mpnet-base-v2"
      provider: "sentence_transformers"
      task: "semantic_similarity"
```

### 3. Workflow Engine
```python
# LangGraph workflow definitions
workflows/
├── construction_monitor_workflow.py
├── british_council_matching_workflow.py
├── procurement_matching_workflow.py
└── credit_analysis_workflow.py
```

### 4. Specialized UI Components
```typescript
// Module-specific React components
frontend/src/modules/
├── ConstructionMonitor/
│   ├── EntityViewer.tsx
│   ├── RelationshipGraph.tsx
│   └── TimelineView.tsx
├── BritishCouncil/
│   ├── ProfileForm.tsx
│   ├── MatchResults.tsx
│   └── CourseComparison.tsx
└── ...
```

---

## Next Steps

1. **Implement Test Scripts:** Create automated tests for each module using this sample data
2. **Build Extraction Pipelines:** Start with Construction Monitor NER/REL as proof of concept
3. **Develop Matching Algorithms:** Implement British Council and Procurement Matcher scoring
4. **Create Specialized UIs:** Design and implement module-specific interfaces
5. **Deploy Specialized Models:** Fine-tune NER, REL, and matching models
6. **Integrate Workflows:** Connect specialized pipelines to LangGraph workflows

---

## Contact

For questions about sample data or testing:
- Technical Lead: [Your Name]
- Documentation: See `/merit/merit_aiml_docs/` for original module specifications
- Issue Tracker: GitHub Issues

**Last Updated:** January 1, 2026
**Version:** 1.0.0
