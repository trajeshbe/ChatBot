# Training14 Root Cause Analysis - FOUND THE ISSUE!

**Date**: 2025-12-21
**Job**: choles-qa-real-training14
**ID**: `6f39397f-a6c0-4306-b76e-7c0f91d7dd3a`

---

## 🔴 CRITICAL FINDING

### The Problem

**Training14 completed in only 3.2 minutes** - identical pattern to training10, 11, and 12.

### Root Cause Identified

The finetuning-runtime Docker image is **2 DAYS OLD** and contains the COMMENTED-OUT training code!

```bash
$ docker images | grep finetuning-runtime
chatbot-finetuning-runtime   latest   218101aa0a73   2 days ago   15.9GB
```

Meanwhile, the backend container has the UPDATED code:

```bash
$ docker-compose exec backend ls -la /app/app/services/finetuning/trainers/peft_trainer.py
-rwxrwxrwx 1 pwuser pwuser 14544 Dec 21 05:28 /app/app/services/finetuning/trainers/peft_trainer.py
```

**The Issue**:
- ✅ Backend container has fixes (Dec 21 05:28)
- ❌ Finetuning-runtime image is stale (2 days old)
- ❌ Training containers spawn from the OLD finetuning-runtime image
- ❌ Training runs with COMMENTED-OUT code (mock training)

---

## Training14 Details

### Job Configuration

```
Job ID:        6f39397f-a6c0-4306-b76e-7c0f91d7dd3a
Name:          choles-qa-real-training14
Base Model:    Qwen/Qwen2.5-1.5B-Instruct ✅
Team:          ITM11 ✅
Status:        completed
Duration:      3.2 minutes ❌ (expected 15-30 for real training)
Created:       2025-12-21 09:51:32 UTC
Completed:     2025-12-21 09:54:45 UTC
```

### Hyperparameters

```json
{
  "learning_rate": 0.0002,  ⚠️ (user wanted 0.01)
  "num_epochs": 3,
  "batch_size": 4,
  "gradient_accumulation_steps": 4,
  "lora_r": 16,
  "lora_alpha": 32,
  "lora_dropout": 0.05,
  "target_modules": ["q_proj", "v_proj"],
  "warmup_steps": 100,
  "max_seq_length": 2048
}
```

**Note**: Learning rate is still 0.0002 instead of the requested 0.01. The UI may not have an option to change this yet.

### MinIO Path

```
minio://documents/technology/itm11/science/admin/finetuning/datasets/company_qa_dataset.jsonl/checkpoints/choles-qa-real-training14/6f39397f-a6c0-4306-b76e-7c0f91d7dd3a/final/adapter_model/adapter_model.safetensors
```

✅ **FIX #2 VERIFIED**: Path uses `technology/itm11/` (correct team)

---

## Why Our Fixes Didn't Work

### Timeline of Events

1. **Dec 19** - Finetuning-runtime image was built with commented-out training code
2. **Dec 21 05:28** - We applied fixes to `peft_trainer.py` in the LOCAL codebase
3. **Dec 21 09:XX** - Backend container was restarted, picked up NEW code
4. **Dec 21 09:51** - Training14 launched
5. **PROBLEM**: Training container spawned from OLD finetuning-runtime image (2 days old)
6. **RESULT**: Training ran with commented-out code = mock training

### Architecture Issue

```
Celery Task (backend) → Spawns → Training Container (finetuning-runtime image)
     ✅ Has fixes                         ❌ OLD image from 2 days ago
```

The backend container orchestrates the job, but the actual training happens in a **separate container** spawned from the `chatbot-finetuning-runtime:latest` image.

**Key Discovery**: When we edit files in the backend container, those changes are NOT automatically reflected in the finetuning-runtime image. The finetuning-runtime image needs to be **rebuilt**.

---

## Verification of Fixes

### FIX #1: Real Training Code

**Backend Container** (✅ Has fix):
```bash
$ docker-compose exec backend grep -n "REAL TRAINING - Now enabled" \
  /app/app/services/finetuning/trainers/peft_trainer.py
290:        # REAL TRAINING - Now enabled!
```

**Finetuning-Runtime Image** (❌ OLD):
- Image built: 2 days ago
- Contains: Commented-out training code

