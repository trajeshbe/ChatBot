# JIRA Task: Fine-Tuning Model Merge & Ollama Deployment

**JIRA ID**: `FINETUNE-001`
**Title**: Implement LoRA Adapter Merge and Ollama Deployment Pipeline
**Type**: Feature
**Priority**: High
**Status**: Backlog
**Created**: 2025-12-22
**Reporter**: System Analysis
**Assignee**: TBD

---

## Summary

Implement on-demand LoRA adapter merging and Ollama deployment for fine-tuned models. Currently, training produces only LoRA adapters (not deployable standalone). Users should be able to request "Merge & Deploy" via UI for approved models.

---

## Business Context

**Problem**:
- Training produces LoRA adapters only (8.7 MB files)
- Adapters cannot be deployed to Ollama directly
- No standalone model for production use

**Goal**:
- User trains model → gets LoRA adapters
- User reviews/approves model
- User clicks "Merge & Deploy" button in UI
- System merges adapters with base model
- System creates Ollama model
- Model ready for inference

**Why separate merge from training?**:
- Merging takes time (5-15 minutes for 1.5B models)
- Not all trained models need deployment
- User approval workflow required
- Resource optimization (merge only approved models)

---

## Acceptance Criteria

### Phase 1: Database Schema

- [ ] Add `merged_model_path` column to `finetuned_models` table
- [ ] Add `deployment_status` enum column: `adapter_only`, `merging`, `merged`, `deploying`, `deployed`, `deployment_failed`
- [ ] Add `ollama_model_name` column (e.g., `choles-qa-v1:latest`)
- [ ] Add `deployment_requested_at` timestamp
- [ ] Add `deployment_approved_by` user reference

### Phase 2: Backend API Endpoints

- [ ] `POST /api/v1/finetuning/models/{model_id}/merge` - Initiate merge process
- [ ] `POST /api/v1/finetuning/models/{model_id}/deploy` - Deploy to Ollama
- [ ] `GET /api/v1/finetuning/models/{model_id}/deployment-status` - Check status
- [ ] `POST /api/v1/finetuning/models/{model_id}/undeploy` - Remove from Ollama
- [ ] All endpoints require admin/model-owner authorization

### Phase 3: Merge Service Implementation

**File**: `backend/app/services/finetuning/model_merge_service.py`

```python
class ModelMergeService:
    async def merge_lora_adapters(
        self,
        model_id: str,
        adapter_path: str,  # MinIO path to adapter_model.safetensors
        base_model: str,    # e.g., "Qwen/Qwen2.5-1.5B-Instruct"
        output_path: str    # MinIO path for merged model
    ) -> Dict[str, Any]:
        """
        Merge LoRA adapters with base model

        Steps:
        1. Download adapter from MinIO
        2. Load base model from HuggingFace
        3. Load PEFT adapter
        4. Merge using model.merge_and_unload()
        5. Save merged model to MinIO
        6. Update database with merged_model_path

        Returns:
            {
                "status": "success",
                "merged_model_path": "minio://...",
                "model_size_mb": 3200,
                "merge_duration_seconds": 450
            }
        """
```

### Phase 4: Ollama Deployment Service

**File**: `backend/app/services/finetuning/ollama_deployment_service.py`

```python
class OllamaDeploymentService:
    async def deploy_to_ollama(
        self,
        model_id: str,
        merged_model_path: str,  # MinIO path to merged model
        model_name: str          # e.g., "choles-qa-v1"
    ) -> Dict[str, Any]:
        """
        Deploy merged model to Ollama

        Steps:
        1. Download merged model from MinIO
        2. Generate Modelfile (FROM, TEMPLATE, SYSTEM, PARAMETERS)
        3. Run `ollama create <model_name> -f Modelfile`
        4. Verify with test inference
        5. Update database with ollama_model_name
        6. Set deployment_status = 'deployed'

        Returns:
            {
                "status": "deployed",
                "ollama_model_name": "choles-qa-v1:latest",
                "model_size_mb": 3200,
                "test_inference": "Q: What is Choles? A: ..."
            }
        """
```

### Phase 5: Celery Background Tasks

**File**: `backend/app/tasks/model_deployment_tasks.py`

```python
@celery.task(name="merge_lora_model", bind=True)
def merge_lora_model_task(self, model_id: str):
    """
    Background task for merging LoRA adapters

    Duration: 5-15 minutes
    Updates deployment_status throughout process
    """

@celery.task(name="deploy_to_ollama", bind=True)
def deploy_to_ollama_task(self, model_id: str, merged_model_path: str):
    """
    Background task for Ollama deployment

    Duration: 2-5 minutes
    Updates deployment_status throughout process
    """
```

### Phase 6: Frontend UI Components

**Component**: `frontend/src/components/finetuning/ModelDeploymentPanel.tsx`

