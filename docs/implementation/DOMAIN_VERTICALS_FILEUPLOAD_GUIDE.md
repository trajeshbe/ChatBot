# Domain Verticals - FileUpload Integration Guide

> **Date**: 2026-01-03
> **Status**: Pattern Documented, Ready for Implementation
> **Scope**: 31 Tier 2 Domain Vertical Panels

---

## Executive Summary

All **31 domain vertical panels** in Tier 2 need FileUpload integration for self-sustainable operation. This document provides:
1. **Implementation pattern** (reusable template)
2. **Priority ranking** (which to implement first)
3. **Metadata mapping** (company/usecase for each vertical)
4. **Testing guide** (how to validate each vertical)

**Current Status**:
- ✅ Customer Solutions (3/3): British Council, CRU, Grant Thornton
- ⏳ Domain Verticals (0/31): Ready for implementation

---

## Implementation Pattern

### Step 1: Add FileUpload Import

```typescript
// At the top of the file, after existing imports
import FileUpload from '../../FileUpload'  // Adjust path based on directory depth
```

**Path Mapping**:
- `/tier2/category/Panel.tsx` → `../../FileUpload` (2 levels up)
- `/components/Panel.tsx` → `./FileUpload` (same level)

### Step 2: Add FileUpload Section in Return

```typescript
return (
  <div className="p-6 max-w-7xl mx-auto">
    {/* Header and Config sections... */}

    {/* NEW: Document Upload Section */}
    <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
      <h3 className="text-lg font-semibold text-slate-800 mb-2">
        📄 [Panel-Specific Title]
      </h3>
      <p className="text-sm text-slate-600 mb-4">
        [Panel-specific description of what files to upload]
      </p>
      <FileUpload
        hideProjectSelector={true}
        compact={true}
        metadata={{
          company: '[vertical_name]',
          usecase: '[specific_usecase]'
        }}
      />
    </div>

    {/* Existing panel content... */}
  </div>
)
```

### Step 3: Update Backend Service (if needed)

Most backend services already support metadata filtering via:
```python
WHERE documents.meta_info->>'company' = 'hr_talent'
  AND documents.meta_info->>'usecase' = 'talent_search'
```

No backend changes needed if service already uses metadata filtering!

---

## Domain Vertical Panels - Priority Ranking

### 🔴 High Priority (Document-Intensive) - Implement First

| # | Panel | Company | Usecase | File Types | Priority Reason |
|---|-------|---------|---------|------------|-----------------|
| 1 | **TalentSearchPanel** | hr_talent | talent_search | Resumes, CVs, JDs | High volume, critical business need |
| 2 | **ProcurementMatcherPanel** | procurement | rfp_matching | RFPs, tenders, specs | Document-heavy vertical |
| 3 | **GenericRAGPanel** | document_intelligence | generic_rag | Any documents | General-purpose, high usage |
| 4 | **LegalDocumentPanel** | legal | document_analysis | Contracts, agreements | Legal compliance critical |
| 5 | **RealEstatePanel** | real_estate | property_analysis | Listings, reports | Property document analysis |
| 6 | **TenderIntelligencePanel** | procurement | tender_analysis | Tender docs, bids | Procurement vertical |
| 7 | **RelationExtractorPanel** | document_intelligence | relation_extraction | Technical docs | Entity extraction |
| 8 | **HealthcareDiagnosticsPanel** | healthcare | diagnostics | Medical records | Compliance-sensitive |

### 🟡 Medium Priority (Analysis-Focused) - Implement Next

| # | Panel | Company | Usecase | File Types | Priority Reason |
|---|-------|---------|---------|------------|-----------------|
| 9 | **CustomerChurnPanel** | analytics | churn_prediction | Customer data, logs | Analytics with uploads |
| 10 | **FinancialAnomalyPanel** | analytics | anomaly_detection | Transaction logs | Financial data analysis |
| 11 | **SalesPerformancePanel** | analytics | sales_analysis | Sales records, CRM | Sales intelligence |
| 12 | **EstimatorAUPanel** | construction | cost_estimation | Building plans, specs | Construction estimates |
| 13 | **MaritimeReportPanel** | maritime | maritime_logistics | Shipping manifests | Maritime logistics |
| 14 | **VendorRecommendationPanel** | procurement | vendor_matching | Vendor profiles | Supplier management |
| 15 | **InsuranceRiskPanel** | insurance | risk_assessment | Policy docs, claims | Insurance vertical |

### 🟢 Lower Priority (Less Document-Dependent) - Implement Later