### FIX #2: Team Path

**Backend Container** (✅ Verified):
```bash
$ docker-compose exec backend grep -A 10 "Get user's primary team from user_teams" \
  /app/app/api/routes/finetuning_routes.py
# Returns correct query to user_teams table
```

**Training14 Result** (✅ Working):
- Team: ITM11 ✅
- MinIO Path: technology/itm11/... ✅

---

## Solution

### Required Action

**Rebuild the finetuning-runtime image** to include the updated `peft_trainer.py` with uncommented training code.

```bash
# Option 1: Rebuild just finetuning-runtime
docker-compose build finetuning-runtime --no-cache

# Option 2: Rebuild all images
docker-compose build --no-cache

# Option 3: Use Makefile
make build
```

After rebuilding:
1. ✅ New training containers will use UPDATED code
2. ✅ Real training will occur (not mock)
3. ✅ Duration will be 15-30 minutes
4. ✅ Model will actually learn from dataset

---

## Impact Analysis

### All Previous Training Jobs

| Job | Duration | Status | Reason |
|-----|----------|--------|--------|
| training10 | ~8 min | Mock | Old image |
| training11 | ~6 min | Mock | Old image |
| training12 | ~6 min | Mock | Old image |
| training13 | Cancelled | N/A | Wrong model selected (7B instead of 1.5B) |
| training14 | 3.2 min | Mock | **Old image** |

**Conclusion**: ALL training jobs used the old finetuning-runtime image with commented-out code.

### What Worked

| Fix | Status | Evidence |
|-----|--------|----------|
| **FIX #2: Team Path** | ✅ **WORKING** | Training14 shows Team=ITM11, path=technology/itm11/... |
| **FIX #1: Real Training** | ⚠️ **CODE FIXED, IMAGE NOT REBUILT** | Backend has fix, but finetuning-runtime image is stale |

---

## Next Steps

### Immediate Actions

1. **Rebuild finetuning-runtime image**
   ```bash
   docker-compose build finetuning-runtime --no-cache
   ```

2. **Create training15** with monitoring
   - Use same settings as training14
   - Model: Qwen2.5-1.5B-Instruct
   - Learning Rate: 0.01 (if UI allows, otherwise 0.0002)
   - Monitor logs for "REAL training" message

3. **Verify success criteria**:
   - ✅ Duration: 15-30 minutes (not 3-6 minutes)
   - ✅ Logs show: "🚀 Starting REAL training (NOT mock)..."
   - ✅ Logs show: "Loaded X training samples"
   - ✅ Logs show: "Epoch 1/3:", "Epoch 2/3:", "Epoch 3/3:"
   - ✅ Team: ITM11
   - ✅ Path: technology/itm11/...

---

## Lessons Learned

### Docker Architecture

1. **Backend container** runs API, Celery workers
2. **Finetuning-runtime image** is used to spawn SEPARATE training containers
3. **Code changes in backend** ≠ code changes in finetuning-runtime
4. **Must rebuild images** after code changes to training scripts

### File Locations

- **Backend**: `/app/app/services/finetuning/trainers/peft_trainer.py`
- **Finetuning-Runtime**: Same path, but FROM IMAGE (not volume mount)
- **Local**: `/mnt/c/AIML/ClaudeCode/chatbot/ChatBot/backend/app/services/finetuning/trainers/peft_trainer.py`

### Why We Missed This

1. We verified the fix in the backend container ✅
2. We restarted the backend container ✅
3. We assumed the finetuning containers would use the same code ❌
4. We didn't check the finetuning-runtime image build date ❌

---

## Summary

**Root Cause**: Finetuning-runtime image is 2 days old, contains commented-out training code.

**Why Training Failed**: Training containers spawn from the OLD image, not the updated backend code.

**Solution**: Rebuild finetuning-runtime image, then create training15.

**FIX #2 Status**: ✅ Fully working (Team=ITM11, correct MinIO path)

**FIX #1 Status**: ⚠️ Code is fixed, but image needs rebuild

---

**Status**: ROOT CAUSE IDENTIFIED - Ready to rebuild and retry

**Date**: 2025-12-21 09:56 UTC

---
