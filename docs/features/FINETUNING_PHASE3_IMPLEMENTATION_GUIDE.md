# Model Fine-Tuning - Phase 3 Implementation Guide

> **Date**: 2025-12-14
> **Status**: Phase 3 Backend Complete, Frontend Implementation Guide
> **Integration**: Grafana, Prometheus, WebSocket, MinIO (Org/Project hierarchy)

---

## ✅ Phase 3 Backend Components COMPLETED

### 1. WebSocket for Real-Time Metrics ✅

**File**: `backend/app/api/routes/finetuning_websocket.py`

**Endpoints**:
- `WS /api/v1/finetuning/ws/jobs/{job_id}/metrics` - Real-time job metrics
- `WS /api/v1/finetuning/ws/gpu/status` - Real-time GPU status

**Features**:
- Live training metrics streaming
- Job status updates
- Progress tracking
- GPU monitoring (memory, utilization, temperature)
- Connection management with ping/pong

**Usage** (Frontend):
```typescript
const ws = new WebSocket(`ws://localhost:8000/api/v1/finetuning/ws/jobs/${jobId}/metrics`);

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  switch (message.type) {
    case 'metric':
      updateMetricsChart(message.data);
      break;
    case 'status':
      updateJobStatus(message.data);
      break;
    case 'progress':
      updateProgressBar(message.data);
      break;
    case 'error':
      showError(message.data.error);
      break;
  }
};
```

### 2. Additional Trainers ✅

#### SFT Trainer
**File**: `backend/app/services/finetuning/trainers/sft_trainer.py`

**Features**:
- Supervised fine-tuning with TRL's SFTTrainer
- Support for instruction, QA, summarization, classification objectives
- Automatic dataset formatting based on objective
- Sample packing for efficiency

**Training Objectives**:
- `instruction`: Alpaca/ShareGPT format
- `qa`: Question-answer pairs
- `summarization`: Document-summary pairs
- `classification`: Text-label pairs

#### RLHF-PPO Trainer
**File**: `backend/app/services/finetuning/trainers/rlhf_ppo_trainer.py`

**Features**:
- Proximal Policy Optimization for RLHF
- Optional reward model or rule-based rewards
- PPO-specific hyperparameters (KL coefficients, clipping, etc.)
- Preference dataset support (chosen/rejected pairs)

#### RLHF-GRPO Trainer
**File**: `backend/app/services/finetuning/trainers/rlhf_grpo_trainer.py`

**Features**:
- Group Relative Policy Optimization (more stable than PPO)
- Group-based advantage estimation
- Lower variance, more sample efficient
- Configurable group size

### 3. Hyperparameter Tuning Service ✅

**File**: `backend/app/services/finetuning/hyperparameter_tuning_service.py`

**Features**:
- **Automated optimization** with Optuna (Bayesian optimization)
- **Method-specific search spaces** for PEFT, SFT, RLHF-PPO, RLHF-GRPO
- **User constraints** - fix parameters or narrow ranges
- **Early stopping** with MedianPruner
- **Heuristic recommendations** based on dataset size and GPU memory

**Key Methods**:
```python
# Get search space for a method
search_space = service.get_search_space("peft", user_constraints={
    "learning_rate": {"min": 1e-5, "max": 1e-4},
    "lora_r": {"fixed_value": 16}  # Fix this parameter
})

# Get recommended hyperparameters (heuristic)
recommended = service.get_recommended_hyperparameters(
    finetuning_method="peft",
    dataset_size=1000,
    available_memory_gb=16.0
)

# Run Optuna optimization
results = await service.optimize_hyperparameters(study_config, objective_fn)
```

### 4. Trainer Factory ✅

**File**: `backend/app/services/finetuning/trainer_factory.py`

**Features**:
- Routes to correct trainer script based on method
- Validates configuration
- Merges user hyperparameters with defaults
- Recommends resources (GPUs, memory, CPU)
- Estimates training time

**Usage**:
```python
from app.services.finetuning.trainer_factory import trainer_factory

# Get trainer script
script = trainer_factory.get_trainer_script("sft")  # Returns "sft_trainer.py"

