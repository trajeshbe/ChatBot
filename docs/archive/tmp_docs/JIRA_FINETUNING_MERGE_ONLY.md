# JIRA Task: LoRA Adapter Merge Implementation

**JIRA ID**: `FINETUNE-002`
**Title**: Implement LoRA Adapter Merge for Fine-Tuned Models
**Type**: Feature
**Priority**: High
**Status**: Backlog
**Created**: 2025-12-22
**Reporter**: System Analysis
**Assignee**: TBD

---

## Summary

Implement on-demand LoRA adapter merging for fine-tuned models. Currently, training produces only LoRA adapters (8.7 MB, not deployable). Users need merged full models (3.2 GB) to deploy to Ollama.

**Note**: Ollama deployment UI and backend already exist. This task **ONLY** implements the merge step.

---

## Business Context

**Current State**:
- Training produces: `adapter_model.safetensors` (8.7 MB)
- Cannot deploy to Ollama (requires full model weights)
- No standalone model for production use

**Goal**:
- User trains model → gets LoRA adapters ✅ (working)
- User clicks "Merge Adapters" button in UI
- System merges adapters + base model → full model (3.2 GB)
- User deploys merged model to Ollama ✅ (UI/backend exists)

**Why separate merge from training?**:
- Merging takes 5-15 minutes (don't block training completion)
- Not all trained models need deployment (save resources)
- User approval workflow required
- Training already completed, merge is optional

---

## Acceptance Criteria

### Phase 1: Database Schema ✅ (May Already Exist)

Check if `finetuned_models` table has these columns:

- [ ] `merged_model_path` TEXT
- [ ] `merge_status` VARCHAR(50) - values: `not_merged`, `merging`, `merged`, `merge_failed`
- [ ] `merge_requested_at` TIMESTAMPTZ
- [ ] `merge_duration_seconds` INTEGER
- [ ] `merge_error_message` TEXT (for failures)

**If missing, add migration**:

```sql
ALTER TABLE finetuned_models
ADD COLUMN merged_model_path TEXT,
ADD COLUMN merge_status VARCHAR(50) DEFAULT 'not_merged'
    CHECK (merge_status IN ('not_merged', 'merging', 'merged', 'merge_failed')),
ADD COLUMN merge_requested_at TIMESTAMPTZ,
ADD COLUMN merge_duration_seconds INTEGER,
ADD COLUMN merge_error_message TEXT;

CREATE INDEX idx_finetuned_models_merge_status ON finetuned_models(merge_status);
```

---

### Phase 2: Backend API Endpoint

**File**: `backend/app/api/routes/finetuning_routes.py` (or create new file)

**Endpoint**:
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

**Status Check Endpoint**:
```http
GET /api/v1/finetuning/models/{model_id}/merge-status
Authorization: Bearer <token>

Response (200 OK):
{
  "model_id": "af037e98-225f-409b-a5e1-98dd35084240",
  "merge_status": "merged",
  "merged_model_path": "minio://models/.../merged_model",
  "merge_duration_seconds": 480,
  "merge_requested_at": "2025-12-22T06:00:00Z"
}
```

---

### Phase 3: Merge Service Implementation

**File**: `backend/app/services/finetuning/model_merge_service.py` (NEW)

```python
import os
import shutil
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.core.config import settings
from minio import Minio
import logging

logger = logging.getLogger(__name__)

class ModelMergeService:
    """
    Service for merging LoRA adapters with base models
    """

    def __init__(self, db: Session):
        self.db = db
        self.minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )

    def merge_lora_adapters(
        self,
        model_id: str,
        adapter_path: str,  # MinIO path: minio://bucket/path/to/adapter
        base_model: str,    # HuggingFace model: "Qwen/Qwen2.5-1.5B-Instruct"
        output_name: str = None
    ) -> Dict[str, Any]:
        """
        Merge LoRA adapters with base model to create standalone model

        Steps:
        1. Download adapter from MinIO
        2. Load base model from HuggingFace
        3. Load PEFT adapter
        4. Merge using model.merge_and_unload()
        5. Save merged model locally
        6. Upload to MinIO
        7. Update database
        8. Cleanup

        Args:
            model_id: UUID of finetuned model record
            adapter_path: MinIO path to adapter files
            base_model: HuggingFace model name
            output_name: Optional custom name for merged model

        Returns:
            {
                "status": "success",
                "merged_model_path": "minio://...",
                "model_size_mb": 3200,
                "merge_duration_seconds": 450
            }
        """
        start_time = datetime.utcnow()

        try:
            # Update status to 'merging'
            self._update_merge_status(model_id, "merging")

            # 1. Download adapter from MinIO
            logger.info(f"[{model_id[:8]}] Downloading adapter from MinIO: {adapter_path}")
            local_adapter_path = self._download_adapter_from_minio(adapter_path)

            # 2-4. Load base model and merge
            logger.info(f"[{model_id[:8]}] Loading base model: {base_model}")
            merged_model_path = self._merge_adapter_with_base(
                base_model,
                local_adapter_path,
                output_name or f"merged_model_{model_id[:8]}"
            )

            # 5. Upload merged model to MinIO
            logger.info(f"[{model_id[:8]}] Uploading merged model to MinIO")
            minio_merged_path = self._upload_merged_model_to_minio(
                merged_model_path,
                model_id
            )

            # 6. Calculate duration and size
            duration_seconds = int((datetime.utcnow() - start_time).total_seconds())
            model_size_mb = self._get_directory_size_mb(merged_model_path)

            # 7. Update database
            self._update_merge_complete(
                model_id,
                minio_merged_path,
                duration_seconds
            )

            # 8. Cleanup
            logger.info(f"[{model_id[:8]}] Cleaning up local files")
            shutil.rmtree(local_adapter_path, ignore_errors=True)
            shutil.rmtree(merged_model_path, ignore_errors=True)

            return {
                "status": "success",
                "merged_model_path": minio_merged_path,
                "model_size_mb": model_size_mb,
                "merge_duration_seconds": duration_seconds
            }

        except Exception as e:
            logger.error(f"[{model_id[:8]}] Merge failed: {e}")
            self._update_merge_failed(model_id, str(e))
            raise

    def _merge_adapter_with_base(
        self,
        base_model: str,
        adapter_path: str,
        output_name: str
    ) -> str:
        """
        Merge PEFT adapter with base model using transformers + peft

        Returns:
            Local path to merged model directory
        """
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
        import torch

        output_path = f"/tmp/{output_name}"
        os.makedirs(output_path, exist_ok=True)

        # Load base model
        logger.info(f"Loading base model: {base_model}")
        model = AutoModelForCausalLM.from_pretrained(
            base_model,
            torch_dtype=torch.float16,  # Use float16 to save memory
            device_map="auto"            # Auto GPU/CPU allocation
        )

        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(base_model)

        # Load PEFT adapter
        logger.info(f"Loading adapter from: {adapter_path}")
        model = PeftModel.from_pretrained(model, adapter_path)

        # Merge adapter into base model weights
        logger.info("Merging adapter with base model (this takes 5-15 minutes)...")
        merged_model = model.merge_and_unload()  # ← KEY STEP!

        # Save merged model
        logger.info(f"Saving merged model to: {output_path}")
        merged_model.save_pretrained(output_path)
        tokenizer.save_pretrained(output_path)

        logger.info(f"✅ Merge complete! Saved to {output_path}")
        return output_path

    def _download_adapter_from_minio(self, minio_path: str) -> str:
        """
        Download adapter files from MinIO

        Args:
            minio_path: minio://bucket/path/to/adapter

        Returns:
            Local path to downloaded adapter
        """
        # Parse MinIO path
        parts = minio_path.replace("minio://", "").split("/", 1)
        bucket = parts[0]
        prefix = parts[1]

        local_path = f"/tmp/adapter_{os.urandom(8).hex()}"
        os.makedirs(local_path, exist_ok=True)

        # Download all files in adapter directory
        objects = self.minio_client.list_objects(bucket, prefix=prefix, recursive=True)
        for obj in objects:
            local_file = os.path.join(local_path, os.path.basename(obj.object_name))
            self.minio_client.fget_object(bucket, obj.object_name, local_file)
            logger.info(f"Downloaded: {obj.object_name} → {local_file}")

        return local_path

    def _upload_merged_model_to_minio(self, local_path: str, model_id: str) -> str:
        """
        Upload merged model to MinIO

        Returns:
            MinIO path to merged model
        """
        bucket = "models"  # Or use settings.MINIO_BUCKET
        prefix = f"finetuned/{model_id}/merged_model"

        # Upload all files in merged model directory
        for root, dirs, files in os.walk(local_path):
            for file in files:
                local_file = os.path.join(root, file)
                object_name = f"{prefix}/{file}"

                self.minio_client.fput_object(
                    bucket,
                    object_name,
                    local_file
                )
                logger.info(f"Uploaded: {local_file} → minio://{bucket}/{object_name}")

        return f"minio://{bucket}/{prefix}"

    def _update_merge_status(self, model_id: str, status: str):
        """Update merge_status in database"""
        from sqlalchemy import text

        self.db.execute(
            text("""
                UPDATE finetuned_models
                SET merge_status = :status,
                    merge_requested_at = NOW()
                WHERE id = :model_id
            """),
            {"status": status, "model_id": model_id}
        )
        self.db.commit()

    def _update_merge_complete(
        self,
        model_id: str,
        merged_path: str,
        duration_seconds: int
    ):
        """Update database with merge completion"""
        from sqlalchemy import text

        self.db.execute(
            text("""
                UPDATE finetuned_models
                SET merge_status = 'merged',
                    merged_model_path = :merged_path,
                    merge_duration_seconds = :duration
                WHERE id = :model_id
            """),
            {
                "model_id": model_id,
                "merged_path": merged_path,
                "duration": duration_seconds
            }
        )
        self.db.commit()

    def _update_merge_failed(self, model_id: str, error_message: str):
        """Update database with merge failure"""
        from sqlalchemy import text

        self.db.execute(
            text("""
                UPDATE finetuned_models
                SET merge_status = 'merge_failed',
                    merge_error_message = :error
                WHERE id = :model_id
            """),
            {"model_id": model_id, "error": error_message}
        )
        self.db.commit()

    def _get_directory_size_mb(self, path: str) -> int:
        """Calculate directory size in MB"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        return int(total_size / (1024 * 1024))
```

---

### Phase 4: Celery Background Task

**File**: `backend/app/tasks/finetuning_tasks.py` (add to existing file)

```python
from celery import Task
from app.services.finetuning.model_merge_service import ModelMergeService
from app.core.database import get_db

@celery.task(name="merge_lora_model", bind=True)
def merge_lora_model_task(
    self: Task,
    model_id: str,
    adapter_path: str,
    base_model: str,
    output_name: str = None
):
    """
    Background task for merging LoRA adapters

    Args:
        model_id: UUID of finetuned model
        adapter_path: MinIO path to adapter files
        base_model: HuggingFace model name
        output_name: Optional custom name

    Duration: 5-15 minutes for 1.5B models
    """
    db = next(get_db())  # Get database session

    try:
        merge_service = ModelMergeService(db)
        result = merge_service.merge_lora_adapters(
            model_id=model_id,
            adapter_path=adapter_path,
            base_model=base_model,
            output_name=output_name
        )

        logger.info(f"✅ Merge complete: {result['merged_model_path']}")
        return result

    except Exception as e:
        logger.error(f"❌ Merge failed for {model_id}: {e}")
        raise
    finally:
        db.close()
```

---

### Phase 5: API Route Implementation

**File**: `backend/app/api/routes/finetuning_routes.py` (add to existing routes)

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.tasks.finetuning_tasks import merge_lora_model_task
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class MergeRequest(BaseModel):
    output_name: Optional[str] = None

@router.post("/api/v1/finetuning/models/{model_id}/merge")
async def merge_lora_adapters(
    model_id: str,
    request: MergeRequest,
    db: Session = Depends(get_db)
):
    """
    Initiate merge process for fine-tuned model

    Merges LoRA adapters with base model to create standalone model
    """
    # 1. Get model record from database
    model = db.execute(
        text("SELECT * FROM finetuned_models WHERE id = :id"),
        {"id": model_id}
    ).fetchone()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # 2. Check if already merged or merging
    if model.merge_status == "merged":
        raise HTTPException(
            status_code=400,
            detail="Model already merged"
        )

    if model.merge_status == "merging":
        raise HTTPException(
            status_code=400,
            detail="Merge already in progress"
        )

    # 3. Get adapter path and base model from model record
    adapter_path = model.checkpoint_path  # Adjust based on your schema
    base_model = model.base_model_name    # e.g., "Qwen/Qwen2.5-1.5B-Instruct"

    # 4. Trigger Celery task
    task = merge_lora_model_task.delay(
        model_id=model_id,
        adapter_path=adapter_path,
        base_model=base_model,
        output_name=request.output_name
    )

    return {
        "message": "Merge process started",
        "model_id": model_id,
        "task_id": str(task.id),
        "estimated_duration_minutes": 8,
        "status": "merging"
    }


@router.get("/api/v1/finetuning/models/{model_id}/merge-status")
async def get_merge_status(
    model_id: str,
    db: Session = Depends(get_db)
):
    """
    Get merge status for model
    """
    model = db.execute(
        text("""
            SELECT
                merge_status,
                merged_model_path,
                merge_duration_seconds,
                merge_requested_at,
                merge_error_message
            FROM finetuned_models
            WHERE id = :id
        """),
        {"id": model_id}
    ).fetchone()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    return {
        "model_id": model_id,
        "merge_status": model.merge_status,
        "merged_model_path": model.merged_model_path,
        "merge_duration_seconds": model.merge_duration_seconds,
        "merge_requested_at": model.merge_requested_at,
        "merge_error_message": model.merge_error_message
    }
```

---

### Phase 6: Frontend UI Integration

**Assumption**: You already have a fine-tuning model list/card UI.

**Add to existing component** (e.g., `frontend/src/components/finetuning/ModelCard.tsx`):

```typescript
// Add merge status display
const getMergeStatusBadge = (status: string) => {
  switch (status) {
    case 'not_merged':
      return <Badge variant="secondary">Adapter Only</Badge>;
    case 'merging':
      return <Badge variant="info">Merging...</Badge>;
    case 'merged':
      return <Badge variant="success">Merged</Badge>;
    case 'merge_failed':
      return <Badge variant="danger">Merge Failed</Badge>;
    default:
      return null;
  }
};

// Add merge button handler
const handleMerge = async (modelId: string) => {
  try {
    setMerging(true);
    const response = await axios.post(
      `/api/v1/finetuning/models/${modelId}/merge`,
      { output_name: null }
    );

    toast.success('Merge started! This will take 5-15 minutes.');

    // Poll for status updates
    const interval = setInterval(async () => {
      const status = await axios.get(
        `/api/v1/finetuning/models/${modelId}/merge-status`
      );

      if (status.data.merge_status === 'merged') {
        clearInterval(interval);
        toast.success('Merge completed!');
        refreshModels();
      } else if (status.data.merge_status === 'merge_failed') {
        clearInterval(interval);
        toast.error('Merge failed: ' + status.data.merge_error_message);
      }
    }, 10000); // Poll every 10 seconds

  } catch (error) {
    toast.error('Failed to start merge: ' + error.message);
  } finally {
    setMerging(false);
  }
};

// UI rendering
<div className="model-card">
  <div className="model-header">
    <h3>{model.name}</h3>
    {getMergeStatusBadge(model.merge_status)}
  </div>

  <div className="model-actions">
    {model.merge_status === 'not_merged' && (
      <button
        onClick={() => handleMerge(model.id)}
        disabled={merging}
      >
        {merging ? 'Starting Merge...' : 'Merge Adapters'}
      </button>
    )}

    {model.merge_status === 'merged' && (
      <button onClick={() => deployToOllama(model.id)}>
        Deploy to Ollama
      </button>
    )}
  </div>
</div>
```

---

## Testing Plan

### Unit Tests

```python
# backend/tests/test_model_merge_service.py

def test_merge_lora_adapters(db_session):
    """Test adapter merge functionality"""
    service = ModelMergeService(db_session)

    result = service.merge_lora_adapters(
        model_id="test-model-id",
        adapter_path="minio://models/test-adapter",
        base_model="Qwen/Qwen2.5-1.5B-Instruct"
    )

    assert result["status"] == "success"
    assert "merged_model_path" in result
    assert result["model_size_mb"] > 0

def test_merge_status_updates(db_session):
    """Test database status updates during merge"""
    # Test status transitions: not_merged → merging → merged
    pass
```

### Integration Tests

```bash
# Manual testing workflow
# 1. Train a model (produces adapters)
# 2. Click "Merge Adapters" button
# 3. Monitor Celery logs: docker-compose logs -f celery
# 4. Wait 5-15 minutes
# 5. Verify merged model in MinIO
# 6. Check database: merge_status = 'merged'
# 7. Click "Deploy to Ollama" (your existing UI)
```

---

## Performance Considerations

### Resource Requirements

- **VRAM**: Requires GPU memory = base model size (e.g., 3.2 GB for 1.5B model)
- **Duration**: 5-15 minutes for 1.5B models
- **Storage**: Merged model = base model size (3.2 GB)

### Optimization Strategies

1. **CPU Fallback**: If GPU unavailable, use CPU (slower but works)
2. **Merge Queue**: Process one merge at a time to avoid OOM
3. **HuggingFace Cache**: Base models cached locally after first download
4. **Float16**: Use `torch_dtype=torch.float16` to reduce memory

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| OOM during merge | High | Queue merges, use CPU fallback, monitor GPU memory |
| Merge fails silently | Medium | Comprehensive error logging, status updates |
| Storage bloat | Medium | Auto-delete old merged models, retention policy |
| Concurrent merges | High | Implement merge queue/lock in Celery |

---

## Dependencies

✅ Already in requirements:
- `peft` library
- `transformers` library
- `torch` library
- MinIO client
- Celery

---

## Timeline Estimate

- **Phase 1 (DB Schema)**: 1 hour (check if exists, create migration)
- **Phase 2 (API Endpoints)**: 2 hours
- **Phase 3 (Merge Service)**: 6 hours
- **Phase 4 (Celery Task)**: 2 hours
- **Phase 5 (API Routes)**: 2 hours
- **Phase 6 (Frontend UI)**: 4 hours (integrate with existing UI)
- **Testing**: 4 hours

**Total**: ~21 hours (~3 days for 1 developer)

**Note**: This is MUCH faster than the full implementation because:
- Ollama deployment UI/backend already exists
- Only implementing merge functionality
- No new frontend components needed (integrate with existing)

---

## Success Metrics

- [ ] Users can merge adapters via UI
- [ ] Merge completes in < 15 minutes for 1.5B models
- [ ] Merged models saved to MinIO successfully
- [ ] Database status tracking works (not_merged → merging → merged)
- [ ] Error handling captures and logs failures
- [ ] UI shows real-time status updates

---

## Implementation Checklist

### Backend

- [ ] Create database migration (if columns don't exist)
- [ ] Implement `ModelMergeService` class
- [ ] Add Celery task `merge_lora_model_task`
- [ ] Create API endpoints (POST /merge, GET /merge-status)
- [ ] Add error handling and logging
- [ ] Write unit tests

### Frontend

- [ ] Add merge status badge to model cards
- [ ] Add "Merge Adapters" button
- [ ] Implement merge handler with status polling
- [ ] Add loading/progress indicators
- [ ] Show merge errors to user

### Testing

- [ ] Unit test merge service
- [ ] Test database status updates
- [ ] Test MinIO upload/download
- [ ] End-to-end test: train → merge → deploy (using existing Ollama deployment)

---

## Related Documentation

- `/tmp/TRAINING36_SUCCESS_REPORT.md` - Training pipeline working
- `/tmp/TRAINING37_SUCCESS_REPORT.md` - Validation of bug fixes
- `docs/features/FINETUNING_COMPLETE_IMPLEMENTATION_GUIDE.md`

---

**Status**: Ready for Implementation
**Next Steps**:
1. Verify Ollama deployment UI/backend paths
2. Check if database columns exist
3. Assign to developer
4. Create sprint backlog items

---

**JIRA Comments**:
- [2025-12-22] User confirmed: Ollama deployment UI/backend already exists
- [2025-12-22] Simplified to merge-only implementation (~21 hours)
- [2025-12-22] Approved for next sprint
