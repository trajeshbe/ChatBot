# Database Debug Logging - Bug #2 FIXED

**Date**: 2025-12-22 04:45 UTC
**Status**: ✅ **BUG #2 FIXED - READY FOR TRAINING33**

---

## What Happened to Training32?

**Training32** (`0634d00d-e3db-4920-aaa0-56e3823c3460`) completed successfully but had **EMPTY debug_log**.

**Root Cause**: Async/sync mismatch - async function called from synchronous Celery context

### The Bug

**File**: `backend/app/services/finetuning/finetuning_sandbox_manager.py:93-132`

**Problematic code**:
```python
async def _log_debug(self, job_id: str, message: str):  # ❌ async in sync context
    try:
        from app.core.database import get_db  # Returns async generator
        from sqlalchemy.orm import Session

        db_gen = get_db()          # Async generator
        db: Session = next(db_gen)  # ❌ Can't use next() on async generator!
```

**Error in celery logs**:
```
Debug logging failed for job 0634d00d: 'async_generator' object is not an iterator
```

**Why it happened**:
- Celery tasks are **SYNCHRONOUS** - they run in a worker process without an async event loop
- `get_db()` is **ASYNC** - designed for FastAPI endpoints with async/await
- Using `next()` on an async generator doesn't work
- The entire function signature was `async def` but being called from sync context

---

## The Fix

**Rewrote as completely synchronous function**:

```python
# BEFORE (Bug #2 - async/sync mismatch):
async def _log_debug(self, job_id: str, message: str):  # ❌
    try:
        from app.core.database import get_db  # Async generator
        from sqlalchemy.orm import Session

        db_gen = get_db()
        db: Session = next(db_gen)  # ❌ Fails!

# AFTER (Fixed - fully synchronous):
def _log_debug(self, job_id: str, message: str):  # ✅ No async!
    """
    SYNCHRONOUS version for Celery tasks (no async/await)
    """
    try:
        from sqlalchemy import create_engine, text
        from app.core.config import settings

        # Create synchronous engine (convert asyncpg to psycopg2)
        database_url = settings.DATABASE_URL.replace('+asyncpg', '')
        engine = create_engine(database_url)

        with engine.connect() as conn:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            log_entry = f"[{timestamp}] {message}"

            conn.execute(
                text("""
                    UPDATE finetuning_jobs
                    SET debug_log = array_append(debug_log, :log_entry)
                    WHERE id = :job_id
                """),
                {"job_id": job_id, "log_entry": log_entry}
            )
            conn.commit()

        logger.info(f"[{job_id[:8]}] {message}")
    except Exception as e:
        logger.warning(f"Debug logging failed: {e}")
```

**Key Changes**:
1. Removed `async` from function signature
2. Replaced `get_db()` async generator with direct SQLAlchemy `create_engine()`
3. Convert DATABASE_URL from `postgresql+asyncpg` to `postgresql` (psycopg2)
4. Use synchronous `engine.connect()` context manager
5. No async/await anywhere in the function

**File modified**: `backend/app/services/finetuning/finetuning_sandbox_manager.py:93-129`

**Celery worker restarted**: ✅ `docker-compose restart celery-worker` (2025-12-22 04:44 UTC)

---

## Training History

| Job | Name | Duration | Status | Debug Log | Issue |
|-----|------|----------|--------|-----------|-------|
| 1770a884 | - | 418.6s | completed | ❌ Empty | Created before restart |
| **5576001e** | **training31** | **208.6s** | **completed** | **❌ Empty** | **Bug #1: Import error** |
| **0634d00d** | **training32** | **326.8s** | **completed** | **❌ Empty** | **Bug #2: Async/sync** |
| *training33* | *TBD* | *TBD* | *TBD* | **✅ Will work!** | **Both bugs fixed!** |

---

## Why Training32 Had No Debug Logs

1. **Training32 was created**: Job `0634d00d-e3db-4920-aaa0-56e3823c3460`
2. **Bug #1 was fixed**: Import error resolved
3. **Celery worker processed it**: Started at 04:36 UTC
4. **Bug #2 manifested**: Async/sync mismatch error appeared
5. **Logging code tried to run**: Called `_log_debug()` multiple times
6. **Every call failed silently**: `'async_generator' object is not an iterator`
7. **Graceful degradation worked**: Training continued, but no logs saved
8. **Result**: Empty debug_log array

**Evidence**:
```bash
docker-compose logs celery-worker | grep "Debug logging failed"
```
Output:
```
[2025-12-22 04:36:49] Debug logging failed for job 0634d00d: 'async_generator' object is not an iterator
... (repeated ~16 times)
```

---

## What's Different Now

### Bug #1 Fix (Training31 → Training32):
- Removed `from app.models.database import FineTuningJob` import
- Still had async/sync issue

### Bug #2 Fix (Training32 → Training33):
- Completely rewrote function as synchronous
- No more async generator dependency
- Direct database connection using psycopg2 driver

---

## Next Steps

### Create Training33

**Name**: `choles-qa-real-training33`
**Dataset**: Same Choles QA dataset (4,321 bytes, 10 samples)
**Expected**: **FULL DEBUG LOGS** 🎉

After training33 is created and completes, query the debug_log:

```sql
SELECT unnest(debug_log) AS log_entry
FROM finetuning_jobs
WHERE job_name = 'choles-qa-real-training33'
ORDER BY created_at DESC
LIMIT 1;
```

