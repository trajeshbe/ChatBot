# Model Merge & Deploy Workflow - Complete Implementation

> **Date**: 2025-12-22
> **Status**: ✅ Complete
> **Feature**: LoRA Adapter Merge → Approval → Ollama Deployment

---

## 🎯 Overview

Complete end-to-end workflow for merging LoRA adapters with base models and deploying to Ollama for production use.

### Workflow Steps

```
1. Fine-Tuning Job Completes
   ↓
2. Model Registered (status: adapter_only/registered)
   ↓
3. **REQUEST MERGE** → Celery Task (5-15 min)
   ↓
4. Model Merged (status: merged)
   ↓
5. Request Approval (optional governance step)
   ↓
6. Admin Approves (status: approved)
   ↓
7. **DEPLOY TO OLLAMA** → Model Available in Chat UI
   ↓
8. Model Deployed (status: deployed)
```

---

## 📁 Files Modified/Created

### Backend

| File | Changes |
|------|---------|
| `backend/app/models/finetuning_models.py:199-203` | ✅ Added merge tracking fields to `FineTunedModel` ORM |
| `backend/app/api/routes/finetuning_routes.py:1000` | ✅ POST `/merge` endpoint (existing) |
| `backend/app/api/routes/finetuning_routes.py:1087` | ✅ GET `/merge-status` endpoint (existing) |
| `backend/app/services/finetuning/model_merge_service.py` | ✅ Merge service implementation (existing) |
| `backend/app/tasks/finetuning_tasks.py:1094` | ✅ Celery task `merge_lora_model_task` (existing) |
| `backend/migrations/023_add_merge_tracking_columns.sql` | ✅ Database migration (existing) |

### Frontend

| File | Status |
|------|--------|
| `frontend/src/components/finetuning/ModelMergeManager.tsx` | ✅ **NEW** - Standalone merge management UI |
| `frontend/src/components/finetuning/FineTuningGovernanceUI.tsx` | ✅ **UPDATED** - Added "Merge Models" navigation item |
| `frontend/src/components/finetuning/ModelLifecycleManager.tsx` | ✅ **UPDATED** - Added merge step in deployment tab |

---

## 🔧 Backend Implementation

### Database Schema (FineTunedModel)

```python
class FineTunedModel(Base):
    # ... existing fields ...

    # Merge tracking (migration 023)
    merged_model_path = Column(Text, nullable=True)  # Path to merged model
    merge_duration_seconds = Column(Integer, nullable=True)  # Duration in seconds
    merge_requested_at = Column(DateTime(timezone=True), nullable=True)  # Request timestamp
    merge_error_message = Column(Text, nullable=True)  # Error if failed

    # Status values:
    # - adapter_only / registered: Not merged yet
    # - merging: Merge in progress (Celery task running)
    # - merged: Merge complete, ready for deployment
    # - merge_failed: Merge error
    # - deployed: Model deployed to Ollama
```

### API Endpoints

#### 1. Request Merge

```http
POST /api/v1/finetuning/models/{model_id}/merge
Content-Type: application/json

{
  "base_model_name": "Qwen/Qwen2.5-1.5B-Instruct",
  "force_cpu": false
}
```

**Response:**
```json
{
  "task_id": "abc-123-def",
  "model_id": "uuid",
  "status": "merging",
  "message": "Merge task started. Expected duration: 5-15 minutes"
}
```

**Location**: `backend/app/api/routes/finetuning_routes.py:1000`

#### 2. Get Merge Status

```http
GET /api/v1/finetuning/models/{model_id}/merge-status
```

**Response:**
```json
{
  "model_id": "uuid",
  "status": "merged",
  "merged_model_path": "/workspace/finetuning/{job_id}/output/merged_model",
  "merge_duration_seconds": 420,
  "merge_requested_at": "2025-12-22T10:30:00Z",
  "merge_error_message": null
}
```

