# Fine-Tuning Model Selection Architecture

**Date**: 2025-12-20
**Topic**: Ollama Models vs HuggingFace Models in Fine-Tuning Workflow
**User Question**: Are Ollama models placeholders or actual training sources? How does model downloading work? Best practices for GGUF/GGML model selection?

---

## Executive Summary

### Quick Answer

**Ollama models listed in the UI are PLACEHOLDERS (display names) only.**

The actual fine-tuning process:
1. ✅ **Downloads base model from HuggingFace** (full precision FP16/BF16)
2. ✅ **Trains using HuggingFace model** (not Ollama model)
3. ✅ **Merges LoRA adapters into base model**
4. ✅ **Deploys merged model to Ollama** (creates new Ollama model)

**Why?** GGUF/GGML quantized models (used by Ollama) **CANNOT be fine-tuned** - you need full-precision models from HuggingFace.

---

## Architecture Overview

### Training vs Inference Models

| Stage | Model Format | Source | Purpose |
|-------|--------------|--------|---------|
| **Training** | FP16/BF16 (full precision) | HuggingFace | Fine-tuning with LoRA/QLoRA |
| **Inference** | GGUF/GGML (quantized) | Ollama | Fast inference on CPU/consumer GPUs |

**Critical Difference**:
- **Training requires gradient computation** → Needs full-precision weights (FP16/BF16)
- **GGUF/GGML are quantized formats** (4-bit/8-bit) → Cannot compute gradients, only inference

---

## Fine-Tuning Workflow (Step-by-Step)

### Phase 1: Model Selection in UI (Admin → Fine-Tuning)

**User sees**: Ollama models listed in dropdown
```
qwen2.5:1.5b
qwen2.5:latest (7B)
mistral:latest
llama3.2:latest
```

**What this means**: These are **DISPLAY NAMES** mapped to HuggingFace models.

**Mapping** (from `model_registry_service.py:323-339`):
```python
mappings = {
    "qwen2.5:1.5b"          → "Qwen/Qwen2.5-1.5B-Instruct" (HuggingFace)
    "qwen2.5:7b"            → "Qwen/Qwen2.5-7B-Instruct"
    "mistral:7b"            → "mistralai/Mistral-7B-Instruct-v0.2"
    "llama2:7b"             → "meta-llama/Llama-2-7b-hf"
}
```

**User Action**: Select "qwen2.5:1.5b" → System translates to "Qwen/Qwen2.5-1.5B-Instruct"

---

### Phase 2: Training Preparation

**File**: `backend/app/services/finetuning/trainers/peft_trainer.py`

**What happens when you click "Start Training"**:

```python
# 1. Load tokenizer from HuggingFace
tokenizer = AutoTokenizer.from_pretrained(
    "Qwen/Qwen2.5-1.5B-Instruct",  # ← HuggingFace model ID
    trust_remote_code=True
)

# 2. Download base model from HuggingFace (NOT Ollama)
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-1.5B-Instruct",  # ← Downloads from HuggingFace
    quantization_config=quantization_config,  # 4-bit/8-bit for training
    device_map="auto",
    trust_remote_code=True
)
```

**Where is it downloaded to?**
- `/root/.cache/huggingface/hub/models--Qwen--Qwen2.5-1.5B-Instruct/`
- **Cached** - if already downloaded, reuses cached model
- **NOT from Ollama** - completely separate from Ollama's GGUF models

---

### Phase 3: LoRA/QLoRA Training

**File**: `peft_trainer.py:106-118`

```python
# Apply LoRA adapters to base model
lora_config = LoraConfig(
    r=16,                    # LoRA rank (trainable parameters)
    lora_alpha=32,           # Scaling factor
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],  # Which layers to adapt
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Output:
# trainable params: 4,194,304 || all params: 1,500,000,000 || trainable%: 0.28%
```

**Result**: Only 0.28% of parameters are trainable (LoRA adapters), rest frozen.

