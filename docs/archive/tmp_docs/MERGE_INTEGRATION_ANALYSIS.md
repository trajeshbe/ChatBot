# LoRA Merge Integration Analysis

**Date**: 2025-12-22
**Analysis**: Existing Ollama deployment infrastructure and merge integration points

---

## 🎯 Executive Summary

**Good News**: Your existing Ollama deployment infrastructure is **production-ready** and **merge-aware**!

### Key Findings:

✅ **Ollama deployment service exists** (`ollama_deployment_service.py`)
✅ **Already checks for merged models** (workspace-first optimization)
✅ **Database schema partially ready** (has `ollama_model_name`, `deployment_url`)
✅ **API routes exist** (finetuning_routes.py integrates OllamaDeploymentService)
⚠️ **Missing**: Merge tracking columns (status, path, duration)
⚠️ **Missing**: Merge service implementation
⚠️ **Missing**: Merge API endpoints

---

## 📊 Current Architecture Analysis

### 1. OllamaDeploymentService (ALREADY EXISTS!)

**File**: `backend/app/services/ollama_deployment_service.py`

**Key Features** (lines 43-72):
```python
# OPTIMIZED: Try workspace first, then download from MinIO as fallback
if model_path.startswith("minio://"):
    # Extract job_id from MinIO path to check workspace
    workspace_merged = f"/workspace/finetuning/{job_id}/output/merged_model"
    if os.exists(workspace_merged):
        logger.info(f"✅ Using merged model from workspace: {workspace_merged}")
        logger.info(f"   (Skipping MinIO download for efficiency)")
        local_model_path = workspace_merged
    else:
        logger.warning(f"⚠️  Workspace not found, falling back to MinIO download")
        local_model_path = await self._download_from_minio(model_path)
```

**Smart Optimization**: Already checks `/workspace/finetuning/{job_id}/output/merged_model` FIRST!

**This means**:
- ✅ If merge service saves to workspace, deployment will find it automatically
- ✅ No MinIO download needed (saves time!)
- ✅ Seamless integration with our merge service

**Modelfile Generation** (lines 204-254):
```python
# Detects merged vs adapter models
if "adapter_model" in model_path and "merged_model" not in model_path:
    logger.warning(f"⚠️ Using adapter_model path - may not work correctly")
    use_adapter = True
else:
    # Preferred: Use merged model directly (FROM points to merged model)
    modelfile_content = f"""
FROM {model_path}  # ← Points directly to merged model directory
PARAMETER temperature {parameters.get('temperature', 0.7)}
...
"""
```

**Perfect!**: Already prefers merged models over adapters!

---

### 2. Database Schema - Existing Columns

**Table**: `finetuned_models`

**Already exists**:
| Column | Type | Purpose | Status |
|--------|------|---------|--------|
| `ollama_model_name` | VARCHAR(255) | Deployed model name | ✅ Ready |
| `deployment_url` | VARCHAR(512) | Ollama endpoint URL | ✅ Ready |
| `minio_checkpoint_path` | VARCHAR(512) | Adapter checkpoint path | ✅ Ready |
| `status` | VARCHAR(50) | Generic status field | ✅ Can reuse for merge status |

**Missing columns for merge tracking**:
- `merged_model_path` TEXT - Path to merged model in MinIO/workspace
- `merge_status` VARCHAR(50) - Separate merge status (optional if reusing `status`)
- `merge_duration_seconds` INTEGER - Merge performance tracking
- `merge_requested_at` TIMESTAMPTZ - Audit trail
- `merge_error_message` TEXT - Error details

**Recommendation**: **REUSE `status` column** for merge status to avoid migration!

**Status values** can be:
- `adapter_only` - Training complete, not merged
- `merging` - Merge in progress
- `merged` - Merge complete, ready for deployment
- `deployed` - Deployed to Ollama
- `merge_failed` - Merge failed

---

### 3. API Integration Points

**File**: `backend/app/api/routes/finetuning_routes.py`

**Existing import** (line 67):
```python
from app.services.ollama_deployment_service import OllamaDeploymentService
```

**Perfect!**: Already imports OllamaDeploymentService!

**Where to add merge endpoints**:
```python
# Add after line 100 (dataset endpoints)
# Add before model registry endpoints

@router.post("/models/{model_id}/merge")
async def merge_lora_adapters(...):
    # Trigger merge Celery task
    pass

@router.get("/models/{model_id}/merge-status")
async def get_merge_status(...):
    # Return merge status from database
    pass
```

---

## 🔗 Integration Strategy

### Option 1: Minimal Migration (RECOMMENDED)

**Advantages**:
- No database migration needed
- Reuse existing `status` column
- Add only 2 new columns: `merged_model_path`, `merge_duration_seconds`
- Fastest to implement (~1 day)

**Database Change**:
```sql
ALTER TABLE finetuned_models
ADD COLUMN merged_model_path TEXT,
ADD COLUMN merge_duration_seconds INTEGER;

-- Update status enum if needed (check current constraint)
-- Or just use status values without constraint
```

