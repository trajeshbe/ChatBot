# ML Model Lifecycle + Pipeline Visualization Implementation Plan

**Date**: 2025-12-19
**Scope**: Complete ML lifecycle management + Real-time training pipeline visualization
**Status**: Implementation in Progress

---

## Executive Summary

This document outlines the implementation of two major features:

1. **Complete ML Model Lifecycle** (Option 2)
   - Model registration, evaluation, deployment, monitoring, governance

2. **Training Pipeline Visualization** (Option 3)
   - Real-time stage tracking with visual progress indicators

**Estimated Implementation Time**: 2-3 days
**Complexity**: High
**Business Value**: High - Makes fine-tuning production-ready

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER INTERFACE (Next.js)                     │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│ Fine-Tuning  │ Pipeline     │ Evaluations  │ Model Deployment   │
│ Jobs Page    │ Visualizer   │ Dashboard    │ & Monitoring       │
└──────────────┴──────────────┴──────────────┴────────────────────┘
                       │                  │
                       ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                   BACKEND APIs (FastAPI)                         │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│ Job Status   │ Stage        │ Model        │ Deployment         │
│ API          │ Updates API  │ Registry API │ & Metrics API      │
└──────────────┴──────────────┴──────────────┴────────────────────┘
                       │                  │
                       ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SERVICE LAYER                                 │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│ Fine-Tuning  │ Model        │ Evaluation   │ Deployment         │
│ Service      │ Registry     │ Service      │ Service            │
└──────────────┴──────────────┴──────────────┴────────────────────┘
                       │                  │
                       ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA LAYER (PostgreSQL)                       │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│ finetuning_  │ finetuned_   │ model_       │ model_             │
│ jobs         │ models       │ evaluations  │ deployments        │
└──────────────┴──────────────┴──────────────┴────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│            INFERENCE & STORAGE (Ollama, vLLM, MinIO)            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Feature 1: Training Pipeline Visualization

### User Experience

**Before Training Starts**:
```
┌────────────────────────────────────────────────┐
│  Short Story Fine-Tuning Job                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                │
│  ⏳ Queued - Waiting for GPU                  │
│                                                │
│  [ View Details ]                             │
└────────────────────────────────────────────────┘
```

**During Training** (Real-time updates):
```
┌────────────────────────────────────────────────┐
│  Short Story Fine-Tuning Job                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                │
│  Pipeline Progress:                            │
│                                                │
│  ✅ Setup            (completed in 2s)        │
│  ✅ Tokenizer Load   (completed in 3s)        │
│  ✅ Model Download   (completed in 4m 12s)    │
│  🔄 Model Load       (in progress - 2.1GB/3.2GB) │
│  ⏳ Dataset Prep     (pending)                │
│  ⏳ Training         (pending)                │
│  ⏳ Checkpoint Save  (pending)                │
│                                                │
│  Current Stage: Loading model into GPU        │
│  GPU: NVIDIA RTX 5060 (4.5GB / 8GB used)      │
│  ETA: ~2 minutes remaining                    │
│                                                │
│  [ View Logs ]  [ Cancel Job ]                │
└────────────────────────────────────────────────┘
```

**Training Stage** (Epoch Progress):
```
┌────────────────────────────────────────────────┐
│  Short Story Fine-Tuning Job                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                │
│  Pipeline Progress:                            │
│  ✅ Setup → ✅ Tokenizer → ✅ Download →      │
│  ✅ Load Model → ✅ Dataset Prep →            │
│                                                │
│  🔥 Training (Epoch 2/3)                      │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                │
│  Step 145/216  (67%)                          │
│  Train Loss: 0.234  ↓                         │
│  Learning Rate: 0.00018                       │
│  Tokens/sec: 1,234                            │
│                                                │
│  ⏱  Elapsed: 3m 24s  │  ETA: 1m 42s          │
│                                                │
│  [ View Metrics Graph ]  [ Cancel ]           │
└────────────────────────────────────────────────┘
```

### Database Schema