---

### Phase 4: Model Merging (CRITICAL STEP)

**File**: `peft_trainer.py:206-249`

**After training completes**, the system MUST merge LoRA adapters into the base model:

```python
# 1. Save adapter weights
adapter_dir = output_dir / "adapter_model"
model.save_pretrained(adapter_dir)  # ← Only saves LoRA weights (small file)

# 2. CRITICAL: Merge adapters into base model
logger.info("🔄 Merging PEFT adapters into base model...")

# Load base model again (without quantization for merge)
base_model_full = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-1.5B-Instruct",
    device_map="auto",
    trust_remote_code=True,
    torch_dtype=torch.bfloat16,  # ← Full precision for merge
    low_cpu_mem_usage=True
)

# Load PEFT model with adapters
peft_model = PeftModel.from_pretrained(
    base_model_full,
    str(adapter_dir),
    is_trainable=False
)

# Merge and unload - THIS IS THE KEY STEP
merged_model = peft_model.merge_and_unload()

# Save merged model
merged_dir = output_dir / "merged_model"
merged_model.save_pretrained(merged_dir)  # ← Full fine-tuned model
```

**Result**:
- `adapter_model/` - LoRA weights only (~20-50MB)
- `merged_model/` - Full fine-tuned model (~3GB for 1.5B, ~14GB for 7B)

**Why merge?**
- Adapter-only models require base model + adapter loading (complex)
- Merged models are standalone (easier deployment)
- Ollama deployment requires merged model

---

### Phase 5: Deployment to Ollama

**File**: `model_registry_service.py:249-321`

**After training completes**, user clicks "Deploy to Ollama":

```python
# 1. Check if merged model exists in workspace
workspace_merged_path = f"/workspace/finetuning/{job_id}/output/merged_model"

if os.path.exists(workspace_merged_path):
    logger.info("✅ Using merged fine-tuned model from workspace")
    model_reference = workspace_merged_path  # ← Local merged model
else:
    logger.warning("⚠️ Workspace not found, falling back to base model")
    model_reference = "qwen2.5:1.5b"  # ← Fallback to Ollama base model

# 2. Create Ollama Modelfile
modelfile = f"""
FROM {model_reference}

# Fine-tuned model configuration
# Original base: Qwen/Qwen2.5-1.5B-Instruct
# Fine-tuning method: peft_lora
# Version: v1.0.0

SYSTEM "You are a specialized AI assistant based on Qwen/Qwen2.5-1.5B-Instruct. This model was fine-tuned using PEFT_LORA method."

# Model parameters
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1
"""

# 3. Register with Ollama
response = await self.client.post(
    f"{OLLAMA_BASE_URL}/api/create",
    json={
        "name": "customer-support-qa-v1.0.0",  # ← New Ollama model name
        "modelfile": modelfile
    }
)
```

**Result**: New Ollama model created from fine-tuned weights!

```bash
$ ollama list
NAME                           SIZE    MODIFIED
customer-support-qa-v1.0.0     3.0 GB  5 minutes ago  ← Fine-tuned model
qwen2.5:1.5b                   934 MB  2 days ago     ← Original base model
```

---

## Ollama Models: Placeholder vs Training Source

### What Happens with Ollama Models in the UI?

| User Action | Backend Action | Source |
|-------------|----------------|--------|
| Select "qwen2.5:1.5b" in UI | Maps to "Qwen/Qwen2.5-1.5B-Instruct" | HuggingFace |
| Click "Start Training" | Downloads from HuggingFace (if not cached) | HuggingFace Hub |
| Training runs | Uses HuggingFace model (FP16/BF16) | Cached HuggingFace |
| Training completes | Merges LoRA into HuggingFace model | Local workspace |
| Deploy to Ollama | Creates new Ollama model from merged weights | Workspace → Ollama |

### Are Ollama Models Used for Training?

**NO - Ollama models are NEVER used for training.**

