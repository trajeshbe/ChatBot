# LoRA Merge - Quick Start Reference

**JIRA**: FINETUNE-002 | **Timeline**: 3 days | **Status**: Ready for Implementation

---

## 📋 Documents Roadmap

| Read First | Purpose | Time |
|------------|---------|------|
| **This file** | Quick reference | 2 min |
| `/tmp/MERGE_IMPLEMENTATION_SUMMARY.md` | Executive summary | 5 min |
| `/tmp/JIRA_FINETUNING_MERGE_ONLY.md` | Complete spec + code | 15 min |
| `/tmp/MERGE_INTEGRATION_ANALYSIS.md` | Technical deep dive | 10 min |

---

## 🎯 The 30-Second Summary

**What's missing**: Merge service to combine LoRA adapters (8.7 MB) with base model → full model (3.2 GB)

**What exists**:
- ✅ Ollama deployment service (already checks for merged models!)
- ✅ Database schema (80% ready, just add 2 columns)
- ✅ API infrastructure (just add 2 endpoints)
- ✅ Workspace optimization (skip MinIO download!)

**Implementation**: ~21 hours (3 days)

---

## 🔑 Critical Integration Point

### MUST Save Merged Model To:

```
/workspace/finetuning/{job_id}/output/merged_model/
```

**Why?** OllamaDeploymentService **already checks this path FIRST**:

```python
# From ollama_deployment_service.py:55
workspace_merged = f"/workspace/finetuning/{job_id}/output/merged_model"
if os.path.exists(workspace_merged):
    logger.info("✅ Using merged model from workspace")
    local_model_path = workspace_merged  # ← No MinIO download!
```

---

## 📝 Implementation Checklist

### Database (1 hour)
```sql
ALTER TABLE finetuned_models
ADD COLUMN merged_model_path TEXT,
ADD COLUMN merge_duration_seconds INTEGER;
```

### Merge Service (6 hours)
Create: `backend/app/services/finetuning/model_merge_service.py`

**Key method**:
```python
def merge_lora_adapters(self, model_id, adapter_path, base_model):
    # 1. Download adapter from MinIO
    # 2. Load base model: AutoModelForCausalLM.from_pretrained(base_model)
    # 3. Load adapter: PeftModel.from_pretrained(model, adapter_path)
    # 4. Merge: merged_model = model.merge_and_unload()  ← KEY!
    # 5. Save to: /workspace/{job_id}/output/merged_model  ← CRITICAL PATH!
    # 6. Update DB: status='merged', merged_model_path='...'
```

### Celery Task (2 hours)
Add to: `backend/app/tasks/finetuning_tasks.py`

```python
@celery.task(name="merge_lora_model", bind=True)
def merge_lora_model_task(self, model_id, adapter_path, base_model):
    # Call ModelMergeService
    pass
```

### API Endpoints (2 hours)
Add to: `backend/app/api/routes/finetuning_routes.py`

```python
@router.post("/api/v1/finetuning/models/{model_id}/merge")
async def merge_lora_adapters(...):
    # Trigger Celery task
    pass

@router.get("/api/v1/finetuning/models/{model_id}/merge-status")
async def get_merge_status(...):
    # Return status from DB
    pass
```

### Frontend (4 hours)
Update: Your model card component

```typescript
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

## 🔗 Complete Workflow

```
Training → LoRA adapters (8.7 MB) ✅ Working
        ↓
User clicks "Merge Adapters" ← NEW (4 hours frontend work)
        ↓
Celery task runs merge (5-15 min) ← NEW (8 hours backend work)
        ↓
Merged model in workspace (3.2 GB) ← NEW
        ↓
User clicks "Deploy to Ollama" ✅ Your existing UI
        ↓
OllamaDeploymentService finds merged model ✅ Already implemented!
        ↓
Model deployed to Ollama ✅ Working
```

---

## ⚡ Key Performance Optimization

**Workspace-first strategy** (already in your code!):

```
Deployment WITHOUT merge implementation:
- Download adapter from MinIO (2 sec)
- Try to use adapter with ADAPTER directive (may not work)

Deployment WITH merge implementation:
- Check /workspace/{job_id}/output/merged_model ✅
- Model found in workspace ✅
- Skip MinIO download (save 2-5 minutes!) ✅
- Use merged model directly ✅
```

---

## 🚀 Day-by-Day Plan

### Day 1
- [ ] Database migration (1 hour)
- [ ] ModelMergeService implementation (5 hours)
- [ ] Celery task (2 hours)

### Day 2
- [ ] API endpoints (2 hours)
- [ ] End-to-end backend testing (4 hours)
  - Trigger merge via API
  - Verify workspace output
  - Check database updates

### Day 3
- [ ] Frontend integration (4 hours)
  - Merge button
  - Status polling
  - Error handling
- [ ] Integration testing (2 hours)
  - Train → Merge → Deploy workflow

---

## 📊 Status Values

```
Training complete → status='adapter_only'
User triggers merge → status='merging'
Merge complete → status='merged'
User triggers deploy → status='deployed'
```

---

## ✅ Pre-Implementation Verification

Run these commands to verify assumptions:

```bash
# 1. Check if workspace persists after training
docker-compose exec finetuning-runtime ls -la /workspace/finetuning/427b1025-57db-45de-826c-3713fc8ecb19/

# 2. Check status column constraint
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "
SELECT consrc FROM pg_constraint
WHERE conname LIKE '%finetuned_models_status%';"

# 3. Verify Ollama deployment service
grep -A 10 "workspace_merged" backend/app/services/ollama_deployment_service.py
```

---

## 🎯 Success Criteria

- [ ] Merge completes in < 15 minutes
- [ ] Workspace optimization works (no MinIO download)
- [ ] Database status transitions correctly
- [ ] UI shows real-time progress
- [ ] Deployed models respond within 2 seconds
- [ ] Error handling logs failures

---

## 📚 Full Documentation Links

All in `/tmp/`:
- `JIRA_FINETUNING_MERGE_ONLY.md` - Complete spec with code examples
- `MERGE_INTEGRATION_ANALYSIS.md` - Infrastructure analysis
- `MERGE_IMPLEMENTATION_SUMMARY.md` - Executive summary
- `TRAINING36_SUCCESS_REPORT.md` - Training pipeline validation
- `TRAINING37_SUCCESS_REPORT.md` - Bug fixes validation

---

**Ready to implement!** All specs complete, integration points identified, existing infrastructure is merge-aware. 🚀
