# Option C: Database Debug Logging - Implementation Complete

**Date**: 2025-12-21 20:30 UTC
**Status**: ✅ **DATABASE LOGGING IMPLEMENTED**

---

## What Was Implemented

### 1. Database Schema Migration ✅

Added `debug_log` column to `finetuning_jobs` table:

```sql
ALTER TABLE finetuning_jobs
ADD COLUMN IF NOT EXISTS debug_log TEXT[] DEFAULT ARRAY[]::TEXT[];

CREATE INDEX IF NOT EXISTS idx_finetuning_jobs_debug_log
ON finetuning_jobs USING GIN (debug_log);
```

**Benefits**:
- Persistent logging that survives container removal
- Fast array operations in PostgreSQL
- GIN index for efficient querying
- No additional infrastructure needed

### 2. Debug Logging Helper Method ✅

Added `_log_debug()` method to `FineTuningSandboxManager` class (lines 93-133):

```python
async def _log_debug(self, job_id: str, message: str):
    """
    Add timestamped debug message to job's debug_log array in database

    This allows us to trace the training pipeline even after container removal
    """
    try:
        from app.core.database import get_db
        from sqlalchemy.orm import Session

        # Create database session
        db_gen = get_db()
        db: Session = next(db_gen)

        try:
            # Get current timestamp
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            log_entry = f"[{timestamp}] {message}"

            # Update job's debug_log array using PostgreSQL array append
            from sqlalchemy import text
            db.execute(
                text("""
                    UPDATE finetuning_jobs
                    SET debug_log = array_append(debug_log, :log_entry)
                    WHERE id = :job_id
                """),
                {"job_id": job_id, "log_entry": log_entry}
            )
            db.commit()

            # Also log to console for immediate visibility
            logger.info(f"[{job_id[:8]}] {message}")

        finally:
            db.close()

    except Exception as e:
        # Don't fail training if logging fails
        logger.warning(f"Debug logging failed for job {job_id}: {e}")
```

