# Celery-Worker PEFT Installation Fix

> **Date**: 2025-12-22 13:20 UTC
> **Status**: 🔄 Rebuilding celery-worker image
> **Root Cause Found**: Celery-worker uses separate image name but same Dockerfile

---

## 🎯 Root Cause Analysis

### The Problem:
Training45 auto-merge failed with:
```
[2025-12-22 13:09:25,895: ERROR/ForkPoolWorker-1] ❌ [AUTO-MERGE] Missing dependency: No module named 'peft'
```

Despite:
- ✅ Backend image rebuilt with PEFT
- ✅ Backend services restarted
- ✅ PEFT verified in `backend` container

### Why Auto-Merge Still Failed:

**Docker Architecture Discovery:**
```yaml
# docker-compose.yml

backend:
  build:
    context: ./backend
    dockerfile: Dockerfile
  container_name: rag-backend
  # Image name: chatbot-backend

celery-worker:
  build:
    context: ./backend        # SAME Dockerfile!
    dockerfile: Dockerfile
  container_name: rag-celery-worker
  # Image name: chatbot-celery-worker  ← Different name!
```

**Key Insight:**
- Both services use the SAME Dockerfile (`backend/Dockerfile`)
- But they build into DIFFERENT Docker images:
  - `chatbot-backend` (backend service)
  - `chatbot-celery-worker` (celery-worker service)

**What Happened:**
1. We rebuilt `chatbot-backend` with PEFT ✅
2. We restarted `backend` service → Now has PEFT ✅
3. We restarted `celery-worker` service → BUT still using OLD image ❌
4. Old `chatbot-celery-worker` image doesn't have PEFT!

**Why `docker-compose restart` Didn't Work:**
```bash
docker-compose restart celery-worker
# This restarts the CONTAINER but doesn't rebuild the IMAGE
# Container still uses old chatbot-celery-worker image
```

---

## ✅ The Fix

### Step 1: Rebuild Celery-Worker Image
```bash
docker-compose build celery-worker --no-cache
```

**Expected Duration:** 10-15 minutes (PyTorch download ~900MB)

**Current Progress:**
```
#11 66.25 Downloading torch-2.9.1-cp310-cp310-manylinux_2_28_x86_64.whl (899.8 MB)
```

### Step 2: Restart Celery-Worker with New Image
```bash
docker-compose up -d --force-recreate celery-worker
```

### Step 3: Verify PEFT Installed
```bash
docker-compose exec celery-worker python -c "import peft; print(f'PEFT version: {peft.__version__}')"
```

**Expected Output:**
```
PEFT version: 0.7.1
```

### Step 4: Verify Auto-Merge Can Import
```bash
docker-compose exec celery-worker python -c "
from app.tasks.auto_merge import auto_merge_lora_adapters, should_auto_merge
print('✅ auto_merge imported successfully')
print(f'Auto-merge enabled: {should_auto_merge()}')
"
```

**Expected Output:**
```
✅ auto_merge imported successfully
Auto-merge enabled: True
```

---

## 📊 Build Timeline

| Time | Event | Status |
|------|-------|--------|
| 13:20 | Build started | ✅ |
| 13:21 | Downloading packages | 🔄 |
| 13:25 | Downloading PyTorch (~900MB) | 🔄 |
| 13:30 | Installing PyTorch | ⏳ |
| 13:32 | Installing other packages | ⏳ |
| 13:35 | **Build complete** | ⏳ |

**Expected Completion:** ~13:35 UTC (15 minutes from start)

**Monitor with:**
```bash
tail -f /tmp/celery_worker_rebuild.log
```

---

## 🧪 After Build Completes

### Test Plan:

#### Option 1: Test Existing Training45
```bash
# Manually trigger merge for training45
curl -X POST "http://localhost:8000/api/v1/finetuning/models/8023d31c-b105-4531-9069-751ef6f0d9a4/merge" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "base_model_name": "Qwen/Qwen2.5-1.5B-Instruct",
    "force_cpu": false
  }'
```

#### Option 2: Create Training46 (Test Auto-Merge)
Create new training via UI and verify auto-merge runs automatically after training completes.

---

## 📝 Lessons Learned

### Docker Compose Image Architecture:

**Before Understanding:**
```
backend service → chatbot-backend image
celery-worker service → ??? (assumed same image)
```

**After Understanding:**
```
backend/Dockerfile (ONE Dockerfile)
    ↓
    ├─→ chatbot-backend image (for backend service)
    └─→ chatbot-celery-worker image (for celery-worker service)
```

**Key Takeaway:**
When services use the same Dockerfile but have different service names, docker-compose builds SEPARATE images for each service. You must rebuild BOTH images if you change the Dockerfile.

### Correct Rebuild Process:
```bash
# Wrong (only rebuilds one image):
docker-compose build backend
docker-compose restart backend celery-worker  # celery-worker still old!

# Correct (rebuilds both images):
docker-compose build backend celery-worker
docker-compose up -d --force-recreate backend celery-worker
```

---

## ✅ Success Criteria

### Build Phase:
- [ ] Celery-worker image builds without errors
- [ ] Image size ~16.5GB (same as backend)
- [ ] PEFT, torch, transformers installed

### Verification Phase:
- [ ] `import peft` works in celery-worker container
- [ ] `import torch` works
- [ ] `import transformers` works
- [ ] `auto_merge` module imports without error

### Merge Testing Phase:
- [ ] Manual merge works (training45)
- [ ] Auto-merge works (training46)
- [ ] Model status updates to 'merged'
- [ ] merged_model_path populated

### Deployment Phase:
- [ ] Merged model deploys to Ollama
- [ ] Model appears in chat dropdown
- [ ] Model responds with Choles product knowledge

---

## 🎉 Expected Outcome

After celery-worker rebuild completes:

1. ✅ PEFT available in celery-worker
2. ✅ Auto-merge imports work
3. ✅ Training45 can be merged (manual or retry)
4. ✅ Training46 auto-merges automatically
5. ✅ Full automation achieved! 🚀

---

**Build started:** 13:20 UTC
**Expected completion:** 13:35 UTC
**Monitor:** `tail -f /tmp/celery_worker_rebuild.log`

---

**End of Document**
