# Training Container Logging - Real-Time Solution

**Date**: 2025-12-21
**Problem**: Unable to trace training container logs while execution is in progress
**Status**: Solution Designed

---

## Problem Analysis

### Current Implementation Issues

**File**: `/backend/app/services/finetuning/finetuning_sandbox_manager.py`

```python
# Line 591-635: Container launches
container = self.docker_client.containers.run(
    image=self.finetuning_image,
    name=f"finetuning-{job_id}",
    detach=True,
    remove=False,  # Keep for inspection
    ...
)

# Lines 639-647: ❌ BLOCKING WAIT - Cannot access logs until done
exit_status = await asyncio.to_thread(
    container.wait,
    timeout=timeout_seconds
)

# Lines 649-656: ❌ Logs retrieved ONLY AFTER completion
logs = await asyncio.to_thread(container.logs, stdout=True, stderr=True)
logs_text = logs.decode('utf-8')

# Line 654: ❌ Logs saved ONLY at the end
log_file = workspace["logs"] / "training.log"
with open(log_file, 'w') as f:
    f.write(logs_text)
```

**Problems**:
1. **Blocking wait**: `container.wait()` blocks until container finishes
2. **No streaming**: Logs are fetched as a single blob after completion
3. **No real-time access**: Cannot check logs while training is running
4. **Single file**: All logs dumped to one file at the end
5. **No error detection**: Errors only visible after job completes

---

## Solution: Real-Time Log Streaming

### Architecture

```
┌─────────────────┐
│ Training        │
│ Container       │ ──── stdout/stderr ────┐
│ (finetuning-X)  │                        │
└─────────────────┘                        │
                                           ▼
                                    ┌──────────────┐
                                    │ Log Streamer │
                                    │  (async bg)  │
                                    └──────────────┘
                                           │
                         ┌─────────────────┼─────────────────┐
                         │                 │                 │
                         ▼                 ▼                 ▼
                  ┌──────────┐      ┌──────────┐     ┌───────────┐
                  │  File    │      │ Database │     │  Backend  │
                  │  Logs    │      │  Updates │     │  Logger   │
                  └──────────┘      └──────────┘     └───────────┘
                  /workspace/       finetuning_jobs   Python logging
                  logs/training     .error_message
                  .log              .training_stage
```

### Implementation Strategy

#### 1. Background Log Streamer Task

Create an async background task that streams logs in real-time and:
- Writes to log file incrementally
- Detects errors immediately
- Updates database with progress
- Allows API to fetch live logs

#### 2. Enhanced Container Launch

Replace blocking `container.wait()` with:
- Launch container
- Start background log streamer
- Poll container status periodically
- Allow early error detection

#### 3. Real-Time Log API

Already implemented at `/api/v1/finetuning/jobs/{job_id}/logs` - just needs to read the streaming log file

---

## Implementation Plan

### Step 1: Create Log Streamer Service

**File**: `/backend/app/services/finetuning/training_log_streamer.py` (NEW)

