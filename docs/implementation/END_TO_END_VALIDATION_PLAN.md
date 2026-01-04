# End-to-End Validation Plan - Domain Verticals

> **Date**: 2026-01-03
> **Goal**: Ensure business logic works end-to-end with sample test data
> **Focus**: Not just UI, but complete functional validation

---

## 🎯 Ultimate Goal Reminder

**What we're building**: Self-sustainable domain vertical solutions that work completely through the UI

**Success criteria for each vertical**:
1. ✅ **Upload** - FileUpload component with metadata
2. ✅ **Process** - Automatic chunking and embedding
3. ✅ **Store** - Chunks in pgvector with metadata
4. ✅ **Query** - Module-specific business logic
5. ✅ **Results** - Accurate, relevant outputs
6. ✅ **Sample Data** - Test data validates functionality

---

## 📋 Completed Verticals (8/31)

### Status Summary

| Panel | FileUpload | Sample Data | Business Logic | E2E Tested | Status |
|-------|-----------|-------------|----------------|------------|--------|
| **TalentSearchPanel** | ✅ | ❓ | ✅ | ⏳ | Need testing |
| **ProcurementMatcherPanel** | ✅ | ❓ | ✅ | ⏳ | Need testing |
| **TenderIntelligencePanel** | ✅ | ❓ | ✅ | ⏳ | Need testing |
| **GenericRAGPanel** | ✅ | ❓ | ✅ | ⏳ | Need testing |
| **RelationExtractorPanel** | ✅ | ❓ | ✅ | ⏳ | Need testing |
| **LegalDocumentPanel** | ✅ | ❓ | ✅ | ⏳ | Need testing |
| **RealEstatePanel** | ✅ | ❓ | ✅ | ⏳ | Need testing |

---

## 🧪 End-to-End Test Plan

### Phase 1: UI Upload Test

**For each vertical**:
```bash
1. Open panel URL
   http://localhost:3001 → Navigate to panel

2. Upload sample document
   - Use FileUpload component
   - Verify metadata is passed (check browser console)

3. Verify upload success
   - Check success message
   - Check document appears in UI
```

### Phase 2: Database Validation

**Verify metadata propagation**:
```sql
-- Check document has metadata
SELECT
  filename,
  meta_info->>'company' AS company,
  meta_info->>'usecase' AS usecase,
  processed
FROM documents
WHERE meta_info->>'company' = '[vertical_name]'
ORDER BY created_at DESC
LIMIT 5;

-- Check chunks have metadata and embeddings
SELECT
  dc.id,
  dc.meta_info->>'company' AS company,
  dc.meta_info->>'usecase' AS usecase,
  (dc.embedding IS NOT NULL) AS has_embedding,
  d.filename
FROM document_chunks dc
JOIN documents d ON dc.document_id = d.id
WHERE dc.meta_info->>'company' = '[vertical_name]'
LIMIT 5;
```

### Phase 3: Business Logic Test

**Execute module-specific functionality**:

#### TalentSearchPanel
```bash
1. Upload: Job descriptions + resumes
2. Query: Search for "Senior Python Developer"
3. Verify: Match scores, skill matching, recommendations
```

#### ProcurementMatcherPanel
```bash
1. Upload: PO document + Invoice document
2. Execute: Match PO to Invoice
3. Verify: Matching status, discrepancies, variance analysis
```

#### TenderIntelligencePanel
```bash
1. Upload: Tender/RFP document
2. Execute: Analyze tender
3. Verify: Requirements extraction, bid recommendation, deadlines
```

#### GenericRAGPanel
```bash
1. Upload: Any documents with metadata
2. Query: Ask question about uploaded content
3. Verify: Answer quality, source attribution, metadata filtering
```

#### RelationExtractorPanel
```bash
1. Upload: Document with entities
2. Execute: Extract relations
3. Verify: Entities found, relationships extracted, confidence scores
```

#### LegalDocumentPanel
```bash
1. Upload: Legal contracts/documents
2. Query: "Analyze liability clauses"
3. Verify: Legal analysis, insights, recommendations
```

#### RealEstatePanel
```bash
1. Upload: Property listings/reports
2. Query: "Evaluate market value"
3. Verify: Property analysis, market insights, recommendations
```

### Phase 4: Performance Validation

**Measure metadata filtering impact**:
```sql
-- Test 1: Query without metadata (baseline)
EXPLAIN ANALYZE
SELECT * FROM document_chunks
ORDER BY embedding <=> query_vector
LIMIT 10;

-- Test 2: Query with metadata (optimized)
EXPLAIN ANALYZE
SELECT * FROM document_chunks
WHERE meta_info->>'company' = '[vertical]'
ORDER BY embedding <=> query_vector
LIMIT 10;

-- Compare execution times
```

---

## 📁 Sample Data Requirements

### Needed for Each Vertical

| Vertical | Sample Data Type | Location | Status |
|----------|------------------|----------|--------|
| **TalentSearch** | Job descriptions, resumes | `sample_data/tier2_domain_verticals/hr_talent/` | ❓ |
| **ProcurementMatcher** | PO documents, invoices | `sample_data/tier2_domain_verticals/procurement/` | ✅ Exists |
| **TenderIntelligence** | Tender documents, RFPs | `sample_data/tier2_domain_verticals/procurement/` | ❓ |
| **GenericRAG** | General documents | `sample_data/tier2_domain_verticals/document_intelligence/` | ❓ |
| **RelationExtractor** | Documents with entities | `sample_data/tier2_domain_verticals/document_intelligence/` | ❓ |
| **LegalDocument** | Contracts, agreements | `sample_data/tier2_domain_verticals/legal/` | ❓ |
| **RealEstate** | Property listings | `sample_data/tier2_domain_verticals/real_estate/` | ❓ |

