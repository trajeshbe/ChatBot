# Fine-Tuned Model Deployment Fix - Implementation Plan

**Date**: 2025-12-18
**Issue**: PEFT adapters not merged before deployment, resulting in base model being used instead of fine-tuned model
**Status**: 🔴 CRITICAL - Chat UI not using actual fine-tuned models

---

## 🔍 Root Cause Analysis

### Current Broken Flow:

```
1. Training → Creates PEFT/LoRA adapter_model ✅
2. Save adapters to MinIO ✅
3. Deploy to Ollama → Uses adapter_model directly ❌ (WRONG)
   └─→ Result: Base model deployed, adapters ignored
```

### What Should Happen:

```
1. Training → Creates PEFT/LoRA adapter_model ✅
2. **MERGE adapters into base model** ❌ (MISSING)
   └─→ merged_model = model.merge_and_unload()
3. Save merged_model to MinIO ❌ (MISSING)
4. Deploy merged_model to Ollama ✅
   └─→ Result: Fully fine-tuned model deployed
```

---

## 📊 Evidence of the Problem

### Database Check:
```sql
SELECT name, base_model, minio_checkpoint_path
FROM finetuning_jobs
WHERE name = 'qwen_test_job';
```

**Result**:
```
name          | base_model         | minio_checkpoint_path
qwen_test_job | Qwen/Qwen2.5-1.5B | AI-ML/Research/.../final/adapter_model
```

**Problem**: Path ends with `adapter_model` (adapters only), not `merged_model` (full model)

### Chat UI Behavior:
- Model says "I am Claude" (wrong identity)
- Model says "created by Anthropic" (wrong creator)
- Direct Ollama test says "I am Qwen, created by Alibaba Cloud" (base model, not fine-tuned)

### Ollama Model Size:
```json
{
  "name": "qwen-test-v1:latest",
  "size": 986062081  // 940 MB - base model size, not merged size
}
```

---

## 🛠️ Implementation Plan

### Phase 1: Add Merge Step to Training Workflow ⭐ CRITICAL

**File**: `backend/app/services/finetuning/trainers/peft_trainer.py`

**Changes Required**:

#### Current Code (lines 215-231):
```python
# Write result
result = {
    "success": True,
    "message": "Training setup successful (no dataset)",
    "status": "completed",
    "model_info": {
        "base_model": config.get("base_model"),
        "quantization": config.get("quantization"),
        "lora_config": {
            "r": config["hyperparameters"].get("lora_r", 16),
            "alpha": config["hyperparameters"].get("lora_alpha", 32)
        }
    }
}
```

#### Fixed Code (with merge step):
```python
# Save adapter weights
adapter_dir = output_dir / "adapter_model"
adapter_dir.mkdir(parents=True, exist_ok=True)
model.save_pretrained(adapter_dir)
tokenizer.save_pretrained(adapter_dir)
logger.info(f"✅ Adapter saved to {adapter_dir}")

# **CRITICAL: Merge adapters into base model**
logger.info("🔄 Merging PEFT adapters into base model...")
try:
    # Load base model again (without quantization for merging)
    from transformers import AutoModelForCausalLM
    base_model_full = AutoModelForCausalLM.from_pretrained(
        config.get("base_model"),
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16  # Use fp16 or bf16 for efficiency
    )

    # Load PEFT model with adapters
    from peft import PeftModel
    peft_model = PeftModel.from_pretrained(base_model_full, adapter_dir)

    # Merge and unload - THIS IS THE KEY STEP
    merged_model = peft_model.merge_and_unload()

    # Save merged model
    merged_dir = output_dir / "merged_model"
    merged_dir.mkdir(parents=True, exist_ok=True)
    merged_model.save_pretrained(merged_dir)
    tokenizer.save_pretrained(merged_dir)

    logger.info(f"✅ Merged model saved to {merged_dir}")

    # Write result with BOTH paths
    result = {
        "success": True,
        "status": "completed",
        "output_dir": str(output_dir),
        "adapter_dir": str(adapter_dir),
        "merged_dir": str(merged_dir),  # ← NEW: Path to merged model
        "model_info": {
            "base_model": config.get("base_model"),
            "quantization": config.get("quantization"),
            "has_merged_model": True  # ← NEW: Flag indicating merge succeeded
        }
    }

except Exception as merge_error:
    logger.error(f"❌ Failed to merge model: {merge_error}")
    result = {
        "success": True,  # Training succeeded, merge failed
        "status": "completed_no_merge",
        "adapter_dir": str(adapter_dir),
        "merged_dir": None,
        "merge_error": str(merge_error),
        "model_info": {
            "has_merged_model": False
        }
    }
```

