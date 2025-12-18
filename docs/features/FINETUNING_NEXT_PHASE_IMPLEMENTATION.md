# Fine-Tuning Next Phase Implementation Guide

**Created**: 2025-12-15
**Status**: ✅ In Progress
**Phase**: Enhancement & Integration
**Target**: Complete the remaining 50% to production-ready

---

## Overview

This document outlines the enhancements needed to complete the fine-tuning system based on existing architecture. We're at **~50% completion** with strong foundation - now completing the integration and missing features.

---

## Current Status

### ✅ What's Complete (Backend)
- Database schema with 4 tables + triggers
- ORM models and Pydantic schemas (28+ schemas)
- REST API with 20+ endpoints
- WebSocket API for real-time metrics
- PEFT, SFT, RLHF-PPO, RLHF-GRPO trainers
- Base trainer with callback system
- Dataset preprocessor with 5 formatters
- Fine-tuning service orchestration
- Model registry with versioning
- GPU Pool Manager
- Fin et un Sandbox Manager (extends AgentSandboxManager)
- Hyperparameter tuning service (Optuna)

### ✅ What's Complete (Frontend)
- FineTuningGovernanceUI (role-based navigation)
- ModelCatalog (consumer GPU optimized)
- DatasetInspector (quality metrics)
- JobManager (3 hyperparameter modes)
- DatasetManager, ModelManager, GPUMonitor
- TrainingJobsManagerEnhanced (comprehensive grid)
- WebSocket client integration

### 🔴 What's Missing (Critical Gaps)
1. **Sandbox-GPU Integration**: FineTuningSandboxManager doesn't call gpu_pool_manager
2. **MinIO Integration**: Dataset download and checkpoint upload are TODO
3. **Deployment Strategies**: Ollama and vLLM deployment not implemented
4. **Evaluation Executor**: No automatic evaluation implementation
5. **WebSocket Auto-Metrics**: Metrics not auto-streamed from trainers
6. **Stub Components**: 5 frontend components are placeholders

---

## Phase 4 Implementation Plan

### Priority 1: Core Integration (Week 1)

#### 1.1 Sandbox-GPU Integration

**File**: `backend/app/services/finetuning/finetuning_sandbox_manager.py`

**Enhancement**: Add GPU allocation before training

```python
async def execute_training(
    self,
    job_id: str,
    trainer_script: str,
    config: Dict[str, Any],
    memory_required_gb: float = 12.0,
    timeout_hours: int = 24
) -> Dict[str, Any]:
    """Execute training with automatic GPU allocation"""

    from app.services.finetuning.gpu_pool_manager import gpu_pool_manager

    logger.info(f"🚀 Starting training job {job_id}")

    # ✨ NEW: Allocate GPU from pool
    gpu_devices = await gpu_pool_manager.allocate_gpu(
        job_id=job_id,
        count=1,  # Single GPU for consumer setup
        memory_required_gb=memory_required_gb
    )

    if not gpu_devices:
        logger.warning(f"⏳ No GPU available, queuing job {job_id}")
        gpu_devices = await gpu_pool_manager.wait_for_gpu(
            job_id=job_id,
            timeout_seconds=3600  # 1 hour max wait
        )

        if not gpu_devices:
            raise RuntimeError("GPU allocation timeout - no available GPUs")

    gpu_ids_str = ",".join(gpu_devices)
    logger.info(f"✅ Allocated GPUs: {gpu_ids_str} for job {job_id}")

    try:
        # Create workspace
        workspace = await self.create_training_workspace(job_id)

        # ... rest of existing code ...

        # Launch container with allocated GPUs
        container = self.docker_client.containers.run(
            image=self.finetuning_image,
            name=f"finetuning-{job_id}",
            device_requests=[
                docker.types.DeviceRequest(
                    device_ids=gpu_devices,  # Use allocated GPUs
                    capabilities=[['gpu']]
                )
            ],
            # ... rest of config ...
        )

        return result

    except Exception as e:
        logger.error(f"❌ Training failed: {e}")
        raise
    finally:
        # ✨ NEW: Always release GPU
        await gpu_pool_manager.release_gpu(job_id)
        logger.info(f"🔓 Released GPUs for job {job_id}")
```

**Integration Point**: Called from `FineTuningService.submit_job()`

---

#### 1.2 MinIO Integration

**Part A: Dataset Download**

**File**: `backend/app/services/finetuning/finetuning_sandbox_manager.py`

