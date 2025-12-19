# MinIO Checkpoint Upload and Deployment Fix

**Date**: 2025-12-19
**Status**: ✅ COMPLETE - Ready for testing
**Issue**: Model checkpoints were not being uploaded to MinIO, causing deployment failures

---

## 🐛 Problem Summary

### Issue Discovered
During the previous session, we found that fine-tuning model checkpoints were NOT being uploaded to MinIO despite the upload logic existing. This caused:
1. ❌ Model deployments to fail (Ollama couldn't access checkpoints)
2. ❌ `minio_checkpoint_path` in database showing local paths instead of MinIO URLs
3. ❌ Models deployed with base weights only, not fine-tuned weights

### Root Cause Analysis

**Path Mismatch in Celery Worker**:
- Training saves checkpoints to: `/workspace/finetuning/{job_id}/output` (via Docker volume)
- Celery task looked for: `/workspace/output/{job_id}/checkpoints` ❌ **WRONG PATH!**
- Result: `upload_checkpoints_to_minio()` failed silently (directory not found)

**Deployment Issue**:
- OllamaDeploymentService expected local filesystem paths
- MinIO URLs (minio://bucket/path) were not supported
- Result: Even if upload succeeded, deployment couldn't access MinIO files

---

## 🔧 Fixes Implemented

### Fix 1: Correct Checkpoint Path in Celery Task

**File**: `backend/app/tasks/finetuning_tasks.py`

**Change** (lines 680-682):
```python
# BEFORE (Wrong path from config)
checkpoint_dir = training_config["checkpoint_dir"]  # /workspace/output/{job_id}/checkpoints

# AFTER (Actual path from sandbox manager result)
checkpoint_dir = result.get("checkpoint_path") or training_config["output_dir"]
logger.info(f"Checkpoint directory for upload: {checkpoint_dir}")
```

**Why**: The sandbox manager returns the actual checkpoint location in `result["checkpoint_path"]` which is `/workspace/finetuning/{job_id}/output`. Using this ensures we look in the right place.

---

### Fix 2: MinIO Download Support in Deployment Service

**File**: `backend/app/services/ollama_deployment_service.py`

#### Added MinIO Download Method (lines 79-155):
```python
async def _download_from_minio(self, minio_url: str) -> Optional[str]:
    """
    Download model checkpoints from MinIO to local temporary directory

    Args:
        minio_url: MinIO URL in format minio://bucket/path/to/checkpoint

    Returns:
        Local path to downloaded checkpoint directory, or None if failed
    """
    # Parse minio://bucket/path format
    # Download all checkpoint files recursively
    # Return local temporary directory path
```

**Features**:
- Parses `minio://bucket/path` URLs
- Downloads entire checkpoint directory recursively
- Maintains directory structure
- Creates temporary directory for Ollama access

#### Updated Deploy Method (lines 43-49):
```python
# Download from MinIO if needed
local_model_path = model_path
if model_path.startswith("minio://"):
    logger.info(f"Downloading model from MinIO: {model_path}")
    local_model_path = await self._download_from_minio(model_path)
    if not local_model_path:
        raise RuntimeError(f"Failed to download model from MinIO: {model_path}")
```

**Why**: Ollama needs local filesystem access. This downloads checkpoints from MinIO before deployment.

---

## 🏗️ Architecture

### Training → Upload → Deploy Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. TRAINING (in GPU container)                                          │
│    - Saves checkpoints to: /workspace/finetuning/{job_id}/output       │
│    - Docker volume: chatbot_finetuning_workspaces                       │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. CHECKPOINT UPLOAD (Celery worker)                                    │
│    - Reads from: /workspace/finetuning/{job_id}/output ✅ FIXED         │
│    - Uploads to: minio://documents/{dept}/{team}/{project}/{user}/...   │
│    - Path format: .../finetuning/datasets/{dataset}/checkpoints/...     │
│    - Updates DB: job.minio_checkpoint_path = "minio://..."             │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. MODEL REGISTRATION (Celery worker)                                   │
│    - Creates FineTunedModel record                                      │
│    - Sets minio_checkpoint_path from job                                │
│    - Status: "registered" → ready for approval                          │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 4. APPROVAL (UI)                                                         │
│    - Admin approves model in Governance tab                             │
│    - Status: "registered" → "approved"                                  │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 5. DEPLOYMENT (Backend API + Ollama)                                    │
│    - Downloads from minio://... to /tmp/ollama_model_xxx ✅ NEW         │
│    - Generates Modelfile with merged model                              │
│    - Calls Ollama HTTP API: POST /api/create                            │
│    - Updates DB: status="deployed", ollama_model_name="xxx"            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 MinIO Path Structure

### Dataset Path (Already Implemented)
```
documents/
  technology/
    backend-development/
      global/
        admin/
          finetuning/
            datasets/
              story8/
                {dataset_id}/
                  simple_extended_story_question_answers_for_rag.csv
```

### Checkpoint Path (Now Being Uploaded)
```
documents/
  technology/
    backend-development/
      global/
        admin/
          finetuning/
            datasets/
              story8/
                checkpoints/
                  short_story_6/              ← job_name
                    {job_id}/
                      final/
                        adapter_model/
                          adapter_config.json
                          adapter_model.safetensors
                        merged_model/
                          config.json
                          model.safetensors
                          tokenizer.json
                          tokenizer_config.json
                        config/
                          training_args.bin
```

---

## 🧪 Testing Instructions

### Test 1: Verify Checkpoint Upload (NEW Training Job)

**Note**: Existing models won't benefit from this fix. You need to train a NEW model.

1. **Navigate to Fine-Tuning Hub** → **Jobs** tab
2. **Create a new training job**:
   - Name: "test_minio_upload"
   - Base Model: "Qwen/Qwen2.5-1.5B-Instruct" (faster)
   - Dataset: Use existing "story8" dataset
   - Method: PEFT (LoRA)
   - Epochs: 1 (for quick testing)

3. **Submit the job** and wait for training to complete

4. **Check Celery worker logs** for upload confirmation:
   ```bash
   docker-compose logs -f celery-worker | grep -i "upload\|minio\|checkpoint"
   ```

   **Expected logs**:
   ```
   Training completed. Uploading checkpoints to MinIO...
   Checkpoint directory for upload: /workspace/finetuning/{job_id}/output
   Found X checkpoint files to upload
   Uploading adapter_model.safetensors to MinIO: technology/backend...
   Successfully uploaded X files to MinIO
   Checkpoints uploaded successfully to: minio://documents/technology/...
   ✅ Model registered: test_minio_upload_model (ID: xxx)
   ```

5. **Verify in Database**:
   ```bash
   docker-compose exec postgres psql -U postgres -d ragchatbot -c "
   SELECT name, status, minio_checkpoint_path
   FROM finetuned_models
   WHERE name LIKE '%test_minio_upload%';"
   ```

   **Expected**: `minio_checkpoint_path` should start with `minio://documents/technology/...`

6. **Verify in MinIO UI**:
   - Navigate to http://localhost:9001 (minioadmin/minioadmin)
   - Browse to: `documents/technology/backend-development/global/admin/finetuning/datasets/story8/checkpoints/`
   - You should see your job folder with checkpoint files

---

### Test 2: Deploy Model from MinIO

1. **Approve the model** (Governance tab)

2. **Deploy to Ollama** (Evaluations tab)

3. **Check backend logs** for MinIO download:
   ```bash
   docker-compose logs -f backend | grep -i "download\|minio\|ollama"
   ```

   **Expected logs**:
   ```
   Downloading model from MinIO: minio://documents/technology/...
   Downloading from MinIO to /tmp/ollama_model_xxx
   Downloading technology/backend-development/.../adapter_model.safetensors to /tmp/...
   Downloaded X files from MinIO to /tmp/ollama_model_xxx
   ✅ Successfully created Ollama model: test_minio_upload-v1
   ```

4. **Verify model in Ollama**:
   ```bash
   docker-compose exec ollama ollama list
   ```

   **Expected**: Your model appears in the list

5. **Test in Chat UI**:
   - Navigate to http://localhost:3001
   - Select your fine-tuned model from dropdown (under "Fine-Tuned Models")
   - Send a test message
   - Model should respond using fine-tuned weights

---

### Test 3: Deployment Logs Verification

Expected sequence in backend logs:
```
1. POST /api/v1/finetuning/models-public/{id}/deploy
2. Downloading model from MinIO: minio://documents/...
3. Downloading from MinIO to /tmp/ollama_model_xxx
4. Downloading {N} files...
5. Downloaded {N} files from MinIO
6. ✅ Generated Modelfile (using FROM merged model)
7. Creating Ollama model 'xxx' via API at http://ollama:11434/api/create
8. ✅ Successfully created Ollama model: xxx
9. Model deployed successfully
```

---

## ❌ Common Issues and Solutions

### Issue 1: "Checkpoint directory not found"
**Symptom**: Celery logs show `Checkpoint directory not found: /workspace/output/...`

**Cause**: Using an old training job (before the fix)

**Solution**: Train a NEW model after the fix was applied

---

### Issue 2: "No checkpoint files found"
**Symptom**: Logs show `No checkpoint files found in /workspace/finetuning/{job_id}/output`

**Cause**: Training failed or didn't save checkpoints

**Solution**:
1. Check training container logs
2. Verify training completed successfully (status="completed")
3. Check if output directory has files: `docker-compose exec celery-worker ls -la /workspace/finetuning/{job_id}/output`

---

### Issue 3: "MinIO upload fails"
**Symptom**: Upload logs show MinIO S3 errors

**Cause**: MinIO connection or permissions issue

**Solution**:
1. Check MinIO is running: `docker-compose ps minio`
2. Verify credentials in .env match (MINIO_ACCESS_KEY, MINIO_SECRET_KEY)
3. Check bucket exists: http://localhost:9001 → "documents" bucket

---

### Issue 4: "Model downloads but deployment fails"
**Symptom**: Download succeeds but Ollama creation fails

**Cause**: Checkpoint format incompatible or Modelfile issue

**Solution**:
1. Check downloaded files in /tmp/ollama_model_xxx
2. Verify adapter_model.safetensors or model.safetensors exists
3. Check Ollama logs: `docker-compose logs ollama`

---

## 🎯 Success Criteria

✅ **All these must be true**:
1. Celery logs show "Checkpoints uploaded successfully to: minio://..."
2. Database `finetuned_models.minio_checkpoint_path` starts with "minio://"
3. MinIO UI shows checkpoint files in correct organizational hierarchy
4. Backend downloads checkpoints from MinIO during deployment
5. Ollama successfully creates model with fine-tuned weights
6. Model appears in chat UI and responds correctly

---

## 📋 Next Steps (Future Enhancements)

1. **Checkpoint Cleanup**: Add periodic cleanup of /tmp/ollama_model_* directories
2. **Resume Training**: Support resuming from MinIO checkpoints
3. **Versioning**: Track checkpoint versions (best, latest, epoch-N)
4. **Model Diffing**: Compare checkpoint vs base model
5. **Distributed Training**: Multi-GPU checkpoint sharding to MinIO
6. **Rollback**: Revert to previous checkpoint version

---

## 🗂️ Files Modified

### Backend Files:
1. **`backend/app/tasks/finetuning_tasks.py`** (lines 680-682)
   - Fixed checkpoint directory path to use actual result from sandbox manager
   - Added logging for checkpoint directory

2. **`backend/app/services/ollama_deployment_service.py`** (lines 43-49, 79-155)
   - Added `_download_from_minio()` method for MinIO URL support
   - Updated `deploy_model()` to download from MinIO before deployment

### Services Restarted:
- ✅ `celery-worker` (for task fix)
- ✅ `backend` (for deployment service fix)

---

## 📚 Related Documentation

- **Dataset Upload**: `docs/fixes/FINETUNING_MINIO_ORGANIZATIONAL_PATHS_COMPLETE.md`
- **Approval Workflow**: `docs/features/finetuning/APPROVAL_DEPLOYMENT_WORKFLOW.md`
- **Pipeline Stages**: `docs/features/finetuning/PIPELINE_STAGES_OLLAMA_UI_INTEGRATION_COMPLETE.md`

---

**Current Status**: ✅ **ALL FIXES IMPLEMENTED AND SERVICES RESTARTED**

**Action Required**: User must test by training a NEW model and verifying:
1. Checkpoints uploaded to MinIO
2. Model deployed from MinIO
3. Chat works with fine-tuned weights

---

**Date**: 2025-12-19
**Session**: MinIO Checkpoint Upload Fix
**Status**: ✅ READY FOR TESTING