**Key Points**:
1. **Save adapters first** - Always keep adapter_model as backup
2. **Load base model without quantization** - Required for merging
3. **Use `merge_and_unload()`** - This creates a standalone fine-tuned model
4. **Save both paths** - Store both adapter_model and merged_model in MinIO

---

### Phase 2: Update Database Schema

**File**: Add new migration

**Changes Required**:

```sql
-- Add column to store merged model path separately
ALTER TABLE finetuning_jobs
ADD COLUMN merged_model_path VARCHAR(512);

-- Update existing job (for testing)
UPDATE finetuning_jobs
SET merged_model_path = REPLACE(minio_checkpoint_path, 'adapter_model', 'merged_model')
WHERE minio_checkpoint_path LIKE '%adapter_model';
```

**Or** update the existing `minio_checkpoint_path` column to point to merged_model:

```python
# In training service after merge:
job.minio_checkpoint_path = f"{base_path}/merged_model"  # Use merged, not adapter
```

---

### Phase 3: Fix Ollama Deployment Service ⭐ CRITICAL

**File**: `backend/app/services/ollama_deployment_service.py`

**Current Broken Code** (lines 90-104):
```python
modelfile_content = f"""# Modelfile for {model_name}
FROM {base_model}

# Load fine-tuned adapter weights
ADAPTER {model_path}  # ← THIS DOESN'T WORK PROPERLY

# Model parameters
PARAMETER temperature {parameters.get('temperature', 0.7)}
...
"""
```

**Problem**: The `ADAPTER` directive doesn't work correctly for most models. It's meant for loading adapters on top of an already-deployed base model, not for deploying merged models.

**Fixed Code**:
```python
modelfile_content = f"""# Modelfile for {model_name}
# Use the merged fine-tuned model directly
FROM {model_path}  # ← Point directly to merged model GGUF or safetensors

# Model parameters
PARAMETER temperature {parameters.get('temperature', 0.7)}
PARAMETER top_p {parameters.get('top_p', 0.9)}
PARAMETER top_k {parameters.get('top_k', 40)}
PARAMETER num_ctx {parameters.get('num_ctx', 2048)}

# System prompt (optional)
SYSTEM You are a helpful AI assistant.
"""
```

**Key Changes**:
1. **Remove `ADAPTER` directive** - Don't try to load adapters separately
2. **Use `FROM {model_path}`** - Point directly to the merged model files
3. **Convert to GGUF format first** (if needed) - Ollama prefers GGUF format

---

### Phase 4: Add Model Format Conversion (Optional but Recommended)

**File**: New service `backend/app/services/finetuning/model_converter_service.py`

**Purpose**: Convert merged PyTorch/HuggingFace model to GGUF format for Ollama

```python
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ModelConverterService:
    """Convert fine-tuned models to Ollama-compatible formats"""

    async def convert_to_gguf(
        self,
        merged_model_path: str,
        output_path: str,
        quantization: str = "Q4_K_M"
    ) -> Path:
        """
        Convert HuggingFace model to GGUF format

        Args:
            merged_model_path: Path to merged HuggingFace model
            output_path: Where to save GGUF file
            quantization: GGUF quantization type (Q4_K_M, Q5_K_M, Q8_0, etc.)

        Returns:
            Path to GGUF file
        """
        logger.info(f"Converting {merged_model_path} to GGUF...")

        try:
            # Use llama.cpp's convert.py script
            cmd = [
                "python3",
                "/path/to/llama.cpp/convert.py",
                merged_model_path,
                "--outfile", f"{output_path}/model.gguf",
                "--outtype", quantization
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            if result.returncode == 0:
                logger.info(f"✅ GGUF conversion successful")
                return Path(f"{output_path}/model.gguf")
            else:
                raise RuntimeError(f"GGUF conversion failed: {result.stderr}")

        except Exception as e:
            logger.error(f"❌ GGUF conversion error: {e}")
            raise
```

