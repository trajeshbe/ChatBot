# Fine-Tuning Evaluation & Pipeline Logging Implementation Plan

**Date**: 2025-12-23
**Status**: 📋 **PLAN CREATED - READY FOR IMPLEMENTATION**

---

## 🎯 Overview

This document outlines the comprehensive implementation plan for:
1. ✅ **Increasing max epochs to 50** (COMPLETED)
2. 🔄 **Integrating evaluation metrics into training loop** (IN PROGRESS)
3. 🔄 **Adding comprehensive pipeline logging** (PLANNED)
4. 🔄 **Implementing Details button UI** (PLANNED)

---

## ✅ Phase 0: Max Epochs Extension (COMPLETED)

### Changes Made
- **Max epochs**: 10 → **50**
- **Validation warnings**: >15 epochs triggers overfitting warning
- **3 new presets added**:
  - 📊 **Large Dataset Deep** (20 epochs)
  - 🧠 **Reasoning Model** (30 epochs)
  - 🎓 **GRPO Extended** (50 epochs)

### Files Modified
- `backend/config/finetuning_hyperparameter_defaults.yaml`
  - Lines 14-25: Updated `num_epochs` max to 50 with validation
  - Lines 393-460: Added 3 new extended training presets

### Verification
```bash
curl -s http://localhost:8000/api/v1/finetuning/hyperparameters/config | jq '.hyperparameters.num_epochs.max'
# Output: 50 ✅

curl -s http://localhost:8000/api/v1/finetuning/hyperparameters/config | jq '.presets | keys | length'
# Output: 10 ✅
```

---

## 🔄 Phase 1: Evaluation Metrics Integration (IN PROGRESS)

### Current State Analysis

#### ✅ What We Have
- **Evaluation Service** exists: `backend/app/services/finetuning/model_evaluation_service.py`
- **Comprehensive metrics** implemented:
  - BLEU, ROUGE-1/2/L, METEOR, BERTScore
  - Perplexity, Accuracy, F1 Score
- **API endpoint**: `POST /api/v1/finetuning/models-public/{model_id}/evaluate`
- **Database columns** exist:
  - `finetuning_jobs.eval_loss` (double precision)
  - `finetuning_jobs.eval_metrics` (JSON) - **Missing in schema!**
  - `training_metrics.eval_loss` (double precision)
  - `training_metrics.custom_metrics` (JSON)

#### ❌ What's Missing
1. **Training doesn't evaluate**: Trainers don't call evaluation during training
2. **No eval during checkpoints**: eval_steps configured but not used for evaluation
3. **Blank UI fields**: No data populating `eval_loss` or `eval_metrics`
4. **Missing DB column**: `finetuning_jobs.eval_metrics` column doesn't exist

###Implementation Steps

#### Step 1.1: Add Missing Database Column

**File**: Create new migration `backend/migrations/024_add_eval_metrics_column.sql`

```sql
-- Add eval_metrics JSON column to finetuning_jobs
ALTER TABLE finetuning_jobs
ADD COLUMN IF NOT EXISTS eval_metrics JSON;

-- Add index for faster queries
CREATE INDEX IF NOT EXISTS idx_finetuning_jobs_eval_metrics
ON finetuning_jobs USING gin (eval_metrics);

-- Comment
COMMENT ON COLUMN finetuning_jobs.eval_metrics IS
'Comprehensive evaluation metrics: BLEU, ROUGE, METEOR, BERTScore, accuracy, perplexity';
```

#### Step 1.2: Modify Trainers to Call Evaluation

**Files to Modify**:
- `backend/app/services/finetuning/trainers/sft_trainer.py`
- `backend/app/services/finetuning/trainers/peft_trainer.py`
- `backend/app/services/finetuning/trainers/rlhf_grpo_trainer.py`
- `backend/app/services/finetuning/trainers/rlhf_ppo_trainer.py`

**Changes Needed**:

