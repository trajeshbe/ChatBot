# Fine-Tuning UI Dashboard - Access Guide

**Date**: 2025-12-16
**Status**: ✅ Backend Fixed, UI Ready

---

## 🎯 Quick Access

### Step 1: Open the Admin Dashboard

```
URL: http://localhost:3001/admin
```

### Step 2: Navigate to Fine-Tuning Tab

1. Login with admin credentials (username: `admin`, password: `admin`)
2. Click on the **"Fine-tuning"** tab in the top navigation
3. You'll see 8 sections:
   - **Models** - Base model catalog
   - **Datasets** - Dataset management
   - **Fine-tuning Jobs** ← THIS IS WHERE YOUR JOB IS
   - **Evaluations** - Model evaluation
   - **Adapters & Versions** - Adapter management
   - **Deployment** - Model deployment
   - **Monitoring** - Training metrics
   - **Governance & Audit** - Compliance logs

### Step 3: View Your Completed Training Job

Click on **"Fine-tuning Jobs"** to see:

```
Job Name: Qwen 2.5 1.5B - CloudSync Support
Status: ✅ completed
Progress: 100%
Base Model: qwen-2.5-1.5b
Method: peft (QLoRA)
Training Time: 17 seconds (simulated)
Created: 2025-12-16T17:06:41Z
Completed: 2025-12-16T17:11:10Z
```

---

## 🔍 What You Should See

### Jobs Grid View

The dashboard displays a **grid of all training jobs** with:

#### Job Cards showing:
- **Status Badge**: completed (green), running (blue), pending (yellow), failed (red)
- **Progress Bar**: Visual representation of training progress
- **Job Name**: "Qwen 2.5 1.5B - CloudSync Support"
- **Base Model**: qwen-2.5-1.5b
- **Method**: peft (QLoRA with 4-bit quantization)
- **Hyperparameters**:
  - LoRA rank (r): 16
  - LoRA alpha: 32
  - LoRA dropout: 0.05
  - Learning rate: 2e-4
  - Epochs: 3
  - Batch size: 4
  - Max sequence length: 512

#### Filtering & Search:
- **Search bar**: Filter by name or model
- **Status filter**: all, pending, queued, running, completed, failed, cancelled
- **Method filter**: all, peft, sft, rlhf-ppo, rlhf-grpo
- **Sort by**: created_at, status, progress

#### Bulk Actions (for selected jobs):
- Cancel selected jobs
- Delete selected jobs
- Clone job configurations
- Compare jobs side-by-side

---

## 📊 Backend API Status

All endpoints are now **✅ WORKING**:

### 1. List Jobs
```bash
GET http://localhost:8000/api/v1/finetuning/jobs
```

**Response**:
```json
{
  "jobs": [
    {
      "id": "c4ad0963-b194-4f85-b816-3fd0fdaaff9d",
      "name": "Qwen 2.5 1.5B - CloudSync Support",
      "status": "completed",
      "base_model": "qwen-2.5-1.5b",
      "finetuning_method": "peft",
      "started_at": "2025-12-16T17:10:52.999685Z",
      "completed_at": "2025-12-16T17:11:10.657659Z"
    }
  ],
  "total": 2
}
```

### 2. Get Job Details
```bash
GET http://localhost:8000/api/v1/finetuning/jobs/{job_id}
```

**Returns**: Full job details including hyperparameters

### 3. Create Training Job
```bash
POST http://localhost:8000/api/v1/finetuning/jobs
```

**Status**: ✅ Working (tested with CloudSync QA dataset)

---

## 🔧 Recent Fixes Applied

### Issue 1: Column Name Mismatches
**Problem**: API returned 500 errors because response used wrong database column names

**Fixed**:
```python
# OLD (broken):
checkpoint_path = job.checkpoint_path
started_at = job.started_at
completed_at = job.completed_at
training_duration_seconds = job.training_duration_seconds

# NEW (working):
checkpoint_path = job.minio_checkpoint_path
started_at = job.training_start_time
completed_at = job.training_end_time
training_duration_seconds = job.training_time_seconds
```

**Files Modified**:
- `/backend/app/api/routes/finetuning_routes.py` (lines 650-655, 693-698)

**Restarted**: Backend container to apply fixes

---

## 🎨 UI Components

The fine-tuning UI consists of:

### Main Component
**`FineTuningGovernanceUI.tsx`**
- Top-level container with 8-section navigation
- Role-based access control
- Stats dashboard (running jobs, pending approvals, active models)