```python
"""
Training Log Streamer

Streams container logs in real-time to:
- Log file (incremental writes)
- Database (error detection + progress updates)
- Python logger (debugging)
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime
import docker
import re

logger = logging.getLogger(__name__)


class TrainingLogStreamer:
    """
    Real-time log streamer for training containers

    Features:
    - Async log streaming (non-blocking)
    - Incremental file writes
    - Error detection with regex patterns
    - Progress extraction (Epoch X/Y, Step X/Y, Loss)
    - Database updates
    """

    def __init__(
        self,
        container: docker.models.containers.Container,
        log_file: Path,
        job_id: str,
        db_callback: Optional[Callable] = None
    ):
        """
        Initialize log streamer

        Args:
            container: Docker container to stream from
            log_file: Path to write logs
            job_id: Fine-tuning job ID
            db_callback: Optional callback to update database
        """
        self.container = container
        self.log_file = log_file
        self.job_id = job_id
        self.db_callback = db_callback
        self.is_streaming = False

        # Error detection patterns
        self.error_patterns = [
            r"(?i)error:",
            r"(?i)exception:",
            r"(?i)traceback",
            r"(?i)cuda out of memory",
            r"(?i)killed",
            r"(?i)segmentation fault",
            r"(?i)assertion.*failed",
            r"RuntimeError",
            r"ValueError",
            r"KeyError"
        ]

        # Progress extraction patterns
        self.progress_patterns = {
            'epoch': r'Epoch (\d+)/(\d+)',
            'step': r'Step (\d+)/(\d+)',
            'loss': r'Loss[:\s]+([0-9.]+)',
            'samples': r'Loaded (\d+).*samples',
            'stage': r'(Preprocessing|Training|Evaluation|Merging)'
        }

    async def stream_logs(self) -> None:
        """
        Stream logs from container to file and database

        Runs until container stops
        """
        self.is_streaming = True
        logger.info(f"📡 Starting log stream for job {self.job_id}")

        try:
            # Create log file
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

            # Stream logs with follow=True (like tail -f)
            log_generator = await asyncio.to_thread(
                self.container.logs,
                stream=True,
                follow=True,
                stdout=True,
                stderr=True
            )

            # Process log lines
            with open(self.log_file, 'w') as f:
                for log_chunk in log_generator:
                    if not self.is_streaming:
                        break

                    # Decode log line
                    log_line = log_chunk.decode('utf-8', errors='replace').strip()

                    if not log_line:
                        continue

                    # Write to file immediately
                    timestamp = datetime.utcnow().isoformat()
                    f.write(f"[{timestamp}] {log_line}\n")
                    f.flush()  # Force write to disk

                    # Log to Python logger
                    logger.info(f"[{self.job_id}] {log_line}")

                    # Detect errors
                    if self._is_error(log_line):
                        logger.error(f"❌ Error detected in job {self.job_id}: {log_line}")
                        if self.db_callback:
                            await self.db_callback(
                                job_id=self.job_id,
                                status="failed",
                                error_message=log_line[:500]  # Truncate to 500 chars
                            )

                    # Extract progress
                    progress = self._extract_progress(log_line)
                    if progress and self.db_callback:
                        await self.db_callback(
                            job_id=self.job_id,
                            **progress
                        )

            logger.info(f"✅ Log streaming completed for job {self.job_id}")

        except Exception as e:
            logger.error(f"❌ Log streaming error for job {self.job_id}: {e}")
            if self.db_callback:
                await self.db_callback(
                    job_id=self.job_id,
                    status="failed",
                    error_message=f"Log streaming failed: {str(e)}"
                )
        finally:
            self.is_streaming = False

    def _is_error(self, log_line: str) -> bool:
        """Check if log line contains an error"""
        for pattern in self.error_patterns:
            if re.search(pattern, log_line):
                return True
        return False

    def _extract_progress(self, log_line: str) -> Optional[dict]:
        """
        Extract training progress from log line

        Returns:
            Dict with progress metrics or None
        """
        progress = {}

        # Extract epoch
        if match := re.search(self.progress_patterns['epoch'], log_line):
            progress['current_epoch'] = int(match.group(1))
            progress['total_epochs'] = int(match.group(2))

        # Extract step
        if match := re.search(self.progress_patterns['step'], log_line):
            progress['current_step'] = int(match.group(1))
            progress['total_steps'] = int(match.group(2))

        # Extract loss
        if match := re.search(self.progress_patterns['loss'], log_line):
            progress['train_loss'] = float(match.group(1))

        # Extract stage
        if match := re.search(self.progress_patterns['stage'], log_line):
            stage = match.group(1).lower()
            progress['training_stage'] = stage

        return progress if progress else None

    def stop(self):
        """Stop log streaming"""
        self.is_streaming = False
        logger.info(f"🛑 Stopping log stream for job {self.job_id}")
```

### Step 2: Update Sandbox Manager

**File**: `/backend/app/services/finetuning/finetuning_sandbox_manager.py`

**Changes Required**:

1. **Import the log streamer** (top of file):
   ```python
   from app.services.finetuning.training_log_streamer import TrainingLogStreamer
   ```

2. **Replace blocking wait with async log streaming** (lines 636-680):
   ```python
   # OLD CODE (lines 637-658):
   # logger.info(f"✅ Training container {container.short_id} started")
   # logger.info(f"⏳ Waiting for training to complete (timeout: {timeout_hours}h)...")
   # exit_status = await asyncio.to_thread(container.wait, timeout=timeout_seconds)
   # logs = await asyncio.to_thread(container.logs, stdout=True, stderr=True)
   # logs_text = logs.decode('utf-8')

   # NEW CODE:
   logger.info(f"✅ Training container {container.short_id} started")

   # Create log file path
   log_file = workspace["logs"] / "training.log"

   # Create database update callback
   async def update_job_progress(**kwargs):
       """Update job progress in database"""
       try:
           from app.models.finetuning_models import FineTuningJob
           from app.core.database import get_async_session
           from sqlalchemy import update

           async with get_async_session() as db:
               stmt = update(FineTuningJob).where(
                   FineTuningJob.id == job_id
               ).values(**kwargs)
               await db.execute(stmt)
               await db.commit()
       except Exception as e:
           logger.error(f"Failed to update job progress: {e}")

   # Start log streamer in background
   log_streamer = TrainingLogStreamer(
       container=container,
       log_file=log_file,
       job_id=job_id,
       db_callback=update_job_progress
   )

   # Launch log streaming as background task
   log_task = asyncio.create_task(log_streamer.stream_logs())

   logger.info(f"📡 Log streaming started for job {job_id}")
   logger.info(f"⏳ Waiting for training to complete (timeout: {timeout_hours}h)...")

   # Wait for container with timeout
   try:
       exit_status = await asyncio.to_thread(
           container.wait,
           timeout=timeout_seconds
       )

       # Stop log streaming
       log_streamer.stop()
       await log_task

       logger.info(f"📋 Training completed with exit code: {exit_status['StatusCode']}")

       # Read logs from file (now contains all logs)
       logs_text = log_file.read_text() if log_file.exists() else ""

   except asyncio.TimeoutError:
       logger.error(f"❌ Training timeout after {timeout_hours} hours")
       log_streamer.stop()
       await log_task
       raise
   ```

