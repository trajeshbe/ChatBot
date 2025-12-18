# Fine-Tuning Complete Lifecycle - Implementation Plan

**Date**: 2025-12-17
**Status**: 📋 **PLANNING** - Comprehensive feature roadmap
**Current State**: Training works, but Evaluation/Deployment/Monitoring/Governance tabs are empty

---

## Executive Summary

The fine-tuning system successfully trains models via Celery, but the complete MLOps lifecycle is incomplete. This document outlines the implementation plan for:

1. **Model Artifact Storage** (MinIO checkpoints)
2. **Evaluation Tab** (metrics, validation, comparison)
3. **Deployment Tab** (Ollama/vLLM integration)
4. **Monitoring Tab** (usage metrics, performance tracking)
5. **Governance Tab** (approval workflow, audit trail)
6. **Chat UI Integration** (model registry → dropdown)

---

## Current State Analysis

### ✅ What's Working
- Training job submission via Celery
- GPU allocation and management
- Progress tracking in database
- Basic job lifecycle (pending → queued → running → completed)

### ❌ What's Missing

**Critical Issues**:
1. **No checkpoint storage**: `minio_checkpoint_path` is NULL after training completes
2. **No model registry**: Trained models don't create entries in `finetuned_models` table
3. **No evaluation**: `eval_metrics` field is empty
4. **No deployment**: Models can't be loaded into Ollama/vLLM for inference
5. **No Chat UI integration**: Trained models don't appear in model dropdown
6. **Empty UI tabs**: Evaluation, Deployment, Monitoring, Governance show no data

**Database State**:
```sql
-- Current model1 state
name: model1
status: completed
minio_checkpoint_path: NULL  ❌ Should contain MinIO path
progress: 100
celery_task_id: ad34b092-4262-4bec-87ba-14078ece1a83

-- No entry in finetuned_models table ❌
SELECT COUNT(*) FROM finetuned_models WHERE job_id IN (SELECT id FROM finetuning_jobs WHERE name='model1');
-- Result: 0
```

---

## Implementation Phases

## Phase 1: Model Artifact Storage (P0 - Critical)

### Overview
Save trained model checkpoints to MinIO during training completion.

### Database Schema
Already exists:
```sql
-- finetuning_jobs table
minio_checkpoint_path VARCHAR(512)

-- finetuned_models table
minio_checkpoint_path VARCHAR(512)
```

### Implementation Tasks

#### 1.1: Update Training Task to Upload Checkpoints
**File**: `backend/app/tasks/finetuning_tasks.py`

**Changes Needed** (lines 250-270):
```python
# Current (BROKEN):
result = asyncio.run(sandbox_manager.execute_training(...))

# Training completed successfully
job.status = "completed"
job.minio_checkpoint_path = result.get("checkpoint_path")  # This is None!

# Fixed:
result = asyncio.run(sandbox_manager.execute_training(...))

# Upload checkpoint to MinIO
from minio import Minio
minio_client = Minio(...)
checkpoint_dir = f"/workspace/output/{job_id}/checkpoints"

# Find latest checkpoint
checkpoint_files = glob.glob(f"{checkpoint_dir}/**/*.safetensors", recursive=True)
if checkpoint_files:
    latest_checkpoint = max(checkpoint_files, key=os.path.getmtime)

    # Upload to MinIO
    bucket_name = "finetuning-artifacts"
    object_name = f"jobs/{job_id}/checkpoints/{os.path.basename(latest_checkpoint)}"

    minio_client.fput_object(
        bucket_name=bucket_name,
        object_name=object_name,
        file_path=latest_checkpoint
    )

    minio_path = f"minio://{bucket_name}/{object_name}"
    job.minio_checkpoint_path = minio_path

    logger.info(f"Uploaded checkpoint to MinIO: {minio_path}")
```

**API Endpoint**:
```python
# backend/app/api/routes/finetuning_routes.py
@router.get("/jobs/{job_id}/artifacts")
async def get_job_artifacts(job_id: str):
    """Get model artifacts (checkpoint files, logs, metrics)"""
    return {
        "checkpoint_path": job.minio_checkpoint_path,
        "checkpoint_size_mb": 1234,
        "logs_path": f"minio://logs/{job_id}/training.log",
        "tensorboard_path": f"minio://tensorboard/{job_id}/"
    }
```