**Location**: `backend/app/api/routes/finetuning_routes.py:1087`

### Celery Background Task

**File**: `backend/app/tasks/finetuning_tasks.py:1094`

```python
@celery_app.task(name="merge_lora_model", bind=True)
def merge_lora_model_task(
    self,
    model_id: str,
    base_model_name: str = "Qwen/Qwen2.5-1.5B-Instruct",
    force_cpu: bool = False
)
```

**Process**:
1. Downloads LoRA adapter from MinIO
2. Loads base model from HuggingFace
3. Merges using PEFT's `merge_and_unload()`
4. Saves to `/workspace/finetuning/{job_id}/output/merged_model/`
5. Updates database with status and duration

**Expected Duration**: 5-15 minutes for 1.5B models

---

## 🎨 Frontend Implementation

### 1. ModelMergeManager Component

**File**: `frontend/src/components/finetuning/ModelMergeManager.tsx`

**Purpose**: Dedicated UI for managing model merge operations

**Features**:
- ✅ Display all models that can be merged (adapter_only, merging, merged, merge_failed)
- ✅ Request merge button with confirmation dialog
- ✅ Real-time merge progress monitoring (auto-polling every 5 seconds)
- ✅ Merge status badges (Adapter Only, Merging, Merged, Merge Failed)
- ✅ Merge duration and timestamp display
- ✅ Error messages for failed merges with retry option
- ✅ Links to MinIO for adapter checkpoints
- ✅ Info banner explaining workflow

**Access**:
- Navigate to: **Fine-Tuning Hub → Merge Models**
- Roles: `admin`, `ml_engineer`

**UI States**:

| Status | Badge Color | Actions Available |
|--------|-------------|-------------------|
| `adapter_only` | Blue | Request Merge |
| `merging` | Yellow (spinning) | View Progress |
| `merged` | Green | Ready for Deployment |
| `merge_failed` | Red | Retry Merge |

### 2. FineTuningGovernanceUI Updates

**File**: `frontend/src/components/finetuning/FineTuningGovernanceUI.tsx`

**Changes**:
- ✅ Added `GitMerge` icon import
- ✅ Added `ModelMergeManager` component import
- ✅ Added new navigation item: "Merge Models"
- ✅ Added role-based description for merge section

**Navigation Order**:
1. Models (Base Model Catalog)
2. Datasets
3. Fine-tuning Jobs
4. Evaluations
5. Adapters & Versions
6. **Merge Models** ← NEW
7. Deployment
8. Monitoring
9. Governance & Audit

### 3. ModelLifecycleManager Updates

**File**: `frontend/src/components/finetuning/ModelLifecycleManager.tsx`

**Changes**:
- ✅ Added merge-related fields to `Model` interface
- ✅ Added `merging` and `pollingMerge` state
- ✅ Added `requestMerge()` function
- ✅ Added merge status polling with `useEffect`
- ✅ Updated **Deployment Tab** to show:
  - Warning banner if model not merged
  - "Request Merge" button inline
  - Merge progress indicator
  - Success state when merged
  - Deploy button only enabled after merge

**Deployment Tab Flow**:

```
IF status = deployed:
  ✅ Show deployed info (URL, Ollama name)

ELSE IF status = merged:
  ✅ Show "Merge completed successfully"
  → Show deployment config form
  → Enable "Deploy Model" button

ELSE (adapter_only, registered, merging, merge_failed):
  ⚠️ Show warning: "Model must be merged before deployment"

  IF adapter_only OR registered:
    → Show "Request Merge" button

  ELSE IF merging:
    → Show progress indicator (5-15 minutes)

  ELSE IF merge_failed:
    → Show error message
    → Show "Retry Merge" button
```

---

## 🧪 Testing Guide

### Prerequisites

1. **Backend Running**:
   ```bash
   cd backend
   docker-compose up -d
   ```

2. **Celery Worker Running** (for merge tasks):
   ```bash
   docker-compose up -d celery-worker
   ```

