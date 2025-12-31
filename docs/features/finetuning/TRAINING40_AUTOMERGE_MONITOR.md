# Training40 - Auto-Merge Monitoring Guide

> **Training Job**: choles-qa-real-training40
> **Job ID**: 27df16d1-ac85-47ac-84d8-95742fd1d9dc
> **Status**: Running (will auto-merge when complete!)
> **Date**: 2025-12-22

---

## 🎯 What to Expect

### Training Flow:
```
1. Training starts (status: "running")
   ↓
2. Training in progress (10-30 mins)
   - Epochs: 1/3, 2/3, 3/3
   - Loss decreasing
   ↓
3. Training completes (status: "completed")
   ↓
4. Model registered (status: "registered")
   ↓
5. 🆕 AUTO-MERGE starts (2-5 mins)
   ↓
6. Model status updated to "merged" ✅
```

---

## 📊 Monitor Training Progress

### Command 1: Check Job Status
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT
  name,
  status,
  progress,
  current_epoch,
  train_loss,
  eval_loss
FROM finetuning_jobs
WHERE name = 'choles-qa-real-training40';"
```

**Run every 2-3 minutes** to see progress

### Command 2: Watch Live Logs
```bash
docker-compose logs -f celery-worker | grep -i "training40\|auto-merge"
```

**This will show**:
- Training progress
- Auto-merge start
- Auto-merge completion

### Command 3: Check Model Status
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT
  name,
  status,
  merged_model_path,
  merge_duration_seconds
FROM finetuned_models
WHERE name LIKE '%training40%'
ORDER BY created_at DESC;"
```

**Expected progression**:
- First: No rows (not registered yet)
- Then: status="registered", merged_model_path=NULL
- Finally: status="merged", merged_model_path=/workspace/... ✅

---

## 🔍 What Auto-Merge Logs Look Like

### When Training Completes:
```
✅ Training completed
📦 Model registered with ID: abc-123-def
```

### Auto-Merge Starts:
```
🔄 Starting auto-merge for model abc-123-def
🔄 [AUTO-MERGE] Starting auto-merge for job 27df16d1-ac85-47ac-84d8-95742fd1d9dc
   Base model: Qwen/Qwen2.5-1.5B-Instruct
   Adapter path: /workspace/finetuning/27df16d1.../output/final
```

### During Merge:
```
📁 [AUTO-MERGE] Merge output: /workspace/.../merged_model
📦 [AUTO-MERGE] Loading base model: Qwen/Qwen2.5-1.5B-Instruct
🎮 [AUTO-MERGE] Using GPU: NVIDIA GeForce RTX 3090
📝 [AUTO-MERGE] Loading tokenizer
🔗 [AUTO-MERGE] Loading LoRA adapters from: /workspace/.../final
⚙️  [AUTO-MERGE] Merging adapters with base model...
💾 [AUTO-MERGE] Saving merged model to: /workspace/.../merged_model
```

### Merge Complete:
```
✅ [AUTO-MERGE] Merge completed successfully in 45.2 seconds
📍 [AUTO-MERGE] Merged model path: /workspace/finetuning/27df16d1.../output/merged_model
🧹 [AUTO-MERGE] GPU memory cleared
✅ Model status updated to 'merged' (ready for deployment)
```

---

## ⏱️ Timeline Estimates

| Phase | Duration | Status Check |
|-------|----------|--------------|
| Training | 10-30 mins | `status="running"`, progress 0-100% |
| Model Registration | 10 seconds | `status="registered"` |
| **Auto-Merge** | 2-5 mins GPU | Watch for AUTO-MERGE logs |
| Status Update | 1 second | `status="merged"` ✅ |
| **Total** | 12-35 mins | Ready for deployment! |

---

## 🎬 Step-by-Step Monitoring

### Step 1: Wait for Training to Complete (10-30 mins)

**Run every 3 minutes**:
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT progress, current_epoch, train_loss, status
FROM finetuning_jobs
WHERE id = '27df16d1-ac85-47ac-84d8-95742fd1d9dc';"
```

**Expected output**:
```
progress | current_epoch | train_loss | status
---------+---------------+------------+---------
  33.3   |       1       |   1.234    | running
  66.6   |       2       |   0.856    | running
 100.0   |       3       |   0.432    | completed ✅