```python
# backend/app/services/finetuning/trainers/sft_trainer.py

from app.services.finetuning.model_evaluation_service import ModelEvaluationService

class SFTTrainer(BaseTrainer):
    def __init__(self, ...):
        super().__init__(...)
        self.eval_service = ModelEvaluationService()

    async def train(self, ...):
        # ... existing training loop ...

        # ✅ ADD: Evaluation at eval_steps intervals
        if self.training_args.eval_steps and global_step % self.training_args.eval_steps == 0:
            logger.info(f"📊 Running evaluation at step {global_step}...")

            # Run evaluation on validation set
            eval_results = await self.eval_service.evaluate_model(
                model_id=self.job_id,
                model=self.model,
                tokenizer=self.tokenizer,
                eval_dataset=self.eval_dataset,
                num_samples=min(100, len(self.eval_dataset))
            )

            # Store eval metrics
            eval_metrics = {
                "bleu": eval_results.get("metrics", {}).get("bleu", {}).get("mean"),
                "rouge_1": eval_results.get("metrics", {}).get("rouge_rouge1", {}).get("mean"),
                "rouge_2": eval_results.get("metrics", {}).get("rouge_rouge2", {}).get("mean"),
                "rouge_l": eval_results.get("metrics", {}).get("rouge_rougeL", {}).get("mean"),
                "meteor": eval_results.get("metrics", {}).get("meteor", {}).get("mean"),
                "bertscore": eval_results.get("metrics", {}).get("bertscore_f1", {}).get("mean"),
                "perplexity": eval_results.get("metrics", {}).get("perplexity"),
                "eval_loss": eval_results.get("eval_loss"),
                "timestamp": datetime.utcnow().isoformat(),
                "step": global_step,
                "epoch": current_epoch
            }

            # Update job with latest eval metrics
            await self.finetuning_service.update_job(
                job_id=self.job_id,
                eval_loss=eval_metrics["eval_loss"],
                eval_metrics=eval_metrics  # ✅ NEW: Store full metrics
            )

            # Also store in training_metrics for historical tracking
            await self.finetuning_service.create_metric(
                job_id=self.job_id,
                epoch=current_epoch,
                step=global_step,
                metrics={
                    "train_loss": train_loss,
                    "eval_loss": eval_metrics["eval_loss"],
                    "custom_metrics": eval_metrics  # Store full eval metrics
                }
            )

            logger.info(f"✅ Evaluation complete: BLEU={eval_metrics['bleu']:.4f}, "
                       f"ROUGE-1={eval_metrics['rouge_1']:.4f}, "
                       f"Perplexity={eval_metrics['perplexity']:.2f}")
```

#### Step 1.3: Update Finetuning Service

**File**: `backend/app/services/finetuning/finetuning_service.py`

Add method to update eval_metrics:

```python
async def update_job(
    self,
    job_id: UUID,
    **kwargs  # Allow any field updates including eval_metrics
) -> FineTuningJob:
    """
    Update fine-tuning job fields

    Args:
        job_id: Job ID
        **kwargs: Fields to update (status, eval_loss, eval_metrics, etc.)
    """
    job = await self.get_job(job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")

    for key, value in kwargs.items():
        if hasattr(job, key):
            setattr(job, key, value)

    self.db.commit()
    self.db.refresh(job)

    return job
```

#### Step 1.4: Frontend UI Updates

**File**: `frontend/src/components/finetuning/EvaluationHub.tsx`

Display evaluation metrics in the UI:

```typescript
// Add evaluation metrics display
{job.eval_metrics && (
  <div className="bg-white rounded-lg shadow p-6">
    <h3 className="text-lg font-semibold mb-4">📊 Evaluation Metrics</h3>

    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <MetricCard
        label="BLEU Score"
        value={job.eval_metrics.bleu?.toFixed(4)}
        icon="🎯"
        tooltip="Translation quality (higher is better)"
      />
      <MetricCard
        label="ROUGE-1"
        value={job.eval_metrics.rouge_1?.toFixed(4)}
        icon="📝"
        tooltip="Unigram overlap (summarization)"
      />
      <MetricCard
        label="ROUGE-L"
        value={job.eval_metrics.rouge_l?.toFixed(4)}
        icon="📄"
        tooltip="Longest common subsequence"
      />
      <MetricCard
        label="BERTScore"
        value={job.eval_metrics.bertscore?.toFixed(4)}
        icon="🧠"
        tooltip="Semantic similarity"
      />
      <MetricCard
        label="Perplexity"
        value={job.eval_metrics.perplexity?.toFixed(2)}
        icon="🔤"
        tooltip="Language modeling quality (lower is better)"
      />
      <MetricCard
        label="Eval Loss"
        value={job.eval_loss?.toFixed(4)}
        icon="📉"
        tooltip="Validation loss (lower is better)"
      />
    </div>

    <p className="text-xs text-gray-500 mt-4">
      Last evaluated: {job.eval_metrics.timestamp}
      (Step {job.eval_metrics.step}, Epoch {job.eval_metrics.epoch})
    </p>
  </div>
)}
```

---

## 🔄 Phase 2: Comprehensive Pipeline Logging (PLANNED)

### Pipeline Stages to Log

1. **Fine-Tuning** (existing)
2. **Model Merge** (LoRA → Full Model)
3. **Model Conversion** (Safetensors → GGUF / Ollama)
4. **Deployment** (Upload to Ollama / vLLM)

### Database Schema Changes

**Create migration**: `backend/migrations/025_add_pipeline_logs_table.sql`

```sql
-- Pipeline execution logs table
CREATE TABLE IF NOT EXISTS pipeline_execution_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES finetuning_jobs(id) ON DELETE CASCADE,
    stage VARCHAR(50) NOT NULL,  -- 'training', 'merge', 'convert', 'deploy'
    status VARCHAR(20) NOT NULL,  -- 'pending', 'running', 'completed', 'failed'
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,

    -- Stage-specific data
    input_path TEXT,
    output_path TEXT,
    command TEXT,
    exit_code INTEGER,

    -- Logs and errors
    stdout_log TEXT,
    stderr_log TEXT,
    error_message TEXT,

    -- Metadata
    metadata JSON,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_pipeline_logs_job_id ON pipeline_execution_logs(job_id);
CREATE INDEX idx_pipeline_logs_stage ON pipeline_execution_logs(stage);
CREATE INDEX idx_pipeline_logs_status ON pipeline_execution_logs(status);
```

### Implementation

**File**: `backend/app/services/finetuning/pipeline_logger.py` (NEW)

```python
class PipelineLogger:
    """
    Comprehensive logging for entire fine-tuning pipeline
    """

    async def log_stage_start(
        self,
        job_id: UUID,
        stage: str,  # 'training', 'merge', 'convert', 'deploy'
        metadata: dict = None
    ) -> UUID:
        """Start logging a pipeline stage"""
        log = PipelineExecutionLog(
            job_id=job_id,
            stage=stage,
            status="running",
            started_at=datetime.utcnow(),
            metadata=metadata
        )
        self.db.add(log)
        self.db.commit()
        return log.id

    async def log_stage_complete(
        self,
        log_id: UUID,
        status: str,  # 'completed' or 'failed'
        output_path: str = None,
        stdout_log: str = None,
        stderr_log: str = None,
        error_message: str = None
    ):
        """Complete logging a pipeline stage"""
        log = self.db.query(PipelineExecutionLog).filter_by(id=log_id).first()
        if not log:
            return

        log.status = status
        log.completed_at = datetime.utcnow()
        log.duration_seconds = (log.completed_at - log.started_at).total_seconds()
        log.output_path = output_path
        log.stdout_log = stdout_log
        log.stderr_log = stderr_log
        log.error_message = error_message

        self.db.commit()
```

**Integrate into existing services**:

```python
# backend/app/services/finetuning/trainers/sft_trainer.py

async def train(self, ...):
    # ✅ START: Log training stage
    log_id = await self.pipeline_logger.log_stage_start(
        job_id=self.job_id,
        stage="training",
        metadata={
            "model_name": self.model_name,
            "dataset_size": len(self.train_dataset),
            "hyperparameters": self.hyperparameters
        }
    )

    try:
        # ... training loop ...

        # ✅ COMPLETE: Log successful training
        await self.pipeline_logger.log_stage_complete(
            log_id=log_id,
            status="completed",
            output_path=final_checkpoint_path,
            stdout_log=training_logs
        )
    except Exception as e:
        # ✅ FAILED: Log training failure
        await self.pipeline_logger.log_stage_complete(
            log_id=log_id,
            status="failed",
            error_message=str(e),
            stderr_log=traceback.format_exc()
        )
        raise
```

---

## 🔄 Phase 3: Details Button UI (PLANNED)

### UI Component Structure

**File**: `frontend/src/components/finetuning/PipelineDetailsModal.tsx` (NEW)

```typescript
interface PipelineDetailsModalProps {
  jobId: string;
  onClose: () => void;
}

export default function PipelineDetailsModal({ jobId, onClose }: PipelineDetailsModalProps) {
  const [pipelineLogs, setPipelineLogs] = useState<PipelineLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPipelineLogs();
  }, [jobId]);

  const fetchPipelineLogs = async () => {
    const response = await fetch(`/api/v1/finetuning/jobs/${jobId}/pipeline-logs`);
    const data = await response.json();
    setPipelineLogs(data.logs);
    setLoading(false);
  };

  return (
    <Modal isOpen onClose={onClose} size="xl">
      <div className="p-6">
        <h2 className="text-2xl font-bold mb-4">🔍 Pipeline Execution Details</h2>

        {/* Pipeline Timeline */}
        <div className="space-y-4">
          {pipelineLogs.map((log, index) => (
            <PipelineStageCard
              key={log.id}
              stage={log.stage}
              status={log.status}
              startTime={log.started_at}
              endTime={log.completed_at}
              duration={log.duration_seconds}
              metadata={log.metadata}
              logs={{
                stdout: log.stdout_log,
                stderr: log.stderr_log,
                error: log.error_message
              }}
              isLast={index === pipelineLogs.length - 1}
            />
          ))}
        </div>
      </div>
    </Modal>
  );
}

function PipelineStageCard({ stage, status, startTime, endTime, duration, metadata, logs, isLast }) {
  const [expanded, setExpanded] = useState(false);

  const stageIcons = {
    training: "🏋️",
    merge: "🔄",
    convert: "⚙️",
    deploy: "🚀"
  };

  const statusColors = {
    pending: "bg-gray-100 text-gray-700",
    running: "bg-blue-100 text-blue-700",
    completed: "bg-green-100 text-green-700",
    failed: "bg-red-100 text-red-700"
  };

  return (
    <div className={`border-l-4 ${status === 'completed' ? 'border-green-500' : status === 'failed' ? 'border-red-500' : 'border-blue-500'} pl-4`}>
      <div
        className="bg-white rounded-lg shadow p-4 cursor-pointer hover:shadow-md transition"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{stageIcons[stage]}</span>
            <div>
              <h3 className="text-lg font-semibold capitalize">{stage}</h3>
              <p className="text-sm text-gray-500">
                Duration: {duration ? `${duration}s` : 'In progress...'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusColors[status]}`}>
              {status}
            </span>
            <ChevronDown className={`w-5 h-5 transition-transform ${expanded ? 'rotate-180' : ''}`} />
          </div>
        </div>

        {/* Expandable Details */}
        {expanded && (
          <div className="mt-4 space-y-3">
            {/* Metadata */}
            {metadata && (
              <div className="bg-gray-50 rounded p-3">
                <h4 className="text-sm font-semibold mb-2">Metadata</h4>
                <pre className="text-xs overflow-x-auto">
                  {JSON.stringify(metadata, null, 2)}
                </pre>
              </div>
            )}

            {/* Logs */}
            {logs.stdout && (
              <div>
                <h4 className="text-sm font-semibold mb-1">Standard Output</h4>
                <pre className="bg-black text-green-400 p-3 rounded text-xs overflow-x-auto max-h-48">
                  {logs.stdout}
                </pre>
              </div>
            )}

            {logs.stderr && (
              <div>
                <h4 className="text-sm font-semibold mb-1">Standard Error</h4>
                <pre className="bg-black text-red-400 p-3 rounded text-xs overflow-x-auto max-h-48">
                  {logs.stderr}
                </pre>
              </div>
            )}

            {logs.error && (
              <div className="bg-red-50 border border-red-200 rounded p-3">
                <h4 className="text-sm font-semibold text-red-900 mb-1">Error Message</h4>
                <p className="text-sm text-red-700">{logs.error}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
```

**Add Details Button to Job List**:

```typescript
// frontend/src/components/finetuning/TrainingJobsManager.tsx

<button
  onClick={() => setSelectedJobForDetails(job.id)}
  className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 flex items-center gap-1"
>
  <Info className="w-4 h-4" />
  Details
</button>

{selectedJobForDetails && (
  <PipelineDetailsModal
    jobId={selectedJobForDetails}
    onClose={() => setSelectedJobForDetails(null)}
  />
)}
```

---

## 📊 Implementation Timeline

| Phase | Task | Estimated Time | Priority |
|-------|------|----------------|----------|
| ✅ 0 | Max epochs to 50 + new presets | ~30 min | **COMPLETED** |
| 🔄 1.1 | Add `eval_metrics` DB column | ~10 min | **HIGH** |
| 🔄 1.2 | Integrate evaluation into trainers | ~2 hours | **HIGH** |
| 🔄 1.3 | Update finetuning service | ~30 min | **HIGH** |
| 🔄 1.4 | Frontend eval metrics display | ~1 hour | **HIGH** |
| 🔄 2.1 | Pipeline logs DB table | ~15 min | **MEDIUM** |
| 🔄 2.2 | Pipeline logger service | ~1 hour | **MEDIUM** |
| 🔄 2.3 | Integrate into all stages | ~2 hours | **MEDIUM** |
| 🔄 3.1 | Pipeline details modal UI | ~2 hours | **MEDIUM** |
| 🔄 3.2 | Details button integration | ~30 min | **MEDIUM** |

**Total Estimated Time**: ~10-12 hours

---

## 🎯 Success Criteria

### Phase 1: Evaluation Metrics
- ✅ `eval_metrics` JSON column exists in `finetuning_jobs`
- ✅ BLEU, ROUGE, METEOR, BERTScore computed during training
- ✅ Metrics displayed in UI (not blank)
- ✅ Evaluation runs at configured `eval_steps` intervals
- ✅ Historical metrics tracked in `training_metrics.custom_metrics`

### Phase 2: Pipeline Logging
- ✅ All 4 stages logged: Training → Merge → Convert → Deploy
- ✅ Comprehensive logs: stdout, stderr, duration, exit codes
- ✅ Metadata captured: input/output paths, hyperparameters, commands
- ✅ Database table `pipeline_execution_logs` created
- ✅ API endpoint for fetching pipeline logs

### Phase 3: Details Button UI
- ✅ "Details" button added to job list
- ✅ Modal shows full pipeline timeline
- ✅ Expandable sections for each stage
- ✅ Logs viewable (stdout, stderr, errors)
- ✅ Duration and status clearly visible

---

## 🚀 Next Steps

1. **Create DB migrations** for `eval_metrics` and `pipeline_execution_logs`
2. **Modify all 4 trainers** to call evaluation service
3. **Update finetuning service** with `update_job()` method
4. **Create pipeline logger service**
5. **Build Details button UI component**
6. **Test end-to-end** with real training job

---

**Plan Created**: 2025-12-23
**Status**: ✅ Ready for implementation
**Next**: User approval to proceed with implementation
