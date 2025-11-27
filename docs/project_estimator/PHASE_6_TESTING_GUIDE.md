# Phase 6 Testing Guide - Estimate One Project

**Date**: 2025-11-26
**Purpose**: Test Phase 6 EDA Download Endpoints with real Estimate One project files

---

## 📁 Test Files Available

Located in: `C:\AIML\ClaudeCode\chatbot\ChatBot\docs\features\project_estimator\estimate_one\`

1. **Project Scope.txt** - Project requirements and scope
2. **cost_estimation_estimate_one.xlsx** - Sample cost estimation file
3. **110494_Edmonton_Storage_Facilty-_B_Block_refit_fullSet.zip** - Sample architectural data
4. **EstimateOne_BRD_Document.docx** - Sample BRD for reference

---

## 🧪 Quick Test Options

### Option 1: Run Automated Test Script

```bash
python3 /tmp/test_phase6_with_estimate_one.py
```

This script will:
1. ✅ Load Project Scope from Estimate One
2. ✅ Trigger workflow execution
3. ✅ Test JSON endpoint
4. ✅ Test Excel endpoint
5. ✅ Verify state file generation

### Option 2: Manual API Test

**Step 1: Check existing state files**
```bash
docker-compose exec backend ls -lh /app/uploads/project_estimator/state_*.json
```

**Step 2: Use most recent job_id** (e.g., from `BRD_20251126_043815.docx` → job_id = `20251126_043815`)

**Step 3: Test JSON endpoint**
```bash
curl -X GET "http://localhost:8000/api/v1/project-estimator/20251126_043815/eda-report" | jq .
```

**Step 4: Test Excel endpoint**
```bash
curl -X GET "http://localhost:8000/api/v1/project-estimator/20251126_043815/eda-report/excel" \
  -o "EDA_Report_20251126_043815.xlsx"
```

### Option 3: UI Test with Estimate One Files

**Step 1: Open frontend**
```
http://localhost:3001
```

**Step 2: Navigate to Project Estimator**

**Step 3: Copy/paste project scope**
- Open: `docs/features/project_estimator/estimate_one/Project Scope.txt`
- Copy entire contents
- Paste into Project Estimator textarea

**Step 4: Upload sample file**
- Click "Browse" or drag-and-drop
- Select: `cost_estimation_estimate_one.xlsx`

**Step 5: Select "Full Service" and Generate**

**Step 6: Wait for completion** (2-5 minutes)

**Step 7: Download generated documents**
- Download BRD
- Download Cost Estimate Excel

**Step 8: Extract job_id from filename**
- Example: `BRD_20251126_143022.docx` → job_id = `20251126_143022`

**Step 9: Test Phase 6 endpoints**
```bash
# JSON
curl http://localhost:8000/api/v1/project-estimator/20251126_143022/eda-report

# Excel
curl http://localhost:8000/api/v1/project-estimator/20251126_143022/eda-report/excel \
  -o EDA_Report.xlsx
