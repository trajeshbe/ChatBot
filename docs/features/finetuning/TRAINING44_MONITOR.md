# Training44 - Complete Monitoring Guide

> **Job ID**: b6f9fb11-08d5-4702-b98c-582c98af6a80
> **Name**: choles-qa-real-training44
> **Status**: Running ✅
> **Created**: 2025-12-22 11:36:09 UTC
> **Container**: finetuning-b6f9fb11-08d5-4702-b98c-582c98af6a80
> **Fix Applied**: Lazy imports in auto_merge.py ✅

---

## 🎯 What's Different in Training44

### Previous Training (training43):
```
✅ Training started
✅ Container loaded model
✅ Training completed
✅ Adapters saved
✅ Model registered
❌ FAILED: ModuleNotFoundError: No module named 'peft'
   - Error when celery imported auto_merge.py
   - Module-level PEFT import failed
```

### Current Training (training44):
```
✅ Training started
✅ Container loaded model
✅ No celery PEFT import errors! (lazy imports working)
⏳ Training in progress...
⏳ Expected: Training completes → Container merge → Model registered → Auto-merge
```

---

## 📊 Real-Time Monitoring

### Command 1: Database Status (Run every 2-3 mins)
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT
  name,
  status,
  progress,
  current_epoch,
  train_loss,
  eval_loss,
  error_message
FROM finetuning_jobs
WHERE id = 'b6f9fb11-08d5-4702-b98c-582c98af6a80';"
```

**Expected Progression:**
```
Time    | Progress | Epoch | Train Loss | Status
--------|----------|-------|------------|--------
+0min   |    0     |       |            | running (loading model)
+5min   |    0     |   1   |            | running (epoch 1 started)
+8min   |   33.3   |   1   |   1.234    | running
+11min  |   66.6   |   2   |   0.856    | running
+14min  |  100.0   |   3   |   0.432    | running
+16min  |  100.0   |   3   |   0.432    | completed ✅
```

### Command 2: Container Logs (Live)
```bash
# Get container ID
CONTAINER_ID=$(docker ps | grep b6f9fb11 | awk '{print $1}')

# Follow logs
docker logs -f $CONTAINER_ID
```

**What to Look For:**
```
✅ Loading tokenizer...
✅ Loading model Qwen/Qwen2.5-1.5B-Instruct...
✅ Preparing model for k-bit training...
✅ Configuring LoRA...
✅ Loaded X training samples
✅ Starting REAL training (NOT mock)...
⏳ [Training progress bars...]
✅ Training completed!
✅ Saving trained adapter weights...
✅ Adapter saved to .../adapter_model
🔄 Merging trained adapters into base model...  ← CRITICAL
✅ Merged model saved to .../merged_model      ← SUCCESS!
```

### Command 3: Celery Logs (Watch for auto-merge)
```bash
docker-compose logs -f celery-worker | grep -i "training44\|auto-merge\|error"
```

**Expected Flow:**
```
[INFO] Job b6f9fb11-...: choles-qa-real-training44 - Method: peft
[INFO] 🐳 Creating GPU container...
[INFO] ✅ GPU container started
⏳ [Wait for training...]
[INFO] 📦 Model registered with ID: xxx
[INFO] 🔄 Starting auto-merge for model xxx       ← If auto-merge runs
[INFO] ✅ [AUTO-MERGE] Merge completed in XX.Xs   ← If auto-merge runs
[INFO] ✅ Model status updated to 'merged'         ← SUCCESS!
```

### Command 4: Check Model Registration
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT
  name,
  status,
  merged_model_path,
  merge_duration_seconds,
  created_at
FROM finetuned_models
WHERE name LIKE '%training44%'
ORDER BY created_at DESC;"
```

**Expected:**
```
Before Registration: (no rows)
After Registration:  status='registered', merged_model_path=NULL
After Auto-Merge:    status='merged', merged_model_path=/workspace/.../merged_model
```

---

## 🐛 Debugging Commands

### Check Container Merge Success:
```bash
CONTAINER_ID=$(docker ps -a | grep b6f9fb11 | awk '{print $1}')

# Check for merge logs
docker logs $CONTAINER_ID | grep -i "merge"

# Should show:
# 🔄 Merging trained adapters into base model...
# ✅ Merged model saved to /workspace/.../merged_model
```

### Check for Import Errors:
```bash
docker-compose logs celery-worker | grep -i "peft\|modulenotfound"

# Should be EMPTY (no PEFT errors!)
```

### Check Auto-Merge Triggered:
```bash
docker-compose logs celery-worker | grep -i "auto-merge"

# If auto-merge runs:
# 🔄 Starting auto-merge for model xxx
# ✅ [AUTO-MERGE] Merge completed
```

