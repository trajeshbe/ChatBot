# Fine-Tuning Complete Implementation Guide

**Date**: 2025-12-16
**Status**: Dataset Upload Fixed ✅ - Remaining Sections Documented

---

## ✅ What's Been Implemented

### 1. Organizational MinIO Paths ✅

**Updated `MinIOPathBuilder`** with fine-tuning methods:

#### Dataset Path Structure:
```
projects/{project_id}/{username}/finetuning/datasets/{dataset_name}/{dataset_id}/{filename}

Example:
projects/global-project/admin/finetuning/datasets/cloudsync-support-qa/451024e0-8759-433c-aeb7-7e273444ae1b/test.jsonl
```

#### Checkpoint Path Structure:
```
projects/{project_id}/{username}/finetuning/checkpoints/{job_name}/{job_id}/{checkpoint_type}/{filename}

Example:
projects/global-project/admin/finetuning/checkpoints/qwen-2.5-cloudsync/c4ad0963-b194-4f85-b816-3fd0fdaaff9d/adapters/adapter_model.bin
```

### 2. Dataset Upload Endpoint ✅

**Endpoint**: `POST /api/v1/finetuning/datasets/upload`

**Features**:
- ✅ Uses organizational MinIO paths
- ✅ Syncs dataset ID with MinIO path
- ✅ Supports all formats (JSONL, CSV, JSON, Parquet)
- ✅ Audit logging
- ✅ Permission checks

**Test Result**:
```bash
$ curl -X POST "http://localhost:8000/api/v1/finetuning/datasets/upload?format_type=qa&training_objective=qa&name=Test%20Dataset" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.jsonl"

Response: 200 OK
MinIO Path: projects/global-project/admin/finetuning/datasets/test-dataset/{uuid}/test.jsonl
```

### 3. Training Job Creation ✅

**Endpoint**: `POST /api/v1/finetuning/jobs`

**Features**:
- ✅ Links to uploaded datasets
- ✅ Validates dataset exists
- ✅ Stores hyperparameters
- ✅ Auto-start option

### 4. Job Monitoring ✅

**Endpoints**:
- ✅ `GET /api/v1/finetuning/jobs` - List all jobs
- ✅ `GET /api/v1/finetuning/jobs/{id}` - Get job details

**Metrics Included**:
- progress, current_epoch, current_step
- train_loss, eval_loss
- gpu_type, gpu_count
- training_start_time, training_end_time

---

## ⏳ What Needs Implementation

### 1. Dataset List API (UI Integration)

**Current Issue**: Frontend can't list available datasets for job creation

**Required Endpoint**: `GET /api/v1/finetuning/datasets`

**Implementation**:

```python
# backend/app/api/routes/finetuning_routes.py

@router.get("/datasets", response_model=DatasetListResponse)
async def list_datasets(
    project_id: Optional[str] = None,
    format_type: Optional[str] = None,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "read")),
    db: AsyncSession = Depends(get_db)
):
    """
    List all uploaded datasets

    Returns datasets with MinIO links for download
    """
    from sqlalchemy import select, and_
    from app.models.finetuning_models import FineTuningDataset

    query = select(FineTuningDataset)

    # Filter by project if specified
    if project_id:
        query = query.where(FineTuningDataset.project_id == uuid.UUID(project_id))

    # Filter by format type
    if format_type:
        query = query.where(FineTuningDataset.format_type == format_type)

    # Order by upload date
    query = query.order_by(FineTuningDataset.uploaded_at.desc())

    result = await db.execute(query)
    datasets = result.scalars().all()

    return DatasetListResponse(
        datasets=[
            DatasetResponse(
                id=str(d.id),
                name=d.name,
                filename=d.filename,
                format_type=d.format_type,
                file_size=d.file_size,
                num_samples=d.num_samples,
                is_valid=d.is_valid,
                preprocessing_status=d.preprocessing_status,
                uploaded_at=d.uploaded_at,
                uploaded_by=str(d.uploaded_by),
                minio_path=d.minio_path  # For download link
            )
            for d in datasets
        ]
    )
```

**Schema**:
```python
# backend/app/schemas/finetuning_schemas.py

class DatasetResponse(BaseModel):
    id: str
    name: str
    filename: str
    format_type: str
    file_size: int
    num_samples: Optional[int] = None
    is_valid: Optional[bool] = None
    preprocessing_status: str
    uploaded_at: datetime
    uploaded_by: str
    minio_path: str

class DatasetListResponse(BaseModel):
    datasets: List[DatasetResponse]
```

---

### 2. Evaluations Section

**Purpose**: Evaluate fine-tuned models against benchmarks

**Required Components**:

#### Backend - Evaluation Models
```python
# backend/app/models/finetuning_models.py

class ModelEvaluation(Base):
    __tablename__ = "model_evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey('finetuned_models.id'))
    eval_dataset_id = Column(UUID(as_uuid=True), ForeignKey('finetuning_datasets.id'))

    # Metrics
    eval_type = Column(String(50))  # 'perplexity', 'bleu', 'rouge', 'custom'
    metrics = Column(JSON)  # {'bleu': 0.85, 'rouge-1': 0.92}

    # Comparisons
    baseline_model = Column(String(255))
    improvement_percent = Column(Float)

    # Execution
    status = Column(String(50))  # 'pending', 'running', 'completed', 'failed'
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Results
    results_minio_path = Column(String(512))  # Detailed results JSON
    error_message = Column(Text)
```

#### Backend - Evaluation Service
```python
# backend/app/services/finetuning/evaluation_service.py

class EvaluationService:
    """Run evaluations on fine-tuned models"""

    async def run_evaluation(
        self,
        model_id: UUID,
        eval_dataset_id: UUID,
        eval_type: str,
        baseline_model: Optional[str] = None
    ) -> ModelEvaluation:
        """
        Run evaluation on fine-tuned model

        Steps:
        1. Load fine-tuned model
        2. Load evaluation dataset
        3. Run inference on eval set
        4. Calculate metrics (BLEU, ROUGE, perplexity, etc.)
        5. Compare to baseline if provided
        6. Store results to MinIO
        """
        pass

    async def calculate_perplexity(self, model, dataset) -> float:
        """Calculate model perplexity on dataset"""
        pass

    async def calculate_bleu(self, predictions, references) -> float:
        """Calculate BLEU score"""
        pass

    async def calculate_rouge(self, predictions, references) -> dict:
        """Calculate ROUGE scores"""
        pass
```

#### Frontend - Evaluations UI
```typescript
// frontend/src/components/finetuning/EvaluationHub.tsx

interface Evaluation {
  id: string;
  model_id: string;
  model_name: string;
  eval_dataset: string;
  eval_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  metrics: {
    bleu?: number;
    rouge1?: number;
    rouge2?: number;
    rougeL?: number;
    perplexity?: number;
    accuracy?: number;
  };
  improvement_percent?: number;
  started_at: string;
  completed_at?: string;
}

// Features:
// 1. List all evaluations with status
// 2. Create new evaluation (select model, dataset, metrics)
// 3. View detailed results (charts, examples)
// 4. Compare models side-by-side
// 5. Export evaluation reports
```

**API Endpoints**:
- `POST /api/v1/finetuning/evaluations` - Create evaluation
- `GET /api/v1/finetuning/evaluations` - List evaluations
- `GET /api/v1/finetuning/evaluations/{id}` - Get evaluation details
- `GET /api/v1/finetuning/evaluations/{id}/results` - Download detailed results

---

### 3. Adapters & Versions Section

**Purpose**: Manage LoRA adapters and model versions

**Required Components**:

#### Backend - Adapter Version Models
```python
# backend/app/models/finetuning_models.py

class AdapterVersion(Base):
    __tablename__ = "adapter_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey('finetuned_models.id'))

    # Version info
    version = Column(String(50))  # 'v1.0.0', 'v1.1.0'
    version_tag = Column(String(100))  # 'production', 'staging', 'experimental'

    # Adapter details
    adapter_type = Column(String(50))  # 'lora', 'ia3', 'adapter'
    adapter_config = Column(JSON)  # {'r': 16, 'alpha': 32, 'dropout': 0.05}

    # Storage
    minio_path = Column(String(512))  # Path to adapter weights
    file_size = Column(BigInteger)
    checksum = Column(String(64))  # SHA256 hash for integrity

    # Metadata
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
```

#### Frontend - Adapters UI
```typescript
// frontend/src/components/finetuning/AdapterVersions.tsx

interface AdapterVersion {
  id: string;
  model_name: string;
  version: string;
  version_tag: 'production' | 'staging' | 'experimental';
  adapter_type: string;
  file_size: number;
  created_at: string;
  is_active: boolean;
  metrics?: {
    performance_delta: number;
    inference_speed: number;
  };
}

// Features:
// 1. List all adapter versions for a model
// 2. Compare adapter configurations
// 3. Promote adapter to production
// 4. Rollback to previous version
// 5. Download adapter weights
// 6. View adapter metrics (size, performance)
```

---

### 4. Deployment Section

**Purpose**: Deploy trained models to Ollama/vLLM for inference

**Required Components**:

#### Backend - Deployment Models
```python
# backend/app/models/finetuning_models.py

class ModelDeployment(Base):
    __tablename__ = "model_deployments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey('finetuned_models.id'))

    # Deployment config
    deployment_name = Column(String(255))  # 'qwen-cloudsync-prod'
    deployment_type = Column(String(50))  # 'ollama', 'vllm', 'triton'
    endpoint_url = Column(String(512))

    # Resource allocation
    gpu_type = Column(String(100))
    gpu_count = Column(Integer)
    quantization = Column(String(50))  # '4bit', '8bit', 'none'
    max_batch_size = Column(Integer)

    # Status
    status = Column(String(50))  # 'pending', 'deploying', 'active', 'failed', 'stopped'
    health_status = Column(String(50))  # 'healthy', 'degraded', 'unhealthy'

    # Metrics
    requests_per_second = Column(Float)
    avg_latency_ms = Column(Float)
    error_rate = Column(Float)

    # Timestamps
    deployed_at = Column(DateTime(timezone=True))
    last_health_check = Column(DateTime(timezone=True))
```

#### Backend - Deployment Service
```python
# backend/app/services/finetuning/deployment_service.py

class DeploymentService:
    """Deploy fine-tuned models to inference endpoints"""

    async def deploy_to_ollama(
        self,
        model_id: UUID,
        deployment_name: str,
        quantization: str = "4bit"
    ) -> ModelDeployment:
        """
        Deploy model to Ollama

        Steps:
        1. Download adapter from MinIO
        2. Merge adapter with base model
        3. Create Ollama Modelfile
        4. Push to Ollama registry
        5. Create deployment record
        6. Health check
        """
        pass

    async def deploy_to_vllm(
        self,
        model_id: UUID,
        gpu_count: int = 1,
        max_batch_size: int = 32
    ) -> ModelDeployment:
        """Deploy model to vLLM for high-throughput inference"""
        pass

    async def health_check(self, deployment_id: UUID) -> dict:
        """Check deployment health and update metrics"""
        pass

    async def stop_deployment(self, deployment_id: UUID):
        """Stop running deployment"""
        pass
```

#### Frontend - Deployment UI
```typescript
// frontend/src/components/finetuning/DeploymentManager.tsx

interface Deployment {
  id: string;
  model_name: string;
  deployment_name: string;
  deployment_type: 'ollama' | 'vllm' | 'triton';
  endpoint_url: string;
  status: 'pending' | 'deploying' | 'active' | 'failed' | 'stopped';
  health_status: 'healthy' | 'degraded' | 'unhealthy';
  metrics: {
    rps: number;
    avg_latency_ms: number;
    error_rate: number;
  };
  gpu_count: number;
  deployed_at: string;
}

// Features:
// 1. Deploy model to Ollama/vLLM
// 2. View all deployments with status
// 3. Test deployed model (send sample queries)
// 4. Monitor health and metrics
// 5. Scale deployment (add/remove GPUs)
// 6. Stop/restart deployment
// 7. View logs
```

---

### 5. Monitoring Dashboard

**Purpose**: Real-time training and deployment metrics

**Required Components**:

#### Backend - Metrics Collection
```python
# backend/app/services/finetuning/metrics_service.py

class MetricsService:
    """Collect and aggregate training/deployment metrics"""

    async def record_training_metric(
        self,
        job_id: UUID,
        epoch: int,
        step: int,
        metrics: dict
    ):
        """Record training metric point"""
        pass

    async def get_training_metrics(
        self,
        job_id: UUID,
        metric_type: str = 'loss'
    ) -> List[dict]:
        """Get time-series training metrics for plotting"""
        pass

    async def get_deployment_metrics(
        self,
        deployment_id: UUID,
        time_range: str = '1h'
    ) -> dict:
        """Get deployment metrics (RPS, latency, error rate)"""
        pass

    async def get_gpu_utilization(self) -> List[dict]:
        """Get current GPU utilization across all jobs"""
        pass
```

#### Frontend - Monitoring Dashboard
```typescript
// frontend/src/components/finetuning/MonitoringDashboard.tsx

// Features:
// 1. Training Metrics
//    - Loss curves (train/eval) over time
//    - Learning rate schedule
//    - Gradient norms
//    - Throughput (samples/sec, tokens/sec)

// 2. GPU Metrics
//    - GPU utilization %
//    - GPU memory usage
//    - Temperature
//    - Power consumption

// 3. Deployment Metrics
//    - Requests per second
//    - Latency (p50, p95, p99)
//    - Error rate
//    - Throughput

// 4. System Health
//    - Active jobs count
//    - Queued jobs count
//    - GPU pool status
//    - Disk usage

// 5. Alerts
//    - Training failures
//    - OOM errors
//    - Deployment downtime
//    - High error rates
```

