# End-to-End Fine-Tuning Architecture & Implementation

> **Version**: 1.0.0
> **Date**: 2025-12-22
> **Status**: Production Ready
> **Author**: Enterprise RAG Team

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [System Components](#system-components)
4. [Data Flow](#data-flow)
5. [Implementation Details](#implementation-details)
6. [Container Architecture](#container-architecture)
7. [Database Schema](#database-schema)
8. [API Endpoints](#api-endpoints)
9. [Training Pipeline](#training-pipeline)
10. [Auto-Merge System](#auto-merge-system)
11. [Deployment Pipeline](#deployment-pipeline)
12. [Troubleshooting Guide](#troubleshooting-guide)
13. [Performance & Scaling](#performance--scaling)
14. [Security & Best Practices](#security--best-practices)

---

## Overview

### What is This System?

The Enterprise RAG Fine-Tuning System enables **distributed, GPU-accelerated fine-tuning** of Large Language Models with:

- **Automated Pipeline**: From dataset upload → training → merge → deployment → inference
- **Multi-Method Support**: PEFT (LoRA/QLoRA), Full Fine-Tuning, RLHF (PPO/GRPO)
- **GPU Management**: Dynamic GPU allocation, queue management, resource pooling
- **Model Lifecycle**: Version control, evaluation, approval workflow, deprecation
- **Production Ready**: Monitoring, metrics, audit logs, error handling

### Key Features

| Feature | Description |
|---------|-------------|
| **Distributed Training** | Celery-based task queue with GPU container orchestration |
| **LoRA/QLoRA Support** | Memory-efficient fine-tuning with PEFT |
| **Auto-Merge** | Automatic adapter merging after training completes |
| **Ollama Deployment** | One-click deployment to Ollama for inference |
| **Model Registry** | Central registry with versioning and metadata |
| **Evaluation** | Automated quality metrics (perplexity, BLEU, ROUGE) |
| **Audit Trail** | Complete history of training, merges, deployments |

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ Fine-Tuning  │  │ Governance & │  │  Model       │             │
│  │     Hub      │  │    Audit     │  │  Catalog     │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Backend API (FastAPI)                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Fine-Tuning Routes: /api/v1/finetuning/*                     │  │
│  │  - POST /jobs           (Create job)                         │  │
│  │  - POST /jobs/{id}/submit (Submit to queue)                 │  │
│  │  - GET  /jobs/{id}      (Monitor progress)                  │  │
│  │  - POST /models/{id}/merge (Manual merge)                   │  │
│  │  - POST /models/{id}/deploy (Deploy to Ollama)              │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Celery Task Queue (Redis)                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ run_finetuning_job(job_id)                                   │  │
│  │   1. Validate dataset                                        │  │
│  │   2. Create GPU container                                    │  │
│  │   3. Monitor training progress                               │  │
│  │   4. Register model                                          │  │
│  │   5. Trigger auto-merge                                      │  │
│  │   6. Update database                                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│              GPU Training Container (Docker)                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Image: chatbot-finetuning-trainer:v1.0.4                     │  │
│  │                                                              │  │
│  │ peft_trainer.py:                                             │  │
│  │   1. Load base model (quantized if QLoRA)                   │  │
│  │   2. Configure LoRA adapters                                │  │
│  │   3. Train with HuggingFace Trainer                         │  │
│  │   4. Save adapter weights                                   │  │
│  │   5. Merge adapters with base model                         │  │
│  │   6. Upload to MinIO                                        │  │
│  │   7. Report back to celery                                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  Auto-Merge System (Celery-Worker)                  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ auto_merge.py:                                               │  │
│  │   1. Check if container already merged                      │  │
│  │   2. If not, load base model + adapters                     │  │
│  │   3. Merge using PEFT                                       │  │
│  │   4. Save merged model                                      │  │
│  │   5. Update DB: status='merged'                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Deployment (Ollama Service)                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ ollama_deployment_service.py:                                │  │
│  │   1. Create Modelfile                                        │  │
│  │   2. Convert to GGUF format                                 │  │
│  │   3. Register with Ollama                                   │  │
│  │   4. Update model registry                                  │  │
│  │   5. Model ready for inference                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## System Components

### 1. Frontend Components

#### Fine-Tuning Hub (`/finetuning-hub`)
- **Purpose**: Create and manage fine-tuning jobs
- **Features**:
  - Dataset upload/selection
  - Base model selection
  - Hyperparameter configuration (learning rate, epochs, batch size, LoRA params)
  - Training method selection (PEFT, Full, RLHF)
  - Job submission and monitoring
- **File**: `frontend/src/pages/finetuning-hub.tsx`

#### Governance & Audit (`/governance-audit`)
- **Purpose**: Model lifecycle management and audit trail
- **Features**:
  - Model registry with status badges
  - Merge/deploy actions
  - Evaluation metrics display
  - Approval workflow
  - Usage statistics
- **File**: `frontend/src/pages/governance-audit.tsx`

#### Model Catalog
- **Purpose**: Browse and select fine-tuned models for inference
- **Features**:
  - Model cards with metadata
  - Performance metrics
  - Deployment status
  - Quick deployment actions

### 2. Backend Services

#### Fine-Tuning Service (`FinetuningService`)
- **Location**: `backend/app/services/finetuning/finetuning_service.py`
- **Responsibilities**:
  - Job creation and validation
  - Hyperparameter management
  - Job submission to Celery queue
  - Progress tracking
  - Error handling

#### GPU Pool Manager (`GPUPoolManager`)
- **Location**: `backend/app/services/finetuning/gpu_pool_manager.py`
- **Responsibilities**:
  - GPU availability detection
  - Container creation with GPU allocation
  - Resource monitoring
  - Queue management for multiple jobs

#### Model Merge Service (`ModelMergeService`)
- **Location**: `backend/app/services/finetuning/model_merge_service.py`
- **Responsibilities**:
  - Manual merge trigger (UI button)
  - PEFT adapter merging
  - Merged model storage
  - Status updates

#### Ollama Deployment Service (`OllamaDeploymentService`)
- **Location**: `backend/app/services/ollama_deployment_service.py`
- **Responsibilities**:
  - Modelfile generation
  - GGUF conversion (if needed)
  - Ollama registration
  - Deployment verification

#### Model Registry Service (`ModelRegistryService`)
- **Location**: `backend/app/services/finetuning/model_registry_service.py`
- **Responsibilities**:
  - Model registration after training
  - Version management
  - Metadata storage
  - Lifecycle state tracking

### 3. Celery Tasks

#### Main Training Task (`run_finetuning_job`)
- **Location**: `backend/app/tasks/finetuning_tasks.py`
- **Flow**:
  1. **Validation**: Check dataset, base model, GPU availability
  2. **Container Setup**: Create Docker container with GPU access
  3. **Training Launch**: Execute `peft_trainer.py` in container
  4. **Progress Monitoring**: WebSocket updates to database
  5. **Model Registration**: Create entry in `finetuned_models` table
  6. **Auto-Merge**: Call `auto_merge_lora_adapters()`
  7. **Cleanup**: Release GPU, update status

#### Auto-Merge Task (`auto_merge_lora_adapters`)
- **Location**: `backend/app/tasks/auto_merge.py`
- **Flow**:
  1. **Check Container Merge**: See if training container already merged
  2. **Path Detection**: Look for merged_model or adapter_model
  3. **Load Models**: Base model + PEFT adapters
  4. **Merge**: `model.merge_and_unload()`
  5. **Save**: Store merged model to MinIO
  6. **Update DB**: Set status='merged', populate merged_model_path

### 4. Training Container

#### PEFT Trainer (`peft_trainer.py`)
- **Location**: `backend/app/services/finetuning/trainers/peft_trainer.py`
- **Image**: `chatbot-finetuning-trainer:v1.0.4`
- **Flow**:
  1. **Load Dataset**: From MinIO or local path
  2. **Load Base Model**: With quantization (4-bit/8-bit)
  3. **Configure LoRA**: Set r, alpha, dropout, target_modules
  4. **Prepare Model**: `prepare_model_for_kbit_training()`
  5. **Apply LoRA**: `get_peft_model()`
  6. **Train**: HuggingFace `Trainer` with callbacks
  7. **Save Adapters**: To `/workspace/.../output/adapter_model`
  8. **Container Merge**: Merge adapters with base model
  9. **Save Merged**: To `/workspace/.../output/merged_model`
  10. **Upload**: Copy to MinIO
  11. **Report**: Update database via WebSocket/HTTP

---

## Data Flow

### Complete Training Flow (Step-by-Step)

```
USER ACTION: Click "Start Training" in Fine-Tuning Hub
    │
    ▼
[1] POST /api/v1/finetuning/jobs/{id}/submit
    │
    ├─→ Backend validates job exists
    ├─→ Checks GPU availability
    ├─→ Submits to Celery queue
    │
    ▼
[2] Celery Worker picks up run_finetuning_job(job_id)
    │
    ├─→ Loads job from database
    ├─→ Validates dataset (checks MinIO path)
    ├─→ Validates base model (checks HuggingFace)
    ├─→ Prepares hyperparameters
    │
    ▼
[3] GPU Container Creation
    │
    ├─→ docker run --gpus all chatbot-finetuning-trainer:v1.0.4
    ├─→ Mount: /workspace/finetuning/{job_id}
    ├─→ Env vars: JOB_ID, BASE_MODEL, DATASET_PATH, HYPERPARAMS
    ├─→ Command: python peft_trainer.py
    │
    ▼
[4] Training Container Execution
    │
    ├─→ [Stage 1] Loading tokenizer
    │   └─→ Updates DB: training_stage='loading_tokenizer'
    │
    ├─→ [Stage 2] Loading model
    │   ├─→ Downloads from HuggingFace (cached after first run)
    │   ├─→ Applies quantization (if QLoRA)
    │   └─→ Updates DB: training_stage='loading_model'
    │
    ├─→ [Stage 3] Configuring LoRA
    │   ├─→ target_modules = ["q_proj", "v_proj"]
    │   ├─→ lora_r=16, lora_alpha=32, lora_dropout=0.05
    │   └─→ Updates DB: training_stage='configuring_lora'
    │
    ├─→ [Stage 4] Loading dataset
    │   ├─→ Downloads from MinIO
    │   ├─→ Applies tokenization (Q&A format → chat template)
    │   └─→ Updates DB: training_stage='loading_dataset'
    │
    ├─→ [Stage 5] Training
    │   ├─→ Epoch 1/3 starts
    │   │   ├─→ Updates: current_epoch=1, progress=33.3
    │   │   └─→ Logs: train_loss per step
    │   │
    │   ├─→ Epoch 2/3 starts
    │   │   ├─→ Updates: current_epoch=2, progress=66.6
    │   │   └─→ Logs: train_loss decreasing
    │   │
    │   └─→ Epoch 3/3 completes
    │       ├─→ Updates: current_epoch=3, progress=100
    │       └─→ Training stage: 'training' → 'completed'
    │
    ├─→ [Stage 6] Saving adapters
    │   ├─→ Saves to: /workspace/.../output/adapter_model/
    │   │   ├─→ adapter_model.safetensors
    │   │   ├─→ adapter_config.json
    │   │   └─→ tokenizer files
    │   └─→ Updates DB: training_stage='saving_model'
    │
    ├─→ [Stage 7] Container Merge (OPTIONAL but recommended)
    │   ├─→ Loads base model again (full precision or quantized)
    │   ├─→ Loads adapters from adapter_model/
    │   ├─→ Merges: model = PeftModel.from_pretrained(base, adapter_path)
    │   ├─→ merged_model = model.merge_and_unload()
    │   ├─→ Saves to: /workspace/.../output/merged_model/
    │   └─→ Updates DB: training_stage='merging'
    │
    ├─→ [Stage 8] Upload to MinIO
    │   ├─→ Uploads adapter_model/ → MinIO
    │   ├─→ Uploads merged_model/ → MinIO (if merged)
    │   ├─→ Path: minio://documents/{org}/{project}/finetuning/...
    │   └─→ Updates DB: minio_checkpoint_path
    │
    └─→ [Stage 9] Container Exit
        ├─→ Reports success to celery
        ├─→ Workspace volume persists temporarily
        └─→ GPU released
    │
    ▼
[5] Model Registration (Celery Worker)
    │
    ├─→ Creates entry in finetuned_models table
    │   ├─→ name: "{job_name}_model"
    │   ├─→ version: "v1.0.0"
    │   ├─→ status: "registered"
    │   ├─→ base_model: "Qwen/Qwen2.5-1.5B-Instruct"
    │   ├─→ finetuning_method: "peft"
    │   ├─→ minio_checkpoint_path: "minio://..."
    │   ├─→ adapter_config: {JSON hyperparams}
    │   └─→ merged_model_path: NULL (initially)
    │
    └─→ Returns model_id
    │
    ▼
[6] Auto-Merge (Celery Worker)
    │
    ├─→ Checks: should_auto_merge() → True (env var)
    │
    ├─→ Calls: auto_merge_lora_adapters()
    │   │
    │   ├─→ [Check 1] Container already merged?
    │   │   ├─→ Path: /workspace/.../output/merged_model
    │   │   ├─→ If exists + has config.json:
    │   │   │   └─→ SKIP MERGE (use container merge)
    │   │   └─→ Return: {"status": "success", "source": "container_merge"}
    │   │
    │   ├─→ [Check 2] Find adapters
    │   │   ├─→ Primary path: /workspace/.../output/final
    │   │   ├─→ Fallback path: /workspace/.../output/adapter_model
    │   │   └─→ If not found → ERROR
    │   │
    │   ├─→ [Merge Process] (if container didn't merge)
    │   │   ├─→ Load base model (GPU or CPU)
    │   │   ├─→ Load tokenizer
    │   │   ├─→ Load LoRA adapters
    │   │   ├─→ Merge: merged_model = model.merge_and_unload()
    │   │   ├─→ Save to: /workspace/.../output/merged_model
    │   │   └─→ Duration: 45-120 seconds (model size dependent)
    │   │
    │   └─→ [Update Database]
    │       ├─→ status: 'registered' → 'merged'
    │       ├─→ merged_model_path: /workspace/.../merged_model
    │       ├─→ merge_duration_seconds: XX.X
    │       └─→ COMMIT
    │
    └─→ Auto-merge complete ✅
    │
    ▼
[7] Job Complete
    │
    ├─→ Database status: 'completed'
    ├─→ Model status: 'merged'
    ├─→ Frontend displays: "Ready to Deploy"
    └─→ User can click "Deploy to Ollama"
    │
    ▼
[8] Deployment (Manual or Automated)
    │
    ├─→ POST /api/v1/finetuning/models/{id}/deploy
    │
    ├─→ OllamaDeploymentService.deploy()
    │   │
    │   ├─→ [Step 1] Create Modelfile
    │   │   └─→ FROM /path/to/merged_model
    │   │
    │   ├─→ [Step 2] Register with Ollama
    │   │   └─→ ollama create model_name -f Modelfile
    │   │
    │   ├─→ [Step 3] Verify deployment
    │   │   └─→ ollama list | grep model_name
    │   │
    │   └─→ [Step 4] Update database
    │       ├─→ ollama_model_name: "choles-qa-v1"
    │       ├─→ deployment_url: "http://ollama:11434"
    │       └─→ status: 'deployed'
    │
    └─→ Model ready for inference! 🚀
    │
    ▼
[9] Inference (Chat Interface)
    │
    ├─→ User selects model in chat dropdown
    ├─→ Query sent to LLM service
    ├─→ Routes to Ollama with model name
    ├─→ Returns fine-tuned response
    └─→ Tracks: total_inferences++, avg_latency_ms
```

---

## Implementation Details

### 1. Dataset Format & Preprocessing

#### Supported Formats

**Question-Answering (Q&A)**:
```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is Choles IQ Connect?"},
    {"role": "assistant", "content": "Choles IQ Connect is a cloud-based..."}
  ]
}
```

**Text Generation**:
```json
{
  "text": "Once upon a time in a land far away..."
}
```

**Classification**:
```json
{
  "text": "This product is amazing!",
  "label": "positive"
}
```

#### Preprocessing Pipeline (`peft_trainer.py` lines 128-164)

```python
def tokenize_messages(examples):
    """
    Converts Q&A messages to model-specific format using chat template.

    Input:
      examples["messages"] = [
        [{"role": "system", "content": "..."},
         {"role": "user", "content": "..."},
         {"role": "assistant", "content": "..."}]
      ]

    Output (Qwen format):
      <|im_start|>system
      You are a helpful assistant.<|im_end|>
      <|im_start|>user
      What is Choles IQ Connect?<|im_end|>
      <|im_start|>assistant
      Choles IQ Connect is a cloud-based...<|im_end|>
    """
    tokenized_texts = []

    for messages in examples["messages"]:
        # Apply model's chat template
        formatted_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False
        )
        tokenized_texts.append(formatted_text)

    # Tokenize all formatted texts
    model_inputs = tokenizer(
        tokenized_texts,
        max_length=hyperparams.get("max_length", 512),
        truncation=True,
        padding=False
    )

    # Copy input_ids to labels for causal LM training
    model_inputs["labels"] = model_inputs["input_ids"].copy()

    return model_inputs
```

### 2. LoRA Configuration

#### Default Hyperparameters (`backend/config/finetuning_hyperparameter_defaults.yaml`)

```yaml
peft:
  learning_rate: 0.0002
  num_epochs: 3
  batch_size: 4
  gradient_accumulation_steps: 4
  lora_r: 16                    # Rank (lower = fewer params)
  lora_alpha: 32                # Scaling factor (usually 2*r)
  lora_dropout: 0.05            # Dropout for regularization
  target_modules:               # Which layers to apply LoRA
    - "q_proj"                  # Query projection
    - "v_proj"                  # Value projection
  warmup_steps: 100
  max_seq_length: 2048
  quantization: "4bit"          # QLoRA: 4-bit quantization
```

#### Target Modules Explanation

| Module | Purpose | Impact |
|--------|---------|--------|
| `q_proj` | Query projection in attention | Language understanding |
| `k_proj` | Key projection in attention | Context matching |
| `v_proj` | Value projection in attention | Information extraction |
| `o_proj` | Output projection | Final attention output |
| `gate_proj` | Gating in FFN | Selective information flow |
| `up_proj` | Up-projection in FFN | Hidden dimension expansion |
| `down_proj` | Down-projection in FFN | Output dimension reduction |

**Recommendation**: Start with `q_proj` and `v_proj` (fastest, good results). Add more modules for complex tasks.

### 3. Memory Optimization (QLoRA)

#### Quantization Strategy

```python
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,                      # 4-bit quantization
    bnb_4bit_use_double_quant=True,         # Double quantization
    bnb_4bit_quant_type="nf4",              # NormalFloat4 (optimal)
    bnb_4bit_compute_dtype=torch.bfloat16   # Compute in bf16
)

model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-1.5B-Instruct",
    quantization_config=bnb_config,
    device_map="auto"
)
```

#### Memory Footprint Comparison

| Model | Full Precision | 8-bit | 4-bit (QLoRA) |
|-------|----------------|-------|---------------|
| Qwen 1.5B | ~6GB VRAM | ~2GB VRAM | ~1GB VRAM ✅ |
| Qwen 3B | ~12GB VRAM | ~4GB VRAM | ~2GB VRAM ✅ |
| Qwen 7B | ~28GB VRAM | ~9GB VRAM | ~5GB VRAM ✅ |

**Our GPU**: NVIDIA GeForce RTX 5060 Laptop (8GB VRAM) → Can train up to Qwen 7B with QLoRA!

### 4. Training Callbacks

#### Progress Tracking (`peft_trainer.py`)

```python
class ProgressCallback(TrainerCallback):
    def on_epoch_begin(self, args, state, control, **kwargs):
        """Called at start of each epoch"""
        update_database(
            job_id=job_id,
            current_epoch=state.epoch,
            training_stage='training'
        )

    def on_log(self, args, state, control, logs=None, **kwargs):
        """Called every logging_steps (default: 10 steps)"""
        if logs:
            update_database(
                job_id=job_id,
                current_step=state.global_step,
                train_loss=logs.get('loss'),
                progress=calculate_progress(state.epoch, state.max_steps)
            )
```

#### WebSocket Updates (Real-time UI)

```python
# Backend sends updates to frontend
await websocket_manager.broadcast({
    "type": "training_progress",
    "job_id": job_id,
    "epoch": current_epoch,
    "progress": progress_percentage,
    "train_loss": loss_value
})
```

---

## Container Architecture

### Docker Images

#### 1. Training Container (`chatbot-finetuning-trainer:v1.0.4`)

**Dockerfile**: `backend/Dockerfile` (specialized build)

**Dependencies** (`requirements-finetuning.txt`):
```txt
transformers==4.57.3         # HuggingFace Transformers (Qwen2 support)
peft==0.7.1                  # LoRA/QLoRA
torch==2.9.1+cu128           # PyTorch with CUDA 12.8
trl==0.7.4                   # Transformer Reinforcement Learning
bitsandbytes==0.44.1         # Quantization
accelerate==1.12.0           # Multi-GPU, mixed precision
datasets==2.16.1             # HuggingFace Datasets
```

**Size**: ~8.5GB (optimized)

**GPU Access**:
```bash
docker run --gpus all \
  -v /workspace/finetuning/{job_id}:/workspace \
  chatbot-finetuning-trainer:v1.0.4 \
  python peft_trainer.py
```

#### 2. Backend/Celery-Worker (`chatbot-backend`, `chatbot-celery-worker`)

**Dockerfile**: `backend/Dockerfile` (same source, different images)

**Dependencies** (`requirements.txt`):
```txt
# Core merge dependencies
peft==0.7.1                  # For auto-merge
transformers>=4.40.0         # Qwen2 support (upgraded from 4.36.0)
accelerate>=1.0.0
torch>=2.2.2

# Backend API
fastapi==0.111.0
celery==5.3.4
redis==5.0.1
sqlalchemy==2.0.23
```

**Size**: ~16.5GB (includes PyTorch + PEFT)

**Why Both Need PEFT**:
- **Training container**: Trains model, does container merge
- **Celery-worker**: Runs auto-merge task (if container didn't merge or as fallback)
- **Backend**: Manual merge via UI button

### Container Lifecycle

```python
# GPUPoolManager creates container
container = docker_client.containers.run(
    image="chatbot-finetuning-trainer:v1.0.4",
    name=f"finetuning-{job_id}",

    # GPU allocation
    device_requests=[
        docker.types.DeviceRequest(
            count=1,                          # Request 1 GPU
            capabilities=[['gpu']]
        )
    ],

    # Volume mounts
    volumes={
        f"/workspace/finetuning/{job_id}": {
            "bind": "/workspace",
            "mode": "rw"
        },
        "/root/.cache/huggingface": {        # Model cache
            "bind": "/root/.cache/huggingface",
            "mode": "rw"
        }
    },

    # Environment
    environment={
        "JOB_ID": job_id,
        "BASE_MODEL": "Qwen/Qwen2.5-1.5B-Instruct",
        "DATASET_PATH": dataset_minio_path,
        "HYPERPARAMS_JSON": json.dumps(hyperparams),
        "CUDA_VISIBLE_DEVICES": "0"
    },

    # Networking
    network_mode="bridge",

    # Resource limits
    mem_limit="16g",
    shm_size="8g",                            # Shared memory for dataloaders

    # Keep running
    detach=True,
    remove=False                              # Don't auto-remove (for debugging)
)
```

---

## Database Schema

### Tables

#### `finetuning_jobs`

```sql
CREATE TABLE finetuning_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Configuration
    base_model VARCHAR(255) NOT NULL,                -- "Qwen/Qwen2.5-1.5B-Instruct"
    finetuning_method VARCHAR(50) NOT NULL,          -- "peft", "full", "rlhf"
    training_objective VARCHAR(50) NOT NULL,         -- "qa", "classification", "generation"
    dataset_id UUID REFERENCES finetuning_datasets(id),
    hyperparameters JSONB,                           -- All hyperparams as JSON

    -- Progress tracking
    status VARCHAR(50) DEFAULT 'pending',            -- pending, queued, running, completed, failed
    progress FLOAT DEFAULT 0,                        -- 0-100%
    training_stage VARCHAR(50),                      -- loading_model, training, saving_model, etc.
    current_epoch INTEGER,
    current_step INTEGER,
    total_steps INTEGER,
    train_loss FLOAT,
    eval_loss FLOAT,

    -- Artifacts
    minio_checkpoint_path TEXT,                      -- minio://documents/.../checkpoints/...
    mlflow_run_id VARCHAR(255),

    -- GPU
    gpu_type VARCHAR(100),                           -- "NVIDIA RTX 5060"
    gpu_count INTEGER DEFAULT 1,

    -- Timing
    training_start_time TIMESTAMP,
    training_end_time TIMESTAMP,
    training_time_seconds INTEGER,

    -- Organization
    project_id UUID REFERENCES projects(id),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Celery
    celery_task_id VARCHAR(255)
);

-- Indexes for performance
CREATE INDEX idx_finetuning_jobs_status ON finetuning_jobs(status);
CREATE INDEX idx_finetuning_jobs_created_by ON finetuning_jobs(created_by);
CREATE INDEX idx_finetuning_jobs_project ON finetuning_jobs(project_id);
```

#### `finetuned_models`

```sql
CREATE TABLE finetuned_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) DEFAULT 'v1.0.0',
    description TEXT,

    -- Training reference
    job_id UUID REFERENCES finetuning_jobs(id),
    base_model VARCHAR(255) NOT NULL,
    finetuning_method VARCHAR(50) NOT NULL,

    -- Artifacts
    minio_checkpoint_path TEXT,                      -- Adapter path
    merged_model_path TEXT,                          -- Merged model path
    adapter_config JSONB,                            -- LoRA config

    -- Merge metadata
    merge_duration_seconds FLOAT,
    merge_requested_at TIMESTAMP,
    merge_error_message TEXT,

    -- Evaluation
    eval_metrics JSONB,                              -- perplexity, BLEU, ROUGE, etc.

    -- Lifecycle
    status VARCHAR(50) DEFAULT 'registered',         -- registered, merged, deployed, deprecated

    -- Deployment
    deployment_url TEXT,                             -- Ollama URL
    ollama_model_name VARCHAR(255),
    vllm_model_name VARCHAR(255),

    -- Usage
    total_inferences INTEGER DEFAULT 0,
    avg_latency_ms FLOAT,
    last_inference_at TIMESTAMP,

    -- Versioning
    parent_model_id UUID REFERENCES finetuned_models(id),
    deprecated_at TIMESTAMP,
    deprecated_by UUID REFERENCES users(id),
    deprecation_reason TEXT,

    -- Organization
    project_id UUID REFERENCES projects(id),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),

    -- Metadata
    tags TEXT[]                                      -- ["peft", "qa", "production"]
);

-- Indexes
CREATE INDEX idx_finetuned_models_status ON finetuned_models(status);
CREATE INDEX idx_finetuned_models_job ON finetuned_models(job_id);
CREATE INDEX idx_finetuned_models_ollama ON finetuned_models(ollama_model_name);
```

#### `finetuning_datasets`

```sql
CREATE TABLE finetuning_datasets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Storage
    minio_path TEXT NOT NULL,                        -- minio://documents/.../datasets/...
    file_format VARCHAR(50),                         -- "jsonl", "csv", "parquet"

    -- Statistics
    total_samples INTEGER,
    train_samples INTEGER,
    eval_samples INTEGER,
    test_samples INTEGER,

    -- Metadata
    data_schema JSONB,                               -- Column info, sample data
    validation_status VARCHAR(50),                   -- "valid", "invalid", "pending"
    validation_errors TEXT[],

    -- Organization
    project_id UUID REFERENCES projects(id),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Database Queries

#### Monitor Training Progress

```sql
SELECT
    name,
    status,
    progress,
    current_epoch,
    train_loss,
    eval_loss,
    training_stage,
    gpu_type
FROM finetuning_jobs
WHERE id = '752106bb-e1f4-4338-bca2-e0059215f44e';
```

#### Check Model Status

```sql
SELECT
    name,
    status,
    merged_model_path,
    merge_duration_seconds,
    ollama_model_name,
    total_inferences,
    created_at
FROM finetuned_models
WHERE name LIKE '%training47%'
ORDER BY created_at DESC;
```

#### Find Models Ready to Deploy

```sql
SELECT
    id,
    name,
    status,
    merged_model_path,
    base_model
FROM finetuned_models
WHERE status = 'merged'
  AND ollama_model_name IS NULL
ORDER BY created_at DESC;
```

---

## API Endpoints

### Fine-Tuning Jobs

#### Create Job
```http
POST /api/v1/finetuning/jobs
Content-Type: application/json

{
  "name": "choles-qa-training",
  "description": "Fine-tune Qwen for Choles product Q&A",
  "base_model": "Qwen/Qwen2.5-1.5B-Instruct",
  "finetuning_method": "peft",
  "training_objective": "qa",
  "dataset_id": "uuid-of-dataset",
  "hyperparameters": {
    "learning_rate": 0.0002,
    "num_epochs": 3,
    "batch_size": 4,
    "lora_r": 16,
    "lora_alpha": 32
  }
}
```

**Response**:
```json
{
  "id": "752106bb-e1f4-4338-bca2-e0059215f44e",
  "name": "choles-qa-training",
  "status": "pending",
  "created_at": "2025-12-22T13:54:34Z"
}
```

#### Submit Job to Queue
```http
POST /api/v1/finetuning/jobs/{job_id}/submit
```

**Response**:
```json
{
  "status": "queued",
  "celery_task_id": "abc-123-def",
  "message": "Job submitted to training queue"
}
```

#### Get Job Status
```http
GET /api/v1/finetuning/jobs/{job_id}
```

**Response**:
```json
{
  "id": "752106bb-e1f4-4338-bca2-e0059215f44e",
  "name": "choles-qa-training",
  "status": "running",
  "progress": 66.6,
  "current_epoch": 2,
  "train_loss": 0.856,
  "training_stage": "training",
  "gpu_type": "NVIDIA RTX 5060",
  "training_start_time": "2025-12-22T13:55:00Z"
}
```

### Model Management

#### Merge Model (Manual)
```http
POST /api/v1/finetuning/models/{model_id}/merge
Content-Type: application/json

{
  "base_model_name": "Qwen/Qwen2.5-1.5B-Instruct",
  "force_cpu": false
}
```

#### Deploy to Ollama
```http
POST /api/v1/finetuning/models/{model_id}/deploy
Content-Type: application/json

{
  "target": "ollama",
  "model_name": "choles-qa-v1"
}
```

**Response**:
```json
{
  "status": "deployed",
  "ollama_model_name": "choles-qa-v1",
  "deployment_url": "http://ollama:11434",
  "message": "Model deployed successfully"
}
```

#### List Models
```http
GET /api/v1/finetuning/models?status=merged&project_id=uuid
```

---

## Training Pipeline

### Training Stages (Detailed)

#### Stage 1: Initialization (0-5 minutes)
```
[13:54:34] Container created
[13:54:35] Loading tokenizer from HuggingFace
[13:54:40] Tokenizer loaded ✅
[13:54:41] Setting up 4-bit quantization (QLoRA)
[13:54:42] Loading base model: Qwen/Qwen2.5-1.5B-Instruct
[13:54:45] Downloading model (first time): ~3GB
[13:55:30] Model loaded and quantized ✅
[13:55:31] Preparing model for k-bit training
[13:55:32] Configuring LoRA adapters
[13:55:33] target_modules: q_proj, v_proj
[13:55:33] lora_r=16, lora_alpha=32
[13:55:34] LoRA configured ✅
```

#### Stage 2: Dataset Loading (1-2 minutes)
```
[13:55:35] Loading dataset from MinIO
[13:55:40] Dataset downloaded: company_qa_dataset.jsonl
[13:55:41] Total samples: 9
[13:55:42] Applying tokenization (Q&A → chat template)
[13:55:45] Tokenization complete ✅
[13:55:46] Dataset prepared: 9 training samples
```

#### Stage 3: Training (5-15 minutes, depends on dataset size)
```
[13:55:47] Starting REAL training (NOT mock)
[13:55:48] Epoch 1/3 started
[13:56:00] Step 1/6: loss=1.234
[13:56:15] Step 2/6: loss=1.156
[13:56:30] Step 3/6: loss=1.089
[13:56:45] Epoch 1/3 completed: avg_loss=1.123, progress=33.3%

[13:57:00] Epoch 2/3 started
[13:57:15] Step 4/6: loss=0.956
[13:57:30] Step 5/6: loss=0.887
[13:57:45] Epoch 2/3 completed: avg_loss=0.912, progress=66.6%

[13:58:00] Epoch 3/3 started
[13:58:15] Step 6/6: loss=0.756
[13:58:30] Epoch 3/3 completed: avg_loss=0.734, progress=100% ✅
```

#### Stage 4: Saving & Merging (2-5 minutes)
```
[13:58:31] Training completed! 🎉
[13:58:32] Saving trained adapter weights
[13:58:40] Adapter saved to /workspace/.../adapter_model/ ✅
[13:58:41] Merging trained adapters into base model
[13:58:42] Loading base model again (for merge)
[13:59:30] Base model loaded
[13:59:31] Loading adapters from /workspace/.../adapter_model
[13:59:32] Merging adapters with base model
[14:00:45] Merge complete ✅
[14:00:46] Saving merged model
[14:01:30] Merged model saved to /workspace/.../merged_model/ ✅
```

#### Stage 5: Upload to MinIO (1-2 minutes)
```
[14:01:31] Uploading checkpoint to MinIO
[14:01:35] Uploading: adapter_model.safetensors (45MB)
[14:01:50] Uploading: merged_model (1.5GB)
[14:02:40] Upload complete ✅
[14:02:41] MinIO path: minio://documents/.../checkpoints/...
```

#### Stage 6: Container Exit & Cleanup
```
[14:02:42] Reporting success to celery
[14:02:43] Container exiting
[14:02:44] GPU released
[14:02:45] Container stopped
```

### Total Duration Breakdown

| Stage | Duration | % of Total |
|-------|----------|------------|
| Initialization | 1-5 min | 10-25% |
| Dataset Loading | 1-2 min | 5-10% |
| **Training** | 5-15 min | 50-70% |
| Saving & Merging | 2-5 min | 10-20% |
| Upload to MinIO | 1-2 min | 5-10% |
| **Total** | **10-29 min** | **100%** |

**Factors Affecting Duration**:
- Model size (1.5B faster than 7B)
- Dataset size (9 samples vs 1000 samples)
- Num epochs (3 epochs typical)
- GPU speed (RTX 5060 vs A100)
- Network speed (MinIO upload)

---

## Auto-Merge System

### Why Auto-Merge?

**Problem**: LoRA adapters (small files ~45MB) need to be merged with base model (large file ~3GB) for deployment.

**Without Auto-Merge**:
1. Training completes → Model status: "registered"
2. User must manually click "Merge & Deploy"
3. Wait 2-5 minutes for merge
4. Then deploy

**With Auto-Merge** (Automated):
1. Training completes → Auto-merge runs immediately
2. Model status: "merged" (ready to deploy)
3. One-click deploy, no waiting!

### Auto-Merge Architecture

```python
# File: backend/app/tasks/auto_merge.py

def auto_merge_lora_adapters(
    job_id: str,
    adapter_path: str,
    base_model_name: str,
    workspace_path: Path,
    force_cpu: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Automatically merge LoRA adapters with base model after training.

    Called by: finetuning_tasks.py after model registration
    Runs in: celery-worker container (has PEFT installed)
    GPU access: Yes (via Docker socket)
    """

    # Step 1: Check if container already merged
    merged_output_path = workspace_path / "output" / "merged_model"
    if merged_output_path.exists() and (merged_output_path / "config.json").exists():
        # Container already merged - just return the path (fast!)
        return {
            "status": "success",
            "merged_path": str(merged_output_path),
            "source": "container_merge"
        }

    # Step 2: Find adapters (check multiple paths)
    adapter_checkpoint = Path(adapter_path)
    adapter_model_path = workspace_path / "output" / "adapter_model"

    if not adapter_checkpoint.exists():
        if adapter_model_path.exists():
            adapter_checkpoint = adapter_model_path
        else:
            logger.error("Adapter not found!")
            return None

    # Step 3: Load base model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map="auto" if device == "cuda" else None,
        trust_remote_code=True
    )

    # Step 4: Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)

    # Step 5: Load LoRA adapters
    model = PeftModel.from_pretrained(base_model, str(adapter_checkpoint))

    # Step 6: Merge adapters with base model
    merged_model = model.merge_and_unload()

    # Step 7: Save merged model
    merged_model.save_pretrained(str(merged_output_path))
    tokenizer.save_pretrained(str(merged_output_path))

    # Step 8: Clean up memory
    del base_model, model, merged_model
    if device == "cuda":
        torch.cuda.empty_cache()

    return {
        "status": "success",
        "merged_path": str(merged_output_path),
        "duration_seconds": duration,
        "device": device
    }
```

### Auto-Merge Flow Diagram

```
Training Container                  Celery Worker                   Database
      │                                   │                             │
      │ [Training completes]              │                             │
      │                                   │                             │
      ├─→ [Container Merge]               │                             │
      │   (Optional but recommended)      │                             │
      │                                   │                             │
      │   Save to:                        │                             │
      │   /workspace/.../merged_model/    │                             │
      │                                   │                             │
      ├─→ [Upload to MinIO]               │                             │
      │   - adapter_model/                │                             │
      │   - merged_model/ (if merged)     │                             │
      │                                   │                             │
      ├─→ [Report Success]                │                             │
      │   └─→ HTTP callback to celery ───→│                             │
      │                                   │                             │
      │                                   ├─→ [Register Model]          │
      │                                   │   └─→ INSERT INTO ──────────→│
      │                                   │       finetuned_models       │
      │                                   │       status='registered'    │
      │                                   │                             │
      │                                   ├─→ [Check Auto-Merge Enabled] │
      │                                   │   should_auto_merge() == True│
      │                                   │                             │
      │                                   ├─→ [Auto-Merge Starts]       │
      │                                   │                             │
      │                                   ├─→ [Path Check 1]            │
      │                                   │   Check: merged_model/      │
      │                                   │   exists?                   │
      │                                   │   ✅ YES → Use it!          │
      │                                   │   ❌ NO → Continue          │
      │                                   │                             │
      │                                   ├─→ [Path Check 2]            │
      │                                   │   Check: adapter_model/     │
      │                                   │   exists?                   │
      │                                   │   ✅ YES → Load adapters    │
      │                                   │   ❌ NO → ERROR             │
      │                                   │                             │
      │                                   ├─→ [Merge Process]           │
      │                                   │   1. Load base model        │
      │                                   │   2. Load adapters          │
      │                                   │   3. Merge                  │
      │                                   │   4. Save merged model      │
      │                                   │   Duration: 45-120 sec      │
      │                                   │                             │
      │                                   ├─→ [Update Database]         │
      │                                   │   └─→ UPDATE ───────────────→│
      │                                   │       finetuned_models       │
      │                                   │       SET status='merged',   │
      │                                   │       merged_model_path=..., │
      │                                   │       merge_duration=XX.X    │
      │                                   │                             │
      │                                   ├─→ [Auto-Merge Complete] ✅  │
      │                                   │                             │
      ▼                                   ▼                             ▼
   [Exit]                          [Task Complete]              [Model Ready]
                                                                 status='merged'
```

### Configuration

**Environment Variable** (`.env` or `docker-compose.yml`):
```bash
FINETUNING_AUTO_MERGE=true    # Enable auto-merge (default: true)
```

**Check Function**:
```python
def should_auto_merge() -> bool:
    """Check if auto-merge is enabled via environment variable."""
    auto_merge_enabled = os.getenv("FINETUNING_AUTO_MERGE", "true").lower()
    return auto_merge_enabled in ("true", "1", "yes", "on")
```

### Error Handling

```python
try:
    merge_result = auto_merge_lora_adapters(...)

    if merge_result and merge_result["status"] == "success":
        # Update database
        model.status = "merged"
        model.merged_model_path = merge_result["merged_path"]
        db.commit()
    else:
        # Merge failed - model stays as 'registered'
        logger.warning("Auto-merge failed. User can merge manually from UI.")

except Exception as e:
    logger.error(f"Auto-merge error: {e}")
    # Non-fatal: Model still usable as adapters
```

**Key Point**: Auto-merge failure is **non-fatal**. Model remains as "registered" (adapters available), and user can manually merge via UI.

---

## Deployment Pipeline

### Ollama Deployment

#### Step 1: Modelfile Generation

```python
# OllamaDeploymentService.deploy()

modelfile_content = f"""
FROM {merged_model_path}

# Model parameters
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40

# System prompt (optional)
SYSTEM You are a helpful AI assistant fine-tuned on Choles products.
"""

# Save to /tmp/Modelfile
with open("/tmp/Modelfile", "w") as f:
    f.write(modelfile_content)
```

#### Step 2: Ollama Registration

```bash
# Execute via subprocess
ollama create choles-qa-v1 -f /tmp/Modelfile
```

**Output**:
```
transferring model data
using existing layer sha256:abcd1234...
creating new layer sha256:efgh5678...
writing manifest
success
```

#### Step 3: Verification

```python
# Check if model exists
result = subprocess.run(
    ["ollama", "list"],
    capture_output=True,
    text=True
)

if "choles-qa-v1" in result.stdout:
    logger.info("✅ Model deployed successfully!")
else:
    raise Exception("❌ Model not found in Ollama")
```

#### Step 4: Database Update

```python
model.ollama_model_name = "choles-qa-v1"
model.deployment_url = "http://ollama:11434"
model.status = "deployed"
db.commit()
```

### Chat Integration

**Model Selection Dropdown**:
```typescript
// frontend/src/components/ChatInterface.tsx

const models = await fetch('/api/v1/finetuning/models?status=deployed');

<select onChange={(e) => setSelectedModel(e.target.value)}>
  {models.map(model => (
    <option value={model.ollama_model_name}>
      {model.name} (v{model.version})
    </option>
  ))}
</select>
```

**Query Routing**:
```python
# backend/app/services/llm_service.py

if model_name in ollama_models:
    response = ollama.generate(
        model=model_name,  # "choles-qa-v1"
        prompt=query
    )
else:
    # Fall back to OpenAI/Claude
    response = openai.chat.completions.create(...)
```

---

## Troubleshooting Guide

### Common Issues & Solutions

#### Issue 1: Training Fails with "CUDA out of memory"

**Error**:
```
torch.cuda.OutOfMemoryError: CUDA out of memory. Tried to allocate 512.00 MiB
```

**Solutions**:
1. **Enable QLoRA** (4-bit quantization):
   ```json
   {"quantization": "4bit"}
   ```

2. **Reduce batch size**:
   ```json
   {"batch_size": 2, "gradient_accumulation_steps": 8}
   ```

3. **Reduce sequence length**:
   ```json
   {"max_seq_length": 1024}
   ```

4. **Use smaller model**:
   - Qwen 7B → Qwen 3B → Qwen 1.5B

#### Issue 2: Auto-Merge Fails with "No module named 'peft'"

**Error**:
```
ModuleNotFoundError: No module named 'peft'
```

**Root Cause**: Celery-worker doesn't have PEFT installed

**Solution**: Rebuild celery-worker:
```bash
# Update requirements.txt with PEFT
docker-compose build celery-worker --no-cache
docker-compose up -d --force-recreate celery-worker

# Verify
docker-compose exec celery-worker python -c "import peft; print(peft.__version__)"
```

#### Issue 3: Auto-Merge Fails with "KeyError: 'qwen2'"

**Error**:
```
KeyError: 'qwen2'
```

**Root Cause**: Transformers version too old (< 4.37.0)

**Solution**: Upgrade transformers:
```bash
# Update requirements.txt
transformers>=4.40.0  # Was: 4.36.0

# Rebuild
docker-compose build celery-worker --no-cache
docker-compose up -d --force-recreate celery-worker
```

#### Issue 4: Training Container Crashes with Import Error

**Error**:
```
cannot access local variable 'AutoModelForCausalLM' where it is not associated with a value
```

**Root Cause**: Missing import in merge section of peft_trainer.py

**Solution**: Add import at line 373:
```python
# peft_trainer.py line 373
from transformers import AutoModelForCausalLM
```

#### Issue 5: Dataset Format Error

**Error**:
```
ValueError: Dataset must have 'messages' column for Q&A training
```

**Solution**: Validate dataset format:
```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Question here?"},
    {"role": "assistant", "content": "Answer here."}
  ]
}
```

---

## Performance & Scaling

### Performance Metrics

#### Training Speed

| Model | Dataset | Epochs | GPU | Duration |
|-------|---------|--------|-----|----------|
| Qwen 1.5B | 9 samples | 3 | RTX 5060 | ~8 mins |
| Qwen 1.5B | 100 samples | 3 | RTX 5060 | ~15 mins |
| Qwen 3B | 100 samples | 3 | RTX 5060 | ~25 mins |
| Qwen 7B | 100 samples | 3 | RTX 5060 | ~45 mins |

#### Throughput

- **Sequential**: 1 job at a time (single GPU)
- **Parallel**: N jobs (N GPUs) with queue management
- **GPU Utilization**: 80-95% during training

### Scaling Strategies

#### 1. Multi-GPU Support (Future)

```python
# gpu_pool_manager.py (future enhancement)

available_gpus = detect_gpus()  # [0, 1, 2, 3]
job_queue = []

while job_queue:
    for gpu_id in available_gpus:
        if gpu_is_free(gpu_id):
            job = job_queue.pop()
            assign_job_to_gpu(job, gpu_id)
```

#### 2. Distributed Training (Future)

```bash
# Multi-node training with DeepSpeed/FSDP
torchrun --nproc_per_node=4 \
  --nnodes=2 \
  --node_rank=0 \
  peft_trainer.py
```

#### 3. Caching Strategies

- **Model Cache**: HuggingFace cache shared across containers
  ```python
  volumes={
      "/root/.cache/huggingface": {
          "bind": "/root/.cache/huggingface",
          "mode": "rw"
      }
  }
  ```

- **Dataset Cache**: MinIO path cached after first download

---

## Security & Best Practices

### Security

#### 1. Model Access Control

```python
# RBAC check before training
if not user.has_permission("finetuning:create"):
    raise PermissionError("User not authorized to create fine-tuning jobs")
```

#### 2. MinIO Path Isolation

```python
# User-specific paths
minio_path = f"minio://documents/{org}/{team}/{user}/finetuning/..."
```

#### 3. API Key Security

```bash
# Never commit to git
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Use environment variables
# Store in .env (gitignored)
```

### Best Practices

#### 1. Hyperparameter Tuning

```yaml
# Start conservative
lora_r: 8         # Lower rank = faster, less capacity
learning_rate: 0.0001
num_epochs: 1

# Iterate based on results
# If underfitting → Increase r, add epochs
# If overfitting → Add dropout, decrease epochs
```

#### 2. Dataset Quality

- **Size**: 50+ samples minimum, 500+ ideal
- **Diversity**: Cover all use cases
- **Quality**: Clean, accurate, representative
- **Balance**: Equal samples per class (classification)

#### 3. Monitoring

```python
# Track key metrics
- Training loss (should decrease)
- Eval loss (should decrease, not diverge)
- GPU utilization (should be 80-95%)
- Memory usage (should be stable)
```

#### 4. Versioning

```python
# Semantic versioning
v1.0.0 → v1.0.1  # Bug fix
v1.0.0 → v1.1.0  # New feature (backward compatible)
v1.0.0 → v2.0.0  # Breaking change
```

---

## Appendix: Code References

### Key Files

| File | Purpose | Lines |
|------|---------|-------|
| `backend/app/tasks/finetuning_tasks.py` | Main training orchestration | 922-957 (auto-merge) |
| `backend/app/tasks/auto_merge.py` | Auto-merge logic | 1-198 (complete) |
| `backend/app/services/finetuning/trainers/peft_trainer.py` | Training script | 128-164 (preprocessing), 369-410 (merge) |
| `backend/app/services/finetuning/gpu_pool_manager.py` | GPU management | Full file |
| `backend/app/services/ollama_deployment_service.py` | Ollama deployment | Full file |

### Configuration Files

| File | Purpose |
|------|---------|
| `backend/config/finetuning_hyperparameter_defaults.yaml` | Default hyperparameters |
| `backend/requirements.txt` | Backend/celery-worker dependencies |
| `backend/requirements-finetuning.txt` | Training container dependencies |
| `.env` | Environment variables |

### Documentation

| File | Purpose |
|------|---------|
| [AUTO_MERGE_PATH_FIX.md](./AUTO_MERGE_PATH_FIX.md) | Path detection fix |
| [TRANSFORMERS_VERSION_FIX.md](./TRANSFORMERS_VERSION_FIX.md) | Qwen2 support |
| [CELERY_WORKER_BUILD_SUCCESS.md](./CELERY_WORKER_BUILD_SUCCESS.md) | PEFT installation |
| [PEFT_BACKEND_INSTALLATION.md](./PEFT_BACKEND_INSTALLATION.md) | Complete PEFT guide |
| [QA_FORMAT_VALIDATION.md](./QA_FORMAT_VALIDATION.md) | Dataset format validation |

---

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-22 | 1.0.0 | Initial comprehensive documentation |

---

**End of Document**

For questions, issues, or contributions, see:
- GitHub: [enterprise-rag-chatbot](https://github.com/...)
- Docs: `/docs/features/finetuning/`
- Support: team@example.com

---

**Authors**: Enterprise RAG Team
**Maintainers**: AI/ML Engineering
**License**: Internal Use Only
**Last Updated**: 2025-12-22
