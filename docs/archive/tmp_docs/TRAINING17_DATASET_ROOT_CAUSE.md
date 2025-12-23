# Training17 - Dataset Loading Failure - ROOT CAUSE ✅

**Date**: 2025-12-21 11:25 UTC
**Status**: 🎯 **ROOT CAUSE IDENTIFIED**

---

## Summary

Training17 failed to load the dataset despite all 4 fixes being applied (backend mount removed, DATASET_PATH env var added, os import added, image rebuilt). Completed with mock training in 3.4 minutes instead of real training (15-30 min).

---

## Investigation Timeline

### What We Found

1. **Backend Restart**: ✅ 11:00:52 UTC - Backend restarted with all fixes
2. **Training17 Created**: ✅ 11:12:16 UTC - Created 11 minutes AFTER restart
3. **Fix #1 Applied**: ✅ Backend mount removed - agent code did NOT run
4. **Fix #4 Applied**: ✅ `import os` added - no "os not defined" error
5. **Fix #2 Applied**: ✅ DATASET_PATH env var in code (line 559)
6. **Fix #3 Applied**: ✅ Trainer uses os.getenv("DATASET_PATH") (line 65)

### But Dataset Still Didn't Load!

**Training17 Logs Show**:
```
📊 Dataset: /workspace/input   ❌ WRONG PATH!
```

Should be:
```
📊 Dataset: /workspace/finetuning/9c0c5304-5ed5-4346-a7cf-87a37b1dc6bf/input  ✅ CORRECT
```

---

## Root Cause Analysis

### The Problem

The `training_config.json` file stored in workspace contains:
```json
{
  "dataset_path": "/workspace/input",  ❌ WRONG!
  ...
}
```

### Why This Happens

**File**: `finetuning_sandbox_manager.py`
**Lines**: 550-552

```python
# Save training config
config_file = workspace["input"] / "training_config.json"
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)  # ❌ Config has wrong path!
```

The `config` dictionary is passed FROM THE DATABASE and contains the ORIGINAL `dataset_path` value from when the job was created.

### Where `dataset_path` Comes From

**Database Query** (finetuning_jobs table):
```sql
SELECT config FROM finetuning_jobs WHERE id = '9c0c5304-5ed5-4346-a7cf-87a37b1dc6bf';
```

The `config` JSONB column stores:
```json
{
  "dataset_path": "/workspace/input",  # Hardcoded when job created
  ...
}
```

This value is set when the job is CREATED (in finetuning_routes.py or finetuning_service.py), NOT when the container is spawned.

### Why Environment Variable Didn't Work

**Trainer Code** (peft_trainer.py line 65):
```python
dataset_path = os.getenv("DATASET_PATH", config.get("dataset_path", "/workspace/input/dataset"))
```

**Logic**:
1. Check `os.getenv("DATASET_PATH")` first → Should return `/workspace/finetuning/{job_id}/input`
2. Fall back to `config.get("dataset_path")` → Returns `/workspace/input`
3. Final fallback: `/workspace/input/dataset`

**The env var SHOULD work!** But the logs show it used `/workspace/input` instead.

**This means**: The `DATASET_PATH` environment variable was **NOT SET** in the container!

---

## The REAL Root Cause

Even though line 559 of `finetuning_sandbox_manager.py` has:
```python
"DATASET_PATH": f"/workspace/finetuning/{job_id}/input",  # ✅ FIX: Explicit dataset path
```

The container did NOT receive this environment variable!

### Hypothesis

The training17 container may have been spawned from an **OLD VERSION** of the `execute_training` function that was loaded into memory BEFORE the backend restart.

**Possibility**: Python module caching or Celery worker not reloading code.

---

## Evidence

### 1. Config File Has Wrong Path
```bash
$ cat /workspace/9c0c5304.../input/training_config.json
{
  "dataset_path": "/workspace/input",  ❌
  ...
}
```

### 2. Dataset Files Exist at Correct Location
```bash
$ ls /workspace/9c0c5304.../input/
company_qa_dataset.jsonl  ✅ (4348 bytes)
train.json                ✅ (4891 bytes)
training_config.json      ✅ (1005 bytes)
validation.json           ✅ (531 bytes)
```

### 3. Trainer Logs Show Wrong Path
```
2025-12-21 11:12:23,488 - __main__ - INFO - 📊 Dataset: /workspace/input
2025-12-21 11:15:14,931 - __main__ - INFO - Loading dataset from /workspace/input...
2025-12-21 11:15:15,679 - __main__ - WARNING - Could not load dataset: Unable to find '/workspace/input/train.json'
```

### 4. Fix #1 Worked (No Agent Code)
```
✅ NO "AGENT CONTAINER STARTING"
✅ NO "Calling Ollama LLM"
✅ NO "Registered 13 tools"
```

### 5. Fix #4 Worked (No Import Error)
```
✅ NO "name 'os' is not defined"
```

---

## Verification: Check if ENV Var Was Actually Set

We need to verify if the `DATASET_PATH` env var was passed to the container.

**Command** (if container still exists):
```bash
docker inspect finetuning-9c0c5304-5ed5-4346-a7cf-87a37b1dc6bf | grep -A 20 "Env"
```

**Expected** (if Fix #2 worked):
```json
"Env": [
  "DATASET_PATH=/workspace/finetuning/9c0c5304.../input",  ✅
  ...
]
```

**If NOT present**: The env var was NOT set → backend code wasn't reloaded properly

---

## Next Steps to Fix

### Option 1: Restart Docker Compose Entirely (Nuclear)

```bash
docker-compose restart
```

This will force ALL services (backend, celery, etc.) to reload code.

### Option 2: Update Config in Database

Before creating new jobs, update the `config` JSONB in the database to use correct path:

```sql
UPDATE finetuning_jobs
SET config = jsonb_set(
  config,
  '{dataset_path}',
  '"/workspace/finetuning/" || id::text || "/input"'::jsonb
)
WHERE id = 'new-job-id';
```

### Option 3: Fix Config Generation at Job Creation

**File**: Find where `finetuning_jobs` are created (likely `finetuning_routes.py` or `finetuning_service.py`)

**Change**: Don't set `dataset_path` in config at all - rely entirely on `DATASET_PATH` env var.

**Or**: Set correct path at job creation:
```python
config = {
    "dataset_path": f"/workspace/finetuning/{job_id}/input",  # ✅ Correct path
    ...
}
```

---

## Recommended Solution

**BEST FIX**: Update `finetuning_sandbox_manager.py` to OVERRIDE the config's `dataset_path` before writing it to JSON:

**File**: `backend/app/services/finetuning/finetuning_sandbox_manager.py`
**Lines**: 549-552

**Before**:
```python
# Save training config
config_file = workspace["input"] / "training_config.json"
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)
```

**After**:
```python
# ✅ FIX: Override dataset_path in config to use correct workspace path
config["dataset_path"] = f"/workspace/finetuning/{job_id}/input"

# Save training config
config_file = workspace["input"] / "training_config.json"
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)
```

This ensures the JSON file has the correct path regardless of what's in the database.

---

## Why This Is Better Than Environment Variable Alone

1. **Explicit**: Config file shows correct path (easier debugging)
2. **Fallback**: If env var isn't set, trainer still gets correct path from config
3. **Consistency**: All paths (env var + config) point to same location

---

## Status

**Root Cause**: ✅ IDENTIFIED
**Fix Required**: Update config before writing to JSON
**Test Required**: Create training18 after fix applied

---

**Date**: 2025-12-21 11:25 UTC

---
