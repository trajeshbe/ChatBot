# Training Job 422 Error - Root Cause Analysis ✅

**Date**: 2025-12-17
**Status**: 🔍 **ROOT CAUSE IDENTIFIED**

---

## Problem Summary

User tried to create a training job and received:
1. ❌ **404 Error**: `POST /api/v1/finetuning/hyperparameters/recommend 404 (Not Found)`
2. ❌ **422 Error**: `POST /api/v1/finetuning/jobs 422 (Unprocessable Entity)`

---

## Root Cause: Empty Hyperparameters Object

### The Issue Chain

```
1. Frontend requests recommended hyperparameters
   ↓
2. Backend returns 404 (endpoint doesn't exist)
   ↓
3. Frontend catches error but continues anyway
   ↓
4. Frontend sends job creation with EMPTY hyperparameters: {}
   ↓
5. Backend validator checks: "peft method needs lora_r"
   ↓
6. Validation FAILS → 422 Unprocessable Entity
```

---

## Technical Details

### Backend Schema Validation

**File**: `/backend/app/schemas/finetuning_schemas.py` (Lines 178-206)

```python
class FineTuningJobCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)  # Required, non-empty
    base_model: str = Field(...)  # Required
    finetuning_method: Literal["peft", "sft", "rlhf-ppo", "rlhf-grpo"] = Field(...)
    training_objective: Literal["qa", "classification", "summarization", "instruction"] = Field(...)
    dataset_id: UUID = Field(...)  # Required
    hyperparameters: Dict[str, Any] = Field(...)  # ← Required, cannot be empty for PEFT!

    @validator('hyperparameters')
    def validate_hyperparameters(cls, v, values):
        """Validate hyperparameters based on method"""
        if 'finetuning_method' in values:
            method = values['finetuning_method']

            # ❌ THIS IS WHAT'S FAILING
            if method == "peft" and 'lora_r' not in v:
                raise ValueError("PEFT method requires 'lora_r' in hyperparameters")
```

**Required Hyperparameters for PEFT:**
- `lora_r` - **Required** (LoRA rank)
- `lora_alpha` - Optional but recommended
- `lora_dropout` - Optional
- `learning_rate` - Recommended
- `num_epochs` - Recommended
- `batch_size` - Recommended

---

### Frontend Code

**File**: `/frontend/src/components/finetuning/JobManager.tsx` (Lines 191-250)

```tsx
const createJob = async () => {
  try {
    let hyperparameters = {}  // ← Starts empty

    if (hyperparamMode === 'recommended') {
      // Try to get recommended hyperparameters
      const recommendResponse = await fetch(
        `${API_BASE}/api/v1/finetuning/hyperparameters/recommend`,  // ❌ 404
        { /* ... */ }
      )

      if (recommendResponse.ok) {
        hyperparameters = await recommendResponse.json()
      }
      // ❌ NO ELSE BLOCK - If 404, hyperparameters stays empty {}
    }

    // Send job creation request with potentially empty hyperparameters
    const response = await fetch(`${API_BASE}/api/v1/finetuning/jobs`, {
      method: 'POST',
      body: JSON.stringify({
        ...formData,
        hyperparameters,  // ← Sends {}
      }),
    })
  }
}
```

**Default Settings:**
```tsx
const [hyperparamMode, setHyperparamMode] = useState<HyperparamMode>('recommended')  // ← Default mode
const [formData, setFormData] = useState({
  name: '',  // ← User must fill this
  dataset_id: '',  // ← User must select dataset
  base_model: 'Qwen/Qwen2.5-7B-Instruct',
  finetuning_method: 'peft',  // ← Default method
  training_objective: 'instruction',
  quantization: '4bit',
})
```

---

## Why This Happens

### Scenario: User Creates Job

1. **User opens "Create Job" form**
   - Mode: "Recommended" (default)
   - Method: "PEFT" (default)

2. **User fills in:**
   - Job name: "story8-qwen-1.5b-test"
   - Dataset: story8
   - Base model: Qwen 2.5 1.5B

3. **User clicks "Create Job"**

4. **Frontend makes REQUEST 1:**
   ```
   POST /api/v1/finetuning/hyperparameters/recommend
   Response: 404 Not Found
   ```

