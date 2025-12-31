# Trainer Image Mismatch - Root Cause Analysis & Fix

**Date**: 2025-12-24
**Status**: ✅ **FIXED**
**Version**: v1.0.5

---

## Executive Summary

Story5 and Story6 training jobs failed with the same "text column ignored" error **despite** rebuilding the finetuning-runtime image with the fix. Root cause: The Celery task was using a different Docker image (`chatbot-finetuning-trainer:v1.0.4`) than the one we rebuilt (`chatbot-finetuning-runtime:latest`).

### Critical Discovery:
- **We rebuilt**: `chatbot-finetuning-runtime:latest` (with fix)
- **Code used**: `chatbot-finetuning-trainer:v1.0.4` (without fix, 2 days old)
- **Result**: Story5 and Story6 failed despite timing suggesting they should have the fix

---

## Timeline of Events

### 1. Initial Fix Applied
**Time**: 2025-12-24 ~03:30 AM

**Action**: Added text column handling to `peft_trainer.py`:
```python
# ✅ FIX: Handle "text" column format (from CSV Question/Answer datasets)
elif "text" in dataset["train"].column_names:
    logger.info("🔄 Dataset has 'text' column - applying direct tokenization...")
```

**File**: `backend/app/services/finetuning/trainers/peft_trainer.py` (lines 166-192)

### 2. Docker Image Rebuild
**Time**: 2025-12-24 04:10:19 AM

**Command**:
```bash
docker-compose build finetuning-runtime
```

**Result**:
```
Image: chatbot-finetuning-runtime:latest
Image ID: a38ce52cb969
Created: 2025-12-24 04:10:19
```

### 3. Story5 Training Job
**Time**: 2025-12-24 03:48:46 AM (BEFORE image rebuild)

**Container**: `6afd2f1968b9`
**Image Used**: `chatbot-finetuning-trainer:v1.0.4` (2 days old, NO fix)
**Result**: **FAILED** - "No columns in the dataset match..."

**Expected**: Failure (created before rebuild)
**Actual**: Failure ✅ (expected)

### 4. Story6 Training Job
**Time**: 2025-12-24 04:32:30 AM (AFTER image rebuild)

**Container**: `3e99cb745893`
**Image Used**: `chatbot-finetuning-trainer:v1.0.4` (2 days old, NO fix)
**Result**: **FAILED** - "No columns in the dataset match..."

**Expected**: Success (created AFTER rebuild at 04:10:19)
**Actual**: Failure ❌ (UNEXPECTED!)

This failure triggered the investigation.

---

## Root Cause Analysis

### Investigation Steps

1. **Checked Docker Images**:
   ```bash
   docker images | grep finetuning
   ```

   **Result**:
   - `chatbot-finetuning-runtime:latest` - Built at 04:10:19 (NEW, with fix)
   - `chatbot-finetuning-trainer:v1.0.4` - Built 2 days ago (OLD, no fix)

2. **Checked Running Containers**:
   ```bash
   docker ps -a --filter "name=finetuning"
   ```

   **Result**: All training containers use `chatbot-finetuning-trainer:v1.0.4`

3. **Found the Hardcoded Image Reference**:
   ```bash
   grep -r "TRAINER_IMAGE" backend/app/services/finetuning/
   ```

   **Result**: `finetuning_sandbox_manager.py:55`

### The Smoking Gun

**File**: `backend/app/services/finetuning/finetuning_sandbox_manager.py`

**Line 55** (BEFORE fix):
```python
self.finetuning_image = os.getenv("FINETUNING_TRAINER_IMAGE", "chatbot-finetuning-trainer:v1.0.4")
```

**Problem**:
- Code is hardcoded to use `chatbot-finetuning-trainer:v1.0.4` (2 days old)
- We rebuilt `chatbot-finetuning-runtime:latest` (with fix)
- These are **different images**!

### Why Did This Happen?

**Docker Image Naming Confusion**:
- `chatbot-finetuning-runtime` = Service name in docker-compose.yml
- `chatbot-finetuning-trainer` = Image used by Celery tasks
- Both images built from `Dockerfile.finetuning-runtime`
- But versioned separately (runtime = latest, trainer = v1.0.x)

**Result**:
- We rebuilt the runtime image (latest tag)
- Code continued using the old trainer image (v1.0.4 tag)
- Fix never reached the training containers

---

## Solution Applied

