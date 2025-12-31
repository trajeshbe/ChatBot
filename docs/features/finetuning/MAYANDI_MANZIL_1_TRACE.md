# Training Job Trace: mayandi_manzil_1

**Job ID**: `5e82184c-5859-4c56-8447-a9a902a68ee1`
**Job Name**: `mayandi_manzil_1`
**Current Time**: 2025-12-23 17:00:22 UTC
**Status**: ⏳ **RUNNING** - Model Loading Phase

---

## 📊 Job Overview

| Field | Value |
|-------|-------|
| **Status** | running |
| **Progress** | 0% |
| **Training Stage** | training |
| **Train Loss** | Not yet available |
| **Base Model** | Qwen/Qwen2.5-1.5B-Instruct |
| **Method** | PEFT (LoRA/QLoRA) |
| **Dataset** | mayandi_manzil (104 samples) |
| **Created At** | 2025-12-23 16:58:17 UTC |
| **Started At** | 2025-12-23 16:58:19 UTC |
| **Elapsed Time** | ~2 minutes |

---

## 🔧 Hyperparameters

```json
{
  "learning_rate": 0.0002,
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

---

## 📦 Dataset Information

**Dataset ID**: `09a719ed-7bec-4e1a-898a-4e182646a312`
**Dataset Name**: `mayandi_manzil`

| Property | Value |
|----------|-------|
| **Format** | chat (OpenAI/Anthropic messages format) |
| **Samples** | 104 |
| **Is Valid** | ✅ Yes |
| **Preprocessing Status** | completed |
| **Uploaded At** | 2025-12-23 16:36:29 UTC |

**MinIO Path**: `technology/itm11/global/admin/finetuning/datasets/mayandi_manzil/09a719ed-7bec-4e1a-898a-4e182646a312/mayandi_manzil_dataset.jsonl`

---

## 🐳 Container Status

**Container ID**: `f0e70b8fb48f`
**Container Name**: `finetuning-5e82184c-5859-4c56-8447-a9a902a68ee1`
**Status**: ✅ Up About a minute (healthy)

---

## 📝 Training Log (Latest 50 lines)

```
2025-12-23 16:58:23,363 - __main__ - INFO - ================================================================================
2025-12-23 16:58:23,363 - __main__ - INFO - 🔥 PEFT Fine-Tuning Trainer Started
2025-12-23 16:58:23,363 - __main__ - INFO - ================================================================================
2025-12-23 16:58:23,363 - __main__ - INFO - 📄 Config: {
  "job_id": "5e82184c-5859-4c56-8447-a9a902a68ee1",
  "base_model": "Qwen/Qwen2.5-1.5B-Instruct",
  "finetuning_method": "peft",
  "training_objective": "qa",
  "dataset_id": "09a719ed-7bec-4e1a-898a-4e182646a312",
  "dataset_path": "/workspace/finetuning/5e82184c-5859-4c56-8447-a9a902a68ee1/input",
  "dataset_minio_path": "technology/itm11/global/admin/finetuning/datasets/mayandi_manzil/09a719ed-7bec-4e1a-898a-4e182646a312/mayandi_manzil_dataset.jsonl",
  "hyperparameters": {
    "learning_rate": 0.0002,
    "num_epochs": 3,
    "batch_size": 4,
    "gradient_accumulation_steps": 4,
    "lora_r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05,
    "target_modules": ["q_proj", "v_proj"],
    "warmup_steps": 100,
    "max_seq_length": 2048
  },
  "output_dir": "/workspace/finetuning/5e82184c-5859-4c56-8447-a9a902a68ee1/output",
  "checkpoint_dir": "/workspace/finetuning/5e82184c-5859-4c56-8447-a9a902a68ee1/output/checkpoints",
  "log_dir": "/workspace/finetuning/5e82184c-5859-4c56-8447-a9a902a68ee1/logs"
}