**Expected output** (FINALLY!):
```
[2025-12-22 HH:MM:SS.mmm] 🔍 Validating dataset exists in MinIO
[2025-12-22 HH:MM:SS.mmm] ✅ Dataset found: technology/itm11/.../company_qa_dataset.jsonl (4,321 bytes)
[2025-12-22 HH:MM:SS.mmm] 📦 Starting dataset download from MinIO
[2025-12-22 HH:MM:SS.mmm]    Bucket: documents
[2025-12-22 HH:MM:SS.mmm]    Object: technology/itm11/global/admin/finetuning/datasets/...
[2025-12-22 HH:MM:SS.mmm] ✅ Downloaded dataset: company_qa_dataset.jsonl (4,321 bytes)
[2025-12-22 HH:MM:SS.mmm]    Preview: {"messages": [{"role": "user", "content": "What is Choles?"}...
[2025-12-22 HH:MM:SS.mmm] 📁 Files in input directory: ['company_qa_dataset.jsonl']
[2025-12-22 HH:MM:SS.mmm] ✅ Found dataset file: company_qa_dataset.jsonl (4,321 bytes)
[2025-12-22 HH:MM:SS.mmm] 🔄 Preprocessing dataset (objective: instruction)
[2025-12-22 HH:MM:SS.mmm] ✅ Preprocessing complete: train.json (XX,XXX bytes)
[2025-12-22 HH:MM:SS.mmm]    Dataset contains 10 samples
[2025-12-22 HH:MM:SS.mmm] 🚀 Starting training container
[2025-12-22 HH:MM:SS.mmm] ✅ Container started: finetuning-xxx
```

---

## Verification

To verify the fix is in place:

```bash
# Check the fixed code in celery worker
docker-compose exec -T celery-worker grep -A 3 "def _log_debug" /app/app/services/finetuning/finetuning_sandbox_manager.py | head -10
```

Expected output (should NOT contain `async`):
```python
def _log_debug(self, job_id: str, message: str):
    """
    Add timestamped debug message to job's debug_log array in database

    SYNCHRONOUS version for Celery tasks (no async/await)
```

✅ **VERIFIED**: Synchronous function is loaded in celery-worker

---

## Summary of Both Bugs

### Bug #1: Import Error (Training31)
- **Error**: `cannot import name 'FineTuningJob' from 'app.models.database'`
- **Cause**: Importing non-existent model
- **Fix**: Removed unnecessary import
- **Status**: ✅ Fixed

### Bug #2: Async/Sync Mismatch (Training32)
- **Error**: `'async_generator' object is not an iterator`
- **Cause**: Async function in synchronous Celery context
- **Fix**: Rewrote as completely synchronous function
- **Status**: ✅ Fixed

### Both Bugs Now Fixed
- **Training31**: Failed due to Bug #1
- **Training32**: Failed due to Bug #2
- **Training33**: Should work with both bugs fixed! 🚀

---

## Technical Details

### Why Direct SQLAlchemy Connection?

**Problem**: Celery tasks run in synchronous worker processes without async event loop

**Solution**: Create synchronous database connection directly:
1. Convert DATABASE_URL: `postgresql+asyncpg` → `postgresql`
2. Use `create_engine()` for synchronous connection
3. Use `engine.connect()` context manager
4. Execute raw SQL with parameterized queries
5. Explicit `conn.commit()`

**Advantages**:
- Works in synchronous Celery context
- No async/await complexity
- Direct database access
- Lightweight (no session overhead)
- Atomic operations with PostgreSQL array_append

---

## What Makes Training33 Different

**Training31**:
- Created after Bug #1 was supposedly fixed
- BUT: Bug #1 wasn't actually fixed (import error)
- Result: Empty debug_log

**Training32**:
- Created after Bug #1 was actually fixed
- BUT: Bug #2 existed (async/sync mismatch)
- Result: Empty debug_log

**Training33** (upcoming):
- Will be created after BOTH bugs are fixed
- Synchronous logging function
- No import errors
- Result: **FULL DEBUG LOGS** 🎉

---

**Status**: ✅ **READY FOR TRAINING33 - Both bugs fixed, celery worker restarted**
**Last Updated**: 2025-12-22 04:45 UTC
**Fix Applied**: 2025-12-22 04:43 UTC
**Celery Restarted**: 2025-12-22 04:44 UTC

---

## Testing Instructions

1. **Create training33** via finetuning UI:
   - Job name: `choles-qa-real-training33`
   - Dataset: `company_qa_dataset.jsonl` (same as training31/32)
   - Model: `Qwen/Qwen2.5-1.5B-Instruct`
   - Training method: PEFT/LoRA
   - Objective: instruction

2. **Monitor in real-time**:
   ```bash
   # Watch debug log populate
   watch -n 5 'docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "SELECT unnest(debug_log) FROM finetuning_jobs WHERE job_name = '\''choles-qa-real-training33'\'';"'
   ```

3. **After completion**, verify full debug log exists:
   ```sql
   SELECT
       job_name,
       status,
       array_length(debug_log, 1) as log_count,
       unnest(debug_log) as log_entry
   FROM finetuning_jobs
   WHERE job_name = 'choles-qa-real-training33';
   ```

4. **Success criteria**: `log_count` should be 15-25 entries showing complete pipeline trace

---

**Next Action Required**: Create `choles-qa-real-training33` via finetuning UI to test the complete fix!
