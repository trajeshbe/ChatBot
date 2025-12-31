# Estimate One Testing Guide - Phase 3 Step 1

**Date**: 2025-11-26
**Purpose**: Test Phase 3 Step 1 (Model Selection) with real Estimate One project files

---

## Quick Start

### Option 1: Automated Test Script (Recommended)

```bash
cd /mnt/c/AIML/ClaudeCode/chatbot/ChatBot

# Run the comprehensive test
./test_estimate_one_phase3.sh
```

This script will:
1. ✅ Verify all Estimate One files exist
2. ✅ Test with explicit model selection (`llama3.2-vision:11b`)
3. ✅ Test with Model Registry fallback (no model_id)
4. ✅ Analyze backend logs for model selection
5. ✅ Generate summary report

### Option 2: Manual cURL Test

**Test 1: With Explicit Model Selection**

```bash
curl -X POST http://localhost:8000/api/v1/project-estimator/generate-agentic \
  -F "project_scope=$(cat 'docs/features/project_estimator/estimate_one/Project Scope.txt')" \
  -F "project_type=full_service" \
  -F "scenario=baseline" \
  -F "rate_config={}" \
  -F "model_id=llama3.2-vision:11b" \
  -F "brd_files=@docs/features/project_estimator/estimate_one/EstimateOne_BRD_Document.docx" \
  -F "cost_files=@docs/features/project_estimator/estimate_one/cost_estimation_estimate_one.xlsx" \
  -F "sample_data=@docs/features/project_estimator/estimate_one/Project Size Sourcing.xlsx"
```

**Expected Output:**
```
HTTP/1.1 200 OK
{
  "brd_url": "http://localhost:9000/...",
  "excel_url": "http://localhost:9000/...",
  "message": "Project estimation completed successfully"
}
```

**Test 2: Without Model ID (Model Registry Fallback)**

```bash
curl -X POST http://localhost:8000/api/v1/project-estimator/generate-agentic \
  -F "project_scope=$(cat 'docs/features/project_estimator/estimate_one/Project Scope.txt')" \
  -F "project_type=full_service" \
  -F "scenario=baseline" \
  -F "rate_config={}" \
  -F "brd_files=@docs/features/project_estimator/estimate_one/EstimateOne_BRD_Document.docx"
```

### Option 3: Python Test Script

```bash
cd /mnt/c/AIML/ClaudeCode/chatbot/ChatBot

# Inside Docker container
docker-compose exec backend python3 /workspace/test_phase3_model_selection.py
```

---

## Estimate One Project Files

Located in: `docs/features/project_estimator/estimate_one/`

### 1. Project Scope.txt (2.6 KB)

**Content**: Construction drawing data extraction project

**Key Requirements**:
- Extract levels (above/below ground) from architectural drawings
- Identify gross floor area from floor plans
- Process external area measurements
- Support multiple document types (CAD drawings, PDFs, Excel)

**Preview**:
```
Item: Levels (Above Ground)
Document Types: Architectural General Arrangement Plans / Floor Plans
Drawing Examples: A.105 - LEVEL 1 CONSTRUCTION PLAN
Identification: Count the number of Architectural General Arrangement Plans...
```

### 2. cost_estimation_estimate_one.xlsx (56 KB)

**Content**: Sample cost estimation spreadsheet

**Contains**:
- Labor cost breakdowns
- Material costs
- Resource allocation
- Timeline estimates
- Risk factors

### 3. Project Size Sourcing.xlsx (14 KB)

**Content**: Project sizing and metrics data

**Contains**:
- Square footage calculations
- Floor count analysis
- External area measurements
- Building footprint data

### 4. EstimateOne_BRD_Document.docx (31 KB)

**Content**: Sample Business Requirement Document

**Sections**:
- Project overview
- Functional requirements
- Technical specifications
- Acceptance criteria

### 5. Sampe_data/ Directory

**Content**: Full construction project ZIP (73 MB)

**Contains**:
- Complete architectural drawing set
- CAD files
- Specification documents
- Supporting materials

---

## What Phase 3 Step 1 Tests

### ✅ Test 1: Explicit Model Selection

**What it tests**:
- API endpoint accepts `model_id` parameter
- User's model choice is respected
- Model selection is logged correctly

**Expected Backend Log**:
```
INFO:     User selected model: llama3.2-vision:11b
INFO:     Starting agentic workflow execution with model: llama3.2-vision:11b...
```

### ✅ Test 2: Model Registry Fallback

**What it tests**:
- Model Registry is queried when `model_id` not provided
- Recommended model is used
- Fallback to "gpt-4" if Model Registry fails

**Expected Backend Log**:
```
INFO:     No model specified, using recommended: gpt-4
INFO:     Starting agentic workflow execution with model: gpt-4...
```

### ✅ Test 3: State Integration

**What it tests**:
- `model_id` is included in `ProjectEstimatorState`
- Workflow has access to user's model selection via `state["model_id"]`

**Code Verification**:
```python
# In workflow.py line 99
class ProjectEstimatorState(TypedDict):
    model_id: str  # ← This should exist
```

---

## Verification Commands

### Check Backend Logs

```bash
# View model selection logs
docker-compose logs backend | grep "User selected model:"

# View Model Registry fallback logs
docker-compose logs backend | grep "No model specified"
docker-compose logs backend | grep "using recommended"

# View workflow execution
docker-compose logs backend | grep "Starting agentic workflow"

# View all model-related logs (last 100 lines)
docker-compose logs backend --tail=100 | grep -i "model"
```

