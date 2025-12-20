# Fine-Tuning Training Monitoring Guide

## 📊 Where to Find Training Details & Loss Metrics

Your training job: **6d89d7ad-971b-403c-b24b-79f067b3af82**

---

## Option 1: 🔴 Real-Time Docker Logs (RECOMMENDED)

**Best for**: Live training progress, loss values, step-by-step output

### Command:
```bash
docker logs --follow 890f17006a71
```

**What you'll see**:
- Training loss per step
- Evaluation loss per epoch
- Learning rate
- GPU memory usage
- Progress percentage
- ETA for completion

**Expected output**:
```
Epoch 1/3:  10%|█         | 50/500 [01:23<12:45, 1.70s/it]
Step 50 | Loss: 2.1543 | LR: 0.0002 | GPU: 4.2GB
```

---

## Option 2: 📊 Grafana Dashboard (VISUAL)

**Best for**: Real-time charts, historical trends, multiple metrics at once

### Access:
- URL: **http://localhost:3000**
- Login: `admin` / `admin`
- Navigate to: **Fine-Tuning Dashboard** (if exists) or **Explore → Prometheus**

### Available Metrics:
- `finetuning_train_loss{job_id="6d89d7ad..."}` - Training loss over time
- `finetuning_eval_loss{job_id="6d89d7ad..."}` - Evaluation loss
- `finetuning_current_epoch{job_id="6d89d7ad..."}` - Current epoch
- `finetuning_progress_percent{job_id="6d89d7ad..."}` - Progress %
- `finetuning_job_status{job_id="6d89d7ad..."}` - Job status

### How to Query:
1. Open Grafana: http://localhost:3000
2. Go to **Explore** (left sidebar)
3. Select **Prometheus** data source
4. Query: `finetuning_train_loss{job_name="short_story_7"}`
5. Click **Run Query**

---

## Option 3: 🔍 Prometheus Metrics (RAW DATA)

**Best for**: Direct metric queries, debugging

### Access:
- URL: **http://localhost:9090**
- Navigate to: **Graph**

### Query Examples:
```promql
# Training loss
finetuning_train_loss{job_id="6d89d7ad-971b-403c-b24b-79f067b3af82"}

# All metrics for your job
{job_name="short_story_7"}

# Progress percentage
finetuning_progress_percent{job_id="6d89d7ad-971b-403c-b24b-79f067b3af82"}
```

---

## Option 4: 📁 Training Log Files

**Best for**: Post-training analysis, debugging

### Location (inside container):
```bash
# View logs inside container
docker exec 890f17006a71 cat /workspace/logs/6d89d7ad-971b-403c-b24b-79f067b3af82/training.log
```

### Location (on host via volume):
```bash
# If volumes are mounted
cat /path/to/workspace/logs/6d89d7ad-971b-403c-b24b-79f067b3af82/*.log
```

---

## Option 5: 💾 Database (STORED METRICS)

**Best for**: Final results, comparison across jobs

### Query:
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT 
    name, 
    status, 
    train_loss, 
    eval_loss, 
    current_epoch, 
    progress 
FROM finetuning_jobs 
WHERE id = '6d89d7ad-971b-403c-b24b-79f067b3af82';
"
```

**What you'll get**:
- Final training loss
- Final eval loss
- Last completed epoch
- Overall progress percentage

---

## Option 6: 🖥️ Frontend UI (if implemented)

**Best for**: User-friendly interface

### Access:
- URL: **http://localhost:3001**
- Navigate to: **Fine-Tuning Hub → Jobs**
- Find: **short_story_7**
- View: Real-time progress bar and metrics

---

## 🚀 Quick Start Commands

### 1. Watch training logs LIVE:
```bash
docker logs --follow --tail=50 890f17006a71
```

### 2. Check current training status:
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT name, status, progress, current_epoch, train_loss 
FROM finetuning_jobs 
WHERE id = '6d89d7ad-971b-403c-b24b-79f067b3af82';
"
```

### 3. Monitor GPU usage:
```bash
watch -n 2 'docker-compose exec ollama nvidia-smi --query-gpu=index,memory.used,memory.total,utilization.gpu --format=csv,noheader'
```

### 4. Check if training completed:
```bash
docker inspect 890f17006a71 | jq '.[0].State.Status'
# "running" = still training
# "exited" with ExitCode 0 = completed successfully
```

---

## 📈 Expected Training Timeline

**Your job settings**:
- Epochs: 3
- Batch size: 4
- Gradient accumulation: 4
- Model: Qwen2.5-1.5B (small)

**Estimated duration**: 30-60 minutes (depends on dataset size)

**Progress checkpoints**:
- Epoch 1/3: ~33% progress
- Epoch 2/3: ~66% progress
- Epoch 3/3: ~100% progress

---

## 🔔 Monitoring Tips

1. **Start with Docker logs** - Most detailed, real-time
2. **Use Grafana for visualization** - Best for charts
3. **Check Prometheus for raw metrics** - Good for debugging
4. **Query database for final results** - After training completes

---

## 🎯 What to Look For

### Good Signs ✅:
- Training loss decreasing over time
- Eval loss decreasing (but may fluctuate)
- Progress incrementing steadily
- No OOM (Out of Memory) errors

### Warning Signs ⚠️:
- Loss = NaN (learning rate too high)
- Loss not decreasing after 1 epoch
- GPU memory errors
- Container restarting

---

**Current Container ID**: `890f17006a71`
**Job ID**: `6d89d7ad-971b-403c-b24b-79f067b3af82`
**Job Name**: `short_story_7`