Already implemented:
```sql
ALTER TABLE finetuning_jobs
ADD COLUMN training_stage VARCHAR(50) DEFAULT 'queued';
ADD COLUMN stage_details JSONB DEFAULT '{}'::jsonb;
ADD COLUMN stage_started_at TIMESTAMP WITH TIME ZONE;
ADD COLUMN stage_completed_at TIMESTAMP WITH TIME ZONE;
```

**Stage Values**:
- `queued` - Waiting for GPU
- `setup` - Container initializing
- `tokenizer_load` - Loading tokenizer
- `model_download` - Downloading from HuggingFace
- `model_load` - Loading into GPU
- `dataset_prep` - Tokenizing dataset
- `training` - Active training
- `checkpoint_save` - Saving/uploading model
- `completed` - Finished successfully
- `failed` - Error occurred

**Stage Details JSON Examples**:
```json
// During model download
{
  "substage": "downloading_model",
  "progress_pct": 45,
  "downloaded_bytes": 1470000000,
  "total_bytes": 3270000000,
  "download_speed_mbps": 12.5
}

// During training
{
  "current_epoch": 2,
  "total_epochs": 3,
  "current_step": 145,
  "total_steps": 216,
  "train_loss": 0.234,
  "learning_rate": 0.00018,
  "tokens_per_second": 1234
}
```

### Implementation Components

#### 1. Backend: Stage Update Helper (✅ Implemented)

File: `backend/app/tasks/finetuning_tasks.py`

```python
def update_training_stage(
    db: Session,
    job_id: UUID,
    stage: str,
    stage_details: Optional[Dict[str, Any]] = None
):
    """Update current training pipeline stage with metadata"""
    # Implementation complete - see line 192
```

#### 2. Backend: API Endpoint for Stage Status

File: `backend/app/api/routes/finetuning_routes.py` (NEW)

```python
@router.get("/jobs/{job_id}/pipeline-status")
async def get_pipeline_status(
    job_id: UUID,
    db: Session = Depends(get_db)
) -> PipelineStatusResponse:
    """
    Get real-time pipeline status for a training job

    Returns:
        - current_stage: Stage name
        - stage_progress: Percentage within stage
        - stage_details: Stage-specific metadata
        - overall_progress: Total job progress (0-100)
        - eta_seconds: Estimated time remaining
        - pipeline_stages: List of all stages with status
    """
    pass
```

#### 3. Frontend: Pipeline Visualizer Component

File: `frontend/src/components/finetuning/PipelineVisualizer.tsx` (NEW)

```typescript
interface PipelineStage {
  name: string;
  label: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  startedAt?: string;
  completedAt?: string;
  duration?: number;
  details?: Record<string, any>;
}

export const PipelineVisualizer: React.FC<{jobId: string}> = ({jobId}) => {
  const [stages, setStages] = useState<PipelineStage[]>([]);
  const [currentStage, setCurrentStage] = useState<string>('queued');

  // Poll for updates every 2 seconds
  useEffect(() => {
    const interval = setInterval(async () => {
      const status = await fetchPipelineStatus(jobId);
      setStages(status.pipeline_stages);
      setCurrentStage(status.current_stage);
    }, 2000);

    return () => clearInterval(interval);
  }, [jobId]);

  return (
    <div className="pipeline-visualizer">
      {stages.map((stage, idx) => (
        <StageCard
          key={stage.name}
          stage={stage}
          isActive={stage.name === currentStage}
          isLast={idx === stages.length - 1}
        />
      ))}
    </div>
  );
};
```

---

## Feature 2: Complete ML Model Lifecycle

### Phase 1: Model Registration

**Trigger**: Automatically after training completes

#### Database Schema (NEW)

File: `backend/migrations/022_create_model_lifecycle_tables.sql`