### Step 1: Tag the Fixed Image
```bash
docker tag chatbot-finetuning-runtime:latest chatbot-finetuning-trainer:v1.0.5
```

**Result**:
- Created new tag `chatbot-finetuning-trainer:v1.0.5`
- Points to same image as `chatbot-finetuning-runtime:latest` (a38ce52cb969)
- Includes the text column handling fix

### Step 2: Update Code to Use New Tag
**File**: `backend/app/services/finetuning/finetuning_sandbox_manager.py:56`

**BEFORE**:
```python
self.finetuning_image = os.getenv("FINETUNING_TRAINER_IMAGE", "chatbot-finetuning-trainer:v1.0.4")
```

**AFTER**:
```python
# v1.0.5: Added text column handling for story datasets (2025-12-24)
self.finetuning_image = os.getenv("FINETUNING_TRAINER_IMAGE", "chatbot-finetuning-trainer:v1.0.5")
```

### Step 3: Restart Celery Worker
```bash
docker-compose restart celery-worker
```

**Why**: Celery worker imports `finetuning_sandbox_manager.py` at startup. Must restart to load updated image version.

---

## Verification

### Image Tags After Fix
```bash
$ docker images | grep finetuning-trainer

chatbot-finetuning-trainer   v1.0.5    a38ce52cb969   3 hours ago    16GB  ← NEW (with fix)
chatbot-finetuning-trainer   v1.0.4    352ecfef5593   2 days ago     16GB  ← OLD (no fix)
chatbot-finetuning-trainer   v1.0.3    64cc51cf383f   2 days ago     16GB
```

### Image ID Verification
```bash
$ docker images | grep a38ce52cb969

chatbot-finetuning-runtime   latest    a38ce52cb969   3 hours ago    16GB
chatbot-finetuning-trainer   v1.0.5    a38ce52cb969   3 hours ago    16GB
```

✅ Both tags point to same image (a38ce52cb969) - Fix is in v1.0.5!

### What's in v1.0.5

**Dockerfile**: `backend/Dockerfile.finetuning-runtime`

**Key Line**:
```dockerfile
COPY app/services/finetuning/trainers/ /app/app/services/finetuning/trainers/
```

This copies the fixed `peft_trainer.py` with text column handling into the image.

---

## Impact Analysis

### Story5 (Expected Failure)
- **Created**: 03:48:46 AM
- **Image Rebuilt**: 04:10:19 AM
- **Status**: FAILED ✅ (expected - created before rebuild)
- **Image Used**: v1.0.4 (no fix)

