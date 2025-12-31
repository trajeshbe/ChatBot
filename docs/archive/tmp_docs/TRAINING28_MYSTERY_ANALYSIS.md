# Training28 Mystery - Analysis

**Date**: 2025-12-21 18:30 UTC
**Status**: ⚠️ **INCONCLUSIVE** - Training28 completed but left no evidence

---

## What Happened

Training28 was created to test the v1.0.4 tokenization fix. The database shows:

```
status: completed
training_stage: completed
duration: 226.5 seconds (3.77 minutes)
current_epoch: NULL
current_step: NULL
train_loss: NULL
error_message: NULL
logs: (empty)
```

---

## Missing Evidence

### 1. No Container Logs
```bash
$ docker logs finetuning-950161b6-e18b-4cc7-916b-94e364ae1d75
Error response from daemon: No such container
```

Container was already removed - suggests it exited quickly or was cleaned up.

### 2. No Workspace Files
```bash
$ docker run --rm -v finetuning_workspaces:/workspace alpine ls -lah /workspace/950161b6-e18b-4cc7-916b-94e364ae1d75/
No workspace directory
```

No output directory means either:
- Container never created workspace
- Workspace was cleaned up
- Training failed before creating directories

### 3. No Celery Logs
```bash
$ docker-compose logs celery 2>&1 | grep "3e3e7640-386c-43d1-a2a2-f17cfbfc7a69"
(no results)
```

Task ID not found in Celery logs - either rotated out or task never executed.

### 4. Empty Database Logs Field
```sql
SELECT logs FROM finetuning_jobs WHERE id = '950161b6-e18b-4cc7-916b-94e364ae1d75';
-- Result: (empty)
```

No logs captured in database.

---

## Timeline Analysis

### Duration Comparison

| Training | Version | Duration | Error | Outcome |
|----------|---------|----------|-------|---------|
| **23-25** | v1.0.1 | 2-3 sec | Exit 2 | File not found |
| **26** | v1.0.2 | 162 sec | Exit 1 | TensorBoard missing |
| **27** | v1.0.3 | 156 sec | Exit 1 | Dataset format error |
| **28** | v1.0.4 | 226 sec | None? | Completed (no evidence) |

**Observation**: Training28 ran **70 seconds longer** than training27!

**Possible explanations**:
1. ✅ **Training actually ran** - longer duration suggests it got past the dataset format error
2. ⚠️ **Mock mode** - took 226 seconds to complete mock training with model merge
3. ❌ **Silent failure** - failed in a way that wasn't captured

---

## What We Know

### Training28 Configuration
```json
{
  "id": "950161b6-e18b-4cc7-916b-94e364ae1d75",
  "name": "choles-qa-real-training28",
  "base_model": "Qwen/Qwen2.5-1.5B-Instruct",
  "finetuning_method": "peft",
  "training_objective": "instruction",
  "quantization": "4bit",
  "dataset_id": "added64c-16fd-42a9-9370-e08f2516f198",
  "hyperparameters": {
    "learning_rate": 0.0002,
    "num_epochs": 3,
    "batch_size": 4,
    "lora_r": 16,
    "lora_alpha": 32
  }
}
```

### Celery Task Submission
```python
from app.tasks.finetuning_tasks import run_finetuning_job
task = run_finetuning_job.delay('950161b6-e18b-4cc7-916b-94e364ae1d75')
# Task ID: 3e3e7640-386c-43d1-a2a2-f17cfbfc7a69
```

Task was successfully submitted to Celery queue.

### Expected Docker Image
```python
# From finetuning_sandbox_manager.py:55
self.finetuning_image = os.getenv("FINETUNING_TRAINER_IMAGE", "chatbot-finetuning-trainer:v1.0.4")
```

Should have used v1.0.4 with tokenization fix.

---

## Theories

### Theory 1: Training Actually Succeeded
**Evidence**:
- Status: "completed"
- Duration: 226 seconds (longer than previous failures)
- No error_message

**Gaps**:
- Why no workspace files?
- Why no logs?
- Why container gone so fast?

**Likelihood**: 30%

### Theory 2: Mock Mode Ran
**Evidence**:
- No dataset found → `dataset = None` → mock mode triggered
- Mock mode runs model merge which takes ~200 seconds
- Mock mode doesn't create proper workspace structure

