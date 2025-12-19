# Evaluation System - Current Gaps and Required Fixes

**Date**: 2025-12-19
**Status**: ⚠️ CRITICAL ISSUES IDENTIFIED - Requires Implementation

---

## 🚨 Critical Issues Found

### Issue 1: No Actual Model Inference ⚠️

**Current State** (`backend/app/services/finetuning/model_evaluation_service.py` lines 230-262):
```python
async def _generate_output(
    self,
    model_path: str,
    input_text: str,
    task_type: str
) -> str:
    """
    Generate output from fine-tuned model

    NOTE: This is a placeholder. In production, you'd:
    1. Load the model from model_path
    2. Run inference on input_text
    3. Return generated output
    """
    # TODO: Implement actual model loading and inference
    logger.warning("Using placeholder inference - implement actual model loading")
    return f"[Generated response to: {input_text[:50]}...]"
```

**Problem**:
- Evaluation currently computes REAL BLEU/ROUGE scores on PLACEHOLDER text
- Scores are MEANINGLESS because they're comparing placeholders to real references
- No actual model is being loaded or run

**Impact**: All evaluation metrics shown are bogus and cannot be trusted

---

### Issue 2: Test Set Not Being Saved ⚠️

**Current State** (`backend/app/services/finetuning/dataset_preprocessor.py` lines 633-706):

The `process()` method DOES create train/val split:
```python
def process(
    self,
    dataset_path: str,
    format_type: str,
    columns: Dict[str, str],
    train_split: float = 0.8,  # ← Train/val split exists!
    max_samples: Optional[int] = None,
    shuffle: bool = True
) -> Dict[str, Any]:
    # ...
    # Split train/val
    split_idx = int(len(formatted_data) * train_split)
    train_data = formatted_data[:split_idx]
    val_data = formatted_data[split_idx:]

    return {
        "train": train_data,
        "validation": val_data,
        "metadata": {...}
    }
```

**Problem**:
- Validation/test split IS created during preprocessing
- But we need to verify if it's being SAVED to MinIO for later evaluation use
- Evaluation service needs access to the original test set (with questions AND reference answers)

---

### Issue 3: No Automatic Post-Training Evaluation ⚠️

**Current State**:
- Training completes ✅
- Checkpoints uploaded to MinIO ✅ (after recent fix)
- Model registered in database ✅
- **BUT**: No automatic evaluation triggered

**What's Missing**:
1. No evaluation job triggered after training completes
2. User must manually click "Evaluate" button
3. No validation metrics computed during or after training

---

## 🔧 Required Fixes

### Fix 1: Implement Real Model Inference

**Options**:

#### Option A: Use Deployed Ollama Model (Simplest)
```python
async def _generate_output(
    self,
    model_path: str,  # Actually ollama_model_name from DB
    input_text: str,
    task_type: str
) -> str:
    """Generate using deployed Ollama model"""
    import httpx

    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{ollama_url}/api/generate",
            json={
                "model": model_path,  # ollama_model_name
                "prompt": input_text,
                "stream": False
            }
        )

        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            raise RuntimeError(f"Ollama inference failed: {response.text}")
```

**Pros**:
- Simple to implement
- No model loading overhead
- Reuses deployed model