**Why?**
1. **GGUF/GGML formats are quantized** (4-bit/8-bit) → Cannot compute gradients
2. **Fine-tuning requires backpropagation** → Needs full-precision weights (FP16/BF16)
3. **HuggingFace models are full-precision** → Suitable for training

**Ollama models are ONLY used for**:
- Inference in the chat UI (fast, low memory)
- Fallback if merged model workspace is cleaned up before deployment

---

## HuggingFace Model Caching

### First Time Training

```bash
# User selects "qwen2.5:1.5b" in UI
# Backend maps to "Qwen/Qwen2.5-1.5B-Instruct"

# Download from HuggingFace
Downloading: 100% ████████████████ 2.9GB/2.9GB [00:15:23<00:00, 3.14MB/s]

# Saved to cache:
/root/.cache/huggingface/hub/models--Qwen--Qwen2.5-1.5B-Instruct/
├── config.json
├── model.safetensors
├── tokenizer.json
├── tokenizer_config.json
└── special_tokens_map.json
```

### Subsequent Training

```bash
# Same model selected again
# Backend checks cache first

Loading cached model from /root/.cache/huggingface/hub/...
✅ Model loaded in 2 seconds (from cache, no download)
```

**Cache Persistence**:
- Stored in Docker volume: `huggingface_cache:/root/.cache/huggingface`
- Persists across container restarts
- Only downloads once per unique model

---

## GGUF vs GGML Models: Training Perspective

### Can You Train GGUF/GGML Models?

**NO - GGUF/GGML models CANNOT be fine-tuned.**

### Why?

| Format | Precision | Trainable? | Use Case |
|--------|-----------|------------|----------|
| **FP16/BF16** | 16-bit float | ✅ YES | Training, fine-tuning |
| **FP32** | 32-bit float | ✅ YES | Research, high-precision training |
| **8-bit (INT8)** | 8-bit integer | ❌ NO (limited) | QLoRA training (special case) |
| **4-bit (GGUF/GGML)** | 4-bit quantized | ❌ NO | Inference only |
| **2-bit (GGUF)** | 2-bit quantized | ❌ NO | Inference only |

**Gradient Computation Requirements**:
- Training requires **differentiable operations**
- GGUF/GGML use **lookup tables** (non-differentiable)
- Result: **Cannot backpropagate through quantized weights**

### Special Case: QLoRA (4-bit Training)

**QLoRA is NOT the same as GGUF 4-bit!**

| Method | Quantization | Training | Gradients |
|--------|--------------|----------|-----------|
| **GGUF 4-bit** | Asymmetric lookup table | ❌ NO | Non-differentiable |
| **QLoRA 4-bit** | NormalFloat4 (symmetric) | ✅ YES | Differentiable via dequantization |

**How QLoRA works**:
```python
# QLoRA uses NF4 (NormalFloat4) quantization
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,  # Nested quantization
    bnb_4bit_quant_type="nf4",        # ← NormalFloat4 (NOT GGUF)
    bnb_4bit_compute_dtype=torch.bfloat16  # Compute in BF16
)

# During forward pass:
# 1. Dequantize 4-bit weights to BF16
# 2. Compute in BF16
# 3. Compute gradients in BF16
# 4. Update LoRA adapters (stored in FP16)
# 5. Base model stays frozen in 4-bit
```

**Result**: QLoRA trains LoRA adapters in FP16 while keeping base model in 4-bit (memory efficient).

---

## Best Practices for Model Selection

### For Fine-Tuning

#### 1. Choose Base Model Size Based on GPU Memory

| Base Model | Size | Quantization | VRAM Required | Recommended GPU |
|------------|------|--------------|---------------|-----------------|
| **Qwen 2.5 1.5B** | 1.5B params | 4-bit QLoRA | ~3-4 GB | RTX 3060 (12GB) |
| **Qwen 2.5 7B** | 7B params | 4-bit QLoRA | ~10-12 GB | RTX 3080 (16GB) / A4000 |
| **Mistral 7B** | 7B params | 4-bit QLoRA | ~10-12 GB | RTX 3080 (16GB) |
| **Llama 2 13B** | 13B params | 4-bit QLoRA | ~18-20 GB | RTX 4090 (24GB) / A5000 |