| # | Panel | Company | Usecase | File Types | Priority Reason |
|---|-------|---------|---------|------------|-----------------|
| 16 | **PredictiveAnalyticsPanel** | analytics | predictive_modeling | Historical datasets | Model-focused |
| 17 | **ProductRecommendationPanel** | ecommerce | product_recommendations | Product catalogs | E-commerce |
| 18 | **CampaignOptimizerPanel** | marketing | campaign_optimization | Campaign reports | Marketing analytics |
| 19 | **SentimentSocialPanel** | marketing | sentiment_analysis | Social media data | Sentiment analysis |
| 20 | **TalentPulsePanel** | hr_talent | talent_pulse | HR surveys | Employee analytics |
| 21 | **TaxonomySkillmatchPanel** | hr_talent | skill_matching | Skill taxonomies | Skill management |
| 22 | **SpendSmartPanel** | procurement | spend_analysis | Purchase orders | Spend analytics |
| 23 | **PlanningClassifierPanel** | construction | planning_classification | Planning apps | Planning documents |
| 24 | **MineScopePanel** | construction | mining_scope | Mine plans | Mining vertical |
| 25 | **BuildingMetricsPanel** | construction | building_metrics | Building data | Construction metrics |
| 26 | **AgriTaxonomyPanel** | agriculture | taxonomy_classification | Crop data | Agricultural taxonomy |
| 27 | **AgronomyDecisionPanel** | agriculture | agronomy_decisions | Soil reports | Agronomy data |
| 28 | **CodeAnalysisPanel** | advanced | code_analysis | Source code | Code review |
| 29 | **MultilingualTranslatorPanel** | advanced | translation | Any language docs | Translation service |
| 30 | **EducationalContentPanel** | education | content_analysis | Course materials | Educational content |

---

## Metadata Mapping Table

| Panel | Company | Usecase | Title | Description |
|-------|---------|---------|-------|-------------|
| **TalentSearchPanel** | `hr_talent` | `talent_search` | 📄 Upload Resumes & Job Descriptions | Upload resumes, CVs, job descriptions, or candidate profiles for intelligent matching. |
| **ProcurementMatcherPanel** | `procurement` | `rfp_matching` | 📋 Upload RFP Documents | Upload RFPs, tenders, supplier profiles, or procurement specifications. |
| **GenericRAGPanel** | `document_intelligence` | `generic_rag` | 📚 Upload Documents | Upload any documents for intelligent search and retrieval. |
| **LegalDocumentPanel** | `legal` | `document_analysis` | ⚖️ Upload Legal Documents | Upload contracts, agreements, legal briefs, or case documents. |
| **RealEstatePanel** | `real_estate` | `property_analysis` | 🏠 Upload Property Documents | Upload property listings, inspection reports, or market analyses. |
| **TenderIntelligencePanel** | `procurement` | `tender_analysis` | 🔍 Upload Tender Documents | Upload tender documents, bid submissions, or contract specifications. |
| **RelationExtractorPanel** | `document_intelligence` | `relation_extraction` | 🔗 Upload Documents for Relation Extraction | Upload documents to extract entities and relationships. |
| **HealthcareDiagnosticsPanel** | `healthcare` | `diagnostics` | 🏥 Upload Medical Documents | Upload medical records, lab results, or clinical guidelines. |
| **CustomerChurnPanel** | `analytics` | `churn_prediction` | 📊 Upload Customer Data | Upload customer records, usage data, or interaction logs. |
| **FinancialAnomalyPanel** | `analytics` | `anomaly_detection` | 💹 Upload Financial Data | Upload transaction logs, financial statements, or audit reports. |
| **SalesPerformancePanel** | `analytics` | `sales_analysis` | 💼 Upload Sales Data | Upload sales records, CRM exports, or performance reports. |
| **EstimatorAUPanel** | `construction` | `cost_estimation` | 🏗️ Upload Construction Documents | Upload building plans, specifications, or cost estimates. |
| **MaritimeReportPanel** | `maritime` | `maritime_logistics` | 🚢 Upload Maritime Documents | Upload shipping manifests, port reports, or logistics data. |
| **VendorRecommendationPanel** | `procurement` | `vendor_matching` | 🏢 Upload Vendor Profiles | Upload vendor profiles, capability statements, or supplier catalogs. |
| **InsuranceRiskPanel** | `insurance` | `risk_assessment` | 🛡️ Upload Insurance Documents | Upload policy documents, claims, or risk assessment reports. |
| **PredictiveAnalyticsPanel** | `analytics` | `predictive_modeling` | 🔮 Upload Historical Data | Upload historical datasets for predictive analysis. |
| **ProductRecommendationPanel** | `ecommerce` | `product_recommendations` | 🛒 Upload Product Catalogs | Upload product catalogs, user behavior data, or purchase histories. |
| **CampaignOptimizerPanel** | `marketing` | `campaign_optimization` | 📢 Upload Campaign Data | Upload campaign reports, performance metrics, or marketing materials. |
| **SentimentSocialPanel** | `marketing` | `sentiment_analysis` | 💬 Upload Social Media Data | Upload social media posts, reviews, or customer feedback. |
| **TalentPulsePanel** | `hr_talent` | `talent_pulse` | 📊 Upload HR Data | Upload employee surveys, performance reviews, or engagement data. |
| **TaxonomySkillmatchPanel** | `hr_talent` | `skill_matching` | 🎯 Upload Skill Taxonomies | Upload skill taxonomies, competency frameworks, or job requirement documents. |
| **SpendSmartPanel** | `procurement` | `spend_analysis` | 💰 Upload Spend Data | Upload purchase orders, invoices, or spend analytics reports. |
| **PlanningClassifierPanel** | `construction` | `planning_classification` | 📐 Upload Planning Applications | Upload planning applications, permits, or regulatory documents. |
| **MineScopePanel** | `construction` | `mining_scope` | ⛏️ Upload Mining Documents | Upload mine plans, geological surveys, or scope documents. |
| **BuildingMetricsPanel** | `construction` | `building_metrics` | 📏 Upload Building Data | Upload building metrics, performance data, or compliance reports. |
| **AgriTaxonomyPanel** | `agriculture` | `taxonomy_classification` | 🌾 Upload Agricultural Documents | Upload crop data, taxonomy documents, or agricultural reports. |
| **AgronomyDecisionPanel** | `agriculture` | `agronomy_decisions` | 🌱 Upload Agronomy Data | Upload soil reports, weather data, or crop management documents. |
| **CodeAnalysisPanel** | `advanced` | `code_analysis` | 💻 Upload Code Files | Upload source code files, documentation, or code review reports. |
| **MultilingualTranslatorPanel** | `advanced` | `translation` | 🌐 Upload Documents for Translation | Upload documents in any language for translation and analysis. |
| **EducationalContentPanel** | `education` | `content_analysis` | 🎓 Upload Educational Materials | Upload course materials, textbooks, or learning resources. |