3. **Frontend Running**:
   ```bash
   cd frontend
   npm run dev
   ```

4. **Completed Fine-Tuning Job**:
   - Must have a registered model with `minio_checkpoint_path`
   - Model status should be `adapter_only` or `registered`

### Test Workflow

#### Step 1: Navigate to Merge Models

1. Open browser: `http://localhost:3001`
2. Login as `admin` or `ml_engineer`
3. Go to: **Admin → Fine-Tuning Hub**
4. Click: **Merge Models** (in left navigation)

**Expected**: Should see grid of models ready for merge

#### Step 2: Request Merge

1. Find a model with status "Adapter Only" (blue badge)
2. Click: **Request Merge** button
3. Confirm dialog

**Expected**:
- ✅ Alert: "Merge started! Task ID: ..."
- ✅ Model status changes to "Merging..." (yellow badge with spinner)
- ✅ Progress indicator shows: "Started: [timestamp]"

#### Step 3: Monitor Merge Progress

**Expected** (auto-updates every 5 seconds):
- ✅ Merge progress indicator
- ✅ Estimated completion time shown
- ✅ After 5-15 minutes: Status changes to "Merged" (green badge)
- ✅ Alert: "Merge completed successfully!"

#### Step 4: Deploy via ModelLifecycleManager

1. Go to: **Fine-Tuning Hub → Models** (or use existing component)
2. Select the merged model
3. Click: **Deployment** tab

**Expected**:
- ✅ Green success banner: "Merge completed successfully"
- ✅ Deployment config form appears
- ✅ "Deploy Model" button is enabled

4. Configure:
   - Target: `ollama`
   - Model Name: `my-finetuned-model-v1`
5. Click: **Deploy Model**

**Expected**:
- ✅ Model deploys to Ollama
- ✅ Model status changes to `deployed`
- ✅ Model appears in Chat UI dropdown

#### Step 5: Verify in Chat UI

1. Go to: **Chat** page
2. Open: **Model Selector** dropdown
3. Find: `my-finetuned-model-v1` in Ollama section

**Expected**:
- ✅ Model appears in dropdown
- ✅ Can select and use for inference

### Error Testing

#### Test Merge Failure

1. Request merge with invalid base model name
2. **Expected**:
   - ✅ Status changes to "Merge Failed" (red badge)
   - ✅ Error message displayed
   - ✅ "Retry Merge" button appears

#### Test Pre-Deployment Validation

1. Try to deploy a model with status `adapter_only`
2. **Expected**:
   - ✅ Yellow warning banner: "Model must be merged before deployment"
   - ✅ "Request Merge" button shown inline
   - ✅ Deploy button NOT shown

---

## 📊 Status Values Reference

| Status | Meaning | UI Badge | Actions Available |
|--------|---------|----------|-------------------|
| `adapter_only` | LoRA adapter only, not merged | Blue | Request Merge |
| `registered` | Registered but not merged | Gray | Request Merge |
| `merging` | Merge in progress (Celery task) | Yellow (spinner) | View Progress |
| `merged` | Merge complete, ready to deploy | Green | Deploy |
| `merge_failed` | Merge error | Red | Retry Merge |
| `approved` | Deployment approved by admin | Green | Deploy |
| `deployed` | Deployed to Ollama/vLLM | Green (check) | Undeploy |
| `archived` | Undeployed/deprecated | Gray | None |

---

## 🔗 API Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      MERGE & DEPLOY WORKFLOW                    │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐
│ Fine-Tuning  │ status: completed
│ Job Complete │ minio_checkpoint_path: "finetuning/..."
└──────┬───────┘
       │
       ↓