**Example** (from your system):
```bash
# Available GPUs
NVIDIA RTX A4000 (16 GB VRAM)

# Recommended Models for Fine-Tuning:
✅ qwen2.5:1.5b  (fits comfortably with batch_size=4)
✅ qwen2.5:7b    (fits with batch_size=2)
⚠️  llama2:13b   (tight fit, batch_size=1)
❌ llama2:70b    (exceeds VRAM)
```

#### 2. Choose Quantization Strategy

| Method | VRAM Usage | Training Speed | Quality | Use Case |
|--------|------------|----------------|---------|----------|
| **4-bit QLoRA** | 3-4 GB | Fast | Good | Consumer GPUs (RTX 3060+) |
| **8-bit** | 6-8 GB | Medium | Better | Mid-range GPUs (RTX 3080+) |
| **FP16 (no quant)** | 12-16 GB | Slow | Best | High-end GPUs (A100, H100) |

**Recommendation**: **4-bit QLoRA** for consumer GPUs (best VRAM/quality trade-off)

```python
# In UI: Select quantization
Quantization: 4-bit  ← Recommended for RTX A4000

# Backend applies:
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16
)
```

#### 3. Choose LoRA Hyperparameters

| Parameter | Small Models (1.5B) | Medium Models (7B) | Large Models (13B+) |
|-----------|---------------------|--------------------|--------------------|
| **LoRA r** | 8-16 | 16-32 | 32-64 |
| **LoRA alpha** | 16-32 | 32-64 | 64-128 |
| **Learning rate** | 2e-4 | 1e-4 | 5e-5 |
| **Batch size** | 4-8 | 2-4 | 1-2 |

**Example** (Qwen 2.5 1.5B on RTX A4000):
```json
{
  "lora_r": 16,
  "lora_alpha": 32,
  "learning_rate": 2e-4,
  "batch_size": 4,
  "gradient_accumulation_steps": 4,
  "num_epochs": 3
}
```

---

## Common Misconceptions

### Misconception 1: Ollama Models are Used for Training

**WRONG** ❌
```
User thinks:
"I selected qwen2.5:1.5b in UI, so it uses Ollama's GGUF model for training"

Reality:
Ollama model name is PLACEHOLDER → Mapped to HuggingFace model ID → Downloads FP16 model from HuggingFace
```

**CORRECT** ✅
```
UI Selection → Backend Mapping → HuggingFace Download → Training → Merge → Deploy to Ollama
qwen2.5:1.5b → Qwen/Qwen2.5-1.5B-Instruct → Download FP16 → Train with QLoRA → Merge adapters → Create new Ollama model
```

### Misconception 2: GGUF Models Can Be Fine-Tuned

**WRONG** ❌
```
"I can convert GGUF to safetensors and fine-tune it"

Reality:
GGUF quantization is IRREVERSIBLE - information loss during quantization cannot be recovered
```

**CORRECT** ✅
```
Training workflow:
1. Start with FP16/BF16 model from HuggingFace
2. Train with QLoRA (4-bit during forward pass, gradients in FP16)
3. Merge adapters into FP16 base model
4. (Optional) Convert merged model to GGUF for deployment
```

### Misconception 3: Cached Models are in GGUF Format

**WRONG** ❌
```
"HuggingFace cache stores GGUF models like Ollama"

Reality:
HuggingFace models are stored in safetensors/bin format (FP16/BF16)
Ollama models are stored in GGUF format (quantized)
These are SEPARATE, INDEPENDENT caches
```

