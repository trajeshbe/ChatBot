"""
SQLAlchemy ORM Models for Model Fine-Tuning

This module defines the database models for the fine-tuning system including:
- FineTuningDataset: Uploaded datasets for training
- FineTuningJob: Training job configurations and status
- FineTunedModel: Model registry with deployment info
- TrainingMetric: Time-series metrics during training

Reference: docs/features/MODEL_FINETUNING_IMPLEMENTATION_PLAN.md
Migration: backend/migrations/019_add_finetuning_tables.sql
"""

from sqlalchemy import (
    Column, String, DateTime, Integer, Text, ForeignKey,
    Boolean, Float, JSON, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.models.database import Base


class FineTuningDataset(Base):
    """
    Dataset uploaded for model fine-tuning

    Supports multiple formats:
    - QA: Question-answer pairs
    - Classification: Text-label pairs
    - Instruction: Instruction-response pairs
    - Preference: Prompt with chosen/rejected responses (for RLHF)
    - Summarization: Document-summary pairs
    """
    __tablename__ = "finetuning_datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Dataset metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # File info
    filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=True)
    file_type = Column(String(50), nullable=True)  # "csv", "json", "jsonl", "parquet"
    minio_path = Column(String(512), nullable=True)

    # Dataset statistics
    num_samples = Column(Integer, nullable=True)
    num_train_samples = Column(Integer, nullable=True)
    num_val_samples = Column(Integer, nullable=True)

    # Schema/format
    format_type = Column(String(100), nullable=True)  # "qa", "classification", "instruction", "preference", "summarization"
    columns = Column(JSON, nullable=True)  # Column mapping configuration

    # Validation
    is_valid = Column(Boolean, default=False)
    validation_errors = Column(JSON, nullable=True)

    # Preview
    sample_rows = Column(JSON, nullable=True)  # First 5 rows for preview

    # Processing status
    preprocessing_status = Column(String(50), default='pending')  # pending, processing, completed, failed
    preprocessed_path = Column(String(512), nullable=True)

    # Project association
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    jobs = relationship("FineTuningJob", back_populates="dataset")

    def __repr__(self):
        return f"<FineTuningDataset(id={self.id}, name={self.name}, format={self.format_type}, samples={self.num_samples})>"


