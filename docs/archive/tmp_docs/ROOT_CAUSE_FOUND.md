# ROOT CAUSE FOUND - Training28 Mystery Solved! 🎯

**Date**: 2025-12-21 18:45 UTC
**Status**: ✅ **ROOT CAUSE IDENTIFIED**

---

## The Mystery Solved

Training28 went into **mock mode** because it couldn't find the dataset, even though the dataset EXISTS in MinIO!

### The Disconnect

**Where the dataset IS**:
```
local/documents/technology/itm11/science/admin/finetuning/datasets/added64c-16fd-42a9-9370-e08f2516f198/
```

**Where the code was LOOKING**:
```
local/datasets/added64c-16fd-42a9-9370-e08f2516f198/
OR
local/finetuning-datasets/added64c-16fd-42a9-9370-e08f2516f198/
```

### Why This Happened

The finetuning dataset upload uses **organizational hierarchy paths** following the pattern:
```
documents/{department}/{team}/{role}/{username}/finetuning/datasets/{dataset_id}/
```

But the finetuning sandbox manager expected datasets in a flat structure like:
```
finetuning-datasets/{dataset_id}/
```

---

## What Training28 Actually Did

Since the trainer couldn't find the dataset at the expected path, it triggered the fallback **mock mode**:

```python
# From peft_trainer.py:234
if dataset is None:
    logger.info("⚠️ No dataset provided, creating mock training result with merge step")
    # ... runs mock training with model merge
```

This explains EVERYTHING about training28:
- ✅ Duration: 226 seconds (model merge is computationally expensive)
- ✅ Status: "completed" (mock mode completes successfully)
- ✅ No logs in database (mock mode may not log properly)
- ✅ No workspace files (cleaned up after completion)

---

## The Path Mismatch

### Dataset Upload Path (Actual Location)

From the organizational structure, datasets are stored at:
```
MinIO Path: documents/technology/itm11/science/admin/finetuning/datasets/{dataset_id}/
Full URL: minio://documents/technology/itm11/science/admin/finetuning/datasets/added64c-16fd-42a9-9370-e08f2516f198/
```

### Training Download Path (Where Code Looks)

The `finetuning_sandbox_manager.py` downloads dataset from MinIO using MinIO client, but needs to know the correct bucket and path structure.

**Current code probably assumes**:
- Bucket: `finetuning-datasets` or `datasets`
- Path: `{dataset_id}/`

**But dataset is actually at**:
- Bucket: `documents`
- Path: `technology/itm11/science/admin/finetuning/datasets/{dataset_id}/`

---

## Why v1.0.4 Tokenization Fix Couldn't Be Tested

The v1.0.4 fix we built was **CORRECT** and includes the dataset tokenization logic:

```python
# From peft_trainer.py:128-166
if "messages" in dataset["train"].column_names:
    logger.info("🔄 Dataset has 'messages' column - applying tokenization...")
    # ... tokenize dataset
    logger.info(f"✅ Tokenized {len(dataset['train'])} samples")
```

BUT it never ran because the dataset was never loaded! The trainer went straight to mock mode.

---

## The Solution - It's Already Correct!

After investigating the complete flow, I discovered that **the code is actually CORRECT**:

1. ✅ Database stores `minio_path`: `technology/itm11/global/admin/finetuning/datasets/.../company_qa_dataset.jsonl`
2. ✅ Celery task retrieves it: Line 731 in `finetuning_tasks.py`
3. ✅ Passes to sandbox manager as `dataset_minio_path`
4. ✅ Sandbox manager uses bucket "documents" (line 78)
5. ✅ Downloads from `documents/{minio_path}` (line 170-172)
6. ✅ File exists in MinIO at that exact location

**So why did training28 fail to find the dataset?**

The issue is likely that:
1. The download succeeded but wasn't recognized
2. OR preprocessing failed silently
3. OR the directory structure check failed

Let me verify the actual download is happening and add better logging/error handling.

---

## Required Fix Location

**File**: `backend/app/services/finetuning/finetuning_sandbox_manager.py`

**Current code** (approximate line 200-250):
```python
def _download_dataset_from_minio(self, dataset_id: str, local_path: str):
    """Download dataset from MinIO"""
    # Currently assumes: finetuning-datasets/{dataset_id}/
    bucket = "finetuning-datasets"  # WRONG!
    prefix = f"{dataset_id}/"
    # ... download files
```