**CORRECT** ✅
```
HuggingFace Cache:
/root/.cache/huggingface/hub/models--Qwen--Qwen2.5-1.5B-Instruct/
├── model.safetensors  ← FP16 weights (2.9 GB)

Ollama Cache:
/root/.ollama/models/blobs/
├── sha256-abc123...   ← GGUF 4-bit quantized (934 MB)

COMPLETELY DIFFERENT FILES!
```

---

## Workflow Diagram

### Complete Fine-Tuning Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                              │
│  Admin → Fine-Tuning → Select Model: qwen2.5:1.5b                   │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKEND MAPPING                                │
│  qwen2.5:1.5b → Qwen/Qwen2.5-1.5B-Instruct (HuggingFace ID)        │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────────┐
│                  HUGGINGFACE DOWNLOAD                               │
│  Check cache: /root/.cache/huggingface/hub/                        │
│  If not cached: Download from HuggingFace Hub                      │
│  Format: safetensors (FP16/BF16)                                   │
│  Size: ~2.9 GB                                                     │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    LORA TRAINING                                    │
│  1. Load model with QLoRA (4-bit)                                  │
│  2. Add LoRA adapters (r=16, alpha=32)                             │
│  3. Train for 3 epochs                                             │
│  4. Save adapter weights (~20-50 MB)                               │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    MODEL MERGING                                    │
│  1. Load base model (FP16/BF16)                                    │
│  2. Load LoRA adapters                                             │
│  3. merged_model = peft_model.merge_and_unload()                   │
│  4. Save merged model (~3 GB)                                      │
│  Location: /workspace/finetuning/{job_id}/output/merged_model/    │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────────┐
│                  OLLAMA DEPLOYMENT                                  │
│  1. Create Ollama Modelfile (references merged model)              │
│  2. POST /api/create to Ollama                                     │
│  3. New Ollama model created: customer-support-qa-v1.0.0           │
│  4. Available in chat UI model selector                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Recommendations

### 1. Model Selection Strategy

**For Customer Support / Domain-Specific Tasks**:
```
✅ Use: qwen2.5:1.5b (fast, efficient, good quality)
✅ Method: 4-bit QLoRA
✅ Epochs: 3-5
✅ Dataset: 500-2000 examples

Expected VRAM: 3-4 GB
Expected Training Time: 30-60 minutes (RTX A4000)
```

**For Complex Reasoning / High Quality**:
```
✅ Use: qwen2.5:7b (better reasoning, more knowledge)
✅ Method: 4-bit QLoRA
✅ Epochs: 3
✅ Dataset: 1000-5000 examples

Expected VRAM: 10-12 GB
Expected Training Time: 2-4 hours (RTX A4000)
```

### 2. Caching Strategy

**ALWAYS rely on HuggingFace cache**:
- First download takes 10-20 minutes
- Subsequent training starts in <2 seconds
- Cache persists across restarts (Docker volume)

**Clean cache only when**:
- Disk space critical
- Model never used again
- New model version available

### 3. Deployment Strategy

**After Training Completes**:
1. ✅ **Verify merged model exists**: Check `/workspace/finetuning/{job_id}/output/merged_model/`
2. ✅ **Test merged model locally**: Run inference test before deployment
3. ✅ **Deploy to Ollama**: Creates new Ollama model from merged weights
4. ✅ **Preserve workspace**: Keep workspace until deployment confirmed (for redeployment)

**Workspace Cleanup**:
- ⚠️ **Only clean after successful deployment**
- Workspace size: ~5-10 GB per job
- Keep recent jobs (last 5-10) for rollback capability

---

## Summary

