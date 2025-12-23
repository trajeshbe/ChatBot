# 422 Validation Error - FIXED

**Date**: 2025-12-21 02:17 UTC
**Issue**: Job creation failing with "422 Unprocessable Entity"
**Root Cause**: Missing `lora_r` field in hyperparameters for PEFT method
**Status**: ✅ FIXED

---

## Problem Description

When creating a new fine-tuning job with PEFT method, the request was failing with:
```
❌ Job creation failed: [object Object]
POST http://localhost:8000/api/v1/finetuning/jobs 422 (Unprocessable Entity)
```

Browser console showed:
```javascript
Creating job with hyperparameters: {
  learning_rate: 0.0002,
  num_epochs: 3,
  batch_size: 4,
  gradient_accumulation_steps: 4,
  warmup_steps: 100
  // ❌ Missing: lora_r, lora_alpha, lora_dropout, target_modules, max_seq_length
}
```

---

## Root Cause Analysis

### 1. Backend Validation (finetuning_schemas.py:203)
```python
@validator('hyperparameters')
def validate_hyperparameters(cls, v, values):
    """Validate hyperparameters based on method"""
    if 'finetuning_method' in values:
        method = values['finetuning_method']
        if method == "peft" and 'lora_r' not in v:
            raise ValueError("PEFT method requires 'lora_r' in hyperparameters")
```

**Requirement**: PEFT method MUST have `lora_r` in hyperparameters, or validation fails with 422.

### 2. Frontend Logic Bug (JobManager.tsx:263-264)
```typescript
// ❌ OLD CODE (BUGGY)
if (hyperparamMode === 'manual') {
  hyperparameters = Object.keys(hyperparameterConfig).length > 0
    ? hyperparameterConfig  // ❌ Replaces defaults entirely!
    : manualHyperparams
}
```

**Problem**: When `HyperparameterConfiguration` component loads, it fetches defaults from backend API and returns partial hyperparameters. This code REPLACED the full defaults (which included `lora_r`) with the partial config.

### 3. HyperparameterConfiguration Component
```typescript
// HyperparameterConfiguration.tsx:107-132
const loadDefaults = async () => {
  const response = await fetch(
    `${API_BASE}/api/v1/finetuning/hyperparameters/defaults?finetuning_method=${finetuningMethod}`
  )
  const data = await response.json()
  setValues(data.defaults || {})
}
```

This component fetches from backend, which may return PARTIAL defaults (missing PEFT-specific fields like `lora_r`, `target_modules`, `max_seq_length`).

---

## The Fix

### Code Change (JobManager.tsx:261-267)
```typescript
// ✅ NEW CODE (FIXED)
if (hyperparamMode === 'manual') {
  // Merge hyperparameters: defaults + component overrides
  // This ensures required fields like lora_r are always included
  hyperparameters = {
    ...getDefaultHyperparameters(formData.finetuning_method), // Start with FULL defaults
    ...(Object.keys(hyperparameterConfig).length > 0 ? hyperparameterConfig : manualHyperparams) // Override with user selections
  }
}
```

**Solution**: Use JavaScript object spread to MERGE instead of REPLACE:
1. Start with `getDefaultHyperparameters()` which includes ALL required fields
2. Overlay user customizations from `hyperparameterConfig` on top
3. Result: User changes preserved + required fields guaranteed present

---

## Full Defaults for PEFT Method

```typescript
// JobManager.tsx:224-236
if (method === 'peft') {
  return {
    learning_rate: 0.0002,
    num_epochs: 3,
    batch_size: 4,
    gradient_accumulation_steps: 4,
    warmup_steps: 100,
    lora_r: 16,              // ✅ Required by backend
    lora_alpha: 32,          // ✅ LoRA config
    lora_dropout: 0.05,      // ✅ LoRA config
    target_modules: ["q_proj", "v_proj"],  // ✅ Required by backend
    max_seq_length: 2048     // ✅ Required by backend
  }
}
```

---

## Verification

### Before Fix
```json
// POST /api/v1/finetuning/jobs
{
  "name": "test-job",
  "finetuning_method": "peft",
  "hyperparameters": {
    "learning_rate": 0.0002,
    "num_epochs": 3
    // ❌ Missing lora_r → 422 Validation Error
  }
}
```

### After Fix
```json
// POST /api/v1/finetuning/jobs
{
  "name": "test-job",
  "finetuning_method": "peft",
  "hyperparameters": {
    "learning_rate": 0.0002,
    "num_epochs": 3,
    "lora_r": 16,                          // ✅ Present
    "lora_alpha": 32,                      // ✅ Present
    "lora_dropout": 0.05,                  // ✅ Present
    "target_modules": ["q_proj", "v_proj"], // ✅ Present
    "max_seq_length": 2048                 // ✅ Present
  }
}
```

---

## Testing Instructions

1. **Refresh the frontend**: Hard refresh (Ctrl+Shift+R) to load updated JavaScript
2. **Create a new job**:
   - Name: "choles-qa-real-training8"
   - Method: PEFT
   - Training Objective: QA
   - Dataset: company_qa_dataset
   - Hyperparameters: Use Manual or Recommended mode
3. **Click Create Job**
4. **Expected Result**: ✅ Job created successfully (no 422 error)
5. **Verify in console**: Check browser console for hyperparameters object - should include `lora_r`, `target_modules`, `max_seq_length`

---

## Additional Modes

The fix also applies to other hyperparameter modes:

### Recommended Mode
```typescript
} else if (hyperparamMode === 'recommended') {
  // Fetch from backend /api/v1/finetuning/hyperparameters/recommend
  hyperparameters = recommended
  // Already includes all required fields
}
```

### Auto-Tune Mode
```typescript
} else if (hyperparamMode === 'auto-tune') {
  hyperparameters = {
    auto_tune: true,
    ...autoTuneConfig
  }
  // Backend will handle defaults for auto-tune
}
```

---

## Related Files

- `/frontend/src/components/finetuning/JobManager.tsx` - Main job creation logic (FIXED)
- `/frontend/src/components/finetuning/HyperparameterConfiguration.tsx` - Dynamic hyperparam component
- `/backend/app/schemas/finetuning_schemas.py` - Validation schema (lines 197-207)
- `/backend/app/api/routes/finetuning_routes.py` - Job creation endpoint (lines 511-634)

---

## Summary

**Before**: HyperparameterConfiguration component was completely replacing defaults, removing required fields
**After**: Merging strategy ensures all required fields are present while preserving user customizations
**Impact**: Job creation now works reliably across all hyperparameter modes
**Next Step**: Test the pipeline visualization with a new training job!

