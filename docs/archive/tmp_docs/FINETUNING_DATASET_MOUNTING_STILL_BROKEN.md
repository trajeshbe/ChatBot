# Fine-Tuning Dataset Mounting - Still Broken Analysis

**Date**: 2025-12-20 17:22 UTC
**Job**: choles-qa-real-training4
**Job ID**: 230020cb-6397-4c7d-ab52-88dccbca9978
**Status**: Completed in MOCK MODE (no real training)

---

## Summary

Despite applying fixes and restarting Celery, the training job STILL ran in mock mode. The dataset download is working, but there's a disconnect between WHERE the dataset is downloaded and WHERE the trainer is looking for it.

---

## What's Working ✅

1. **Dataset found in MinIO**: `✅ Found dataset in MinIO: technology/itm11/.../company_qa_dataset.jsonl`
2. **MinIO client using correct bucket**: `✅ MinIO client initialized (bucket: documents)`
3. **Dataset downloaded to HOST**: `✅ Downloaded dataset to /workspace/finetuning/230020cb-.../input/company_qa_dataset.jsonl (4348 bytes)`
4. **Training container started**: Container spawned successfully
5. **Model loaded**: Qwen 1.5B loaded with 4-bit quantization
6. **dataset_path passed in config**: Config shows `"dataset_path": "technology/itm11/.../company_qa_dataset.jsonl"`

---

## What's NOT Working ❌

1. **Trainer can't find dataset file**: Logs show `Using dummy dataset for testing`
2. **No TensorBoard metrics**: No `events.out.tfevents.*` files generated
3. **Mock training executed**: Untrained LoRA adapters saved
4. **Empty TensorBoard dashboards**: No loss graphs, no metrics

---

## Root Cause Analysis

### Path Mismatch Issue

**Dataset downloaded to (HOST)**:
```
/workspace/finetuning/230020cb-6397-4c7d-ab52-88dccbca9978/input/company_qa_dataset.jsonl
```

**Container workspace mount**:
```
docker run -v /tmp/finetuning_workspaces/230020cb-...:/workspace
```

**Trainer looking for**:
```
technology/itm11/global/admin/finetuning/datasets/company_qa_dataset/.../company_qa_dataset.jsonl
```

**THE PROBLEM**: The `dataset_path` being passed is the **MinIO relative path**, NOT the local filesystem path where the file was downloaded!

---

## The Fix That's Needed

### Current Code Flow (BROKEN):

```python
# In finetuning_tasks.py
dataset_minio_path = dataset.minio_path
# = "technology/itm11/.../company_qa_dataset.jsonl"

training_config = {
    "dataset_path": dataset_minio_path,  # ❌ MinIO path, not filesystem path!
    ...
}

# In finetuning_sandbox_manager.py
dataset_path = config.get("dataset_path")
# Downloads to: /workspace/finetuning/{job_id}/input/company_qa_dataset.jsonl

# But trainer receives: "technology/itm11/.../company_qa_dataset.jsonl"
# And looks for: /workspace/technology/itm11/... (doesn't exist!)
```

### Required Fix:

```python
# Option 1: Pass the LOCAL path instead of MinIO path
training_config = {
    "dataset_path": "/workspace/input/company_qa_dataset.jsonl",  # ✅ Where file actually is
    ...
}

# Option 2: Download AND update config with actual downloaded path
downloaded_path = await self.create_training_workspace(job_id, dataset_path=dataset_minio_path)
training_config["dataset_path"] = downloaded_path  # Update with actual path
```

---

## Evidence from Logs

### Celery Logs (Dataset Download - Working):
```
[2025-12-20 17:14:31] ✅ Found dataset in MinIO: technology/itm11/.../company_qa_dataset.jsonl
[2025-12-20 17:14:31] ✅ MinIO client initialized (bucket: documents)
[2025-12-20 17:14:31] 📦 Downloading dataset from MinIO: technology/itm11/...
[2025-12-20 17:14:31] ✅ Downloaded dataset to /workspace/finetuning/230020cb-.../input/company_qa_dataset.jsonl (4348 bytes)
```

### Training Container Logs (File Not Found - Broken):
```
2025-12-20 17:14:35 - INFO - 📊 Dataset: technology/itm11/.../company_qa_dataset.jsonl
2025-12-20 17:18:55 - INFO - Loading dataset from technology/itm11/.../company_qa_dataset.jsonl...
2025-12-20 17:18:56 - INFO - Using dummy dataset for testing
```

The trainer tried to load from `technology/itm11/...` (relative MinIO path) but the file is actually at `/workspace/input/company_qa_dataset.jsonl`.

---

## Dataset Preview Issue (Separate Bug)

**Question**: "btw. is there a way to preview the dataset?? the samples, overview, quality view doesn't show anything"

**Answer**: The dataset file HAS data (4348 bytes), but the UI preview is empty because the background validation task never ran after upload.

**Database State**:
```sql
num_samples: NULL
sample_rows: NULL
is_valid: false
```

**Solution**: The validation task should:
1. Download dataset from MinIO
2. Parse and count samples
3. Extract first 3-5 rows for preview
4. Update database with metadata

This task either never ran or failed silently during upload.

---

## Next Steps

### Fix 1: Correct the dataset_path

**File**: `backend/app/services/finetuning/trainers/peft_trainer.py` (or wherever trainer code loads dataset)

Change from:
```python
dataset_path = config.get("dataset_path")  # MinIO relative path
# Tries to open: technology/itm11/.../file.jsonl
```

To:
```python
# Resolve to actual filesystem path
dataset_filename = os.path.basename(config.get("dataset_path", ""))
dataset_path = f"/workspace/input/{dataset_filename}"
```

OR

**File**: `backend/app/tasks/finetuning_tasks.py`

Change from:
```python
training_config = {
    "dataset_path": dataset_minio_path,  # MinIO path
    ...
}
```

To:
```python
# Extract just the filename
dataset_filename = os.path.basename(dataset_minio_path) if dataset_minio_path else None
training_config = {
    "dataset_path": f"/workspace/input/{dataset_filename}" if dataset_filename else None,
    ...
}
```

### Fix 2: Dataset Preview Validation

Ensure the background validation task runs after dataset upload to populate:
- `num_samples`
- `sample_rows`
- `is_valid`

---

## Verification Checklist

After applying the fix:

- [ ] Create new training job
- [ ] Trainer logs show: `✅ Loaded X training samples` (NOT "Using dummy dataset")
- [ ] Training progresses with loss values
- [ ] TensorBoard event files created
- [ ] TensorBoard dashboard shows loss graphs
- [ ] Model is actually trained (not untrained adapters)

---

**Created**: 2025-12-20 17:22 UTC
**Author**: Claude Code Assistant
**Priority**: P0 CRITICAL - Blocks all real finetuning
**Status**: Investigation complete, fix identified

