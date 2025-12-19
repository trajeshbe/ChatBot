# Fine-Tuned Model Lifecycle Management Guide

**Date**: 2025-12-19
**Status**: Training Complete, Lifecycle Features Needed

## Current State: Training Completed ✅

### Job Details: short_story_5
- **Job ID**: `9b7a56b9-fe0e-4d50-bbcc-3f340579100e`
- **Status**: `completed` (100%)
- **Base Model**: `Qwen/Qwen2.5-1.5B-Instruct`
- **Method**: PEFT (LoRA/QLoRA)
- **Training Time**: ~6 minutes (05:28 - 05:34 UTC)
- **Checkpoint Path**: `/workspace/finetuning/9b7a56b9-fe0e-4d50-bbcc-3f340579100e/output`

### What Was Created
1. ✅ **Training Completed**: Model fine-tuned successfully
2. ✅ **Checkpoints Saved**: LoRA adapter weights saved locally
3. ✅ **Job Record**: Training job metadata stored in database

### What's Missing
1. ❌ **Model Registration**: Model not registered in `finetuned_models` table
2. ❌ **Deployment**: Model not deployed to inference endpoint (Ollama/vLLM)
3. ❌ **Evaluation**: No evaluation metrics calculated
4. ❌ **Monitoring**: No inference tracking or performance monitoring
5. ❌ **Governance**: No audit trail for model usage

---

## ML Model Lifecycle Phases

### Phase 1: Training (✅ COMPLETE)
**What Happened**:
- Fine-tuning job submitted via UI
- GPU allocated (NVIDIA GeForce RTX 5060)
- Model downloaded and loaded
- Training executed (3 epochs)
- Checkpoints saved to workspace

**Database Tables Used**:
- `finetuning_jobs` - Job configuration and status
- `finetuning_datasets` - Training dataset metadata
- `training_metrics` - Per-epoch training metrics (if enabled)

---

### Phase 2: Model Registration (❌ MISSING)

**What Should Happen**:
1. After training completes, automatically register the model
2. Store model metadata in `finetuned_models` table
3. Upload checkpoints to MinIO for persistent storage
4. Generate model versioning (v1, v2, etc.)
5. Link to parent job and dataset

**Database Schema**: `finetuned_models`
```sql
CREATE TABLE finetuned_models (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,                -- e.g., "short_story_qwen_v1"
    version VARCHAR(50),                        -- e.g., "v1.0.0"
    description TEXT,
    job_id UUID REFERENCES finetuning_jobs(id), -- Link to training job
    base_model VARCHAR(255),                    -- Original base model
    finetuning_method VARCHAR(50),              -- peft, sft, rlhf-ppo, etc.
    mlflow_model_uri VARCHAR(512),              -- MLflow model registry URI
    mlflow_run_id VARCHAR(255),                 -- MLflow experiment run ID
    minio_checkpoint_path VARCHAR(512),         -- MinIO path to adapter weights
    adapter_config JSONB,                       -- LoRA config (r, alpha, dropout, etc.)
    eval_metrics JSONB,                         -- Evaluation scores
    status VARCHAR(50) DEFAULT 'registered',    -- registered, deployed, deprecated
    deployment_url VARCHAR(512),                -- Inference endpoint URL
    ollama_model_name VARCHAR(255),             -- If deployed to Ollama
    vllm_model_name VARCHAR(255),               -- If deployed to vLLM
    created_at TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES users(id),
    project_id UUID REFERENCES projects(id)
);
```

**Implementation Needed**:
```python
# In finetuning_tasks.py, after training completes:

def register_finetuned_model(db: Session, job: FineTuningJob, checkpoint_path: str):
    """Register the fine-tuned model in the model registry"""
    from app.models.finetuning_models import FineTunedModel

    model = FineTunedModel(
        name=f"{job.name}_model",
        version="v1.0.0",
        description=f"Fine-tuned {job.base_model} for {job.training_objective}",
        job_id=job.id,
        base_model=job.base_model,
        finetuning_method=job.finetuning_method,
        minio_checkpoint_path=checkpoint_path,
        adapter_config=job.hyperparameters,
        eval_metrics={},  # Populate after evaluation
        status="registered",
        created_by=job.created_by,
        project_id=job.project_id
    )
    db.add(model)
    db.commit()

    logger.info(f"✅ Model registered: {model.name} (version {model.version})")
    return model
```

---

