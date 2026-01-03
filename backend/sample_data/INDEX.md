# Sample Data & Testing - Complete Index

**Last Updated:** January 1, 2026
**Purpose:** Central navigation for all sample data, testing guides, and documentation

---

## 🚀 Quick Start (5 Minutes)

**Start here if you want to immediately test the platform:**

📄 **[QUICK_START_TESTING.md](QUICK_START_TESTING.md)**
- One-file upload test
- One-question validation
- Pass/fail criteria
- 5-minute time commitment

---

## 📚 Core Documentation

### 1. Sample Data Overview
📄 **[README.md](README.md)** (459 lines)
- Complete sample data catalog
- Testing strategy (Phase 1-4)
- Expected functionality by module
- Implementation priorities (P0, P1, P2)
- Architecture recommendations

### 2. Executive Summary
📄 **[/SAMPLE_DATA_AND_TESTING_SUMMARY.md](../SAMPLE_DATA_AND_TESTING_SUMMARY.md)** (520 lines)
- Deliverables summary
- Key findings (95% implementation gap)
- Detailed test coverage
- Implementation roadmap (4 phases)
- Success metrics

---

## 🧪 Testing Guides

### Manual Testing
📄 **[/scripts/testing/use_cases/manual_test_guide.md](../scripts/testing/use_cases/manual_test_guide.md)**
- 15 test cases across 5 modules
- Step-by-step UI testing instructions
- Expected results for each test
- Test results template
- Troubleshooting guide

### Automated Testing
📄 **[/scripts/testing/use_cases/test_generic_rag_with_sample_data.py](../scripts/testing/use_cases/test_generic_rag_with_sample_data.py)** (525 lines)
- Automated upload and query testing
- Gap analysis reporting
- 11 test cases with assertions
- Expected vs. actual output comparison

**Note:** Automated tests currently have upload issues due to backend file_type detection. Use manual testing until resolved.

---

## 📁 Sample Data Files

### Tier 3 Customer POCs (6 modules, 11 files)

#### 1. Construction Monitor
**Location:** `tier3_customer_pocs/construction_monitor/`

| File | Size | Description |
|------|------|-------------|
| `planning_application_sample.txt` | ~2.5KB | Planning notice with entities (ORG, PERSON, DATE, LOCATION, QUANTITY) |
| `planning_entities_expected.json` | ~2KB | Ground truth for NER/REL evaluation (15+ entities, 3 relationships) |

**Required Features:** NER, REL, Timeline visualization, Stakeholder network

---

#### 2. British Council
**Location:** `tier3_customer_pocs/british_council/`

| File | Size | Description |
|------|------|-------------|
| `learner_profile_sample.json` | ~1.5KB | 3 learner profiles (Egypt, Spain, China) with levels, goals, budgets |
| `course_catalog_sample.json` | ~1.8KB | 4 courses (IELTS, Business, General, Academic) with requirements, pricing |

**Required Features:** Multi-criteria matching, Match scoring, Recommendations, ROI calculation

---

#### 3. Grant Thornton
**Location:** `tier3_customer_pocs/grant_thornton/`

| File | Size | Description |
|------|------|-------------|
| `company_financial_ratios.csv` | ~2.2KB | 15 companies × 20+ ratios (liquidity, leverage, profitability, efficiency) |
| `credit_analysis_benchmarks.json` | ~3KB | Industry benchmarks, credit rating criteria, Z-score interpretation |

**Required Features:** Financial calculations, Benchmark comparison, Credit rating, Peer analysis

---

#### 4. CRU Mining Intelligence
**Location:** `tier3_customer_pocs/cru/`

| File | Size | Description |
|------|------|-------------|
| `mining_market_report_sample.txt` | ~4.5KB | Copper market analysis with prices, production, demand, inventory, costs |
| `expected_extraction_fields.json` | ~3KB | Structured schema for 50+ data points (price forecasts, production tables) |

**Required Features:** Structured extraction, Multi-table parsing, Time-series data, Financial entities

---

#### 5. GT Motive (Ready for Samples)
**Location:** `tier3_customer_pocs/gt_motive/`

**Status:** Directory created, samples pending
**Required:** Vehicle damage images for computer vision testing (YOLO object detection)

---

#### 6. Solera (Ready for Samples)
**Location:** `tier3_customer_pocs/solera/`

**Status:** Directory created, samples pending
**Required:** Insurance claim documents for OCR + vision AI testing

---

### Tier 2 Domain Verticals (1 module, 2 files + 19 ready directories)

#### 1. Procurement Matcher
**Location:** `tier2_domain_verticals/procurement_matcher/`

| File | Size | Description |
|------|------|-------------|
| `rfp_construction_materials.txt` | ~8KB | £4.5-5.2M RFP with materials, quantities, certifications, evaluation criteria |
| `supplier_profiles.json` | ~6KB | 4 suppliers with capabilities, certifications, pricing, sustainability metrics |

**Required Features:** Requirement extraction, Capability matching, Weighted scoring, Gap analysis

---

#### Other Tier 2 Modules (Ready for Samples)
- `tender_intelligence/`
- `credit_profile_analyzer/`
- `talent_search/`
- `email_campaign_analyzer/`
- `mine_scope/`
- `maritime_report/`
- `planning_classifier/`
- `agri_taxonomy/`
- `agronomy_support/`
- `bot_detect/`
- `email_bounce/`
- `fashion_tagging/`
- `docu_extract/`
- *(and 6 more...)*

---

## 📊 Test Coverage Matrix