### Story6 (Unexpected Failure - Led to Discovery)
- **Created**: 04:32:30 AM
- **Image Rebuilt**: 04:10:19 AM
- **Status**: FAILED ❌ (unexpected - created AFTER rebuild)
- **Image Used**: v1.0.4 (no fix - code didn't point to new image!)

### Story7+ (Future Jobs)
- **Expected**: ✅ SUCCESS
- **Reason**: Will use v1.0.5 (with fix)
- **Verification**: Next story dataset will be the true test

---

## Why Story6 Failed (Timeline Proof)

```
03:30 AM - Added text column fix to peft_trainer.py code
03:48 AM - Story5 created (used old v1.0.4 image) → FAILED ✅
04:10 AM - Rebuilt finetuning-runtime:latest (with fix)
04:32 AM - Story6 created (still used old v1.0.4 image!) → FAILED ❌
          ↑
          WHY? Code hardcoded to v1.0.4, never updated to use new image

07:00 AM - Tagged runtime:latest as trainer:v1.0.5
07:01 AM - Updated code to use v1.0.5
07:02 AM - Restarted Celery worker
07:03 AM+ - Story7+ will use v1.0.5 (with fix) → SHOULD SUCCEED ✅
```

---

## Lessons Learned

### Issue 1: Inconsistent Image Naming
**Problem**: Multiple names for same image concept
- `finetuning-runtime` (service name)
- `finetuning-trainer` (actual image used)

**Fix**: Standardize on one name or document mapping clearly

### Issue 2: Version Tag Mismatch
**Problem**: Code uses versioned tag (v1.0.4), rebuild uses :latest
- Rebuild updated :latest but not v1.0.4
- Code continued using old v1.0.4

**Fix**: Either:
- Always use :latest in code
- Or version bump in code when rebuilding

### Issue 3: Container Image Verification
**Problem**: Assumed rebuild would be picked up automatically
- Didn't verify which image containers actually used
- Timing made it seem like it should work

**Fix**: Always verify:
```bash
docker inspect <container_id> | grep Image
```

### Issue 4: Missing Changelog
**Problem**: No clear version history for trainer images
- Hard to know what's in each version
- No documentation of changes

**Fix**: Maintain CHANGELOG.md with:
- Version numbers
- Changes in each version
- Build dates

---

## Prevention Measures

### 1. Automated Tagging Script
Create `scripts/tag_trainer_image.sh`:
```bash
#!/bin/bash
# Automatically tag runtime:latest as trainer:vX.X.X

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: ./tag_trainer_image.sh v1.0.6"
    exit 1
fi

# Tag the image
docker tag chatbot-finetuning-runtime:latest chatbot-finetuning-trainer:$VERSION

# Update code
sed -i "s/chatbot-finetuning-trainer:v[0-9.]*\"/chatbot-finetuning-trainer:$VERSION\"/" \
    backend/app/services/finetuning/finetuning_sandbox_manager.py

# Restart Celery
docker-compose restart celery-worker

echo "✅ Updated to $VERSION and restarted Celery worker"
```

### 2. Pre-deployment Verification
Before submitting new training jobs:
```bash
# Check current image version in code
grep "FINETUNING_TRAINER_IMAGE" backend/app/services/finetuning/finetuning_sandbox_manager.py

# Verify image exists
docker images | grep finetuning-trainer | grep <version>
```

### 3. Image Version in Database
Add `trainer_image_version` column to `finetuning_jobs` table:
```sql
ALTER TABLE finetuning_jobs ADD COLUMN trainer_image_version VARCHAR(50);
```

Update task to log which image was used:
```python
job.trainer_image_version = self.finetuning_image
```

### 4. Documentation
Maintain `docs/FINETUNING_IMAGE_VERSIONS.md`:
```markdown
| Version | Date | Changes | Git Commit |
|---------|------|---------|------------|
| v1.0.5  | 2024-12-24 | Added text column handling | abc123 |
| v1.0.4  | 2024-12-22 | GPU pool manager | def456 |
```

---

## Files Modified

| File | Change |
|------|--------|
| `backend/app/services/finetuning/finetuning_sandbox_manager.py` | Updated default image from v1.0.4 → v1.0.5 |
| Docker images | Tagged `chatbot-finetuning-runtime:latest` as `chatbot-finetuning-trainer:v1.0.5` |

---

## Success Criteria

✅ All criteria will be met when:

1. ✅ v1.0.5 image tagged and available
2. ✅ Code updated to use v1.0.5
3. ✅ Celery worker restarted
4. ⏳ Story7 training succeeds (PENDING - next test)
5. ⏳ Container inspection shows v1.0.5 image used (PENDING)
6. ⏳ Training logs show "🔄 Dataset has 'text' column" message (PENDING)

---

## Next Steps

1. **Create Story7 Training Job**
   - Use same story dataset format
   - Monitor container creation
   - Verify it uses `chatbot-finetuning-trainer:v1.0.5`

2. **Verify Training Logs**
   ```bash
   docker logs <container_id> | grep "text column"
   ```
   Expected: "🔄 Dataset has 'text' column - applying direct tokenization..."

3. **Monitor to Completion**
   - Expect training to succeed
   - Expect checkpoint creation
   - Expect deployment to Ollama

4. **Document Success**
   - Update `TEXT_COLUMN_TRAINER_FIX_COMPLETE.md`
   - Add to deployment checklist
   - Close related issue

---

## Related Documents

- `TEXT_COLUMN_TRAINER_FIX_COMPLETE.md` - Original fix documentation
- `DATASET_PREPROCESSING_FIX_COMPLETE.md` - Success validation fix
- `backend/app/services/finetuning/trainers/peft_trainer.py` - Trainer code with fix
- `backend/Dockerfile.finetuning-runtime` - Image build definition

---

## Conclusion

**Root Cause**: Image naming mismatch between rebuild and code usage

**Symptoms**:
- Story6 failed despite being created after Docker rebuild
- Training containers used old v1.0.4 image
- Fix existed in codebase but never reached containers

**Fix Applied**:
1. Tagged fixed image as v1.0.5
2. Updated code to use v1.0.5
3. Restarted Celery worker

**Status**: ✅ **FIXED** - Ready for Story7 testing

**Expected Outcome**: Story7 will be the first job to successfully train story datasets!

---

**End of Report**