| Question | Answer |
|----------|--------|
| **Are Ollama models used for training?** | ❌ NO - Only as display names/placeholders |
| **What models are actually used?** | ✅ HuggingFace models (FP16/BF16 from HuggingFace Hub) |
| **Are models downloaded dynamically?** | ✅ YES - First time downloads, then cached |
| **Can I train GGUF/GGML models?** | ❌ NO - Only inference-ready, cannot compute gradients |
| **What's the difference between QLoRA and GGUF 4-bit?** | QLoRA uses NF4 (trainable), GGUF uses lookup tables (inference only) |
| **Where are HuggingFace models cached?** | `/root/.cache/huggingface/hub/` (Docker volume) |
| **How does Ollama deployment work?** | Merged model → Ollama Modelfile → New Ollama model |
| **Best model for RTX A4000 (16GB)?** | qwen2.5:1.5b (4-bit QLoRA) or qwen2.5:7b (4-bit QLoRA) |

---

## Technical Details for Developers

### Model Download Process

```python
# When user selects model in UI
selected_model = "qwen2.5:1.5b"

# Backend maps to HuggingFace ID
hf_model_id = model_mappings.get(selected_model, "Qwen/Qwen2.5-1.5B-Instruct")

# AutoModelForCausalLM.from_pretrained() does:
# 1. Check cache: /root/.cache/huggingface/hub/models--Qwen--Qwen2.5-1.5B-Instruct/
# 2. If exists: Load from cache (fast)
# 3. If not: Download from HuggingFace Hub
#    - Downloads config.json, tokenizer files, model weights
#    - Saves to cache
#    - Returns loaded model

model = AutoModelForCausalLM.from_pretrained(
    hf_model_id,
    quantization_config=quantization_config,
    device_map="auto",
    trust_remote_code=True,
    cache_dir="/root/.cache/huggingface"  # ← Cache location
)
```

### Quantization Formats Comparison

| Format | Bits | Size (1.5B) | Size (7B) | Training | Inference | Gradients |
|--------|------|-------------|-----------|----------|-----------|-----------|
| **FP32** | 32 | 6 GB | 28 GB | ✅ YES | ✅ YES | ✅ YES |
| **FP16/BF16** | 16 | 3 GB | 14 GB | ✅ YES | ✅ YES | ✅ YES |
| **QLoRA 4-bit** | 4 (NF4) | 900 MB | 4 GB | ✅ YES | ✅ YES | ✅ YES (via dequant) |
| **GGUF Q4_K_M** | 4 (lookup) | 800 MB | 3.5 GB | ❌ NO | ✅ YES | ❌ NO |
| **GGUF Q2_K** | 2 (lookup) | 500 MB | 2.3 GB | ❌ NO | ✅ YES | ❌ NO |

### LoRA vs Full Fine-Tuning

| Method | Trainable Params | Memory | Training Time | Quality |
|--------|------------------|--------|---------------|---------|
| **Full Fine-Tuning** | 100% (1.5B) | 12-16 GB | 10x | Best |
| **LoRA (r=16)** | 0.28% (4M) | 3-4 GB | 1x | Good |
| **LoRA (r=32)** | 0.56% (8M) | 4-5 GB | 1.5x | Better |
| **LoRA (r=64)** | 1.12% (16M) | 5-6 GB | 2x | Best (LoRA) |

**Recommendation**: Start with r=16 (fastest), increase to r=32 if quality insufficient.

---

## Conclusion

✅ **Ollama models are display names ONLY** - actual training uses HuggingFace models
✅ **Models are downloaded from HuggingFace Hub** and cached locally
✅ **GGUF/GGML models CANNOT be fine-tuned** - only for inference
✅ **QLoRA 4-bit is NOT GGUF 4-bit** - different quantization methods
✅ **Merged model is deployed to Ollama** - creates new Ollama model
✅ **Best choice for RTX A4000**: qwen2.5:1.5b or qwen2.5:7b with 4-bit QLoRA

**Workflow**: UI Selection → HuggingFace Download → QLoRA Training → Merge Adapters → Ollama Deployment

---

**Last Updated**: 2025-12-20
**Status**: Complete architecture documentation
**User Question Answered**: YES - Ollama models are placeholders, actual training uses HuggingFace models downloaded dynamically or from cache