5. **Frontend makes REQUEST 2:**
   ```
   POST /api/v1/finetuning/jobs
   Body: {
     name: "story8-qwen-1.5b-test",
     dataset_id: "3b5aebf0-8dcf-423c-aad4-65a8f3dba3b6",
     base_model: "Qwen/Qwen2.5-1.5B-Instruct",
     finetuning_method: "peft",
     training_objective: "instruction",
     quantization: "4bit",
     hyperparameters: {}  // ❌ EMPTY!
   }
   ```

6. **Backend validates request:**
   ```python
   if method == "peft" and 'lora_r' not in v:
       raise ValueError("PEFT method requires 'lora_r' in hyperparameters")
   ```

   **Result**: ❌ **ValidationError** → 422 Unprocessable Entity

---

## Solution Options

### Option 1: Provide Default Hyperparameters (Quick Fix) ✅

**Change frontend to use sensible defaults when recommended endpoint fails:**

**File**: `/frontend/src/components/finetuning/JobManager.tsx`

```tsx
const createJob = async () => {
  try {
    // Default hyperparameters for PEFT method
    let hyperparameters = {
      learning_rate: 0.0002,
      num_epochs: 3,
      batch_size: 4,
      gradient_accumulation_steps: 4,
      warmup_steps: 100,
      lora_r: 16,  // ✅ Required for PEFT
      lora_alpha: 32,
      lora_dropout: 0.05
    }

    if (hyperparamMode === 'recommended') {
      try {
        const recommendResponse = await fetch(
          `${API_BASE}/api/v1/finetuning/hyperparameters/recommend`,
          { /* ... */ }
        )

        if (recommendResponse.ok) {
          hyperparameters = await recommendResponse.json()
        }
      } catch (error) {
        console.warn('Failed to get recommended hyperparameters, using defaults:', error)
        // Continue with default hyperparameters
      }
    } else if (hyperparamMode === 'manual') {
      // Use user-provided manual hyperparameters
      hyperparameters = manualHyperparams
    }

    // Now hyperparameters is NEVER empty
    const response = await fetch(`${API_BASE}/api/v1/finetuning/jobs`, {
      method: 'POST',
      body: JSON.stringify({
        ...formData,
        hyperparameters,
      }),
    })
  }
}
```

---

### Option 2: Create the Missing Endpoint (Proper Fix) 🔧

**Add the hyperparameters recommendation endpoint:**

**File**: `/backend/app/api/routes/finetuning_routes.py`

```python
@router.post("/hyperparameters/recommend")
async def recommend_hyperparameters(
    request: HyperparameterRecommendationRequest,
    user: User = Depends(require_authentication)
):
    """
    Recommend hyperparameters based on finetuning method and dataset size
    """
    method = request.finetuning_method
    dataset_size = request.dataset_size
    available_memory_gb = request.available_memory_gb

    if method == "peft":
        # Adjust batch size based on memory
        if available_memory_gb < 12:
            batch_size = 2
        elif available_memory_gb < 24:
            batch_size = 4
        else:
            batch_size = 8

        # Adjust epochs based on dataset size
        if dataset_size < 100:
            num_epochs = 5
        elif dataset_size < 1000:
            num_epochs = 3
        else:
            num_epochs = 2

        return {
            "learning_rate": 0.0002,
            "num_epochs": num_epochs,
            "batch_size": batch_size,
            "gradient_accumulation_steps": 4,
            "warmup_steps": min(100, dataset_size // 10),
            "lora_r": 16,
            "lora_alpha": 32,
            "lora_dropout": 0.05
        }

    # Add other methods...
```

**Schema**:
```python
class HyperparameterRecommendationRequest(BaseModel):
    finetuning_method: Literal["peft", "sft", "rlhf-ppo", "rlhf-grpo"]
    dataset_size: int
    available_memory_gb: int = 24
```

---

### Option 3: Change Default Mode to Manual 🔧

**Change default mode from "recommended" to "manual":**

**File**: `/frontend/src/components/finetuning/JobManager.tsx`

