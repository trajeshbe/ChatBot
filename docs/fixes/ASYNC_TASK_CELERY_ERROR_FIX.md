# Async Task Celery Error - Complete Solution

**Date**: 2025-12-18
**Status**: 🔧 Solution Identified

---

## Error Encountered

After making `run_finetuning_job` async, we got:
```
ERROR: Task raised unexpected: EncodeError(TypeError('Object of type coroutine is not JSON serializable'))
```

---

## Root Cause

**Problem**: Making a Celery task `async def` means it returns a coroutine, but standard Celery tasks expect regular functions that return serializable values.

**Solution Options**:

### Option 1: Use asyncio.run() in a Wrapper (RECOMMENDED)

Instead of making the entire task async, keep the task function synchronous and use `asyncio.run()` only for the async parts within a wrapper.

### Option 2: Use Celery's Native Async Support

Requires configuring Celery with `task_protocol=2` and using `gevent` or `eventlet`.

---

## The Right Fix: Use Helper Functions

The solution is to **keep the Celery task synchronous** but create async helper functions that we call with `asyncio.run()`.

This approach:
- ✅ Works with standard Celery configuration
- ✅ Properly handles async operations
- ✅ Avoids serialization errors
- ✅ No need to change Celery broker configuration

---

## Implementation

Create async helper functions and call them from the synchronous task:

```python
@celery.task(...)
def run_finetuning_job(self, job_id: str) -> Dict[str, Any]:
    """Celery task wrapper - MUST be synchronous"""
    # Run the actual async work
    return asyncio.run(_run_finetuning_job_async(job_id))


async def _run_finetuning_job_async(job_id: str) -> Dict[str, Any]:
    """Actual async implementation"""
    # All the GPU allocation, training, etc. code goes here
    # Use await for all async operations
    pass
```

---

## Alternative: Using asyncio.run() Correctly

The original approach was almost correct! The issue was calling `asyncio.run()` from within an already-running event loop. But in a Celery task, there ISN'T an event loop running. The real problem was making the task itself async.

**Correct Pattern**:
```python
@celery.task(...)  # Task decorator - synchronous
def run_finetuning_job(self, job_id: str):  # Regular function
    # Inside, use asyncio.run() to execute async code
    result = asyncio.run(some_async_function())
    return result  # Return regular dict, not coroutine
```

---

## Files to Fix

`backend/app/tasks/finetuning_tasks.py`

**Change from**:
```python
@celery.task(...)
async def run_finetuning_job(self, job_id: str) -> Dict[str, Any]:
    result = await sandbox_manager.execute_training(...)
```

**Change to** (keep original async.io.run() approach!):
```python
@celery.task(...)
def run_finetuning_job(self, job_id: str) -> Dict[str, Any]:  # Remove 'async'
    result = asyncio.run(sandbox_manager.execute_training(...))  # Use asyncio.run()
```

The original code was correct! The issue wasn't with `asyncio.run()` - it was that we made the task itself async, which breaks Celery's serialization.

---

## Conclusion

**The actual problem**: We incorrectly diagnosed the root cause. The issue wasn't `asyncio.run()` failing silently - it was that the result wasn't being checked properly. We need to add error handling and logging INSIDE the execute_training method to see what's actually happening.

**Next Step**: Revert the async changes and instead focus on adding better error handling and logging to see why `execute_training` returns immediately without creating the container.

---

**Session**: Async Task Celery Error Fix
**Date**: 2025-12-18