---

### Phase 5: Add MinIO Artifact Links to UI 🎨

**File**: `frontend/src/components/finetuning/DeploymentManager.tsx`

**Changes Required**:

#### Add MinIO Link Section (after line 235):
```typescript
{/* MinIO Artifacts */}
{model.minio_path && (
  <div className="mt-4 pt-4 border-t border-gray-200">
    <p className="text-sm font-medium text-gray-700 mb-2">📦 Model Artifacts:</p>
    <a
      href={`http://localhost:9001/browser/${model.minio_path}`}
      target="_blank"
      rel="noopener noreferrer"
      className="text-sm text-blue-600 hover:text-blue-800 underline flex items-center gap-1"
    >
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      View in MinIO
    </a>
  </div>
)}
```

#### Update API Response to Include MinIO Path

**Backend** (`finetuning_routes.py` lines 2750-2800):

```python
models_response = []
for m in models:
    # Get MinIO path from job
    job = db.query(FineTuningJob).filter(
        FineTuningJob.id == m.job_id
    ).first()

    minio_path = None
    if job and job.minio_checkpoint_path:
        minio_path = job.minio_checkpoint_path

    models_response.append({
        "id": str(m.id),
        "name": m.name,
        "version": m.version,
        "status": m.status,
        "base_model": m.base_model,
        "finetuning_method": m.finetuning_method,
        "ollama_model_name": m.ollama_model_name,
        "minio_path": minio_path,  # ← NEW: Include MinIO path
        ...
    })
```

#### Add Type Definition (DeploymentManager.tsx line 4):
```typescript
interface DeployedModel {
  id: string;
  name: string;
  version: string;
  status: string;
  ollama_model_name?: string;
  deployment_url?: string;
  base_model: string;
  finetuning_method: string;
  total_inferences?: number;
  avg_latency_ms?: number;
  last_inference_at?: string;
  created_at?: string;
  minio_path?: string;  // ← NEW: MinIO artifact path
}
```

---

## 🧪 Testing Plan

### Test 1: Verify Merge Step Works

```bash
# After implementing Phase 1, run training:
curl -X POST http://localhost:8000/api/v1/finetuning/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_merge_model",
    "base_model": "Qwen/Qwen2.5-1.5B",
    "finetuning_method": "PEFT",
    "dataset_id": "{dataset_id}"
  }'

# Check job completion:
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c \
  "SELECT name, status, minio_checkpoint_path FROM finetuning_jobs WHERE name = 'test_merge_model';"

# EXPECTED: minio_checkpoint_path should end with '/merged_model', not '/adapter_model'
```

### Test 2: Verify Merged Model in MinIO

```bash
# Login to MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
# Navigate to: AI-ML/Research/.../test_merge_model/final/
# EXPECTED FILES:
#   - adapter_model/ (folder with adapter weights)
#   - merged_model/ (folder with merged model - config.json, model.safetensors, etc.)
```

### Test 3: Verify Deployment Uses Merged Model

```bash
# Deploy model:
curl -X POST http://localhost:8000/api/v1/finetuning/models-public/{model_id}/approve \
  -H "Content-Type: application/json" \
  -d '{"approval_notes": "test merge"}'

# Test model behavior:
curl -s -X POST http://localhost:11434/api/generate \
  -d '{"model": "test-merge-v1", "prompt": "What is your name?", "stream": false}' | jq .

