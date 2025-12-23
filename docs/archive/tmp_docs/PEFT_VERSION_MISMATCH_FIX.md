# PEFT Version Mismatch Issue - Root Cause & Fix

## Problem Discovery

**Date**: 2025-12-22
**Time**: 19:09 UTC (after 5+ minutes of deployment processing)

### Error Message
```
❌ Merge failed: LoraConfig.__init__() got an unexpected keyword argument 'alora_invocation_tokens'
```

### Root Cause Analysis

The adapter was trained with a **newer PEFT version** that includes experimental features (like ALoRA), but the backend had an **older PEFT version** that doesn't recognize these parameters.

**Version Mismatch**:
- **Backend (deployment)**: PEFT 0.7.1 (June 2023)
- **Finetuning trainer (training)**: PEFT 0.18.0 (December 2024)

**Timeline of Issues**:
1. ✅ Transformers 4.36.0 → 4.57.3 (fixed Qwen2 support)
2. ❌ **PEFT 0.7.1 → 0.18.0** (NEW BLOCKER - adapter compatibility)

### Why This Happened

The adapter was created during training by `finetuning-trainer` container which has PEFT 0.18.0. When the backend tries to load this adapter for merging, it uses PEFT 0.7.1 which doesn't support the new config parameters introduced in 0.18.0.

**Adapter Config** (`adapter_config.json` created by PEFT 0.18.0):
```json
{
  "base_model_name_or_path": "Qwen/Qwen2.5-1.5B-Instruct",
  "peft_type": "LORA",
  "alora_invocation_tokens": null,  // ❌ NOT RECOGNIZED by PEFT 0.7.1
  ...
}
```

When PEFT 0.7.1 tries to load this config:
```python
# In backend (PEFT 0.7.1)
from peft import PeftModel

# This fails because LoraConfig.__init__ in 0.7.1 doesn't accept 'alora_invocation_tokens'
peft_model = PeftModel.from_pretrained(base_model, adapter_path)
# TypeError: LoraConfig.__init__() got an unexpected keyword argument 'alora_invocation_tokens'
```

## The Fix

### Step 1: Upgrade PEFT in Backend

**File Modified**: `backend/requirements.txt` (line 291)

**Before**:
```
peft==0.7.1                     # Parameter-Efficient Fine-Tuning - LoRA adapter merging
```

**After**:
```
peft>=0.18.0                    # Parameter-Efficient Fine-Tuning - LoRA adapter merging (0.18.0+ for ALoRA support)
```

### Step 2: Rebuild Backend Container

```bash
docker-compose build backend --no-cache
```

**Status**: IN PROGRESS (started at 19:12 UTC)
**ETA**: 20-25 minutes

### Step 3: Recreate Containers

```bash
docker-compose stop backend celery-worker
docker-compose rm -f backend celery-worker
docker-compose up -d backend celery-worker
```

### Step 4: Verify PEFT Version

```bash
docker-compose exec backend pip show peft
# Expected: Version: 0.18.0 or higher
```

### Step 5: Retry Deployment

```bash
curl -X POST "http://localhost:8000/api/v1/finetuning/models-public/242b3688-f220-47a4-b146-64e33d14a244/deploy" \
  -H "Content-Type: application/json" \
  -d '{"deployment_target": "ollama", "deployment_config": {"model_name": "choles-qa-ft", "base_model": "Qwen/Qwen2.5-1.5B-Instruct"}}'
```

**Expected Result**: Merge succeeds, GGUF conversion proceeds, Ollama deployment completes

## Why Two Rebuilds Were Needed

| Rebuild | Purpose | Package Upgraded | Issue Fixed |
|---------|---------|------------------|-------------|
| **First** (18:10-18:34 UTC) | Fix Qwen2 support | transformers 4.36.0 → 4.57.3 | `KeyError: 'qwen2'` ✅ |
| **Second** (19:12-19:37 UTC) | Fix adapter loading | peft 0.7.1 → 0.18.0 | `alora_invocation_tokens` ❌→✅ |

## Lessons Learned