```python
async def _copy_dataset_to_workspace(
    self,
    dataset_minio_path: str,
    input_dir: Path
):
    """Download dataset from MinIO to workspace"""
    from app.services.minio_path_builder import minio_client
    from app.core.config import settings

    try:
        bucket_name = settings.MINIO_BUCKET_NAME or "rag-documents"

        # Parse MinIO path (format: "path/to/dataset.jsonl")
        object_name = dataset_minio_path
        local_path = input_dir / Path(object_name).name

        logger.info(f"📥 Downloading dataset from MinIO: {bucket_name}/{object_name}")

        # Download from MinIO
        minio_client.fget_object(
            bucket_name=bucket_name,
            object_name=object_name,
            file_path=str(local_path)
        )

        logger.info(f"✅ Dataset downloaded to {local_path}")
        return local_path

    except Exception as e:
        logger.error(f"❌ Failed to download dataset from MinIO: {e}")
        raise RuntimeError(f"Dataset download failed: {e}")
```

**Part B: Checkpoint Upload**

```python
async def upload_checkpoint_to_minio(
    self,
    job_id: str,
    checkpoint_dir: Path,
    org_path: str
) -> str:
    """Upload trained model checkpoint to MinIO"""
    from app.services.minio_path_builder import minio_client, MinIOPathBuilder
    from app.core.config import settings

    try:
        bucket_name = settings.MINIO_BUCKET_NAME or "rag-documents"

        # Build organizational path
        # Format: {org_path}/finetuning-checkpoints/{job_id}/
        minio_base_path = f"{org_path}/finetuning-checkpoints/{job_id}/"

        logger.info(f"📤 Uploading checkpoint to MinIO: {minio_base_path}")

        uploaded_files = []

        # Upload all files in checkpoint directory
        for file_path in checkpoint_dir.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(checkpoint_dir)
                object_name = f"{minio_base_path}{relative_path}"

                minio_client.fput_object(
                    bucket_name=bucket_name,
                    object_name=object_name,
                    file_path=str(file_path)
                )

                uploaded_files.append(object_name)
                logger.debug(f"  ✓ Uploaded {relative_path}")

        logger.info(f"✅ Uploaded {len(uploaded_files)} files to MinIO")
        return minio_base_path

    except Exception as e:
        logger.error(f"❌ Failed to upload checkpoint: {e}")
        raise RuntimeError(f"Checkpoint upload failed: {e}")
```

**Integration**: Called after training completes successfully

---

#### 1.3 WebSocket Auto-Metrics

**Challenge**: Trainers currently don't auto-send metrics to WebSocket

**Solution**: Add metric callback to base trainer

**File**: `backend/app/services/finetuning/trainers/base_trainer.py`

```python
class WebSocketMetricsCallback(TrainingCallback):
    """Automatically send metrics to WebSocket subscribers"""

    def __init__(self, job_id: str):
        self.job_id = job_id

    async def on_step_end(self, trainer, step: int, metrics: Dict[str, float]):
        """Send metrics after each training step"""
        from app.api.routes.finetuning_websocket import send_metric_update

        await send_metric_update(
            job_id=self.job_id,
            metric={
                "timestamp": datetime.now().isoformat(),
                "step": step,
                "epoch": trainer.current_epoch,
                "train_loss": metrics.get("loss"),
                "learning_rate": metrics.get("learning_rate"),
                "gpu_memory": metrics.get("gpu_memory_allocated"),
            }
        )

    async def on_epoch_end(self, trainer, epoch: int, metrics: Dict[str, float]):
        """Send progress update after each epoch"""
        from app.api.routes.finetuning_websocket import send_progress_update

        progress_pct = (epoch / trainer.config.num_epochs) * 100

        await send_progress_update(
            job_id=self.job_id,
            progress={
                "epoch": epoch,
                "total_epochs": trainer.config.num_epochs,
                "progress_percentage": progress_pct,
                "eval_loss": metrics.get("eval_loss"),
            }
        )
```

**Usage in PEFT Trainer**:

```python
# backend/app/services/finetuning/trainers/peft_trainer.py

def train(self, config: TrainingConfig):
    """Train with WebSocket metrics callback"""

    # Add WebSocket callback
    ws_callback = WebSocketMetricsCallback(job_id=config.job_id)
    config.callbacks.append(ws_callback)

    # ... rest of training code ...
```

---

### Priority 2: Deployment & Evaluation (Week 2)

#### 2.1 Ollama Deployment Strategy

**File**: `backend/app/services/finetuning/model_registry_service.py`