```

### Step 2: Watch for Auto-Merge (2-5 mins after training completes)

**Run**:
```bash
docker-compose logs --tail 100 celery-worker | grep "AUTO-MERGE"
```

**Expected to see**:
- "Starting auto-merge"
- "Loading base model"
- "Merging adapters"
- "Merge completed successfully"

### Step 3: Verify Model Status Changed to "Merged"

**Run**:
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT name, status, merged_model_path
FROM finetuned_models
WHERE name LIKE '%training40%';"
```

**Expected output**:
```
name                         | status | merged_model_path
-----------------------------+--------+-------------------
choles-qa-real-training40... | merged | /workspace/finetuning/.../merged_model ✅
```

### Step 4: Deploy to Ollama

Once status="merged":

1. Go to: http://localhost:3001/admin
2. Navigate: **Fine-Tuning Hub** → **Governance & Audit**
3. Find: **choles-qa-real-training40_model**
4. Status badge should show: **"Merged"** (green) ✅
5. Click: **"Deploy to Ollama"**
6. Wait: ~2 minutes
7. Success!

---

## 🧪 Quick Status Checks

### Is Training Done?
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT status FROM finetuning_jobs
WHERE id = '27df16d1-ac85-47ac-84d8-95742fd1d9dc';" | grep completed
```
If returns "completed" → Training is done!

### Did Auto-Merge Run?
```bash
docker-compose logs celery-worker | grep "AUTO-MERGE.*training40" | head -1
```
If shows "Starting auto-merge" → Yes!

### Is Model Merged?
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT status FROM finetuned_models
WHERE name LIKE '%training40%';" | grep merged
```
If returns "merged" → Ready to deploy!

---

## 📈 TensorBoard (Training Metrics)

View real-time training loss:
```
http://localhost:6006/#timeseries&runFilter=27df16d1-ac85-47ac-84d8-95742fd1d9dc
```

**What to look for**:
- Training loss decreasing
- Eval loss stable or decreasing
- No spikes (indicates good learning)

---

## 🐛 Troubleshooting

### Issue 1: Auto-Merge Didn't Run

**Check env var**:
```bash
docker-compose exec celery-worker printenv | grep FINETUNING_AUTO_MERGE
```

**Should show**: `FINETUNING_AUTO_MERGE=true`

**If not**:
```bash
echo "FINETUNING_AUTO_MERGE=true" >> .env
docker-compose restart celery-worker
```

### Issue 2: Training Failed

**Check logs**:
```bash
docker-compose logs celery-worker | grep "training40" | grep -i "error\|failed"
```

**Check job error**:
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT error_message
FROM finetuning_jobs
WHERE id = '27df16d1-ac85-47ac-84d8-95742fd1d9dc';"
```

### Issue 3: Model Status Stuck at "registered"

**Check if merge failed**:
```bash
docker-compose logs celery-worker | grep "AUTO-MERGE.*failed\|WARNING.*merge"
```

**Manual retry**: Wait for next training (auto-merge should work)

---

## ✅ Success Checklist

- [ ] Training completes (status="completed")
- [ ] Model registered
- [ ] Auto-merge logs appear
- [ ] Auto-merge completes successfully
- [ ] Model status changes to "merged"
- [ ] Model appears in Governance & Audit with "Merged" badge
- [ ] Can click "Deploy to Ollama"
- [ ] Model deploys successfully
- [ ] Can test in chat

---

## 🎉 What This Proves

If training40 auto-merges successfully:

✅ **Auto-merge feature works!**
✅ **No manual clicking needed!**
✅ **PEFT is installed correctly**
✅ **Persistent across restarts** (config in .env)
✅ **Ready for production use!**

---

## 📝 Notes

**Job ID**: 27df16d1-ac85-47ac-84d8-95742fd1d9dc
**Training Dataset**: company_qa_dataset.jsonl (Choles products)
**Base Model**: Qwen/Qwen2.5-1.5B-Instruct
**Expected Duration**: 12-35 minutes total
**Auto-Merge**: Enabled (FINETUNING_AUTO_MERGE=true)

---

**Keep this document open and run the monitoring commands periodically!**

**We're making history - this is the first training with auto-merge!** 🚀

---

**End of Monitor Guide**
