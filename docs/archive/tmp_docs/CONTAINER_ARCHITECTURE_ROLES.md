# Container Architecture - Who Does What

## Container Roles in Fine-Tuning Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        FINE-TUNING WORKFLOW                              │
└─────────────────────────────────────────────────────────────────────────┘

1. USER UPLOADS DATASET
   ↓
   [rag-backend] ← FastAPI handles upload
   ↓
   Saves to MinIO + PostgreSQL

2. USER CREATES TRAINING JOB
   ↓
   [rag-backend] ← Creates job record in DB
   ↓
   [celery-worker] ← Receives async task
   ↓
   Docker spawns → [finetuning-trainer] ← GPU container (created on-demand)
   ↓
   TRAINING HAPPENS HERE (5-10 min)
   - Loads Qwen/Qwen2.5-1.5B-Instruct
   - Trains LoRA adapter
   - Saves to /workspace/finetuning/{job_id}/output/adapter_model/
   ↓
   [celery-worker] ← Updates job status to "completed"
   ↓
   [rag-backend] ← Creates finetuned_models record

3. USER CLICKS "DEPLOY TO OLLAMA"
   ↓
   [rag-frontend] ← Button clicked
   ↓
   [rag-backend] ← POST /models-public/{model_id}/deploy
   ↓
   **CURRENTLY FAILS HERE** ❌
   - Backend tries to merge adapter + base model
   - Backend has transformers 4.36.0 (too old for Qwen2)
   - KeyError: 'qwen2'
```

## Container Details

### 1. rag-backend (FastAPI Application)

**Container Name**: `rag-backend`
**Image**: Built from `backend/Dockerfile`
**Purpose**: Main API server
**Current Transformers Version**: 4.36.0 ❌ (TOO OLD)

**What It Does**:
- ✅ Handles all HTTP API requests
- ✅ Manages dataset uploads
- ✅ Creates fine-tuning job records
- ✅ Triggers Celery tasks
- ❌ **CURRENTLY TRIES TO MERGE** (but fails due to old transformers)
- ✅ Would handle GGUF conversion (llama.cpp)
- ✅ Would handle Ollama deployment API calls

**Current Problem**:
```python
# This code runs in rag-backend container:
base_model_obj = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")
# ❌ FAILS: transformers 4.36.0 doesn't know about Qwen2 architecture
```

### 2. celery-worker (Task Queue Processor)

**Container Name**: `celery-worker`
**Image**: Same as rag-backend
**Purpose**: Process async background tasks
**Transformers Version**: Same as backend (4.36.0)

**What It Does**:
- ✅ Receives training job submission tasks
- ✅ Spawns Docker containers for training via `docker run`
- ✅ Monitors training progress
- ✅ Updates job status in database
- ❌ **DOES NOT** do the actual training itself
- ❌ **DOES NOT** merge models

**Key Code** (from `backend/app/tasks/finetuning_tasks.py`):
```python
@celery_app.task(name="submit_finetuning_job")
def submit_finetuning_job(job_id: str):
    # This runs in celery-worker container
    # But spawns a NEW container for training:
    subprocess.run([
        "docker", "run", "--gpus", "all",
        "-v", "/workspace/finetuning:/workspace/finetuning",
        "chatbot-finetuning-trainer:v1.0.4",
        "python", "train.py", ...
    ])
```

### 3. finetuning-trainer (GPU Training Container)

**Container Name**: `chatbot-finetuning-trainer-{job_id}` (created on-demand)
**Image**: `chatbot-finetuning-trainer:v1.0.4`
**Purpose**: Actual model training
**Transformers Version**: >=4.38.0 ✅ (SUPPORTS QWEN2)

**What It Does**:
- ✅ **TRAINING HAPPENS HERE**
- ✅ Loads base model (Qwen/Qwen2.5-1.5B-Instruct)
- ✅ Loads training dataset from /workspace/finetuning/{job_id}/input/
- ✅ Trains LoRA adapter using GPU
- ✅ Saves adapter to /workspace/finetuning/{job_id}/output/adapter_model/
- ✅ Saves checkpoints during training
- ✅ Container is **destroyed** after training completes

**Lifecycle**:
```
Training job submitted
   ↓
celery-worker spawns container
   ↓
Container runs for ~5-10 minutes
   ↓
Training completes
   ↓
Container exits and is removed
   ↓
Adapter files remain in /workspace/finetuning/ (persistent volume)
```

### 4. rag-ollama (Model Serving)

**Container Name**: `rag-ollama`
**Image**: `ollama/ollama:latest`
**Purpose**: Serve models for inference
**Transformers Version**: Has Python + transformers ✅ (recent version)

**What It Does**:
- ✅ Serves models via Ollama API (port 11434)
- ✅ Has access to /workspace/finetuning/ (volume mounted)
- ✅ Has newer transformers (can load Qwen2)
- ✅ Can run Python scripts if needed
- ✅ Final destination for deployed models

**Volumes**:
```yaml
volumes:
  - /workspace/finetuning:/workspace/finetuning  # ✅ Can access adapters
  - ollama-models:/root/.ollama/models           # Model storage
