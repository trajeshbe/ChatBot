# TensorBoard Dashboard Issue - Root Cause Analysis & Fix

**Date**: 2025-12-20
**Issue**: "I don't see anything in TensorBoard or any meaningful dashboards with data to monitor"

---

## Root Cause Analysis

### Issue #1: Mock Training (No Real Training Happening)

**Evidence**:
```
2025-12-20 14:41:47 - WARNING - Could not load dataset: Unable to find '/workspace/input/dataset/train.json'
2025-12-20 14:41:47 - INFO - Using dummy dataset for testing
2025-12-20 14:41:47 - INFO - ⚠️ No dataset provided, creating mock training result with merge step
```

**Root Cause**: The finetuning service is NOT properly copying the uploaded dataset file from MinIO to the container's workspace before training starts.

**Expected Flow**:
1. User uploads dataset → Stored in MinIO (✅ Working)
2. Finetuning service creates job (✅ Working)
3. **Finetuning service downloads dataset from MinIO** → `/workspace/input/dataset/train.json` (❌ **BROKEN**)
4. Trainer loads dataset and runs training (❌ Skipped due to missing file)

**Actual Flow**:
1. Trainer looks for `/workspace/input/dataset/train.json`
2. File not found
3. Trainer enters "mock mode" - just saves untrained adapters
4. No actual training → No TensorBoard metrics

---

### Issue #2: Wrong TensorBoard Logging Directory (FIXED)

**Before Fix**:
```python
logging_dir=f"{output_dir}/logs",  # Wrong: /workspace/finetuning/{job_id}/output/logs
```

**After Fix**:
```python
logging_dir=config.get("log_dir", "/workspace/logs"),  # Correct: /workspace/finetuning/{job_id}/logs
```

**Status**: ✅ Fixed in `backend/app/services/finetuning/trainers/peft_trainer.py:140`

---

## Why You See No Dashboards

### TensorBoard (http://localhost:6006)
- **Expected**: Training loss, learning rate, epoch graphs
- **Actual**: Empty / "No dashboards are active"
- **Reason**: No TensorFlow event files generated because no training happened

### Grafana (http://localhost:3000)
- **Expected**: Multi-reward metrics (for GRPO only)
- **Actual**: Empty panels
- **Reason**:
  1. SFT jobs don't emit reward metrics (expected - Grafana is for GRPO)
  2. No training happened anyway

### Prometheus (http://localhost:9090)
- **Expected**: `train_loss`, `reward_*` metrics
- **Actual**: No metrics
- **Reason**: Training didn't run, so no metrics exported

### Frontend UI (http://localhost:3001/finetuning)
- **Expected**: Job status, progress bar
- **Actual**: Shows "completed" but no training metrics
- **Reason**: Job completed in mock mode, not real training

---

## The Real Problem: Dataset Mounting Bug

### Where It Breaks

The finetuning service has **two paths** for dataset handling:

**Path 1: Direct file path** (if dataset already on disk)
```python
dataset_path = "/path/to/local/dataset"
```

**Path 2: MinIO download** (if dataset in object storage) ❌ **NOT IMPLEMENTED**
```python
# This code is MISSING or BROKEN
# Should download from MinIO to workspace before training
minio_client.fget_object(
    bucket_name=self.minio_bucket,
    object_name=f"finetuning/datasets/{dataset_id}/train.json",
    file_path=f"/workspace/input/dataset/train.json"
)
```

### Current Behavior

**When you upload a dataset via API:**
1. Dataset stored in MinIO ✅
2. Database record created with `file_path` = MinIO object path ✅
3. Finetuning job created with `dataset_id` ✅
4. **Finetuning service starts container** ✅
5. **BUT**: Dataset file is NOT downloaded from MinIO to container ❌
6. Trainer can't find file → Mock mode ❌
7. No training → No TensorBoard metrics ❌

---

## Solution Options

### Option A: Fix MinIO Dataset Download (Proper Fix)

**What to do**: Implement dataset download in `FineTuningSandboxManager.create_training_workspace()`

**Code to add** (in `finetuning_sandbox_manager.py`):
```python
async def create_training_workspace(self, job_id: str, dataset_id: str) -> Dict[str, Path]:
    # ... existing code ...

    # Download dataset from MinIO
    if dataset_id and self.minio_client:
        try:
            # Get dataset record from database
            from app.models.database_enhanced import FineTuningDataset
            from app.core.database import get_db

            async for db in get_db():
                dataset = db.query(FineTuningDataset).filter_by(id=dataset_id).first()
                if dataset and dataset.file_path:
                    # Download from MinIO
                    minio_path = dataset.file_path.replace("minio://", "").split("/", 1)[1]
                    local_path = workspace_paths["input"] / "dataset" / "train.json"
                    local_path.parent.mkdir(parents=True, exist_ok=True)

                    self.minio_client.fget_object(
                        bucket_name=self.minio_bucket,
                        object_name=minio_path,
                        file_path=str(local_path)
                    )

                    logger.info(f"✅ Downloaded dataset from MinIO: {minio_path} → {local_path}")
                break
        except Exception as e:
            logger.error(f"❌ Failed to download dataset: {e}")
```