#### 1.2: MinIO Bucket Setup
**Script**: `backend/scripts/setup_minio_buckets.py`

```python
from minio import Minio

client = Minio(
    endpoint="minio:9000",
    access_key=os.getenv("MINIO_ROOT_USER"),
    secret_key=os.getenv("MINIO_ROOT_PASSWORD"),
    secure=False
)

# Create buckets
buckets = [
    "finetuning-artifacts",
    "training-logs",
    "evaluation-results",
    "tensorboard-logs"
]

for bucket in buckets:
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        print(f"✅ Created bucket: {bucket}")
```

#### 1.3: Frontend - Show Artifacts
**File**: `frontend/src/components/finetuning/JobDetails.tsx`

```typescript
const JobArtifacts: React.FC<{ jobId: string }> = ({ jobId }) => {
  const [artifacts, setArtifacts] = useState<any>(null)

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/finetuning/jobs/${jobId}/artifacts`)
      .then(res => res.json())
      .then(setArtifacts)
  }, [jobId])

  return (
    <div>
      <h3>Model Artifacts</h3>
      {artifacts?.checkpoint_path ? (
        <a href={artifacts.checkpoint_path} download>
          📦 Download Checkpoint ({artifacts.checkpoint_size_mb}MB)
        </a>
      ) : (
        <p>No artifacts available</p>
      )}
    </div>
  )
}
```

---

## Phase 2: Model Registry (P0 - Critical)

### Overview
After training completes, automatically create entry in `finetuned_models` table for model registry.

### Implementation Tasks

#### 2.1: Auto-Register Model After Training
**File**: `backend/app/tasks/finetuning_tasks.py`

**Changes** (add after checkpoint upload):
```python
# After training completes and checkpoint uploaded
from app.models.finetuning_models import FineTunedModel

# Create model registry entry
finetuned_model = FineTunedModel(
    name=f"{job.name}-v1.0",
    version="1.0",
    description=f"Fine-tuned {job.base_model} for {job.training_objective}",
    job_id=job_uuid,
    base_model=job.base_model,
    finetuning_method=job.finetuning_method,
    minio_checkpoint_path=job.minio_checkpoint_path,
    status="trained",  # Not deployed yet
    created_by=job.created_by,
    project_id=job.project_id,
    tags={"method": job.finetuning_method, "objective": job.training_objective}
)
db.add(finetuned_model)
db.commit()

