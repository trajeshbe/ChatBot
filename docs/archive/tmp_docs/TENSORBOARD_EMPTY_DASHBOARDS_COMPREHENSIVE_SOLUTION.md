# TensorBoard Empty Dashboards - Comprehensive Root Cause & Solution

**Date**: 2025-12-20
**Status**: CRITICAL BUG - No actual training happening
**User Issue**: "i don't see anything in tensorboard or any meaningful dashboards with data to monitor"

---

## Executive Summary

All finetuning jobs are completing in **MOCK MODE** - no actual training occurs, resulting in:
- ❌ Empty TensorBoard dashboards (no loss graphs, no metrics)
- ❌ Empty Grafana dashboards (no training data)
- ❌ No Prometheus metrics
- ❌ "Finetuned" models are actually untrained adapters

---

## Root Cause Analysis

### Primary Issue: Dataset File Not Accessible to Training Container

**Evidence from logs:**
```
2025-12-20 15:08:52 - WARNING - Could not load dataset: Unable to find '/workspace/input/dataset/train.json'
2025-12-20 15:08:52 - INFO - Using dummy dataset for testing
2025-12-20 15:08:52 - INFO - ⚠️ No dataset provided, creating mock training result with merge step
```

**The Problem:**

1. **Dataset Upload** (✅ Working)
   - User uploads dataset via API → Stored in MinIO
   - Database record created with `file_path` = MinIO path
   - Example: `minio://rag-documents/global/admin/finetuning/datasets/9a430194.../train.json`

2. **Workspace Creation** (✅ Working)
   - `create_training_workspace()` creates directory structure on HOST:
   - `/tmp/finetuning_workspaces/{job_id}/input/dataset/`

3. **Dataset Download** (❌ **BROKEN**)
   - `_copy_dataset_to_workspace()` exists but is NOT being called
   - Reason: `dataset_path` parameter not passed to `create_training_workspace()`
   - Result: Training container mounts empty `/workspace/input/dataset/` directory

4. **Training Container Startup** (✅ Working but finds no data)
   - Container mounts HOST path `/tmp/finetuning_workspaces/{job_id}/` to `/workspace/`
   - Trainer looks for `/workspace/input/dataset/train.json`
   - File doesn't exist → Falls back to mock mode

5. **Mock Training** (❌ Problem)
   - Saves untrained adapters
   - No TensorBoard metrics generated
   - No actual learning occurs

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        User Action                          │
│                  POST /api/v1/finetuning/datasets/upload    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     MinIO Storage (✅)                       │
│  Path: minio://rag-documents/global/admin/finetuning/...    │
│  File: train.json (5 examples, 2.8KB)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ ❌ MISSING STEP: Download to workspace
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              HOST: /tmp/finetuning_workspaces/              │
│                         {job_id}/                           │
│  ├── input/dataset/     ← EMPTY (should have train.json)   │
│  ├── output/                                                │
│  └── logs/                                                  │
└────────────────────────┬────────────────────────────────────┘
                         │ Docker volume mount
                         ▼
┌─────────────────────────────────────────────────────────────┐
│        Training Container: /workspace/                      │
│  ├── input/dataset/     ← EMPTY                             │
│  ├── output/                                                │
│  └── logs/                                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 Trainer (peft_trainer.py)                   │
│  if os.path.exists('/workspace/input/dataset/train.json'): │
│      # Real training                                        │
│  else:                                                      │
│      # ❌ MOCK MODE - No TensorBoard metrics                │
└─────────────────────────────────────────────────────────────┘
```

---

## Code Analysis

### Where the Fix Needs to Happen

**File**: `backend/app/services/finetuning/finetuning_service.py` (line ~300)

**Current Code** (BROKEN):
```python
# Create training workspace
workspace_paths = await self.sandbox_manager.create_training_workspace(
    job_id=str(job.id)
    # ❌ Missing: dataset_path=dataset.file_path
)
```

**Fixed Code** (SHOULD BE):
```python
# Get dataset record
dataset = db.query(FineTuningDataset).filter_by(id=job.dataset_id).first()

# Create training workspace with dataset download
workspace_paths = await self.sandbox_manager.create_training_workspace(
    job_id=str(job.id),
    dataset_path=dataset.file_path if dataset else None  # ✅ Pass MinIO path
)
```

### Supporting Code (Already Exists)

**File**: `backend/app/services/finetuning/finetuning_sandbox_manager.py` (lines 138-180)

The `_copy_dataset_to_workspace()` method ALREADY EXISTS and works correctly:

```python
async def _copy_dataset_to_workspace(
    self,
    dataset_minio_path: str,
    input_dir: Path
):
    """Download dataset from MinIO to training workspace"""

    if not self.minio_client:
        logger.warning("MinIO client not available")
        return

    # Parse MinIO path: minio://bucket/path/to/file.json
    minio_path = dataset_minio_path.replace("minio://", "").split("/", 1)[1]

    # Download to workspace
    local_path = input_dir / "dataset" / "train.json"
    local_path.parent.mkdir(parents=True, exist_ok=True)

    self.minio_client.fget_object(
        bucket_name=self.minio_bucket,
        object_name=minio_path,
        file_path=str(local_path)
    )

    logger.info(f"✅ Downloaded dataset from MinIO: {minio_path} → {local_path}")
```

**This code works!** It just needs to be called by passing `dataset_path` parameter.

---

## Solution

### Option A: Fix the Service Layer (PROPER FIX)

**What to do**: Modify `finetuning_service.py` to pass dataset path when creating workspace

**Steps**:
1. Read `backend/app/services/finetuning/finetuning_service.py`
2. Find where `create_training_workspace()` is called
3. Add dataset query and pass `dataset_path` parameter
4. Restart backend service
5. Create new training job
6. Verify real training happens

**Implementation**:
```python
# In finetuning_service.py (around line 300)