### 1. Version Alignment is Critical
Training and deployment environments must have **aligned PEFT versions**. If training uses PEFT 0.18.0, deployment must also use 0.18.0+.

### 2. Why Versions Diverged
- **Finetuning trainer** (`chatbot-finetuning-trainer:v1.0.4`): Built recently with PEFT 0.18.0
- **Backend** (`chatbot-backend`): Built months ago with PEFT 0.7.1 pinned in requirements.txt

### 3. Future Prevention
- **Sync requirements.txt**: Keep backend and finetuning-trainer in sync for critical packages (transformers, peft, accelerate, torch)
- **Version constraints**: Use `peft>=0.18.0` instead of `peft==0.7.1` to allow compatible updates
- **CI/CD checks**: Add automated checks to ensure training/deployment package versions are compatible

## Expected Deployment Flow (After Fix)

```
1. User clicks "Deploy to Ollama"
   ↓
2. Backend endpoint: /models-public/{id}/deploy
   ↓
3. OllamaDeploymentService.deploy_model()
   ↓
4. Detect adapter → Start merge process
   ↓
5. Load base model (Qwen2.5-1.5B-Instruct) with PEFT 0.18.0 ✅
   ↓
6. Load adapter with PEFT 0.18.0 ✅ (recognizes alora_invocation_tokens)
   ↓
7. Merge adapter + base → merged_model/ (2-3 min)
   ↓
8. Convert to GGUF q4_K_M (5-10 min)
   ↓
9. Deploy to Ollama via HTTP API (1-2 min)
   ↓
10. Update database: status = "deployed"
   ↓
11. Model available in Ollama: choles-qa-ft
```

## Testing Plan (After Build Completes)

### Test 1: Verify PEFT Version
```bash
docker-compose exec backend pip show peft | grep Version
# Expected: Version: 0.18.0 or higher
```

### Test 2: Deploy Model
```bash
curl -X POST "http://localhost:8000/api/v1/finetuning/models-public/242b3688-f220-47a4-b146-64e33d14a244/deploy" \
  -H "Content-Type: application/json" \
  -d '{"deployment_target": "ollama", "deployment_config": {"model_name": "choles-qa-ft", "base_model": "Qwen/Qwen2.5-1.5B-Instruct"}}'

# Monitor logs
docker-compose logs -f backend | grep -E "(🚀|Deploy|merge|GGUF|✅|❌)"
```

**Success Criteria**:
- ✅ No `alora_invocation_tokens` error
- ✅ Merge completes successfully
- ✅ GGUF conversion proceeds
- ✅ Ollama deployment succeeds

### Test 3: Verify in Ollama
```bash
docker-compose exec ollama ollama list | grep choles-qa-ft
# Expected: choles-qa-ft ~900 MB
```

### Test 4: Inference Test
```bash
docker-compose exec ollama ollama run choles-qa-ft "What is Choles Food Technologies?"
# Expected: Response based on training data
```

## Timeline

| Time (UTC) | Event |
|------------|-------|
| 18:10 | First rebuild started (transformers upgrade) |
| 18:34 | First rebuild completed |
| 18:35 | Containers recreated |
| 18:36 | Verified transformers 4.57.3 ✅ |
| 19:04 | Deployment triggered |
| 19:09 | **Deployment failed** - PEFT version mismatch discovered |
| 19:12 | Second rebuild started (PEFT upgrade) |
| ~19:37 | Second rebuild expected to complete |
| ~19:38 | Containers will be recreated |
| ~19:40 | Deployment will be retried |
| ~19:52 | Deployment expected to complete (10-15 min) |

## Total Time Investment

- **First rebuild**: 24 minutes
- **First deployment attempt**: 5 minutes (failed at merge)
- **Investigation**: 3 minutes
- **Second rebuild**: 25 minutes (expected)
- **Second deployment attempt**: 15 minutes (expected)

**Total**: ~72 minutes to resolve both version issues

---

**Status**: Second rebuild in progress (PEFT 0.7.1 → 0.18.0)
**Next Action**: Wait for rebuild to complete, then recreate containers and retry deployment
**Final Goal**: choles-qa-ft model deployed to Ollama and responding to Choles Food Technologies questions
