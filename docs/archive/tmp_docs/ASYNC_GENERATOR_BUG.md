# Database Debug Logging - Async Generator Bug

**Date**: 2025-12-22 04:40 UTC
**Status**: ❌ **NEW BUG FOUND IN TRAINING32**

---

## The Problem

Training32 also failed with a different error:

```
Debug logging failed for job 0634d00d: 'async_generator' object is not an iterator
```

## Root Cause

The `_log_debug()` method is defined as `async`, but:
1. It's being called from **Celery tasks** which are SYNCHRONOUS
2. `get_db()` returns an **async generator**
3. Using `next()` on an async generator doesn't work
4. The entire function is async but being called without `await` in a sync context

### The Problematic Code

```python
async def _log_debug(self, job_id: str, message: str):  # ❌ async but called from sync context
    try:
        from app.core.database import get_db  # Returns async generator
        from sqlalchemy.orm import Session

        db_gen = get_db()          # Async generator
        db: Session = next(db_gen)  # ❌ Can't use next() on async generator!
```

## Why This Happened

1. **Celery tasks are synchronous** - They run in a worker process without an async event loop
2. **get_db() is async** - It's designed for FastAPI endpoints with async/await
3. **Mixed async/sync** - Can't use `async def` in Celery tasks

## Solution Required

We need to create a **synchronous** database session for logging, NOT use the async `get_db()` generator.

### Option 1: Direct SQLAlchemy Session (RECOMMENDED)

```python
def _log_debug_sync(self, job_id: str, message: str):  # Synchronous!
    """Synchronous logging for Celery tasks"""
    try:
        from sqlalchemy import create_engine, text
        from app.core.config import settings

        # Create synchronous engine (one-time)
        engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))

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

### Option 2: Use psycopg2 (PostgreSQL driver)

```python
def _log_debug_sync(self, job_id: str, message: str):
    try:
        import psycopg2
        from app.core.config import settings

        conn = psycopg2.connect(settings.DATABASE_URL.replace('postgresql+asyncpg', 'postgresql'))
        cursor = conn.cursor()

        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] {message}"

        cursor.execute("""
            UPDATE finetuning_jobs
            SET debug_log = array_append(debug_log, %s)
            WHERE id = %s
        """, (log_entry, job_id))

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"[{job_id[:8]}] {message}")
    except Exception as e:
        logger.warning(f"Debug logging failed: {e}")
```

## Training History

| Job | Name | Debug Log | Error |
|-----|------|-----------|-------|
| 1770a884 | - | ❌ Empty | Created before restart |
| 5576001e | training31 | ❌ Empty | Import error (FineTuningJob) |
| **0634d00d** | **training32** | **❌ Empty** | **Async generator error** |

---

## Next Steps

1. Rewrite `_log_debug()` as a **synchronous** function
2. Use direct SQLAlchemy connection (not async generator)
3. Restart celery worker
4. Create training33 to test

---

**Last Updated**: 2025-12-22 04:40 UTC
