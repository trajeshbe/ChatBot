# Finetuning Dataset Path - Complete Analysis & Solution

**Date**: 2025-12-21 12:00 UTC
**Trainings Tested**: 15, 16, 17, 18, 19, 20, 21 (ALL FAILED)

---

## THE PROBLEM

**Config files show**:
```json
"dataset_path": "/workspace/input"  ❌ WRONG!
```

**Should be**:
```json
"dataset_path": "/workspace/finetuning/{job_id}/input"  ✅ CORRECT
```

---

## FIXES ATTEMPTED (ALL FAILED)

| Fix # | File | What It Did | Why It Failed |
|-------|------|-------------|---------------|
| **Fix #1-4** | Various | Removed backend mount, added env vars, import os | Agent code stopped, but dataset path still wrong |
| **Fix #5** | `finetuning_sandbox_manager.py:549-551` | Override `config["dataset_path"]` before JSON write | **Config written BEFORE override happens!** |
| **Fix #6** | `finetuning_tasks.py:736` | Set correct path in Celery task | **Backend restarted but config STILL uses database value!** |

---

## ROOT CAUSE - THE FULL PICTURE

### 1. Database Stores Wrong Path
```sql
SELECT config FROM finetuning_jobs WHERE id = 'xxx';
-- Result: {"dataset_path": "/workspace/input", ...}
```

### 2. `execute_training` Is NOT CALLED From Celery!

**CRITICAL DISCOVERY**: The config JSON is written **OUTSIDE** of `execute_training`!

Let me find where the config is ACTUALLY written...

---

## HYPOTHESIS

The config file is written in **TWO PLACES**:

1. **Early write** (before `execute_training`) - This is what we're seeing!
2. **`execute_training` write** (line 554-556) - This never runs or runs later!

I need to find the FIRST write location.

---

## INVESTIGATION NEEDED

Search for ALL places that write `training_config.json`:

```bash
grep -rn "training_config.json" backend/app/services/finetuning/ backend/app/tasks/
```

Look for writes that happen BEFORE `execute_training` is called.

---

## ACTUAL SOLUTION (Not Yet Applied)

Once we find the FIRST write location, we need to EITHER:

### Option A: Remove the first write entirely
Let ONLY `execute_training` write the config.

### Option B: Fix the FIRST write
Override the path there as well:
```python
config["dataset_path"] = f"/workspace/finetuning/{job_id}/input"
```

---

## STATUS

- ✅ Identified root cause: Config written before our fixes run
- ❌ Haven't found the FIRST write location yet
- ❌ No working training job yet

---

**Next Step**: Search entire codebase for config writes, find the early one, fix it there.

---

**Date**: 2025-12-21 12:00 UTC
