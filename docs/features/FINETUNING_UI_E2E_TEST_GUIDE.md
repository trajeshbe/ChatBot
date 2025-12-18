# Fine-Tuning System - UI End-to-End Testing Guide

**Test Date**: 2025-12-15
**Frontend URL**: http://localhost:3001/admin
**Backend URL**: http://localhost:8000

---

## Prerequisites Completed ✅

- ✅ Qwen 2.5 1.5B added to base models
- ✅ Backend running successfully
- ✅ Frontend compiled (2026 modules)
- ✅ Training dataset created: `/tmp/cloudsync_support_qa.jsonl`
- ✅ Base model tested via API
- ✅ Fine-tuned model deployed to Ollama: `cloudsync-qa-v1:latest`

---

## UI End-to-End Test Checklist

### Phase 1: Access & Navigation ✅

**Step 1: Access Frontend**
1. Open browser and navigate to: **http://localhost:3001/admin**
2. You should see the Admin Dashboard

**Expected Result**:
- Admin dashboard loads
- Sidebar menu visible with navigation options

**Step 2: Navigate to Fine-Tuning**
1. Look for "Fine-Tuning" in the sidebar menu
2. Click on "Fine-Tuning" to expand submenu

**Expected Result**:
- Fine-Tuning submenu expands showing tabs:
  - Training Jobs
  - Evaluations
  - Monitoring
  - Governance

---

### Phase 2: Dataset Management 📁

**Step 3: Upload Dataset**
1. Navigate to **Fine-Tuning → Training Jobs**
2. Look for "Upload Dataset" or "New Dataset" button
3. Click the button to open upload form

**Form Fields**:
- Dataset Name: `CloudSync Support QA`
- Format Type: `qa` (Question-Answer)
- Training Objective: `question_answering`
- File: Upload `/tmp/cloudsync_support_qa.jsonl`
- Column Mappings (optional): Leave default

4. Click "Upload" button

**Expected Result**:
- ✅ Dataset upload success message
- Dataset appears in datasets list with status "validating" → "validated"
- Dataset ID generated
- Row count shows: 20 rows
- Quality metrics displayed

**API Endpoint Called**:
```
POST /api/v1/finetuning/datasets/upload
```

**Verification**:
- Check dataset appears in list
- Status shows "completed" or "validated"
- Download sample button works (if available)

---

### Phase 3: Base Model Selection 🔍

**Step 4: Check Base Models**
1. Look for "Create Training Job" or "New Job" button
2. Click to open job creation form
3. Find "Base Model" dropdown

**Expected Result**:
- ✅ Dropdown shows multiple base models
- **Qwen2.5-1.5B-Instruct** should be FIRST in the list
- Model shows:
  - Name: Qwen2.5-1.5B-Instruct
  - Size: 1.5B
  - VRAM: 2GB (QLoRA)
  - Tags: fast, lightweight, multilingual
  - Recommended: ✅ Yes

**API Endpoint Called**:
```
GET /api/v1/finetuning/base-models
```

**Verification**:
- Qwen 2.5 1.5B appears in dropdown
- Model details display correctly
- QLoRA compatibility shown

---

### Phase 4: Training Job Creation 🚀

**Step 5: Create Training Job**
1. Fill out training job form:

**Basic Information**:
- Job Name: `cloudsync-qa-qwen-1.5b-test`
- Description: `Testing CloudSync Pro support QA fine-tuning`
- Base Model: Select **Qwen2.5-1.5B-Instruct**
- Dataset: Select `CloudSync Support QA` (from Step 3)
- Fine-Tuning Method: Select **QLoRA**

**Training Configuration**:
- Learning Rate: `0.0002` (default)
- Batch Size: `4`
- Number of Epochs: `3`
- Warmup Steps: `100`
- LoRA Rank (r): `16`
- LoRA Alpha: `32`
- LoRA Dropout: `0.05`

2. Click "Create Job" or "Submit" button

**Expected Result**:
- ✅ Job created successfully
- Job ID displayed
- Job appears in "Training Jobs" list
- Status shows "queued" or "pending"
- GPU allocation request initiated

**API Endpoint Called**:
```
POST /api/v1/finetuning/jobs
```

**Verification**:
- Job appears in jobs list
- Job status updates (queued → running → completed)
- Job details page accessible

---

### Phase 5: Monitor Training Progress 📊

**Step 6: Access Monitoring Dashboard**
1. Navigate to **Fine-Tuning → Monitoring**
2. Dashboard should load with real-time metrics

**Expected Components**:

**A. Statistics Cards**:
- ✅ Running Jobs: Should show 1 (if job is running)
- ✅ Pending Approvals: Count of registered models
- ✅ Active Models: Count of deployed models
- ✅ Datasets Ready: Should show 1 (CloudSync QA dataset)

**B. GPU Utilization Chart**:
- ✅ Pie chart showing allocated vs available GPUs
- Total GPUs displayed
- Color-coded visualization

**C. Cost Tracking Panel**:
- ✅ Total GPU Hours
- ✅ Estimated Cost (USD)
- ✅ Storage Used (GB)
- ✅ Active Cost/Hour

**D. Training Metrics Charts**:
- ✅ **Loss Over Time**: Area chart (red gradient)
- ✅ **Accuracy Over Time**: Line chart (green)
- Shows step, epoch, and metric values
- Custom tooltips with details

**E. System Health Indicators**:
- ✅ Training Pipeline: Active/Idle status
- ✅ GPU Pool: Healthy/Warning
- ✅ Model Drift: Warnings if any

**F. Auto-Refresh Toggle**:
- ✅ Toggle button to enable/disable auto-refresh
- Refreshes every 5 seconds when ON

**API Endpoints Called**:
```
GET /api/v1/finetuning/stats
GET /api/v1/finetuning/gpu/stats
GET /api/v1/finetuning/jobs?limit=10
GET /api/v1/finetuning/jobs/{job_id}/metrics
```

**Verification**:
- All charts render without errors
- Data populates correctly
- Auto-refresh works
- No console errors

---

### Phase 6: Model Evaluation 🎯

**Step 7: Access Evaluation Hub**
1. Navigate to **Fine-Tuning → Evaluations**
2. Wait for job to complete and model to be registered

**Expected Components**:

**A. Model List Table**:
- ✅ Columns: Checkbox, Name, Version, Base Model, Method, Status, Metrics, Actions
- Models displayed with:
  - Name
  - Version (e.g., 1.0.0)
  - Base Model (qwen-2.5-1.5b)
  - Method (qlora)
  - Status (registered/approved/deployed)
  - Evaluation metrics (if run)

**B. Selection & Comparison**:
1. Select up to 3 models using checkboxes
2. "Compare Selected" button should enable
3. Click "Compare Selected"

**Expected Result**:
- ✅ Comparison panel opens
- Shows side-by-side view of selected models
- Test prompt input field
- "Run Comparison" button

**C. Test Comparison**:
1. Enter test prompt: `How do I reset my CloudSync Pro password?`
2. Click "Run Comparison"

**Expected Result**:
- ✅ Each model generates a response
- Responses displayed side-by-side
- Latency shown for each model
- Token usage displayed
- Color-coded performance indicators

**D. Trigger Evaluation**:
1. Find a model in the list
2. Click "Evaluate" button

**Expected Result**:
- ✅ Evaluation job starts
- Progress indicator shows
- Metrics update when complete:
  - Accuracy
  - Perplexity
  - ROUGE-1, ROUGE-2, ROUGE-L
  - BLEU Score
  - F1 Score
- Color-coded metrics (green/yellow/red)

**E. Deploy to Ollama Button**:
1. Find a model with status "registered" or "approved"
2. Click "Deploy to Ollama" button

**Expected Result**:
- ✅ Confirmation dialog appears
- Click "Confirm"
- Deployment starts (loading state)
- Success message on completion
- Model status changes to "deployed"
- Ollama model name displayed (e.g., `cloudsync-qa-v1.0.0`)
- "Undeploy" button appears

**F. Undeploy Button**:
1. Click "Undeploy" button on deployed model

**Expected Result**:
- ✅ Confirmation dialog
- Model removed from Ollama
- Status changes back to "registered"
- Deploy button reappears

**API Endpoints Called**:
```
GET /api/v1/finetuning/models
POST /api/v1/finetuning/models/{id}/evaluate
POST /api/v1/finetuning/models/inference
POST /api/v1/finetuning/models/{id}/deploy
POST /api/v1/finetuning/models/{id}/undeploy
```

**Verification**:
- All buttons work
- Deployment succeeds
- Metrics display correctly
- Comparison works
- No console errors

---

### Phase 7: Governance & Audit 🛡️

**Step 8: Access Governance Tab**
1. Navigate to **Fine-Tuning → Governance**

**Expected Components**:

**A. Pending Model Approvals**:
- ✅ Section header: "Pending Model Approvals" with count badge
- List of models with status "registered"
- For each model:
  - Name, version, base model
  - Registration date
  - Evaluation metrics (if available)
  - "View Lineage" button
  - Approval notes textarea
  - "Approve" button (green)
  - "Reject" button (red)