2025-12-23 16:58:23,364 - __main__ - INFO - 🔧 Setting up training...
2025-12-23 16:58:27,943 - __main__ - INFO - ✅ All dependencies loaded
2025-12-23 16:58:27,943 - __main__ - INFO - 🎯 Base Model: Qwen/Qwen2.5-1.5B-Instruct
2025-12-23 16:58:27,943 - __main__ - INFO - 🔢 Quantization: 4bit
2025-12-23 16:58:27,944 - __main__ - INFO - 📊 Dataset: /workspace/finetuning/5e82184c-5859-4c56-8447-a9a902a68ee1/input
2025-12-23 16:58:27,944 - __main__ - INFO - Loading tokenizer...
2025-12-23 16:58:32,117 - __main__ - INFO - Setting up 4-bit quantization (QLoRA)...
2025-12-23 16:58:32,118 - __main__ - INFO - Loading model Qwen/Qwen2.5-1.5B-Instruct...
```

---

## ⏱️ Timeline

| Time (UTC) | Event | Duration |
|------------|-------|----------|
| 16:58:17 | Job created | - |
| 16:58:19 | Training stage started | +2s |
| 16:58:23 | Container started, trainer initialized | +4s |
| 16:58:27 | Dependencies loaded | +4s |
| 16:58:32 | **Model loading started** | +5s |
| **Current** | **16:58:32 → 17:00:22** | **~1m 50s (model loading)** |

---

## 📈 Current Stage Analysis

### Stage: Model Loading (in progress)

**What's happening**:
- Loading Qwen/Qwen2.5-1.5B-Instruct model from HuggingFace
- Model size: ~2.9 GB (1.5B parameters)
- Using 4-bit quantization (QLoRA) to reduce VRAM usage
- Model will be loaded into GPU memory

**Expected duration**:
- Based on Training52: **~5 minutes** total for model loading
- Current elapsed: ~1m 50s
- **Estimated remaining: ~3 minutes**

**Next stages**:
1. ✅ Dependencies loaded (completed)
2. ✅ Tokenizer loaded (completed)
3. ⏳ **Model loading** (in progress) ← **CURRENT**
4. ⏳ Dataset preparation (pending)
5. ⏳ Training (pending) - should complete in ~5-10 seconds with 104 samples
6. ⏳ Checkpoint save (pending)
7. ⏳ Upload to MinIO (pending)
8. ⏳ Model registration (pending)

---

## 🎯 Expected Outcome

Based on Training52 (similar configuration):

| Metric | Training52 | Expected for mayandi_manzil_1 |
|--------|------------|-------------------------------|
| **Dataset Size** | 9 samples | 104 samples |
| **Model Loading** | ~5 minutes | ~5 minutes |
| **Training Time** | ~5 seconds | ~10-15 seconds (more data) |
| **Total Time** | ~5m 23s | **~5-6 minutes** |
| **Final Model Size** | 2.9 GB | 2.9 GB |
| **Adapter Size** | 8.3 MB | ~8-10 MB |

---

## 🔍 Monitoring Commands

### Watch Container Logs (Live)
```bash
docker logs -f finetuning-5e82184c-5859-4c56-8447-a9a902a68ee1
```

### Check Job Status
```bash
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c \
  "SELECT name, status, progress, training_stage, train_loss \
   FROM finetuning_jobs WHERE id='5e82184c-5859-4c56-8447-a9a902a68ee1';"
```

### Check Container Status
```bash
docker ps | grep mayandi
```

### Check GPU Usage (if available)
```bash
docker exec finetuning-5e82184c-5859-4c56-8447-a9a902a68ee1 nvidia-smi
```

---

## ⚙️ System Resources

**Workspace Path**: `/workspace/finetuning/5e82184c-5859-4c56-8447-a9a902a68ee1/`

### Directory Structure:
```
/workspace/finetuning/5e82184c-5859-4c56-8447-a9a902a68ee1/
├── input/                     # Dataset location
├── output/                    # Training outputs
│   ├── adapter_model/        # LoRA adapters (will be created)
│   └── checkpoints/          # Training checkpoints
└── logs/                      # Training logs
```

---

## 🚨 Known Issues / Watch For

1. **Chat Format Dataset**: This is the first training with the new chat format support
   - Format: OpenAI/Anthropic messages (role/content pairs)
   - Preprocessor: ChatFormatter class (just added)
   - Should work correctly as dataset validated successfully

2. **Larger Dataset**: 104 samples vs 9 samples in Training52
   - Expect slightly longer training time (~10-15s vs 5s)
   - More robust fine-tuning with more examples

3. **Auto-Merge Status**: After Training52, we fixed the deployment pipeline
   - Merge should work automatically
   - Deployment should work (using Docker exec + CLI now)

---

## ✅ Next Steps (After Training Completes)

1. **Wait for completion** (~3-4 more minutes)
2. **Verify adapter upload** to MinIO
3. **Check model registration** in database
4. **Merge adapters** (should be automatic)
5. **Deploy to Ollama** (click button in UI)
6. **Test the model** in chat UI with queries like:
   - "What is Mayandi_Manzil?"
   - "What dishes do you serve?"
   - "Do you have organic certification?"

---

## 📊 Status Summary

**Current State**: ⏳ **Training in progress - Model loading phase**

**Estimated Time Remaining**: ~3-4 minutes (total ~5-6 minutes)

**Health**: ✅ Container healthy, no errors detected

**Recommendation**: Wait for completion. Model loading is the longest phase (5 min), then training will be very fast (~10-15 seconds).

---

**Trace Generated**: 2025-12-23 17:00:22 UTC
**Next Update**: Check logs in 2-3 minutes for training progress
