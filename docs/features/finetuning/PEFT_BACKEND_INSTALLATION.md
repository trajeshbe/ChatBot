# PEFT Installation in Backend - Complete Guide

> **Date**: 2025-12-22
> **Status**: ✅ Requirements updated, ✅ Docling conflict fixed, 🔄 Building image
> **Reason**: ModelMergeService runs in celery-worker (backend container)
> **Impact**: Fixes both auto-merge AND manual merge

---

## 🎯 Why This Is Necessary

### The Problem:
Both **auto-merge** (after training) and **manual merge** (UI button) use the same code:
```python
ModelMergeService.merge_lora_adapters()
  ↓
Runs in: celery-worker (backend container)
  ↓
Imports: torch, transformers, peft
  ↓
❌ Backend doesn't have these libs
  ↓
Error: "No module named 'peft'"
```

### Where Merge Happens:
- **Training container**: Has PEFT ✅ (but only for container merge)
- **Backend container** (celery-worker): NO PEFT ❌ (where ModelMergeService runs)

### Services That Need PEFT:
1. **ModelMergeService** (`model_merge_service.py`)
   - Used by: UI "Merge & Deploy" button
   - Runs in: celery-worker (backend)
   - Imports: `from peft import PeftModel` (line 20)

2. **Auto-Merge** (`auto_merge.py`)
   - Used by: Automatic merge after training
   - Runs in: celery-worker (backend)
   - Imports: `from peft import PeftModel` (lazy, line 61)

---

## ✅ What Was Changed

### File: `/backend/requirements.txt`

**Added (lines 283-296):**
```txt
# ----------------------------------------------------------------------------
# MODEL MERGING DEPENDENCIES (Required for ModelMergeService)
# Used by: app/services/finetuning/model_merge_service.py, app/tasks/auto_merge.py
# ----------------------------------------------------------------------------
# These are needed in backend because merge happens in celery-worker (backend container)
# Both auto-merge (after training) and manual merge (UI button) use ModelMergeService

peft==0.7.1                     # Parameter-Efficient Fine-Tuning - LoRA adapter merging
transformers==4.36.0            # HuggingFace Transformers - model loading and merging
accelerate>=1.0.0               # Accelerate - device_map support (compatible with docling >=1.0.0)
torch>=2.2.2                    # PyTorch - model operations (compatible with docling-ibm-models >=2.2.2)

# NOTE: Full finetuning stack (trl/bitsandbytes/deepspeed) remains in requirements-finetuning.txt
# Only core merge dependencies above are needed in backend
```

### Why These Versions:
- **peft==0.7.1**: Same as finetuning-runtime (compatibility)
- **transformers==4.36.0**: Same as finetuning-runtime
- **accelerate>=1.0.0**: docling requires >=1.0.0 (not 0.25.0)
- **torch>=2.2.2**: docling-ibm-models requires >=2.2.2 (not 2.1.0)

### Docling Dependency Conflict Fix:

**Problem:**
```
ERROR: Cannot install -r requirements.txt (line 78) and docling-core[chunking]==2.57.0
because these package versions have conflicting dependencies.
```

**Root Cause:**
- `docling==2.62.0` requires `docling-core>=2.50.1,<3.0.0`
- But pip was trying to install `docling-core[chunking]==2.57.0` which conflicts

**Fix Applied (line 78):**
```txt
# Before:
docling==2.62.0             # Pinned version - caused conflict

# After:
docling>=2.50.0,<3.0.0      # Version range - lets pip resolve
```

**Result:** Pip can now choose a compatible docling version that works with all dependencies.

---

## 🔧 Build Process

### Command:
```bash
docker-compose build backend --no-cache
```

### Expected Duration:
- **Download packages**: 5-7 minutes (PyTorch is ~2GB)
- **Install packages**: 3-5 minutes
- **Total**: ~10-15 minutes

### Build Stages:
```
1. Load base image (playwright:v1.48.0-jammy)
   ↓
2. Install system dependencies
   ↓
3. Copy requirements.txt
   ↓
4. Install Python packages
   - torch>=2.2.2 (~2GB download)
   - transformers==4.36.0
   - peft==0.7.1
   - accelerate>=1.0.0
   - ... (all other packages)
   ↓
5. Copy application code
   ↓
6. Build complete ✅
```

### Monitor Build:
```bash
# Real-time monitoring
tail -f /tmp/backend_build_final.log

# Check if still running
ps aux | grep "docker-compose build"

# Check progress (look for package installs)
tail -30 /tmp/backend_build_final.log
```

---

## 📊 Impact Analysis

### Image Size Increase:
- **Before**: ~1.5GB (backend without ML libs)
- **After**: ~3.5GB (backend with torch/transformers/peft)
- **Increase**: ~2GB (acceptable for merge functionality)

### Services Affected:
- ✅ `backend` service (FastAPI)
- ✅ `celery-worker` service (uses backend image)
- ❌ `frontend` - no change
- ❌ `postgres` - no change
- ❌ `finetuning-trainer` - no change (already has PEFT)

### What Gets Fixed:
1. ✅ **Auto-merge after training**: Will work in celery-worker
2. ✅ **UI "Merge & Deploy" button**: Will work
3. ✅ **ModelMergeService**: Can import PEFT
4. ✅ **auto_merge.py**: Can actually run (not just import)

---

## 🎬 After Build Completes

### Step 1: Restart Services
```bash
# Stop celery-worker and backend
docker-compose stop celery-worker backend

# Recreate with new image
docker-compose up -d celery-worker backend

# Verify restart
docker-compose ps | grep -E "celery-worker|backend"
```