```

### 5. finetuning-runtime (On-Demand Training)

**Container Name**: `finetuning-runtime` (built but not running by default)
**Image**: Built from `backend/Dockerfile.finetuning-runtime`
**Purpose**: Alternative training runtime
**Transformers Version**: >=4.38.0 ✅ (SUPPORTS QWEN2)

**What It Does**:
- Similar to finetuning-trainer
- Can be used for Celery tasks
- Has all training dependencies
- Has newer transformers

## Where Operations Currently Happen

| Operation | Current Container | Status | Notes |
|-----------|------------------|--------|-------|
| **Dataset Upload** | rag-backend | ✅ Works | Saves to MinIO |
| **Create Job** | rag-backend | ✅ Works | Creates DB record |
| **Submit Job** | celery-worker | ✅ Works | Triggers training |
| **Training** | finetuning-trainer | ✅ Works | GPU container, Qwen2 support ✅ |
| **Save Adapter** | finetuning-trainer | ✅ Works | Saves to /workspace/finetuning/ |
| **Merge Adapter** | rag-backend | ❌ **FAILS** | transformers 4.36.0 too old |
| **GGUF Conversion** | rag-backend | ⚠️ Not tested | Would work with llama.cpp |
| **Ollama Deploy** | rag-backend → rag-ollama | ⚠️ Not reached | Blocked by merge failure |

## The Problem

```
Training (finetuning-trainer):
✅ Has transformers >=4.38.0
✅ Can load Qwen/Qwen2.5-1.5B-Instruct
✅ Creates adapter successfully

Deployment (rag-backend):
❌ Has transformers 4.36.0
❌ CANNOT load Qwen/Qwen2.5-1.5B-Instruct
❌ Merge fails with KeyError: 'qwen2'
```

## The Solution Options

### Option 1: Upgrade Backend Transformers ⭐ RECOMMENDED

**Change**: `backend/requirements.txt`
```diff
- transformers==4.36.0
+ transformers>=4.38.0
```

**Pros**:
- Simple one-line fix
- Backend can handle everything
- Consistent with training environment

**Cons**:
- Need to rebuild backend image
- Potential compatibility issues with other code

**Implementation**:
```bash
# Update requirements
sed -i 's/transformers==4.36.0/transformers>=4.38.0/' backend/requirements.txt

# Rebuild
docker-compose build backend --no-cache
docker-compose up -d backend
```

### Option 2: Offload Merge to Ollama Container

**Change**: Modify `ollama_deployment_service.py` to run merge in Ollama container

**Implementation**:
```python
async def _merge_adapter_to_base(self, adapter_path, base_model, output_path):
    # Instead of running merge in backend, exec into Ollama container
    cmd = f"""docker exec rag-ollama python3 -c '
import torch
from transformers import AutoModelForCausalLM
from peft import PeftModel

base = AutoModelForCausalLM.from_pretrained("{base_model}", device_map="auto", trust_remote_code=True)
peft_model = PeftModel.from_pretrained(base, "{adapter_path}")
merged = peft_model.merge_and_unload()
merged.save_pretrained("{output_path}")
'"""

    subprocess.run(cmd, shell=True)
```

**Pros**:
- No backend rebuild
- Ollama container has newer transformers

**Cons**:
- Requires Docker-in-Docker permissions
- More complex

### Option 3: Use Celery Task in Finetuning-Runtime

**Change**: Create Celery task for merge operation

**Implementation**:
```python
# backend/app/tasks/finetuning_tasks.py
@celery_app.task(name="merge_adapter_task")
def merge_adapter_task(adapter_path, base_model, output_path):
    # Spawn finetuning-runtime container to do merge
    subprocess.run([
        "docker", "run", "--gpus", "all",
        "-v", "/workspace/finetuning:/workspace/finetuning",
        "chatbot-finetuning-runtime:latest",
        "python", "-c", f"""
import torch
from transformers import AutoModelForCausalLM
from peft import PeftModel

base = AutoModelForCausalLM.from_pretrained("{base_model}", device_map="auto")
peft = PeftModel.from_pretrained(base, "{adapter_path}")
merged = peft.merge_and_unload()
merged.save_pretrained("{output_path}")
"""
    ])
```

**Pros**:
- Proper async handling
- Uses existing training infrastructure
- Progress tracking

**Cons**:
- Most complex
- Requires Celery setup

## Recommended Path Forward

**Implement Option 1** - Upgrade backend transformers:

1. ✅ Update `backend/requirements.txt`
2. ✅ Rebuild backend container
3. ✅ Test deployment end-to-end
4. ✅ Verify model works in Ollama

**Why Option 1?**
- Simplest and fastest (5 minutes)
- Aligns backend with training environment
- No architectural changes needed
- Easy to rollback if issues arise

---

**Status**: Container architecture explained ✅
**Next Action**: Implement Option 1 fix
**ETA**: 5 minutes to fix + 10-15 minutes to test deployment
