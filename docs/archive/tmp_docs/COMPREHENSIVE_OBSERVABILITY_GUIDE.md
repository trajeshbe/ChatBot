# Comprehensive Observability Dashboard Guide for Fine-Tuning

**Date**: 2025-12-20
**Purpose**: Complete guide for monitoring fine-tuning jobs across all observability platforms
**Training System**: Enterprise RAG Chatbot - Fine-Tuning Module

---

## Table of Contents

1. [Overview](#overview)
2. [Dashboard Access URLs](#dashboard-access-urls)
3. [TensorBoard - Real-Time Training Metrics](#tensorboard)
4. [Grafana - Time-Series Visualization](#grafana)
5. [Prometheus - Raw Metrics Query](#prometheus)
6. [Frontend UI - Web Interface](#frontend-ui)
7. [Training Logs - Container Logs](#training-logs)
8. [Troubleshooting Guide](#troubleshooting)
9. [Complete Monitoring Workflow](#complete-workflow)
10. [Metric Reference](#metric-reference)

---

## Overview

### Four Observability Platforms

| Platform | Purpose | Best For | Update Frequency |
|----------|---------|----------|------------------|
| **TensorBoard** | Training metrics visualization | Loss graphs, learning rate, training progress | Real-time (5s refresh) |
| **Grafana** | Multi-reward metrics (GRPO only) | Reward breakdowns, reasoning quality | Real-time (via Prometheus) |
| **Prometheus** | Raw metric storage and querying | Custom PromQL queries, metric exploration | 15s scrape interval |
| **Frontend UI** | User-friendly web interface | Job management, status monitoring | WebSocket real-time |

### When to Use Each Platform

- **During Active Training**: TensorBoard (loss graphs) + Frontend UI (job status)
- **GRPO Training**: Grafana (reward metrics) + TensorBoard (loss)
- **Debugging**: Training Logs (container logs) + Prometheus (raw metrics)
- **Production Monitoring**: Frontend UI (job management) + Grafana (dashboards)

---

## Dashboard Access URLs

### Quick Access Table

| Dashboard | URL | Credentials | Container |
|-----------|-----|-------------|-----------|
| Frontend UI | http://localhost:3001/finetuning | (user session) | rag-frontend |
| TensorBoard | http://localhost:6006 | None required | rag-tensorboard |
| Grafana | http://localhost:3000 | admin/admin | grafana |
| Prometheus | http://localhost:9090 | None required | prometheus |
| Backend API | http://localhost:8000/api/docs | (bearer token) | rag-backend |

### Verification Commands

```bash
# Check all services are running
docker-compose ps | grep -E "tensorboard|grafana|prometheus|frontend|backend"

# Test TensorBoard
curl -s http://localhost:6006 | grep "<title>TensorBoard</title>"

# Test Grafana
curl -s http://localhost:3000/api/health

# Test Prometheus
curl -s http://localhost:9090/-/healthy

# Test Frontend
curl -s http://localhost:3001 | grep "Next.js"
```

---

## TensorBoard - Real-Time Training Metrics

### Accessing TensorBoard

**URL**: http://localhost:6006

**No authentication required** - Open directly in browser

### What You'll See

#### 1. Scalars Tab (Main Training Metrics)

**Expected Metrics for SFT/PEFT Training**:

```
train/loss                    # Training loss (should decrease)
train/learning_rate          # Learning rate schedule
train/epoch                  # Current epoch (0.0 to num_epochs)
train/global_step            # Global training step
eval/loss                    # Validation loss (if eval enabled)
```

**Example Screenshot Description**:
- X-axis: Step number (0 to total_steps)
- Y-axis: Metric value
- Line graph showing progression over time
- Smoothing slider (default 0.6) to reduce noise

#### 2. Expected Values

| Metric | Initial Value | Expected Final | Interpretation |
|--------|---------------|----------------|----------------|
| train/loss | 0.5 - 2.0 | 0.1 - 0.5 | Lower = better learning |
| train/learning_rate | 2e-4 | ~0.0 | Decreases with warmup schedule |
| train/epoch | 0.0 | 3.0 | Linear progression |

### Log Directory Structure

TensorBoard reads from the **finetuning_workspaces Docker volume**:

```
/logs/finetuning/{job_id}/
├── events.out.tfevents.{timestamp}.{hostname}
└── (training event files)
```

**Mounted as**:
- TensorBoard container: `/logs`
- Backend container: `/workspace/finetuning/{job_id}/logs`

### How to Use TensorBoard

#### Step 1: Wait for Training to Start

```bash
# Monitor container logs until you see "Step 1" or "Epoch 1/3"
docker logs -f finetuning-{job_id} 2>&1 | grep -E "Step|Epoch"
```

**Typical timing**:
- Model loading: 30-60 seconds
- First step: 60-120 seconds after job submission

#### Step 2: Open TensorBoard

1. Navigate to http://localhost:6006
2. Wait 5-10 seconds for page to load
3. Click **"Scalars"** tab in top navigation
4. **Refresh** if no data appears (click refresh icon or F5)

#### Step 3: Navigate the Interface

**Left Sidebar**:
- Runs selector (if multiple jobs)
- Tag filter (train/loss, train/lr, etc.)

**Main Panel**:
- Scalar graphs with smoothing control
- Download data as CSV/JSON
- Toggle log scale

**Controls**:
- **Smoothing slider**: Adjust line smoothness (0.0 = raw, 0.9 = very smooth)
- **Horizontal axis**: Step, relative time, or wall time
- **Tooltip mode**: Hover to see exact values

### Example: Reading Loss Graph

```
Graph: train/loss
X-axis: Step 0 → 150 (for 3 epochs, 50 steps each)
Y-axis: Loss 1.5 → 0.3

Interpretation:
- Steep drop in first 10 steps: Model learning quickly
- Gradual decline 10-100: Continued optimization
- Plateau 100-150: Convergence (good!)
- Spikes: Possible batch with harder examples
```

### TensorBoard Commands

```bash
# Check if TensorBoard is running
docker ps | grep tensorboard

# Check TensorBoard logs
docker-compose logs tensorboard

# Restart TensorBoard (if needed)
docker-compose restart tensorboard

# Check mounted volume
docker-compose exec tensorboard ls -la /logs/finetuning/

# Manually start TensorBoard (alternative)
docker-compose exec backend tensorboard --logdir=/workspace/finetuning/{job_id}/logs --host=0.0.0.0 --port=6007
```

### TensorBoard Troubleshooting

| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| No data appears | Training hasn't started yet | Wait 60-120 seconds, check container logs |
| Empty Scalars tab | Logs not written to correct directory | Verify `/logs/finetuning/{job_id}` exists |
| "No dashboards are active" | No event files found | Check training is writing TensorBoard logs |
| Stale data | TensorBoard not auto-refreshing | Click refresh icon or restart container |

---

## Grafana - Time-Series Visualization

### Accessing Grafana

**URL**: http://localhost:3000
**Credentials**: admin/admin (change on first login)

### Dashboard Location

1. Log in to Grafana
2. Navigate to **"Dashboards"** (left sidebar, four squares icon)
3. Click **"Reasoning Model - Multi-Reward Training"**
4. Or use direct URL: http://localhost:3000/d/reasoning-model/reasoning-model-multi-reward-training

### What You'll See (GRPO Jobs Only)

⚠️ **Important**: Multi-reward metrics are only emitted for **GRPO training jobs**, not SFT/PEFT jobs.

#### Dashboard Panels

**Panel 1: Total Reward Trend**
- Time-series graph of total reward over training steps
- Aggregates all 6 reward components
- Expected: Upward trend indicating policy improvement

**Panel 2: Reward Breakdown**
- Stacked area chart showing individual reward contributions:
  - Correctness (40% weight)
  - Reasoning Clarity (20% weight)
  - Step-by-Step (15% weight)
  - Efficiency (10% weight)
  - Mathematical Notation (10% weight)
  - Coherence (5% weight)

**Panel 3: Reasoning Quality Metrics**
- Average reasoning steps count
- Reasoning depth over time
- Quality score distribution

**Panel 4: Reward Weights**
- Configurable weight display
- Shows current reward function coefficients

### Expected Metrics (GRPO)

```
# Prometheus metrics scraped from training container
reward_total_score{job_id="xxx"}                    # Combined reward score
reward_correctness_score{job_id="xxx"}              # Correctness component
reward_reasoning_clarity_score{job_id="xxx"}        # Clarity component
reward_step_by_step_score{job_id="xxx"}             # Step-by-step component
reward_efficiency_score{job_id="xxx"}               # Efficiency component
reward_mathematical_notation_score{job_id="xxx"}    # Math notation component
reward_coherence_score{job_id="xxx"}                # Coherence component
reward_batch_avg_total{job_id="xxx"}                # Batch average
reasoning_avg_steps_count{job_id="xxx"}             # Average steps in reasoning
```

### How to Use Grafana

#### Step 1: Create GRPO Job (Required for Dashboard)

```bash
# SFT jobs won't show data in this dashboard
# You need a GRPO training job for multi-reward metrics

# Upload GRPO dataset
curl -X POST "http://localhost:8000/api/v1/finetuning/datasets/upload?format_type=reasoning&training_objective=reasoning" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/tomato_grading_reasoning.jsonl" \
  -F "name=Tomato Grading - GRPO Demo"

# Create GRPO job
curl -X POST "http://localhost:8000/api/v1/finetuning/jobs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tomato GRPO - Reasoning",
    "base_model": "Qwen/Qwen2.5-1.5B-Instruct",
    "dataset_id": "{dataset_id}",
    "finetuning_method": "grpo",
    "training_objective": "reasoning",
    "hyperparameters": {
      "num_train_epochs": 3,
      "learning_rate": 1e-5,
      "per_device_train_batch_size": 2
    }
  }'
```

#### Step 2: Monitor GRPO Dashboard

1. Open http://localhost:3000
2. Navigate to "Reasoning Model - Multi-Reward Training" dashboard
3. Set time range: **"Last 30 minutes"** or **"Last 1 hour"**
4. Apply job filter: Select your job ID from dropdown
5. Enable auto-refresh: Click refresh icon → Set to "5s" or "10s"

#### Step 3: Interpret Reward Trends

**Healthy Training Signals**:
- Total reward increases over time
- Correctness score improves (most weighted)
- Reasoning steps count stabilizes (not too short, not too long)
- No sudden drops in coherence

**Warning Signals**:
- Total reward decreasing: Policy degradation
- Efficiency dropping: Model generating overly long reasoning
- Coherence score dropping: Output becoming incoherent

### Grafana Commands

```bash
# Check Grafana is running
docker-compose ps grafana

# Check Grafana logs
docker-compose logs grafana

# Restart Grafana
docker-compose restart grafana

# Access Grafana config
docker-compose exec grafana cat /etc/grafana/grafana.ini

# Check provisioned dashboards
docker-compose exec grafana ls /etc/grafana/provisioning/dashboards/
```

### Creating SFT Dashboard (Optional)

For SFT jobs, you can create a simpler dashboard:

1. Go to Grafana → Create → Dashboard
2. Add panel for training loss:
   ```promql
   train_loss{job_id="3f68e08f-1739-43e0-9d03-8685a77b74e7"}
   ```
3. Add panel for learning rate:
   ```promql
   learning_rate{job_id="3f68e08f-1739-43e0-9d03-8685a77b74e7"}
   ```
4. Add panel for epoch progress:
   ```promql
   epoch{job_id="3f68e08f-1739-43e0-9d03-8685a77b74e7"}
   ```

**Note**: These metrics require training code to export Prometheus metrics (not currently implemented for SFT).

---

## Prometheus - Raw Metrics Query

### Accessing Prometheus

**URL**: http://localhost:9090
**No authentication required**

### What You'll See

**Main Interface**:
- **Graph tab**: Execute PromQL queries and visualize results
- **Alerts tab**: View active alerts (if configured)
- **Status → Targets**: See scrape endpoints and health
- **Status → Configuration**: View Prometheus config

### How to Query Metrics

#### Step 1: Navigate to Graph Tab

1. Open http://localhost:9090
2. Click **"Graph"** in top navigation
3. Enter PromQL query in text box
4. Click **"Execute"** or press Enter

#### Step 2: Example Queries for GRPO

**Query 1: Total Reward Over Time**
```promql
reward_total_score{job_id="3f68e08f-1739-43e0-9d03-8685a77b74e7"}
```

**Query 2: Reward Rate of Change**
```promql
rate(reward_total_score{job_id="3f68e08f-1739-43e0-9d03-8685a77b74e7"}[5m])
```

**Query 3: Batch Average Reward**
```promql
reward_batch_avg_total{job_id="3f68e08f-1739-43e0-9d03-8685a77b74e7"}
```

**Query 4: Reasoning Steps Histogram**
```promql
histogram_quantile(0.95, reasoning_avg_steps_count{job_id="3f68e08f-1739-43e0-9d03-8685a77b74e7"})
```

#### Step 3: View Results

**Table View**:
- Raw metric values with timestamps
- Copy values for analysis

**Graph View**:
- Time-series visualization
- Zoom in/out on time range
- Stacked/line graphs

### Prometheus PromQL Examples

```promql
# Get latest value
reward_correctness_score{job_id="xxx"}

# Average over 5 minutes
avg_over_time(reward_correctness_score{job_id="xxx"}[5m])

# Compare correctness vs efficiency
reward_correctness_score{job_id="xxx"} / reward_efficiency_score{job_id="xxx"}

# Alert if reward drops
reward_total_score{job_id="xxx"} < 0.5

# Sum all reward components
sum(reward_correctness_score{job_id="xxx"} + reward_reasoning_clarity_score{job_id="xxx"} + ...)
```

### Checking Scrape Targets

1. Go to **Status → Targets**
2. Look for finetuning job endpoint:
   ```
   finetuning-{job_id}:9090/metrics
   ```
3. Status should be **"UP"** (green)
4. Last scrape shows recent timestamp

### Prometheus Commands

```bash
# Check Prometheus is running
docker-compose ps prometheus

# Check Prometheus logs
docker-compose logs prometheus

# Check Prometheus config
docker-compose exec prometheus cat /etc/prometheus/prometheus.yml

# Query Prometheus API directly
curl 'http://localhost:9090/api/v1/query?query=reward_total_score'

# Check scrape targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job | contains("finetuning"))'
```

---

## Frontend UI - Web Interface

### Accessing Frontend

**URL**: http://localhost:3001/finetuning
**Authentication**: Required (login with user session)

### What You'll See

#### Fine-Tuning Dashboard Page

**Top Section**: Job Controls
- "Create New Job" button
- Dataset upload link
- Filter/search bar

**Main Section**: Job List Table

| Column | Description | Example |
|--------|-------------|---------|
| Name | Job name | "Choles SFT - Company Knowledge" |
| Status | Current status | pending, running, completed, failed |
| Base Model | Model being finetuned | Qwen/Qwen2.5-1.5B-Instruct |
| Method | Training method | peft, grpo, sft |
| Progress | Training progress % | 0% → 100% |
| Started At | Job start timestamp | 2025-12-20 10:23:06 |
| Actions | View, Download, Delete | 👁️ 💾 🗑️ |

**Bottom Section**: Job Details Panel (when job selected)
- Real-time logs stream
- Hyperparameters display
- Checkpoint links
- Model registry entry

### How to Monitor Jobs

#### Step 1: Navigate to Fine-Tuning Page

1. Log in to http://localhost:3001
2. Click **"Fine-Tuning"** in left sidebar
3. Or directly: http://localhost:3001/finetuning

#### Step 2: Find Your Job

**Method 1: Scroll and click**
- Jobs sorted by creation date (newest first)
- Click on job row to expand details

**Method 2: Search**
- Use search bar at top
- Enter job name or ID
- Results filter in real-time

**Method 3: API**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/finetuning/jobs/3f68e08f-1739-43e0-9d03-8685a77b74e7"
```

#### Step 3: Watch Real-Time Updates

**WebSocket Connection**:
- Frontend establishes WebSocket at: `ws://localhost:8000/ws/finetuning/{job_id}`
- Updates received every 5 seconds
- Progress bar animates
- Status changes reflected immediately

**Manual Refresh**:
- Click refresh icon in top-right
- Page auto-refreshes every 30 seconds

### Job Status Indicators

| Status | Color | Icon | Meaning | Next Action |
|--------|-------|------|---------|-------------|
| pending | Gray | ⏳ | Waiting in queue | Wait or check Celery |
| running | Blue | ▶️ | Training in progress | Monitor dashboards |
| completed | Green | ✅ | Successfully finished | Test model |
| failed | Red | ❌ | Training error | Check logs |
| cancelled | Orange | 🛑 | User cancelled | Delete or retry |

### Viewing Job Details

**Click on job row** to expand:

**Hyperparameters Panel**:
```json
{
  "learning_rate": 0.0002,
  "num_train_epochs": 3,
  "per_device_train_batch_size": 2,
  "gradient_accumulation_steps": 4,
  "lora_r": 8,
  "lora_alpha": 16,
  "lora_dropout": 0.05
}
```

**Training Logs Panel**:
- Real-time log streaming (last 100 lines)
- Auto-scroll to bottom
- Search/filter logs

**Checkpoints Panel**:
- List of saved checkpoints
- Download links for each checkpoint
- MinIO path display

**Metrics Panel** (for GRPO jobs):
- RewardBreakdownChart component
- Real-time reward metrics
- Training loss graph

### Frontend Commands

```bash
# Check frontend is running
docker-compose ps frontend

# Check frontend logs
docker-compose logs frontend

# Restart frontend
docker-compose restart frontend

# Rebuild frontend
docker-compose build frontend --no-cache
docker-compose up -d frontend

# Check frontend container
docker-compose exec frontend ls /app/src/components/
```

### Frontend Troubleshooting

| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| Jobs not loading | API connection issue | Check backend is running, check browser console |
| No real-time updates | WebSocket disconnected | Refresh page, check WebSocket endpoint |
| Metrics not showing | GRPO job required | Create GRPO job or check metric export |
| Authentication error | Token expired | Log out and log back in |

---

## Training Logs - Container Logs

### Accessing Container Logs

**Most Direct Method**: Docker logs command

```bash
# Find finetuning container
docker ps -a | grep finetuning

# Follow logs in real-time
docker logs -f finetuning-{job_id}

# View last 100 lines
docker logs --tail=100 finetuning-{job_id}

# Search for errors
docker logs finetuning-{job_id} 2>&1 | grep -i error

# Search for training metrics
docker logs finetuning-{job_id} 2>&1 | grep -E "Epoch|Step|Loss"
```

### What You'll See in Logs

#### Training Start (Example)

```log
2025-12-20 10:23:06 - INFO - ================================================================================
2025-12-20 10:23:06 - INFO - 🔥 PEFT Fine-Tuning Trainer Started
2025-12-20 10:23:06 - INFO - ================================================================================
2025-12-20 10:23:06 - INFO - 📄 Config: {
  "job_id": "3f68e08f-1739-43e0-9d03-8685a77b74e7",
  "base_model": "Qwen/Qwen2.5-1.5B-Instruct",
  "finetuning_method": "peft",
  "training_objective": "qa"
}
2025-12-20 10:23:14 - INFO - 🎯 Base Model: Qwen/Qwen2.5-1.5B-Instruct
2025-12-20 10:23:14 - INFO - 🔢 Quantization: 4bit
2025-12-20 10:23:18 - INFO - Loading model Qwen/Qwen2.5-1.5B-Instruct...
```

#### Model Loading

```log
2025-12-20 10:28:29 - INFO - We will use 90% of the memory on device 0 for storing the model
2025-12-20 10:28:34 - INFO - Preparing model for k-bit training...
2025-12-20 10:28:34 - INFO - Configuring LoRA...
trainable params: 1,089,536 || all params: 1,544,803,840 || trainable%: 0.0705
```

#### Training Progress (Real Training)

```log
2025-12-20 10:30:00 - INFO - ***** Running training *****
2025-12-20 10:30:00 - INFO -   Num examples = 10
2025-12-20 10:30:00 - INFO -   Num Epochs = 3
2025-12-20 10:30:00 - INFO -   Total train batch size = 8
2025-12-20 10:30:00 - INFO -   Total optimization steps = 15

{'loss': 1.234, 'learning_rate': 0.0002, 'epoch': 0.33}
{'loss': 0.987, 'learning_rate': 0.00018, 'epoch': 0.67}
{'loss': 0.765, 'learning_rate': 0.00016, 'epoch': 1.0}
...
{'loss': 0.321, 'learning_rate': 0.00002, 'epoch': 3.0}
```

#### Training Complete

```log
2025-12-20 10:28:35 - INFO - ✅ Adapter saved to /workspace/finetuning/{job_id}/output/adapter_model
2025-12-20 10:28:35 - INFO - 🔄 Merging PEFT adapters into base model...
2025-12-20 10:28:46 - INFO - ✅ Merged model saved to /workspace/finetuning/{job_id}/output/merged_model
2025-12-20 10:28:46 - INFO - ✅ Training completed successfully
```

### Log File Locations

**Inside training container**:
```
/workspace/finetuning/{job_id}/
├── logs/
│   └── training.log              # Main training log
├── output/
│   ├── adapter_model/            # PEFT adapter
│   ├── merged_model/             # Final merged model
│   └── checkpoints/              # Intermediate checkpoints
└── input/
    ├── dataset/                  # Training data
    └── training_config.json      # Training config
```

**From backend container**:
```bash
# View training log
docker-compose exec backend cat /workspace/finetuning/{job_id}/logs/training.log

# List all files
docker-compose exec backend find /workspace/finetuning/{job_id} -type f

# Check checkpoint files
docker-compose exec backend ls -lh /workspace/finetuning/{job_id}/output/adapter_model/
```

### Celery Worker Logs

**For job orchestration and status updates**:

```bash
# Follow Celery worker logs
docker-compose logs -f celery-worker

# Search for specific job
docker-compose logs celery-worker | grep "3f68e08f"

# Check task status
docker-compose logs celery-worker | grep -E "Task.*succeeded|Task.*failed"
```

### Log Commands Cheat Sheet

```bash
# Real-time monitoring
docker logs -f finetuning-{job_id} 2>&1 | grep -E "Epoch|Step|Loss"

# Check for errors
docker logs finetuning-{job_id} 2>&1 | grep -i -E "error|exception|failed"

# GPU usage
docker logs finetuning-{job_id} 2>&1 | grep -i "gpu\|memory"

# Training metrics
docker logs finetuning-{job_id} 2>&1 | grep -E "{'loss'|'learning_rate'|'epoch'}"

# Save logs to file
docker logs finetuning-{job_id} > training_logs_$(date +%Y%m%d_%H%M%S).log

# Follow multiple containers
docker-compose logs -f backend celery-worker | grep "3f68e08f"
```

---

## Troubleshooting Guide

### Issue 1: No Metrics in Any Dashboard

**Symptoms**:
- TensorBoard shows "No dashboards are active"
- Grafana panels empty
- Prometheus has no finetuning targets

**Diagnosis**:
```bash
# Check if training container is running
docker ps | grep finetuning

# Check container logs
docker logs finetuning-{job_id} 2>&1 | tail -50

# Check job status
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/finetuning/jobs/{job_id}
```

**Possible Causes**:
1. Training hasn't started yet (wait 60-120 seconds)
2. Container crashed (check logs for errors)
3. Logs not being written (check log directory)

**Solutions**:
```bash
# Wait for training to start
sleep 60 && docker logs finetuning-{job_id}

# Check log directory
docker-compose exec backend ls -la /workspace/finetuning/{job_id}/logs/

# Restart observability services
docker-compose restart tensorboard grafana prometheus
```

---

### Issue 2: TensorBoard Shows Old Data

**Symptoms**:
- Metrics from previous job still visible
- New job metrics not appearing

**Solution**:
```bash
# Restart TensorBoard with fresh mount
docker-compose restart tensorboard

# Or specify exact log directory
docker-compose exec tensorboard tensorboard \
  --logdir=/logs/finetuning/{job_id} \
  --host=0.0.0.0 \
  --port=6006 \
  --reload_interval=5
```

---

### Issue 3: Grafana Dashboard Empty for SFT Job

**Symptoms**:
- "Reasoning Model" dashboard shows no data
- SFT job running successfully

**Expected Behavior**:
- Multi-reward dashboard only works for GRPO jobs
- SFT jobs don't emit reward metrics

**Solution**:
- Use TensorBoard for SFT jobs
- Create custom SFT dashboard in Grafana (see section above)
- Or wait for GRPO job to monitor multi-reward metrics

---

### Issue 4: Frontend Not Showing Real-Time Updates

**Symptoms**:
- Job stuck on "pending" status
- Progress bar not moving
- No log updates

**Diagnosis**:
```bash
# Check WebSocket connection
docker-compose logs frontend | grep -i websocket

# Check backend is sending updates
docker-compose logs backend | grep -i "job.*{job_id}"

# Test WebSocket manually
wscat -c ws://localhost:8000/ws/finetuning/{job_id}
```

**Solutions**:
```bash
# Refresh browser page
# Check browser console for errors (F12)

# Restart frontend
docker-compose restart frontend

# Check backend WebSocket endpoint
curl -i -N -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  http://localhost:8000/ws/finetuning/{job_id}
```

---

### Issue 5: Container Exited Immediately

**Symptoms**:
- Container appears then disappears
- Status shows "Exited (1)"

**Diagnosis**:
```bash
# Check container exit code
docker ps -a | grep finetuning

# Check logs
docker logs finetuning-{job_id}

# Common errors:
# - "Dataset not found"
# - "CUDA out of memory"
# - "Model download failed"
```

**Solutions**:
```bash
# Dataset issue: Check dataset was uploaded correctly
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/finetuning/datasets/{dataset_id}

# GPU memory: Reduce batch size or use smaller model
# Model download: Check internet connection, HuggingFace access
```

---

### Issue 6: Training Loss Not Decreasing

**Symptoms**:
- Loss stays flat or increases
- Model not learning

**Diagnosis**:
```bash
# Check learning rate
docker logs finetuning-{job_id} | grep learning_rate

# Check dataset quality
docker-compose exec backend cat /workspace/finetuning/{job_id}/input/dataset/train.json
```

**Possible Causes**:
1. Learning rate too low (increase to 1e-4 or 2e-4)
2. Learning rate too high (decrease to 1e-5)
3. Dataset too small (need more examples)
4. Dataset quality issues (incorrect format)

**Solutions**:
- Adjust hyperparameters and retry
- Add more training examples
- Validate dataset format

---

## Complete Monitoring Workflow

### Scenario 1: Monitoring SFT Training

**Step-by-Step Process**:

```bash
# 1. Submit training job
JOB_ID=$(curl -X POST "http://localhost:8000/api/v1/finetuning/jobs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @job_config.json | jq -r '.id')

echo "Job ID: $JOB_ID"

# 2. Wait for container to start (60 seconds)
sleep 60

# 3. Open TensorBoard in browser
echo "TensorBoard: http://localhost:6006"
# Navigate to Scalars tab

# 4. Monitor container logs
docker logs -f finetuning-$JOB_ID | grep -E "Epoch|Step|Loss" &
LOGS_PID=$!

# 5. Check job status via API every 30 seconds
while true; do
  STATUS=$(curl -s -H "Authorization: Bearer $TOKEN" \
    http://localhost:8000/api/v1/finetuning/jobs/$JOB_ID | jq -r '.status')
  echo "$(date): Job status = $STATUS"

  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    break
  fi

  sleep 30
done

# 6. Stop log monitoring
kill $LOGS_PID

# 7. View final results
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/finetuning/jobs/$JOB_ID | jq '.'
```

**What to Watch**:
1. **Minutes 0-2**: Model loading, no metrics yet
2. **Minutes 2-5**: Training starts, loss appears in TensorBoard
3. **Minutes 5-10**: Loss decreasing, learning rate adjusting
4. **Minutes 10-15**: Training completes, adapter merging

---

### Scenario 2: Monitoring GRPO Training with All Dashboards

**Multi-Dashboard Setup**:

```bash
# Terminal 1: Container logs
docker logs -f finetuning-{grpo_job_id} 2>&1 | grep -E "Reward|Step|Loss"

# Terminal 2: Job status polling
watch -n 10 'curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/finetuning/jobs/{grpo_job_id} | jq ".status, .progress"'

# Terminal 3: Prometheus metrics
watch -n 5 'curl -s "http://localhost:9090/api/v1/query?query=reward_total_score{job_id=\"{grpo_job_id}\"}" | jq ".data.result[0].value[1]"'
```

**Browser Tabs**:
1. **Tab 1**: TensorBoard (http://localhost:6006) - Training loss
2. **Tab 2**: Grafana (http://localhost:3000) - Reward breakdown dashboard
3. **Tab 3**: Frontend UI (http://localhost:3001/finetuning) - Job management
4. **Tab 4**: Prometheus (http://localhost:9090) - Raw metric queries

**Monitoring Checklist**:
- [ ] TensorBoard shows decreasing training loss
- [ ] Grafana shows increasing total reward
- [ ] Prometheus has all 6 reward component metrics
- [ ] Frontend UI shows "running" status with progress
- [ ] Container logs show step-by-step progress
- [ ] No errors in Celery worker logs

---

## Metric Reference

### SFT/PEFT Metrics

| Metric | Source | Typical Range | Interpretation |
|--------|--------|---------------|----------------|
| train/loss | TensorBoard | 2.0 → 0.3 | Lower = better learning |
| train/learning_rate | TensorBoard | 2e-4 → 0 | Warmup then decay |
| train/epoch | TensorBoard | 0.0 → 3.0 | Linear progression |
| train/global_step | TensorBoard | 0 → total_steps | Increments each batch |
| eval/loss | TensorBoard | 1.5 → 0.4 | Validation performance |

### GRPO Metrics

| Metric | Source | Typical Range | Weight | Interpretation |
|--------|--------|---------------|--------|----------------|
| reward_correctness_score | Prometheus/Grafana | 0.0 → 1.0 | 40% | Answer correctness |
| reward_reasoning_clarity_score | Prometheus/Grafana | 0.0 → 1.0 | 20% | Explanation clarity |
| reward_step_by_step_score | Prometheus/Grafana | 0.0 → 1.0 | 15% | Stepwise reasoning |
| reward_efficiency_score | Prometheus/Grafana | 0.0 → 1.0 | 10% | Brevity vs completeness |
| reward_mathematical_notation_score | Prometheus/Grafana | 0.0 → 1.0 | 10% | Math notation quality |
| reward_coherence_score | Prometheus/Grafana | 0.0 → 1.0 | 5% | Logical flow |
| reward_total_score | Prometheus/Grafana | 0.0 → 1.0 | 100% | Weighted sum |
| reasoning_avg_steps_count | Prometheus/Grafana | 3 → 10 | N/A | Average reasoning steps |

### Job Status Values

| Status | Description | Next State |
|--------|-------------|------------|
| pending | Waiting in Celery queue | running |
| running | Training in progress | completed, failed |
| completed | Successfully finished | N/A |
| failed | Error occurred | N/A |
| cancelled | User cancelled job | N/A |

---

## Quick Reference Commands

### Essential Commands

```bash
# Check all observability services
docker-compose ps | grep -E "tensorboard|grafana|prometheus"

# Find training container
docker ps | grep finetuning

# Monitor training logs
docker logs -f finetuning-{job_id} | grep -E "Epoch|Step|Loss"

# Check job status
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/finetuning/jobs/{job_id} | jq '.status, .progress'

# View TensorBoard logs
docker-compose exec backend cat /workspace/finetuning/{job_id}/logs/training.log

# Query Prometheus
curl 'http://localhost:9090/api/v1/query?query=reward_total_score{job_id="{job_id}"}'

# Check Celery task status
docker-compose logs celery-worker | grep "{job_id}"

# Restart all observability
docker-compose restart tensorboard grafana prometheus frontend
```

---

## Training Examples from Current Job

### Job Details

```json
{
  "job_id": "3f68e08f-1739-43e0-9d03-8685a77b74e7",
  "name": "Choles SFT - Company Knowledge",
  "status": "completed",
  "base_model": "Qwen/Qwen2.5-1.5B-Instruct",
  "finetuning_method": "peft",
  "training_objective": "qa",
  "duration_seconds": 358.44,
  "checkpoint_path": "minio://documents/technology/system-administrator/global/admin/finetuning/datasets/company_qa_dataset.jsonl/checkpoints/choles-sft---company-knowledge/3f68e08f-1739-43e0-9d03-8685a77b74e7/final/adapter_model/adapter_model.safetensors"
}
```

### LoRA Configuration

```
trainable params: 1,089,536
all params: 1,544,803,840
trainable%: 0.0705

LoRA Config:
- rank (r): 8
- alpha: 16
- dropout: 0.05
- target_modules: ["q_proj", "v_proj"]
- bias: none
- task_type: CAUSAL_LM
```

### Resource Usage

```
GPU: GPU 0
Memory: 90% of available (6.0GB reserved)
Quantization: 4-bit (QLoRA)
Model size: ~1.5B parameters
Training time: ~6 minutes (mock training)
```

---

## Conclusion

This guide covers all four observability platforms for monitoring fine-tuning jobs:

1. **TensorBoard**: Primary tool for SFT training metrics (loss, learning rate, epochs)
2. **Grafana**: Best for GRPO multi-reward visualization and time-series dashboards
3. **Prometheus**: Raw metric queries and custom PromQL analysis
4. **Frontend UI**: User-friendly job management and real-time status monitoring

### Best Practices

- **Always start with TensorBoard** for training loss visualization
- **Use Frontend UI** for high-level job management
- **Use Grafana** for GRPO reward breakdown (not applicable for SFT)
- **Use Prometheus** for debugging and custom metric queries
- **Monitor container logs** for detailed training progress and errors

### Next Steps

1. Complete SFT training validation (test finetuned model)
2. Upload GRPO dataset for reasoning training
3. Monitor GRPO job with all 4 dashboards
4. Document screenshots and examples from live training
5. Create custom Grafana dashboard for SFT jobs

---

**Document Version**: 1.0
**Last Updated**: 2025-12-20
**Author**: AI Assistant
**Training Job Reference**: 3f68e08f-1739-43e0-9d03-8685a77b74e7