**Cons**:
- Model must be deployed first (can't evaluate before approval)
- Requires Ollama running

#### Option B: Load Checkpoints from MinIO (More Flexible)
```python
async def _generate_output(
    self,
    model_path: str,  # minio://bucket/path
    input_text: str,
    task_type: str
) -> str:
    """Load model from MinIO checkpoints and run inference"""
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch

    # Download from MinIO to temp dir
    local_path = await self._download_checkpoints(model_path)

    # Load model and tokenizer
    model = AutoModelForCausalLM.from_pretrained(
        local_path,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    tokenizer = AutoTokenizer.from_pretrained(local_path)

    # Generate
    inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=256)
    generated = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return generated
```

**Pros**:
- Can evaluate before deployment
- Full control over inference parameters
- Works offline

**Cons**:
- Requires GPU
- Memory intensive
- Slower than Ollama

#### Recommended: Hybrid Approach
1. Check if model is deployed in Ollama → use Ollama API
2. If not deployed → download from MinIO and load locally

---

### Fix 2: Save and Track Test Set

**Implementation**:

1. **During Dataset Upload** (`backend/app/api/routes/finetuning_routes.py`):
```python
# After preprocessing
processed_data = preprocessor.process(
    dataset_path=local_path,
    format_type=training_objective,
    columns=column_mapping,
    train_split=0.8,  # 80% train, 20% test
    shuffle=True
)

# Save BOTH train and test sets to MinIO
train_path = f".../{dataset_id}/train.jsonl"
test_path = f".../{dataset_id}/test.jsonl"  # ← NEW: Save test set

# Upload to MinIO
await upload_to_minio(bucket, train_path, processed_data["train"])
await upload_to_minio(bucket, test_path, processed_data["validation"])  # ← NEW

# Store test set path in database
dataset.test_set_path = f"minio://documents/{test_path}"  # ← NEW
```

2. **Link Test Set to Model** (`backend/app/tasks/finetuning_tasks.py`):
```python
# When creating FineTunedModel after training
model = FineTunedModel(
    name=f"{job.name}_model",
    job_id=job.id,
    dataset_id=job.dataset_id,
    minio_checkpoint_path=checkpoint_url,
    test_dataset_path=dataset.test_set_path,  # ← NEW: Link to test set
    ...
)
```

3. **Use Test Set in Evaluation**:
```python
async def evaluate_model(self, model_id: str, num_samples: int = 100):
    model = await db.get(FineTunedModel, model_id)

    # Load test set from MinIO
    test_samples = await self._load_test_dataset(
        model.test_dataset_path,  # ← Use saved test set
        num_samples
    )

    # Run evaluation...
```

---

### Fix 3: Automatic Post-Training Evaluation

**Implementation in** `backend/app/tasks/finetuning_tasks.py`:

```python
@celery_app.task(name="execute_finetuning_job")
def execute_finetuning_job(job_id: str):
    # ... existing training code ...

    # After training completes and model is registered
    logger.info(f"✅ Model registered: {model.name} (ID: {model.id})")

    # ═══════════════════════════════════════════════════════════
    # NEW: Trigger automatic evaluation
    # ═══════════════════════════════════════════════════════════
    logger.info(f"🔍 Starting automatic evaluation for model {model.id}")

    try:
        eval_service = ModelEvaluationService()

        # Download test dataset from MinIO
        test_dataset_path = await download_from_minio(model.test_dataset_path)

        # Run evaluation (uses first 50 samples for speed)
        evaluation_result = await eval_service.evaluate_model(
            model_path=model.minio_checkpoint_path,
            test_dataset_path=test_dataset_path,
            task_type=job.training_objective or "text-generation",
            num_samples=50  # Quick evaluation
        )

        # Store metrics in model
        model.eval_metrics = evaluation_result.get("metrics", {})
        model.eval_timestamp = datetime.utcnow()
        db.commit()

        logger.info(f"✅ Automatic evaluation complete: {model.eval_metrics}")

    except Exception as e:
        logger.error(f"⚠️  Automatic evaluation failed: {e}")
        # Don't fail the training job if evaluation fails

    return {"status": "completed", "model_id": str(model.id)}
```

---

## 📊 Updated Workflow

### NEW: Complete Training → Evaluation Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. DATASET UPLOAD                                                   │
│    - Split dataset: 80% train, 20% test                            │
│    - Save train.jsonl to MinIO ✅                                   │
│    - Save test.jsonl to MinIO ✅ NEW                                │
│    - Store test_set_path in database ✅ NEW                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. TRAINING JOB CREATION                                            │
│    - Associate job with dataset (train + test)                     │
│    - Submit to Celery queue                                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. TRAINING EXECUTION (GPU Container)                               │
│    - Train on train.jsonl ONLY                                     │
│    - Save checkpoints to /workspace/finetuning/{job_id}/output     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. CHECKPOINT UPLOAD (Celery Worker)                                │
│    - Upload model checkpoints to MinIO                             │
│    - Register model in database with test_dataset_path             │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. AUTOMATIC EVALUATION ✅ NEW                                      │
│    - Download test.jsonl from MinIO                                │
│    - Load model from checkpoints OR use Ollama                     │
│    - Run inference on test samples                                 │
│    - Compute BLEU, ROUGE, METEOR scores                            │
│    - Store metrics in model.eval_metrics                           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 6. MODEL READY FOR APPROVAL                                         │
│    - Status: "registered"                                           │
│    - Has eval_metrics ✅                                            │
│    - Admin reviews metrics before approval                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🧪 Testing Strategy

### Phase 1: Fix Model Inference (Highest Priority)

1. **Implement Option A** (Ollama-based inference):
   - Update `_generate_output()` in `model_evaluation_service.py`
   - Deploy a model to Ollama
   - Manually trigger evaluation from UI
   - Verify REAL scores are computed

2. **Test**:
   ```bash
   # Check Ollama has models
   docker-compose exec ollama ollama list

   # Trigger evaluation via API
   curl -X POST http://localhost:8000/api/v1/finetuning/models-public/{model_id}/evaluate?num_samples=10

   # Check if scores are different from before (not all 0.0)
   ```

### Phase 2: Save Test Sets

1. Modify dataset upload endpoint
2. Upload a new dataset
3. Verify two files in MinIO:
   - `train.jsonl`
   - `test.jsonl`
4. Verify `test_set_path` in database

### Phase 3: Automatic Evaluation

1. Add evaluation trigger to Celery task
2. Train a new model
3. Verify evaluation runs automatically
4. Check `eval_metrics` populated in database

---

## 🎯 Priority Order

1. **CRITICAL**: Fix model inference (Option A - Ollama)
2. **HIGH**: Save test sets during upload
3. **MEDIUM**: Automatic post-training evaluation
4. **LOW**: Option B (local checkpoint loading) as fallback

---

## 📋 Database Schema Changes Needed

```sql
-- Add test_set_path to datasets table
ALTER TABLE finetuning_datasets
ADD COLUMN test_set_path VARCHAR(512);

-- Add test_dataset_path to models table
ALTER TABLE finetuned_models
ADD COLUMN test_dataset_path VARCHAR(512);

-- Add eval_timestamp
ALTER TABLE finetuned_models
ADD COLUMN eval_timestamp TIMESTAMP;
```

---

## ✅ Acceptance Criteria

**Before declaring evaluation "complete":**

- [ ] Evaluation uses REAL model inference (not placeholder)
- [ ] Test sets are saved to MinIO during dataset upload
- [ ] Models are linked to their test sets
- [ ] Evaluation loads test sets from MinIO
- [ ] BLEU/ROUGE scores are non-zero and meaningful
- [ ] Sample-by-sample results show real generated text vs reference
- [ ] Manual testing calls Ollama API successfully
- [ ] Frontend UI displays evaluation results correctly
- [ ] Automatic evaluation triggers after training (optional)

---

**Current Status**: ⚠️ **PLACEHOLDER IMPLEMENTATION - SCORES ARE NOT REAL**

**Action Required**: Implement Fix 1 (model inference) ASAP before user tests evaluation

---

**Date**: 2025-12-19
**Reported By**: User observation - "i dontt see a train test split OR automatic evaluation of fintuning happening or the scores that we see are just hardcoded ???"
**Status**: ⚠️ CRITICAL - Requires immediate implementation