**Merge Workflow**:
```
Training complete → status='adapter_only'
                 ↓
User clicks "Merge" → status='merging'
                 ↓
Merge service runs → saves to /workspace/{job_id}/output/merged_model
                 ↓
Merge complete → status='merged', merged_model_path='minio://...'
                 ↓
User clicks "Deploy" → OllamaDeploymentService.deploy_model()
                    → (finds merged model in workspace automatically!)
                 ↓
Deploy complete → status='deployed', ollama_model_name='choles-qa-v1'
```

---

### Option 2: Full Migration (COMPREHENSIVE)

**Advantages**:
- Separate merge status tracking
- Better audit trail
- Clearer status separation

**Database Change**:
```sql
ALTER TABLE finetuned_models
ADD COLUMN merged_model_path TEXT,
ADD COLUMN merge_status VARCHAR(50) DEFAULT 'not_merged'
    CHECK (merge_status IN ('not_merged', 'merging', 'merged', 'merge_failed')),
ADD COLUMN merge_requested_at TIMESTAMPTZ,
ADD COLUMN merge_duration_seconds INTEGER,
ADD COLUMN merge_error_message TEXT;

CREATE INDEX idx_finetuned_models_merge_status ON finetuned_models(merge_status);
```

**Complexity**: Higher (requires more testing)

---

## 📝 Implementation Checklist

### Phase 1: Database Schema (1 hour)

- [ ] Choose migration strategy (Option 1 recommended)
- [ ] Create migration file
- [ ] Test migration locally
- [ ] Apply to dev environment

### Phase 2: Merge Service (6 hours)

**File**: `backend/app/services/finetuning/model_merge_service.py` (NEW)

**Key integration points**:
```python
class ModelMergeService:
    def merge_lora_adapters(self, model_id, adapter_path, base_model):
        # 1. Download adapter from MinIO (or use workspace)
        # 2. Load base model from HuggingFace
        # 3. Merge using PEFT: model.merge_and_unload()
        # 4. Save to /workspace/{job_id}/output/merged_model  ← KEY PATH!
        # 5. Upload to MinIO (optional, workspace is enough)
        # 6. Update database: status='merged', merged_model_path='...'
```

**Critical**: Save to `/workspace/finetuning/{job_id}/output/merged_model`
- OllamaDeploymentService already checks this path!
- Avoids MinIO download during deployment

### Phase 3: Celery Task (2 hours)

**File**: `backend/app/tasks/finetuning_tasks.py` (add to existing)

```python
@celery.task(name="merge_lora_model", bind=True)
def merge_lora_model_task(self, model_id, adapter_path, base_model):
    # Call ModelMergeService
    pass
```

### Phase 4: API Endpoints (2 hours)

**File**: `backend/app/api/routes/finetuning_routes.py` (add to existing)

```python
@router.post("/api/v1/finetuning/models/{model_id}/merge")
async def merge_lora_adapters(...):
    # Trigger Celery task
    pass

@router.get("/api/v1/finetuning/models/{model_id}/merge-status")
async def get_merge_status(...):
    # Query database
    pass
```

### Phase 5: Frontend Integration (4 hours)

**Assuming**: You already have model list/card UI

**Changes needed**:
1. Add merge status badge
2. Add "Merge Adapters" button (enabled when status='adapter_only')
3. Add merge progress polling
4. "Deploy to Ollama" button (enabled when status='merged')

**Example**:
```typescript
// In ModelCard.tsx
{model.status === 'adapter_only' && (
  <button onClick={() => handleMerge(model.id)}>
    Merge Adapters
  </button>
)}

{model.status === 'merged' && (
  <button onClick={() => handleDeploy(model.id)}>
    Deploy to Ollama
  </button>
)}
```

---

## 🔍 Key Integration Points Summary

### 1. Merge Output Path (CRITICAL!)

**Must save to**: `/workspace/finetuning/{job_id}/output/merged_model`

**Why?**: OllamaDeploymentService checks this path FIRST (line 55)

**Directory structure**:
```
/workspace/finetuning/{job_id}/
├── input/                      # Dataset
├── output/
│   ├── adapter_model/         # ✅ Already saved here (training output)
│   │   ├── adapter_model.safetensors
│   │   ├── adapter_config.json
│   │   └── tokenizer files
│   └── merged_model/          # ← NEW: Save merged model here
│       ├── model.safetensors  # Full weights (~3.2 GB)
│       ├── config.json
│       └── tokenizer files
```

### 2. Database Status Flow

**Current** (training only):
```
status: NULL → training → completed
```

**New** (with merge):
```
status: completed → adapter_only → merging → merged → deploying → deployed
```

**Or reuse existing `status`**:
```
status: NULL → training → completed (adapter_only implied)
       → User triggers merge → merging → merged
       → User triggers deploy → deployed
```

### 3. API Call Flow