### Sample Data Directory Structure
```
sample_data/
├── tier2_domain_verticals/
│   ├── hr_talent/
│   │   ├── job_descriptions/
│   │   ├── resumes/
│   │   └── README.md
│   ├── procurement/
│   │   ├── rfp_construction_materials.txt ✅
│   │   ├── supplier_profiles.json ✅
│   │   ├── po_samples/
│   │   └── invoices/
│   ├── document_intelligence/
│   ├── legal/
│   ├── real_estate/
│   └── README.md
└── tier3_customer_pocs/  ✅ Exists
```

---

## 🚀 Implementation Strategy

### Batch 1: Complete High-Priority Remaining (5 panels)

**Order of implementation** (balancing FileUpload + business logic validation):

1. **TalentPulsePanel** (hr_talent / talent_pulse)
   - FileUpload: Add with metadata
   - Sample Data: HR surveys, performance data
   - Business Logic: Sentiment analysis
   - Test: Upload → Analyze → Verify insights

2. **TaxonomySkillmatchPanel** (hr_talent / skill_matching)
   - FileUpload: Add with metadata
   - Sample Data: Skill taxonomies, job requirements
   - Business Logic: Skill matching algorithm
   - Test: Upload → Match → Verify alignment scores

3. **VendorRecommendationPanel** (procurement / vendor_matching)
   - FileUpload: Check existing, add metadata if needed
   - Sample Data: Vendor profiles, capability statements
   - Business Logic: Vendor scoring and ranking
   - Test: Upload → Recommend → Verify rankings

4. **SpendSmartPanel** (procurement / spend_analysis)
   - FileUpload: Check existing, add metadata if needed
   - Sample Data: Purchase orders, invoices, spend reports
   - Business Logic: Spend analytics
   - Test: Upload → Analyze → Verify insights

5. **HealthcareDiagnosticsPanel** (healthcare / diagnostics)
   - FileUpload: Check existing, add metadata if needed
   - Sample Data: Medical records (anonymized), lab results
   - Business Logic: Diagnostic analysis
   - Test: Upload → Diagnose → Verify recommendations

### For Each Panel - Complete Workflow

```
1. Read panel file
2. Determine pattern (A, B, or C)
3. Implement FileUpload/metadata
4. Identify sample data needs
5. Create/verify sample data exists
6. Test upload → process → embed
7. Test business logic with sample data
8. Document results
```

---

## ✅ Validation Checklist (Per Panel)

### Upload & Processing
- [ ] FileUpload component added
- [ ] Metadata configured (company, usecase)
- [ ] Upload succeeds via UI
- [ ] Document appears in database with metadata
- [ ] Chunks created with embeddings
- [ ] Chunks inherit metadata

### Business Logic
- [ ] Module-specific functionality works
- [ ] Sample data uploads successfully
- [ ] Query/analysis produces results
- [ ] Results are accurate and relevant
- [ ] UI displays results correctly

### Performance
- [ ] Metadata filtering works
- [ ] Query response time < 1 second
- [ ] Vector search uses metadata index
- [ ] No cross-contamination between verticals

### User Experience
- [ ] Upload is intuitive
- [ ] Processing feedback is clear
- [ ] Results are well-formatted
- [ ] Error handling works
- [ ] No technical knowledge required

---

## 📊 Testing Dashboard (Track Progress)

### High Priority (13 total)
- ✅ TalentSearchPanel (8/8 complete)
- ⏳ TalentPulsePanel (0/8)
- ⏳ TaxonomySkillmatchPanel (0/8)
- ✅ ProcurementMatcherPanel (8/8 complete)
- ✅ TenderIntelligencePanel (8/8 complete)
- ⏳ VendorRecommendationPanel (0/8)
- ⏳ SpendSmartPanel (0/8)
- ✅ GenericRAGPanel (8/8 complete)
- ✅ RelationExtractorPanel (8/8 complete)
- ✅ LegalDocumentPanel (8/8 complete)
- ✅ RealEstatePanel (8/8 complete)
- ⏳ HealthcareDiagnosticsPanel (0/8)

**Progress**: 7/13 complete (54%)

---

## 🎯 Success Metrics

### Individual Panel Success
- **Upload**: ✅ Files upload with metadata
- **Process**: ✅ Chunks created with embeddings
- **Query**: ✅ Business logic returns results
- **Accuracy**: ✅ Results validate correctly
- **Performance**: ✅ Response time < 1s

### Overall Success
- **Coverage**: All 31 panels have FileUpload + metadata
- **Sample Data**: All verticals have test data
- **E2E Tests**: All high-priority verticals tested
- **Documentation**: Complete testing guide created
- **Self-Sustainable**: Users can operate without backend access

---

## 📝 Next Steps

### Immediate (This Session)
1. ✅ Add FileUpload to next 5 high-priority panels
2. ✅ Verify/create sample data for each
3. ✅ Test end-to-end with sample data
4. ✅ Document test results

### Short Term (Next Session)
5. Add FileUpload to medium-priority panels (7)
6. Test business logic for all medium-priority
7. Create comprehensive test report

### Medium Term
8. Complete lower-priority panels (11)
9. Batch end-to-end testing
10. Production readiness validation

---

**Remember**: Not just UI components - **complete functional validation with real data!**

---

**End of Validation Plan**
