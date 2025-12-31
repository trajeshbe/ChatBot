# Training46 - Monitoring Guide (Auto-Merge Test)

> **Job ID**: 17cbc1f7-935c-4ca9-8b90-cd3dc7b98fd9
> **Name**: choles-qa-real-training46
> **Status**: Running (Loading Model)
> **Created**: 2025-12-22 13:37:36 UTC
> **Container**: b17236c54125
> **Purpose**: Test auto-merge with PEFT-enabled celery-worker

---

## 🎯 What's Different in Training46

### Context:
This is the **FIRST training after fixing celery-worker PEFT installation**!

### Previous Training (training45):
```
✅ Training completed
✅ Model registered
❌ Auto-merge FAILED: No module named 'peft' (celery-worker didn't have PEFT)
```

### Current Training (training46):
```
✅ Celery-worker rebuilt with PEFT
✅ Training started
⏳ Loading model... (currently at this stage)
⏳ Expected: Training → Merge → Auto-merge (NEW!) → Status='merged'
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
WHERE id = '17cbc1f7-935c-4ca9-8b90-cd3dc7b98fd9';"
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
CONTAINER_ID=b17236c54125

# Follow logs
docker logs -f $CONTAINER_ID
```

**What to Look For:**
```
✅ Loading tokenizer...
✅ Loading model Qwen/Qwen2.5-1.5B-Instruct...
✅ Preparing model for k-bit training...
✅ Configuring LoRA...
✅ Loaded 9 training samples
✅ Starting REAL training (NOT mock)...
⏳ [Training progress bars...]
✅ Training completed!
✅ Saving trained adapter weights...
✅ Adapter saved to .../adapter_model
🔄 Merging trained adapters into base model...  ← Container merge
✅ Merged model saved to .../merged_model      ← SUCCESS!
```

### Command 3: Celery Logs (Watch for auto-merge) **← CRITICAL!**
```bash
docker-compose logs -f celery-worker | grep -i "training46\|auto-merge\|peft\|error"
```

**Expected Flow (NEW - with PEFT working):**
```
[INFO] Job 17cbc1f7-...: choles-qa-real-training46 - Method: peft
[INFO] 🐳 Creating GPU container...
[INFO] ✅ GPU container started
⏳ [Wait for training...]
[INFO] 📦 Model registered with ID: xxx
[INFO] 🔄 Starting auto-merge for model xxx       ← NEW! Should work now!
[INFO] ✅ [AUTO-MERGE] Merge completed in XX.Xs   ← SUCCESS!
[INFO] ✅ Model status updated to 'merged'         ← FINAL!
```

