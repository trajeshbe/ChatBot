# Training Metrics Capture Issue

**Date**: 2025-12-19
**Status**: ⚠️ IDENTIFIED - Needs Fix
**Severity**: Medium (Model usable, but no monitoring)

---

## 🔍 Issue Summary

Training jobs complete successfully but **metrics (loss, epochs, steps) are NOT captured** for monitoring.

### What Works ✅
- Training completes
- Model weights updated
- Checkpoint saved
- Model registered
- Can deploy and use

### What Doesn't Work ❌
- No live training metrics
- No loss values in database
- No Grafana charts
- No progress tracking
- Cannot monitor convergence

---

## 📊 Example

**Job**: `short_story_7` (ID: `6d89d7ad-971b-403c-b24b-79f067b3af82`)

### Database State:
```sql
SELECT train_loss, eval_loss, current_epoch, total_steps, progress
FROM finetuning_jobs WHERE name = 'short_story_7';

 train_loss | eval_loss | current_epoch | total_steps | progress
------------+-----------+---------------+-------------+----------
            |           |               |             |      100
```

**Result**: All metrics NULL, only progress shows 100%

---

## 🔍 Root Cause Analysis

### Architecture Gap

**Current Implementation**:
```
Training Container (Docker)
  ├─ Loads model
  ├─ Runs training loop
  ├─ Saves checkpoint
  └─ Exits with success ✅

Parent Celery Task
  ├─ Launches container
  ├─ Waits for completion
  ├─ ❌ NO metrics received
  └─ Marks job as "completed"
```

**Expected Implementation**:
```
Training Container (Docker)
  ├─ Loads model
  ├─ Runs training loop
  │   ├─ After each step → Report metrics
  │   ├─ After each epoch → Report eval metrics
  │   └─ Write to shared volume/DB
  ├─ Saves checkpoint
  └─ Exits with success ✅

Parent Celery Task
  ├─ Launches container
  ├─ Monitors metrics (polling)
  │   ├─ Reads from shared volume/DB
  │   ├─ Updates job.train_loss, job.current_epoch
  │   └─ Pushes to Prometheus
  ├─ Waits for completion
  └─ Marks job as "completed"
```

### Missing Communication Channel

Training container is **isolated** - no way to send metrics to parent process.

---

## 🛠️ Solution Options

### Option 1: HTTP Callback (RECOMMENDED)

**Pros**: Real-time, reliable, industry standard
**Cons**: Requires backend endpoint

**Implementation**:

**Step 1: Add endpoint to backend**
```python
# backend/app/api/routes/finetuning_routes.py

@router.post("/internal/finetuning/jobs/{job_id}/metrics")
async def update_job_metrics(
    job_id: str,
    metrics: dict,
    db: Session = Depends(get_db)
):
    """Receive metrics from training container"""
    job = db.query(FineTuningJob).filter(
        FineTuningJob.id == UUID(job_id)
    ).first()

    if not job:
        raise HTTPException(404, "Job not found")

    # Update metrics
    job.current_step = metrics.get("current_step")
    job.train_loss = metrics.get("train_loss")
    job.eval_loss = metrics.get("eval_loss")
    job.current_epoch = metrics.get("current_epoch")
    job.progress = metrics.get("progress")

    db.commit()

    # Update Prometheus
    update_prometheus_metrics(job)

    return {"status": "updated"}
```

**Step 2: Modify training script**
```python
# In training container script
import requests
import os

JOB_ID = os.environ["JOB_ID"]
BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:8000")

def report_metrics(step, loss, epoch, progress):
    """Send metrics to backend"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/internal/finetuning/jobs/{JOB_ID}/metrics",
            json={
                "current_step": step,
                "train_loss": float(loss),
                "current_epoch": epoch,
                "progress": progress
            },
            timeout=2
        )
        response.raise_for_status()
    except Exception as e:
        # Don't fail training if reporting fails
        print(f"Warning: Failed to report metrics: {e}")

# In training loop
for epoch in range(num_epochs):
    for step, batch in enumerate(train_dataloader):
        # ... training code ...

        if step % 10 == 0:  # Every 10 steps
            progress = ((epoch * len(train_dataloader) + step) /
                       (num_epochs * len(train_dataloader))) * 100

            report_metrics(
                step=step,
                loss=loss.item(),
                epoch=epoch + 1,
                progress=progress
            )
```

---

### Option 2: Shared Volume with Polling

**Pros**: No network dependency
**Cons**: Latency (5-10s delay), disk I/O

**Implementation**:

**Training container writes**:
```python
# In training container
import json

METRICS_FILE = f"/workspace/logs/{JOB_ID}/metrics.json"

def save_metrics(step, loss, epoch):
    os.makedirs(os.path.dirname(METRICS_FILE), exist_ok=True)
    with open(METRICS_FILE, "w") as f:
        json.dump({
            "current_step": step,
            "train_loss": float(loss),
            "current_epoch": epoch,
            "timestamp": datetime.now().isoformat()
        }, f)

# In training loop
if step % 10 == 0:
    save_metrics(step, loss.item(), epoch)
```