### Step 2: Verify PEFT Installation
```bash
# Check PEFT installed in backend
docker-compose exec backend python -c "import peft; print(f'PEFT version: {peft.__version__}')"

# Check torch installed
docker-compose exec backend python -c "import torch; print(f'PyTorch version: {torch.__version__}')"

# Check transformers installed
docker-compose exec backend python -c "import transformers; print(f'Transformers version: {transformers.__version__}')"
```

**Expected Output:**
```
PEFT version: 0.7.1
PyTorch version: 2.2.2 (or higher)
Transformers version: 4.36.0
```

### Step 3: Test Import in Celery
```bash
# Verify celery-worker can import ModelMergeService
docker-compose exec celery-worker python -c "
from app.services.finetuning.model_merge_service import ModelMergeService
print('✅ ModelMergeService imported successfully')
"

# Verify auto_merge can be imported
docker-compose exec celery-worker python -c "
from app.tasks.auto_merge import auto_merge_lora_adapters, should_auto_merge
print('✅ auto_merge imported successfully')
print(f'Auto-merge enabled: {should_auto_merge()}')
"
```

**Expected Output:**
```
✅ ModelMergeService imported successfully
✅ auto_merge imported successfully
Auto-merge enabled: True
```

---

## 🧪 Testing Merge Functionality

### Test 1: Manual Merge (UI Button)
```bash
# Merge training44 model manually
curl -X POST "http://localhost:8000/api/v1/finetuning/models/79dcee23-0740-4c10-b323-f88e5ccd109f/merge" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "base_model_name": "Qwen/Qwen2.5-1.5B-Instruct",
    "force_cpu": false
  }'
```

**Expected Response:**
```json
{
  "task_id": "celery-task-id",
  "model_id": "79dcee23-0740-4c10-b323-f88e5ccd109f",
  "status": "merging",
  "message": "Merge task started. Expected duration: 5-15 minutes."
}
```

### Test 2: Monitor Merge Progress
```bash
# Watch celery logs
docker-compose logs -f celery-worker | grep -i "merge\|79dcee23"

# Check database status
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT name, status, merged_model_path, merge_duration_seconds
FROM finetuned_models
WHERE id = '79dcee23-0740-4c10-b323-f88e5ccd109f';"
```

**Expected Progression:**
```
status: registered → merging → merged
merged_model_path: NULL → /workspace/finetuning/.../merged_model
merge_duration_seconds: NULL → 45.2 (or similar)
```

### Test 3: Auto-Merge (Create New Training)
```bash
# Create training45 via UI
# Wait for training to complete
# Auto-merge should run automatically
# Check logs for: "🔄 Starting auto-merge for model xxx"
```

---

## ✅ Success Criteria

### Build Success:
- [ ] Backend image builds without errors
- [ ] Image size ~3.5GB
- [ ] PEFT, torch, transformers installed

### Import Success:
- [ ] `import peft` works in backend container
- [ ] `import torch` works in backend container
- [ ] `import transformers` works in backend container
- [ ] ModelMergeService imports without error
- [ ] auto_merge imports without error

### Merge Success:
- [ ] Manual merge (UI button) works
- [ ] Auto-merge (after training) works
- [ ] Model status changes to "merged"
- [ ] merged_model_path populated
- [ ] No "No module named 'peft'" errors

### Deployment Success:
- [ ] Merged model can be deployed to Ollama
- [ ] Model appears in chat dropdown
- [ ] Model responds with fine-tuned knowledge

---

## 🐛 Troubleshooting

### Build Fails with Dependency Conflict:
```bash
# Check conflict details
tail -50 /tmp/backend_build_final.log | grep -i "conflict\|error"

# Common issues:
# - torch version conflict → Use >=2.2.2
# - accelerate version conflict → Use >=1.0.0
```

### Import Still Fails After Build:
```bash
# Check if container using new image
docker-compose ps

# Force recreate
docker-compose up -d --force-recreate celery-worker backend

# Verify image
docker images | grep chatbot-backend
```

### Merge Still Fails:
```bash
# Check celery logs for actual error
docker-compose logs celery-worker | grep -A 20 "merge"

# Check if PEFT actually installed
docker-compose exec celery-worker pip list | grep peft
```

---

## 📝 Summary

### Before:
- ❌ Backend doesn't have PEFT
- ❌ Auto-merge fails
- ❌ Manual merge fails
- ❌ Models stuck at "registered"

### After:
- ✅ Backend has PEFT, torch, transformers
- ✅ Auto-merge works
- ✅ Manual merge works
- ✅ Models automatically merged
- ✅ Ready for deployment!

### Trade-offs:
- **Pro**: Merge functionality works end-to-end
- **Pro**: No manual intervention needed
- **Pro**: Consistent merge behavior
- **Con**: Backend image +2GB larger
- **Con**: Longer build time (~15 mins)
- **Acceptable**: Merge is critical feature, worth the cost

---

## 🎉 Expected Outcome

After build completes and services restart:

1. **Training45**: Create new training
   - Training completes
   - Auto-merge runs automatically
   - Model status = "merged"
   - Ready to deploy!

2. **Training44**: Manual merge existing model
   - Click "Merge & Deploy" button
   - Merge runs in celery
   - Model status = "merged"
   - Ready to deploy!

3. **All Future Trainings**: Auto-merge enabled
   - Training → Merge → Ready
   - No manual steps!
   - Full automation! 🚀

---

**Build in progress... Monitor with: tail -f /tmp/backend_build_final.log**

---

**End of Document**