```tsx
// Change this:
const [hyperparamMode, setHyperparamMode] = useState<HyperparamMode>('recommended')

// To this:
const [hyperparamMode, setHyperparamMode] = useState<HyperparamMode>('manual')
```

**Pros**: Avoids the 404 error entirely
**Cons**: User must manually provide all hyperparameters

---

## Recommended Solution

**Use Option 1 (Default Hyperparameters) as the immediate fix**, then implement Option 2 (proper endpoint) later.

### Why Option 1 is Best Short-Term:
1. ✅ **Quick fix** - No backend changes required
2. ✅ **Sensible defaults** - Users get working values immediately
3. ✅ **Graceful degradation** - If recommendation fails, continue with defaults
4. ✅ **Better UX** - Users don't need to know all hyperparameters

### Why Option 2 is Best Long-Term:
1. ✅ **Smart recommendations** - Adjust based on dataset size and available memory
2. ✅ **Better performance** - Optimized hyperparameters for each scenario
3. ✅ **Complete feature** - As originally intended in the UI

---

## Additional Issues Found

### Issue 1: Job Name Might Be Empty

**Problem**: The form allows empty job name, but schema requires `min_length=1`

**Frontend validation needed:**
```tsx
if (!formData.name || formData.name.trim() === '') {
  alert('❌ Job name is required')
  return
}
```

---

### Issue 2: Dataset ID Might Be Empty

**Problem**: If user doesn't select dataset, `dataset_id` is `''` which can't convert to UUID

**Frontend validation needed:**
```tsx
if (!formData.dataset_id) {
  alert('❌ Please select a dataset')
  return
}
```

---

## Implementation Plan

### Step 1: Add Default Hyperparameters ✅

**Edit**: `/frontend/src/components/finetuning/JobManager.tsx`

Add default hyperparameters and graceful error handling for the 404.

---

### Step 2: Add Frontend Validation ✅

Add validation before submitting:
- Job name not empty
- Dataset selected
- Base model selected

---

### Step 3: (Optional) Create Recommendation Endpoint 🔧

Implement proper backend endpoint for hyperparameter recommendations.

---

## Testing After Fix

### Test Case 1: Create Job with Qwen 1.5B

1. **Open Fine-Tuning page**
2. **Click "Create New Job"**
3. **Fill in:**
   - Job Name: "test-story8-qwen-1.5b"
   - Dataset: story8
   - Base Model: Qwen 2.5 1.5B Instruct (Lightweight)
   - Method: PEFT
   - Objective: Instruction
   - Quantization: 4bit
4. **Click "Create Job"**

**Expected**:
- ✅ No 404 error (or gracefully handled)
- ✅ No 422 error (default hyperparameters used)
- ✅ Job created successfully
- ✅ Job visible in jobs list

---

### Test Case 2: Verify Default Hyperparameters

Check the created job in the database:

```bash
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "
  SELECT
    name,
    base_model,
    finetuning_method,
    hyperparameters
  FROM finetuning_jobs
  ORDER BY created_at DESC
  LIMIT 1;"
```

**Expected hyperparameters**:
```json
{
  "learning_rate": 0.0002,
  "num_epochs": 3,
  "batch_size": 4,
  "gradient_accumulation_steps": 4,
  "warmup_steps": 100,
  "lora_r": 16,
  "lora_alpha": 32,
  "lora_dropout": 0.05
}
```

---

## Summary

**Root Cause**:
- Frontend sends empty `hyperparameters: {}` when recommendation endpoint fails (404)
- Backend validator requires `lora_r` for PEFT method
- Validation fails → 422 error

**Fix**:
- Add default hyperparameters in frontend
- Handle 404 gracefully
- Add frontend validation for required fields

**Impact**:
- ✅ Job creation will work immediately
- ✅ Users get sensible default hyperparameters
- ✅ Better error messages if validation still fails

---

**Status**: ⏳ **Ready to implement fix**

---

**Related Files**:
- `TRAINING_JOB_CREATION_FAILED_DIAGNOSIS.md` - Initial diagnostic guide
- `QWEN_1.5B_MODEL_ADDED.md` - Qwen 1.5B model addition
- `UI_DATASET_DISPLAY_FIX_COMPLETE.md` - Dataset display fixes

---

**End of Root Cause Analysis**