```sql
-- Fine-tuned models registry
CREATE TABLE finetuned_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,                  -- Semantic versioning
    description TEXT,

    -- Training linkage
    job_id UUID REFERENCES finetuning_jobs(id),
    base_model VARCHAR(255) NOT NULL,
    finetuning_method VARCHAR(50) NOT NULL,

    -- Model storage
    minio_checkpoint_path VARCHAR(512),
    mlflow_model_uri VARCHAR(512),
    mlflow_run_id VARCHAR(255),
    adapter_config JSONB,                          -- LoRA config

    -- Evaluation
    eval_metrics JSONB DEFAULT '{}'::jsonb,        -- {perplexity, bleu, rouge, etc.}

    -- Lifecycle status
    status VARCHAR(50) DEFAULT 'registered',       -- registered, evaluated, deployed, deprecated
    deployment_url VARCHAR(512),
    ollama_model_name VARCHAR(255),
    vllm_model_name VARCHAR(255),

    -- Usage tracking
    total_inferences INTEGER DEFAULT 0,
    avg_latency_ms FLOAT,
    last_inference_at TIMESTAMP WITH TIME ZONE,

    -- Governance
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    project_id UUID REFERENCES projects(id),
    parent_model_id UUID REFERENCES finetuned_models(id),  -- For v2 → v1 lineage
    deprecated_at TIMESTAMP WITH TIME ZONE,
    deprecated_by UUID REFERENCES users(id),
    deprecation_reason TEXT,

    -- Metadata
    tags JSONB DEFAULT '[]'::jsonb,                -- ["production", "experiment", etc.]

    UNIQUE(name, version)
);

CREATE INDEX idx_finetuned_models_status ON finetuned_models(status);
CREATE INDEX idx_finetuned_models_project ON finetuned_models(project_id);
CREATE INDEX idx_finetuned_models_created_at ON finetuned_models(created_at DESC);


-- Model evaluations (detailed metrics per evaluation run)
CREATE TABLE model_evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES finetuned_models(id) ON DELETE CASCADE,
    evaluation_type VARCHAR(50) NOT NULL,          -- "auto", "manual", "ab_test"

    -- Test dataset
    test_dataset_id UUID REFERENCES finetuning_datasets(id),
    test_dataset_path VARCHAR(512),
    num_test_samples INTEGER,

    -- Metrics
    metrics JSONB NOT NULL,                        -- All calculated metrics

    -- Details
    evaluation_time_seconds INTEGER,
    evaluator_model VARCHAR(255),                  -- If using LLM-as-judge
    notes TEXT,

    -- Metadata
    evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    evaluated_by UUID REFERENCES users(id),

    -- Comparison
    baseline_model_id UUID REFERENCES finetuned_models(id),  -- Compare against
    improvement_pct FLOAT                          -- % improvement over baseline
);


-- Model deployments (track where models are deployed)
CREATE TABLE model_deployments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES finetuned_models(id) ON DELETE CASCADE,

    deployment_type VARCHAR(50) NOT NULL,          -- "ollama", "vllm", "local"
    deployment_url VARCHAR(512),
    deployment_config JSONB,                       -- Backend-specific config

    status VARCHAR(50) DEFAULT 'deploying',        -- deploying, active, failed, stopped
    health_status VARCHAR(50),                     -- healthy, degraded, unhealthy

    deployed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deployed_by UUID REFERENCES users(id),
    stopped_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT
);


-- Model inferences (track usage)
CREATE TABLE model_inferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES finetuned_models(id) ON DELETE SET NULL,

    -- Request details
    session_id VARCHAR(255),
    user_id UUID REFERENCES users(id),
    input_text TEXT,
    output_text TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,

    -- Performance
    latency_ms FLOAT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Feedback
    feedback_score INTEGER CHECK (feedback_score IN (-1, 0, 1)),  -- thumbs down, neutral, thumbs up
    feedback_comment TEXT,
    feedback_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_model_inferences_model ON model_inferences(model_id);
CREATE INDEX idx_model_inferences_timestamp ON model_inferences(timestamp DESC);


-- Model approvals (governance)
CREATE TABLE model_approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES finetuned_models(id) ON DELETE CASCADE,

    approval_stage VARCHAR(50) NOT NULL,           -- "staging", "production"
    status VARCHAR(50) DEFAULT 'pending',          -- pending, approved, rejected

    requested_by UUID REFERENCES users(id),
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    request_notes TEXT,

    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_comments TEXT,
    approval_conditions TEXT                       -- Requirements for approval
);
```