class FineTuningJob(Base):
    """
    Fine-tuning job configuration and execution status

    Supports multiple methods:
    - PEFT: Parameter-Efficient Fine-Tuning (LoRA/QLoRA)
    - SFT: Supervised Fine-Tuning
    - RLHF-PPO: Reinforcement Learning from Human Feedback with PPO
    - RLHF-GRPO: RLHF with Group Relative Policy Optimization (DeepSeek-style)
    """
    __tablename__ = "finetuning_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Job metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Model configuration
    base_model = Column(String(255), nullable=False)  # e.g., "Qwen/Qwen2.5-7B-Instruct"
    quantization = Column(String(50), nullable=True)  # "4bit", "8bit", "none"

    # Fine-tuning configuration
    finetuning_method = Column(String(50), nullable=False)  # "peft", "sft", "rlhf-ppo", "rlhf-grpo"
    training_objective = Column(String(100), nullable=False)  # "qa", "classification", "summarization", "instruction"

    # Dataset
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("finetuning_datasets.id", ondelete="SET NULL"), nullable=True)
    train_split = Column(Float, default=0.8)  # Train/validation split ratio

    # Hyperparameters (stored as JSON for flexibility)
    hyperparameters = Column(JSON, nullable=True)

    # Training status
    status = Column(String(50), default='pending')  # pending, queued, running, completed, failed, cancelled
    progress = Column(Float, default=0.0)  # 0.0 to 1.0

    # Training pipeline stages
    training_stage = Column(String(50), default='queued')  # queued, setup, tokenizer_load, model_download, model_load, dataset_prep, training, checkpoint_save, completed, failed
    stage_details = Column(JSON, default={})  # Stage-specific metadata (download progress, current file, etc.)
    stage_started_at = Column(DateTime(timezone=True), nullable=True)  # When current stage started
    stage_completed_at = Column(DateTime(timezone=True), nullable=True)  # When current stage completed

    # Training metrics (current values)
    current_epoch = Column(Integer, nullable=True)
    current_step = Column(Integer, nullable=True)
    total_steps = Column(Integer, nullable=True)
    train_loss = Column(Float, nullable=True)
    eval_loss = Column(Float, nullable=True)

    # Results
    final_model_name = Column(String(255), nullable=True)
    mlflow_run_id = Column(String(255), nullable=True)
    minio_checkpoint_path = Column(String(512), nullable=True)

    # Training logs
    logs = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    # Resource usage
    gpu_type = Column(String(100), nullable=True)
    gpu_count = Column(Integer, default=1)
    training_time_seconds = Column(Integer, nullable=True)
    training_start_time = Column(DateTime(timezone=True), nullable=True)
    training_end_time = Column(DateTime(timezone=True), nullable=True)

    # Project association
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    department = Column(String(255), nullable=True)
    team = Column(String(255), nullable=True)

    # Celery task tracking
    celery_task_id = Column(String(255), nullable=True)

    # Relationships
    dataset = relationship("FineTuningDataset", back_populates="jobs")
    model = relationship("FineTunedModel", back_populates="job", uselist=False)
    metrics = relationship("TrainingMetric", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<FineTuningJob(id={self.id}, name={self.name}, method={self.finetuning_method}, status={self.status})>"


class FineTunedModel(Base):
    """
    Registry of fine-tuned models with deployment information

    Tracks:
    - Model versions and lineage
    - Deployment status (registered, deployed, archived)
    - Evaluation metrics
    - Usage statistics
    """
    __tablename__ = "finetuned_models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Model metadata
    name = Column(String(255), nullable=False)
    version = Column(String(50), default='v1.0.0')
    description = Column(Text, nullable=True)

    # Source job
    job_id = Column(UUID(as_uuid=True), ForeignKey("finetuning_jobs.id", ondelete="SET NULL"), nullable=True)
    base_model = Column(String(255), nullable=False)
    finetuning_method = Column(String(50), nullable=True)

    # Model artifacts
    mlflow_model_uri = Column(String(512), nullable=True)
    mlflow_run_id = Column(String(255), nullable=True)
    minio_checkpoint_path = Column(String(512), nullable=True)
    adapter_config = Column(JSON, nullable=True)  # PEFT adapter configuration

    # Merge tracking (migration 023)
    merged_model_path = Column(Text, nullable=True)  # Path to merged model (workspace or MinIO)
    merge_duration_seconds = Column(Integer, nullable=True)  # Duration of merge operation
    merge_requested_at = Column(DateTime(timezone=True), nullable=True)  # When merge was requested
    merge_error_message = Column(Text, nullable=True)  # Error message if merge failed

    # Evaluation metrics
    eval_metrics = Column(JSON, nullable=True)  # accuracy, perplexity, ROUGE, BLEU, etc.

    # Deployment
    status = Column(String(50), default='registered')  # registered, deployed, archived, deprecated
    deployment_url = Column(String(512), nullable=True)
    ollama_model_name = Column(String(255), nullable=True)
    vllm_model_name = Column(String(255), nullable=True)

    # Usage tracking
    total_inferences = Column(Integer, default=0)
    avg_latency_ms = Column(Float, nullable=True)
    last_inference_at = Column(DateTime(timezone=True), nullable=True)

    # Versioning and lineage
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    parent_model_id = Column(UUID(as_uuid=True), ForeignKey("finetuned_models.id", ondelete="SET NULL"), nullable=True)

    # Deprecation
    deprecated_at = Column(DateTime(timezone=True), nullable=True)
    deprecated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    deprecation_reason = Column(Text, nullable=True)

    # Project association
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)

    # Model tags for categorization
    tags = Column(JSON, nullable=True)  # ["production", "customer-support", "v2"]

    # Relationships
    job = relationship("FineTuningJob", back_populates="model")
    children = relationship("FineTunedModel", backref="parent", remote_side=[id])

    def __repr__(self):
        return f"<FineTunedModel(id={self.id}, name={self.name}, version={self.version}, status={self.status})>"