# Get default hyperparameters
defaults = trainer_factory.get_default_hyperparameters("peft")

# Merge with user values
final_params = trainer_factory.merge_with_defaults("peft", user_params)

# Get resource recommendations
resources = trainer_factory.get_recommended_resources(
    finetuning_method="peft",
    base_model="Qwen/Qwen2.5-7B-Instruct",
    quantization="4bit"
)
# Returns: {gpu_count: 1, min_gpu_memory_gb: 12, ...}
```

---

## 🎨 Frontend Implementation Guide

### Required Components

#### 1. Fine-Tuning Admin Page

**Location**: `frontend/src/pages/admin/fine-tuning.tsx`

**Structure**:
```tsx
import { useState, useEffect } from 'react';
import { Cpu, Database, Zap, Settings } from 'lucide-react';

const FineTuningAdmin = () => {
  const [activeTab, setActiveTab] = useState<'datasets' | 'jobs' | 'models' | 'gpu'>('datasets');

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Model Fine-Tuning</h1>

      {/* Tab Navigation */}
      <div className="flex space-x-4 mb-6">
        <TabButton
          active={activeTab === 'datasets'}
          onClick={() => setActiveTab('datasets')}
          icon={<Database />}
        >
          Datasets
        </TabButton>
        <TabButton
          active={activeTab === 'jobs'}
          onClick={() => setActiveTab('jobs')}
          icon={<Zap />}
        >
          Training Jobs
        </TabButton>
        <TabButton
          active={activeTab === 'models'}
          onClick={() => setActiveTab('models')}
          icon={<Settings />}
        >
          Model Registry
        </TabButton>
        <TabButton
          active={activeTab === 'gpu'}
          onClick={() => setActiveTab('gpu')}
          icon={<Cpu />}
        >
          GPU Status
        </TabButton>
      </div>

      {/* Tab Content */}
      {activeTab === 'datasets' && <DatasetManager />}
      {activeTab === 'jobs' && <JobManager />}
      {activeTab === 'models' && <ModelRegistry />}
      {activeTab === 'gpu' && <GPUMonitor />}
    </div>
  );
};
```

#### 2. Dataset Upload Component

**Location**: `frontend/src/components/finetuning/DatasetUpload.tsx`

**Features**:
- Drag & drop file upload
- Format selection (QA, instruction, summarization, etc.)
- Column mapping interface
- Validation preview
- Integration with MinIO (org/project hierarchy)

**Key UI Elements**:
```tsx
<div className="border-2 border-dashed rounded-lg p-8">
  <input type="file" accept=".csv,.json,.jsonl,.parquet" />

  <select name="format_type">
    <option value="qa">Question-Answer</option>
    <option value="instruction">Instruction Following</option>
    <option value="summarization">Summarization</option>
    <option value="classification">Classification</option>
    <option value="preference">Preference (RLHF)</option>
  </select>

  {/* Column Mapping */}
  <div className="mt-4">
    <label>Question Column:</label>
    <select name="question_col">{/* columns */}</select>

    <label>Answer Column:</label>
    <select name="answer_col">{/* columns */}</select>
  </div>

  <button onClick={uploadDataset}>Upload to MinIO</button>