### Phase 3: Evaluation (❌ MISSING)

**What Should Happen**:
1. Run automated evaluation on held-out test set
2. Calculate metrics: perplexity, BLEU, ROUGE, F1, accuracy
3. Compare against base model (improvement %)
4. Store results in `eval_metrics` JSONB field
5. Generate evaluation report

**Evaluation Types**:
- **Perplexity**: Language modeling quality
- **Task-specific**: Depends on `training_objective`
  - QA: F1, Exact Match
  - Classification: Accuracy, Precision, Recall
  - Summarization: ROUGE-1, ROUGE-2, ROUGE-L
  - Instruction Following: Win rate vs base model

**Implementation Needed**:
```python
# app/services/finetuning/evaluation_service.py

class ModelEvaluationService:
    async def evaluate_model(
        self,
        model_id: UUID,
        test_dataset_path: str,
        evaluation_type: str
    ) -> Dict[str, float]:
        """
        Evaluate fine-tuned model on test dataset

        Returns:
            Dict of metric_name -> metric_value
        """
        # Load model from MinIO
        # Run inference on test set
        # Calculate metrics
        # Store in database
        pass
```

**UI Integration**:
- **Admin → Fine-Tuning → Evaluations** tab
- Show evaluation results table
- Compare models side-by-side
- Visualize metrics over model versions

---

### Phase 4: Deployment (❌ MISSING)

**What Should Happen**:
1. Deploy model to inference endpoint (Ollama or vLLM)
2. Register model in inference server
3. Create API endpoint for inference
4. Update `finetuned_models.deployment_url`
5. Enable model selection in chat UI

**Deployment Options**:

#### Option A: Ollama Deployment
```bash
# Convert LoRA adapter to GGUF format
python convert_lora_to_gguf.py \
  --base-model Qwen/Qwen2.5-1.5B-Instruct \
  --adapter-path /path/to/checkpoint \
  --output short_story_qwen.gguf

# Create Ollama modelfile
cat > Modelfile <<EOF
FROM short_story_qwen.gguf
PARAMETER temperature 0.7
PARAMETER top_p 0.9
EOF

# Build and register model
ollama create short_story_qwen:v1 -f Modelfile
```

**Database Update**:
```python
model.ollama_model_name = "short_story_qwen:v1"
model.deployment_url = "http://ollama:11434/api/generate"
model.status = "deployed"
db.commit()
```

#### Option B: vLLM Deployment
```python
# Launch vLLM server with LoRA adapter
docker run --gpus all -v /path/to/checkpoints:/models \
  vllm/vllm-openai:latest \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --enable-lora \
  --lora-modules short_story=/models/short_story_5/adapter_model
```

**Database Update**:
```python
model.vllm_model_name = "Qwen/Qwen2.5-1.5B-Instruct+short_story"
model.deployment_url = "http://vllm-service:8000/v1/completions"
model.status = "deployed"
db.commit()
```

**UI Integration**:
- **Chat Interface → Model Selector**
- Add fine-tuned models to dropdown
- Show model info (version, eval metrics, last updated)
- Allow switching between base models and fine-tuned models

---

### Phase 5: Monitoring (❌ MISSING)

**What Should Happen**:
1. Track inference requests to fine-tuned model
2. Monitor latency, throughput, GPU usage
3. Collect user feedback (thumbs up/down)
4. Detect model drift over time
5. Generate dashboards in Grafana

**Database Table**: Track Usage
```sql
-- Update finetuned_models with usage stats
ALTER TABLE finetuned_models ADD COLUMN total_inferences INTEGER DEFAULT 0;
ALTER TABLE finetuned_models ADD COLUMN avg_latency_ms FLOAT;
ALTER TABLE finetuned_models ADD COLUMN last_inference_at TIMESTAMP WITH TIME ZONE;

-- Track per-inference details
CREATE TABLE model_inferences (
    id UUID PRIMARY KEY,
    model_id UUID REFERENCES finetuned_models(id),
    session_id VARCHAR(255),
    user_id UUID REFERENCES users(id),
    input_text TEXT,
    output_text TEXT,
    latency_ms FLOAT,
    tokens_generated INTEGER,
    feedback_score INTEGER,  -- -1, 0, 1 (thumbs down, neutral, thumbs up)
    feedback_comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Prometheus Metrics**:
```python
# app/metrics/model_metrics.py

from prometheus_client import Counter, Histogram, Gauge