**B. Model Approval Workflow**:
1. Find a pending model
2. Enter approval notes in textarea: `Tested on CloudSync QA dataset. Metrics meet requirements. Approved for production.`
3. Click "Approve" button

**Expected Result**:
- ✅ Success message
- Model status changes to "approved"
- Model disappears from pending list
- Audit log entry created
- Approval metadata stored

**C. Model Rejection Workflow**:
1. Click "Reject" button on a model
2. Enter rejection reason in prompt: `Accuracy below production threshold. Needs retraining.`
3. Confirm rejection

**Expected Result**:
- ✅ Model status changes to "rejected"
- Model disappears from pending list
- Rejection recorded in audit log

**D. Model Lineage Viewer**:
1. Click "View Lineage" on any model
2. Lineage panel opens

**Expected Result**:
- ✅ **Visual Flow Diagram**:
  ```
  Dataset → Training → Model → Deployment
  (blue)    (green)    (purple) (orange)
  ```
- Each stage shows:
  - Icon representation
  - Status indicator (color-coded)
  - Key details

**Lineage Details**:
- **Dataset Section**:
  - Dataset name
  - Format type
  - Row count
  - Validation status
  - Upload date

- **Training Job Section**:
  - Job name
  - Job status
  - GPU allocated
  - Training steps (current/total)
  - Start/completion times

- **Model Section**:
  - Model name and version
  - Base model
  - Fine-tuning method
  - Evaluation metrics
  - Created/updated dates

- **Deployment Section** (if deployed):
  - Deployment target (Ollama)
  - Deployed model name
  - Deployment URL
  - Deployed date

- **Approval History**:
  - Timeline of approvals/rejections
  - Approver name
  - Approval/rejection date
  - Notes or reasons

**E. Download Compliance Report**:
1. Click "Download Report" button on lineage viewer

**Expected Result**:
- ✅ JSON file downloads
- Filename: `compliance-report-{model-name}-{version}.json`
- Contains complete lineage data:
  - Model details
  - Training provenance
  - Data source
  - Deployment info
  - Approval chain

**F. Audit Trail**:
- ✅ Section showing all fine-tuning activities
- Filter dropdown: All Actions, Create, Approve, Reject, Deploy
- For each audit log entry:
  - Action icon (color-coded)
  - Description
  - Timestamp
  - Action type badge
  - Resource type badge
  - Expandable details (click to view JSON)

**G. Audit Trail Filtering**:
1. Select "Approve" from filter dropdown

**Expected Result**:
- ✅ List filters to show only approval actions
- Other actions hidden
- Count updates

**H. Expandable Log Details**:
1. Click on any audit log entry

**Expected Result**:
- ✅ Details panel expands
- Shows full JSON of `details` field
- Formatted for readability

**API Endpoints Called**:
```
GET /api/v1/finetuning/models?status=registered
POST /api/v1/finetuning/models/{id}/approve
POST /api/v1/finetuning/models/{id}/reject
GET /api/v1/finetuning/models/{id}/lineage
GET /api/v1/finetuning/audit/logs?action=...
```

**Verification**:
- Approval workflow works
- Lineage displays correctly
- Audit trail updates
- Filtering works
- Download works
- No console errors

---

### Phase 8: Complete Workflow Test 🔄

**Step 9: End-to-End Workflow**
Execute complete workflow from start to finish:

1. ✅ **Upload Dataset** → CloudSync QA dataset
2. ✅ **Create Job** → QLoRA training on Qwen 1.5B
3. ✅ **Monitor Training** → Watch metrics in Monitoring Dashboard
4. ✅ **Evaluate Model** → Run evaluation in Evaluation Hub
5. ✅ **Compare Models** → Side-by-side comparison with base model
6. ✅ **Review for Approval** → Check in Governance tab
7. ✅ **View Lineage** → Verify complete data lineage
8. ✅ **Approve Model** → Enter notes and approve
9. ✅ **Deploy to Ollama** → Click deploy button
10. ✅ **Verify Deployment** → Check model in Ollama
11. ✅ **Test Deployed Model** → Run inference
12. ✅ **Monitor Post-Deployment** → Check monitoring dashboard
13. ✅ **Audit Trail** → Verify all actions logged

---

## Testing Matrix

### Browser Compatibility
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari
- [ ] Edge

### Features to Verify