**Features**:
- Display model status badge: "Adapter Only", "Merging...", "Merged", "Deploying...", "Deployed"
- "Merge Adapters" button (enabled when status = "adapter_only")
- "Deploy to Ollama" button (enabled when status = "merged")
- "Undeploy" button (enabled when status = "deployed")
- Progress indicator during merge/deploy
- Deployment log viewer

**UI Flow**:
```
[Model Card: choles-qa-real-training37]
├── Status: ✅ Training Complete | 📦 Adapter Only
├── Adapters: adapter_model.safetensors (8.7 MB)
├── Created: 2025-12-22
└── Actions:
    ├── [View Details]
    ├── [Merge Adapters] ← Initiates merge process
    └── [Delete]

After merge:
[Model Card: choles-qa-real-training37]
├── Status: ✅ Merged | 🚀 Ready for Deployment
├── Merged Model: merged_model.safetensors (3.2 GB)
├── Merge Time: 8 minutes
└── Actions:
    ├── [View Details]
    ├── [Deploy to Ollama] ← Initiates Ollama deployment
    ├── [Download Merged Model]
    └── [Delete]

After deployment:
[Model Card: choles-qa-real-training37]
├── Status: ✅ Deployed | 🎯 Ready for Inference
├── Ollama Model: choles-qa-v1:latest
├── Endpoint: http://localhost:11434/api/generate
└── Actions:
    ├── [Test Inference]
    ├── [Undeploy]
    ├── [View Logs]
    └── [Delete]
```

---

## Technical Implementation Details

### Merge Process (Celery Task)

```python
# Pseudo-code
def merge_lora_adapters(job_id, adapter_path, base_model):
    # 1. Update status
    update_deployment_status(job_id, "merging")

    # 2. Download adapter from MinIO
    adapter_local_path = download_from_minio(adapter_path)

    # 3. Load base model
    from transformers import AutoModelForCausalLM
    model = AutoModelForCausalLM.from_pretrained(base_model, torch_dtype="auto")

    # 4. Load and merge adapter
    from peft import PeftModel
    model = PeftModel.from_pretrained(model, adapter_local_path)
    merged_model = model.merge_and_unload()  # ← This is the key step!

    # 5. Save merged model locally
    merged_model.save_pretrained("/tmp/merged_model")
    tokenizer.save_pretrained("/tmp/merged_model")

    # 6. Upload to MinIO
    merged_path = upload_to_minio("/tmp/merged_model", bucket="models")

    # 7. Update database
    update_model(job_id, merged_model_path=merged_path, deployment_status="merged")

    # 8. Cleanup
    shutil.rmtree("/tmp/merged_model")
```

### Ollama Deployment (Celery Task)

```python
# Pseudo-code
def deploy_to_ollama(job_id, merged_model_path, model_name):
    # 1. Update status
    update_deployment_status(job_id, "deploying")

    # 2. Download merged model
    model_local_path = download_from_minio(merged_model_path)

    # 3. Generate Modelfile
    modelfile = f"""
FROM {model_local_path}

TEMPLATE \"\"\"
{{{{ if .System }}}}<|im_start|>system
{{{{ .System }}}}<|im_end|>
{{{{ end }}}}{{{{ if .Prompt }}}}<|im_start|>user
{{{{ .Prompt }}}}<|im_end|>
{{{{ end }}}}<|im_start|>assistant
\"\"\"

SYSTEM \"\"\"You are a helpful assistant trained on domain-specific data.\"\"\"

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER stop "<|im_end|>"
"""

    # 4. Create Ollama model
    subprocess.run([
        "ollama", "create", f"{model_name}:latest",
        "-f", "/tmp/Modelfile"
    ], check=True)

    # 5. Verify deployment
    response = subprocess.run([
        "ollama", "run", f"{model_name}:latest",
        "Hello, can you introduce yourself?"
    ], capture_output=True, text=True)

    # 6. Update database
    update_model(
        job_id,
        ollama_model_name=f"{model_name}:latest",
        deployment_status="deployed",
        deployment_url=f"http://localhost:11434/api/generate"
    )

    # 7. Cleanup
    shutil.rmtree(model_local_path)
```

---

## Database Migration

```sql
-- Migration: Add deployment tracking columns

ALTER TABLE finetuned_models
ADD COLUMN merged_model_path TEXT,
ADD COLUMN deployment_status VARCHAR(50) DEFAULT 'adapter_only'
    CHECK (deployment_status IN ('adapter_only', 'merging', 'merged', 'deploying', 'deployed', 'deployment_failed')),
ADD COLUMN ollama_model_name VARCHAR(255),
ADD COLUMN deployment_url TEXT,
ADD COLUMN deployment_requested_at TIMESTAMPTZ,
ADD COLUMN deployment_approved_by UUID REFERENCES users(id),
ADD COLUMN merge_duration_seconds INTEGER,
ADD COLUMN deploy_duration_seconds INTEGER;

CREATE INDEX idx_finetuned_models_deployment_status ON finetuned_models(deployment_status);
CREATE INDEX idx_finetuned_models_ollama_name ON finetuned_models(ollama_model_name);
```

---

## API Endpoints Specification