| Module | Sample Files | Generic RAG Tests | Specialized Feature Tests | Implementation Status |
|--------|-------------|------------------|--------------------------|----------------------|
| Construction Monitor | 2 | 3 questions | NER, REL | ❌ 0% (NER/REL missing) |
| British Council | 2 | 3 questions | Matching, Scoring | ❌ 0% (Matching missing) |
| Grant Thornton | 2 | 3 questions | Financial calc, Rating | ❌ 0% (Calc engine missing) |
| CRU Mining | 2 | 3 questions | Structured extraction | ❌ 0% (Extraction missing) |
| Procurement Matcher | 2 | 3 questions | Matching, Scoring | ❌ 0% (Matching missing) |
| **TOTAL** | **10 files** | **15 tests** | **5 specialized modules** | **0/5 (0%)** |

**Generic RAG Expected:** 80-100% pass rate (12-15/15)
**Specialized Features Expected:** 0% pass rate (0/5 modules)

---

## 🎯 Implementation Priorities

### P0 - Critical Gaps (Weeks 1-4)
1. **Plugin Architecture** - Foundation for modular specialized features
2. **Construction Monitor POC** - NER/REL proof of concept
3. **Profile Matching** - British Council algorithm

### P1 - High Value (Weeks 5-8)
4. **Procurement Matcher** - Multi-criteria scoring
5. **Financial Analysis** - Grant Thornton calculations
6. **Structured Extraction** - CRU templates

### P2 - Advanced Features (Weeks 9-12)
7. **Computer Vision** - GT Motive, Solera
8. **Specialized UIs** - Multi-tab interfaces for all modules
9. **Workflow Engine** - Multi-stage business processes

---

## 🏗️ Architecture Recommendations

### Plugin System
```
plugins/
├── construction_monitor/
│   ├── models.py          # NER/REL models
│   ├── pipeline.py        # Extraction workflow
│   └── ui/                # React components
├── british_council/
│   ├── matcher.py         # Matching algorithm
│   └── ui/
└── ... (30+ modules)
```

### Model Registry
```yaml
ner_models:
  - name: "construction_ner_v1"
    entities: [DEVELOPER, PLANNING_OFFICER, SITE_ADDRESS]

matching_models:
  - name: "profile_matcher_v1"
    embedding_model: "all-mpnet-base-v2"
```

### Workflow Integration
```python
# LangGraph workflows
from langgraph.graph import StateGraph

workflow = StateGraph()
workflow.add_node("extract_entities", ner_extraction)
workflow.add_node("extract_relationships", rel_extraction)
workflow.add_node("build_graph", knowledge_graph_construction)
```

---

## 📈 Success Metrics

### Technical Metrics
- **NER F1 Score:** >0.85 on planning applications
- **Matching Accuracy:** Top-3 hits >90%
- **Credit Rating Accuracy:** ±1 grade vs. expert
- **Extraction Completeness:** >95% of fields

### Business Metrics
- **Time Savings:** 80% reduction in manual data entry
- **User Satisfaction:** >4.5/5 on specialized UIs
- **Adoption Rate:** >60% within 30 days

---

## 🔧 Troubleshooting

### Upload Fails
1. Check backend: `docker-compose ps backend` (should be "Up" and "healthy")
2. View logs: `docker-compose logs backend --tail 50`
3. Restart: `docker-compose restart backend`

### Query Returns No Results
1. Verify document processed: Check for "processed successfully" in logs
2. Check embeddings: Query `document_chunks` table in database
3. Try simpler question: "What is in this document?"

### Backend Error: "NoneType has no attribute 'lower'"
**Current Issue:** File upload has file_type detection bug

**Workaround:** Use manual UI upload (auto-detects content type) instead of API upload

**Fix Needed:** Update `/backend/app/api/routes/` upload endpoint to handle None file_type

---

## 📝 Change Log

### Version 1.0.0 (January 1, 2026)
- ✅ Created 11 sample data files across 5 modules
- ✅ Generated 2,800+ lines of documentation
- ✅ Developed automated test script (525 lines)
- ✅ Comprehensive gap analysis completed
- ✅ Implementation roadmap defined
- ⚠️ Identified upload file_type bug in backend
- ⚠️ Automated tests blocked by upload issue
- ✅ Created manual testing guide as workaround

---

## 🔗 Related Documentation

### Original Module Specifications
- **Source:** `/merit/merit_aiml_docs/` (30+ module documentation folders)
- **Analysis:** See previous Explore agent report for detailed module breakdowns

### Platform Documentation
- **Architecture:** `/docs/architecture/MEMORY_HIERARCHY_GUIDE.md`
- **API Reference:** http://localhost:8000/api/docs
- **GraphQL:** http://localhost:8000/graphql

---

## 👥 Contact & Support

### Questions About Sample Data
- **Technical Lead:** [Assign name]
- **Sample Data Issues:** Check `/sample_data/README.md` first
- **Testing Support:** See manual test guide troubleshooting section

### Issues Tracker
- Backend bugs: GitHub Issues
- Feature requests: Based on gap analysis in SAMPLE_DATA_AND_TESTING_SUMMARY.md

---

## ✅ Next Steps

1. **Immediate (Today):**
   - [ ] Run 5-minute quick start test
   - [ ] Verify generic RAG is working
   - [ ] Review gap analysis findings

2. **Short Term (This Week):**
   - [ ] Complete manual testing for all 5 modules
   - [ ] Document test results
   - [ ] Fix backend file_type upload bug

3. **Medium Term (This Month):**
   - [ ] Design plugin architecture
   - [ ] Start Construction Monitor POC
   - [ ] Plan resource allocation

4. **Long Term (Next Quarter):**
   - [ ] Implement P0 specialized features
   - [ ] Deploy NER/REL models
   - [ ] Build matching algorithms
   - [ ] Create specialized UIs

---

**Document Version:** 1.0.0
**Last Updated:** January 1, 2026
**Status:** Complete - Ready for Testing