logger.info(f"Registered model in registry: {finetuned_model.id}")
```

#### 2.2: Model Registry API
**File**: `backend/app/api/routes/model_registry_routes.py` (NEW)

```python
@router.get("/models")
async def list_models(
    status: Optional[str] = None,
    project_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all fine-tuned models in registry"""
    query = select(FineTunedModel)
    if status:
        query = query.where(FineTunedModel.status == status)
    if project_id:
        query = query.where(FineTunedModel.project_id == project_id)

    result = await db.execute(query)
    models = result.scalars().all()
    return models


@router.get("/models/{model_id}")
async def get_model(model_id: str, db: AsyncSession = Depends(get_db)):
    """Get model details"""
    result = await db.execute(
        select(FineTunedModel).where(FineTunedModel.id == model_id)
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.post("/models/{model_id}/approve")
async def approve_model(
    model_id: str,
    user: User = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """Approve model for deployment"""
    result = await db.execute(
        select(FineTunedModel).where(FineTunedModel.id == model_id)
    )
    model = result.scalar_one_or_none()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # Update status
    model.status = "approved"
    await db.commit()

    return {"message": "Model approved", "status": "approved"}
```

---

## Phase 3: Evaluation Tab (P1 - High Priority)

### Overview
Add evaluation metrics, validation results, and comparison with baseline models.

### Database Fields
```sql
-- finetuned_models.eval_metrics (JSON)
{
  "accuracy": 0.92,
  "loss": 0.145,
  "perplexity": 1.23,
  "bleu_score": 0.85,
  "rouge_l": 0.78,
  "eval_dataset_size": 1000,
  "eval_time_seconds": 45
}
```

### Implementation Tasks

#### 3.1: Add Evaluation Step to Training
**File**: `backend/app/tasks/finetuning_tasks.py`

```python
# After training completes, run evaluation
eval_result = asyncio.run(sandbox_manager.run_evaluation(
    job_id=job_id,
    checkpoint_path=job.minio_checkpoint_path,
    eval_dataset_path=f"/workspace/datasets/{job.dataset_id}/eval.jsonl"
))

# Store evaluation metrics
finetuned_model.eval_metrics = eval_result.get("metrics", {})
db.commit()
```

#### 3.2: Frontend Evaluation Tab
**File**: `frontend/src/components/finetuning/EvaluationTab.tsx`

```typescript
const EvaluationTab: React.FC<{ modelId: string }> = ({ modelId }) => {
  const [metrics, setMetrics] = useState<any>(null)

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/models/${modelId}`)
      .then(res => res.json())
      .then(data => setMetrics(data.eval_metrics))
  }, [modelId])

  return (
    <div>
      <h3>Evaluation Metrics</h3>
      {metrics ? (
        <div className="grid grid-cols-3 gap-4">
          <MetricCard label="Accuracy" value={metrics.accuracy} />
          <MetricCard label="Loss" value={metrics.loss} />
          <MetricCard label="Perplexity" value={metrics.perplexity} />
          <MetricCard label="BLEU Score" value={metrics.bleu_score} />
          <MetricCard label="ROUGE-L" value={metrics.rouge_l} />
        </div>
      ) : (
        <p>No evaluation data available</p>
      )}

      <h3>Model Comparison</h3>
      <ComparisonChart
        models={[
          { name: "Baseline", accuracy: 0.78 },
          { name: currentModel.name, accuracy: metrics.accuracy }
        ]}
      />
    </div>
  )
}
```

---

## Phase 4: Deployment Tab (P1 - High Priority)

### Overview
Deploy trained models to Ollama or vLLM for inference.

### Implementation Tasks

#### 4.1: Deploy to Ollama
**File**: `backend/app/services/finetuning/deployment_service.py` (NEW)

```python
class DeploymentService:
    async def deploy_to_ollama(
        self,
        model_id: UUID,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Deploy model to Ollama"""

        # Get model from registry
        result = await db.execute(
            select(FineTunedModel).where(FineTunedModel.id == model_id)
        )
        model = result.scalar_one_or_none()

        # Download checkpoint from MinIO
        local_path = await self._download_checkpoint(model.minio_checkpoint_path)

        # Create Ollama Modelfile
        modelfile = f"""
FROM {model.base_model}
ADAPTER {local_path}
PARAMETER temperature 0.7
PARAMETER top_p 0.9
"""

        # Create model in Ollama
        ollama_name = f"{model.name.lower().replace(' ', '-')}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://ollama:11434/api/create",
                json={
                    "name": ollama_name,
                    "modelfile": modelfile,
                    "stream": False
                }
            )

        if response.status_code == 200:
            # Update model registry
            model.ollama_model_name = ollama_name
            model.status = "deployed"
            model.deployment_url = f"http://ollama:11434/api/generate"
            await db.commit()

            return {
                "status": "deployed",
                "ollama_model_name": ollama_name,
                "deployment_url": model.deployment_url
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Ollama deployment failed: {response.text}"
            )