**Charts/Visualizations**:
- Line charts for loss curves
- Bar charts for GPU utilization
- Heatmaps for batch-level metrics
- Real-time streaming updates (WebSocket)

---

### 6. Governance & Audit Section

**Purpose**: Track all fine-tuning activities for compliance

**Required Components**:

#### Backend - Audit Trail
```python
# backend/app/models/finetuning_models.py

class FineTuningAuditLog(Base):
    __tablename__ = "finetuning_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Event info
    event_type = Column(String(100))  # 'dataset_upload', 'job_create', 'model_deploy'
    event_timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Actor
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    username = Column(String(255))
    user_role = Column(String(50))

    # Resource
    resource_type = Column(String(50))  # 'dataset', 'job', 'model', 'deployment'
    resource_id = Column(UUID(as_uuid=True))
    resource_name = Column(String(255))

    # Details
    action = Column(String(100))  # 'create', 'update', 'delete', 'deploy', 'stop'
    before_state = Column(JSON)
    after_state = Column(JSON)

    # Context
    ip_address = Column(String(50))
    user_agent = Column(String(512))
    project_id = Column(UUID(as_uuid=True))
    department = Column(String(255))
    team = Column(String(255))

    # Approval workflow
    requires_approval = Column(Boolean, default=False)
    approval_status = Column(String(50))  # 'pending', 'approved', 'rejected'
    approved_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    approved_at = Column(DateTime(timezone=True))
```

#### Frontend - Governance UI
```typescript
// frontend/src/components/finetuning/GovernanceAudit.tsx

interface AuditLog {
  id: string;
  event_type: string;
  event_timestamp: string;
  username: string;
  user_role: string;
  resource_type: string;
  resource_name: string;
  action: string;
  before_state?: any;
  after_state?: any;
  ip_address: string;
  department: string;
  team: string;
}

// Features:
// 1. Audit Log Viewer
//    - Filterable by date, user, resource, action
//    - Exportable to CSV/JSON
//    - Full-text search

// 2. Approval Workflow
//    - Pending approvals queue
//    - Approve/reject with comments
//    - Approval history

// 3. Compliance Reports
//    - Weekly/monthly activity summaries
//    - User activity reports
//    - Resource usage reports
//    - Cost allocation reports

// 4. Access Control
//    - View who has access to what
//    - Permission matrix
//    - Role assignments

// 5. Data Lineage
//    - Track dataset → job → model → deployment
//    - View full lifecycle of a model
//    - Reproducibility tracking
```

---

## Implementation Priority

### Phase 1: Core Functionality (This Week)
1. ✅ ~~Dataset upload with org paths~~ - **DONE**
2. ✅ ~~Job creation~~ - **DONE**
3. ✅ ~~Job monitoring~~ - **DONE**
4. ⏳ Dataset list API (for job creation)
5. ⏳ Basic monitoring dashboard

### Phase 2: Production Features (Next Week)
6. Evaluations section
7. Deployment to Ollama
8. Adapters & versions management

### Phase 3: Enterprise Features (Week 3)
9. Advanced monitoring
10. Governance & audit
11. Approval workflows

---

## Quick Start Commands

### Test Dataset Upload
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin"}' | jq -r '.access_token')

curl -X POST "http://localhost:8000/api/v1/finetuning/datasets/upload?format_type=qa&training_objective=qa&name=My Dataset" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/dataset.jsonl"
```

### Check MinIO Path
```bash
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c \
  "SELECT name, minio_path FROM finetuning_datasets ORDER BY uploaded_at DESC LIMIT 5;"
```

### List Jobs
```bash
curl -s http://localhost:8000/api/v1/finetuning/jobs \
  -H "Authorization: Bearer $TOKEN" | jq '.jobs[] | {name, status, progress}'
```

---

## Current Status Summary

### ✅ Working Now:
- Organizational MinIO paths (matching agent tasks structure)
- Dataset upload to `projects/{project}/user}/finetuning/datasets/...`
- Training job creation with hyperparameters
- Job monitoring with real-time metrics
- Frontend UI loads without errors

### ⏳ Next Steps:
1. Implement dataset list endpoint
2. Connect job creation form to uploaded datasets
3. Test end-to-end: upload → create job → simulate training → view results

### 📋 Future Work:
- All 6 sections need full implementation (Evaluations, Adapters, Deployment, Monitoring, Governance, Audit)
- Each section requires: backend models, services, API endpoints, frontend UI components
- Estimated effort: 2-3 weeks for full enterprise-grade implementation

---

**Status**: Dataset Upload Fixed ✅ - Ready for Testing

Try uploading a dataset now via the UI (Fine-tuning → Datasets → Upload) and it will use the organizational MinIO path structure!