```
Frontend: Click "Merge Adapters"
    ↓
POST /api/v1/finetuning/models/{id}/merge
    ↓
Trigger Celery task: merge_lora_model_task
    ↓
ModelMergeService.merge_lora_adapters()
    ↓
Save to /workspace/{job_id}/output/merged_model
    ↓
Update database: status='merged', merged_model_path='...'
    ↓
Frontend: Poll GET /api/v1/finetuning/models/{id}/merge-status
    ↓
Frontend: Enable "Deploy to Ollama" button
    ↓
User clicks "Deploy"
    ↓
POST /api/v1/finetuning/models/{id}/deploy  # ← YOUR EXISTING ENDPOINT!
    ↓
OllamaDeploymentService.deploy_model()
    ↓
Finds merged model in workspace (no MinIO download!)
    ↓
Generates Modelfile
    ↓
Calls Ollama API: POST /api/create
    ↓
Model deployed: status='deployed', ollama_model_name='choles-qa-v1'
```

---

## ⚠️ Critical Considerations

### 1. Workspace Persistence

**Question**: Does `/workspace/finetuning/{job_id}` persist after training?

**From OllamaDeploymentService code** (line 56):
```python
workspace_merged = f"/workspace/finetuning/{job_id}/output/merged_model"
if os.path.exists(workspace_merged):
```

**This suggests**: Workspace DOES persist after training!

**Verification needed**:
```bash
# Check if workspace exists for training36
docker-compose exec finetuning-runtime ls -la /workspace/finetuning/427b1025-57db-45de-826c-3713fc8ecb19/
```

**If workspace does NOT persist**:
- Merge service MUST download adapter from MinIO first
- Then save merged model to MinIO
- OllamaDeploymentService will download from MinIO

### 2. MinIO Paths

**Adapter checkpoint path** (from training):
```
minio://documents/technology/itm11/global/admin/finetuning/datasets/.../checkpoints/{job_name}/{job_id}/final/adapter_model/
```

**Merged model path** (recommended):
```
minio://models/finetuned/{job_id}/merged_model/
```

**Or reuse documents bucket**:
```
minio://documents/technology/itm11/global/admin/finetuning/models/{job_id}/merged_model/
```

### 3. Model Size & Storage

**Per model**:
- Adapter: 8.7 MB
- Merged model: 3.2 GB (for 1.5B models)

**Storage impact**:
- 10 models = 32 GB
- 100 models = 320 GB

**Recommendation**: Implement retention policy (delete old merged models)

---

## 🚀 Quick Start (Recommended Path)

### Day 1: Database + Merge Service

1. Add database columns (Option 1 - minimal):
```sql
ALTER TABLE finetuned_models
ADD COLUMN merged_model_path TEXT,
ADD COLUMN merge_duration_seconds INTEGER;
```

2. Create `ModelMergeService` class

3. Add Celery task

### Day 2: API + Testing

4. Add merge API endpoints to `finetuning_routes.py`

5. Test end-to-end:
   - Trigger merge via API
   - Check workspace for merged model
   - Verify database update

### Day 3: Frontend Integration

6. Add merge button to UI

7. Add status polling

8. Test deployment with merged model

---

## 📚 Files to Modify/Create

### Create (NEW):
- `backend/app/services/finetuning/model_merge_service.py`
- `backend/migrations/02X_add_merge_tracking.sql`

### Modify (EXISTING):
- `backend/app/api/routes/finetuning_routes.py` (add merge endpoints)
- `backend/app/tasks/finetuning_tasks.py` (add Celery task)
- `frontend/src/components/finetuning/ModelCard.tsx` (add merge button)

### No changes needed:
- ✅ `backend/app/services/ollama_deployment_service.py` (already merge-aware!)
- ✅ `backend/app/models/finetuning_models.py` (columns already exist)

---

## ✅ Integration Confidence: HIGH

**Why?**:
1. OllamaDeploymentService already checks for merged models
2. Database schema 80% ready (just add 2 columns)
3. API infrastructure exists (just add 2 endpoints)
4. Workspace optimization already implemented
5. Modelfile generation already prefers merged models

**Estimated Total Time**: ~3 days (21 hours)

**Biggest Unknowns**:
1. Does `/workspace/finetuning/{job_id}` persist after training?
2. What's the current `status` column constraint? (can we reuse it?)

---

## 🔧 Next Steps

1. **Verify workspace persistence**: Check if training workspace survives after completion
2. **Check status column**: Verify if constraint exists or if we can use any values
3. **Choose migration strategy**: Option 1 (minimal) or Option 2 (full)
4. **Implement merge service**: Follow JIRA_FINETUNING_MERGE_ONLY.md spec
5. **Integrate with deployment**: Test end-to-end workflow

---

**Status**: Ready for Implementation
**Risk Level**: LOW (existing infrastructure is merge-aware)
**Recommended Start**: Verify workspace persistence, then begin Day 1 tasks
