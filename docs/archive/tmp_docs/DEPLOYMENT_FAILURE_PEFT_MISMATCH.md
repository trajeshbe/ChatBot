# Deployment Failure - PEFT Version Mismatch

**Date**: 2025-12-23 08:40 UTC
**Issue**: One-click deployment merge task failed with `alora_invocation_tokens` error

---

## Problem

User clicked "Merge and Deploy to Ollama" button for model `choles-qa-real-training51_model`, but the merge failed with:

```
❌ [AUTO-MERGE] Merge failed: LoraConfig.__init__() got an unexpected keyword argument 'alora_invocation_tokens'
```

Additionally:
```
ModuleNotFoundError("No module named 'app.services.finetuning.minio_service'")
```

---

## Root Cause

**PEFT version mismatch between containers:**
- **Training container** (finetuning-trainer): PEFT 0.18.0 with ALoRA support ✅
- **Backend container**: PEFT 0.18.0 ✅
- **Celery worker container**: PEFT 0.7.1 ❌ (OUTDATED!)

The training job created LoRA adapters with ALoRA invocation tokens (PEFT 0.18.0 feature), but the Celery worker trying to merge them only has PEFT 0.7.1, which doesn't recognize this parameter.

---

## Why Restart Didn't Fix It

When we ran:
```bash
docker-compose stop celery-worker && docker-compose rm -f celery-worker
docker-compose up -d celery-worker
```

Docker Compose **reused the existing cached image** with PEFT 0.7.1.

Even though the backend image was rebuilt with PEFT 0.18.0, the Celery worker is using an old cached version of the same image.

---

## Solution Required

**Rebuild the backend image with `--no-cache` and recreate both backend and celery-worker:**

```bash
# Step 1: Build fresh backend image (no cache)
docker-compose build backend --no-cache

# Step 2: Stop and remove both backend and celery-worker
docker-compose stop backend celery-worker
docker-compose rm -f backend celery-worker

# Step 3: Recreate with new image
docker-compose up -d backend celery-worker

# Step 4: Verify PEFT versions match
docker-compose exec backend pip show peft | grep Version
docker-compose exec celery-worker pip show peft | grep Version
# Both should show: Version: 0.18.0
```

---

## Estimated Time

- **Image rebuild**: 20-25 minutes (no-cache build)
- **Container recreation**: 30 seconds
- **Total**: ~25 minutes

---

## After Fix

User will need to:
1. Navigate back to Governance & Audit UI
2. Click "Merge and Deploy to Ollama" button again
3. Wait for successful deployment (10-20 minutes)

---

## Files Affected

- `backend/requirements.txt`: Already has `peft>=0.18.0`
- Docker cached layers need to be cleared to pick up the new version

---

**Status**: PENDING FIX - Waiting for no-cache rebuild approval