**Features**:
- Timestamped messages (millisecond precision)
- PostgreSQL array append for atomic operations
- Graceful degradation (won't fail training if logging fails)
- Dual logging (database + console)
- Short job ID prefix for readability

---

## Next Steps: Add Logging Calls

### Where to Add `await self._log_debug(job_id, message)`

#### 1. In `_copy_dataset_to_workspace()` Method

**Current signature**:
```python
async def _copy_dataset_to_workspace(
    self,
    dataset_minio_path: str,
    input_dir: Path
):
```

**Needs to become**:
```python
async def _copy_dataset_to_workspace(
    self,
    dataset_minio_path: str,
    input_dir: Path,
    job_id: str  # ADD THIS PARAMETER
):
```

**Add logging at these points**:
```python
# Line ~204: Before download
await self._log_debug(job_id, f"📦 Starting dataset download from MinIO")
await self._log_debug(job_id, f"   Bucket: {self.minio_bucket}")
await self._log_debug(job_id, f"   Object: {dataset_minio_path}")

# Line ~226: After download
await self._log_debug(job_id, f"✅ Downloaded dataset: {filename} ({file_size:,} bytes)")

# Line ~235: After first-line preview
await self._log_debug(job_id, f"   Preview: {preview}")

# Line ~242: On error
await self._log_debug(job_id, f"❌ MinIO download failed: {e}")
```

#### 2. In `execute_training()` Method

**Add logging at these critical points**:

```python
# After dataset validation (line ~547)
await self._log_debug(job_id, f"🔍 Validating dataset exists in MinIO")
await self._log_debug(job_id, f"✅ Dataset found: {dataset_minio_path} ({stat.size:,} bytes)")

# OR on failure
await self._log_debug(job_id, f"❌ Dataset NOT found: {dataset_minio_path}")

# When calling _copy_dataset_to_workspace (line ~587)
await self._copy_dataset_to_workspace(dataset_minio_path, workspace["input"], job_id)

# After listing files (line ~593)
await self._log_debug(job_id, f"📁 Files in input directory: {[f.name for f in dataset_files]}")

# After finding dataset file (line ~603)
await self._log_debug(job_id, f"✅ Found dataset file: {dataset_file.name} ({dataset_file.stat().st_size:,} bytes)")

# Before preprocessing (line ~605)
await self._log_debug(job_id, f"🔄 Preprocessing dataset (objective: {training_objective})")

# After preprocessing success (line ~620)
await self._log_debug(job_id, f"✅ Preprocessing complete: train.json created")
await self._log_debug(job_id, f"   Size: {train_json.stat().st_size:,} bytes")

# On preprocessing error (line ~628)
await self._log_debug(job_id, f"❌ Preprocessing failed: {e}")

# Before starting Docker container (line ~710)
await self._log_debug(job_id, f"🚀 Starting training container")

# After container starts (line ~740)
await self._log_debug(job_id, f"✅ Container started: {container.id[:12]}")
```

---

## Testing the Implementation

### Create Training30 with Database Logging

Once the logging calls are added, create training30 and check the debug_log:

```sql
-- View debug log for training30
SELECT
    id,
    status,
    training_stage,
    debug_log
FROM finetuning_jobs
WHERE id = 'training30-job-id'
ORDER BY created_at DESC
LIMIT 1;

-- View just the debug log (formatted)
SELECT unnest(debug_log) AS log_entry
FROM finetuning_jobs
WHERE id = 'training30-job-id';
```

**Expected Output**:
```
[2025-12-21 20:35:01.234] 🔍 Validating dataset exists in MinIO
[2025-12-21 20:35:01.456] ✅ Dataset found: technology/itm11/.../company_qa_dataset.jsonl (4,321 bytes)
[2025-12-21 20:35:02.123] 📦 Starting dataset download from MinIO
[2025-12-21 20:35:02.124]    Bucket: documents
[2025-12-21 20:35:02.125]    Object: technology/itm11/global/admin/finetuning/datasets/...
[2025-12-21 20:35:02.987] ✅ Downloaded dataset: company_qa_dataset.jsonl (4,321 bytes)
[2025-12-21 20:35:03.012]    Preview: {"messages": [{"role": "user", "content": "What is Choles?"}...
[2025-12-21 20:35:03.234] 📁 Files in input directory: ['company_qa_dataset.jsonl']
[2025-12-21 20:35:03.456] ✅ Found dataset file: company_qa_dataset.jsonl (4,321 bytes)
[2025-12-21 20:35:03.567] 🔄 Preprocessing dataset (objective: instruction)
[2025-12-21 20:35:04.123] ✅ Preprocessing complete: train.json created
[2025-12-21 20:35:04.124]    Size: 15,234 bytes
[2025-12-21 20:35:05.000] 🚀 Starting training container
[2025-12-21 20:35:06.123] ✅ Container started: finetuning-abc
```

**OR if it fails**:
```
[2025-12-21 20:35:01.234] 🔍 Validating dataset exists in MinIO
[2025-12-21 20:35:01.456] ❌ Dataset NOT found: technology/itm11/.../missing.jsonl
```

---

## Advantages of This Approach

### 1. **Persistence** ✅
- Logs survive container removal
- Can inspect days/weeks later
- No dependency on Docker logs retention

### 2. **Query**able ✅
```sql
-- Find all failed jobs
SELECT id, unnest(debug_log) AS log_entry
FROM finetuning_jobs
WHERE 'failed' = ANY(debug_log);

-- Find jobs that went into mock mode
SELECT id, created_at
FROM finetuning_jobs
WHERE 'Mock' = ANY(debug_log);

-- Find dataset download failures
SELECT id, unnest(debug_log) AS log_entry
FROM finetuning_jobs
WHERE '❌ MinIO download failed' = ANY(debug_log);
```

### 3. **Minimal Overhead** ✅
- Single database UPDATE per log entry
- No file I/O
- No additional containers
- GIN index makes queries fast

### 4. **No Code Changes to Celery** ✅
- Works within existing sandbox manager
- No changes to task queue
- No changes to Docker orchestration

### 5. **Debugging Power** ✅
- See exact point of failure
- Track timing between steps
- Compare successful vs failed jobs

---

## Remaining Work

### Immediate (Required for Training30)

1. **Update `_copy_dataset_to_workspace()` signature**:
   - Add `job_id: str` parameter
   - Add 6 logging calls (download start, success, preview, error, etc.)

2. **Update `execute_training()` calls**:
   - Pass `job_id` when calling `_copy_dataset_to_workspace()`
   - Add ~8 logging calls (validation, file listing, preprocessing, container start, etc.)

3. **Restart Celery worker**:
   ```bash
   docker-compose restart celery
   ```

4. **Test with Training30**:
   - Create new job
   - Query debug_log immediately after completion
   - Analyze exactly where it fails

### Optional Enhancements

1. **Add logging to trainer script** (`peft_trainer.py`):
   - Log when dataset is loaded
   - Log when tokenization runs
   - Log when training starts (REAL vs mock)

2. **Add log viewer endpoint**:
   ```python
   @router.get("/api/v1/finetuning/jobs/{job_id}/debug-log")
   async def get_debug_log(job_id: str):
       # Return formatted debug log
   ```

3. **Add frontend display**:
   - Show debug log in job details
   - Real-time log streaming while job runs

---

## Files Modified

1. **Database Schema** (via SQL migration):
   - Added `debug_log TEXT[]` column
   - Added GIN index

2. **`backend/app/services/finetuning/finetuning_sandbox_manager.py`**:
   - Lines 93-133: Added `_log_debug()` method

---

## Summary

**Status**: Database logging infrastructure is complete ✅

**Ready for**: Adding logging calls to critical steps

**Next step**: Modify `_copy_dataset_to_workspace()` and `execute_training()` to add the ~14 logging calls, then create training30

**Expected outcome**: After training30 completes (or fails), we'll have a complete trace of exactly what happened during dataset download and preprocessing, even after the container is removed!

---

**Implementation Date**: 2025-12-21 20:30 UTC
**Implemented by**: Claude Code Assistant
**Status**: ✅ Infrastructure Complete - Logging Calls Pending