### Check API Health

```bash
# Verify backend is running
curl http://localhost:8000/health

# Check if endpoint exists
curl -X OPTIONS http://localhost:8000/api/v1/project-estimator/generate-agentic
```

### Inspect Response

```bash
# Save response to file for detailed inspection
curl -X POST http://localhost:8000/api/v1/project-estimator/generate-agentic \
  -F "project_scope=$(cat 'docs/features/project_estimator/estimate_one/Project Scope.txt')" \
  -F "project_type=full_service" \
  -F "scenario=baseline" \
  -F "rate_config={}" \
  -F "model_id=llama3.2-vision:11b" \
  > /tmp/estimate_one_response.json

# Pretty print the response
cat /tmp/estimate_one_response.json | jq '.'
```

---

## Expected Results

### Successful Test Output

```
================================================================================
🧪 PHASE 3 STEP 1 TEST: Estimate One Project with Model Selection
================================================================================

📂 Step 1: Verifying Estimate One project files...
✅ Project Scope.txt found (2648 bytes)
✅ cost_estimation_estimate_one.xlsx found (57344 bytes)
✅ Project Size Sourcing.xlsx found (14336 bytes)
✅ EstimateOne_BRD_Document.docx found (31744 bytes)

================================================================================
🚀 Step 2: Testing with EXPLICIT model selection (llama3.2-vision:11b)
================================================================================

📝 Project Scope Preview (first 200 chars):
Item	Value	Document Types	Drawing No. & Name	Field Locations	Identification Methods
Levels (Above Ground)	Number	"Option 1: Architectural General Arrangement Plans / Floor Plans...

🔧 Sending request with model_id=llama3.2-vision:11b...

📊 Response Status: 200

✅ Request successful with explicit model selection!

Response preview (first 500 chars):
{"brd_url":"http://localhost:9000/project-estimator/...", "excel_url":"..."}

📋 Checking backend logs for model selection...
INFO:     User selected model: llama3.2-vision:11b

================================================================================
🚀 Step 3: Testing WITHOUT model_id (Model Registry fallback)
================================================================================

📊 Response Status: 200

✅ Request successful with Model Registry fallback!

📋 Checking backend logs for Model Registry fallback...
INFO:     No model specified, using recommended: gpt-4

================================================================================
✅ PHASE 3 STEP 1 VALIDATION COMPLETE
================================================================================

Summary:
  ✅ Test 1: Explicit model selection (llama3.2-vision:11b) - PASSED
  ✅ Test 2: Model Registry fallback - PASSED
  ✅ Real Estimate One files processed successfully
  ✅ model_id parameter integration verified
```

---

## Troubleshooting

### Problem: Files Not Found

**Error**: `❌ Project Scope.txt not found`

**Solution**:
```bash
# Verify you're in the correct directory
cd /mnt/c/AIML/ClaudeCode/chatbot/ChatBot

# Check if files exist
ls -lh docs/features/project_estimator/estimate_one/

# Check file paths in script
cat test_estimate_one_phase3.sh | grep "ESTIMATE_ONE_DIR"
```

### Problem: Backend Not Running

**Error**: `Connection refused`

**Solution**:
```bash
# Check if backend is running
docker-compose ps

# Start backend if not running
docker-compose up -d backend

# Check backend logs for errors
docker-compose logs backend --tail=50
```

### Problem: No Model Selection Logs

**Error**: No logs found with "User selected model"

**Solution**:
```bash
# Check if recent requests were made
docker-compose logs backend --tail=500 | grep "generate-agentic"

# Check if model_id parameter was received
docker-compose logs backend --tail=500 | grep "model"

# Verify the implementation
grep -n "model_id" backend/app/api/routes/project_estimator_routes.py
```

### Problem: HTTP 422 or 500 Error

**Error**: Response status is 422 (validation error) or 500 (server error)

**Solution**:
```bash
# Check detailed error in response
curl -v -X POST http://localhost:8000/api/v1/project-estimator/generate-agentic \
  -F "project_scope=test" \
  -F "project_type=full_service" \
  -F "scenario=baseline" \
  -F "rate_config={}"

# Check backend error logs
docker-compose logs backend --tail=100 | grep -E "(ERROR|Exception)"

# Verify database connection
docker-compose exec postgres psql -U postgres -c "SELECT 1"
```

---

## Next Steps After Testing

Once Phase 3 Step 1 tests pass successfully:

### 1. Document Results
- Save test output to file
- Note any warnings or issues
- Record model selection behavior

### 2. Proceed to Phase 3 Step 2
- Create `_call_llm_optimized()` helper method
- Implement prompt template selection
- Add text compression logic
- Use `state["model_id"]` instead of hardcoded values

### 3. Update Frontend (Phase 3 Step 13)
- Integrate ModelSelector dropdown
- Send `model_id` from frontend
- Display selected model in UI

---

## Related Documentation

- **PHASE_3_MODEL_SELECTION_IMPLEMENTED.md** - Implementation details
- **PHASE_3_STEP_1_TESTING_SUMMARY.md** - Testing guide
- **PHASE_3_INTEGRATION_PLAN.md** - Overall Phase 3 plan
- **test_phase3_model_selection.py** - Python test script

---

**Created**: 2025-11-26
**Status**: Ready for testing with Estimate One files
**Phase**: 3 Step 1 - Model Selection Integration ✅