```python
class OllamaDeploymentStrategy(ModelDeploymentStrategy):
    """Deploy fine-tuned model to Ollama"""

    async def deploy(
        self,
        model: FineTunedModel,
        deployment_config: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, str]:
        """
        Deploy model to Ollama

        Steps:
        1. Download checkpoint from MinIO
        2. Merge adapter with base model (if PEFT)
        3. Create Ollama Modelfile
        4. Push to Ollama
        5. Update database
        """
        import httpx
        import tempfile
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel

        logger.info(f"🚀 Deploying model {model.model_name} to Ollama")

        try:
            # 1. Download checkpoint from MinIO
            with tempfile.TemporaryDirectory() as temp_dir:
                checkpoint_dir = Path(temp_dir) / "checkpoint"
                checkpoint_dir.mkdir()

                await self._download_checkpoint_from_minio(
                    minio_path=model.minio_checkpoint_path,
                    local_dir=checkpoint_dir
                )

                # 2. Load and merge model (if PEFT)
                if model.finetuning_method == "peft":
                    logger.info("🔀 Merging LoRA adapter with base model")

                    # Load base model
                    base_model = AutoModelForCausalLM.from_pretrained(
                        model.base_model,
                        load_in_8bit=False,
                        device_map="cpu"  # Merge on CPU
                    )

                    # Load and merge adapter
                    merged_model = PeftModel.from_pretrained(
                        base_model,
                        str(checkpoint_dir)
                    )
                    merged_model = merged_model.merge_and_unload()

                    # Save merged model
                    merged_dir = checkpoint_dir / "merged"
                    merged_dir.mkdir()
                    merged_model.save_pretrained(str(merged_dir))

                    tokenizer = AutoTokenizer.from_pretrained(model.base_model)
                    tokenizer.save_pretrained(str(merged_dir))

                    model_path = merged_dir
                else:
                    model_path = checkpoint_dir

                # 3. Create Ollama Modelfile
                modelfile = f"""
FROM {model_path}

TEMPLATE \"\"\"{{{{ if .System }}}}{{{{ .System }}}}{{{{ end }}}}{{{{ if .Prompt }}}}{{{{ .Prompt }}}}{{{{ end }}}}\"\"\"

PARAMETER temperature 0.7
PARAMETER top_k 40
PARAMETER top_p 0.9
PARAMETER num_ctx 4096
"""

                modelfile_path = checkpoint_dir / "Modelfile"
                with open(modelfile_path, 'w') as f:
                    f.write(modelfile)

                # 4. Push to Ollama
                ollama_model_name = f"{model.model_name}:v{model.version}"

                async with httpx.AsyncClient(timeout=600.0) as client:
                    # Create model in Ollama
                    create_response = await client.post(
                        f"{settings.OLLAMA_BASE_URL}/api/create",
                        json={
                            "name": ollama_model_name,
                            "modelfile": modelfile,
                            "stream": False
                        }
                    )

                    if create_response.status_code != 200:
                        raise RuntimeError(f"Ollama create failed: {create_response.text}")

                    logger.info(f"✅ Model pushed to Ollama: {ollama_model_name}")

                # 5. Update database
                model.ollama_model_name = ollama_model_name
                model.deployment_url = f"{settings.OLLAMA_BASE_URL}/api/generate"
                model.status = "deployed"

                await db.commit()

                return {
                    "ollama_model_name": ollama_model_name,
                    "deployment_url": model.deployment_url,
                    "status": "deployed"
                }

        except Exception as e:
            logger.error(f"❌ Deployment failed: {e}")
            model.status = "registered"  # Rollback status
            await db.commit()
            raise RuntimeError(f"Deployment failed: {e}")

    async def undeploy(self, model: FineTunedModel, db: AsyncSession):
        """Remove model from Ollama"""
        import httpx

        try:
            if not model.ollama_model_name:
                raise ValueError("Model not deployed to Ollama")

            async with httpx.AsyncClient() as client:
                # Delete model from Ollama
                delete_response = await client.delete(
                    f"{settings.OLLAMA_BASE_URL}/api/delete",
                    json={"name": model.ollama_model_name}
                )

                if delete_response.status_code != 200:
                    logger.warning(f"Ollama delete warning: {delete_response.text}")

            # Update database
            model.status = "archived"
            model.deployment_url = None

            await db.commit()

            logger.info(f"✅ Model removed from Ollama: {model.ollama_model_name}")

        except Exception as e:
            logger.error(f"❌ Undeployment failed: {e}")
            raise
```

**Integration**: Called from deployment API endpoint

---

#### 2.2 Evaluation Hub (Frontend)