---

## Implementation Examples

### Example 1: TalentSearchPanel (High Priority)

```typescript
// File: frontend/src/components/tier2/hr_talent/TalentSearchPanel.tsx

import { useState } from 'react'
import axios from 'axios'
import { Search, Plus, X, Users, Star, TrendingUp, Award, Briefcase, Settings } from 'lucide-react'
import POCConfigManager from '../../POCConfigManager'
import FileUpload from '../../FileUpload'  // ADD THIS

export default function TalentSearchPanel() {
  // ... existing state ...

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        {/* ... header content ... */}
      </div>

      {/* Configuration Panel */}
      {showConfig && (
        <div className="mb-6">
          <POCConfigManager
            moduleName="talent_search"
            onClose={() => setShowConfig(false)}
          />
        </div>
      )}

      {/* ADD THIS: Document Upload Section */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <h3 className="text-lg font-semibold text-slate-800 mb-2">
          📄 Upload Resumes & Job Descriptions
        </h3>
        <p className="text-sm text-slate-600 mb-4">
          Upload resumes, CVs, job descriptions, or candidate profiles for intelligent matching.
        </p>
        <FileUpload
          hideProjectSelector={true}
          compact={true}
          metadata={{
            company: 'hr_talent',
            usecase: 'talent_search'
          }}
        />
      </div>

      {/* Existing panel content */}
      {/* ... rest of component ... */}
    </div>
  )
}
```

### Example 2: ProcurementMatcherPanel (High Priority)

```typescript
// File: frontend/src/components/tier2/procurement/ProcurementMatcherPanel.tsx

import FileUpload from '../../FileUpload'  // ADD THIS

export default function ProcurementMatcherPanel() {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header and Config... */}

      {/* ADD THIS: Document Upload Section */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <h3 className="text-lg font-semibold text-slate-800 mb-2">
          📋 Upload RFP Documents
        </h3>
        <p className="text-sm text-slate-600 mb-4">
          Upload RFPs, tenders, supplier profiles, or procurement specifications.
        </p>
        <FileUpload
          hideProjectSelector={true}
          compact={true}
          metadata={{
            company: 'procurement',
            usecase: 'rfp_matching'
          }}
        />
      </div>

      {/* Existing panel content */}
    </div>
  )
}
```

---

## Testing Guide

### Test Template for Each Vertical

```bash
# 1. Open UI
http://localhost:3001 → [Vertical Name] Panel

# 2. Upload test document
sample_data/tier2_domain_verticals/[vertical]/sample_file.[ext]

# 3. Verify upload in database
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
  SELECT filename, meta_info
  FROM documents
  WHERE meta_info->>'company' = '[company]'
    AND meta_info->>'usecase' = '[usecase]'
  LIMIT 5
"

# 4. Test vertical functionality
[Vertical-specific action: search, analyze, match, etc.]

# 5. Verify results
Should return results filtered by metadata
```