```

---

## 📊 Expected Results

### For Workflows WITH Sample Files Uploaded:

**JSON Endpoint (200 OK)**:
```json
{
  "job_id": "20251126_143022",
  "eda_report": {
    "total_files_analyzed": 1,
    "domain": "Construction/Cost Estimation",
    "detected_data_types": ["tabular_excel"],
    "overall_data_quality": 0.85,
    "total_data_volume_mb": 0.15,
    "files_analysis": [
      {
        "file_type": "excel",
        "sheets": 3,
        "overall_data_quality": 0.85,
        "insights": [...]
      }
    ]
  },
  "recommended_tech_stack": {
    "primary_tools": {
      "data_processing": ["pandas", "openpyxl"],
      "cost_analysis": ["NumPy", "SciPy"]
    },
    "chatbot_tools": {...},
    "use_cases": [...]
  },
  "consensus_analysis": {
    "alignment_score": 90,
    "status": "ALIGNED",
    "issues": [],
    "recommendation": "Sample cost data aligns well with project scope"
  }
}
```

**Excel Endpoint (200 OK)**:
- File: `EDA_Report_{job_id}.xlsx`
- Size: ~50-100 KB
- Sheets:
  1. Summary Metrics
  2. Detailed File Analysis (cost_estimation_estimate_one.xlsx breakdown)
  3. Recommended Tech Stack
  4. Consensus Analysis

### For Workflows WITHOUT Sample Files:

**JSON Endpoint (404 Not Found)**:
```json
{
  "detail": "No EDA report found in workflow state. Sample files may not have been uploaded."
}
```

**Excel Endpoint (404 Not Found)**:
```json
{
  "detail": "No EDA report found in workflow state"
}
```

---

## 🔍 Validation Checklist

### ✅ Phase 6 Implementation Complete

- [x] State saving logic added to workflow
- [x] JSON endpoint implemented and working
- [x] Excel endpoint implemented and working
- [x] Error handling (404 for missing data)
- [x] Professional Excel formatting
- [x] Documentation complete

### ✅ Test Results Expected

For NEW workflows (after Phase 6 deployment):
- [x] `state_{job_id}.json` file created
- [x] JSON endpoint returns EDA data
- [x] Excel file generated with 4 sheets
- [x] Consensus analysis included (Agent 1.2)

For EXISTING workflows (before Phase 6):
- [x] JSON endpoint returns 404 (expected)
- [x] Excel endpoint returns 404 (expected)
- [x] No state file exists (expected)

---

## 🚀 Next Steps After Testing

### If All Tests Pass ✅

Phase 6 is complete and ready for production use!

**What you can do now**:
1. Run new workflows with sample files
2. Download EDA reports via API
3. Integrate EDA endpoints into frontend
4. Share EDA insights with stakeholders

### Phase 7: Frontend Integration (Future)

**Proposed enhancements**:
1. Add "Download EDA Report" button to UI
2. Display EDA summary metrics on completion screen
3. Show alignment score from consensus analysis
4. Visualize tech stack recommendations

---

## 📝 API Reference Quick Guide

### JSON Endpoint

```http
GET /api/v1/project-estimator/{job_id}/eda-report
```

**Parameters**:
- `job_id` (path): Timestamp from BRD filename (e.g., "20251126_143022")

**Response**:
- **200**: JSON with full EDA report
- **404**: No EDA report found
- **500**: Server error

### Excel Endpoint

```http
GET /api/v1/project-estimator/{job_id}/eda-report/excel
```

**Parameters**:
- `job_id` (path): Timestamp from BRD filename

**Response**:
- **200**: Excel file download
- **404**: No EDA report found
- **500**: Server error

---

## 🐛 Troubleshooting

### Issue: 404 - State file not found

**Cause**: Workflow executed before Phase 6 state-saving was added

**Solution**: Run a new workflow to generate state file

```bash
# Quick test workflow
python3 /tmp/test_simple_workflow.py
```

### Issue: 404 - No EDA report in state

**Cause**: No sample files were uploaded during workflow

**Solution**: Run workflow with sample files uploaded

### Issue: Excel file corrupt or empty

**Check**:
```bash
# Verify file size
ls -lh /tmp/EDA_Report_*.xlsx

# Try to open with openpyxl
python3 -c "import openpyxl; wb = openpyxl.load_workbook('/tmp/EDA_Report_20251126_143022.xlsx'); print(wb.sheetnames)"
```

### Issue: Backend logs show errors

**Check backend logs**:
```bash
docker-compose logs backend | grep -E "(ERROR|Exception|eda-report)" | tail -50
```

---

## 📞 Support

**Phase 6 Documentation**:
- `PHASE_6_COMPLETE_EDA_DOWNLOAD_ENDPOINTS.md` - Complete implementation details
- `PHASE_4_AGENT_12_DEBATE_COORDINATOR_COMPLETE.md` - Agent 1.2 details
- `PHASE_5_COMPLETE_BRD_ENHANCEMENT.md` - BRD enhancement details

**Related Phases**:
- Phase 1-2: EDA Analyzer Service and Tech Stack KB
- Phase 3: Agent 1.1 EDA Integration
- Phase 4: Agent 1.2 Debate Coordinator
- Phase 5: BRD Enhancement with EDA sections

---

**Testing Date**: 2025-11-26
**Status**: ✅ Phase 6 Ready for Testing
**Test Files**: Estimate One project files available