**Gaps**:
- Should have created adapter_dir and merged_dir
- Should have logs about "⚠️ No dataset provided"

**Likelihood**: 50%

### Theory 3: Silent Failure
**Evidence**:
- No logs captured
- No workspace created
- Container removed quickly

**Gaps**:
- Status would be "failed" not "completed"
- Should have error_message

**Likelihood**: 20%

---

## Why Mock Mode is Most Likely

Looking at `peft_trainer.py:234-329`, when `dataset is None`:

```python
if dataset is None:
    logger.info("⚠️ No dataset provided, creating mock training result with merge step")

    # 1. Save adapter weights
    adapter_dir = output_dir / "adapter_model"
    model.save_pretrained(adapter_dir)  # Takes time

    # 2. Merge adapters
    base_model_full = AutoModelForCausalLM.from_pretrained(...)  # Downloads model
    peft_model = PeftModel.from_pretrained(...)
    merged_model = peft_model.merge_and_unload()  # Heavy operation
    merged_model.save_pretrained(merged_dir)  # Saves full model

    # Result: status="completed"
```

**This would explain**:
- ✅ 226 second duration (model download + merge takes time)
- ✅ "completed" status
- ❓ Missing workspace (cleanup after completion?)
- ❓ Missing logs (not captured properly?)

---

## Key Question

**Did the dataset load or not?**

If dataset loaded → should have seen:
- "🔄 Dataset has 'messages' column - applying tokenization..."
- "✅ Tokenized 9 samples"
- "🚀 Starting REAL training (NOT mock)..."

If dataset didn't load → mock mode:
- "⚠️ No dataset provided, creating mock training result"

**We need to check**: Did v1.0.4 image have access to the dataset?

---

## Next Steps

### Immediate: Create Training29 with Verbose Logging

```python
# Add environment variable to force dataset path
DATASET_PATH=/workspace/input/dataset

# Check if dataset files exist BEFORE starting trainer
docker exec finetuning-<id> ls -la /workspace/input/dataset/

# Monitor container logs in real-time
docker logs -f finetuning-<id> 2>&1 | tee /tmp/training29_full.log
```

### Investigation Checklist

1. ✅ Verify v1.0.4 image has tokenization fix
2. ✅ Verify .env.example points to v1.0.4
3. ✅ Verify Celery worker restarted with new code
4. ❓ **Check if dataset exists in MinIO** - CRITICAL!
5. ❓ Verify dataset preprocessing created train.json
6. ❓ Monitor container creation and startup

---

## Critical Hypothesis to Test

**Hypothesis**: The dataset preprocessing in `finetuning_sandbox_manager.py` may not have created the dataset files properly, causing the trainer to fall back to mock mode.

**Test**:
1. Create training29
2. BEFORE submission, manually verify dataset exists:
   ```bash
   docker-compose exec minio ls -la minio/datasets/<dataset_id>/
   ```
3. After container starts, exec into it and check:
   ```bash
   docker exec finetuning-<id> ls -la /workspace/input/dataset/
   docker exec finetuning-<id> cat /workspace/input/dataset/train.json | head -5
   ```

If dataset doesn't exist → **ROOT CAUSE FOUND**: Dataset preprocessing is broken
If dataset exists → Training should work with v1.0.4 tokenization

---

## Files to Check

1. **MinIO dataset location**:
   - Bucket: `datasets`
   - Path: `added64c-16fd-42a9-9370-e08f2516f198/`
   - Expected files: `train.json`, potentially `metadata.json`

2. **Container mount points** (from finetuning_sandbox_manager.py):
   - Dataset: `/workspace/input/dataset` (from MinIO download)
   - Output: `/workspace/output`
   - Logs: `/workspace/logs`

3. **Environment variables** (passed to container):
   - `DATASET_PATH=/workspace/input/dataset`
   - Should override config's dataset_path

---

## Conclusion

Training28's completion with no evidence is **most likely due to mock mode** being triggered by a missing dataset. The 226-second duration matches the time needed for:
- Loading Qwen/Qwen2.5-1.5B-Instruct (~7.4GB)
- Creating adapter
- Merging adapter into base model
- Saving merged model

**Next action**: Create training29 with explicit dataset verification before and after container launch.

---

**Date**: 2025-12-21 18:30 UTC