finetuned_model_requests = Counter(
    'finetuned_model_requests_total',
    'Total inference requests to fine-tuned models',
    ['model_id', 'model_name', 'version']
)

finetuned_model_latency = Histogram(
    'finetuned_model_latency_seconds',
    'Latency of fine-tuned model inference',
    ['model_id', 'model_name']
)

finetuned_model_feedback = Gauge(
    'finetuned_model_feedback_score',
    'Average user feedback score',
    ['model_id', 'model_name']
)
```

**Grafana Dashboard**:
- **Fine-Tuned Models Monitoring**
- Requests per second (by model)
- Latency percentiles (p50, p95, p99)
- Feedback scores over time
- Model comparison (base vs fine-tuned)

---

### Phase 6: Governance & Audit (❌ MISSING)

**What Should Happen**:
1. Log all model lifecycle events to `audit_logs`
2. Track who deployed/deprecated models
3. Require approval for production deployment
4. Version control and rollback capability
5. Cost tracking per model

**Audit Events**:
```python
# Log model registration
audit_service.log_action(
    user_id=user_id,
    action_type="model_registered",
    details={
        "model_id": model.id,
        "model_name": model.name,
        "base_model": model.base_model,
        "training_job_id": job.id
    }
)

# Log model deployment
audit_service.log_action(
    user_id=user_id,
    action_type="model_deployed",
    details={
        "model_id": model.id,
        "deployment_url": deployment_url,
        "inference_backend": "ollama"
    }
)

# Log model deprecation
audit_service.log_action(
    user_id=user_id,
    action_type="model_deprecated",
    details={
        "model_id": model.id,
        "reason": "Replaced by v2.0.0",
        "replacement_model_id": new_model.id
    }
)
```

**Model Approval Workflow**:
```python
# app/models/finetuning_models.py

class ModelApproval(Base):
    __tablename__ = "model_approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("finetuned_models.id"))
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status = Column(String(50), default="pending")  # pending, approved, rejected
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_comments = Column(Text, nullable=True)
```

---

## Implementation Roadmap

### Phase 1: Immediate (Today)
1. ✅ Fix import error in finetuning_tasks.py
2. ✅ Enable GPU access for celery-worker
3. ✅ Verify training completes successfully
4. 🔲 Implement automatic model registration after training

### Phase 2: Short-term (This Week)
1. 🔲 Add model evaluation service
2. 🔲 Implement Ollama deployment integration
3. 🔲 Add fine-tuned models to chat UI model selector
4. 🔲 Basic monitoring (track inference count)

### Phase 3: Medium-term (Next Week)
1. 🔲 Build evaluation UI (compare models)
2. 🔲 Add Grafana dashboards for model monitoring
3. 🔲 Implement user feedback collection
4. 🔲 Add model versioning and rollback

### Phase 4: Long-term (Next Month)
1. 🔲 Model approval workflow
2. 🔲 Advanced monitoring (drift detection)
3. 🔲 Cost tracking per model
4. 🔲 A/B testing framework for models

---

## Next Steps for You

### Immediate Actions:

1. **Verify Model Checkpoints**:
   ```bash
   # Check what files were created
   docker-compose exec backend ls -lh /workspace/finetuning/9b7a56b9-fe0e-4d50-bbcc-3f340579100e/output/
   ```

2. **Check Training Logs**:
   ```bash
   # See detailed training output
   docker logs 47c90555b86f
   ```

3. **Test Inference** (Manual):
   ```python
   # Load the fine-tuned model
   from transformers import AutoTokenizer, AutoModelForCausalLM
   from peft import PeftModel

   base_model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")
   tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")

   # Load LoRA adapter
   model = PeftModel.from_pretrained(
       base_model,
       "/workspace/finetuning/9b7a56b9-fe0e-4d50-bbcc-3f340579100e/output"
   )

   # Generate text
   inputs = tokenizer("Write a short story about", return_tensors="pt")
   outputs = model.generate(**inputs, max_length=200)
   print(tokenizer.decode(outputs[0]))
   ```

### Recommended Priority:
1. **First**: Implement automatic model registration (add to finetuning_tasks.py)
2. **Second**: Deploy to Ollama for testing
3. **Third**: Add to chat UI model selector
4. **Fourth**: Build evaluation and monitoring UIs

Would you like me to implement any of these phases? I recommend starting with Phase 1 (model registration) so your trained models are automatically available for use.