**What We're Testing:**
- Does celery-worker now have PEFT? ✅ **YES** (verified earlier)
- Can auto_merge import without error? ✅ **YES** (verified earlier)
- Will auto-merge actually RUN after training? ⏳ **Testing now**
- Will model status update to 'merged'? ⏳ **Testing now**

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
WHERE name LIKE '%training46%'
ORDER BY created_at DESC;"
```

**Expected:**
```
Before Training Completes: (no rows)
After Training/Container Merge: status='registered', merged_model_path=NULL
After Auto-Merge (NEW!):  status='merged', merged_model_path=/workspace/.../merged_model ✅
```

---

## 🐛 Debugging Commands

### Check Container Still Running:
```bash
docker ps | grep b17236c54125
# Should show "Up X minutes"
```

### Check for PEFT Errors in Celery:
```bash
docker-compose logs celery-worker | grep -i "peft\|modulenotfound"
# Should be EMPTY (no PEFT errors!)
```

### Check Training Progress:
```bash
docker logs b17236c54125 | tail -50
# Look for epoch progress, loss values
```

### Check GPU Usage:
```bash
docker exec b17236c54125 nvidia-smi
# Should show GPU utilization
```

---

## ⏱️ Timeline

| Time | Event | Status Check |
|------|-------|--------------|
| 13:37 | Training started | Container created, loading model |
| 13:38 | Model loading | Logs show "Loading model..." |
| 13:42 | Model loaded | progress=0, current_epoch=1 |
| 13:45 | Epoch 1 starts | Training progress |
| 13:48 | Epoch 1 done | progress=33.3 |
| 13:51 | Epoch 2 done | progress=66.6 |
| 13:54 | Epoch 3 done | progress=100, status=completed |
| 13:56 | Container merge | Logs show "Merging adapters..." |
| 13:57 | Model registered | finetuned_models table updated |
| 13:57 | **Auto-merge check** | Celery checks should_auto_merge() |
| 13:59 | **Auto-merge runs** | ✅ NEW! Should work now! |
| 14:00 | **DONE** | status='merged' ✅ |

**Total Expected Time:** ~23 minutes (similar to training44/45)

---

## ✅ Success Criteria

### Training Phase:
- [x] Container starts
- [x] Model loading in progress
- [ ] Training progresses (epochs 1/3 → 2/3 → 3/3)
- [ ] Database updates (progress, train_loss)
- [ ] Training completes (status='completed')

### Container Merge Phase:
- [ ] Container merge starts
- [ ] Merged model saved to `/workspace/.../merged_model`
- [ ] Container reports success back to celery

### Registration Phase:
- [ ] Model registered in `finetuned_models` table
- [ ] `adapter_path` populated
- [ ] `checkpoint_path` populated
- [ ] Initial status='registered'

### Auto-Merge Phase (THE BIG TEST!) **← NEW!**:
- [ ] Celery sees model registration
- [ ] **No PEFT import error** (we fixed this!)
- [ ] `should_auto_merge()` returns True
- [ ] `auto_merge_lora_adapters()` runs successfully
- [ ] Model status updated to 'merged'
- [ ] `merged_model_path` populated
- [ ] No "No module named 'peft'" error ✅

### Deployment Ready:
- [ ] Model appears in Governance & Audit UI
- [ ] Status badge shows "Merged" (green)
- [ ] "Deploy to Ollama" button clickable
- [ ] Deployment succeeds (~2 mins)
- [ ] Model in chat dropdown
- [ ] Model responds with domain knowledge

---

## 🔍 Key Differences from Training45

| Aspect | Training45 | Training46 (This) |
|--------|-----------|-------------------|
| **Celery-worker image** | Old (no PEFT) | New (PEFT ✅) |
| **PEFT installed** | ❌ No | ✅ Yes (0.7.1) |
| **auto_merge imports** | ❌ Failed | ✅ Works |
| **Auto-merge runs** | ❌ Failed | ⏳ Testing now |
| **Expected result** | status='registered' | status='merged' ✅ |

---

## 🎬 What Happens Next

### If Training46 Succeeds (Expected):
1. ✅ Training completes
2. ✅ Container merge works
3. ✅ Model registered
4. ✅ **Auto-merge runs** (no PEFT error!)
5. ✅ Model status='merged'
6. ✅ **FULL AUTOMATION ACHIEVED!** 🚀

### If Auto-Merge Still Fails:
- Check celery logs for actual error
- Verify PEFT still available in celery-worker
- Check if auto_merge function has other issues

### If Training Fails:
- Check container logs for training errors
- Verify GPU availability
- Check dataset format

---

## 📝 Notes

**Job Details:**
- Base Model: Qwen/Qwen2.5-1.5B-Instruct
- Dataset: company_qa_dataset (Choles products)
- Method: PEFT (LoRA)
- Epochs: 3
- Batch Size: 4
- Quantization: 4-bit (QLoRA)

**Fixes Applied Before This Training:**
1. ✅ `auto_merge.py`: Lazy imports (no module-level PEFT)
2. ✅ `peft_trainer.py`: AutoModelForCausalLM import
3. ✅ `docker-compose.yml`: FINETUNING_AUTO_MERGE env var
4. ✅ `.env`: FINETUNING_AUTO_MERGE=true
5. ✅ **`backend/requirements.txt`: Added PEFT, torch, transformers**
6. ✅ **Rebuilt backend image with PEFT**
7. ✅ **Rebuilt celery-worker image with PEFT** ← KEY FIX!

**What We're Testing:**
- Complete end-to-end fine-tuning workflow
- Auto-merge functionality with PEFT-enabled celery-worker
- No manual intervention required

---

## 🎉 Expected Outcome

If training46 completes successfully with auto-merge:

✅ **Training works**
✅ **Container merge works**
✅ **Model registration works**
✅ **Celery imports work** (no PEFT error)
✅ **Auto-merge works** (PEFT available!)
✅ **Database updates correctly**
✅ **Model ready to deploy**
✅ **FULL AUTOMATION** 🚀

**No manual clicking needed!**

---

**Keep this document open and run the monitoring commands every 2-3 minutes!**

---

**Current Status:** Loading model (step 1/8)
**Next Checkpoint:** Epoch 1 starts (~5 mins from start)
**Monitor with:** `docker logs -f b17236c54125`

---

**End of Monitor Guide**