### 1. Merge LoRA Adapters

```http
POST /api/v1/finetuning/models/{model_id}/merge
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "output_name": "choles-qa-merged-v1"  // Optional custom name
}

Response (202 Accepted):
{
  "message": "Merge process started",
  "model_id": "af037e98-225f-409b-a5e1-98dd35084240",
  "task_id": "celery-task-uuid",
  "estimated_duration_minutes": 8,
  "status": "merging"
}
```

### 2. Deploy to Ollama

```http
POST /api/v1/finetuning/models/{model_id}/deploy
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "ollama_model_name": "choles-qa-v1",  // Required
  "system_prompt": "You are...",         // Optional override
  "temperature": 0.7,                    // Optional
  "auto_start": true                     // Start serving immediately
}

Response (202 Accepted):
{
  "message": "Deployment started",
  "model_id": "af037e98-225f-409b-a5e1-98dd35084240",
  "task_id": "celery-task-uuid",
  "estimated_duration_minutes": 3,
  "status": "deploying"
}
```

### 3. Check Deployment Status

```http
GET /api/v1/finetuning/models/{model_id}/deployment-status
Authorization: Bearer <token>

Response (200 OK):
{
  "model_id": "af037e98-225f-409b-a5e1-98dd35084240",
  "deployment_status": "deployed",
  "merged_model_path": "minio://models/...",
  "ollama_model_name": "choles-qa-v1:latest",
  "deployment_url": "http://localhost:11434/api/generate",
  "merge_duration_seconds": 480,
  "deploy_duration_seconds": 180,
  "deployment_logs": [
    "[2025-12-22 06:00:00] Starting merge process...",
    "[2025-12-22 06:08:00] Merge completed successfully",
    "[2025-12-22 06:08:30] Starting Ollama deployment...",
    "[2025-12-22 06:11:30] Deployment completed"
  ]
}
```

---

## Testing Plan

### Unit Tests

- [ ] Test `ModelMergeService.merge_lora_adapters()`
- [ ] Test `OllamaDeploymentService.deploy_to_ollama()`
- [ ] Test Celery task execution
- [ ] Test MinIO upload/download
- [ ] Test database status updates

### Integration Tests

- [ ] End-to-end: Train → Merge → Deploy → Inference
- [ ] Test error handling (merge failure, deploy failure)
- [ ] Test concurrent merge requests
- [ ] Test deployment verification

### UI Tests

- [ ] Test "Merge Adapters" button workflow
- [ ] Test "Deploy to Ollama" button workflow
- [ ] Test status updates in real-time
- [ ] Test deployment log viewer

---

## Performance Considerations

### Resource Requirements

- **Merging**: Requires VRAM = base model size (e.g., 3.2 GB for 1.5B model)
- **Duration**: 5-15 minutes depending on model size
- **Storage**: Merged model = base model size (3.2 GB for 1.5B)

### Optimization Strategies

- Use CPU for merge if GPU unavailable (slower but works)
- Implement merge queue (one at a time to avoid OOM)
- Cache base models in HuggingFace cache
- Use `torch_dtype="float16"` to reduce memory

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|----------|
| OOM during merge | High | Queue merges, use CPU fallback |
| Ollama deployment failure | Medium | Rollback, keep adapters |
| Storage bloat | Medium | Auto-delete old merged models |
| Concurrent merges | High | Implement merge queue/lock |

---

## Dependencies

- `peft` library (already in requirements)
- `transformers` library (already in requirements)
- Ollama CLI installed on host
- MinIO storage configured
- Celery worker running

---

## Timeline Estimate

- **Phase 1 (DB Schema)**: 2 hours
- **Phase 2 (API Endpoints)**: 4 hours
- **Phase 3 (Merge Service)**: 8 hours
- **Phase 4 (Ollama Service)**: 6 hours
- **Phase 5 (Celery Tasks)**: 4 hours
- **Phase 6 (Frontend UI)**: 12 hours
- **Testing**: 8 hours

**Total**: ~44 hours (~1 week for 1 developer)

---

## Success Metrics

- [ ] Users can merge adapters via UI
- [ ] Merge completes in < 15 minutes for 1.5B models
- [ ] Deployment to Ollama succeeds 95%+ of time
- [ ] Deployed models respond to inference within 2 seconds
- [ ] UI shows real-time status updates

---

## Related Documentation

- `/tmp/TRAINING36_SUCCESS_REPORT.md` - Training pipeline working
- `/tmp/TRAINING37_SUCCESS_REPORT.md` - Validation of bug fixes
- `docs/features/FINETUNING_COMPLETE_IMPLEMENTATION_GUIDE.md`

---

**Status**: Ready for Implementation
**Next Steps**: Assign to developer, create sprint backlog items
**Questions**: Contact system architect

---

**JIRA Comments**:
- [2025-12-22] Analysis complete - training works, merge/deploy missing
- [2025-12-22] User requested on-demand merge (not automatic)
- [2025-12-22] Approved for next sprint