**Status**: Not yet implemented

---

### Option B: Direct Container File Mount (Quick Workaround)

**What to do**: Manually copy dataset to finetuning workspace BEFORE starting job

**Steps**:
```bash
# 1. Find where finetuning workspaces are stored
WORKSPACE_DIR="/tmp/finetuning_workspaces"  # or check docker volume

# 2. Create job workspace
JOB_ID="your-job-id-here"
mkdir -p $WORKSPACE_DIR/$JOB_ID/input/dataset

# 3. Copy your dataset file
cp /path/to/your/train.json $WORKSPACE_DIR/$JOB_ID/input/dataset/train.json

# 4. Start training job (it will find the file)
```

**Status**: Manual workaround

---

### Option C: Use Docker Volume Direct Write (Current Best Option)

**What to do**: Write dataset directly to the Docker volume before job starts

**Implementation**:
```bash
#!/bin/bash
# Write dataset to finetuning workspace volume

JOB_ID="7653a630-2629-4fcb-a430-5e7c96749fd8"
DATASET_FILE="/tmp/proper_train_dataset.json"

# Use docker-compose exec to write to volume
docker-compose exec backend bash -c "
mkdir -p /workspace/finetuning/$JOB_ID/input/dataset &&
cat > /workspace/finetuning/$JOB_ID/input/dataset/train.json <<'EOFDATA'
$(cat $DATASET_FILE)
EOFDATA
"

echo "✅ Dataset written to workspace"
```

**Status**: Can implement now as immediate fix

---

## Verification Steps

After implementing the fix, verify with:

```bash
# 1. Check dataset file exists in container workspace
docker-compose exec backend ls -la /workspace/finetuning/{job_id}/input/dataset/

# Should show:
# train.json  (your dataset file)

# 2. Start training and monitor logs
docker logs -f finetuning-{job_id} | grep -E "Loading dataset|training samples"

# Should show:
# "✅ Loaded 5 training samples"  (not "Using dummy dataset")

# 3. Wait for training to start (~60 seconds)
# Then check for TensorBoard event files
docker-compose exec tensorboard find /logs/{job_id} -name "events.out.tfevents.*"

# Should show:
# /logs/{job_id}/events.out.tfevents.{timestamp}.{hostname}

# 4. Open TensorBoard
# http://localhost:6006
# Should show: Scalars tab with train/loss, train/learning_rate, etc.
```

---

## Expected Timeline to See Dashboards

**After implementing the fix:**

| Time | Event | Dashboard Status |
|------|-------|------------------|
| T+0s | Job submitted | Frontend: "queued" |
| T+10s | Container started | Frontend: "running" |
| T+60s | Model loaded (Qwen 1.5B from cache) | Still no metrics |
| T+90s | **Training starts** | TensorBoard: First metrics appear! |
| T+120s | Step 1-5 complete | TensorBoard: Loss graph visible |
| T+180s | Training complete (10 steps) | All metrics captured |

**What you'll see in TensorBoard at T+120s:**
- **Scalars tab** → `train/loss` (decreasing line graph)
- **Scalars tab** → `train/learning_rate` (warmup schedule)
- **Scalars tab** → `train/epoch` (0.0 → 1.0)
- **Scalars tab** → `train/global_step` (1 → 10)

---

## Summary

**Why dashboards are empty:**
1. ✅ TensorBoard logging directory fix applied
2. ❌ **PRIMARY ISSUE**: Dataset file not copied from MinIO to container workspace
3. ❌ Trainer enters mock mode when dataset not found
4. ❌ No training = No TensorBoard event files = Empty dashboards

**Solution:**
- **Immediate**: Use Option C (direct volume write) to test with current job
- **Proper**: Implement Option A (MinIO download in workspace setup)

**Expected Result After Fix:**
- ✅ Real training with actual loss graphs
- ✅ TensorBoard shows all training metrics
- ✅ Training logs show "Loaded X samples" instead of "Using dummy dataset"
- ✅ Full observability stack functional

---

**Next Step**: I'll implement Option C (direct volume write) for the current job to demonstrate working TensorBoard metrics immediately.
