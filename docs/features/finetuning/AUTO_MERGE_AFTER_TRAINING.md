# Auto-Merge After Training - Implementation Plan

> **Goal**: Automatically merge LoRA adapters with base model immediately after training completes
> **Benefits**: No manual merge step, models ready to deploy immediately
> **Date**: 2025-12-22

---

## 🎯 Current Problem

**What happens now**:
1. Training completes → Saves LoRA adapters (small files ~50-200MB)
2. User must manually click "Merge & Deploy" button
3. Merge tries to run but fails (PEFT not installed in backend)
4. Progress bar shows fake progress (UI bug)
5. Model stays in `approved` status forever

**Root Cause**: Merge infrastructure not properly set up

---

## ✅ Proposed Solution: Auto-Merge in Training Container

### Architecture:

```
Training Container (has PEFT + transformers):
  1. Train model → Saves LoRA adapters
  2. Auto-merge → Combines adapters + base model  ⬅️ NEW STEP
  3. Save merged model → Full model weights
  4. Upload to MinIO → Both adapters + merged
  5. Update database → status = "merged"

Backend Container (no PEFT needed):
  1. User clicks "Deploy to Ollama"
  2. Copies merged model → Ollama
  3. No merge needed! ✅
```

---

## 📝 Implementation Steps

### Step 1: Add Merge Function to Training Script

**File**: `/backend/app/tasks/finetuning_tasks.py` (or wherever training task is defined)

**Add after training completes**:

```python
# At end of training task
def run_finetuning_task(job_id: str, ...):
    # ... existing training code ...

    # Training completed successfully
    logger.info(f"✅ Training completed for job {job_id}")

    # ========== NEW: AUTO-MERGE ==========
    try:
        logger.info(f"🔄 Starting auto-merge for job {job_id}")

        # Merge LoRA adapters with base model
        merged_model_path = merge_lora_after_training(
            job_id=job_id,
            adapter_path=final_checkpoint_path,
            base_model_name=base_model,
            output_path=workspace_path / "merged_model"
        )

        logger.info(f"✅ Auto-merge completed: {merged_model_path}")

        # Update database: status = "merged"
        update_model_status(model_id=model_id, status="merged", merged_path=str(merged_model_path))

    except Exception as e:
        logger.error(f"⚠️ Auto-merge failed: {e}")
        logger.info("Model saved as adapters only (manual merge required)")
        # Don't fail the whole job - adapters are still usable
    # =====================================

    return {"status": "success", "model_id": model_id}
```

### Step 2: Implement Merge Function

**File**: Create `/backend/app/tasks/auto_merge.py`

```python
"""
Auto-Merge After Training

Merges LoRA adapters with base model immediately after training.
Runs in the same container that did training (has PEFT installed).
"""

import logging
from pathlib import Path
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

logger = logging.getLogger(__name__)


def merge_lora_after_training(
    job_id: str,
    adapter_path: Path,
    base_model_name: str,
    output_path: Path
) -> Path:
    """
    Merge LoRA adapters with base model.

    Args:
        job_id: Training job ID
        adapter_path: Path to LoRA adapter checkpoint
        base_model_name: HuggingFace base model name
        output_path: Where to save merged model

    Returns:
        Path to merged model directory
    """
    logger.info(f"Loading base model: {base_model_name}")

    # Determine device
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Load base model
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map="auto" if device == "cuda" else None
    )

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)

    logger.info(f"Loading LoRA adapters from: {adapter_path}")

    # Load LoRA model
    model = PeftModel.from_pretrained(base_model, adapter_path)

    logger.info("Merging adapters with base model...")

    # Merge and unload adapters
    merged_model = model.merge_and_unload()

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving merged model to: {output_path}")

    # Save merged model
    merged_model.save_pretrained(output_path)
    tokenizer.save_pretrained(output_path)

    logger.info(f"✅ Merge complete! Model saved to: {output_path}")

    # Clean up memory
    del base_model
    del model
    del merged_model
    if device == "cuda":
        torch.cuda.empty_cache()

    return output_path
```

### Step 3: Update Database Schema (if needed)

If `merged_model_path` doesn't exist in `finetuned_models` table, add it:

```sql
ALTER TABLE finetuned_models
ADD COLUMN IF NOT EXISTS merged_model_path VARCHAR(512);
```

Already exists! ✅

### Step 4: Update Frontend

**File**: `/frontend/src/components/finetuning/MergeAndDeployButton.tsx`

**Change button logic**:

```typescript
// Before: Shows "Merge & Deploy" for all models
// After: Shows different button based on status

if (model.status === 'merged') {
  // Model already merged during training
  return <button onClick={handleDeploy}>Deploy to Ollama</button>;
} else if (model.status === 'approved' || model.status === 'adapter_only') {
  // Old models (trained before auto-merge feature)
  return <button onClick={handleMergeAndDeploy}>Merge & Deploy</button>;
}
```

### Step 5: Make Merge Optional (Backward Compatibility)

**Config option** in `.env`:

```bash
# Auto-merge after training (recommended)
FINETUNING_AUTO_MERGE=true

# Skip auto-merge (for debugging, saves time if testing training only)
# FINETUNING_AUTO_MERGE=false
```

**In training task**:

```python
import os

AUTO_MERGE = os.getenv("FINETUNING_AUTO_MERGE", "true").lower() == "true"

if AUTO_MERGE:
    # Run auto-merge
    merge_lora_after_training(...)
else:
    logger.info("Auto-merge disabled (FINETUNING_AUTO_MERGE=false)")
```

---

## 🔄 Complete Workflow (After Implementation)

### Training + Auto-Merge:

```
1. User creates training job
   ↓
2. Celery picks up job
   ↓
3. Training runs in finetuning-runtime container
   ↓
4. Training completes → Saves LoRA adapters
   ↓
5. AUTO-MERGE runs (same container) ⬅️ NEW
   - Loads base model
   - Loads LoRA adapters
   - Merges using PEFT
   - Saves full model
   - Uploads to MinIO
   - Updates DB: status="merged"
   ↓
6. Model appears in "Governance & Audit" as "Merged" ✅
   ↓
7. User clicks "Deploy to Ollama" (no merge needed)
   ↓
8. Model deployed, ready to use!
```

### Old Workflow (For Comparison):

```
1-4. Same as above
5. ❌ No auto-merge
6. Model appears as "Approved" (not ready)
7. User clicks "Merge & Deploy"
8. ❌ Merge fails (PEFT not in backend)
9. ❌ User stuck, can't deploy
```

---

## 📊 Benefits

### For Users:
- ✅ **No manual merge step** - One less button to click
- ✅ **Models ready immediately** - Deploy as soon as training finishes
- ✅ **No confusing status** - "Merged" means ready to deploy
- ✅ **Faster deployment** - Skip the 5-10 minute merge wait

### For System:
- ✅ **Correct architecture** - Merge happens where PEFT is installed
- ✅ **No fake progress bars** - Merge actually runs
- ✅ **Backward compatible** - Old models can still manual merge
- ✅ **Resource efficient** - GPU warm from training, use for merge

---

## ⚠️ Considerations

### Disk Space:
- **Before**: Only LoRA adapters (~50-200MB)
- **After**: Adapters + merged model (~1.5GB for Qwen2.5-1.5B)
- **Solution**: Clean up old merged models, keep only adapters for archival

### Training Time:
- **Before**: Training only
- **After**: Training + merge (~2-5 minutes extra on GPU)
- **Solution**: Make optional via `FINETUNING_AUTO_MERGE=false`

### Failure Handling:
- **If merge fails**: Log warning, save adapters, continue
- **User can**: Manual merge later from UI
- **Database**: Mark as `adapter_only` status

---

## 🧪 Testing Plan

### Test 1: New Training with Auto-Merge
1. Create new training job (training40)
2. Wait for training to complete
3. Check logs for "Auto-merge completed"
4. Verify model status = "merged" in database
5. Verify merged model exists in MinIO
6. Click "Deploy to Ollama" (should skip merge)
7. Verify model works in chat

### Test 2: Old Training (Backward Compat)
1. Use existing training39 (status="approved")
2. Should still show "Merge & Deploy" button
3. Click it, manual merge should work
4. Deploy and test

### Test 3: Merge Failure Handling
1. Simulate merge failure (invalid adapter path)
2. Verify training job still succeeds
3. Verify model status = "adapter_only"
4. Verify user can retry merge from UI

---

## 📝 Implementation Checklist

- [ ] Add auto-merge function to training task
- [ ] Create merge utility module
- [ ] Add FINETUNING_AUTO_MERGE config option
- [ ] Update frontend button logic (merged vs adapter_only)
- [ ] Test with new training job
- [ ] Test backward compatibility with old jobs
- [ ] Update documentation
- [ ] Create user guide

---

## 💡 Alternative Solutions (Considered and Rejected)

### Option 1: Add PEFT to Main Backend
- ❌ Bloats main container with heavy ML deps
- ❌ Main backend doesn't need PEFT for anything else
- ❌ Increases build time and image size

### Option 2: Separate Merge Service
- ❌ Over-engineering (adds complexity)
- ❌ Requires separate container
- ❌ GPU already warm from training, wasteful to spin up again

### Option 3: Client-Side Merge
- ❌ Impossible (models too large for browser)
- ❌ Security risk (exposing model weights)

### ✅ Option 4: Auto-Merge in Training Container (CHOSEN)
- ✅ Simple - reuses existing infrastructure
- ✅ Efficient - GPU already allocated
- ✅ Fast - no container spin-up
- ✅ Clean - merge where PEFT already installed

---

## 🚀 Next Steps

1. **Implement auto-merge** in training task
2. **Test thoroughly** with new training job
3. **Deploy** and verify in production
4. **Document** for users
5. **Monitor** for any issues

---

**Status**: 📋 **PLANNED** - Ready to implement

**Estimated Time**: 2-3 hours

**Priority**: 🔴 **HIGH** - Blocks model deployment workflow

---

**End of Document**
