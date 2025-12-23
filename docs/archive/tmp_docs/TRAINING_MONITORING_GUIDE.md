# Training Job Monitoring and One-Click Deployment Test

**Date**: 2025-12-23 07:07 UTC
**Training Job**: `choles-qa-real-training51`
**Job ID**: `d908cd79-da54-4e0b-9694-f6cfc6349aac`
**Status**: Running (created at 07:06:53)

---

## Current Status

Your training job was successfully created and is showing status "running" in the database.

### Job Configuration
- **Name**: choles-qa-real-training51
- **Base Model**: Qwen/Qwen2.5-1.5B-Instruct
- **Dataset**: qwen_test_dataset (10 samples)
- **Hyperparameters**:
  - Learning Rate: 0.0002
  - Epochs: 3
  - Batch Size: 4
  - LoRA rank: 16
  - LoRA alpha: 32
  - Max sequence length: 2048

### Expected Timeline
- **Training**: 5-10 minutes (10 samples, 3 epochs)
- **Total**: Should complete by ~07:17 UTC

---

## How to Monitor Training

### Method 1: Database Checks

```bash
# Check job status
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT id, name, status, progress FROM finetuning_jobs \
   WHERE id = 'd908cd79-da54-4e0b-9694-f6cfc6349aac';"

# Expected output when complete:
# status: completed
# progress: 100
```

### Method 2: Check for Generated Model

```bash
# Check if LoRA adapter was created
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT id, name, status FROM finetuned_models \
   WHERE training_job_id = 'd908cd79-da54-4e0b-9694-f6cfc6349aac';"

# Expected: A model with status 'registered' or 'adapter_only'
```

### Method 3: Check Celery Worker Logs

```bash
docker-compose logs --tail=100 celery-worker | grep -E "(choles-qa-real-training51|Task|ERROR)"
```

### Method 4: Check Training Artifacts

```bash
ls -lh /workspace/finetuning/d908cd79-da54-4e0b-9694-f6cfc6349aac/output/adapter_model/ 2>/dev/null || echo "Not yet created"

# When ready, should show ~8.4 MB of files
```

---

## When Training Completes

### Expected Artifacts

```
/workspace/finetuning/d908cd79-da54-4e0b-9694-f6cfc6349aac/
├── output/
│   └── adapter_model/          # ~8.4 MB LoRA adapter
│       ├── adapter_config.json
│       ├── adapter_model.safetensors
│       └── ...
```

### Database Updates

**finetuning_jobs table**:
- status: 'completed'
- progress: 100

**finetuned_models table** (new row created):
- name: `choles-qa-real-training51_model`
- status: 'registered' or 'approved' or 'adapter_only'
- training_job_id: `d908cd79-da54-4e0b-9694-f6cfc6349aac`

---

## Testing One-Click Deployment

### Step 1: Navigate to Governance & Audit UI

1. Open browser: `http://localhost:3001`
2. Click **"Governance & Audit"** tab in top navigation

### Step 2: Find Your Model

Look for a model card with:
- **Name**: `choles-qa-real-training51_model`
- **Base Model**: Qwen/Qwen2.5-1.5B-Instruct
- **Status**: registered/approved
- Should appear in "Pending Approvals" section

### Step 3: Locate Quick Deployment Section

You should see a beautiful UI section with:
- **Gradient purple/indigo background** (`from-indigo-50 to-purple-50`)
- **Header**: "⚡ Quick Deployment"
- **Description**: "Approve → Merge → Deploy to Ollama in one click (takes 5-15 min)"
- **Button**: "Quick Deploy" or "Merge and Deploy"

**Example UI (from code)**:
```
┌─────────────────────────────────────────────────┐
│ ⚡ Quick Deployment                             │
│ Approve → Merge → Deploy to Ollama in one      │
│ click (takes 5-15 min)                          │
│                                                 │
│ [  Quick Deploy  ]  ← Click this button        │
└─────────────────────────────────────────────────┘
```

### Step 4: Click "Quick Deploy"

When you click the button, you should see:

**Real-time Progress**:
```
⏳ Step 1: Approve Model
   Status: Approving...

⏳ Step 2: Merge LoRA Adapter (5-15 min)
   Status: Merging adapter into base model...

⏳ Step 3: Deploy to Ollama
   Status: Converting to GGUF and deploying...
```

**Expected Duration**: 10-20 minutes total

### Step 5: Monitor Backend Logs (Optional)

```bash
docker-compose logs -f backend | grep -E "(🚀|Deploy|merge|GGUF|Ollama|✅|❌)"
```

Expected log sequence:
```
📦 Detected LoRA adapter - merge required for Ollama
🔄 Merging adapter into base model...
✅ Merge complete: 2.9 GB
🔄 Converting to GGUF f16...
✅ GGUF conversion successful: 3.1 GB
🚀 Deploying to Ollama: choles-qa-real-training51_model-v1
✅ Ollama deployment successful
```

### Step 6: Verify Deployment Success

**In UI**:
- Status changes to "✅ Deployment Complete!"
- Model disappears from "Pending Approvals" section
- Check "Audit Logs" tab for deployment record

**In Database**:
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT name, status, ollama_model_name FROM finetuned_models \
   WHERE training_job_id = 'd908cd79-da54-4e0b-9694-f6cfc6349aac';"

