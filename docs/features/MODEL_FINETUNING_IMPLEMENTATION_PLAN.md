# Model Fine-Tuning System - Comprehensive Implementation Plan

> **Date**: 2025-12-14
> **Status**: 📋 Planning Phase
> **Scope**: Enterprise-grade model fine-tuning with PEFT, SFT, RLHF, and RLFG
> **Estimated Effort**: 4-6 weeks (3 developers)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Implementation Phases](#implementation-phases)
5. [Database Schema](#database-schema)
6. [API Design](#api-design)
7. [Frontend Components](#frontend-components)
8. [Fine-Tuning Methods](#fine-tuning-methods)
9. [Training Pipeline](#training-pipeline)
10. [Monitoring & Evaluation](#monitoring--evaluation)
11. [Integration Points](#integration-points)
12. [Infrastructure Requirements](#infrastructure-requirements)
13. [Security & Compliance](#security--compliance)
14. [Testing Strategy](#testing-strategy)
15. [Timeline & Milestones](#timeline--milestones)

---

## Executive Summary

### Vision
Build a comprehensive model fine-tuning system that allows users to:
- Fine-tune open-source models (Qwen, Llama, Mistral, etc.) with custom domain data
- Choose from multiple fine-tuning strategies (PEFT, SFT, RLHF, RLFG)
- Automatically preprocess datasets based on training objectives
- Monitor training progress in real-time
- Evaluate and deploy fine-tuned models directly to the chatbot

### Key Features
1. **Model Selection**: Choose from quantized models (4-bit, 8-bit)
2. **Fine-Tuning Methods**: PEFT, SFT, RLHF (PPO), RLHF (GRPO with DeepSeek-style custom rewards)
3. **Training Objectives**: QA, Classification, Summarization, Instruction Following
4. **Dataset Management**: Upload, validate, preprocess datasets
5. **Training Monitoring**: Real-time metrics, loss curves, GPU utilization
6. **Model Evaluation**: Automated evaluation on test sets
7. **Model Registry**: Version control, deployment, A/B testing

### Success Metrics
- Fine-tune a model in < 4 hours on single GPU
- Achieve >90% accuracy on domain-specific tasks
- Support concurrent training jobs (multi-GPU)
- < 5 minute deployment time for fine-tuned models

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Model Select │  │ Dataset Upload│  │Training Monitor│         │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Fine-Tuning Orchestration Service            │  │
│  │  • Job Queue Management                                   │  │
│  │  • Training Configuration                                 │  │
│  │  • Dataset Preprocessing Pipeline                         │  │
│  │  • Model Registry Management                              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Training Worker (Ray/Celery)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ PEFT Trainer │  │ SFT Trainer  │  │RLHF/RLFG Train│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Training Frameworks Integration                 │  │
│  │  • Hugging Face Transformers                              │  │
│  │  • PEFT (LoRA, QLoRA, Prefix Tuning)                     │  │
│  │  • TRL (Transformer Reinforcement Learning)               │  │
│  │  • DeepSpeed (Distributed Training)                       │  │
│  │  • BitsAndBytes (Quantization)                            │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Storage Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   MinIO      │  │  PostgreSQL  │  │   MLflow     │          │
│  │ (Datasets,   │  │ (Metadata,   │  │ (Experiments,│          │
│  │  Models)     │  │  Jobs)       │  │  Metrics)    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Monitoring & Observability                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Grafana    │  │   Tempo      │  │  Prometheus  │          │
│  │ (Dashboards) │  │  (Traces)    │  │  (Metrics)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### 1. Frontend (Next.js)
- **Model Selection UI**: Browse and select base models
- **Fine-Tuning Configuration**: Choose method, objective, hyperparameters
- **Dataset Management**: Upload, validate, preview datasets
- **Training Monitor**: Real-time progress, metrics, logs
- **Model Evaluation**: Run test inferences, compare models
- **Model Registry**: Version management, deployment controls

#### 2. Backend (FastAPI)
- **Fine-Tuning Service**: Orchestrate training jobs
- **Dataset Service**: Validate, preprocess, split datasets
- **Model Service**: Manage model versions, deployments
- **Job Queue Service**: Manage training job queue (Celery/Ray)
- **Evaluation Service**: Run automated evaluations

#### 3. Training Workers
- **PEFT Trainer**: LoRA, QLoRA, Prefix Tuning
- **SFT Trainer**: Instruction fine-tuning
- **RLHF Trainer**: Reward model + PPO
- **RLFG Trainer**: Custom rewards (GRPO)
- **Distributed Training**: Multi-GPU support (DeepSpeed)

#### 4. Storage
- **MinIO**: Store datasets, model checkpoints, artifacts
- **PostgreSQL**: Store job metadata, configurations, results
- **MLflow**: Track experiments, metrics, model versions

#### 5. Monitoring
- **Grafana**: Training dashboards (loss, accuracy, GPU usage)
- **Prometheus**: Collect metrics
- **Tempo**: Distributed tracing

---

## Technology Stack

### Core Training Frameworks

```python
# requirements-finetuning.txt

# Core ML Frameworks
transformers==4.36.0           # Hugging Face Transformers
peft==0.7.1                    # Parameter-Efficient Fine-Tuning
trl==0.7.4                     # Transformer Reinforcement Learning
bitsandbytes==0.41.3          # Quantization (4-bit, 8-bit)
accelerate==0.25.0             # Distributed training
torch==2.1.0                   # PyTorch

# Dataset Processing
datasets==2.15.0               # Hugging Face Datasets
pandas==2.1.4                  # Data manipulation
pyarrow==14.0.1                # Fast data loading

# Distributed Training
deepspeed==0.12.6              # DeepSpeed optimization
ray[train]==2.9.0              # Distributed orchestration

# Evaluation
evaluate==0.4.1                # Hugging Face Evaluate
rouge-score==0.1.2             # Text generation metrics
sacrebleu==2.3.1               # Translation metrics

# Experiment Tracking
mlflow==2.9.2                  # Experiment tracking
wandb==0.16.1                  # Weights & Biases (optional)

# Monitoring
tensorboard==2.15.1            # TensorBoard logging
prometheus-client==0.19.0      # Metrics export

# Task Queue
celery==5.3.4                  # Distributed task queue
redis==5.0.1                   # Celery backend

# Utilities
sentencepiece==0.1.99          # Tokenizer
protobuf==4.25.1               # Protocol buffers
```

### Infrastructure

- **GPU**: NVIDIA A100/H100 (recommended), V100, RTX 4090
- **VRAM**: 24GB minimum (for 7B models with QLoRA)
- **Storage**: 500GB+ SSD for checkpoints
- **RAM**: 64GB+ system RAM

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
**Goal**: Set up infrastructure and basic UI

#### Tasks
1. **Database Schema**
   - Create `finetuning_jobs` table
   - Create `finetuning_datasets` table
   - Create `finetuned_models` table
   - Create `training_metrics` table

2. **Backend Services**
   - Create `FineTuningService` class
   - Create `DatasetPreprocessor` class
   - Create `ModelRegistryService` class
   - Set up Celery/Ray workers

3. **Frontend UI**
   - Create `ModelFineTuning` admin page
   - Create `ModelSelector` component
   - Create `DatasetUploader` component
   - Create `TrainingConfigForm` component

4. **Storage Setup**
   - Configure MinIO buckets for datasets/models
   - Set up MLflow tracking server
   - Configure Prometheus/Grafana dashboards

#### Deliverables
- ✅ Database migrations
- ✅ Basic backend API endpoints
- ✅ Admin UI with model selection
- ✅ Dataset upload functionality

---

### Phase 2: PEFT Implementation (Week 2-3)
**Goal**: Implement LoRA/QLoRA fine-tuning

#### Tasks
1. **PEFT Trainer**
   ```python
   # backend/app/services/finetuning/peft_trainer.py
   from peft import LoraConfig, get_peft_model
   from transformers import AutoModelForCausalLM, TrainingArguments

   class PEFTTrainer:
       def __init__(self, config: FineTuningConfig):
           self.config = config
           self.model = self.load_model()
           self.tokenizer = self.load_tokenizer()

       def train(self, dataset):
           # LoRA configuration
           lora_config = LoraConfig(
               r=16,  # Rank
               lora_alpha=32,
               target_modules=["q_proj", "v_proj"],
               lora_dropout=0.05,
               bias="none",
               task_type="CAUSAL_LM"
           )

           # Get PEFT model
           model = get_peft_model(self.model, lora_config)

           # Training arguments
           training_args = TrainingArguments(
               output_dir=self.config.output_dir,
               num_train_epochs=3,
               per_device_train_batch_size=4,
               gradient_accumulation_steps=4,
               learning_rate=2e-4,
               fp16=True,
               logging_steps=10,
               save_steps=100,
           )

           # Train
           trainer = Trainer(
               model=model,
               args=training_args,
               train_dataset=dataset,
               callbacks=[MetricsCallback()]
           )

           trainer.train()
   ```

2. **QLoRA Support**
   - 4-bit quantization with BitsAndBytes
   - Nested quantization for memory efficiency
   - Flash Attention 2 integration

3. **Dataset Preprocessing**
   - Automatic tokenization
   - Prompt template application
   - Train/validation split

4. **Real-time Monitoring**
   - WebSocket connection for live metrics
   - GPU utilization tracking
   - Loss curve visualization

#### Deliverables
- ✅ PEFT trainer implementation
- ✅ QLoRA with 4-bit quantization
- ✅ Dataset preprocessing pipeline
- ✅ Real-time training dashboard

---

### Phase 3: SFT Implementation (Week 3-4)
**Goal**: Implement Supervised Fine-Tuning for instructions

#### Tasks
1. **SFT Trainer**
   ```python
   # backend/app/services/finetuning/sft_trainer.py
   from trl import SFTTrainer, DataCollatorForCompletionOnlyLM

   class SupervisedFineTuner:
       def train(self, dataset):
           # Format dataset for instruction tuning
           def formatting_func(example):
               return f"### Instruction:\n{example['instruction']}\n\n### Response:\n{example['response']}"

           # Data collator (only train on completions)
           collator = DataCollatorForCompletionOnlyLM(
               response_template="### Response:",
               tokenizer=self.tokenizer
           )

           # SFT Trainer
           trainer = SFTTrainer(
               model=self.model,
               train_dataset=dataset,
               formatting_func=formatting_func,
               data_collator=collator,
               max_seq_length=2048,
               packing=True,  # Pack multiple samples
           )

           trainer.train()
   ```

2. **Training Objectives**
   - **Question & Answer**: Format as instruction-response pairs
   - **Classification**: Format with class labels
   - **Summarization**: Format as document-summary pairs
   - **General Instruction**: Alpaca/ShareGPT format

3. **Intelligent Preprocessing**
   ```python
   class DatasetPreprocessor:
       def preprocess_qa(self, dataset):
           """Convert QA dataset to instruction format"""
           return dataset.map(lambda x: {
               "instruction": x["question"],
               "response": x["answer"]
           })

       def preprocess_classification(self, dataset):
           """Convert classification to instruction format"""
           return dataset.map(lambda x: {
               "instruction": f"Classify the following: {x['text']}",
               "response": x["label"]
           })
   ```

4. **Evaluation Metrics**
   - Perplexity
   - ROUGE scores (for summarization)
   - Accuracy (for classification)
   - Custom domain metrics

#### Deliverables
- ✅ SFT trainer with multiple objectives
- ✅ Intelligent dataset preprocessing
- ✅ Automatic evaluation pipeline
- ✅ Training objective selector UI

---

### Phase 4: RLHF Implementation (Week 4-5)
**Goal**: Implement Reinforcement Learning from Human Feedback

#### Tasks
1. **Reward Model Training**
   ```python
   from trl import RewardTrainer

   class RewardModelTrainer:
       def train(self, preference_dataset):
           """
           Dataset format:
           {
               "prompt": "...",
               "chosen": "...",    # Preferred response
               "rejected": "..."   # Non-preferred response
           }
           """
           trainer = RewardTrainer(
               model=self.model,
               tokenizer=self.tokenizer,
               train_dataset=preference_dataset,
           )

           trainer.train()
   ```

2. **PPO Training**
   ```python
   from trl import PPOTrainer, PPOConfig

   class PPOFineTuner:
       def train(self, dataset, reward_model):
           ppo_config = PPOConfig(
               batch_size=16,
               learning_rate=1e-5,
               ppo_epochs=4,
               mini_batch_size=4,
           )

           ppo_trainer = PPOTrainer(
               config=ppo_config,
               model=self.model,
               ref_model=self.ref_model,
               tokenizer=self.tokenizer,
               dataset=dataset,
               reward_model=reward_model,
           )

           for epoch in range(10):
               for batch in ppo_trainer.dataloader:
                   # Generate responses
                   response = ppo_trainer.generate(batch["query"])

                   # Get reward
                   reward = reward_model(batch["query"], response)

                   # PPO update
                   stats = ppo_trainer.step(batch["query"], response, reward)
   ```

3. **Human Feedback Collection UI**
   - Side-by-side response comparison
   - Preference voting interface
   - Feedback submission

4. **Reward Model Evaluation**
   - Agreement with human preferences
   - Correlation analysis

#### Deliverables
- ✅ Reward model training
- ✅ PPO-based policy optimization
- ✅ Human feedback collection UI
- ✅ Reward model evaluation

---

### Phase 5: RLHF with GRPO Implementation (Week 5)
**Goal**: Implement DeepSeek-style GRPO with custom weighted rewards

Reference: https://github.com/trajeshbe/LLM/tree/main/Reinforcement_Learning/code

#### Tasks
1. **GRPO Trainer**
   ```python
   from grpo import GRPOTrainer, GRPOConfig

   class GRPOFineTuner:
       def train(self, dataset, reward_fn):
           """
           GRPO: Group Relative Policy Optimization (DeepSeek-style)

           Key differences from PPO:
           - Compares group of N responses instead of pairs
           - Uses relative ranking within group
           - No separate reward model needed
           - More stable and sample-efficient

           DeepSeek approach:
           - Generate N responses per prompt (typically 4-8)
           - Compute reward for each response
           - Rank responses by reward
           - Update policy to increase probability of higher-ranked responses
           """
           config = GRPOConfig(
               learning_rate=1e-5,
               beta=0.1,  # KL divergence penalty coefficient
               group_size=4,  # Number of responses to compare per prompt
               temperature=0.7,  # Sampling temperature for response generation
           )

           trainer = GRPOTrainer(
               config=config,
               model=self.model,
               reward_fn=reward_fn,
           )

           trainer.train(dataset)
   ```

2. **Custom Reward Functions**
   - Domain-specific metrics
   - Multi-objective rewards (accuracy + fluency + safety)
   - Configurable reward weights

3. **Advanced Optimization**
   - Group-wise ranking
   - Advantage estimation
   - Entropy regularization

#### Deliverables
- ✅ GRPO trainer implementation
- ✅ Custom reward function support
- ✅ Multi-objective optimization
- ✅ GRPO vs PPO comparison

---

### Phase 6: Deployment & Integration (Week 6)
**Goal**: Deploy fine-tuned models to production

#### Tasks
1. **Model Registry**
   ```python
   class ModelRegistry:
       def register_model(self, job_id: str, model_name: str):
           """Register fine-tuned model"""
           # Save to MLflow
           mlflow.transformers.log_model(
               model,
               artifact_path=model_name,
               registered_model_name=model_name
           )

           # Update database
           finetuned_model = FineTunedModel(
               name=model_name,
               base_model=job.base_model,
               finetuning_method=job.method,
               status="registered",
               mlflow_run_id=run_id
           )
           db.add(finetuned_model)
   ```

2. **Model Deployment**
   - Load fine-tuned model adapter
   - Merge adapter with base model (optional)
   - Deploy to Ollama/vLLM

3. **A/B Testing**
   - Route % of traffic to fine-tuned model
   - Compare metrics vs base model
   - Gradual rollout

4. **Model Versioning**
   - Semantic versioning (v1.0.0)
   - Rollback capability
   - Model lineage tracking

#### Deliverables
- ✅ Model registry with MLflow
- ✅ Deployment pipeline
- ✅ A/B testing framework
- ✅ Version management UI

---

## Database Schema

### 1. `finetuning_jobs` Table

```sql
CREATE TABLE finetuning_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Job metadata
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Model configuration
    base_model VARCHAR(255) NOT NULL,  -- e.g., "Qwen/Qwen2.5-7B-Instruct"
    quantization VARCHAR(50),  -- "4bit", "8bit", "none"

    -- Fine-tuning configuration
    finetuning_method VARCHAR(50) NOT NULL,  -- "peft", "sft", "rlhf", "rlfg"
    training_objective VARCHAR(100) NOT NULL,  -- "qa", "classification", "summarization"

    -- Dataset
    dataset_id UUID REFERENCES finetuning_datasets(id),
    train_split FLOAT DEFAULT 0.8,

    -- Hyperparameters (JSONB for flexibility)
    hyperparameters JSONB,
    -- Example:
    -- {
    --   "learning_rate": 2e-4,
    --   "num_epochs": 3,
    --   "batch_size": 4,
    --   "lora_r": 16,
    --   "lora_alpha": 32
    -- }

    -- Training status
    status VARCHAR(50) DEFAULT 'pending',  -- pending, running, completed, failed, cancelled
    progress FLOAT DEFAULT 0.0,  -- 0.0 to 1.0

    -- Training metrics (updated during training)
    current_epoch INT,
    current_step INT,
    total_steps INT,
    train_loss FLOAT,
    eval_loss FLOAT,

    -- Results
    final_model_name VARCHAR(255),
    mlflow_run_id VARCHAR(255),
    minio_checkpoint_path VARCHAR(512),

    -- Training logs
    logs TEXT,
    error_message TEXT,

    -- Resource usage
    gpu_type VARCHAR(100),
    training_time_seconds INT,

    -- Project association
    project_id UUID REFERENCES projects(id),
    department VARCHAR(255),
    team VARCHAR(255)
);

CREATE INDEX idx_finetuning_jobs_status ON finetuning_jobs(status);
CREATE INDEX idx_finetuning_jobs_created_by ON finetuning_jobs(created_by);
CREATE INDEX idx_finetuning_jobs_project ON finetuning_jobs(project_id);
```

### 2. `finetuning_datasets` Table

```sql
CREATE TABLE finetuning_datasets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Dataset metadata
    name VARCHAR(255) NOT NULL,
    description TEXT,
    uploaded_by UUID REFERENCES users(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- File info
    filename VARCHAR(255) NOT NULL,
    file_size BIGINT,
    file_type VARCHAR(50),  -- "csv", "json", "jsonl", "parquet"
    minio_path VARCHAR(512),

    -- Dataset statistics
    num_samples INT,
    num_train_samples INT,
    num_val_samples INT,

    -- Schema/format
    format_type VARCHAR(100),  -- "qa", "classification", "instruction", "preference"
    columns JSONB,
    -- Example for QA:
    -- {
    --   "question_column": "question",
    --   "answer_column": "answer"
    -- }

    -- Validation
    is_valid BOOLEAN DEFAULT FALSE,
    validation_errors JSONB,

    -- Preview
    sample_rows JSONB,

    -- Processing status
    preprocessing_status VARCHAR(50) DEFAULT 'pending',
    preprocessed_path VARCHAR(512),

    -- Project association
    project_id UUID REFERENCES projects(id)
);

CREATE INDEX idx_finetuning_datasets_uploaded_by ON finetuning_datasets(uploaded_by);
```

### 3. `finetuned_models` Table

```sql
CREATE TABLE finetuned_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Model metadata
    name VARCHAR(255) UNIQUE NOT NULL,
    version VARCHAR(50) DEFAULT 'v1.0.0',
    description TEXT,

    -- Source job
    job_id UUID REFERENCES finetuning_jobs(id),
    base_model VARCHAR(255) NOT NULL,
    finetuning_method VARCHAR(50),

    -- Model artifacts
    mlflow_model_uri VARCHAR(512),
    minio_checkpoint_path VARCHAR(512),
    adapter_config JSONB,

    -- Evaluation metrics
    eval_metrics JSONB,
    -- Example:
    -- {
    --   "accuracy": 0.92,
    --   "perplexity": 3.45,
    --   "rouge_l": 0.67
    -- }

    -- Deployment
    status VARCHAR(50) DEFAULT 'registered',  -- registered, deployed, archived
    deployment_url VARCHAR(512),
    ollama_model_name VARCHAR(255),

    -- Usage tracking
    total_inferences INT DEFAULT 0,
    avg_latency_ms FLOAT,

    -- Versioning
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    parent_model_id UUID REFERENCES finetuned_models(id),  -- For model lineage

    -- Project association
    project_id UUID REFERENCES projects(id)
);

CREATE INDEX idx_finetuned_models_status ON finetuned_models(status);
CREATE INDEX idx_finetuned_models_job ON finetuned_models(job_id);
```

### 4. `training_metrics` Table (Time-series)

```sql
CREATE TABLE training_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES finetuning_jobs(id) ON DELETE CASCADE,

    -- Timestamp
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Training progress
    epoch INT,
    step INT,

    -- Loss metrics
    train_loss FLOAT,
    eval_loss FLOAT,

    -- Learning metrics
    learning_rate FLOAT,
    gradient_norm FLOAT,

    -- Resource metrics
    gpu_utilization FLOAT,
    gpu_memory_allocated BIGINT,
    gpu_memory_cached BIGINT,

    -- Performance
    samples_per_second FLOAT,
    tokens_per_second FLOAT
);

CREATE INDEX idx_training_metrics_job ON training_metrics(job_id, timestamp);
```

---

## API Design

### 1. Fine-Tuning Job Endpoints

#### Create Fine-Tuning Job
```python
POST /api/v1/finetuning/jobs

Request:
{
  "name": "Customer Support QA - Qwen-7B",
  "base_model": "Qwen/Qwen2.5-7B-Instruct",
  "quantization": "4bit",
  "finetuning_method": "peft",  # peft, sft, rlhf-ppo, rlhf-grpo
  "training_objective": "qa",  # qa, classification, summarization, instruction
  "dataset_id": "uuid",
  "hyperparameters": {
    "learning_rate": 2e-4,
    "num_epochs": 3,
    "batch_size": 4,
    "lora_r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05
  },
  "project_id": "uuid"
}

Response:
{
  "job_id": "uuid",
  "status": "pending",
  "estimated_time_hours": 2.5
}
```

#### List Fine-Tuning Jobs
```python
GET /api/v1/finetuning/jobs?status=running&project_id=uuid&page=1&page_size=20

Response:
{
  "jobs": [
    {
      "id": "uuid",
      "name": "Customer Support QA - Qwen-7B",
      "status": "running",
      "progress": 0.45,
      "current_epoch": 2,
      "train_loss": 1.23,
      "created_at": "2025-12-14T10:00:00Z"
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20
}
```

#### Get Job Details
```python
GET /api/v1/finetuning/jobs/{job_id}

Response:
{
  "id": "uuid",
  "name": "Customer Support QA - Qwen-7B",
  "base_model": "Qwen/Qwen2.5-7B-Instruct",
  "status": "running",
  "progress": 0.45,
  "current_epoch": 2,
  "current_step": 450,
  "total_steps": 1000,
  "train_loss": 1.23,
  "eval_loss": 1.45,
  "hyperparameters": {...},
  "metrics": {
    "loss_curve": [...],
    "learning_rate_curve": [...]
  },
  "estimated_completion": "2025-12-14T12:30:00Z"
}
```

#### Cancel Job
```python
POST /api/v1/finetuning/jobs/{job_id}/cancel

Response:
{
  "status": "cancelled"
}
```

### 2. Dataset Endpoints

#### Upload Dataset
```python
POST /api/v1/finetuning/datasets

Form Data:
- file: File
- name: string
- description: string
- format_type: "qa" | "classification" | "instruction" | "preference"
- columns: JSON (mapping of dataset columns)
- project_id: string

Response:
{
  "dataset_id": "uuid",
  "validation_status": "pending"
}
```

#### Validate Dataset
```python
POST /api/v1/finetuning/datasets/{dataset_id}/validate

Response:
{
  "is_valid": true,
  "num_samples": 10000,
  "validation_errors": [],
  "sample_rows": [...]
}
```

#### List Datasets
```python
GET /api/v1/finetuning/datasets?project_id=uuid

Response:
{
  "datasets": [
    {
      "id": "uuid",
      "name": "Customer Support QA Dataset",
      "num_samples": 10000,
      "format_type": "qa",
      "uploaded_at": "2025-12-14T09:00:00Z"
    }
  ]
}
```

### 3. Model Registry Endpoints

#### Register Model
```python
POST /api/v1/finetuning/models/register

Request:
{
  "job_id": "uuid",
  "name": "customer-support-qwen-v1",
  "version": "v1.0.0",
  "description": "Fine-tuned for customer support QA"
}

Response:
{
  "model_id": "uuid",
  "status": "registered"
}
```

#### Deploy Model
```python
POST /api/v1/finetuning/models/{model_id}/deploy

Request:
{
  "deployment_target": "ollama",  # ollama, vllm
  "deployment_config": {
    "context_length": 4096,
    "num_gpu": 1
  }
}

Response:
{
  "status": "deployed",
  "deployment_url": "http://localhost:11434/api/generate",
  "ollama_model_name": "customer-support-qwen-v1"
}
```

#### List Models
```python
GET /api/v1/finetuning/models?status=deployed

Response:
{
  "models": [
    {
      "id": "uuid",
      "name": "customer-support-qwen-v1",
      "version": "v1.0.0",
      "status": "deployed",
      "eval_metrics": {
        "accuracy": 0.92
      },
      "total_inferences": 15234
    }
  ]
}
```

### 4. Monitoring Endpoints

#### Get Training Metrics (WebSocket)
```python
WS /api/v1/finetuning/jobs/{job_id}/metrics

# Real-time stream of metrics
{
  "timestamp": "2025-12-14T10:30:00Z",
  "epoch": 2,
  "step": 450,
  "train_loss": 1.23,
  "learning_rate": 0.0002,
  "gpu_utilization": 0.95,
  "samples_per_second": 12.3
}
```

#### Get Training Logs
```python
GET /api/v1/finetuning/jobs/{job_id}/logs?tail=100

Response:
{
  "logs": [
    "[2025-12-14 10:30:00] Epoch 2/3, Step 450/1000, Loss: 1.23",
    ...
  ]
}
```

### 5. Evaluation Endpoints

#### Run Evaluation
```python
POST /api/v1/finetuning/models/{model_id}/evaluate

Request:
{
  "test_dataset_id": "uuid",
  "metrics": ["accuracy", "perplexity", "rouge"]
}

Response:
{
  "evaluation_id": "uuid",
  "status": "running"
}
```

#### Get Evaluation Results
```python
GET /api/v1/finetuning/evaluations/{evaluation_id}

Response:
{
  "model_id": "uuid",
  "metrics": {
    "accuracy": 0.92,
    "perplexity": 3.45,
    "rouge_1": 0.65,
    "rouge_l": 0.67
  },
  "sample_predictions": [...]
}
```

---

## Frontend Components

### 1. Model Fine-Tuning Dashboard

**Location**: `/admin/model-finetuning`

```typescript
// frontend/src/pages/admin/model-finetuning.tsx

import React, { useState } from 'react';
import { ModelSelector } from '@/components/finetuning/ModelSelector';
import { DatasetUploader } from '@/components/finetuning/DatasetUploader';
import { TrainingConfigForm } from '@/components/finetuning/TrainingConfigForm';
import { JobsList } from '@/components/finetuning/JobsList';

export default function ModelFineTuningPage() {
  const [activeTab, setActiveTab] = useState<'jobs' | 'new' | 'datasets' | 'models'>('jobs');

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Model Fine-Tuning</h1>

      <div className="tabs mb-6">
        <button onClick={() => setActiveTab('jobs')}>Training Jobs</button>
        <button onClick={() => setActiveTab('new')}>New Fine-Tuning</button>
        <button onClick={() => setActiveTab('datasets')}>Datasets</button>
        <button onClick={() => setActiveTab('models')}>Models</button>
      </div>

      {activeTab === 'jobs' && <JobsList />}
      {activeTab === 'new' && <NewFineTuningWorkflow />}
      {activeTab === 'datasets' && <DatasetsManager />}
      {activeTab === 'models' && <ModelsRegistry />}
    </div>
  );
}
```

### 2. New Fine-Tuning Workflow Component

```typescript
// frontend/src/components/finetuning/NewFineTuningWorkflow.tsx

export const NewFineTuningWorkflow: React.FC = () => {
  const [step, setStep] = useState(1);
  const [config, setConfig] = useState<FineTuningConfig>({});

  return (
    <div className="workflow">
      {/* Step 1: Model Selection */}
      {step === 1 && (
        <ModelSelector
          onSelect={(model) => {
            setConfig({ ...config, baseModel: model });
            setStep(2);
          }}
        />
      )}

      {/* Step 2: Fine-Tuning Method */}
      {step === 2 && (
        <MethodSelector
          methods={['peft', 'sft', 'rlhf', 'rlfg']}
          onSelect={(method) => {
            setConfig({ ...config, method });
            setStep(3);
          }}
        />
      )}

      {/* Step 3: Training Objective */}
      {step === 3 && (
        <ObjectiveSelector
          objectives={['qa', 'classification', 'summarization', 'instruction']}
          onSelect={(objective) => {
            setConfig({ ...config, objective });
            setStep(4);
          }}
        />
      )}

      {/* Step 4: Dataset Upload/Selection */}
      {step === 4 && (
        <DatasetSelector
          onSelect={(datasetId) => {
            setConfig({ ...config, datasetId });
            setStep(5);
          }}
        />
      )}

      {/* Step 5: Hyperparameters */}
      {step === 5 && (
        <HyperparametersForm
          method={config.method}
          onSubmit={(hyperparams) => {
            setConfig({ ...config, hyperparameters: hyperparams });
            setStep(6);
          }}
        />
      )}

      {/* Step 6: Review & Submit */}
      {step === 6 && (
        <ReviewAndSubmit
          config={config}
          onSubmit={async () => {
            await createFineTuningJob(config);
            router.push('/admin/model-finetuning?tab=jobs');
          }}
        />
      )}
    </div>
  );
};
```

### 3. Model Selector Component

```typescript
// frontend/src/components/finetuning/ModelSelector.tsx

export const ModelSelector: React.FC<{ onSelect: (model: string) => void }> = ({ onSelect }) => {
  const [models, setModels] = useState<BaseModel[]>([]);

  useEffect(() => {
    // Fetch available base models
    fetch('/api/v1/finetuning/base-models')
      .then(res => res.json())
      .then(data => setModels(data.models));
  }, []);

  return (
    <div className="grid grid-cols-3 gap-4">
      {models.map(model => (
        <div key={model.id} className="model-card">
          <h3>{model.name}</h3>
          <p>{model.size}</p>
          <p>{model.parameters}</p>

          <div className="quantization-options">
            <button onClick={() => onSelect(`${model.id}:4bit`)}>
              4-bit (Recommended)
            </button>
            <button onClick={() => onSelect(`${model.id}:8bit`)}>
              8-bit
            </button>
            <button onClick={() => onSelect(model.id)}>
              Full Precision
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};
```

### 4. Training Monitor Component

```typescript
// frontend/src/components/finetuning/TrainingMonitor.tsx

import { Line } from 'react-chartjs-2';
import { useWebSocket } from '@/hooks/useWebSocket';

export const TrainingMonitor: React.FC<{ jobId: string }> = ({ jobId }) => {
  const [metrics, setMetrics] = useState<Metric[]>([]);

  // WebSocket connection for real-time metrics
  const { data, isConnected } = useWebSocket(`/api/v1/finetuning/jobs/${jobId}/metrics`);

  useEffect(() => {
    if (data) {
      setMetrics(prev => [...prev, data]);
    }
  }, [data]);

  // Loss curve data
  const lossData = {
    labels: metrics.map(m => m.step),
    datasets: [
      {
        label: 'Train Loss',
        data: metrics.map(m => m.train_loss),
        borderColor: 'rgb(75, 192, 192)',
      },
      {
        label: 'Eval Loss',
        data: metrics.map(m => m.eval_loss),
        borderColor: 'rgb(255, 99, 132)',
      }
    ]
  };

  return (
    <div className="training-monitor">
      {/* Progress Bar */}
      <div className="progress-section">
        <h3>Training Progress</h3>
        <ProgressBar value={data?.progress || 0} />
        <p>Epoch {data?.epoch}/{data?.total_epochs}, Step {data?.step}/{data?.total_steps}</p>
      </div>

      {/* Loss Curve */}
      <div className="chart-section">
        <h3>Loss Curve</h3>
        <Line data={lossData} />
      </div>

      {/* Metrics Grid */}
      <div className="metrics-grid">
        <MetricCard label="Current Loss" value={data?.train_loss.toFixed(4)} />
        <MetricCard label="Learning Rate" value={data?.learning_rate.toExponential(2)} />
        <MetricCard label="GPU Utilization" value={`${(data?.gpu_utilization * 100).toFixed(1)}%`} />
        <MetricCard label="Samples/sec" value={data?.samples_per_second.toFixed(1)} />
      </div>

      {/* Resource Utilization */}
      <div className="resource-section">
        <h3>GPU Memory</h3>
        <ProgressBar
          value={data?.gpu_memory_allocated / data?.gpu_memory_total}
          label={`${formatBytes(data?.gpu_memory_allocated)} / ${formatBytes(data?.gpu_memory_total)}`}
        />
      </div>

      {/* Logs */}
      <div className="logs-section">
        <h3>Training Logs</h3>
        <LogViewer jobId={jobId} />
      </div>
    </div>
  );
};
```

### 5. Dataset Uploader Component

```typescript
// frontend/src/components/finetuning/DatasetUploader.tsx

export const DatasetUploader: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [formatType, setFormatType] = useState<'qa' | 'classification' | 'instruction'>('qa');
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({});
  const [validationResults, setValidationResults] = useState<ValidationResults | null>(null);

  const handleUpload = async () => {
    const formData = new FormData();
    formData.append('file', file!);
    formData.append('format_type', formatType);
    formData.append('columns', JSON.stringify(columnMapping));

    const response = await fetch('/api/v1/finetuning/datasets', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();

    // Validate dataset
    const validationResponse = await fetch(`/api/v1/finetuning/datasets/${data.dataset_id}/validate`, {
      method: 'POST'
    });

    const validation = await validationResponse.json();
    setValidationResults(validation);
  };

  return (
    <div className="dataset-uploader">
      {/* File Upload */}
      <div className="upload-section">
        <input type="file" accept=".csv,.json,.jsonl,.parquet" onChange={(e) => setFile(e.target.files?.[0] || null)} />
      </div>

      {/* Format Type Selection */}
      <div className="format-section">
        <label>Dataset Format:</label>
        <select value={formatType} onChange={(e) => setFormatType(e.target.value as any)}>
          <option value="qa">Question & Answer</option>
          <option value="classification">Classification</option>
          <option value="summarization">Summarization</option>
          <option value="instruction">General Instruction</option>
          <option value="preference">Preference (for RLHF)</option>
        </select>
      </div>

      {/* Column Mapping */}
      <div className="mapping-section">
        <h3>Column Mapping</h3>
        {formatType === 'qa' && (
          <>
            <input
              placeholder="Question column name"
              onChange={(e) => setColumnMapping({...columnMapping, question: e.target.value})}
            />
            <input
              placeholder="Answer column name"
              onChange={(e) => setColumnMapping({...columnMapping, answer: e.target.value})}
            />
          </>
        )}
        {formatType === 'classification' && (
          <>
            <input
              placeholder="Text column name"
              onChange={(e) => setColumnMapping({...columnMapping, text: e.target.value})}
            />
            <input
              placeholder="Label column name"
              onChange={(e) => setColumnMapping({...columnMapping, label: e.target.value})}
            />
          </>
        )}
      </div>

      {/* Upload Button */}
      <button onClick={handleUpload} disabled={!file}>
        Upload & Validate Dataset
      </button>

      {/* Validation Results */}
      {validationResults && (
        <div className="validation-results">
          <h3>Validation Results</h3>
          {validationResults.is_valid ? (
            <div className="success">
              ✅ Dataset is valid
              <p>Total samples: {validationResults.num_samples}</p>
            </div>
          ) : (
            <div className="error">
              ❌ Validation failed
              <ul>
                {validationResults.validation_errors.map((error, i) => (
                  <li key={i}>{error}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Sample Preview */}
          <div className="sample-preview">
            <h4>Sample Rows:</h4>
            <pre>{JSON.stringify(validationResults.sample_rows, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  );
};
```

---

## Fine-Tuning Methods

### 1. PEFT (LoRA/QLoRA)

**Use Case**: Memory-efficient fine-tuning of large models

**Implementation**:
```python
# backend/app/services/finetuning/peft_trainer.py

from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import BitsAndBytesConfig

class PEFTTrainer:
    def load_model_4bit(self, model_name: str):
        """Load model with 4-bit quantization"""
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,  # Nested quantization
            bnb_4bit_quant_type="nf4",  # NormalFloat4
            bnb_4bit_compute_dtype=torch.bfloat16
        )

        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
        )

        # Prepare for k-bit training
        model = prepare_model_for_kbit_training(model)

        return model

    def apply_lora(self, model, config: LoRAConfig):
        """Apply LoRA adapters"""
        lora_config = LoraConfig(
            r=config.lora_r,  # Rank (default: 16)
            lora_alpha=config.lora_alpha,  # Scaling factor (default: 32)
            target_modules=[
                "q_proj", "k_proj", "v_proj", "o_proj",  # Attention
                "gate_proj", "up_proj", "down_proj"  # MLP
            ],
            lora_dropout=config.lora_dropout,
            bias="none",
            task_type="CAUSAL_LM"
        )

        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()

        return model
```

**Configuration Options**:
- `lora_r`: Rank (4, 8, 16, 32) - Higher = more capacity but more memory
- `lora_alpha`: Scaling factor (typically 2x lora_r)
- `target_modules`: Which layers to adapt
- `lora_dropout`: Dropout rate for regularization

### 2. SFT (Supervised Fine-Tuning)

**Use Case**: Instruction following, task-specific adaptation

**Implementation**:
```python
# backend/app/services/finetuning/sft_trainer.py

from trl import SFTTrainer, DataCollatorForCompletionOnlyLM

class SupervisedFineTuner:
    def format_instruction_dataset(self, dataset, objective: str):
        """Format dataset based on training objective"""

        if objective == "qa":
            template = """### Question:
{question}

### Answer:
{answer}"""

            def format_func(example):
                return template.format(
                    question=example["question"],
                    answer=example["answer"]
                )

        elif objective == "classification":
            template = """### Task:
Classify the following text into one of these categories: {categories}

### Text:
{text}

### Classification:
{label}"""

            def format_func(example):
                return template.format(
                    categories=", ".join(example.get("categories", [])),
                    text=example["text"],
                    label=example["label"]
                )

        elif objective == "summarization":
            template = """### Document:
{document}

### Summary:
{summary}"""

            def format_func(example):
                return template.format(
                    document=example["document"],
                    summary=example["summary"]
                )

        return dataset.map(lambda x: {"text": format_func(x)})

    def train_sft(self, model, tokenizer, dataset, config):
        """Train with SFTTrainer"""

        # Data collator (only compute loss on response portion)
        response_template = "### Answer:" if config.objective == "qa" else "### Classification:"
        collator = DataCollatorForCompletionOnlyLM(
            response_template=response_template,
            tokenizer=tokenizer
        )

        trainer = SFTTrainer(
            model=model,
            train_dataset=dataset["train"],
            eval_dataset=dataset["validation"],
            tokenizer=tokenizer,
            data_collator=collator,
            max_seq_length=2048,
            packing=True,  # Pack multiple samples into one sequence
            args=TrainingArguments(
                output_dir=config.output_dir,
                num_train_epochs=config.num_epochs,
                per_device_train_batch_size=config.batch_size,
                gradient_accumulation_steps=4,
                learning_rate=config.learning_rate,
                fp16=True,
                logging_steps=10,
                evaluation_strategy="steps",
                eval_steps=100,
                save_steps=100,
                warmup_steps=100,
            )
        )

        trainer.train()
```

### 3. RLHF (Reinforcement Learning from Human Feedback)

**Use Case**: Align model with human preferences

**Two-stage process**:
1. Train reward model on preference data
2. Optimize policy using PPO

**Implementation**:
```python
# backend/app/services/finetuning/rlhf_trainer.py

from trl import RewardTrainer, PPOTrainer, PPOConfig, AutoModelForCausalLMWithValueHead

class RLHFTrainer:
    def stage1_train_reward_model(self, preference_dataset):
        """
        Stage 1: Train reward model

        Dataset format:
        {
            "prompt": "User query",
            "chosen": "Preferred response",
            "rejected": "Non-preferred response"
        }
        """
        # Load model for reward prediction
        reward_model = AutoModelForSequenceClassification.from_pretrained(
            self.base_model,
            num_labels=1  # Scalar reward
        )

        trainer = RewardTrainer(
            model=reward_model,
            tokenizer=self.tokenizer,
            train_dataset=preference_dataset["train"],
            eval_dataset=preference_dataset["validation"],
        )

        trainer.train()
        return reward_model

    def stage2_ppo_training(self, policy_model, reward_model, prompts_dataset):
        """
        Stage 2: PPO training
        """
        # Prepare policy model with value head
        policy_model = AutoModelForCausalLMWithValueHead.from_pretrained(policy_model)
        ref_model = AutoModelForCausalLMWithValueHead.from_pretrained(self.base_model)

        # PPO configuration
        ppo_config = PPOConfig(
            batch_size=16,
            mini_batch_size=4,
            learning_rate=1.41e-5,
            ppo_epochs=4,
            init_kl_coef=0.2,  # KL divergence penalty
            target_kl=6.0,
            adap_kl_ctrl=True,
        )

        ppo_trainer = PPOTrainer(
            config=ppo_config,
            model=policy_model,
            ref_model=ref_model,
            tokenizer=self.tokenizer,
            dataset=prompts_dataset,
        )

        # Training loop
        for epoch in range(ppo_config.ppo_epochs):
            for batch in ppo_trainer.dataloader:
                # Generate responses
                query_tensors = batch["input_ids"]
                response_tensors = ppo_trainer.generate(
                    query_tensors,
                    max_new_tokens=128,
                    do_sample=True,
                    top_p=0.9,
                    temperature=0.7
                )

                # Compute rewards
                texts = [self.tokenizer.decode(r.squeeze()) for r in response_tensors]
                rewards = []
                for query, response in zip(batch["query"], texts):
                    reward_input = f"{query}\n{response}"
                    reward_tensor = reward_model(
                        **self.tokenizer(reward_input, return_tensors="pt")
                    ).logits
                    rewards.append(reward_tensor)

                # PPO update
                stats = ppo_trainer.step(query_tensors, response_tensors, rewards)

                # Log metrics
                ppo_trainer.log_stats(stats, batch, rewards)

        return policy_model
```

### 4. RLHF with GRPO (DeepSeek-Style)

**Use Case**: More sample-efficient than PPO, custom weighted reward functions

**Key Advantages**:
- Group-wise ranking (compare N responses instead of pairs)
- No separate reward model needed
- Multi-objective optimization with custom weights
- Used by DeepSeek, Qwen, and other state-of-the-art models

Reference: https://github.com/trajeshbe/LLM/tree/main/Reinforcement_Learning/code

**Implementation**:
```python
# backend/app/services/finetuning/grpo_trainer.py

from grpo import GRPOTrainer, GRPOConfig

class GRPOTrainer:
    def define_custom_reward(self, config):
        """
        Define DeepSeek-style multi-objective reward function

        Similar to DeepSeek-V2/V3 approach:
        - Helpfulness: How well does it answer the question?
        - Harmlessness: Is it safe and appropriate?
        - Honesty: Is it factual and doesn't hallucinate?
        - Format: Does it follow the desired format?
        """

        def reward_function(prompt: str, response: str) -> float:
            """
            DeepSeek-style multi-objective reward with custom weights

            Weights can be adjusted per domain:
            - Customer Support: High helpfulness, high safety
            - Technical QA: High accuracy, medium verbosity
            - Creative Writing: High fluency, low safety constraints
            """
            rewards = {}

            # 1. Helpfulness (domain-specific)
            if config.objective == "qa":
                # Check if response contains expected answer patterns
                helpfulness = self.check_qa_accuracy(prompt, response)
                rewards["helpfulness"] = helpfulness
            elif config.objective == "classification":
                # Check if response contains valid class label
                helpfulness = self.check_classification_format(response, config.classes)
                rewards["helpfulness"] = helpfulness

            # 2. Harmlessness (safety)
            # Use toxicity detector + PII detector
            toxicity = self.check_toxicity(response)
            pii_score = self.check_pii(response)  # Detect personal info
            rewards["harmlessness"] = 1.0 - max(toxicity, pii_score)

            # 3. Honesty (factuality)
            # Check for hedging phrases, uncertainty markers
            # Penalize hallucination indicators
            factuality = self.check_factuality(prompt, response)
            rewards["honesty"] = factuality

            # 4. Format Compliance
            # Check if response follows expected structure
            format_score = self.check_format(response, config.expected_format)
            rewards["format"] = format_score

            # 5. Fluency (language quality)
            perplexity = self.compute_perplexity(response)
            rewards["fluency"] = 1.0 / (1.0 + perplexity)

            # 6. Length Appropriateness
            # Prefer concise but complete responses
            ideal_length = config.ideal_response_length or 100
            actual_length = len(response.split())
            length_score = 1.0 - abs(actual_length - ideal_length) / ideal_length
            rewards["length"] = max(0.0, length_score)

            # DeepSeek-style weighted combination
            # Weights are configurable per use case
            total_reward = (
                config.reward_weights.get("helpfulness", 0.4) * rewards["helpfulness"] +
                config.reward_weights.get("harmlessness", 0.2) * rewards["harmlessness"] +
                config.reward_weights.get("honesty", 0.2) * rewards["honesty"] +
                config.reward_weights.get("format", 0.1) * rewards["format"] +
                config.reward_weights.get("fluency", 0.05) * rewards["fluency"] +
                config.reward_weights.get("length", 0.05) * rewards["length"]
            )

            # Log individual reward components for debugging
            self.log_reward_breakdown(rewards)

            return total_reward

        return reward_function

    def train_grpo(self, model, dataset, reward_fn):
        """Train with GRPO"""

        grpo_config = GRPOConfig(
            learning_rate=1e-5,
            beta=0.1,  # KL penalty coefficient
            group_size=4,  # Compare 4 responses per prompt
            num_iterations=100,
            batch_size=16,
        )

        trainer = GRPOTrainer(
            config=grpo_config,
            model=model,
            tokenizer=self.tokenizer,
            reward_fn=reward_fn,
        )

        trainer.train(dataset)

        return model
```

**GRPO Advantages** (DeepSeek Approach):
- **Group-wise Ranking**: Compare N responses per prompt instead of pairwise comparisons
- **No Reward Model**: Direct optimization without separate reward model training
- **Sample Efficient**: 2-4x fewer samples than PPO to reach same performance
- **Stable Training**: Lower variance in gradients
- **Multi-objective**: Easily combine multiple reward signals with custom weights
- **Production-Ready**: Used by DeepSeek, Qwen2.5, and other SOTA models

---

## Training Pipeline

### Pipeline Orchestration

```python
# backend/app/services/finetuning/orchestrator.py

from celery import Celery
from typing import Dict, Any

app = Celery('finetuning', broker='redis://redis:6379/0')

@app.task(bind=True)
def run_finetuning_job(self, job_id: str, config: Dict[str, Any]):
    """
    Main fine-tuning orchestration task

    Workflow:
    1. Load and preprocess dataset
    2. Initialize model and tokenizer
    3. Configure trainer based on method
    4. Run training with monitoring
    5. Evaluate model
    6. Save and register model
    """

    try:
        # 1. Initialize job
        job = FineTuningJob.get(job_id)
        job.status = "running"
        job.save()

        # 2. Load dataset
        dataset = load_and_preprocess_dataset(
            dataset_id=config["dataset_id"],
            objective=config["training_objective"]
        )

        # 3. Initialize model
        model, tokenizer = load_base_model(
            model_name=config["base_model"],
            quantization=config["quantization"]
        )

        # 4. Select trainer based on method
        if config["finetuning_method"] == "peft":
            trainer = PEFTTrainer(config)
        elif config["finetuning_method"] == "sft":
            trainer = SupervisedFineTuner(config)
        elif config["finetuning_method"] == "rlhf":
            trainer = RLHFTrainer(config)
        elif config["finetuning_method"] == "rlfg":
            trainer = RLFGTrainer(config)

        # 5. Run training with callbacks
        trainer.add_callback(MetricsCallback(job_id))
        trainer.add_callback(CheckpointCallback(job_id))

        result = trainer.train(model, tokenizer, dataset)

        # 6. Evaluate model
        eval_results = evaluate_model(
            model=result.model,
            test_dataset=dataset["test"],
            objective=config["training_objective"]
        )

        # 7. Save model
        model_path = save_model_to_minio(
            model=result.model,
            job_id=job_id
        )

        # 8. Register model in MLflow
        mlflow_run_id = register_model_mlflow(
            model=result.model,
            metrics=eval_results,
            config=config
        )

        # 9. Update job status
        job.status = "completed"
        job.final_model_name = f"{config['base_model']}-{job_id}"
        job.mlflow_run_id = mlflow_run_id
        job.minio_checkpoint_path = model_path
        job.save()

        return {
            "status": "completed",
            "metrics": eval_results,
            "model_path": model_path
        }

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        job.save()
        raise
```

### Metrics Callback (Real-time Monitoring)

```python
# backend/app/services/finetuning/callbacks.py

from transformers import TrainerCallback
import asyncio

class MetricsCallback(TrainerCallback):
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.ws_manager = WebSocketManager()

    def on_log(self, args, state, control, logs=None, **kwargs):
        """Called when trainer logs metrics"""

        if logs:
            # Save to database
            metric = TrainingMetric(
                job_id=self.job_id,
                epoch=state.epoch,
                step=state.global_step,
                train_loss=logs.get("loss"),
                eval_loss=logs.get("eval_loss"),
                learning_rate=logs.get("learning_rate"),
                gpu_utilization=get_gpu_utilization(),
            )
            metric.save()

            # Broadcast via WebSocket
            asyncio.create_task(
                self.ws_manager.broadcast(self.job_id, {
                    "timestamp": datetime.now().isoformat(),
                    "epoch": state.epoch,
                    "step": state.global_step,
                    **logs
                })
            )

    def on_epoch_end(self, args, state, control, **kwargs):
        """Called at end of each epoch"""

        # Update job progress
        job = FineTuningJob.get(self.job_id)
        job.current_epoch = state.epoch
        job.progress = state.epoch / state.num_train_epochs
        job.save()
```

---

## Monitoring & Evaluation

### Grafana Dashboard Configuration

```yaml
# observability/grafana/dashboards/finetuning.json

{
  "dashboard": {
    "title": "Model Fine-Tuning Monitor",
    "panels": [
      {
        "title": "Training Loss",
        "targets": [{
          "expr": "training_loss{job_id=\"$job_id\"}",
          "legendFormat": "Train Loss"
        }, {
          "expr": "eval_loss{job_id=\"$job_id\"}",
          "legendFormat": "Eval Loss"
        }],
        "type": "graph"
      },
      {
        "title": "GPU Utilization",
        "targets": [{
          "expr": "gpu_utilization{job_id=\"$job_id\"}",
          "legendFormat": "GPU {{gpu_id}}"
        }],
        "type": "graph"
      },
      {
        "title": "GPU Memory",
        "targets": [{
          "expr": "gpu_memory_allocated{job_id=\"$job_id\"}",
          "legendFormat": "Allocated"
        }, {
          "expr": "gpu_memory_cached{job_id=\"$job_id\"}",
          "legendFormat": "Cached"
        }],
        "type": "graph"
      },
      {
        "title": "Training Throughput",
        "targets": [{
          "expr": "samples_per_second{job_id=\"$job_id\"}",
          "legendFormat": "Samples/sec"
        }],
        "type": "stat"
      }
    ]
  }
}
```

### Automated Evaluation

```python
# backend/app/services/finetuning/evaluator.py

from evaluate import load

class ModelEvaluator:
    def evaluate(self, model, tokenizer, test_dataset, objective: str):
        """Run automated evaluation"""

        results = {}

        if objective == "qa":
            # QA metrics: ROUGE, BLEU
            rouge = load("rouge")
            bleu = load("bleu")

            predictions = []
            references = []

            for sample in test_dataset:
                prompt = f"### Question:\n{sample['question']}\n\n### Answer:\n"
                inputs = tokenizer(prompt, return_tensors="pt")
                outputs = model.generate(**inputs, max_new_tokens=128)
                prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)

                predictions.append(prediction)
                references.append(sample["answer"])

            results["rouge"] = rouge.compute(predictions=predictions, references=references)
            results["bleu"] = bleu.compute(predictions=predictions, references=references)

        elif objective == "classification":
            # Classification metrics: Accuracy, F1, Precision, Recall
            from sklearn.metrics import accuracy_score, f1_score, classification_report

            predictions = []
            labels = []

            for sample in test_dataset:
                prompt = f"Classify: {sample['text']}\n\nClass:"
                inputs = tokenizer(prompt, return_tensors="pt")
                outputs = model.generate(**inputs, max_new_tokens=10)
                prediction = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

                predictions.append(prediction)
                labels.append(sample["label"])

            results["accuracy"] = accuracy_score(labels, predictions)
            results["f1_macro"] = f1_score(labels, predictions, average="macro")
            results["classification_report"] = classification_report(labels, predictions)

        # Perplexity (for all objectives)
        perplexity = self.compute_perplexity(model, tokenizer, test_dataset)
        results["perplexity"] = perplexity

        return results

    def compute_perplexity(self, model, tokenizer, dataset):
        """Compute model perplexity"""
        import torch
        from torch.nn import CrossEntropyLoss

        loss_fct = CrossEntropyLoss()
        total_loss = 0
        total_tokens = 0

        for sample in dataset:
            inputs = tokenizer(sample["text"], return_tensors="pt")
            with torch.no_grad():
                outputs = model(**inputs, labels=inputs["input_ids"])
                total_loss += outputs.loss.item() * inputs["input_ids"].size(1)
                total_tokens += inputs["input_ids"].size(1)

        perplexity = torch.exp(torch.tensor(total_loss / total_tokens))
        return perplexity.item()
```

---

## Integration Points

### 1. Model Dropdown Integration

After a model is deployed, add it to the model selector:

```python
# backend/app/api/routes/models.py

@router.get("/api/v1/models")
async def list_models():
    """List all available models (base + fine-tuned)"""

    # Base models from Ollama
    base_models = await get_ollama_models()

    # Fine-tuned models
    finetuned_models = await db.execute(
        select(FineTunedModel).where(FineTunedModel.status == "deployed")
    )

    all_models = []

    # Add base models
    for model in base_models:
        all_models.append({
            "id": model.name,
            "name": model.name,
            "type": "base",
            "size": model.size,
        })

    # Add fine-tuned models
    for model in finetuned_models.scalars():
        all_models.append({
            "id": model.ollama_model_name,
            "name": model.name,
            "type": "finetuned",
            "base_model": model.base_model,
            "eval_metrics": model.eval_metrics,
            "badge": "🎯 Fine-tuned",
        })

    return {"models": all_models}
```

### 2. RAG Query Integration

Use fine-tuned models in RAG pipeline:

```python
# backend/app/services/rag_service.py

async def query(self, query: str, model_id: str, ...):
    """Modified to support fine-tuned models"""

    # Check if model is fine-tuned
    finetuned_model = await db.execute(
        select(FineTunedModel).where(FineTunedModel.ollama_model_name == model_id)
    )

    if finetuned_model:
        # Use fine-tuned model
        response = await self.llm_service.generate(
            model=model_id,
            prompt=prompt,
            context=context
        )

        # Track fine-tuned model usage
        finetuned_model.total_inferences += 1
        await db.commit()
    else:
        # Use base model
        response = await self.llm_service.generate(
            model=model_id,
            prompt=prompt,
            context=context
        )

    return response
```

---

## Infrastructure Requirements

### GPU Requirements

| Model Size | Quantization | VRAM Required | Recommended GPU |
|------------|--------------|---------------|-----------------|
| 7B | 4-bit (QLoRA) | 12 GB | RTX 3090, RTX 4090 |
| 7B | 8-bit | 16 GB | A100 (40GB) |
| 7B | Full Precision | 28 GB | A100 (40GB) |
| 13B | 4-bit (QLoRA) | 20 GB | RTX 4090, A100 |
| 13B | 8-bit | 32 GB | A100 (40GB) |
| 70B | 4-bit (QLoRA) | 48 GB | A100 (80GB) x2 |

### Storage Requirements

- **Datasets**: 10-100 GB (depending on size)
- **Model Checkpoints**: 5-50 GB per model
- **MLflow Artifacts**: 1-10 GB per experiment
- **Total Recommended**: 500 GB - 1 TB SSD

### Compute Infrastructure

```yaml
# docker-compose.yml additions

services:
  finetuning-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.finetuning
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - MLFLOW_TRACKING_URI=http://mlflow:5000
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    volumes:
      - ./models:/models
      - ./datasets:/datasets
    depends_on:
      - redis
      - postgres
      - mlflow
```

---

## Security & Compliance

### 1. Dataset Privacy

- **Encryption at Rest**: MinIO with encryption enabled
- **Encryption in Transit**: HTTPS for all uploads
- **Access Control**: RBAC for dataset access
- **Data Retention**: Configurable retention policies

### 2. Model Security

- **Model Signing**: Sign model artifacts
- **Checksum Verification**: Verify model integrity
- **Access Logs**: Audit all model deployments
- **Sandboxed Inference**: Isolate model execution

### 3. Compliance

- **GDPR**: Right to delete training data
- **Audit Trail**: Log all training jobs
- **Model Cards**: Document model capabilities and limitations

---

## Testing Strategy

### 1. Unit Tests

```python
# backend/tests/test_finetuning.py

def test_peft_trainer():
    """Test PEFT trainer initialization"""
    config = FineTuningConfig(
        base_model="facebook/opt-125m",
        quantization="4bit",
        lora_r=8,
        lora_alpha=16
    )

    trainer = PEFTTrainer(config)
    assert trainer.model is not None
    assert trainer.model.peft_config is not None

def test_dataset_preprocessing():
    """Test dataset preprocessing for different objectives"""
    dataset = load_dataset("csv", data_files="test.csv")

    preprocessor = DatasetPreprocessor()
    processed = preprocessor.preprocess_qa(dataset)

    assert "instruction" in processed.column_names
    assert "response" in processed.column_names
```

### 2. Integration Tests

```python
def test_end_to_end_finetuning():
    """Test complete fine-tuning workflow"""

    # 1. Upload dataset
    response = client.post("/api/v1/finetuning/datasets",
                          files={"file": open("test_dataset.csv")})
    dataset_id = response.json()["dataset_id"]

    # 2. Create job
    response = client.post("/api/v1/finetuning/jobs", json={
        "base_model": "facebook/opt-125m",
        "finetuning_method": "peft",
        "dataset_id": dataset_id,
        "hyperparameters": {"num_epochs": 1}
    })
    job_id = response.json()["job_id"]

    # 3. Wait for completion (with timeout)
    max_wait = 600  # 10 minutes
    elapsed = 0
    while elapsed < max_wait:
        response = client.get(f"/api/v1/finetuning/jobs/{job_id}")
        status = response.json()["status"]
        if status == "completed":
            break
        time.sleep(10)
        elapsed += 10

    assert status == "completed"

    # 4. Verify model registration
    response = client.get("/api/v1/finetuning/models")
    models = response.json()["models"]
    assert any(m["job_id"] == job_id for m in models)
```

### 3. Performance Tests

```python
def test_training_speed():
    """Test training throughput"""

    trainer = PEFTTrainer(config)
    start_time = time.time()

    trainer.train(small_dataset)

    elapsed = time.time() - start_time
    samples_per_second = len(small_dataset) / elapsed

    assert samples_per_second > 10  # Should process >10 samples/sec
```

---

## Timeline & Milestones

### Phase 1: Foundation (Weeks 1-2)
**Deliverables**:
- ✅ Database schema
- ✅ Basic API endpoints
- ✅ Admin UI skeleton
- ✅ Dataset upload

**Acceptance Criteria**:
- Can upload dataset
- Can create fine-tuning job record
- UI displays job list

---

### Phase 2: PEFT (Weeks 2-3)
**Deliverables**:
- ✅ PEFT trainer (LoRA/QLoRA)
- ✅ 4-bit quantization support
- ✅ Real-time monitoring
- ✅ Checkpoint saving

**Acceptance Criteria**:
- Can fine-tune 7B model on single GPU (24GB VRAM)
- Training completes in < 4 hours for 10k samples
- Metrics visible in real-time

---

### Phase 3: SFT (Weeks 3-4)
**Deliverables**:
- ✅ SFT trainer
- ✅ Multi-objective support
- ✅ Intelligent preprocessing
- ✅ Evaluation pipeline

**Acceptance Criteria**:
- Support QA, Classification, Summarization objectives
- Automatic dataset formatting
- Evaluation metrics computed

---

### Phase 4: RLHF (Week 4-5)
**Deliverables**:
- ✅ Reward model training
- ✅ PPO trainer
- ✅ Preference data collection UI
- ✅ Evaluation

**Acceptance Criteria**:
- Can train reward model
- PPO training completes successfully
- Model shows improvement on preference tasks

---

### Phase 5: RLFG (Week 5)
**Deliverables**:
- ✅ GRPO trainer
- ✅ Custom reward functions
- ✅ Multi-objective optimization

**Acceptance Criteria**:
- GRPO training works
- Custom rewards configurable
- Better sample efficiency than PPO

---

### Phase 6: Deployment (Week 6)
**Deliverables**:
- ✅ Model registry
- ✅ Deployment pipeline
- ✅ Model versioning
- ✅ A/B testing

**Acceptance Criteria**:
- Fine-tuned model appears in dropdown
- Can deploy to Ollama
- Inference works correctly
- Metrics tracked

---

## Next Steps

### Immediate Actions (Week 1)

1. **Review & Approval**
   - [ ] Review this implementation plan
   - [ ] Approve technology stack
   - [ ] Allocate GPU resources
   - [ ] Assign development team

2. **Infrastructure Setup**
   - [ ] Provision GPU servers
   - [ ] Set up MLflow tracking server
   - [ ] Configure Celery workers
   - [ ] Set up Grafana dashboards

3. **Database Schema**
   - [ ] Create migration for `finetuning_jobs`
   - [ ] Create migration for `finetuning_datasets`
   - [ ] Create migration for `finetuned_models`
   - [ ] Create migration for `training_metrics`

4. **Initial Development**
   - [ ] Create backend service stubs
   - [ ] Create frontend admin page skeleton
   - [ ] Set up development environment
   - [ ] Write initial unit tests

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| GPU availability | High | Medium | Use cloud GPUs (AWS, GCP) as backup |
| Training time too long | Medium | Medium | Optimize batch size, use DeepSpeed |
| Out of memory errors | High | High | Use gradient checkpointing, QLoRA |
| Model quality issues | High | Low | Extensive evaluation, A/B testing |
| Integration complexity | Medium | Medium | Phased rollout, extensive testing |

---

## Success Criteria

### Technical Metrics
- ✅ Fine-tune 7B model in < 4 hours (single GPU)
- ✅ Support 4 fine-tuning methods (PEFT, SFT, RLHF, RLFG)
- ✅ Real-time metrics with < 1s latency
- ✅ Deployment time < 5 minutes
- ✅ Support concurrent training (multi-GPU)

### Business Metrics
- ✅ Improve domain-specific accuracy by >20%
- ✅ Reduce inference latency vs generic models
- ✅ Enable self-service fine-tuning for users
- ✅ Model registry with >10 fine-tuned models

### User Experience
- ✅ Intuitive UI for non-ML experts
- ✅ Clear error messages and validation
- ✅ Comprehensive training monitoring
- ✅ Easy model comparison and deployment

---

**Status**: 📋 Ready for Review and Implementation

**Estimated Total Effort**: 4-6 weeks with 3 developers

**Dependencies**:
- GPU infrastructure (1-2x A100 or equivalent)
- 500GB+ SSD storage
- Redis for task queue
- MLflow for experiment tracking

**Contacts**:
- ML Engineering: [To be assigned]
- Backend: [To be assigned]
- Frontend: [To be assigned]
- DevOps: [To be assigned]

---

**Document Version**: 1.0.0
**Last Updated**: 2025-12-14
**Next Review**: After Phase 1 completion