#### Backend: Model Registry Service (NEW)

File: `backend/app/services/model_registry_service.py`

```python
class ModelRegistryService:
    """Manage fine-tuned model lifecycle"""

    async def register_model(
        self,
        job_id: UUID,
        checkpoint_path: str,
        eval_metrics: Optional[Dict] = None
    ) -> FineTunedModel:
        """
        Register a fine-tuned model after training completes

        Steps:
        1. Load job details
        2. Generate model name and version
        3. Upload checkpoints to MinIO (if not already uploaded)
        4. Create model record in database
        5. Log audit event
        """
        pass

    async def evaluate_model(
        self,
        model_id: UUID,
        test_dataset_id: UUID,
        evaluation_type: str = "auto"
    ) -> ModelEvaluation:
        """Run evaluation on test dataset"""
        pass

    async def deploy_model(
        self,
        model_id: UUID,
        deployment_type: str,  # "ollama" or "vllm"
        deployment_config: Dict
    ) -> ModelDeployment:
        """Deploy model to inference endpoint"""
        pass

    async def record_inference(
        self,
        model_id: UUID,
        input_text: str,
        output_text: str,
        latency_ms: float,
        session_id: str,
        user_id: Optional[UUID] = None
    ):
        """Track model usage"""
        pass

    async def deprecate_model(
        self,
        model_id: UUID,
        reason: str,
        replacement_model_id: Optional[UUID] = None
    ):
        """Mark model as deprecated"""
        pass
```

### Phase 2: Model Evaluation

#### Evaluation Service

File: `backend/app/services/evaluation/model_evaluation_service.py` (NEW)

```python
class ModelEvaluationService:
    """Automated model evaluation"""

    async def evaluate(
        self,
        model_path: str,
        base_model: str,
        test_dataset_path: str,
        evaluation_type: str
    ) -> Dict[str, float]:
        """
        Run comprehensive evaluation

        Returns metrics dict:
        {
            "perplexity": 12.34,
            "bleu": 0.45,
            "rouge1": 0.52,
            "rouge2": 0.38,
            "rougeL": 0.48,
            "exact_match": 0.67,
            "f1": 0.72
        }
        """
        metrics = {}

        # Load model
        model = self._load_finetuned_model(model_path, base_model)
        test_data = self._load_test_dataset(test_dataset_path)

        # Calculate perplexity
        metrics["perplexity"] = self._calculate_perplexity(model, test_data)

        # Task-specific metrics
        if evaluation_type == "qa":
            metrics.update(self._evaluate_qa(model, test_data))
        elif evaluation_type == "summarization":
            metrics.update(self._evaluate_summarization(model, test_data))

        return metrics
```

### Phase 3: Model Deployment (Ollama Integration)

#### Ollama Deployment Service

File: `backend/app/services/deployment/ollama_deployment_service.py` (NEW)

```python
class OllamaDeploymentService:
    """Deploy fine-tuned models to Ollama"""

    async def deploy(
        self,
        model_id: UUID,
        model_name: str,
        checkpoint_path: str,
        base_model: str
    ) -> str:
        """
        Deploy PEFT adapter to Ollama

        Steps:
        1. Download checkpoint from MinIO
        2. Merge LoRA adapter with base model (or keep separate)
        3. Convert to GGUF format
        4. Create Ollama Modelfile
        5. Register with `ollama create`
        6. Verify deployment

        Returns:
            Ollama model name (e.g., "short_story_qwen:v1")
        """
        # Download adapter
        adapter_dir = await self._download_from_minio(checkpoint_path)

        # Convert to GGUF (or use adapter directly if Ollama supports)
        gguf_path = await self._convert_to_gguf(
            base_model=base_model,
            adapter_path=adapter_dir
        )

        # Create Modelfile
        modelfile_content = f"""
        FROM {gguf_path}
        PARAMETER temperature 0.7
        PARAMETER top_p 0.9
        PARAMETER stop <|im_end|>
        """

        # Register with Ollama
        await self._ollama_create(model_name, modelfile_content)

        return model_name
```

