# Grafana Training Metrics Dashboard - Setup Guide

**Date**: 2025-12-18
**Purpose**: Monitor fine-tuning training metrics (Loss, Accuracy, Progress)
**Status**: Dashboard Created ✅ | Metrics Export TODO ⚠️

---

## What Was Created

### 1. Grafana Dashboard JSON
**File**: `observability/grafana/dashboards/finetuning-metrics.json`

**Dashboard Panels**:
1. **Training Loss** (Time Series) - Shows `train_loss` over time
2. **Evaluation Loss** (Time Series) - Shows `eval_loss` over time
3. **Recent Jobs Table** (PostgreSQL) - Last 24 hours of jobs with loss values
4. **Current Epoch** (Stat) - Current training epoch
5. **Training Progress** (Gauge) - Percentage complete
6. **Total Steps** (Stat) - Total training steps
7. **Job Status** (Stat) - Training/Not Training indicator

---

## How to Import Dashboard

### Method 1: Grafana UI
1. **Open Grafana**: http://localhost:3000
2. **Login**: admin/admin
3. **Navigate**: Dashboards → New → Import
4. **Upload**: Select `observability/grafana/dashboards/finetuning-metrics.json`
5. **Configure**:
   - Prometheus datasource: `prometheus` (should auto-select)
   - PostgreSQL datasource: Add if not exists
6. **Import**

### Method 2: Docker Volume Mount (Persistent)
Add to `docker-compose.yml`:
```yaml
grafana:
  volumes:
    - ./observability/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
    - ./observability/grafana/provisioning:/etc/grafana/provisioning:ro
```

Then restart Grafana:
```bash
docker-compose restart grafana
```

---

## Current Status

### ✅ Working Now
1. **PostgreSQL Panel** - Shows recent jobs from database
   - Pulls data directly from `finetuning_jobs` table
   - Shows: name, status, train_loss, eval_loss, epoch, progress, created_at

### ⚠️ Not Working Yet (Needs Implementation)
2. **Prometheus Metrics Panels** - Need metrics export code
   - Training Loss (Time Series)
   - Evaluation Loss (Time Series)
   - Current Epoch (Stat)
   - Training Progress (Gauge)
   - Total Steps (Stat)
   - Job Status (Stat)

**Why**: Training code doesn't export Prometheus metrics yet

---

## TODO: Add Prometheus Metrics Export

To make all panels work, need to add metrics export to training code.

### Step 1: Add Prometheus Client to Requirements
**File**: `backend/requirements.txt`
```
prometheus-client==0.20.0
```

### Step 2: Create Metrics in Training Task
**File**: `backend/app/tasks/finetuning_tasks.py`

Add at top of file:
```python
from prometheus_client import Gauge, Counter

# Define Prometheus metrics
finetuning_train_loss = Gauge(
    'finetuning_train_loss',
    'Current training loss',
    ['job_id', 'job_name', 'model']
)

finetuning_eval_loss = Gauge(
    'finetuning_eval_loss',
    'Current evaluation loss',
    ['job_id', 'job_name', 'model']
)

finetuning_current_epoch = Gauge(
    'finetuning_current_epoch',
    'Current training epoch',
    ['job_id', 'job_name']
)

finetuning_progress_percent = Gauge(
    'finetuning_progress_percent',
    'Training progress percentage',
    ['job_id', 'job_name']
)

finetuning_total_steps = Gauge(
    'finetuning_total_steps',
    'Total training steps',
    ['job_id', 'job_name']
)

finetuning_job_status = Gauge(
    'finetuning_job_status',
    'Job status (1=training, 0=not training)',
    ['job_id', 'job_name', 'status']
)
```

### Step 3: Update Metrics During Training
In `run_finetuning_job` task, after updating database:
```python
# Update Prometheus metrics
finetuning_train_loss.labels(
    job_id=job_id,
    job_name=job.name,
    model=job.base_model
).set(job.train_loss or 0)

finetuning_eval_loss.labels(
    job_id=job_id,
    job_name=job.name,
    model=job.base_model
).set(job.eval_loss or 0)

finetuning_current_epoch.labels(
    job_id=job_id,
    job_name=job.name
).set(job.current_epoch or 0)

finetuning_progress_percent.labels(
    job_id=job_id,
    job_name=job.name
).set(job.progress or 0)

finetuning_total_steps.labels(
    job_id=job_id,
    job_name=job.name
).set(job.total_steps or 0)

# Job status: 1 if running, 0 otherwise
status_value = 1 if job.status == 'running' else 0
finetuning_job_status.labels(
    job_id=job_id,
    job_name=job.name,
    status=job.status
).set(status_value)
```