### Job Management Components

1. **`TrainingJobsManagerEnhanced.tsx`**
   - Grid view of all jobs
   - Filtering and search
   - Bulk operations
   - Auto-refresh every 10 seconds

2. **`JobManager.tsx`**
   - Job creation form
   - Hyperparameter configuration
   - Dataset selection

3. **`MonitoringDashboard.tsx`**
   - Real-time training metrics
   - Loss curves
   - GPU utilization
   - Progress tracking

4. **`DatasetInspector.tsx`**
   - Dataset upload
   - Preview samples
   - Validation status

5. **`ModelCatalog.tsx`**
   - Base model selection
   - Model specifications
   - Quantization options

---

## 🚀 Creating a New Training Job (UI Workflow)

### Step 1: Upload Dataset
1. Navigate to **Datasets** section
2. Click **"Upload Dataset"**
3. Select file (JSONL, CSV, JSON)
4. Choose format type: `qa`, `classification`, `generation`
5. Map columns (input, output, context)
6. Click **"Upload"**

### Step 2: Create Job
1. Navigate to **Fine-tuning Jobs** section
2. Click **"Create New Job"** button
3. Fill in job configuration:
   - **Name**: Descriptive job name
   - **Base Model**: Select from dropdown (Qwen, Llama, Mistral)
   - **Quantization**: 4-bit (recommended), 8-bit, or none
   - **Method**: PEFT (QLoRA), SFT, RLHF-PPO, RLHF-GRPO
   - **Dataset**: Select uploaded dataset
   - **Training Objective**: qa, classification, generation

4. Configure hyperparameters:
   - **LoRA rank (r)**: 8, 16, 32, 64 (higher = more capacity, slower training)
   - **LoRA alpha**: Typically 2×r (e.g., r=16 → alpha=32)
   - **LoRA dropout**: 0.05 (5% dropout for regularization)
   - **Learning rate**: 1e-4 to 5e-4 (2e-4 is a good default)
   - **Epochs**: 1-5 (start with 3)
   - **Batch size**: 4, 8, 16 (depends on GPU memory)
   - **Max sequence length**: 512, 1024, 2048

5. Click **"Create Job"**
6. Optionally check **"Auto-start"** to begin training immediately

### Step 3: Monitor Training
1. Job appears in grid with status "queued" or "running"
2. Progress bar updates in real-time
3. Click on job card for detailed view:
   - Current epoch/step
   - Training loss curve
   - GPU utilization
   - Estimated time remaining

### Step 4: View Results
1. When status changes to "completed", click job card
2. Review final metrics:
   - Final train loss
   - Training duration
   - Checkpoint location
3. Click **"Deploy"** to deploy to Ollama (future feature)

---

## 🧪 Testing the UI

### Test Scenario 1: View Existing Job

1. Open http://localhost:3001/admin
2. Login (admin/admin)
3. Click **"Fine-tuning"** tab
4. Click **"Fine-tuning Jobs"** subsection
5. **Expected**: You should see 1-2 job cards
6. **Job Status**: completed (green badge)
7. **Progress**: 100% progress bar

### Test Scenario 2: Create New Job

1. In **Fine-tuning Jobs** section, click **"Create New Job"**
2. Fill in form:
   ```
   Name: Test Job - Qwen 7B
   Base Model: Qwen/Qwen2.5-7B-Instruct
   Dataset: (select CloudSync Support QA)
   Method: peft
   Objective: qa
   Quantization: 4bit
   ```
3. Click **"Create Job"**
4. **Expected**: Job appears in grid with status "pending" or "queued"

### Test Scenario 3: Filter Jobs

1. In search bar, type "CloudSync"
2. **Expected**: Only CloudSync jobs are shown
3. In status filter dropdown, select "completed"
4. **Expected**: Only completed jobs shown
5. Click **"Clear Filters"**
6. **Expected**: All jobs visible again

---

## 🐛 Troubleshooting

### Issue: "No jobs are displayed"

**Check 1**: Backend is running
```bash
docker-compose ps backend
# Should show "Up"
```

**Check 2**: Backend is healthy
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

**Check 3**: API returns jobs
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin"}' | jq -r '.access_token')

curl -s http://localhost:8000/api/v1/finetuning/jobs \
  -H "Authorization: Bearer $TOKEN" | jq .