class TrainingMetric(Base):
    """
    Time-series metrics collected during model training

    Stores:
    - Loss metrics (train, eval)
    - Resource utilization (GPU, memory)
    - Performance metrics (throughput, latency)
    - Custom metrics (RLHF rewards, KL divergence, etc.)
    """
    __tablename__ = "training_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("finetuning_jobs.id", ondelete="CASCADE"), nullable=False)

    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Training progress
    epoch = Column(Integer, nullable=True)
    step = Column(Integer, nullable=True)

    # Loss metrics
    train_loss = Column(Float, nullable=True)
    eval_loss = Column(Float, nullable=True)
    gradient_norm = Column(Float, nullable=True)

    # Learning metrics
    learning_rate = Column(Float, nullable=True)

    # Resource metrics
    gpu_utilization = Column(Float, nullable=True)  # 0.0 to 1.0
    gpu_memory_allocated = Column(BigInteger, nullable=True)  # bytes
    gpu_memory_reserved = Column(BigInteger, nullable=True)  # bytes
    gpu_temperature = Column(Float, nullable=True)  # celsius

    # Performance metrics
    samples_per_second = Column(Float, nullable=True)
    tokens_per_second = Column(Float, nullable=True)
    batch_processing_time_ms = Column(Float, nullable=True)

    # Custom metrics (flexible, method-specific)
    custom_metrics = Column(JSON, nullable=True)  # e.g., {"kl_divergence": 0.05, "reward": 0.85}

    # Relationship
    job = relationship("FineTuningJob", back_populates="metrics")

    def __repr__(self):
        return f"<TrainingMetric(job_id={self.job_id}, step={self.step}, train_loss={self.train_loss})>"


class ModelApproval(Base):
    """
    Model deployment approval workflow

    Tracks approval requests for deploying fine-tuned models to production.
    Implements governance controls to ensure only reviewed models are deployed.

    Workflow:
    1. User requests deployment approval
    2. Admin/Approver reviews model metrics and checkpoints
    3. Admin approves or rejects with comments
    4. Approved models can be deployed to Ollama/vLLM
    """
    __tablename__ = "model_approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("finetuned_models.id", ondelete="CASCADE"), nullable=False)

    # Request details
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    request_reason = Column(Text, nullable=True)  # Why deployment is needed

    # Approval/rejection
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="pending")  # pending, approved, rejected
    review_comments = Column(Text, nullable=True)

    # Deployment constraints (optional)
    deployment_environment = Column(String(100), nullable=True)  # "production", "staging", "development"
    max_concurrent_instances = Column(Integer, nullable=True)
    resource_limits = Column(JSON, nullable=True)  # {"max_memory_gb": 16, "max_gpu_count": 1}

    # Relationships
    model = relationship("FineTunedModel", foreign_keys=[model_id])
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])

    def __repr__(self):
        return f"<ModelApproval(id={self.id}, model_id={self.model_id}, status={self.status})>"


# Helper functions for type conversion and validation

def validate_hyperparameters(method: str, hyperparameters: dict) -> bool:
    """
    Validate hyperparameters based on fine-tuning method

    Args:
        method: Fine-tuning method (peft, sft, rlhf-ppo, rlhf-grpo)
        hyperparameters: Dictionary of hyperparameters

    Returns:
        True if valid, False otherwise
    """
    required_params = {
        "peft": ["learning_rate", "lora_r", "lora_alpha"],
        "sft": ["learning_rate", "num_epochs"],
        "rlhf-ppo": ["learning_rate", "ppo_epochs"],
        "rlhf-grpo": ["learning_rate", "group_size"]
    }

    if method not in required_params:
        return False

    return all(param in hyperparameters for param in required_params[method])


def get_default_hyperparameters(method: str) -> dict:
    """
    Get default hyperparameters for a fine-tuning method

    Args:
        method: Fine-tuning method

    Returns:
        Dictionary of default hyperparameters
    """
    defaults = {
        "peft": {
            "learning_rate": 2e-4,
            "num_epochs": 3,
            "batch_size": 4,
            "gradient_accumulation_steps": 4,
            "lora_r": 16,
            "lora_alpha": 32,
            "lora_dropout": 0.05,
            "target_modules": ["q_proj", "v_proj"],
            "warmup_steps": 100,
            "max_seq_length": 2048
        },
        "sft": {
            "learning_rate": 2e-5,
            "num_epochs": 3,
            "batch_size": 4,
            "gradient_accumulation_steps": 4,
            "max_seq_length": 2048,
            "warmup_steps": 100,
            "packing": True
        },
        "rlhf-ppo": {
            "learning_rate": 1.41e-5,
            "batch_size": 16,
            "mini_batch_size": 4,
            "ppo_epochs": 4,
            "init_kl_coef": 0.2,
            "target_kl": 6.0
        },
        "rlhf-grpo": {
            "learning_rate": 1e-5,
            "beta": 0.1,
            "group_size": 4,
            "num_iterations": 100,
            "batch_size": 16
        }
    }

    return defaults.get(method, {})