```

#### 4.2: Deploy to vLLM
```python
    async def deploy_to_vllm(
        self,
        model_id: UUID,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Deploy model to vLLM"""

        model = await self._get_model(model_id, db)

        # Download checkpoint
        local_path = await self._download_checkpoint(model.minio_checkpoint_path)

        # Start vLLM server with adapter
        vllm_name = f"vllm-{model.name.lower().replace(' ', '-')}"

        # Launch vLLM container
        docker_client = docker.from_env()
        container = docker_client.containers.run(
            image="vllm/vllm-openai:latest",
            name=vllm_name,
            command=[
                "--model", model.base_model,
                "--enable-lora",
                "--lora-modules", f"{model.name}={local_path}"
            ],
            ports={"8000/tcp": None},  # Random port
            detach=True,
            runtime="nvidia"
        )

        # Get assigned port
        container.reload()
        port = container.attrs['NetworkSettings']['Ports']['8000/tcp'][0]['HostPort']

        # Update model registry
        model.vllm_model_name = vllm_name
        model.status = "deployed"
        model.deployment_url = f"http://localhost:{port}/v1/completions"
        await db.commit()

        return {
            "status": "deployed",
            "vllm_model_name": vllm_name,
            "deployment_url": model.deployment_url
        }
```

#### 4.3: Frontend Deployment Tab
**File**: `frontend/src/components/finetuning/DeploymentTab.tsx`

```typescript
const DeploymentTab: React.FC<{ modelId: string }> = ({ modelId }) => {
  const [deploymentStatus, setDeploymentStatus] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const deployToOllama = async () => {
    setLoading(true)
    const response = await fetch(
      `${API_BASE}/api/v1/models/${modelId}/deploy/ollama`,
      { method: 'POST' }
    )
    const result = await response.json()
    setDeploymentStatus(result)
    setLoading(false)
  }

  const deployToVLLM = async () => {
    setLoading(true)
    const response = await fetch(
      `${API_BASE}/api/v1/models/${modelId}/deploy/vllm`,
      { method: 'POST' }
    )
    const result = await response.json()
    setDeploymentStatus(result)
    setLoading(false)
  }

  return (
    <div>
      <h3>Deploy Model</h3>

      {deploymentStatus?.status === 'deployed' ? (
        <div className="bg-green-100 p-4 rounded">
          <p>✅ Model deployed successfully!</p>
          <p>Deployment URL: {deploymentStatus.deployment_url}</p>
          <p>Model Name: {deploymentStatus.ollama_model_name || deploymentStatus.vllm_model_name}</p>

          <button
            onClick={() => registerInChatUI(modelId)}
            className="mt-4 bg-blue-500 text-white px-4 py-2 rounded"
          >
            Register in Chat UI
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <button
            onClick={deployToOllama}
            disabled={loading}
            className="bg-blue-500 text-white px-4 py-2 rounded"
          >
            Deploy to Ollama
          </button>

          <button
            onClick={deployToVLLM}
            disabled={loading}
            className="bg-purple-500 text-white px-4 py-2 rounded"
          >
            Deploy to vLLM
          </button>
        </div>
      )}
    </div>
  )
}
```

---

## Phase 5: Chat UI Integration (P0 - Critical)

### Overview
Once model is deployed, add it to the Chat UI model dropdown so users can chat with it.

### Implementation Tasks

#### 5.1: Register Deployed Model in Model List
**File**: `backend/app/api/routes/models.py`

**Current behavior**: Returns hardcoded list of OpenAI/Anthropic/Ollama models

**New behavior**: Also include deployed fine-tuned models

```python
@router.get("/models")
async def list_available_models(db: AsyncSession = Depends(get_db)):
    """List all available models for chat"""

    # Existing models
    models = [
        {"id": "gpt-4", "name": "GPT-4", "provider": "openai"},
        {"id": "claude-3", "name": "Claude 3", "provider": "anthropic"},
        {"id": "ollama/mistral", "name": "Mistral (Local)", "provider": "ollama"}
    ]

    # Add deployed fine-tuned models
    result = await db.execute(
        select(FineTunedModel).where(
            FineTunedModel.status == "deployed"
        )
    )
    finetuned_models = result.scalars().all()

    for model in finetuned_models:
        if model.ollama_model_name:
            models.append({
                "id": f"ollama/{model.ollama_model_name}",
                "name": f"{model.name} (Fine-tuned)",
                "provider": "ollama",
                "is_finetuned": True,
                "base_model": model.base_model
            })
        elif model.vllm_model_name:
            models.append({
                "id": f"vllm/{model.vllm_model_name}",
                "name": f"{model.name} (Fine-tuned)",
                "provider": "vllm",
                "is_finetuned": True,
                "base_model": model.base_model,
                "deployment_url": model.deployment_url
            })

    return models
```

#### 5.2: Frontend Model Selector Update
**File**: `frontend/src/components/ModelSelector.tsx`

**Current**: Displays hardcoded models
**New**: Fetches from API including fine-tuned models

```typescript
const ModelSelector: React.FC = () => {
  const [models, setModels] = useState<any[]>([])
  const [selectedModel, setSelectedModel] = useState<string>('')

  useEffect(() => {
    // Fetch available models (including fine-tuned)
    fetch(`${API_BASE}/api/v1/models`)
      .then(res => res.json())
      .then(data => {
        setModels(data)
        if (data.length > 0) {
          setSelectedModel(data[0].id)
        }
      })
  }, [])

  return (
    <select
      value={selectedModel}
      onChange={(e) => setSelectedModel(e.target.value)}
      className="border rounded px-3 py-2"
    >
      {models.map(model => (
        <option key={model.id} value={model.id}>
          {model.name}
          {model.is_finetuned && ' 🎯'}
          {` (${model.provider})`}
        </option>
      ))}
    </select>
  )
}
```

#### 5.3: LLM Service - Route to Fine-Tuned Models
**File**: `backend/app/services/llm_service.py`

```python
async def generate_response(
    self,
    model: str,
    prompt: str,
    db: AsyncSession
) -> str:
    """Generate response from LLM (including fine-tuned models)"""

    # Check if it's a fine-tuned model
    if model.startswith("ollama/") or model.startswith("vllm/"):
        # Check if it's a deployed fine-tuned model
        model_name = model.split("/", 1)[1]

        result = await db.execute(
            select(FineTunedModel).where(
                or_(
                    FineTunedModel.ollama_model_name == model_name,
                    FineTunedModel.vllm_model_name == model_name
                )
            )
        )
        finetuned_model = result.scalar_one_or_none()

        if finetuned_model:
            # Route to deployed endpoint
            if finetuned_model.ollama_model_name:
                return await self._call_ollama(model_name, prompt)
            elif finetuned_model.vllm_model_name:
                return await self._call_vllm(
                    finetuned_model.deployment_url,
                    prompt
                )

    # Standard model routing
    if model.startswith("gpt-"):
        return await self._call_openai(model, prompt)
    elif model.startswith("claude-"):
        return await self._call_anthropic(model, prompt)
    else:
        return await self._call_ollama(model, prompt)
```

---

## Phase 6: Monitoring Tab (P2 - Medium Priority)

### Overview
Track usage metrics and performance of deployed models.

### Database Fields
```sql
-- finetuned_models table
total_inferences INTEGER
avg_latency_ms FLOAT
last_inference_at TIMESTAMP
```

### Implementation Tasks

#### 6.1: Track Model Usage
**File**: `backend/app/services/llm_service.py`

```python
# After generating response from fine-tuned model
if finetuned_model:
    # Update usage metrics
    finetuned_model.total_inferences += 1

    # Update average latency (moving average)
    current_latency_ms = (time.time() - start_time) * 1000
    if finetuned_model.avg_latency_ms is None:
        finetuned_model.avg_latency_ms = current_latency_ms
    else:
        # Exponential moving average
        alpha = 0.1
        finetuned_model.avg_latency_ms = (
            alpha * current_latency_ms +
            (1 - alpha) * finetuned_model.avg_latency_ms
        )

    finetuned_model.last_inference_at = datetime.utcnow()
    await db.commit()
```

#### 6.2: Monitoring API
```python
@router.get("/models/{model_id}/metrics")
async def get_model_metrics(model_id: str, db: AsyncSession = Depends(get_db)):
    """Get usage metrics for a model"""
    result = await db.execute(
        select(FineTunedModel).where(FineTunedModel.id == model_id)
    )
    model = result.scalar_one_or_none()

    return {
        "total_inferences": model.total_inferences,
        "avg_latency_ms": model.avg_latency_ms,
        "last_inference_at": model.last_inference_at,
        "status": model.status
    }
```

#### 6.3: Frontend Monitoring Tab
```typescript
const MonitoringTab: React.FC<{ modelId: string }> = ({ modelId }) => {
  const [metrics, setMetrics] = useState<any>(null)

  useEffect(() => {
    const interval = setInterval(() => {
      fetch(`${API_BASE}/api/v1/models/${modelId}/metrics`)
        .then(res => res.json())
        .then(setMetrics)
    }, 5000) // Refresh every 5 seconds

    return () => clearInterval(interval)
  }, [modelId])

  return (
    <div>
      <h3>Real-time Metrics</h3>
      {metrics && (
        <div className="grid grid-cols-3 gap-4">
          <MetricCard
            label="Total Inferences"
            value={metrics.total_inferences}
          />
          <MetricCard
            label="Avg Latency"
            value={`${metrics.avg_latency_ms?.toFixed(2)}ms`}
          />
          <MetricCard
            label="Last Inference"
            value={new Date(metrics.last_inference_at).toLocaleString()}
          />
        </div>
      )}

      <h3>Usage Over Time</h3>
      <LineChart
        data={usageHistory}
        xKey="timestamp"
        yKey="inferences"
      />
    </div>
  )
}
```

---

## Phase 7: Governance Tab (P2 - Medium Priority)

### Overview
Approval workflow, versioning, deprecation, and audit trail.

### Database Fields
```sql
-- finetuned_models table
status VARCHAR(50)  -- trained, approved, deployed, deprecated
deprecated_at TIMESTAMP
deprecated_by UUID
deprecation_reason TEXT
parent_model_id UUID  -- For versioning
```

### Implementation Tasks

#### 7.1: Approval Workflow
```python
@router.post("/models/{model_id}/approve")
async def approve_model(
    model_id: str,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_approval", "write")),
    db: AsyncSession = Depends(get_db)
):
    """Approve model for production deployment"""
    result = await db.execute(
        select(FineTunedModel).where(FineTunedModel.id == model_id)
    )
    model = result.scalar_one_or_none()

    model.status = "approved"
    await db.commit()

    # Log approval in audit table
    await audit_service.log_action(
        db=db,
        action="approve_model",
        user_id=user.id,
        resource_type="finetuned_model",
        resource_id=model_id,
        description=f"Approved model {model.name} for deployment"
    )

    return {"message": "Model approved", "status": "approved"}


@router.post("/models/{model_id}/deprecate")
async def deprecate_model(
    model_id: str,
    reason: str,
    user: User = Depends(require_authentication),
    db: AsyncSession = Depends(get_db)
):
    """Deprecate a deployed model"""
    result = await db.execute(
        select(FineTunedModel).where(FineTunedModel.id == model_id)
    )
    model = result.scalar_one_or_none()

    model.status = "deprecated"
    model.deprecated_at = datetime.utcnow()
    model.deprecated_by = user.id
    model.deprecation_reason = reason
    await db.commit()

    return {"message": "Model deprecated", "status": "deprecated"}
```

#### 7.2: Frontend Governance Tab
```typescript
const GovernanceTab: React.FC<{ modelId: string }> = ({ modelId }) => {
  const [model, setModel] = useState<any>(null)
  const [auditLog, setAuditLog] = useState<any[]>([])

  const approveModel = async () => {
    await fetch(`${API_BASE}/api/v1/models/${modelId}/approve`, {
      method: 'POST'
    })
    alert('Model approved!')
  }

  const deprecateModel = async (reason: string) => {
    await fetch(`${API_BASE}/api/v1/models/${modelId}/deprecate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason })
    })
    alert('Model deprecated!')
  }

  return (
    <div>
      <h3>Governance</h3>

      <div className="bg-white p-4 rounded border">
        <p>Status: <StatusBadge status={model?.status} /></p>
        <p>Created: {new Date(model?.created_at).toLocaleDateString()}</p>
        {model?.deprecated_at && (
          <p>Deprecated: {new Date(model.deprecated_at).toLocaleDateString()}</p>
        )}
      </div>

      {model?.status === 'trained' && (
        <button
          onClick={approveModel}
          className="mt-4 bg-green-500 text-white px-4 py-2 rounded"
        >
          Approve for Production
        </button>
      )}

      {model?.status === 'deployed' && (
        <button
          onClick={() => {
            const reason = prompt('Deprecation reason:')
            if (reason) deprecateModel(reason)
          }}
          className="mt-4 bg-red-500 text-white px-4 py-2 rounded"
        >
          Deprecate Model
        </button>
      )}

      <h3 className="mt-6">Audit Log</h3>
      <table className="w-full">
        <thead>
          <tr>
            <th>Action</th>
            <th>User</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {auditLog.map(log => (
            <tr key={log.id}>
              <td>{log.action}</td>
              <td>{log.user?.username}</td>
              <td>{new Date(log.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

---

## Implementation Priority

### P0 - Critical (Week 1)
1. ✅ **Phase 1**: Model Artifact Storage (MinIO)
2. ✅ **Phase 2**: Model Registry (finetuned_models table)
3. ✅ **Phase 5**: Chat UI Integration (model dropdown)

### P1 - High Priority (Week 2)
4. **Phase 3**: Evaluation Tab (metrics, comparison)
5. **Phase 4**: Deployment Tab (Ollama/vLLM)

### P2 - Medium Priority (Week 3-4)
6. **Phase 6**: Monitoring Tab (usage metrics)
7. **Phase 7**: Governance Tab (approval workflow)

---

## Testing Plan

### 1. End-to-End Test
```bash
# 1. Train a model
curl -X POST http://localhost:8000/api/v1/finetuning/jobs \
  -d '{"name": "test-model", ...}'

# 2. Submit for training
curl -X POST http://localhost:8000/api/v1/finetuning/jobs/{id}/submit

# 3. Wait for completion
# Check minio_checkpoint_path is NOT NULL

# 4. Verify model registry entry created
curl http://localhost:8000/api/v1/models

# 5. Deploy to Ollama
curl -X POST http://localhost:8000/api/v1/models/{id}/deploy/ollama

# 6. Verify appears in Chat UI dropdown
curl http://localhost:8000/api/v1/models

# 7. Test inference
curl -X POST http://localhost:8000/api/v1/query \
  -d '{"query": "Hello", "model": "ollama/test-model"}'

# 8. Verify usage metrics updated
curl http://localhost:8000/api/v1/models/{id}/metrics
```

---

## Success Criteria

### Phase 1-2 (Model Artifacts & Registry)
- ✅ Checkpoint uploaded to MinIO after training
- ✅ `minio_checkpoint_path` populated in database
- ✅ Model registry entry auto-created
- ✅ Artifacts downloadable from UI

### Phase 3-4 (Evaluation & Deployment)
- ✅ Evaluation metrics stored in `eval_metrics` field
- ✅ Evaluation tab shows metrics and comparison
- ✅ "Deploy to Ollama" button works
- ✅ Deployed model accessible via API

### Phase 5 (Chat UI Integration)
- ✅ Fine-tuned models appear in model dropdown
- ✅ Users can select and chat with fine-tuned models
- ✅ Inference routed correctly to Ollama/vLLM

### Phase 6-7 (Monitoring & Governance)
- ✅ Usage metrics tracked in real-time
- ✅ Monitoring tab shows graphs and statistics
- ✅ Approval workflow functional
- ✅ Audit log records all actions

---

## Next Steps

**Immediate Actions** (You choose):
1. **Start with Phase 1**: Fix checkpoint storage issue (highest impact)
2. **Or skip to Phase 5**: Add current trained models to Chat UI dropdown (user-facing)
3. **Or implement Phase 3**: Build evaluation tab with metrics

**Recommendation**: Start with Phase 1 (checkpoint storage) since all other phases depend on having model artifacts.

---

**Status**: 📋 Ready for implementation
**Estimated Total Time**: 3-4 weeks for complete lifecycle
**Dependencies**: MinIO, Ollama/vLLM, existing database schema

---

**End of Document**