### Phase 4: Frontend UI Components

#### 1. Evaluations Page

File: `frontend/src/pages/admin/finetuning/evaluations.tsx` (NEW)

```typescript
export default function EvaluationsPage() {
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);

  return (
    <div className="evaluations-page">
      <h1>Model Evaluations</h1>

      {/* Model selector */}
      <ModelSelector models={models} onSelect={setSelectedModel} />

      {selectedModel && (
        <>
          {/* Evaluation metrics dashboard */}
          <MetricsComparison model={selectedModel} />

          {/* Run new evaluation */}
          <EvaluationRunner modelId={selectedModel.id} />
        </>
      )}
    </div>
  );
}
```

#### 2. Deployment Page

File: `frontend/src/pages/admin/finetuning/deployment.tsx` (NEW)

```typescript
export default function DeploymentPage() {
  return (
    <div className="deployment-page">
      <h1>Model Deployment</h1>

      {/* List of registered models */}
      <ModelList />

      {/* Deployment wizard */}
      <DeploymentWizard />

      {/* Active deployments */}
      <ActiveDeployments />
    </div>
  );
}
```

#### 3. Monitoring Dashboard

File: `frontend/src/pages/admin/finetuning/monitoring.tsx` (NEW)

```typescript
export default function MonitoringPage() {
  return (
    <div className="monitoring-page">
      <h1>Model Monitoring</h1>

      {/* Usage statistics */}
      <UsageStatistics />

      {/* Performance metrics */}
      <PerformanceMetrics />

      {/* User feedback */}
      <FeedbackAnalytics />
    </div>
  );
}
```

---

## Implementation Schedule

### Week 1: Core Infrastructure
- ✅ Day 1: Database schema (pipeline + lifecycle)
- 🔲 Day 2: Model registry service
- 🔲 Day 3: Evaluation service
- 🔲 Day 4: Ollama deployment service

### Week 2: UI & Integration
- 🔲 Day 5: Pipeline visualizer component
- 🔲 Day 6: Evaluations UI
- 🔲 Day 7: Deployment UI
- 🔲 Day 8: Monitoring dashboard

### Week 3: Testing & Polish
- 🔲 Day 9: End-to-end testing
- 🔲 Day 10: Performance optimization
- 🔲 Day 11: Documentation
- 🔲 Day 12: User acceptance testing

---

## Testing Plan

### Unit Tests
```python
# test_model_registry_service.py
def test_register_model():
    # Test model registration after training
    pass

def test_evaluate_model():
    # Test automated evaluation
    pass

def test_deploy_to_ollama():
    # Test Ollama deployment
    pass
```

### Integration Tests
```python
# test_complete_lifecycle.py
def test_training_to_deployment():
    # Test full pipeline: train → register → evaluate → deploy
    pass
```

### E2E Tests
```typescript
// test_finetuning_ui.spec.ts
test('complete fine-tuning lifecycle', async ({ page }) => {
  // 1. Submit training job
  // 2. Monitor pipeline visualization
  // 3. Run evaluation
  // 4. Deploy model
  // 5. Test inference
});
```

---

## Success Metrics

1. **Pipeline Visualization**:
   - ✅ Real-time stage updates (< 3 second latency)
   - ✅ Accurate progress percentages
   - ✅ Clear error messages

2. **Model Lifecycle**:
   - ✅ 100% automatic registration after training
   - ✅ Evaluation completes in < 5 minutes
   - ✅ Deployment succeeds on first try

3. **User Experience**:
   - ✅ No manual steps required
   - ✅ Clear visibility into model status
   - ✅ Easy model selection in chat UI

---

## Next Steps

Ready to proceed with implementation? I'll start with:

1. ✅ Database migrations (pipeline stages + model lifecycle tables)
2. 🔄 Model registry service implementation
3. 🔄 Pipeline visualizer UI component
4. 🔄 Automatic registration hook in finetuning task

**Estimated time for MVP**: 2-3 days of focused development

Shall I proceed with the implementation?
