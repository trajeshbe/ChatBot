# Project Estimator - Enhanced Implementation Plan

## Reference Materials Analysis

### Available Reference Files

**Location**: `docs/features/project_estimator/estimate_one/`

1. **EstimateOne_BRD_Document.docx** - Manual BRD template
2. **Estimate_One_Construction_Document_Extraction_Estimation (1).xlsx** - Cost estimation template
3. **Project Size Sourcing.xlsx** - Project scoping/sizing document
4. **Sampe_data/** - Construction project samples:
   - 110199_Galleon_Gardens_Clubhouse_fullSet
   - 110494_Edmonton_Storage_Facilty-_B_Block_refit_fullSet

## Enhancement Requirements

### 1. Multi-File Upload Capability

**Current State**: Single text input for project scope

**Enhanced State**: Support uploading multiple files simultaneously

#### File Types to Support:
- **Project Scope Document**: PDF, DOCX, TXT
- **Sample Data**: Multiple files (construction drawings, specifications, etc.)
- **Reference BRD**: Previous BRD templates (DOCX, PDF)
- **Cost Templates**: Previous cost estimation Excel files (XLSX)

### 2. Enhanced UI Design

#### Current UI Structure:
```typescript
interface CurrentUI {
  projectScope: string;  // Text input only
  scenarios: 3 configs;
  sliders: 15 parameters;
}
```

#### Enhanced UI Structure:
```typescript
interface EnhancedUI {
  // Multi-file upload section
  projectScopeFiles: File[];        // Multiple scope docs
  sampleDataFiles: File[];          // Construction drawings, specs, etc.
  referenceBRDFiles: File[];        // Previous BRD templates
  costTemplateFiles: File[];        // Previous Excel templates

  // Existing sections
  scenarios: 3 configs;
  sliders: 15 parameters;

  // New quality indicators
  estimationQuality: {
    completeness: number;           // % of sections filled
    dataAvailability: number;       // % based on sample data
    templateAlignment: number;      // % match with reference BRD
  };
}
```

### 3. Backend Processing Flow

#### Enhanced Processing Pipeline:

```
Step 1: File Upload & Processing
├─ Project Scope Document(s) → Extract requirements
├─ Sample Data Files → Analyze complexity/scope
├─ Reference BRD → Extract structure/sections
└─ Cost Templates → Extract historical rates/formulas

Step 2: AI Analysis
├─ Combine all extracted content
├─ Cross-reference with sample data
├─ Match to BRD structure from reference
└─ Apply historical rates from cost templates

Step 3: Generate Enhanced Output
├─ BRD (Word) - Structured based on reference template
├─ Cost Estimation (Excel) - Using reference formulas
└─ Quality Report - Validation against standards
```

### 4. API Endpoint Enhancements

#### New/Updated Endpoints:

**POST /api/v1/project-estimator/generate-enhanced**
```json
{
  "project_scope_files": [File, File, ...],
  "sample_data_files": [File, File, ...],
  "reference_brd_files": [File, ...],
  "cost_template_files": [File, ...],
  "session_id": "string",
  "model_id": "gpt-4-turbo",
  "config": {
    // All 15 parameters
  }
}
```

**Response**:
```json
{
  "project_name": "string",
  "total_cost": number,
  "total_effort_hours": number,
  "brd_url": "string",
  "cost_estimation_url": "string",
  "quality_metrics": {
    "completeness_score": 85,
    "data_coverage_score": 92,
    "template_match_score": 78,
    "confidence_level": "HIGH"
  },
  "reference_analysis": {
    "scope_docs_processed": 2,
    "sample_files_analyzed": 15,
    "brd_template_matched": true,
    "historical_rates_applied": true
  }
}
```

### 5. Reference Template Structure Analysis

Based on `estimate_one` folder, the enhanced BRD should include:

#### Standard BRD Sections:
1. **Executive Summary**
2. **Project Objectives**
3. **Scope of Work**
4. **Functional Requirements**
5. **Technical Requirements**
6. **Data Requirements** (based on sample data)
7. **Integration Points**
8. **Assumptions & Constraints**
9. **Success Criteria**
10. **Timeline & Milestones**

#### Enhanced Cost Estimation Tabs:
1. **lookup** - All configurable parameters
2. **AIML_cost** - Detailed task breakdown (from reference)
3. **AIML_COST_SUMMARY** - Summary with formulas
4. **unit_cost** - Role-based rates
5. **Resource_Loading** - Week-by-week allocation
6. **Reference_Rates** (NEW) - Historical rates from uploaded templates
7. **Sample_Analysis** (NEW) - Complexity metrics from sample data
8. **Quality_Report** (NEW) - Validation metrics

### 6. Implementation Phases

#### Phase 1: Multi-File Upload UI (Priority: HIGH)
**Files to Modify**:
- `frontend/src/components/ProjectEstimator.tsx`

**Changes**:
1. Add multi-file dropzone for each file category
2. Display uploaded files with preview/remove options
3. Show file count and total size
4. Add file type validation

**Estimated Effort**: 8 hours

#### Phase 2: Backend Multi-File Processing (Priority: HIGH)
**Files to Modify**:
- `backend/app/api/routes/project_estimator_routes.py`
- `backend/app/services/project_estimator_service.py`

**Changes**:
1. Update `/generate` endpoint to accept multiple files
2. Process each file category separately
3. Extract content from all uploaded files
4. Combine extracted data for AI analysis

**Estimated Effort**: 12 hours

#### Phase 3: Reference Template Integration (Priority: MEDIUM)
**Files to Modify**:
- `backend/app/services/project_estimator_service.py`

**Changes**:
1. Parse uploaded BRD templates to extract structure
2. Parse uploaded Excel templates to extract formulas/rates
3. Use reference structure for generated BRD
4. Apply historical rates when available

**Estimated Effort**: 16 hours

#### Phase 4: Sample Data Analysis (Priority: MEDIUM)
**Files to Create**:
- `backend/app/services/sample_data_analyzer.py`

**Functions**:
1. Analyze complexity based on sample files
2. Extract metadata (file count, types, sizes)
3. Identify data patterns
4. Adjust effort estimates based on data volume

**Estimated Effort**: 12 hours

#### Phase 5: Quality Validation & Metrics (Priority: LOW)
**Files to Create**:
- `backend/app/services/estimation_quality_validator.py`

**Functions**:
1. Calculate completeness score
2. Validate against reference templates
3. Generate quality report
4. Provide confidence metrics

**Estimated Effort**: 8 hours

## Total Estimated Effort

| Phase | Effort | Priority |
|-------|--------|----------|
| Phase 1: Multi-File Upload UI | 8 hours | HIGH |
| Phase 2: Backend Multi-File Processing | 12 hours | HIGH |
| Phase 3: Reference Template Integration | 16 hours | MEDIUM |
| Phase 4: Sample Data Analysis | 12 hours | MEDIUM |
| Phase 5: Quality Validation | 8 hours | LOW |
| **Total** | **56 hours** | **7 days** |

## Acceptance Criteria

### Must Have (MVP):
- [x] Multi-file upload for project scope
- [ ] Support for PDF, DOCX, TXT, XLSX uploads
- [ ] Process all files and extract content
- [ ] Generate enhanced BRD with all sections
- [ ] Generate cost estimation with reference formulas

### Should Have:
- [ ] Reference BRD template parsing
- [ ] Historical rate extraction from Excel templates
- [ ] Sample data complexity analysis
- [ ] Quality metrics in response

### Nice to Have:
- [ ] Side-by-side BRD comparison (generated vs reference)
- [ ] Excel formula validation
- [ ] Automated quality report generation
- [ ] Template library management

## Testing Strategy

### Test Cases:
1. **Test with Reference Files**:
   - Upload all files from `estimate_one/`
   - Verify BRD structure matches reference
   - Verify Excel formulas match reference
   - Validate quality scores

2. **Test with Mixed Files**:
   - Upload partial files (scope only)
   - Upload multiple scope docs
   - Upload reference template only
   - Verify graceful degradation

3. **Test File Size Limits**:
   - Single large file (50MB)
   - Multiple files (100+ files)
   - Verify performance and timeouts

4. **Test Quality Metrics**:
   - Complete upload → High score
   - Minimal upload → Low score
   - Verify metric accuracy

## Next Steps

1. **Immediate**: Start with Phase 1 (Multi-File Upload UI)
2. **Week 1**: Complete Phases 1 & 2 (High Priority)
3. **Week 2**: Implement Phase 3 (Reference Template Integration)
4. **Testing**: Use `estimate_one` files for validation
5. **Iteration**: Refine based on test results

## Questions to Address

1. **File Size Limits**: What's the max file size for uploads?
   - Recommended: 50MB per file, 200MB total

2. **File Storage**: Where to store uploaded files?
   - Temporary: `/tmp/project_estimates/{session_id}/`
   - Retention: 7 days

3. **Template Library**: Should we maintain a template library?
   - Yes, for common project types
   - Location: `backend/app/templates/project_types/`

4. **Historical Rates**: How to version historical rates?
   - Store in database with timestamps
   - Allow users to select which version to use

---

**Status**: Planning Complete
**Next Action**: Start Phase 1 - Multi-File Upload UI
**Owner**: AI Development Team
**Due Date**: TBD