</div>
```

#### 3. Job Creation Form with Hyperparameter Controls

**Location**: `frontend/src/components/finetuning/JobCreationForm.tsx`

**Features**:
- Method selection (PEFT, SFT, RLHF-PPO, RLHF-GRPO)
- Base model selector (integrates with Ollama Models Manager)
- Dataset picker
- **Hyperparameter controls** with auto-tuning option
- Resource allocation preview
- Training time estimate

**Hyperparameter UI**:
```tsx
<div className="hyperparameters-section">
  <h3>Hyperparameters</h3>

  {/* Mode Selection */}
  <div className="flex space-x-4 mb-4">
    <button
      className={mode === 'manual' ? 'active' : ''}
      onClick={() => setMode('manual')}
    >
      Manual Configuration
    </button>
    <button
      className={mode === 'recommended' ? 'active' : ''}
      onClick={() => setMode('recommended')}
    >
      Recommended (Heuristic)
    </button>
    <button
      className={mode === 'auto-tune' ? 'active' : ''}
      onClick={() => setMode('auto-tune')}
    >
      Auto-Tune (Optuna)
    </button>
  </div>

  {mode === 'manual' && (
    <div className="grid grid-cols-2 gap-4">
      <div>
        <label>Learning Rate</label>
        <input
          type="number"
          step="0.00001"
          value={hyperparams.learning_rate}
          onChange={(e) => setHyperparams({...hyperparams, learning_rate: parseFloat(e.target.value)})}
        />
      </div>

      <div>
        <label>LoRA Rank (r)</label>
        <select
          value={hyperparams.lora_r}
          onChange={(e) => setHyperparams({...hyperparams, lora_r: parseInt(e.target.value)})}
        >
          <option value="8">8</option>
          <option value="16">16</option>
          <option value="32">32</option>
          <option value="64">64</option>
        </select>
      </div>

      {/* More parameters... */}
    </div>
  )}

  {mode === 'recommended' && (
    <div>
      <p>Using recommended hyperparameters based on:</p>
      <ul>
        <li>Dataset size: {datasetSize}</li>
        <li>Available GPU memory: {gpuMemory}GB</li>
        <li>Training method: {method}</li>
      </ul>
      <button onClick={loadRecommended}>Load Recommended</button>
    </div>
  )}

  {mode === 'auto-tune' && (
    <div>
      <h4>Optuna Auto-Tuning Configuration</h4>

      <div>
        <label>Number of Trials</label>
        <input
          type="number"
          min="5"
          max="100"
          value={tuningConfig.n_trials}
          onChange={(e) => setTuningConfig({...tuningConfig, n_trials: parseInt(e.target.value)})}
        />
      </div>

      <div>
        <label>Optimization Metric</label>
        <select
          value={tuningConfig.metric}
          onChange={(e) => setTuningConfig({...tuningConfig, metric: e.target.value})}
        >
          <option value="loss">Loss (minimize)</option>
          <option value="accuracy">Accuracy (maximize)</option>
          <option value="f1">F1 Score (maximize)</option>
        </select>
      </div>

      {/* User Constraints */}
      <div>
        <h5>Constraints (Optional)</h5>
        <div>
          <label>Learning Rate Range</label>
          <input type="number" placeholder="Min" />
          <input type="number" placeholder="Max" />
        </div>

        <div>
          <label>Fix LoRA Rank</label>
          <input type="checkbox" />
          {fixLoraR && <input type="number" />}
        </div>
      </div>

      <button onClick={startAutoTuning}>Start Auto-Tuning</button>
    </div>
  )}
