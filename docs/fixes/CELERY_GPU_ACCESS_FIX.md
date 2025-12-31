# Celery Worker GPU Access Fix

**Date**: 2025-12-19
**Status**: ✅ FIXED

## Problem

Fine-tuning job "short_story_3" was stuck in "queued" status indefinitely:

```
Job ID: e858e93a-7966-463f-becf-0c65beda6dd3
Status: queued
Method: PEFT
GPU Required: 1 GPU with 6GB+ memory
```

**User Question**: "why is it still waiting ??"

**Celery Worker Logs**:
```
❌ GPU detection failed: NVML Shared Library Not Found
🎮 GPU Pool Manager initialized with 0 GPUs: []
❌ Not enough GPUs available. Need 1, have 0 with >=6.0GB free
⏳ Waiting for GPU availability (job e858e93a-7966-463f-becf-0c65beda6dd3)...
```

## Root Cause

The **celery-worker GPU configuration was commented out** in `docker-compose.yml` (lines 443-450):

```yaml
# GPU access commented out - celery worker launches separate training containers with GPU
# deploy:
#   resources:
#     reservations:
#       devices:
#         - driver: nvidia
#           count: 1
#           capabilities: [gpu]
```

While other services (`ollama`, `backend`, `finetuning-runtime`) had GPU access enabled, the celery-worker could not detect or allocate GPUs because it had no GPU passthrough configured.

## Environment Verification

✅ **GPU Available**: NVIDIA GeForce RTX 5060 Laptop GPU (8GB VRAM)
✅ **NVIDIA Drivers**: Version 577.03, CUDA 12.9
✅ **Docker GPU Passthrough**: Working (Ollama uses GPU regularly)
✅ **Platform**: WSL2 (Linux 6.6.87.2-microsoft-standard-WSL2)

## Solution Applied

### 1. Enabled GPU Access for Celery Worker

**File**: `docker-compose.yml` (lines 443-450)

**Changed from**:
```yaml
# GPU access commented out - celery worker launches separate training containers with GPU
# deploy:
#   resources:
#     reservations:
#       devices:
#         - driver: nvidia
#           count: 1
#           capabilities: [gpu]
```

**Changed to**:
```yaml
# GPU access enabled for GPU detection and allocation
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

### 2. Recreated Celery Worker Container

```bash
docker-compose up -d --force-recreate celery-worker
```

### 3. Cleared Stuck Task

The old task was stuck in "STARTED" state from the previous worker:

```bash
# Cleared Celery task result
docker-compose exec redis redis-cli DEL "celery-task-meta-1a25e531-56cb-4481-aea6-186621c709ab"

# Updated job status to failed so it can be resubmitted
UPDATE finetuning_jobs SET status = 'failed',
  error_message = 'GPU not available - worker restarted with GPU access. Please resubmit.'
WHERE id = 'e858e93a-7966-463f-becf-0c65beda6dd3';
```

## Verification

✅ **Celery Worker Running**:
```
celery@17ebeac13c7a v5.3.4 (emerald-rush)
Connected to redis://redis:6379/0
celery@17ebeac13c7a ready.
```

✅ **GPU Detected in Celery Worker**:
```bash
$ docker-compose exec celery-worker nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader

NVIDIA GeForce RTX 5060 Laptop GPU, 8151 MiB, 7577 MiB
```

- **Total GPU Memory**: 8151 MiB (8GB)
- **Free GPU Memory**: 7577 MiB (7.4GB)
- **Sufficient for Fine-Tuning**: ✅ (requires 6GB minimum)

## Files Modified

1. **docker-compose.yml** - Enabled GPU access for celery-worker service

## Next Steps for User

1. **Navigate to Admin → Finetuning → Jobs**
2. **Find job "short_story_3"** (status will show "failed")
3. **Resubmit the job** using the UI
4. **New job will start immediately** with GPU access

Expected behavior:
```
🎮 GPU Pool Manager initialized with 1 GPUs: [GPU(0, NVIDIA GeForce RTX 5060 Laptop GPU, 7577MB free)]
✅ Allocated GPU 0 to job e858e93a-7966-463f-becf-0c65beda6dd3
🚀 Starting fine-tuning job...
```

## Prevention

**Always ensure GPU configuration is enabled for services that need GPU detection:**

- ✅ `ollama` - GPU enabled (for LLM inference)
- ✅ `backend` - GPU enabled (for embedding generation)
- ✅ `finetuning-runtime` - GPU enabled (for training containers)
- ✅ `celery-worker` - **NOW enabled** (for GPU detection and allocation)

## Related Documentation

- **Fine-Tuning Admin Fix**: `FINETUNING_ADMIN_FIX.md` (semver dependency issue)
- **Fine-Tuning API**: `/api/v1/finetuning/jobs` endpoints
- **GPU Status API**: `/api/v1/finetuning/gpu/status`

---

**Result**: Celery worker can now detect and allocate GPU resources for fine-tuning jobs. The stuck job has been cleared and can be resubmitted.