```

**Check 4**: Frontend can reach backend
- Open browser console (F12)
- Check Network tab for API calls
- Should see: `GET http://localhost:8000/api/v1/finetuning/jobs` → Status 200

### Issue: "Jobs list loads but shows 0 jobs"

**Possible Cause**: Database has no jobs

**Solution**: Create a test job via API
```bash
python3 /tmp/test_job_creation.py
```

### Issue: "Page shows 'Permission denied'"

**Possible Cause**: User doesn't have `model_finetuning` module permission

**Solution**: Check user permissions
```bash
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c \
  "SELECT u.username, r.name as role, m.name as module
   FROM users u
   JOIN user_roles ur ON u.id = ur.user_id
   JOIN roles r ON ur.role_id = r.id
   JOIN role_permissions rp ON r.id = rp.role_id
   JOIN modules m ON rp.module_id = m.id
   WHERE u.username = 'admin' AND m.name = 'model_finetuning';"
```

### Issue: "Job details don't load"

**Check**: Job ID exists in database
```bash
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c \
  "SELECT id, name, status FROM finetuning_jobs LIMIT 5;"
```

---

## 📈 Monitoring Dashboard (Future Enhancement)

The **Monitoring** section will show:

### Real-time Metrics
- **Loss Curves**: Train/eval loss over time
- **Learning Rate Schedule**: LR warmup and decay
- **GPU Utilization**: Memory usage, compute utilization
- **Throughput**: Samples/second, tokens/second

### System Health
- **GPU Pool Status**: Available/allocated GPUs
- **Queue Status**: Jobs waiting, running, completed
- **Resource Utilization**: CPU, memory, disk

### Cost Tracking
- **Training Cost**: GPU hours × hourly rate
- **Storage Cost**: Checkpoint storage
- **Total Cost**: Running total per project/user

---

## 🎓 Next Steps

### For Viewing Existing Jobs (Now):
1. ✅ Open http://localhost:3001/admin
2. ✅ Navigate to Fine-tuning tab → Fine-tuning Jobs
3. ✅ See your completed job with 100% progress

### For Creating New Jobs (Now):
1. ✅ Upload dataset in Datasets section
2. ✅ Create job in Fine-tuning Jobs section
3. ⏳ Job will be queued (no actual training yet)

### For Actual Training (Next):
1. ⏳ Implement Celery task queue
2. ⏳ Implement GPU pool manager
3. ⏳ Implement training container with PyTorch
4. ⏳ Real-time progress updates
5. ⏳ Model deployment to Ollama

### For Deployment (Steps 5-6):
1. ⏳ Export trained adapter
2. ⏳ Create Ollama Modelfile
3. ⏳ Deploy to Ollama service
4. ⏳ Test inference endpoint
5. ⏳ Compare pre/post fine-tuning performance

---

## 📝 Summary

### ✅ What's Working Now

1. **Backend APIs**
   - List jobs: GET /api/v1/finetuning/jobs ✅
   - Get job details: GET /api/v1/finetuning/jobs/{id} ✅
   - Create job: POST /api/v1/finetuning/jobs ✅
   - Upload dataset: POST /api/v1/finetuning/datasets/upload ✅

2. **Frontend UI**
   - Admin dashboard accessible at http://localhost:3001/admin ✅
   - Fine-tuning tab with 8 sections ✅
   - Job list grid with filtering/search ✅
   - Real-time updates (10-second refresh) ✅

3. **Database**
   - Jobs persisted with full details ✅
   - Datasets linked correctly ✅
   - Metrics recorded (epoch, step, loss) ✅

### ⏳ What's Pending

1. **Actual Training Execution**
   - Celery task queue
   - GPU allocation
   - PyTorch training loop
   - Real-time progress streaming

2. **Model Deployment**
   - Export trained adapter
   - Merge with base model
   - Deploy to Ollama
   - Create inference endpoint

3. **Performance Testing**
   - Pre/post fine-tuning comparison
   - Quality metrics
   - Benchmark queries

---

## 🔗 Quick Links

- **Frontend**: http://localhost:3001/admin
- **Backend API Docs**: http://localhost:8000/api/docs
- **Backend Health**: http://localhost:8000/health
- **Test Scripts**:
  - `/tmp/test_job_creation.py`
  - `/tmp/test_job_status.py`
  - `/tmp/test_jobs_list.py`
- **Simulation Script**: `/app/simulate_training.py` (in backend container)

---

**Status**: UI Dashboard ✅ READY - Go check it out at http://localhost:3001/admin!