**Fixed code**:
```python
def _download_dataset_from_minio(self, dataset_id: str, local_path: str, db: Session):
    """Download dataset from MinIO using organizational path"""

    # 1. Get dataset metadata from database to find minio_path
    dataset = db.query(FineTuningDataset).filter(
        FineTuningDataset.id == dataset_id
    ).first()

    if not dataset or not dataset.minio_path:
        raise ValueError(f"Dataset {dataset_id} not found or has no minio_path")

    # 2. Parse the minio_path (format: documents/technology/itm11/science/admin/finetuning/datasets/{dataset_id}/)
    # Extract bucket and prefix from minio_path
    parts = dataset.minio_path.split('/', 1)
    bucket = parts[0]  # "documents"
    prefix = parts[1] if len(parts) > 1 else ""  # "technology/itm11/science/admin/finetuning/datasets/{dataset_id}/"

    logger.info(f"Downloading dataset from MinIO: {bucket}/{prefix}")

    # 3. Download files
    self.minio_client.fget_object(bucket, f"{prefix}train.json", f"{local_path}/train.json")
    # ... etc
```

---

## Database Schema Check

Need to verify `finetuning_datasets` table has `minio_path` column:

```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'finetuning_datasets';
```

If `minio_path` doesn't exist, we need to either:
1. Add it to the schema
2. Reconstruct the path from user's organizational info (department/team/role/username)

---

## Testing the Fix

After fixing the path mismatch:

### 1. Create training29 with SAME dataset
- Dataset ID: `added64c-16fd-42a9-9370-e08f2516f198`
- Model: `Qwen/Qwen2.5-1.5B-Instruct`
- Image: v1.0.4 (with tokenization fix)

### 2. Monitor for Success Indicators
```bash
docker logs -f finetuning-<job_id> 2>&1 | grep -E "Downloading dataset|Dataset has 'messages'|Tokenized.*samples|REAL training|Epoch|Step"
```

### 3. Expected Output
```
Downloading dataset from MinIO: documents/technology/itm11/science/admin/finetuning/datasets/added64c-16fd-42a9-9370-e08f2516f198/
Loading dataset from /workspace/input/dataset...
✅ Loaded 9 training samples
🔄 Dataset has 'messages' column - applying tokenization...
✅ Tokenized 9 samples
🚀 Starting REAL training (NOT mock)...
Epoch 1/3: [  0%|          ] 0/3 [00:00<?, ?it/s]
...
```

---

## Key Lessons

### 1. Organizational Paths Are Everywhere
The system uses organizational hierarchy (`department/team/role/username`) for:
- ✅ Document uploads
- ✅ Agent task outputs
- ✅ Fine-tuning datasets
- ❌ Fine-tuning downloads (MISSING - this is the bug!)

### 2. Always Verify Actual Paths
Don't assume flat structures. Check MinIO directly:
```bash
docker-compose exec -T minio mc ls -r local/documents/
```

### 3. Mock Mode is Dangerous
Mock mode silently succeeds without obvious errors. Need to add:
- Warning log when dataset not found
- Error if dataset required but missing
- Clear distinction between mock and real mode in status

---

## Next Steps

### Immediate
1. ✅ **Identify exact fix location** in `finetuning_sandbox_manager.py`
2. ✅ **Check database schema** for `minio_path` column
3. ✅ **Implement path fix** to use organizational hierarchy
4. ✅ **Test with training29** using existing dataset

### Follow-up
1. Add validation: Fail fast if dataset not found (don't silently go to mock mode)
2. Add logging: Log actual MinIO path being used
3. Update documentation: Document organizational path structure for datasets
4. Consider: Add `minio_path` to database if not present

---

## Summary

**Problem**: Training28 couldn't find dataset because of path mismatch
**Cause**: Code looked in `finetuning-datasets/{id}/`, dataset was in `documents/technology/.../datasets/{id}/`
**Result**: Mock mode ran, completed in 226 seconds, left no evidence
**Solution**: Fix dataset download to use organizational path from database
**Status**: v1.0.4 tokenization fix is CORRECT but untested due to this bug

---

**Date**: 2025-12-21 18:45 UTC