# Expected:
# status: deployed
# ollama_model_name: choles-qa-real-training51_model-v1
```

**In Ollama**:
```bash
docker-compose exec ollama ollama list | grep choles-qa-real-training51

# Expected:
# choles-qa-real-training51_model-v1    <hash>    3.1 GB    X minutes ago
```

### Step 7: Verify in Chat UI

1. Go to **"Chat"** tab
2. Click **refresh icon** next to model dropdown (important!)
3. Look for: `choles-qa-real-training51_model-v1`
4. Select the model from dropdown
5. Test with a question related to your training data

### Step 8: Test Inference

**Via Chat UI**:
Type any test question and send

**Via CLI**:
```bash
docker-compose exec ollama ollama run choles-qa-real-training51_model-v1 \
  "What is Choles Food Technologies?"
```

Expected: Model responds with information from training dataset

---

## Troubleshooting

### Issue: Training job stuck at status "running" with progress 0

**Check**:
```bash
# Check Celery worker health
docker-compose ps | grep celery-worker

# Check Celery worker logs
docker-compose logs --tail=50 celery-worker
```

**Solution**:
```bash
# Restart Celery worker if unhealthy
docker-compose restart celery-worker
```

### Issue: Model doesn't appear in Governance UI

**Check**:
```bash
# Check if model was created
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT id, name, status FROM finetuned_models \
   WHERE training_job_id = 'd908cd79-da54-4e0b-9694-f6cfc6349aac';"
```

**Solution**: Refresh browser, check that model status is 'registered', 'approved', or 'adapter_only'

### Issue: Quick Deploy button not visible

**Check**: Frontend code should already have it (GovernanceAudit.tsx:315-387)

**Solution**:
1. Hard refresh browser (Ctrl+Shift+R)
2. Check browser console for errors
3. Verify frontend is running: `docker-compose ps | grep frontend`

### Issue: Deployment fails with "Ollama deployment failed"

**Check previous session fixes**:
- transformers >= 4.40.0 (Qwen2 support)
- peft >= 0.18.0 (ALoRA support)

**Verify**:
```bash
docker-compose exec backend pip show transformers peft | grep Version
```

**Solution**: If versions are wrong, backend needs rebuild (see `/tmp/FINAL_SUCCESS_SUMMARY.md`)

### Issue: Model doesn't appear in Chat UI dropdown

**Solution**: Click the **refresh icon** next to model dropdown

**Future Enhancement**: Add polling to auto-detect new models (currently manual refresh required)

---

## Success Criteria Checklist

When you complete the test, verify ALL of these:

- [ ] Training completes without errors (status = 'completed')
- [ ] LoRA adapter is generated (~8 MB)
- [ ] Model appears in Governance & Audit UI
- [ ] "Quick Deploy" button is visible in gradient purple section
- [ ] Clicking button shows real-time progress (3 steps)
- [ ] Deployment completes successfully (10-20 minutes)
- [ ] Merged model is created (2.9 GB)
- [ ] GGUF file is created (3.1 GB f16)
- [ ] Model is deployed to Ollama
- [ ] Database status updates to 'deployed'
- [ ] Model appears in Chat UI dropdown (after refresh)
- [ ] Model responds to inference queries

---

## Reference Documentation

All comprehensive docs created for you:

1. **`/tmp/E2E_NEW_MODEL_TEST_GUIDE.md`** - Complete end-to-end testing guide with both UI and API methods
2. **`/tmp/ONE_CLICK_DEPLOYMENT_COMPLETE_SUMMARY.md`** - Full implementation details showing all code is already complete
3. **`/tmp/ONE_CLICK_DEPLOYMENT_IMPLEMENTATION.md`** - Original implementation plan from previous session
4. **`/tmp/FINAL_SUCCESS_SUMMARY.md`** - Previous session's complete success with choles-qa-ft model
5. **`/tmp/TRAINING_MONITORING_GUIDE.md`** - This document

---

## Next Steps

### Immediate (Now)
1. Wait for training to complete (~5-10 minutes from 07:06:53)
2. Check database for completion status
3. Navigate to Governance & Audit UI
4. Test one-click deployment

### After Successful Test
1. Document any UI issues or improvements needed
2. Test with larger datasets (100+ samples)
3. Test with different base models
4. Evaluate model quality vs base model
5. Share feedback on the one-click deployment UX

---

## Key Files (For Reference)

**Frontend**:
- `frontend/src/components/finetuning/GovernanceAudit.tsx` (Lines 315-387): Quick Deployment UI
- `frontend/src/components/finetuning/MergeAndDeployButton.tsx` (Lines 1-513): Complete workflow logic

**Backend**:
- `backend/app/services/finetuning/model_registry_service.py` (Lines 611-624): Database status update
- `backend/app/services/ollama_deployment_service.py`: Merge + GGUF + Ollama deployment
- `backend/app/api/routes/finetuning_routes.py`: `/models-public/{id}/deploy` endpoint

---

**Last Updated**: 2025-12-23 07:10 UTC
**Training Started**: 2025-12-23 07:06:53
**Expected Completion**: ~07:17 UTC
**Status**: MONITORING - Ready to test one-click deployment when training completes

---

**Good luck with your test!** The one-click deployment feature is fully implemented and ready to use. Just waiting for training to finish.