### Step 3: Verify Real-Time Log Access

The existing `/api/v1/finetuning/jobs/{job_id}/logs` endpoint already reads from:
- Docker container logs via `docker logs`
- Celery logs via `docker-compose logs celery`

With the new streamer, it will also be able to read from the incrementally written log file:
```python
# In finetuning_routes.py /jobs/{job_id}/logs endpoint, add:
log_file = Path(f"/tmp/finetuning_workspaces/{job_id}/logs/training.log")
if log_file.exists():
    with open(log_file, 'r') as f:
        file_logs = f.readlines()[-lines:]  # Get last N lines
```

---

## Benefits

### ✅ Real-Time Monitoring
- Logs written incrementally to `/workspace/logs/training.log`
- Can read logs **while training is running**
- UI pipeline visualizer shows live logs via API

### ✅ Early Error Detection
- Regex patterns detect errors immediately
- Database updated with error message
- Job status changes to "failed" instantly
- No need to wait for container exit

### ✅ Progress Tracking
- Epoch, step, loss extracted from logs
- Database updated in real-time
- UI shows live progress metrics

### ✅ Debugging Friendly
- All logs available via `docker logs finetuning-{job_id}`
- File logs at `/tmp/finetuning_workspaces/{job_id}/logs/training.log`
- Python logger shows all output
- Can inspect logs at any time

### ✅ No Breaking Changes
- Existing API endpoints still work
- Training flow unchanged
- Container lifecycle unchanged
- Only adds real-time streaming

---

## Testing Plan

### 1. Create Test Job
```bash
# Via UI or API, create a new training job
# Name: test-log-streaming
# Dataset: company_qa_dataset
# Method: PEFT
```

### 2. Monitor Logs While Running
```bash
# Terminal 1: Watch log file (should update in real-time)
watch -n 1 "tail -20 /tmp/finetuning_workspaces/<job_id>/logs/training.log"

# Terminal 2: Docker logs (should stream)
docker logs -f finetuning-<job_id>

# Terminal 3: API logs
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/finetuning/jobs/<job_id>/logs?lines=50"
```

### 3. Verify Error Detection
```bash
# Inject an error by using bad hyperparameters
# Should see error in database immediately, not after completion
```

### 4. Check Database Updates
```sql
-- Should see real-time updates to:
SELECT
  current_epoch,
  current_step,
  train_loss,
  training_stage,
  error_message,
  updated_at
FROM finetuning_jobs
WHERE id = '<job_id>';
```

---

## Files to Create/Modify

### New Files
1. `/backend/app/services/finetuning/training_log_streamer.py` - Log streaming service (NEW)

### Modified Files
2. `/backend/app/services/finetuning/finetuning_sandbox_manager.py` - Replace blocking wait with streaming
3. `/backend/app/api/routes/finetuning_routes.py` - Add file log reading to `/jobs/{job_id}/logs` endpoint

---

## Rollout Plan

### Phase 1: Create Log Streamer (15 min)
- Create `training_log_streamer.py`
- Test regex patterns with sample logs

### Phase 2: Update Sandbox Manager (20 min)
- Import log streamer
- Replace `container.wait()` with async streaming
- Add database callback

### Phase 3: Update API Endpoint (10 min)
- Add file log reading to `/logs` endpoint
- Test with existing UI pipeline visualizer

### Phase 4: Test End-to-End (15 min)
- Create test job
- Verify logs stream in real-time
- Check UI pipeline tooltips
- Verify error detection

**Total Estimated Time**: ~60 minutes

---

## Success Criteria

✅ **Real-Time Logs**: Log file updates while container is running
✅ **Error Detection**: Errors caught immediately and job marked as failed
✅ **Progress Updates**: Epoch/step/loss visible in database during training
✅ **UI Integration**: Pipeline visualizer shows live logs in hover tooltips
✅ **No Breaking Changes**: Existing jobs continue to work
✅ **Debugging**: Can access logs via file, docker, and API

---

**Next Step**: Implement Phase 1 - Create the TrainingLogStreamer class
