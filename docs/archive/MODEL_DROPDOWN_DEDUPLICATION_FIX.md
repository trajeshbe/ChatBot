# Model Dropdown Deduplication Fix

**Date**: 2025-12-19
**Status**: ✅ COMPLETED

## Problem

Fine-tuned models appeared **TWICE** in the model dropdown:
1. Once in "**Local CPU**" section (auto-discovered from Ollama)
2. Once in "**Fine-Tuned Models**" section (from database registry)

### Root Cause

The `ModelSelector` component fetches models from two independent sources:

1. **Standard Models** (`/api/v1/models/`):
   - Queries Ollama API to auto-discover deployed models
   - Categorizes as `local-cpu`, `local-gpu`, or `proprietary`
   - Fine-tuned models in Ollama get auto-registered here

2. **Fine-Tuned Models** (`/api/v1/finetuning/models-public/for-chat`):
   - Queries `finetuned_models` database table
   - Returns models with deployment metadata
   - Same models as above, but with fine-tuning info

**Result**: `short_story_11_model-v1:latest` appeared in both lists.

## Solution

### Deduplication Logic

**File**: `frontend/src/components/ModelSelector.tsx`

**Change**: Fetch fine-tuned models first, then filter them out of standard model lists.

**Implementation** (Lines 55-86):

```typescript
const fetchModels = async (isRefresh = false) => {
  try {
    if (isRefresh) {
      setRefreshing(true)
    }

    // Fetch fine-tuned models first
    let fineTunedModelIds: string[] = []
    try {
      const ftResponse = await axios.get(`${API_URL}/api/v1/finetuning/models-public/for-chat`)
      const ftModels = ftResponse.data.finetuned_models || []
      setFineTunedModels(ftModels)
      fineTunedModelIds = ftModels.map((m: FineTunedModel) => m.id)  // Extract IDs
    } catch (ftError) {
      console.error('Error fetching fine-tuned models:', ftError)
      setFineTunedModels([])
    }

    // Fetch standard models and filter out fine-tuned duplicates
    const response = await axios.get(`${API_URL}/api/v1/models/`)

    // Deduplicate: Remove any models that exist in fine-tuned list
    const deduplicateModels = (modelList: Model[]) =>
      modelList.filter(m => !fineTunedModelIds.includes(m.id))

    setModels({
      proprietary: deduplicateModels(response.data.grouped.proprietary || []),
      local_gpu: deduplicateModels(response.data.grouped.local_gpu || []),
      local_cpu: deduplicateModels(response.data.grouped.local_cpu || [])
    })
    setDefaultModel(response.data.default)
    setGpuAvailable(response.data.gpu_info?.available || false)

    // ... rest of function
  }
}
```

### How It Works

1. **Fetch fine-tuned models first** and extract their IDs into an array
2. **Fetch standard models** from the model registry API
3. **Filter each category** (proprietary, local_gpu, local_cpu) to remove any model whose ID matches a fine-tuned model
4. **Set state** with deduplicated model lists

### Before vs After

**Before**:
```
Model Dropdown:
├─ Local CPU
│  └─ Short_Story_11_Model V1 (Ollama)  ← Duplicate 1
└─ Fine-Tuned Models
   └─ short_story_11_model              ← Duplicate 2
```

**After**:
```
Model Dropdown:
└─ Fine-Tuned Models
   └─ short_story_11_model              ← Only appears once!
```

## Benefits

1. **No Confusion**: Users see each model exactly once
2. **Correct Metadata**: Fine-tuned models display with their training info, not generic Ollama metadata
3. **Better UX**: Clear separation between base models and fine-tuned models
4. **Inference Stats**: Fine-tuned section can show usage statistics (total inferences, avg latency)

## Testing

### Verification Steps

1. **Refresh the model dropdown** (click refresh icon or reload page)
2. **Check "Local CPU" section**: `short_story_11_model-v1:latest` should NOT appear here
3. **Check "Fine-Tuned Models" section**: Should appear here with 🏆 Award icon and "Fine-Tuned" badge
4. **Select the model**: Should work correctly (we verified this already)

### Expected UI

```
Fine-Tuned Models
├─ short_story_11_model 🏆
│  ├─ Badge: "Fine-Tuned"
│  ├─ Provider: Ollama
│  ├─ Free (Local)
│  └─ 0 inferences (if no usage yet)
```

## Related Files

| File | Purpose | Changes |
|------|---------|---------|
| `frontend/src/components/ModelSelector.tsx` | Model dropdown UI | Added deduplication logic |
| `backend/app/services/llm_service.py` | LLM routing (previous fix) | Dynamic Ollama discovery |

## Technical Notes

### Why Duplicates Occurred

1. **Ollama Auto-Registration**:
   - Backend startup queries Ollama `/api/tags` endpoint
   - Discovers all deployed models (including fine-tuned ones)
   - Registers them in the model registry as generic Ollama models

2. **Fine-Tuning Registry**:
   - Separate database table (`finetuned_models`) tracks deployed fine-tuned models
   - Has additional metadata (base model, metrics, job ID, etc.)
   - Both systems are independent

### Design Decision

**We chose to prioritize fine-tuned models** because:
- They have richer metadata (training job, base model, metrics)
- They're explicitly managed by the user
- Usage statistics are tracked separately
- Makes it clear which models are custom fine-tuned vs. base models

### Alternative Approaches (Not Chosen)

1. **Hide fine-tuned from standard registry**: Would require backend changes to Ollama auto-discovery
2. **Merge the lists**: Would lose the categorical separation
3. **Show both with labels**: Confusing for users

## Summary

✅ **Fix Applied**: Fine-tuned models now appear only in the "Fine-Tuned Models" section
✅ **Frontend Restarted**: Changes active
✅ **User Action**: Refresh the model dropdown to see the deduplicated list

The model `short_story_11_model-v1:latest` will now appear exactly once, in the "Fine-Tuned Models" section with proper metadata.

---

**Status**: Ready for user to refresh and verify