**Parent task polls**:
```python
# In celery task
async def monitor_training_metrics(job_id: str, container):
    """Poll metrics file while training runs"""
    metrics_file = f"/workspace/finetuning/{job_id}/logs/metrics.json"

    while container.status == "running":
        try:
            if os.path.exists(metrics_file):
                with open(metrics_file) as f:
                    metrics = json.load(f)

                # Update database
                with SessionLocal() as db:
                    job = db.query(FineTuningJob).get(UUID(job_id))
                    job.current_step = metrics["current_step"]
                    job.train_loss = metrics["train_loss"]
                    job.current_epoch = metrics["current_epoch"]
                    db.commit()

                    update_prometheus_metrics(job)

        except Exception as e:
            logger.warning(f"Failed to read metrics: {e}")

        await asyncio.sleep(5)  # Check every 5 seconds
```

---

### Option 3: Parse Container Logs

**Pros**: No code changes needed in container
**Cons**: Fragile (depends on log format), regex complexity

**Implementation**:
```python
# In celery task
import re

async def monitor_training_logs(job_id: str, container):
    """Parse training logs for metrics"""
    for line in container.logs(stream=True, follow=True):
        line = line.decode('utf-8')

        # Parse: "Epoch 2/3 | Step 150/500 | Loss: 2.1543"
        match = re.search(
            r"Epoch (\d+)/(\d+).*Step (\d+)/(\d+).*Loss: ([\d.]+)",
            line
        )

        if match:
            epoch, total_epochs, step, total_steps, loss = match.groups()

            with SessionLocal() as db:
                job = db.query(FineTuningJob).get(UUID(job_id))
                job.current_epoch = int(epoch)
                job.current_step = int(step)
                job.total_steps = int(total_steps)
                job.train_loss = float(loss)
                job.progress = (int(step) / int(total_steps)) * 100
                db.commit()

                update_prometheus_metrics(job)
```

---

## 📝 Implementation Priority

| Option | Priority | Effort | Reliability |
|--------|----------|--------|-------------|
| **Option 1: HTTP Callback** | ⭐⭐⭐ HIGH | Medium | Excellent |
| **Option 2: Shared Volume** | ⭐⭐ MEDIUM | Medium | Good |
| **Option 3: Parse Logs** | ⭐ LOW | Low | Poor |

**Recommendation**: Implement **Option 1** (HTTP Callback) for production quality

---

## 🧪 Testing Plan

### After Implementation

**Test 1: Start new training job**
```bash
# Submit job via UI
# Watch Grafana: http://localhost:3000/d/finetuning-metrics
# Expected: Loss chart updates every 10 steps
```

**Test 2: Check database**
```sql
-- While training is running
SELECT
    name,
    current_step,
    train_loss,
    current_epoch,
    progress
FROM finetuning_jobs
WHERE status = 'running'
ORDER BY updated_at DESC
LIMIT 1;

-- Expected: Non-NULL values updating every 5-10 seconds
```

**Test 3: Prometheus metrics**
```bash
curl http://localhost:9090/api/v1/query?query=finetuning_train_loss
# Expected: Recent datapoints
```

---

## 📋 Files to Modify

### Backend

1. **`backend/app/api/routes/finetuning_routes.py`**
   - Add `/internal/finetuning/jobs/{job_id}/metrics` endpoint
   - Accept metrics from training container

2. **`backend/app/tasks/finetuning_tasks.py`**
   - Add metrics monitoring loop
   - Call `update_prometheus_metrics()` when metrics received

### Training Container

3. **`backend/Dockerfile.finetuning-runtime`** (training image)
   - Add `requests` library to requirements

4. **Training script** (wherever PEFT training runs)
   - Add `report_metrics()` function
   - Call after each training step
   - Include error handling (don't fail training if reporting fails)

---

## 🚨 Current Workaround

For **existing models** (like `short_story_7_model`):

### You Can:
✅ Deploy to Ollama
✅ Use for inference
✅ Evaluate post-deployment (gets BLEU/ROUGE scores)
✅ Test manually

### You Cannot:
❌ See training loss curves
❌ Compare convergence with other models
❌ Know if it overfitted

**Action**: Deploy and evaluate (see `AUTOMATIC_EVALUATION_COMPLETE.md`)

---

## 📚 Related Documentation

- **Evaluation**: `docs/features/finetuning/AUTOMATIC_EVALUATION_COMPLETE.md`
- **Grafana Setup**: `docs/features/finetuning/GRAFANA_MONITORING.md` (to be created)
- **Training Guide**: `docs/features/finetuning/FINETUNING_COMPLETE_IMPLEMENTATION_GUIDE.md`

---

**Status**: ⚠️ Issue identified, solution designed, awaiting implementation
**Impact**: Medium (models work, but no monitoring)
**ETA to fix**: 2-4 hours development + testing

---

**Date**: 2025-12-19
**Reporter**: User (training run 6d89d7ad-971b-403c-b24b-79f067b3af82)
**Root Cause**: Missing metrics communication between training container and parent process