### Step 4: Expose Metrics Endpoint
Already exists at: `http://localhost:8000/metrics`

Verify it's accessible to Prometheus:
```bash
curl http://localhost:8000/metrics | grep finetuning
```

### Step 5: Configure Prometheus Scrape
**File**: `observability/prometheus/prometheus.yml`

Ensure backend is being scraped:
```yaml
scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

---

## PostgreSQL Datasource Setup

If PostgreSQL datasource doesn't exist in Grafana:

### Add PostgreSQL Datasource
1. **Grafana UI**: Configuration → Data Sources → Add data source
2. **Type**: PostgreSQL
3. **Configuration**:
   - Host: `postgres:5432`
   - Database: `ragchatbot`
   - User: `postgres`
   - Password: `postgres`
   - SSL Mode: `disable`
   - Version: `16+`
4. **Save & Test**

---

## Expected Metrics in Prometheus

After implementing metrics export, you should see:

```
# HELP finetuning_train_loss Current training loss
# TYPE finetuning_train_loss gauge
finetuning_train_loss{job_id="uuid",job_name="story8",model="Qwen/Qwen2.5-1.5B-Instruct"} 0.42

# HELP finetuning_eval_loss Current evaluation loss
# TYPE finetuning_eval_loss gauge
finetuning_eval_loss{job_id="uuid",job_name="story8",model="Qwen/Qwen2.5-1.5B-Instruct"} 0.38

# HELP finetuning_current_epoch Current training epoch
# TYPE finetuning_current_epoch gauge
finetuning_current_epoch{job_id="uuid",job_name="story8"} 1

# HELP finetuning_progress_percent Training progress percentage
# TYPE finetuning_progress_percent gauge
finetuning_progress_percent{job_id="uuid",job_name="story8"} 65.5

# HELP finetuning_total_steps Total training steps
# TYPE finetuning_total_steps gauge
finetuning_total_steps{job_id="uuid",job_name="story8"} 100

# HELP finetuning_job_status Job status (1=training, 0=not training)
# TYPE finetuning_job_status gauge
finetuning_job_status{job_id="uuid",job_name="story8",status="running"} 1
```

---

## Verification Steps

### 1. Check Prometheus Targets
```bash
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="backend")'
```

**Expected**: Should show backend target as "up"

### 2. Query Metrics in Prometheus
Open: http://localhost:9090/graph

Query:
```
finetuning_train_loss
```

**Expected**: Should return current training loss values

### 3. View Dashboard in Grafana
Open: http://localhost:3000/d/finetuning-metrics

**Expected**: All panels showing data

---

## Dashboard Features

### Real-Time Monitoring
- Training and evaluation loss trends
- Current progress and status
- Historical data for last 6 hours (adjustable)

### Multi-Job Support
- Each metric labeled with `job_name` and `job_id`
- Can filter by specific job in dashboard variables (future enhancement)

### Database Integration
- Table panel pulls directly from PostgreSQL
- Shows completed jobs with final metrics
- No Prometheus required for table panel

---

## Troubleshooting

### Dashboard Shows "No Data"
1. **Check Prometheus datasource**: Configuration → Data Sources → prometheus
2. **Verify metrics exist**: `curl http://localhost:9090/api/v1/query?query=finetuning_train_loss`
3. **Check time range**: Dashboard defaults to last 6 hours

### PostgreSQL Panel Empty
1. **Check datasource connection**: Test connection in Grafana
2. **Verify database**: `docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM finetuning_jobs;"`
3. **Check time filter**: Panel shows last 24 hours

### Metrics Not Updating
1. **Check celery worker logs**: `docker-compose logs celery-worker | grep finetuning`
2. **Verify Prometheus scraping**: http://localhost:9090/targets
3. **Check scrape interval**: Default 10s, may need wait time

---

## Benefits

1. **Real-Time Visibility**: See training progress without checking logs
2. **Historical Analysis**: Compare training runs over time
3. **Early Problem Detection**: Spot diverging loss or stalled training
4. **Multi-Job Monitoring**: Track multiple training jobs simultaneously
5. **Persistent Storage**: Prometheus retains metrics for time-series analysis

---

## Next Steps

**Priority 1**: Implement Prometheus metrics export in training code
**Priority 2**: Test dashboard with live training job
**Priority 3**: Add alerting rules for training failures
**Priority 4**: Extend dashboard with GPU utilization metrics

---

**Created**: 2025-12-18
**Dashboard UID**: `finetuning-metrics`
**Dashboard URL**: http://localhost:3000/d/finetuning-metrics
**Prometheus URL**: http://localhost:9090
**Status**: Dashboard Ready | Metrics Export Needed ⚠️