┌──────────────────────────────────────────────────────────────────┐
│ POST /api/v1/finetuning/models/register                         │
│ → Creates FineTunedModel record                                 │
│ → status: "registered" or "adapter_only"                        │
└──────┬───────────────────────────────────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────────────────────────────────┐
│ UI: ModelMergeManager or ModelLifecycleManager                  │
│ → User clicks "Request Merge"                                   │
└──────┬───────────────────────────────────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────────────────────────────────┐
│ POST /api/v1/finetuning/models/{id}/merge                      │
│ → Triggers Celery task: merge_lora_model_task                  │
│ → Updates status: "merging"                                     │
│ → Returns task_id                                               │
└──────┬───────────────────────────────────────────────────────────┘
       │
       ↓ (5-15 minutes)
┌──────────────────────────────────────────────────────────────────┐
│ Celery Worker: merge_lora_model_task                           │
│ 1. Download adapter from MinIO                                  │
│ 2. Load base model (Qwen/Qwen2.5-1.5B-Instruct)               │
│ 3. Merge using PEFT merge_and_unload()                         │
│ 4. Save to /workspace/finetuning/{job_id}/output/merged_model/ │
│ 5. Update DB: status="merged", paths, duration                 │
└──────┬───────────────────────────────────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────────────────────────────────┐
│ UI: Auto-polling GET /api/v1/finetuning/models/{id}/merge-status│
│ → Detects status change to "merged"                            │
│ → Shows success alert                                           │
│ → Enables deployment                                            │
└──────┬───────────────────────────────────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────────────────────────────────┐
│ POST /api/v1/finetuning/models/{id}/deploy                     │
│ {                                                               │
│   "deployment_target": "ollama",                                │
│   "deployment_config": {                                        │
│     "model_name": "my-model-v1"                                 │
│   }                                                             │
│ }                                                               │
└──────┬───────────────────────────────────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────────────────────────────────┐
│ OllamaDeploymentService.deploy_model()                         │
│ 1. Check workspace FIRST: /workspace/.../merged_model/         │
│ 2. Generate Modelfile                                           │
│ 3. Create model in Ollama via HTTP API                         │
│ 4. Update DB: status="deployed", ollama_model_name, URL        │
└──────┬───────────────────────────────────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────────────────────────────────┐
│ Model Available in Chat UI Dropdown                             │
│ → Users can select and use for inference                       │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Design Decisions

### 1. Workspace-First Approach

**File**: `backend/app/services/ollama_deployment_service.py:43-71`

When deploying to Ollama, the service:
1. **First checks**: `/workspace/finetuning/{job_id}/output/merged_model/` (local, fast)
2. **Falls back to**: MinIO download if not found (slower)

**Benefit**: Eliminates unnecessary MinIO downloads for recently merged models.

### 2. Status-Driven UI

Models use a single `status` field to control UI flow:
- `adapter_only` → Show "Request Merge"
- `merging` → Show progress indicator
- `merged` → Enable deployment
- `deployed` → Show deployment info

### 3. Auto-Polling for Merge Progress

UI polls `/merge-status` every 5 seconds while status is `merging`:
- Minimal backend load
- Real-time updates for users
- Auto-stops when complete/failed

### 4. Inline Merge in Deployment Tab

Users can request merge directly from deployment tab:
- Reduces navigation friction
- Clear workflow progression
- Contextual guidance (warnings/success messages)

---

## 🚀 Next Steps (Future Enhancements)

### 1. Approval Workflow Integration (Optional)

If governance is required:

```
merged → request_approval → admin_approves → deploy
```

**Endpoints** (already implemented):
- `POST /api/v1/finetuning/models/{id}/request-approval`
- `POST /api/v1/finetuning/approvals/{id}/approve`
- `POST /api/v1/finetuning/approvals/{id}/reject`

### 2. Merge Progress Streaming

Replace polling with WebSocket streaming:
- Real-time merge progress (10%, 50%, 100%)
- Memory usage tracking
- ETL logs streaming

### 3. Multi-Base-Model Support

Allow users to select different base models:
- Dropdown for base model selection
- Validation for adapter compatibility
- Base model version tracking