### Check Job Error:
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT error_message
FROM finetuning_jobs
WHERE id = 'b6f9fb11-08d5-4702-b98c-582c98af6a80';"
```

---

## ⏱️ Timeline

| Time | Event | Status Check |
|------|-------|--------------|
| T+0 | Training started | Container created, loading model |
| T+2min | Model loaded | Logs show "Loading model..." |
| T+5min | Epoch 1 starts | progress=0, current_epoch=1 |
| T+8min | Epoch 1 done | progress=33.3 |
| T+11min | Epoch 2 done | progress=66.6 |
| T+14min | Epoch 3 done | progress=100, status=completed |
| T+16min | Container merge | Logs show "Merging adapters..." |
| T+17min | Model registered | finetuned_models table updated |
| T+17min | Auto-merge check | Celery checks should_auto_merge() |
| T+19min | Auto-merge complete | status='merged' ✅ |
| T+20min | **DONE** | Ready for deployment! |

**Total Expected Time:** ~20 minutes

---

## ✅ Success Criteria

### Training Phase:
- [x] Container starts
- [x] Model loads (no OOM errors)
- [ ] Training progresses (epochs 1/3 → 2/3 → 3/3)
- [ ] Database updates (progress, train_loss)
- [ ] Training completes (status='completed')

### Container Merge Phase:
- [ ] Container merge starts
- [ ] No `AutoModelForCausalLM` import error (we fixed this!)
- [ ] Merged model saved to `/workspace/.../merged_model`
- [ ] Container reports success back to celery

### Registration Phase:
- [ ] Model registered in `finetuned_models` table
- [ ] `adapter_path` populated
- [ ] `checkpoint_path` populated
- [ ] Initial status='registered'

### Auto-Merge Phase (NEW):
- [ ] Celery sees model registration
- [ ] No PEFT import error (we fixed this!)
- [ ] `should_auto_merge()` returns True
- [ ] `auto_merge_lora_adapters()` runs (or skipped if container already merged)
- [ ] Model status updated to 'merged'

### Deployment Ready:
- [ ] Model appears in Governance & Audit UI
- [ ] Status badge shows "Merged" (green)
- [ ] "Deploy to Ollama" button clickable
- [ ] Deployment succeeds (~2 mins)
- [ ] Model in chat dropdown
- [ ] Model responds with domain knowledge

---

## 🔍 Key Files to Monitor

### Container Files (Inside training container):
```
/workspace/finetuning/b6f9fb11-08d5-4702-b98c-582c98af6a80/
├── input/
│   └── train.json                    # Dataset
├── output/
│   ├── adapter_model/                # LoRA adapters ✅
│   │   ├── adapter_config.json
│   │   └── adapter_model.safetensors
│   ├── merged_model/                 # Merged model ✅
│   │   ├── config.json
│   │   ├── model.safetensors
│   │   └── tokenizer files
│   └── result.json                   # Training result
└── logs/
    └── metrics.jsonl                 # Training metrics
```

### Database Tables:
```sql
-- Training job
SELECT * FROM finetuning_jobs WHERE id = 'b6f9fb11-08d5-4702-b98c-582c98af6a80';

-- Registered model
SELECT * FROM finetuned_models WHERE job_id = 'b6f9fb11-08d5-4702-b98c-582c98af6a80';

-- Training stages
SELECT * FROM training_pipeline_stages WHERE finetuning_jobs_id = 'b6f9fb11-08d5-4702-b98c-582c98af6a80';
```

---

## 🎬 What Happens Next

### If Training44 Succeeds:
1. ✅ Training completes
2. ✅ Container merge works (AutoModelForCausalLM fix)
3. ✅ Model registered
4. ✅ Auto-merge runs (no PEFT import error)
5. ✅ Model status='merged'
6. ✅ Ready to deploy!

### If Container Merge Fails:
- Check logs for `AutoModelForCausalLM` error
- We already fixed this (line 373 in peft_trainer.py)
- But maybe image needs rebuild?

### If Auto-Merge Fails:
- Check celery logs for PEFT errors
- We fixed lazy imports
- Should work now!

### If Database Not Updating:
- Check container can write to PostgreSQL
- Check network connectivity
- Check result.json gets created

---

## 📝 Notes

**Job Details:**
- Base Model: Qwen/Qwen2.5-1.5B-Instruct
- Dataset: company_qa_dataset (Choles products)
- Method: PEFT (LoRA)
- Epochs: 3
- Batch Size: 4
- Quantization: 4-bit (QLoRA)

**Fixes Applied:**
1. ✅ `auto_merge.py`: Lazy imports (no module-level PEFT)
2. ✅ `peft_trainer.py`: AutoModelForCausalLM import (line 373)
3. ✅ `docker-compose.yml`: FINETUNING_AUTO_MERGE env var
4. ✅ `.env`: FINETUNING_AUTO_MERGE=true

**What We're Testing:**
- Does training complete? (YES for training43)
- Does container merge work? (UNKNOWN - training43 died before this)
- Does model register? (YES for training43)
- Does celery import auto_merge without error? (YES - tested)
- Does auto-merge actually run? (UNKNOWN - waiting for completion)

---

## 🎉 Expected Outcome

If training44 completes successfully:

✅ **Training works**
✅ **Container merge works**
✅ **Model registration works**
✅ **Celery import works** (no PEFT error)
✅ **Auto-merge works** (lazy imports)
✅ **Database updates correctly**
✅ **Model ready to deploy**

**No manual clicking needed!** 🚀

---

**Keep this document open and run the monitoring commands every 2-3 minutes!**

---

**End of Monitor Guide**
