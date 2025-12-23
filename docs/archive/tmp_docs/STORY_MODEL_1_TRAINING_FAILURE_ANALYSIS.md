# Training Job "story_model_1" - Failure Analysis

**Date**: 2025-12-23 14:17 UTC
**Job ID**: 307c3ce3-4f26-45bb-8a3f-a718838c1e45
**Model ID**: e93360fc-fc0b-4519-a08f-e29f8f75704a
**Status**: ❌ FAILED (marked as "completed" but no training occurred)

---

## What Happened

The training job "story_model_1" was marked as COMPLETED in the database after 316 seconds (~5 minutes), but **NO ACTUAL TRAINING OCCURRED**.

### Evidence

1. **Database Status**: Job shows status="completed", training_stage="completed", progress=100
2. **No Adapter Files**: The `/workspace/finetuning/307c3ce3-4f26-45bb-8a3f-a718838c1e45/output/` directory has NO adapter files
3. **No Training Logs**: The training.log file doesn't exist (expected at `logs/training.log`)
4. **No Result JSON**: No result.json file with training metrics
5. **Training Container Exited**: Container ID `71447a6dc2ed` no longer exists

### What Should Have Happened

After training completes, these files should exist:
```
/workspace/finetuning/307c3ce3-4f26-45bb-8a3f-a718838c1e45/
├── input/
│   ├── train.json (✅ EXISTS - 87 samples)
│   ├── validation.json (✅ EXISTS - 10 samples)
│   └── training_config.json (✅ EXISTS)
├── output/
│   ├── adapter_model/               ❌ MISSING!
│   │   ├── adapter_model.safetensors
│   │   ├── adapter_config.json
│   │   └── ...
│   └── result.json                  ❌ MISSING!
└── logs/
    └── training.log                 ❌ MISSING!
```

---

## Root Cause Hypothesis

### 1. Training Container Never Started Properly

**Evidence from Celery logs**:
```
📡 Log streaming started for job 307c3ce3-4f26-45bb-8a3f-a718838c1e45
✅ Training container 71447a6dc2ed started
```

But then:
```
Training completed
Job 307c3ce3-4f26-45bb-8a3f-a718838c1e45 stage updated: completed
Duration: 316.348912 seconds
```

**Problem**: The job completed in 5 minutes, which is impossibly fast for:
1. Loading Qwen2.5-1.5B-Instruct (2.9 GB) - ~1-2 minutes
2. Training 3 epochs on 87 samples - ~5-8 minutes
3. Saving adapter weights - ~30 seconds

**Total expected**: 8-12 minutes minimum

### 2. Training Script Exited Immediately

Possible reasons:
1. **GPU Not Available**: Training container couldn't access GPU and exited
2. **Import Error**: Missing Python package or incompatible version
3. **CUDA Error**: GPU driver mismatch or out of memory
4. **Configuration Error**: Invalid hyperparameters or dataset format
5. **Container Volume Issue**: /workspace mount not accessible

---

## How To Diagnose

### Check Docker Logs (Training Container Exited)

Since container `71447a6dc2ed` no longer exists, logs are lost. But you can check:

```bash
# Check if any training containers failed recently
docker ps -a --filter "status=exited" --filter "label=training-job" | head -10

# Check Celery worker logs around training time
docker-compose logs celery-worker 2>&1 | grep "307c3ce3" | grep -E "(Error|Failed|Exception)"
```

### Check GPU Availability

```bash
# From training container
docker run --rm --gpus all chatbot-finetuning-trainer:v1.0.4 nvidia-smi
```

### Check Training Script Directly

```bash
# Try to run training script manually with same config
docker run --rm --gpus all \
  -v /workspace/finetuning:/workspace/finetuning \
  chatbot-finetuning-trainer:v1.0.4 \
  python run_training.py \
  --job_id 307c3ce3-4f26-45bb-8a3f-a718838c1e45 \
  --config_path /workspace/finetuning/307c3ce3-4f26-45bb-8a3f-a718838c1e45/input/training_config.json
```

---

## TensorBoard Status

**TensorBoard URL**: http://localhost:6006

**Status**: Running, but NO LOGS available for this job because training never actually ran.

**Expected Logs**: Would appear at `/workspace/finetuning/307c3ce3-4f26-45bb-8a3f-a718838c1e45/logs/` once training starts writing metrics.

---

## Comparison with Working Job (training49)

| Metric | training49 (WORKING) | story_model_1 (FAILED) |
|--------|---------------------|----------------------|
| **Duration** | ~10-15 minutes | 316 seconds (~5 min) ❌ |
| **Adapter Files** | ✅ 8.4 MB saved | ❌ None |
| **Training Logs** | ✅ Created | ❌ Missing |
| **Container Exit** | Clean exit after completion | Premature exit ❌ |
| **GPU Usage** | Visible in nvidia-smi | Unknown (container gone) |
| **Final Status** | approved → deployed | registered (stuck) ❌ |

---

## Next Steps to Fix

### Option 1: Check Celery Worker Logs for Error Details

```bash
docker-compose logs celery-worker 2>&1 | \
  grep -A 100 "307c3ce3" | \
  grep -E "(Error|Exception|Traceback|Failed)" | \
  head -50
```

### Option 2: Retry Training Job

1. **Delete failed model record** from database:
```sql
DELETE FROM finetuned_models WHERE id = 'e93360fc-fc0b-4519-a08f-e29f8f75704a';
DELETE FROM finetuning_jobs WHERE id = '307c3ce3-4f26-45bb-8a3f-a718838c1e45';
```

2. **Create new training job** from UI with same dataset

3. **Monitor closely** this time:
   - Watch Celery logs: `docker-compose logs -f celery-worker`
   - Check GPU usage: `watch -n 1 nvidia-smi`
   - Monitor container: `docker ps -a | grep training`

### Option 3: Run Training Manually (Debugging)

```bash
# 1. Check training container can access GPU
docker run --rm --gpus all chatbot-finetuning-trainer:v1.0.4 nvidia-smi

# 2. Check training script exists
docker run --rm chatbot-finetuning-trainer:v1.0.4 ls -la /app/

# 3. Test training script with minimal config
docker run --rm --gpus all chatbot-finetuning-trainer:v1.0.4 python --version
```

---

## Key Questions to Answer

1. **Did the GPU training container actually start?**
   - Check: `docker ps -a --filter "id=71447a6dc2ed"`
   - Expected: Should show exit code and timestamp

2. **Did the training script run?**
   - Check: Look for training container logs
   - Expected: Should see model loading, training loop, adapter saving

3. **Why did it complete so fast?**
   - 316 seconds is way too fast for full training
   - Expected: 10-15 minutes minimum

4. **Why no error was thrown?**
   - Job marked as "completed" even though nothing was saved
   - Expected: Should fail with error if training didn't work

---

## Recommended Action

**IMMEDIATE**: Check Celery worker logs for the actual error that occurred during training:

```bash
docker-compose logs celery-worker 2>&1 | \
  grep -C 50 "307c3ce3" | \
  grep -E "(Error|Exception|Traceback|Failed|ImportError|RuntimeError|CUDA)" | \
  less
```

This will show the actual error that caused training to fail silently.

---

**Created**: 2025-12-23 14:30 UTC
**Status**: Training failed but marked as complete
**Action Required**: Debug why training exited early without saving adapter weights

---

## Update: User Request

**User asked for**: "TensorBoard link for this job"

**Answer**: 
- TensorBoard is running at http://localhost:6006
- However, NO LOGS exist for this job because training never ran
- Training exited prematurely without creating any metrics/logs
- Need to fix the training failure first before TensorBoard will show anything