### Example: Test TalentSearchPanel

```bash
# 1. Upload resume
Upload: resume_john_doe.pdf

# 2. Verify metadata
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
  SELECT filename, meta_info->>'company', meta_info->>'usecase'
  FROM documents
  WHERE meta_info->>'company' = 'hr_talent'
  LIMIT 1
"

# Expected output:
#  filename          | company   | usecase
# -------------------+-----------+--------------
#  resume_john_doe.pdf | hr_talent | talent_search

# 3. Run talent search
Input: Job requirements for "Senior Python Developer"
Click: "Find Candidates"

# 4. Verify results
Should return matched candidates from uploaded resumes
```

---

## Implementation Checklist

### High Priority (8 panels)

- [ ] 1. TalentSearchPanel (hr_talent / talent_search)
- [ ] 2. ProcurementMatcherPanel (procurement / rfp_matching)
- [ ] 3. GenericRAGPanel (document_intelligence / generic_rag)
- [ ] 4. LegalDocumentPanel (legal / document_analysis)
- [ ] 5. RealEstatePanel (real_estate / property_analysis)
- [ ] 6. TenderIntelligencePanel (procurement / tender_analysis)
- [ ] 7. RelationExtractorPanel (document_intelligence / relation_extraction)
- [ ] 8. HealthcareDiagnosticsPanel (healthcare / diagnostics)

### Medium Priority (7 panels)

- [ ] 9. CustomerChurnPanel (analytics / churn_prediction)
- [ ] 10. FinancialAnomalyPanel (analytics / anomaly_detection)
- [ ] 11. SalesPerformancePanel (analytics / sales_analysis)
- [ ] 12. EstimatorAUPanel (construction / cost_estimation)
- [ ] 13. MaritimeReportPanel (maritime / maritime_logistics)
- [ ] 14. VendorRecommendationPanel (procurement / vendor_matching)
- [ ] 15. InsuranceRiskPanel (insurance / risk_assessment)

### Lower Priority (16 panels)

- [ ] 16-31. (See full list above)

---

## Automation Script (Optional)

A Python script is available at:
```
backend/scripts/add_fileupload_to_panels.py
```

**Usage**:
```bash
cd backend
python3 scripts/add_fileupload_to_panels.py
```

**Warning**: Automated script may require manual review for each panel due to varying component structures. Recommended approach:
1. Use script to add imports
2. Manually verify FileUpload placement
3. Test each panel individually

---

## Estimated Effort

| Priority | Panels | Time per Panel | Total Time |
|----------|--------|----------------|------------|
| High | 8 | 15 mins | 2 hours |
| Medium | 7 | 15 mins | 1.75 hours |
| Lower | 16 | 15 mins | 4 hours |
| **Total** | **31** | | **~8 hours** |

**Phased Approach**:
- **Phase 1** (Week 1): High priority (8 panels)
- **Phase 2** (Week 2): Medium priority (7 panels)
- **Phase 3** (Week 3): Lower priority (16 panels)

---

## Benefits Summary

### For Users

| Benefit | Description |
|---------|-------------|
| **Self-Sustainable** | Upload documents via UI, no backend access |
| **Consistent UX** | Same upload experience across all 31 verticals |
| **Real-Time** | Documents available immediately after upload |
| **Multi-Format** | JSON, CSV, TXT, PDF, DOCX all supported |

### For System

| Benefit | Description |
|---------|-------------|
| **Metadata Filtering** | Efficient vector search (filter first, then search) |
| **JSONB Storage** | Searchable metadata in PostgreSQL |
| **Automatic Processing** | Chunking + embedding handled automatically |
| **No Script Maintenance** | Eliminated 31+ potential ingestion scripts |

---

## Next Steps

1. **Immediate**: Implement High Priority panels (8 panels, 2 hours)
2. **Short-term**: Implement Medium Priority panels (7 panels, 1.75 hours)
3. **Long-term**: Complete Lower Priority panels (16 panels, 4 hours)
4. **Documentation**: Update user guide with vertical-specific upload instructions
5. **Testing**: Validate each vertical end-to-end

---

## Related Documentation

- `ALL_POCs_SELF_SUSTAINABLE_COMPLETE.md` - Customer solutions (already complete)
- `BRITISH_COUNCIL_UI_SELF_SUSTAINABLE.md` - Detailed implementation example
- `MODEL_SELECTOR_INTEGRATION_IN_POC_CONFIG.md` - Module configuration

---

**End of Document**