from app.models.database_enhanced import FineTuningDataset

async def start_training_job(self, job_id: str, db: Session):
    """Start training job"""

    # Get job and dataset
    job = db.query(FineTuningJob).filter_by(id=job_id).first()
    dataset = None
    if job.dataset_id:
        dataset = db.query(FineTuningDataset).filter_by(id=job.dataset_id).first()

    # Create workspace WITH dataset download
    workspace_paths = await self.sandbox_manager.create_training_workspace(
        job_id=str(job.id),
        dataset_path=dataset.file_path if dataset else None  # ✅ FIX
    )

    # ... rest of function
```

---

### Option B: Manual Workaround (TEMPORARY)

**What to do**: Manually download dataset from MinIO to workspace before job starts

**Script**:
```python
#!/usr/bin/env python3
"""
Manually download dataset from MinIO to finetuning workspace
RUN THIS BEFORE SUBMITTING JOB
"""

import os
from minio import Minio
from pathlib import Path

# Configuration
JOB_ID = "your-job-id-here"
DATASET_ID = "your-dataset-id-here"

# Initialize MinIO
minio_client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

# Get dataset path from database (you need to query this)
MINIO_PATH = "global/admin/finetuning/datasets/{dataset_id}/train.json"

# Download to workspace
workspace_base = Path(f"/tmp/finetuning_workspaces/{JOB_ID}")
dataset_dir = workspace_base / "input" / "dataset"
dataset_dir.mkdir(parents=True, exist_ok=True)

local_path = dataset_dir / "train.json"

minio_client.fget_object(
    bucket_name="rag-documents",
    object_name=MINIO_PATH,
    file_path=str(local_path)
)

print(f"✅ Dataset downloaded to {local_path}")
print(f"   File size: {local_path.stat().st_size} bytes")
print(f"   Now submit job: POST /api/v1/finetuning/jobs/{JOB_ID}/submit")
```

---

## Verification Steps

After implementing the fix:

### 1. Check Dataset File Exists
```bash
JOB_ID="your-job-id"
ls -la /tmp/finetuning_workspaces/$JOB_ID/input/dataset/

# Should show:
# train.json  (2.8KB for 5 examples)
```

### 2. Monitor Container Logs
```bash
docker logs -f finetuning-$JOB_ID 2>&1 | grep -E "Loading dataset|training samples"

# Should show:
# ✅ Loaded 5 training samples (NOT "Using dummy dataset")
```

### 3. Wait for Training to Start (~90 seconds)
```bash
# Check for TensorBoard event files
docker-compose exec tensorboard find /logs/$JOB_ID -name "events.out.tfevents.*"

# Should show:
# /logs/{job_id}/events.out.tfevents.{timestamp}.{hostname}
```

### 4. Open TensorBoard
```
http://localhost:6006
```

**Expected to See:**
- **Scalars tab** → `train/loss` (decreasing line graph)
- **Scalars tab** → `train/learning_rate` (warmup schedule)
- **Scalars tab** → `train/epoch` (0.0 → 1.0)
- **Scalars tab** → `train/global_step` (1 → 10)

---

## Timeline

| Time | Event | What to See |
|------|-------|-------------|
| T+0s | Job submitted | Frontend: "queued" |
| T+10s | Container started | Frontend: "running" |
| T+60s | Model loaded (Qwen 1.5B from cache) | Container logs: "Loading base model" |
| T+90s | **Training starts** | TensorBoard: First metrics appear! |
| T+120s | Step 1-5 complete | TensorBoard: Loss graph visible |
| T+180s | Training complete (10 steps) | All metrics captured |

---

## Impact on Dashboards

### Before Fix (Current State):
- TensorBoard: "No dashboards are active" ❌
- Grafana: Empty panels ❌
- Prometheus: No metrics ❌
- Frontend UI: Shows "completed" but no training metrics ❌

### After Fix (Expected):
- TensorBoard: Loss graphs, learning rate, epochs ✅
- Grafana: GRPO multi-reward metrics (for GRPO jobs only) ✅
- Prometheus: `train_loss`, `train_epoch`, etc. ✅
- Frontend UI: Real-time progress bar, metrics streaming ✅

---

## Related Issues

1. **TensorBoard Logging Directory** - FIXED in `peft_trainer.py:140`
   - Was: `logging_dir=f"{output_dir}/logs"`
   - Now: `logging_dir=config.get("log_dir", "/workspace/logs")`

2. **Model Deployment** - SEPARATE ISSUE
   - Models don't auto-deploy to Ollama
   - User must click "Deploy Model" button manually
   - Not related to training/TensorBoard issue

---

## Next Steps

1. **Implement Option A** (proper fix)
   - Modify `finetuning_service.py`
   - Add dataset path parameter
   - Test with new training job

2. **Validate with Real Training**
   - Create job
   - Monitor TensorBoard for metrics
   - Verify loss graphs appear

3. **Test Finetuned Model**
   - After real training completes
   - Deploy to Ollama
   - Test with Choles questions
   - Verify model learned correctly

4. **Proceed with GRPO Testing**
   - Upload GRPO dataset
   - Create GRPO training job
   - Monitor all 4 dashboards
   - Validate multi-reward framework

---

**Created**: 2025-12-20 15:15 UTC
**Author**: Claude Code Assistant
**Priority**: P0 (blocks all finetuning testing)