**File**: `frontend/src/components/finetuning/EvaluationHub.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import { Target, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react';

interface Evaluation {
  id: string;
  model_id: string;
  model_name: string;
  test_dataset_id: string;
  status: 'running' | 'completed' | 'failed';
  metrics: {
    accuracy?: number;
    perplexity?: number;
    rouge_1?: number;
    rouge_l?: number;
    bleu?: number;
    f1?: number;
  };
  created_at: string;
}

export default function EvaluationHub({ userRole }: { userRole: string }) {
  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [models, setModels] = useState<any[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [running, setRunning] = useState(false);

  const fetchEvaluations = async () => {
    // Fetch from /api/v1/finetuning/evaluations
  };

  const fetchModels = async () => {
    // Fetch registered models
  };

  const runEvaluation = async () => {
    setRunning(true);
    try {
      const token = localStorage.getItem('access_token');
      const headers = token ? {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      } : {};

      await fetch('http://localhost:8000/api/v1/finetuning/evaluations', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          model_id: selectedModel,
          metrics: ['accuracy', 'perplexity', 'rouge', 'bleu']
        })
      });

      await fetchEvaluations();
    } catch (error) {
      console.error('Evaluation failed:', error);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Evaluation Dashboard */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border p-6">
        <h3 className="text-lg font-semibold mb-4">Run Evaluation</h3>

        <div className="grid grid-cols-2 gap-4">
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="px-4 py-2 border rounded-lg"
          >
            <option value="">Select Model</option>
            {models.map(m => (
              <option key={m.id} value={m.id}>{m.model_name} v{m.version}</option>
            ))}
          </select>

          <button
            onClick={runEvaluation}
            disabled={!selectedModel || running}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg disabled:opacity-50"
          >
            {running ? 'Running...' : 'Run Evaluation'}
          </button>
        </div>
      </div>

      {/* Evaluation Results */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {evaluations.map(eval => (
          <div key={eval.id} className="bg-white dark:bg-gray-800 rounded-lg border p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold">{eval.model_name}</h4>
              {eval.status === 'completed' ? (
                <CheckCircle className="w-5 h-5 text-green-500" />
              ) : (
                <AlertCircle className="w-5 h-5 text-yellow-500" />
              )}
            </div>

            {eval.metrics && (
              <div className="space-y-2 text-sm">
                {eval.metrics.accuracy && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Accuracy:</span>
                    <span className="font-semibold">{(eval.metrics.accuracy * 100).toFixed(2)}%</span>
                  </div>
                )}
                {eval.metrics.perplexity && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Perplexity:</span>
                    <span className="font-semibold">{eval.metrics.perplexity.toFixed(2)}</span>
                  </div>
                )}
                {eval.metrics.rouge_1 && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">ROUGE-1:</span>
                    <span className="font-semibold">{(eval.metrics.rouge_1 * 100).toFixed(2)}%</span>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

### Priority 3: Monitoring & Governance (Week 3)

**Components to build**:
1. MonitoringDashboard with Charts.js/Recharts
2. GovernanceAudit with approval workflow
3. AdapterVersions with Git-like diff

---

## Testing Strategy

### Integration Tests

```python
# tests/test_finetuning_integration.py

async def test_end_to_end_training():
    """Test complete training workflow with sandbox and GPU"""

    # 1. Create dataset
    dataset = await create_test_dataset()

    # 2. Create job
    job = await create_training_job(dataset_id=dataset.id)

    # 3. Submit job (should allocate GPU)
    await submit_job(job.id)

    # 4. Wait for completion (with timeout)
    await wait_for_job_completion(job.id, timeout=300)

    # 5. Verify checkpoint uploaded to MinIO
    assert job.minio_checkpoint_path is not None

    # 6. Register model
    model = await register_model_from_job(job.id)

    # 7. Deploy to Ollama
    await deploy_model(model.id, target="ollama")

    # 8. Test inference
    response = await test_ollama_inference(model.ollama_model_name)
    assert response is not None
```

---

## Deployment Checklist

- [ ] GPU Pool Manager integrated with sandbox
- [ ] MinIO download/upload implemented
- [ ] WebSocket auto-metrics from trainers
- [ ] Ollama deployment strategy complete
- [ ] vLLM deployment strategy complete
- [ ] Evaluation executor with `evaluate` library
- [ ] All frontend stubs replaced with full components
- [ ] End-to-end tests passing
- [ ] Documentation updated
- [ ] Performance benchmarks run

---

## Expected Outcomes

After completing this phase:
- ✅ **100% Backend Implementation** - All TODOs resolved
- ✅ **100% Frontend Implementation** - No more stubs
- ✅ **Full E2E Workflow** - Dataset → Train → Evaluate → Deploy → Inference
- ✅ **Consumer GPU Optimized** - Runs on RTX 3090/4090
- ✅ **Production Ready** - Enterprise-grade governance and monitoring

---

**End of Document**