</div>
```

#### 4. Training Monitor with Real-Time Updates

**Location**: `frontend/src/components/finetuning/TrainingMonitor.tsx`

**Features**:
- Real-time metrics via WebSocket
- **Grafana dashboard integration**
- Loss/accuracy charts (using Chart.js or Recharts)
- Progress bar with ETA
- GPU utilization visualization
- Log streaming

**WebSocket Integration**:
```tsx
import { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';

const TrainingMonitor = ({ jobId }: { jobId: string }) => {
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [status, setStatus] = useState<string>('pending');
  const [progress, setProgress] = useState<number>(0);

  useEffect(() => {
    // WebSocket connection
    const ws = new WebSocket(
      `ws://localhost:8000/api/v1/finetuning/ws/jobs/${jobId}/metrics`
    );

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      switch (message.type) {
        case 'metric':
          setMetrics(prev => [...prev, message.data]);
          break;
        case 'status':
          setStatus(message.data.status);
          break;
        case 'progress':
          setProgress(message.data.progress_percent);
          break;
      }
    };

    // Ping/pong keepalive
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 25000);

    return () => {
      clearInterval(pingInterval);
      ws.close();
    };
  }, [jobId]);

  return (
    <div className="training-monitor">
      <div className="status-bar">
        <span className={`status-badge ${status}`}>{status}</span>
        <ProgressBar value={progress} />
      </div>

      {/* Metrics Chart */}
      <div className="metrics-chart">
        <h3>Training Loss</h3>
        <Line
          data={{
            labels: metrics.map(m => m.step),
            datasets: [
              {
                label: 'Loss',
                data: metrics.map(m => m.loss),
                borderColor: 'rgb(75, 192, 192)',
              }
            ]
          }}
        />
      </div>

      {/* Grafana Integration */}
      <div className="grafana-embed">
        <h3>Detailed Metrics (Grafana)</h3>
        <iframe
          src={`http://localhost:3000/d/finetuning-${jobId}?orgId=1&refresh=5s`}
          width="100%"
          height="400"
        />
      </div>

      {/* GPU Monitor */}
      <GPUUtilizationChart />
    </div>
  );
};
```

#### 5. Model Registry Component

**Location**: `frontend/src/components/finetuning/ModelRegistry.tsx`

**Features**:
- List all fine-tuned models
- Model details (version, base model, performance metrics)
- Deployment controls (Ollama, vLLM)
- Model comparison
- Download/export

**UI Structure**:
```tsx
<div className="model-registry">
  <div className="model-filters">
    <select name="status">
      <option value="">All Status</option>
      <option value="registered">Registered</option>
      <option value="deployed">Deployed</option>
      <option value="archived">Archived</option>
    </select>
  </div>

  <div className="model-list">
    {models.map(model => (
      <div key={model.id} className="model-card">
        <h3>{model.model_name} v{model.version}</h3>
        <p>Base: {model.base_model}</p>
        <p>Method: {model.finetuning_method}</p>
        <p>Status: <span className={model.status}>{model.status}</span></p>

        <div className="model-actions">
          {model.status === 'registered' && (
            <button onClick={() => deployModel(model.id, 'ollama')}>
              Deploy to Ollama
            </button>
          )}
          {model.status === 'deployed' && (
            <button onClick={() => undeployModel(model.id)}>
              Undeploy
            </button>
          )}
          <button onClick={() => viewDetails(model.id)}>
            View Details
          </button>
        </div>
      </div>
    ))}
  </div>
