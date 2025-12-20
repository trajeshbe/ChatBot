# Training Diagnosis Report

**Job ID**: 6d89d7ad-971b-403c-b24b-79f067b3af82
**Job Name**: short_story_7
**Model**: Qwen/Qwen2.5-1.5B-Instruct

---

## Status Summary

| Aspect | Status | Details |
|--------|--------|---------|
| **Training Completion** | ✅ Success | Completed in 358 seconds (~6 min) |
| **Model Registration** | ✅ Success | Model ID: 955c8380-8980-4586-b04c-463f5eca4fb8 |
| **Checkpoint Saved** | ✅ Success | Path: /workspace/finetuning/.../output |
| **Metrics Capture** | ❌ **FAILED** | All metrics are NULL |
| **Grafana Monitoring** | ❌ **NO DATA** | No metrics pushed to Prometheus |

---

## What's Missing

```sql
SELECT train_loss, eval_loss, current_epoch, total_steps
FROM finetuning_jobs WHERE id = '6d89d7ad...';

 train_loss | eval_loss | current_epoch | total_steps
------------+-----------+---------------+-------------
            |           |               |
(ALL NULL)
```

---

## Root Cause

**Issue**: Training container doesn't send metrics back to parent process

**Expected Flow**:
```
Training Container
  → Writes metrics to shared volume/database
  → Parent celery task reads metrics
  → Updates database (train_loss, eval_loss, etc.)
  → Pushes to Prometheus
  → Grafana displays charts
```

**Actual Flow**:
```
Training Container
  → Trains model ✅
  → Saves checkpoint ✅
  → ❌ Doesn't write metrics
  → Parent celery task receives nothing
  → Database metrics stay NULL
  → Grafana has no data to display
```

---

## Impact

### Can Still Use Model ✅
- Model trained successfully
- Weights are saved
- Can deploy to Ollama
- Can use for inference

### Cannot Monitor Training ❌
- No loss curves in Grafana
- No progress tracking
- No comparison with other models
- Cannot tell if overfitting occurred

---

## Next Steps to Fix

### Option 1: Add Metrics Reporting to Training Container
**File**: Training script inside finetuning-runtime container

**Add**:
```python
# After each training step
import requests

def report_metrics(job_id, metrics):
    """Send metrics back to parent process"""
    requests.post(
        f"http://backend:8000/internal/finetuning/jobs/{job_id}/metrics",
        json={
            "current_step": step,
            "train_loss": loss.item(),
            "current_epoch": epoch,
            "progress": (step / total_steps) * 100
        }
    )

# In training loop
for epoch in range(num_epochs):
    for step, batch in enumerate(train_dataloader):
        # ... training code ...

        if step % 10 == 0:  # Every 10 steps
            report_metrics(job_id, {
                "train_loss": loss.item(),
                "current_step": step,
                "current_epoch": epoch
            })
```

### Option 2: Write Metrics to Shared Volume
**File**: Training container writes to `/workspace/logs/metrics.json`

**Parent reads**:
```python
# In celery task
while training_running:
    metrics_file = f"/workspace/finetuning/{job_id}/logs/metrics.json"
    if os.path.exists(metrics_file):
        with open(metrics_file) as f:
            metrics = json.load(f)
            update_job_metrics(job, metrics)
    await asyncio.sleep(5)  # Check every 5 seconds
```

### Option 3: Use Streaming Logs
**Parse container logs** for metrics:
```python
# In celery task
for line in container.logs(stream=True):
    if "Step" in line and "Loss" in line:
        # Parse: "Step 100 | Loss: 2.1543"
        match = re.match(r"Step (\d+) \| Loss: ([\d.]+)", line)
        if match:
            step, loss = match.groups()
            update_metrics(job, step=step, loss=float(loss))
```

---

## Workaround for Current Model

Your model **IS usable** despite missing metrics:

1. **Deploy to Ollama**:
   ```bash
   # Via UI: Fine-Tuning Hub → Evaluations → Deploy to Ollama
   ```

2. **Test manually**:
   ```bash
   curl http://localhost:11434/api/generate -d '{
     "model": "short_story_7_model",
     "prompt": "Write a short story about...",
     "stream": false
   }'
   ```

3. **Evaluate post-deployment**:
   - Automatic evaluation will run after deployment
   - This will give you BLEU/ROUGE scores
   - Sample-by-sample results in UI

---

## Recommended Action

**For your current model**: Deploy and evaluate (works fine!)

**For future training**: Implement metrics reporting so you can monitor live

---

**Created**: 2025-12-19
**Issue**: Metrics not captured during training
**Status**: Model usable, monitoring needs fix
