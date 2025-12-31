"""
Pydantic Schemas for Model Fine-Tuning API

Request and response models for:
- Dataset upload and validation
- Fine-tuning job creation and management
- Model registry and deployment
- Training metrics and monitoring

Reference: docs/features/MODEL_FINETUNING_IMPLEMENTATION_PLAN.md
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from uuid import UUID


# ============================================================================
# Dataset Schemas
# ============================================================================

class DatasetUploadRequest(BaseModel):
    """Request schema for uploading a fine-tuning dataset"""
    name: str = Field(..., description="Dataset name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Dataset description")
    format_type: Literal["qa", "classification", "instruction", "preference", "summarization"] = Field(
        ..., description="Dataset format type"
    )
    columns: Dict[str, str] = Field(
        ...,
        description="Mapping of dataset columns to expected fields",
        examples=[{"question": "question_column", "answer": "answer_column"}]
    )
    project_id: Optional[UUID] = Field(None, description="Project ID for access control")

    class Config:
        schema_extra = {
            "example": {
                "name": "Customer Support QA Dataset",
                "description": "10K customer support question-answer pairs",
                "format_type": "qa",
                "columns": {
                    "question": "user_query",
                    "answer": "agent_response"
                },
                "project_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class DatasetValidationRequest(BaseModel):
    """Request to validate a dataset"""
    dataset_id: UUID = Field(..., description="Dataset ID to validate")


class DatasetUploadResponse(BaseModel):
    """Response after uploading a dataset"""
    id: str
    name: str
    filename: str
    format_type: str
    status: str
    num_samples: Optional[int] = None
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class DatasetValidationResponse(BaseModel):
    """Response from dataset validation"""
    dataset_id: str
    is_valid: bool
    num_samples: Optional[int] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    quality_metrics: Dict[str, Any] = Field(default_factory=dict)
    sample_preview: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        schema_extra = {
            "example": {
                "dataset_id": "123e4567-e89b-12d3-a456-426614174000",
                "is_valid": True,
                "num_samples": 10000,
                "errors": [],
                "warnings": ["Some samples have very short responses"],
                "quality_metrics": {"avg_length": 150, "vocab_size": 5000},
                "sample_preview": [
                    {"question": "How do I reset my password?", "answer": "Click on 'Forgot Password'..."}
                ]
            }
        }


class DatasetResponse(BaseModel):
    """Dataset details response"""
    id: UUID
    name: str
    description: Optional[str] = None
    filename: str
    file_size: Optional[int] = None
    format_type: Optional[str] = None
    num_samples: Optional[int] = None
    is_valid: bool
    preprocessing_status: str
    uploaded_at: datetime
    uploaded_by: Optional[UUID] = None
    project_id: Optional[UUID] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ============================================================================
# Fine-Tuning Job Schemas
# ============================================================================

class HyperparametersBase(BaseModel):
    """Base hyperparameters common to all methods"""
    learning_rate: float = Field(2e-4, description="Learning rate", gt=0)
    num_epochs: int = Field(3, description="Number of training epochs", ge=1)
    batch_size: int = Field(4, description="Training batch size", ge=1)
    gradient_accumulation_steps: int = Field(4, description="Gradient accumulation steps", ge=1)
    warmup_steps: int = Field(100, description="Number of warmup steps", ge=0)
    max_seq_length: int = Field(2048, description="Maximum sequence length", ge=1)
    min_gpu_memory_gb: float = Field(6.0, description="Minimum GPU memory required (GB)", ge=1, le=80)


class PEFTHyperparameters(HyperparametersBase):
    """Hyperparameters for PEFT (LoRA/QLoRA) fine-tuning"""
    lora_r: int = Field(16, description="LoRA rank", ge=1)
    lora_alpha: int = Field(32, description="LoRA alpha (scaling factor)", ge=1)
    lora_dropout: float = Field(0.05, description="LoRA dropout", ge=0, le=1)
    target_modules: List[str] = Field(
        ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        description="Target modules for LoRA (attention + MLP layers)"
    )


class SFTHyperparameters(HyperparametersBase):
    """Hyperparameters for Supervised Fine-Tuning"""
    packing: bool = Field(True, description="Pack multiple samples into one sequence")


class RLHFPPOHyperparameters(BaseModel):
    """Hyperparameters for RLHF with PPO"""
    learning_rate: float = Field(1.41e-5, description="Learning rate", gt=0)
    batch_size: int = Field(16, description="Batch size", ge=1)
    mini_batch_size: int = Field(4, description="Mini-batch size for PPO", ge=1)
    ppo_epochs: int = Field(4, description="Number of PPO epochs", ge=1)
    init_kl_coef: float = Field(0.2, description="Initial KL divergence coefficient", ge=0)
    target_kl: float = Field(6.0, description="Target KL divergence", ge=0)


class RLHFGRPOHyperparameters(BaseModel):
    """Hyperparameters for RLHF with GRPO (DeepSeek-style)"""
    learning_rate: float = Field(1e-5, description="Learning rate", gt=0)
    beta: float = Field(0.1, description="KL penalty coefficient", ge=0)
    group_size: int = Field(4, description="Number of responses to compare per prompt", ge=2)
    num_iterations: int = Field(100, description="Number of training iterations", ge=1)
    batch_size: int = Field(16, description="Batch size", ge=1)
    reward_weights: Optional[Dict[str, float]] = Field(
        default={
            "helpfulness": 0.4,
            "harmlessness": 0.2,
            "honesty": 0.2,
            "format": 0.1,
            "fluency": 0.05,
            "length": 0.05
        },
        description="Weights for multi-objective reward function"
    )


class FineTuningJobCreateRequest(BaseModel):
    """Request to create a fine-tuning job"""
    name: str = Field(..., description="Job name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Job description")
    base_model: str = Field(..., description="Base model name (e.g., Qwen/Qwen2.5-7B-Instruct)")
    quantization: Optional[Literal["4bit", "8bit", "none"]] = Field("4bit", description="Quantization type")
    finetuning_method: Literal["peft", "sft", "rlhf-ppo", "rlhf-grpo"] = Field(
        ..., description="Fine-tuning method"
    )
    training_objective: Literal["qa", "classification", "summarization", "instruction"] = Field(
        ..., description="Training objective"
    )
    dataset_id: UUID = Field(..., description="Dataset ID to use for training")
    train_split: float = Field(0.8, description="Train/validation split ratio", ge=0.1, le=0.9)
    hyperparameters: Dict[str, Any] = Field(..., description="Hyperparameters (method-specific)")
    project_id: Optional[UUID] = Field(None, description="Project ID")
    auto_start: bool = Field(False, description="Automatically start training after job creation")

    @validator('hyperparameters')
    def validate_hyperparameters(cls, v, values):
        """Validate hyperparameters based on method"""
        if 'finetuning_method' in values:
            method = values['finetuning_method']
            # Basic validation - ensure required keys exist
            if method == "peft" and 'lora_r' not in v:
                raise ValueError("PEFT method requires 'lora_r' in hyperparameters")
            elif method in ["rlhf-ppo", "rlhf-grpo"] and 'batch_size' not in v:
                raise ValueError(f"{method} requires 'batch_size' in hyperparameters")
        return v

    class Config:
        schema_extra = {
            "example": {
                "name": "Customer Support QA - Qwen-7B",
                "description": "Fine-tune Qwen 7B for customer support QA",
                "base_model": "Qwen/Qwen2.5-7B-Instruct",
                "quantization": "4bit",
                "finetuning_method": "peft",
                "training_objective": "qa",
                "dataset_id": "123e4567-e89b-12d3-a456-426614174000",
                "train_split": 0.8,
                "hyperparameters": {
                    "learning_rate": 0.0002,
                    "num_epochs": 3,
                    "batch_size": 4,
                    "lora_r": 16,
                    "lora_alpha": 32
                },
                "project_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class FineTuningJobResponse(BaseModel):
    """Response with job details"""
    id: UUID
    name: str
    description: Optional[str] = None
    base_model: str
    quantization: Optional[str] = None
    finetuning_method: str
    training_objective: str
    status: str
    progress: float
    current_epoch: Optional[int] = None
    current_step: Optional[int] = None
    total_steps: Optional[int] = None
    train_loss: Optional[float] = None
    eval_loss: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    dataset_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    error_message: Optional[str] = None
    training_stage: Optional[str] = None  # Current pipeline stage

    class Config:
        orm_mode = True
        from_attributes = True


class FineTuningJobListResponse(BaseModel):
    """Response with list of jobs"""
    jobs: List["FineTuningJobDetailResponse"]
    total: int
    limit: int
    offset: int


class FineTuningJobDetailResponse(BaseModel):
    """Detailed job response with hyperparameters and metrics"""
    id: str
    name: str
    base_model: str
    finetuning_method: str
    training_objective: str
    status: str
    hyperparameters: Optional[Dict[str, Any]] = None
    checkpoint_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    training_duration_seconds: Optional[int] = None

    # Training progress fields
    progress: Optional[float] = None
    current_epoch: Optional[int] = None
    current_step: Optional[int] = None
    total_steps: Optional[int] = None
    train_loss: Optional[float] = None
    eval_loss: Optional[float] = None

    # Pipeline stage tracking
    training_stage: Optional[str] = None  # queued, setup, tokenizer_load, model_download, model_load, dataset_prep, training, checkpoint_save, completed, failed
    stage_details: Optional[Dict[str, Any]] = None  # Stage-specific metadata (download progress, current file, etc.)
    stage_started_at: Optional[datetime] = None  # When current stage started
    stage_completed_at: Optional[datetime] = None  # When current stage completed

    # Resource tracking
    gpu_type: Optional[str] = None
    gpu_count: Optional[int] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ============================================================================
# Model Registry Schemas
# ============================================================================

class ModelRegisterRequest(BaseModel):
    """Request to register a fine-tuned model"""
    job_id: UUID = Field(..., description="Fine-tuning job ID")
    name: str = Field(..., description="Model name", min_length=1, max_length=255)
    version: str = Field("v1.0.0", description="Model version (semantic versioning)")
    description: Optional[str] = Field(None, description="Model description")
    tags: Optional[List[str]] = Field(None, description="Model tags for categorization")

    class Config:
        schema_extra = {
            "example": {
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "customer-support-qwen-v1",
                "version": "v1.0.0",
                "description": "Qwen 7B fine-tuned for customer support QA",
                "tags": ["production", "customer-support", "qwen"]
            }
        }


class ModelDeployRequest(BaseModel):
    """Request to deploy a fine-tuned model"""
    deployment_target: Literal["ollama", "vllm"] = Field(..., description="Deployment target")
    deployment_config: Optional[Dict[str, Any]] = Field(
        default={},
        description="Deployment configuration",
        examples=[{"context_length": 4096, "num_gpu": 1}]
    )


class ModelDeployResponse(BaseModel):
    """Response from model deployment"""
    model_id: UUID
    status: str
    deployment_url: Optional[str] = None
    ollama_model_name: Optional[str] = None
    vllm_model_name: Optional[str] = None


class FineTunedModelResponse(BaseModel):
    """Response with fine-tuned model details"""
    id: UUID
    name: str
    version: str
    description: Optional[str] = None
    base_model: str
    finetuning_method: Optional[str] = None
    status: str
    eval_metrics: Optional[Dict[str, Any]] = None
    total_inferences: int
    avg_latency_ms: Optional[float] = None
    created_at: datetime
    created_by: Optional[UUID] = None
    project_id: Optional[UUID] = None
    tags: Optional[List[str]] = None

    class Config:
        orm_mode = True
        from_attributes = True


class FineTunedModelListResponse(BaseModel):
    """Response with list of fine-tuned models"""
    models: List[FineTunedModelResponse]
    total: int


# ============================================================================
# Training Metrics Schemas
# ============================================================================

class TrainingMetricResponse(BaseModel):
    """Real-time training metric"""
    timestamp: datetime
    epoch: Optional[int] = None
    step: Optional[int] = None
    train_loss: Optional[float] = None
    eval_loss: Optional[float] = None
    learning_rate: Optional[float] = None
    gpu_utilization: Optional[float] = None
    gpu_memory_allocated: Optional[int] = None
    samples_per_second: Optional[float] = None
    tokens_per_second: Optional[float] = None
    custom_metrics: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True
        from_attributes = True


class TrainingLogsResponse(BaseModel):
    """Training logs response"""
    job_id: UUID
    logs: List[str]
    tail: int = Field(100, description="Number of lines returned")


# ============================================================================
# Evaluation Schemas
# ============================================================================

class EvaluationRequest(BaseModel):
    """Request to evaluate a fine-tuned model"""
    model_id: UUID = Field(..., description="Model ID to evaluate")
    test_dataset_id: UUID = Field(..., description="Test dataset ID")
    metrics: List[Literal["accuracy", "perplexity", "rouge", "bleu", "f1"]] = Field(
        ["accuracy", "perplexity"],
        description="Metrics to compute"
    )


class EvaluationResponse(BaseModel):
    """Evaluation results"""
    evaluation_id: UUID
    model_id: UUID
    status: Literal["running", "completed", "failed"]
    metrics: Optional[Dict[str, float]] = None
    sample_predictions: Optional[List[Dict[str, Any]]] = None

    class Config:
        schema_extra = {
            "example": {
                "evaluation_id": "123e4567-e89b-12d3-a456-426614174000",
                "model_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "completed",
                "metrics": {
                    "accuracy": 0.92,
                    "perplexity": 3.45,
                    "rouge_1": 0.65,
                    "rouge_l": 0.67,
                    "bleu": 0.72
                },
                "sample_predictions": [
                    {
                        "input": "How do I reset my password?",
                        "prediction": "Click on 'Forgot Password' and follow the instructions.",
                        "reference": "To reset your password, click 'Forgot Password'."
                    }
                ]
            }
        }


# ============================================================================
# Utility Schemas
# ============================================================================

class BaseModelInfo(BaseModel):
    """Information about available base models"""
    id: str
    name: str
    size: str
    parameters: str
    quantization_options: List[str]
    recommended_vram: str

    class Config:
        schema_extra = {
            "example": {
                "id": "Qwen/Qwen2.5-7B-Instruct",
                "name": "Qwen 2.5 7B Instruct",
                "size": "7B",
                "parameters": "7 billion",
                "quantization_options": ["4bit", "8bit", "none"],
                "recommended_vram": "12GB (4-bit), 16GB (8-bit), 28GB (full)"
            }
        }


class BaseModelsListResponse(BaseModel):
    """Response with list of available base models"""
    models: List[BaseModelInfo]


class JobCancelRequest(BaseModel):
    """Request to cancel a training job"""
    job_id: UUID


class JobCancelResponse(BaseModel):
    """Response from job cancellation"""
    job_id: UUID
    status: str
    message: str = "Job cancelled successfully"


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    status_code: int

    class Config:
        schema_extra = {
            "example": {
                "error": "Dataset validation failed",
                "detail": "Missing required column: 'question'",
                "status_code": 400
            }
        }


# ============================================================================
# Additional Response Schemas (for API compatibility)
# ============================================================================

class DatasetDetailResponse(BaseModel):
    """Detailed dataset response"""
    id: str
    name: str
    filename: str
    format_type: str
    training_objective: Optional[str] = None
    status: str
    num_samples: Optional[int] = None
    file_size_bytes: Optional[int] = None
    validation_errors: Optional[List[str]] = None
    is_valid: Optional[bool] = None  # Validation status flag
    sample_rows: Optional[List[str]] = None  # Quality preview samples
    meta_info: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class DatasetListResponse(BaseModel):
    """Response with paginated list of datasets"""
    datasets: List[DatasetDetailResponse]
    total: int
    limit: int
    offset: int


class TrainingMetricsResponse(BaseModel):
    """Training metrics response"""
    id: str
    job_id: str
    step: int
    epoch: Optional[int] = None
    loss: Optional[float] = None
    learning_rate: Optional[float] = None
    accuracy: Optional[float] = None
    additional_metrics: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class JobMetricsHistoryResponse(BaseModel):
    """Job metrics history response"""
    job_id: str
    metrics: List[TrainingMetricsResponse]
    latest_metrics: Optional[TrainingMetricsResponse] = None


class FineTunedModelDetailResponse(BaseModel):
    """Detailed fine-tuned model response"""
    id: str
    model_name: str
    version: str
    base_model: str
    finetuning_method: str
    status: str
    checkpoint_path: Optional[str] = None
    deployment_info: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    usage_count: Optional[int] = 0
    created_at: datetime
    deployed_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


class ModelRegistrationRequest(BaseModel):
    """Request to register a fine-tuned model (alias for compatibility)"""
    job_id: str
    model_name: str
    version: str = "v1.0.0"
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class ModelUndeployRequest(BaseModel):
    """Request to undeploy a model"""
    force: bool = False


class GPUStatusResponse(BaseModel):
    """GPU status response"""
    device_id: int
    name: str
    total_memory_gb: float
    free_memory_gb: float
    utilization_percent: float
    temperature_celsius: Optional[float] = None
    is_available: bool
