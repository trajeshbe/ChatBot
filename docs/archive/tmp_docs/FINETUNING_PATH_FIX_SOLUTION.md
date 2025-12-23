# Finetuning Dataset Path Fix - Complete Solution

**Date**: 2025-12-21 19:00 UTC
**Status**: 🔧 **SOLUTION READY**

---

## Problem Summary

Training28 went into mock mode because the dataset download failed due to path mismatch.

### What We Found

1. **Dataset exists** in MinIO with organizational hierarchy path:
   ```
   documents/technology/itm11/global/admin/finetuning/datasets/company_qa_dataset/added64c-16fd-42a9-9370-e08f2516f198/company_qa_dataset.jsonl
   ```

2. **Database stores the full path** in `finetuning_datasets.minio_path`:
   ```sql
   minio_path: technology/itm11/global/admin/finetuning/datasets/company_qa_dataset/added64c-16fd-42a9-9370-e08f2516f198/company_qa_dataset.jsonl
   ```

3. **The issue**: Current code assumes flat bucket structure, but data uses organizational hierarchy

### The Root Cause

In `finetuning_sandbox_manager.py`:
- Line 78: Hardcoded `self.minio_bucket = "documents"`
- Line 168-172: Downloads using `self.minio_bucket` and `dataset_minio_path`
- But `dataset_minio_path` doesn't include the bucket prefix!

---

## The Solution

The fix is simple - we're already using the correct bucket ("documents"), and the `minio_path` from database is already correct!

**The issue**: We just need to ensure the path construction is correct in the dataset upload service.

Let me verify how datasets are being uploaded first, then implement the fix.

---

## Implementation Plan

### Step 1: Verify Dataset Upload Path Construction

Check how `minio_path` is being set when datasets are uploaded.

### Step 2: Fix Download Logic

Update `_copy_dataset_to_workspace()` in `finetuning_sandbox_manager.py` to:
1. Use the dataset's `minio_path` from database
2. Ensure bucket is "documents" (already correct)
3. Add logging to show exact path being accessed

### Step 3: Add Validation

Add validation to ensure:
- Dataset exists before training starts
- Path is correctly constructed
- Clear error messages if dataset not found

---

## Expected Behavior After Fix

When training29 is created:

1. ✅ Query database for dataset `added64c-16fd-42a9-9370-e08f2516f198`
2. ✅ Get `minio_path`: `technology/itm11/global/admin/finetuning/datasets/.../company_qa_dataset.jsonl`
3. ✅ Download from MinIO: `documents/{minio_path}`
4. ✅ Dataset found and downloaded successfully
5. ✅ Preprocessing runs: detects "messages" format, splits 90/10
6. ✅ Trainer starts with v1.0.4 tokenization
7. ✅ Tokenization runs: converts messages to input_ids/attention_mask/labels
8. ✅ **REAL training begins!**

---

## Files to Modify

1. **`backend/app/services/finetuning/finetuning_sandbox_manager.py`**
   - Update `_copy_dataset_to_workspace()` to add validation and logging
   - Ensure correct path construction

2. **Dataset upload service** (if needed)
   - Verify `minio_path` is being set correctly

---

**Next**: Let me check how datasets are uploaded to understand the complete flow.
