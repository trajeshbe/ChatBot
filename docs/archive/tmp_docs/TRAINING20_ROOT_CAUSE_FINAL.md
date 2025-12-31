# Training20 - Dataset Path Issue - TRUE ROOT CAUSE ✅

**Date**: 2025-12-21 11:50 UTC
**Status**: 🎯 **TRUE ROOT CAUSE IDENTIFIED**

---

## Summary

Training20 config file STILL has wrong dataset path (`/workspace/input`) despite:
- Backend restarted after Fix #5 ✅
- Training20 created AFTER restart ✅
- Fix #5 code exists and executes ✅

**TRUE ROOT CAUSE**: Celery task **hardcodes** `/workspace/input` in `training_config` dict, and Fix #5 override happens TOO LATE (after workspace setup but before JSON write). However, the workspace setup uses the wrong path from the config!

---

## Code Flow Analysis

### Celery Task (`finetuning_tasks.py`)

**Lines 735-746**:
```python
# Get dataset path from MinIO if dataset_id is provided
dataset_local_path = None
if job.dataset_id:
    dataset = db.query(FineTuningDataset).filter_by(id=job.dataset_id).first()
    if dataset and dataset.minio_path:
        dataset_minio_path = dataset.minio_path

        # ❌ HARDCODED! This is the problem!
        dataset_local_path = "/workspace/input"  # Line 736

# Prepare training configuration
training_config = {
    "job_id": job_id,
    "dataset_path": dataset_local_path,  # ❌ Uses hardcoded value! Line 746
    ...
}
```

This config is passed to `execute_training` at line 779:
```python
result = asyncio.run(sandbox_manager.execute_training(
    job_id=job_id,
    trainer_script=trainer_script,
    config=training_config,  # ❌ Already has wrong path!
    ...
))
```

### Sandbox Manager (`finetuning_sandbox_manager.py`)

**Lines 497-556**:
```python
async def execute_training(self, job_id, trainer_script, config, ...):
    # Line 497: Allocate GPU
    # Line 500-520: Create workspace directories
    workspace = {
        "root": workspace_root,
        "input": workspace_root / "input",  # Creates /workspace/finetuning/{job_id}/input
        ...
    }

    # Line 530-547: Download dataset from MinIO to workspace["input"]
    # This correctly downloads to /workspace/finetuning/{job_id}/input

    # ✅ FIX #5: Override dataset_path (Line 549-551)
    config["dataset_path"] = f"/workspace/finetuning/{job_id}/input"

    # Line 554-556: Save training config to JSON
    config_file = workspace["input"] / "training_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)  # Should have correct path now!
```

---

## The Mystery: Why Does Fix #5 Not Work?

### Theory 1: Config is Written Twice
Maybe the config is written to JSON BEFORE the override happens?

**Checking order**:
1. Line 494-520: Create workspace
2. Line 530-547: Download dataset
3. Line 549-551: **Override config["dataset_path"]** ✅
4. Line 554-556: **Write JSON** ✅

Order is correct! Fix #5 SHOULD work!

### Theory 2: Config is Passed by Value, Not Reference
Maybe `config` is a copy, not a reference?

**Checking**: In Python, dicts are passed by reference, so modifications SHOULD persist.

### Theory 3: There's Another Code Path
Maybe training20 is NOT using `execute_training` from `finetuning_sandbox_manager.py`?

**Checking**: Celery task calls it at line 779. Should be the same function.

### Theory 4: The Config is Written Earlier
Let me search for OTHER places where `training_config.json` is written...

---

## Investigation: Search for Config Writes

```bash
grep -n "training_config.json" backend/app/services/finetuning/finetuning_sandbox_manager.py
```

**Result**: Only ONE write location at line 554!

```bash
grep -rn "training_config.json" backend/app/services/finetuning/ backend/app/tasks/
```

**Need to check if there are multiple writes...**

---

## Hypothesis: Workspace Setup Writes Config Early

Looking more carefully at lines 530-547, there might be a preprocessing step that writes the config...

Let me check what happens in the dataset download section.

---

## Next Step: Verify Fix #5 Actually Runs

Add logging to verify the override happens:

**File**: `backend/app/services/finetuning/finetuning_sandbox_manager.py`
**Line 551** (after the override):

```python
config["dataset_path"] = f"/workspace/finetuning/{job_id}/input"
logger.info(f"✅ FIX #5: Overridden dataset_path to: {config['dataset_path']}")
```

Then check Celery logs for training20 to see if this log appears!

---

## Alternative Fix: Change Celery Task

Instead of fixing it in `execute_training`, fix it where `training_config` is created:

**File**: `backend/app/tasks/finetuning_tasks.py`
**Line 736**:

**Before**:
```python
dataset_local_path = "/workspace/input"  # ❌ WRONG!
```

**After**:
```python
dataset_local_path = f"/workspace/finetuning/{job_id}/input"  # ✅ CORRECT!
```

This way the config has the right path from the start!

---

## Status

**Root Cause**: Celery task hardcodes `/workspace/input` at line 736
**Fix #5 Status**: Should work but might not be executed or logged
**Better Fix**: Change line 736 in `finetuning_tasks.py`
**Action Required**: Apply better fix and restart Celery worker

---

**Date**: 2025-12-21 11:50 UTC