# EXPECTED: Response should match fine-tuned behavior, NOT say "I am Qwen" or "I am Claude"
```

### Test 4: Verify Chat UI Uses Fine-Tuned Model

1. Open Chat UI: http://localhost:3001
2. Select model: "Test Merge V1 (Ollama)"
3. Ask: "What is your name?"
4. **EXPECTED**: Model should give custom response based on training data
5. **NOT EXPECTED**: Should NOT say "I am Qwen" or "I am Claude"

---

## 📊 Success Criteria

- [ ] Training creates both `adapter_model/` and `merged_model/` folders in MinIO
- [ ] Database stores path to `merged_model`, not `adapter_model`
- [ ] Ollama Modelfile uses `FROM {merged_model_path}`, not `ADAPTER`
- [ ] Deployed model in Ollama responds with fine-tuned behavior
- [ ] Chat UI shows correct fine-tuned responses
- [ ] MinIO artifact links visible in Deployment Manager UI
- [ ] Model size in Ollama reflects merged model (may be larger than adapters)

---

## ⚠️ Important Considerations

### 1. Disk Space

Merged models are **MUCH LARGER** than adapters:

| Model Type | Size |
|------------|------|
| Base Model (Qwen 1.5B) | 3.0 GB |
| PEFT Adapters | 10-50 MB |
| **Merged Model** | **3.0 GB** (same as base) |

**Recommendation**: Ensure sufficient disk space in MinIO and Ollama

### 2. Quantization

For production, consider adding quantization:

```python
# After merging, quantize the model
from optimum.quanto import quantize, qint4

quantize(merged_model, weights=qint4)
merged_model.save_pretrained(quantized_dir)
```

### 3. Memory Requirements

Merging requires loading the full base model into memory:

- **Qwen 1.5B**: ~6 GB RAM (bf16)
- **Qwen 7B**: ~28 GB RAM (bf16)
- **Qwen 14B**: ~56 GB RAM (bf16)

**Recommendation**: Perform merging on machines with sufficient RAM or use CPU offloading

### 4. GPU Availability

Current training uses mock training - when enabling real training:

```python
# Check GPU availability before training
import torch
if not torch.cuda.is_available():
    logger.warning("No GPU available - training will be slow")
    # Consider using CPU or throwing error
```

---

## 🚀 Deployment Rollout

### Step 1: Implement Phase 1 (Merge Step)
- Update `peft_trainer.py` with merge logic
- Test with existing qwen_test_job
- Verify merged_model created in MinIO

### Step 2: Implement Phase 2 (Database)
- Add `merged_model_path` column
- Update training service to store merged path

### Step 3: Implement Phase 3 (Ollama Deployment)
- Update `ollama_deployment_service.py`
- Change `ADAPTER` to `FROM {merged_model_path}`
- Test deployment with merged model

### Step 4: Implement Phase 5 (UI)
- Add MinIO links to Deployment Manager
- Update API responses

### Step 5: Full Integration Test
- Run complete workflow: train → merge → deploy → chat
- Verify chat UI uses fine-tuned model

---

## 📝 Alternative Approaches

### Option 1: Keep Adapters, Fix Loading (NOT RECOMMENDED)

Instead of merging, fix adapter loading in Ollama:

**Pros**:
- Smaller storage (adapters only)
- Faster deployment

**Cons**:
- **Ollama ADAPTER directive is buggy/limited**
- Not all models support adapter loading
- Performance may be slower
- More complex deployment

**Verdict**: ❌ Not recommended - too many issues

### Option 2: Merge + GGUF Conversion (RECOMMENDED FOR PRODUCTION)

Merge adapters AND convert to GGUF:

**Pros**:
- Best Ollama compatibility
- Faster inference
- Smaller file size (quantized)

**Cons**:
- Requires llama.cpp installation
- Additional conversion step

**Verdict**: ✅ Recommended for production

### Option 3: Use vLLM Instead of Ollama

Deploy to vLLM which has better PEFT support:

**Pros**:
- Native PEFT adapter support
- Faster inference (GPU)
- Better scaling

**Cons**:
- Requires GPU
- More complex setup

**Verdict**: ⚙️ Consider for enterprise deployment

---

## 🔗 Related Documentation

- `/tmp/FINETUNED_MODEL_VERIFICATION_REPORT.md` - Detailed problem analysis
- `backend/app/services/finetuning/trainers/peft_trainer.py` - Training script
- `backend/app/services/ollama_deployment_service.py` - Deployment service
- [PEFT Documentation](https://huggingface.co/docs/peft) - Official PEFT guide
- [Ollama Modelfile](https://github.com/ollama/ollama/blob/main/docs/modelfile.md) - Ollama configuration

---

**Date**: 2025-12-18
**Author**: Claude Code AI Assistant
**Priority**: 🔴 P0 - CRITICAL BUG
**Estimated Effort**: 4-8 hours for complete implementation
**Impact**: HIGH - Directly affects fine-tuning functionality