| Feature | Component | Status |
|---------|-----------|--------|
| Dataset Upload | Training Jobs | ⬜ |
| Base Model Dropdown | Training Jobs | ⬜ |
| Job Creation | Training Jobs | ⬜ |
| Real-time Metrics | Monitoring | ⬜ |
| GPU Utilization Chart | Monitoring | ⬜ |
| Cost Tracking | Monitoring | ⬜ |
| Loss Chart | Monitoring | ⬜ |
| Accuracy Chart | Monitoring | ⬜ |
| Auto-refresh Toggle | Monitoring | ⬜ |
| Model List | Evaluations | ⬜ |
| Model Selection | Evaluations | ⬜ |
| Side-by-side Comparison | Evaluations | ⬜ |
| Evaluation Trigger | Evaluations | ⬜ |
| Deploy to Ollama | Evaluations | ⬜ |
| Undeploy | Evaluations | ⬜ |
| Pending Approvals | Governance | ⬜ |
| Approve Model | Governance | ⬜ |
| Reject Model | Governance | ⬜ |
| View Lineage | Governance | ⬜ |
| Download Report | Governance | ⬜ |
| Audit Trail | Governance | ⬜ |
| Audit Filtering | Governance | ⬜ |

---

## Expected Console Output (No Errors)

When testing in browser with DevTools open (F12):

**✅ Good Output**:
```
✓ Compiled /admin in 2.8s
✓ Ready in 1404ms
200 GET /api/v1/finetuning/models
200 GET /api/v1/finetuning/stats
200 POST /api/v1/finetuning/datasets/upload
```

**❌ Bad Output (Should NOT see)**:
```
❌ 500 Internal Server Error
❌ TypeError: Cannot read property...
❌ Network Error
❌ CORS Error
❌ Failed to fetch
```

---

## Common Issues & Solutions

### Issue: Dataset upload fails
**Solution**: Check file format is JSONL, check file size, verify backend logs

### Issue: Training job not starting
**Solution**: Check GPU pool status, verify dataset is validated, check backend logs

### Issue: Charts not loading
**Solution**: Check API endpoints return data, verify recharts library loaded, check console for errors

### Issue: Deploy button not working
**Solution**: Verify Ollama service running, check model status is "registered" or "approved"

### Issue: Approval workflow not saving
**Solution**: Check approval notes field is filled, verify authentication token, check network tab

---

## Performance Benchmarks

**Expected Load Times**:
- Admin page: < 3 seconds
- Monitoring dashboard: < 2 seconds
- Evaluation hub: < 2 seconds
- Governance tab: < 2 seconds
- Chart rendering: < 1 second
- API responses: < 500ms

**Expected Memory Usage**:
- Frontend: < 200MB
- Backend: < 500MB (idle)
- Backend: < 2GB (training active)

---

## Quick Verification Commands

Run these in terminal while testing UI:

```bash
# Check if frontend is accessible
curl -s http://localhost:3001/admin -I | grep "200 OK"

# Check if backend API is responsive
curl -s http://localhost:8000/health | jq .

# Check base models endpoint
curl -s http://localhost:8000/api/v1/finetuning/base-models | jq '.models[] | .name'

# Verify Qwen 1.5B is in list
curl -s http://localhost:8000/api/v1/finetuning/base-models | jq '.models[] | select(.id=="qwen-2.5-1.5b")'

# Check Ollama models
docker exec rag-ollama ollama list

# Monitor backend logs
docker-compose logs -f backend --tail=50

# Monitor frontend logs
docker-compose logs -f frontend --tail=50
```

---

## Success Criteria

✅ **UI Test PASSES if**:
- All components render without errors
- All buttons and forms work
- API calls succeed (200 responses)
- Data displays correctly
- Charts render properly
- Deployment succeeds
- Approval workflow completes
- Audit trail updates
- No console errors
- No network errors

❌ **UI Test FAILS if**:
- Components fail to render
- Buttons don't respond
- API calls fail (500 errors)
- Data doesn't display
- Charts don't render
- Console shows errors
- Network errors occur

---

## Test Report Template

After testing, fill out:

**Tester**: ___________
**Date**: ___________
**Browser**: ___________
**Overall Status**: PASS / FAIL

**Components Tested**:
- [ ] Training Jobs: PASS / FAIL
- [ ] Monitoring: PASS / FAIL
- [ ] Evaluations: PASS / FAIL
- [ ] Governance: PASS / FAIL

**Issues Found**:
1.
2.
3.

**Screenshots**: Attach screenshots of each tab

**Recommendations**:
-
-

---

**Guide Created**: 2025-12-15
**Frontend**: http://localhost:3001/admin
**Backend**: http://localhost:8000
**Status**: Ready for UI testing