### 4. Automated Testing

Add E2E Playwright tests:
- Merge request flow
- Status polling
- Deployment after merge
- Error handling

---

## 📖 User Documentation

### For ML Engineers

**How to Merge and Deploy a Fine-Tuned Model**:

1. **Complete Fine-Tuning Job**:
   - Wait for job status: `completed`
   - Verify adapter checkpoint exists in MinIO

2. **Merge LoRA Adapter**:
   - Go to: **Fine-Tuning Hub → Merge Models**
   - Find your model (status: "Adapter Only")
   - Click: **Request Merge**
   - Wait: 5-15 minutes (status auto-updates)

3. **Deploy to Ollama**:
   - Once merged (green badge), go to **Deployment** tab
   - Select deployment target: `ollama`
   - Enter model name: `my-model-v1`
   - Click: **Deploy Model**

4. **Use in Chat**:
   - Go to: **Chat** page
   - Select your model from dropdown
   - Start chatting!

### For Admins

**Monitoring Merge Operations**:

1. **Track Active Merges**:
   - Go to: **Fine-Tuning Hub → Merge Models**
   - View models with "Merging..." status
   - Check merge duration (should be < 15 min)

2. **Handle Failures**:
   - Red badge indicates merge failed
   - Check `merge_error_message` in model details
   - Common issues:
     - Out of memory (increase GPU/CPU)
     - Invalid adapter path
     - Base model download failed

3. **Database Query**:
   ```sql
   SELECT
     name,
     status,
     merge_duration_seconds,
     merge_requested_at,
     merge_error_message
   FROM finetuned_models
   WHERE status IN ('merging', 'merge_failed')
   ORDER BY merge_requested_at DESC;
   ```

---

## ✅ Checklist

- [x] Database migration applied (023_add_merge_tracking_columns.sql)
- [x] FineTunedModel ORM updated with merge fields
- [x] ModelMergeManager component created
- [x] FineTuningGovernanceUI navigation updated
- [x] ModelLifecycleManager deployment tab updated
- [x] Merge API endpoints tested (`/merge`, `/merge-status`)
- [x] Celery merge task verified
- [x] UI auto-polling implemented
- [x] Error handling (merge failures)
- [x] Documentation created

---

## 🐛 Troubleshooting

### Issue: Merge task stuck in "merging" status

**Diagnosis**:
```bash
# Check Celery worker logs
docker-compose logs celery-worker

# Check task status
celery -A app.tasks inspect active
```

**Solution**:
- Restart Celery worker: `docker-compose restart celery-worker`
- Check GPU/CPU availability
- Verify MinIO adapter path exists

### Issue: "Model must be merged" warning persists after merge

**Diagnosis**:
```bash
# Check model status in database
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT id, name, status, merged_model_path FROM finetuned_models WHERE name = 'your-model-name';"
```

**Solution**:
- Refresh browser
- Verify status is `merged` in database
- Check frontend console for API errors

### Issue: Deployed model not appearing in Chat UI

**Diagnosis**:
```bash
# Check Ollama models
curl http://localhost:11434/api/tags

# Check model status
curl http://localhost:8000/api/v1/finetuning/models-public
```

**Solution**:
- Verify `ollama_model_name` is set in database
- Verify `status = 'deployed'`
- Refresh Chat UI model dropdown

---

## 📚 Related Documentation

- [Fine-Tuning Complete Implementation](./FINETUNING_COMPLETE_IMPLEMENTATION_GUIDE.md)
- [Model Registry Service](../../../backend/app/services/finetuning/model_registry_service.py)
- [Ollama Deployment Service](../../../backend/app/services/ollama_deployment_service.py)
- [Celery Tasks](../../../backend/app/tasks/finetuning_tasks.py)
- [Migration 023](../../../backend/migrations/023_add_merge_tracking_columns.sql)

---

**End of Documentation**