</div>
```

#### 6. GPU Monitor Component

**Location**: `frontend/src/components/finetuning/GPUMonitor.tsx`

**Features**:
- Real-time GPU status via WebSocket
- Memory usage visualization
- Temperature monitoring
- Allocation status
- **Prometheus metrics integration**

**Structure**:
```tsx
const GPUMonitor = () => {
  const [gpus, setGpus] = useState<GPU[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/api/v1/finetuning/ws/gpu/status');

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'gpu_status') {
        setGpus(message.data.gpus);
        setStats(message.data.stats);
      }
    };

    return () => ws.close();
  }, []);

  return (
    <div className="gpu-monitor">
      <div className="stats-summary">
        <div className="stat-card">
          <h4>Total GPUs</h4>
          <p className="stat-value">{stats?.total_gpus}</p>
        </div>
        <div className="stat-card">
          <h4>Available</h4>
          <p className="stat-value">{stats?.available_gpus}</p>
        </div>
        <div className="stat-card">
          <h4>Active Jobs</h4>
          <p className="stat-value">{stats?.active_jobs}</p>
        </div>
      </div>

      <div className="gpu-cards">
        {gpus.map(gpu => (
          <div key={gpu.device_id} className="gpu-card">
            <h3>GPU {gpu.device_id}</h3>
            <p>{gpu.name}</p>

            <div className="gpu-metric">
              <label>Memory</label>
              <ProgressBar
                value={(gpu.total_memory_gb - gpu.free_memory_gb) / gpu.total_memory_gb * 100}
                label={`${gpu.free_memory_gb.toFixed(1)}GB / ${gpu.total_memory_gb.toFixed(1)}GB free`}
              />
            </div>

            <div className="gpu-metric">
              <label>Utilization</label>
              <ProgressBar
                value={gpu.utilization_percent}
                label={`${gpu.utilization_percent}%`}
              />
            </div>

            <div className="gpu-metric">
              <label>Temperature</label>
              <span className={getTempClass(gpu.temperature_celsius)}>
                {gpu.temperature_celsius}°C
              </span>
            </div>

            <div className="gpu-status">
              <span className={gpu.is_available ? 'available' : 'in-use'}>
                {gpu.is_available ? 'Available' : 'In Use'}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Prometheus Dashboard Embed */}
      <div className="prometheus-embed">
        <h3>GPU Metrics (Prometheus)</h3>
        <iframe
          src="http://localhost:9090/graph?g0.expr=gpu_memory_usage&g0.tab=0"
          width="100%"
          height="300"
        />
      </div>
    </div>
  );
};
```

---

## 🔗 Integration with Existing Stack

### 1. Grafana Dashboards

Create Grafana dashboards for fine-tuning metrics:

**Dashboard File**: `observability/grafana/dashboards/finetuning-metrics.json`

**Metrics to Track**:
- Training loss over time
- Learning rate schedule
- GPU utilization
- Memory usage
- Training throughput (samples/sec)
- Job completion rate

**Data Sources**:
- **Prometheus**: GPU metrics, resource usage
- **PostgreSQL**: Job status, historical metrics
- **Tempo**: Distributed tracing for training pipeline

### 2. Prometheus Metrics

**Add to**: `backend/app/services/finetuning/metrics_exporter.py`

```python
from prometheus_client import Gauge, Counter, Histogram

# Training metrics
training_loss = Gauge('finetuning_training_loss', 'Current training loss', ['job_id', 'method'])
training_accuracy = Gauge('finetuning_training_accuracy', 'Current training accuracy', ['job_id', 'method'])
learning_rate = Gauge('finetuning_learning_rate', 'Current learning rate', ['job_id'])

# GPU metrics
gpu_memory_usage = Gauge('finetuning_gpu_memory_bytes', 'GPU memory usage', ['gpu_id'])
gpu_utilization = Gauge('finetuning_gpu_utilization_percent', 'GPU utilization', ['gpu_id'])
gpu_temperature = Gauge('finetuning_gpu_temperature_celsius', 'GPU temperature', ['gpu_id'])

# Job metrics
job_duration = Histogram('finetuning_job_duration_seconds', 'Job duration', ['method'])
jobs_total = Counter('finetuning_jobs_total', 'Total jobs', ['method', 'status'])
```

### 3. MinIO Integration (Org/Project Hierarchy)

**Path Structure**:
```
minio://finetuning-datasets/{org_id}/{project_id}/{dataset_id}/
minio://finetuning-checkpoints/{org_id}/{project_id}/{job_id}/checkpoint-{step}/
minio://finetuning-models/{org_id}/{project_id}/{model_id}/
```

**Update Services**:
```python
# backend/app/services/finetuning/finetuning_service.py

async def upload_dataset(
    self,
    filename: str,
    file_content: bytes,
    user_id: UUID,
    project_id: UUID
):
    # Get org from user
    user = await self.db.get(User, user_id)
    org_id = user.organization_id

    # MinIO path with org/project hierarchy
    minio_path = f"finetuning-datasets/{org_id}/{project_id}/{dataset_id}/{filename}"

    # Upload to MinIO
    await minio_client.put_object(
        bucket_name="finetuning-datasets",
        object_name=minio_path,
        data=io.BytesIO(file_content),
        length=len(file_content)
    )

    return minio_path
```

---

## 📦 Dependencies Update

**Add to**: `backend/requirements-finetuning.txt`

```
# Already included in base requirements-finetuning.txt

# Additional for Phase 3
optuna==3.5.0                  # Hyperparameter tuning
websockets==12.0               # WebSocket support (already in FastAPI)
```

---

## 🚀 Quick Start Guide

### 1. Backend Setup

```bash
# Install dependencies
cd backend
pip install -r requirements-finetuning.txt

# Apply database migration (if not done)
docker-compose exec postgres psql -U postgres -d ragchatbot -f /app/migrations/019_add_finetuning_tables.sql

# Build fine-tuning runtime
docker build -t chatbot-finetuning-runtime:latest -f Dockerfile.finetuning-runtime .

# Start with fine-tuning profile
docker-compose --profile finetuning up -d
```

### 2. Frontend Setup

```bash
cd frontend
npm install

# Add dependencies
npm install chart.js react-chartjs-2 recharts

# Run dev server
npm run dev
```

### 3. Access Fine-Tuning

```
http://localhost:3001/admin/fine-tuning
```

---

## 📊 Monitoring & Observability

### Grafana Dashboards

1. **Fine-Tuning Overview**
   - http://localhost:3000/d/finetuning-overview

2. **GPU Utilization**
   - http://localhost:3000/d/gpu-metrics

3. **Training Jobs**
   - http://localhost:3000/d/training-jobs

### Prometheus Metrics

- http://localhost:9090/graph

### MLflow (Optional)

- http://localhost:5000

---

## 🎯 Usage Examples

### 1. Manual Hyperparameters

```typescript
const jobConfig = {
  name: "Customer Support QA",
  base_model: "Qwen/Qwen2.5-7B-Instruct",
  finetuning_method: "peft",
  training_objective: "qa",
  dataset_id: datasetId,
  hyperparameters: {
    learning_rate: 2e-4,
    num_epochs: 3,
    batch_size: 4,
    lora_r: 16,
    lora_alpha: 32
  },
  auto_start: true
};

await createJob(jobConfig);
```

### 2. Recommended Hyperparameters

```typescript
// Get recommended params
const recommended = await fetch(
  `/api/v1/finetuning/hyperparameters/recommended?` +
  `method=peft&dataset_size=1000&gpu_memory=16`
).then(r => r.json());

// Use recommended
const jobConfig = {
  ...baseConfig,
  hyperparameters: recommended
};
```

### 3. Auto-Tuning with Optuna

```typescript
// Create tuning study
const study = await fetch('/api/v1/finetuning/tuning/create', {
  method: 'POST',
  body: JSON.stringify({
    name: "Tune Customer Support Model",
    finetuning_method: "peft",
    base_model: "Qwen/Qwen2.5-7B-Instruct",
    dataset_id: datasetId,
    n_trials: 20,
    user_constraints: {
      lora_r: { fixed_value: 16 },  // Fix this parameter
      learning_rate: { min: 1e-5, max: 5e-4 }  // Narrow range
    },
    optimization_metric: "loss"
  })
}).then(r => r.json());

// Monitor tuning progress
const progress = await fetch(`/api/v1/finetuning/tuning/${study.study_id}/progress`)
  .then(r => r.json());

// Get best hyperparameters
const best = study.best_hyperparameters;

// Create job with best params
await createJob({ ...baseConfig, hyperparameters: best });
```

---

## ✅ Implementation Checklist

### Backend ✅ COMPLETE
- [x] WebSocket endpoints
- [x] SFT Trainer
- [x] RLHF-PPO Trainer
- [x] RLHF-GRPO Trainer
- [x] Hyperparameter tuning service
- [x] Trainer factory

### Frontend 🚧 TO IMPLEMENT
- [ ] Fine-tuning admin page
- [ ] Dataset upload component
- [ ] Job creation form with hyperparameter controls
- [ ] Training monitor with WebSocket
- [ ] Model registry component
- [ ] GPU monitor component

### Integration ✅ DESIGNED
- [x] Grafana dashboard design
- [x] Prometheus metrics design
- [x] MinIO org/project hierarchy
- [ ] Actual Grafana dashboard JSON
- [ ] Actual Prometheus metrics exporter

---

## 📚 Documentation

**See Also**:
- [FINETUNING_PHASE1_COMPLETE.md](./FINETUNING_PHASE1_COMPLETE.md)
- [FINETUNING_CONTAINERIZED_IMPLEMENTATION_COMPLETE.md](./FINETUNING_CONTAINERIZED_IMPLEMENTATION_COMPLETE.md)
- [FINETUNING_INTEGRATION_GUIDE.md](./FINETUNING_INTEGRATION_GUIDE.md)

---

**Status**: Backend complete, Frontend implementation guide provided
**Next Steps**: Implement frontend components following this guide
**Estimated Effort**: 8-12 hours for complete frontend implementation
