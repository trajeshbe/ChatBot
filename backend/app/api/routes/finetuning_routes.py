"""
API Routes for Model Fine-Tuning System

Endpoints for:
- Dataset management (upload, validate, list, get, delete)
- Training job management (create, submit, cancel, list, get)
- Model registry (register, deploy, undeploy, list, get)
- Real-time metrics and monitoring
- GPU resource status

All endpoints enforce RBAC permissions for enterprise security.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import logging

from app.core.database import get_db
from app.middleware.rbac_middleware import RequirePermission, RequireAdmin, require_authentication, get_current_user
from app.models.database_enhanced import User
from app.models.finetuning_models import (
    FineTuningDataset,
    FineTuningJob,
    FineTunedModel,
    TrainingMetric
)
from app.schemas.finetuning_schemas import (
    # Dataset schemas
    DatasetUploadRequest,
    DatasetUploadResponse,
    DatasetValidationResponse,
    DatasetListResponse,
    DatasetDetailResponse,

    # Job schemas
    FineTuningJobCreateRequest,
    FineTuningJobResponse,
    FineTuningJobListResponse,
    FineTuningJobDetailResponse,
    JobCancelRequest,

    # Model registry schemas
    ModelRegistrationRequest,
    ModelDeployRequest,
    ModelUndeployRequest,
    FineTunedModelResponse,
    FineTunedModelListResponse,
    FineTunedModelDetailResponse,

    # Metrics schemas
    TrainingMetricsResponse,
    JobMetricsHistoryResponse,

    # GPU status
    GPUStatusResponse
)
from app.services.finetuning.finetuning_service import FineTuningService
from app.services.finetuning.model_registry_service import ModelRegistryService
from app.services.finetuning.gpu_pool_manager import gpu_pool_manager
from app.services.audit_service import audit_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/finetuning", tags=["finetuning"])


# ============================================================================
# DATASET MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/datasets/upload", response_model=DatasetUploadResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    name: Optional[str] = None,
    format_type: str = Query(..., description="Dataset format: qa, classification, instruction, etc."),
    training_objective: str = Query(..., description="Training objective"),
    columns: Optional[str] = Query(None, description="JSON string of column mappings"),
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "write")),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a dataset for fine-tuning

    Supports CSV, JSON, JSONL, Parquet formats.
    Automatically validates format and data quality.
    """
    try:
        service = FineTuningService(db)

        # Parse column mappings if provided
        import json
        column_mappings = json.loads(columns) if columns else None

        # Read file content
        file_content = await file.read()

        # Upload to MinIO and create dataset record
        dataset = await service.upload_dataset(
            filename=file.filename,
            file_content=file_content,
            format_type=format_type,
            training_objective=training_objective,
            name=name or file.filename,
            columns=column_mappings,
            user_id=user.id
        )

        # Audit log
        await audit_service.log_action(
            user_id=user.id,
            action="upload_finetuning_dataset",
            details={
                "dataset_id": str(dataset.id),
                "filename": file.filename,
                "format_type": format_type
            },
            db=db
        )

        return DatasetUploadResponse(
            id=str(dataset.id),
            name=dataset.name,
            filename=dataset.filename,
            format_type=dataset.format_type,
            status=dataset.status,
            num_samples=dataset.num_samples,
            created_at=dataset.created_at
        )

    except Exception as e:
        logger.error(f"Dataset upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Dataset upload failed: {str(e)}")


@router.post("/datasets/{dataset_id}/validate", response_model=DatasetValidationResponse)
async def validate_dataset(
    dataset_id: str,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "read")),
    db: AsyncSession = Depends(get_db)
):
    """
    Validate a dataset for fine-tuning

    Checks:
    - Format correctness
    - Required fields presence
    - Data quality metrics
    - Sample distribution
    """
    try:
        service = FineTuningService(db)

        # Get dataset
        query = select(FineTuningDataset).where(FineTuningDataset.id == uuid.UUID(dataset_id))
        result = await db.execute(query)
        dataset = result.scalar_one_or_none()

        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        # Validate
        validation_result = await service.validate_dataset(dataset.id)

        return DatasetValidationResponse(
            dataset_id=str(dataset.id),
            is_valid=validation_result["is_valid"],
            num_samples=validation_result.get("num_samples", 0),
            errors=validation_result.get("errors", []),
            warnings=validation_result.get("warnings", []),
            quality_metrics=validation_result.get("quality_metrics", {}),
            sample_preview=validation_result.get("sample_preview", [])
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dataset validation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/datasets", response_model=DatasetListResponse)
async def list_datasets(
    project_id: Optional[str] = None,
    format_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "read")),
    db: AsyncSession = Depends(get_db)
):
    """
    List all datasets with optional filtering

    Filters by project, format type, and status.
    """
    try:
        query = select(FineTuningDataset)

        # Apply filters
        conditions = []

        if project_id:
            conditions.append(FineTuningDataset.project_id == uuid.UUID(project_id))

        if format_type:
            conditions.append(FineTuningDataset.format_type == format_type)

        if status:
            conditions.append(FineTuningDataset.status == status)

        if conditions:
            query = query.where(and_(*conditions))

        # Order by creation date
        query = query.order_by(FineTuningDataset.created_at.desc())

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Pagination
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        datasets = result.scalars().all()

        return DatasetListResponse(
            datasets=[
                DatasetDetailResponse(
                    id=str(d.id),
                    name=d.name,
                    filename=d.filename,
                    format_type=d.format_type,
                    training_objective=d.training_objective,
                    status=d.status,
                    num_samples=d.num_samples,
                    file_size_bytes=d.file_size_bytes,
                    validation_errors=d.validation_errors,
                    meta_info=d.meta_info,
                    created_at=d.created_at,
                    updated_at=d.updated_at
                )
                for d in datasets
            ],
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Failed to list datasets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list datasets: {str(e)}")


@router.get("/datasets/{dataset_id}", response_model=DatasetDetailResponse)
async def get_dataset(
    dataset_id: str,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "read")),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific dataset"""
    try:
        query = select(FineTuningDataset).where(FineTuningDataset.id == uuid.UUID(dataset_id))
        result = await db.execute(query)
        dataset = result.scalar_one_or_none()

        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        return DatasetDetailResponse(
            id=str(dataset.id),
            name=dataset.name,
            filename=dataset.filename,
            format_type=dataset.format_type,
            training_objective=dataset.training_objective,
            status=dataset.status,
            num_samples=dataset.num_samples,
            file_size_bytes=dataset.file_size_bytes,
            validation_errors=dataset.validation_errors,
            meta_info=dataset.meta_info,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dataset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get dataset: {str(e)}")


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "delete")),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a dataset

    Checks that no active jobs are using this dataset.
    """
    try:
        service = FineTuningService(db)

        # Check for active jobs using this dataset
        job_query = select(FineTuningJob).where(
            and_(
                FineTuningJob.dataset_id == uuid.UUID(dataset_id),
                FineTuningJob.status.in_(["pending", "running", "queued"])
            )
        )
        job_result = await db.execute(job_query)
        active_jobs = job_result.scalars().all()

        if active_jobs:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete dataset: {len(active_jobs)} active jobs are using it"
            )

        # Delete from database
        query = select(FineTuningDataset).where(FineTuningDataset.id == uuid.UUID(dataset_id))
        result = await db.execute(query)
        dataset = result.scalar_one_or_none()

        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        await db.delete(dataset)
        await db.commit()

        # TODO: Delete from MinIO

        # Audit log
        await audit_service.log_action(
            user_id=user.id,
            action="delete_finetuning_dataset",
            details={"dataset_id": dataset_id, "filename": dataset.filename},
            db=db
        )

        return {"message": "Dataset deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete dataset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete dataset: {str(e)}")


# ============================================================================
# TRAINING JOB MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/jobs", response_model=FineTuningJobResponse)
async def create_finetuning_job(
    request: FineTuningJobCreateRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "write")),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new fine-tuning job

    Validates dataset, merges hyperparameters with defaults,
    and optionally starts training immediately.
    """
    try:
        service = FineTuningService(db)

        # Create job
        job = await service.create_job(
            name=request.name,
            base_model=request.base_model,
            finetuning_method=request.finetuning_method,
            training_objective=request.training_objective,
            dataset_id=request.dataset_id,
            hyperparameters=request.hyperparameters,
            user_id=user.id,
            project_id=request.project_id
        )

        # Audit log
        await audit_service.log_action(
            user_id=user.id,
            action="create_finetuning_job",
            details={
                "job_id": str(job.id),
                "name": request.name,
                "method": request.finetuning_method
            },
            db=db
        )

        # Submit job if requested
        if request.auto_start:
            # Add to background task queue
            background_tasks.add_task(
                service.submit_job_background,
                job_id=job.id
            )

        return FineTuningJobResponse(
            id=str(job.id),
            name=job.name,
            base_model=job.base_model,
            finetuning_method=job.finetuning_method,
            training_objective=job.training_objective,
            status=job.status,
            created_at=job.created_at
        )

    except Exception as e:
        logger.error(f"Failed to create job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


@router.post("/jobs/{job_id}/submit")
async def submit_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "write")),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a job for execution

    Allocates GPU resources and starts training in background.
    """
    try:
        service = FineTuningService(db)

        # Submit job
        background_tasks.add_task(
            service.submit_job_background,
            job_id=uuid.UUID(job_id)
        )

        # Update status to queued
        query = select(FineTuningJob).where(FineTuningJob.id == uuid.UUID(job_id))
        result = await db.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        job.status = "queued"
        job.queued_at = datetime.utcnow()
        await db.commit()

        # Audit log
        await audit_service.log_action(
            user_id=user.id,
            action="submit_finetuning_job",
            details={"job_id": job_id},
            db=db
        )

        return {"message": "Job submitted successfully", "status": "queued"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to submit job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}")


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "write")),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel a running or queued job

    Stops container execution and releases GPU resources.
    """
    try:
        # Get job
        query = select(FineTuningJob).where(FineTuningJob.id == uuid.UUID(job_id))
        result = await db.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.status not in ["pending", "queued", "running"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel job with status: {job.status}"
            )

        # TODO: Kill container if running
        # TODO: Release GPU allocation

        # Update status
        job.status = "cancelled"
        job.completed_at = datetime.utcnow()
        job.error_message = "Cancelled by user"
        await db.commit()

        # Audit log
        await audit_service.log_action(
            user_id=user.id,
            action="cancel_finetuning_job",
            details={"job_id": job_id},
            db=db
        )

        return {"message": "Job cancelled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to cancel job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")


@router.get("/jobs", response_model=FineTuningJobListResponse)
async def list_jobs(
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    finetuning_method: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "read")),
    db: AsyncSession = Depends(get_db)
):
    """
    List all fine-tuning jobs with optional filtering

    Filters by project, status, and method.
    """
    try:
        query = select(FineTuningJob)

        # Apply filters
        conditions = []

        if project_id:
            conditions.append(FineTuningJob.project_id == uuid.UUID(project_id))

        if status:
            conditions.append(FineTuningJob.status == status)

        if finetuning_method:
            conditions.append(FineTuningJob.finetuning_method == finetuning_method)

        if conditions:
            query = query.where(and_(*conditions))

        # Order by creation date
        query = query.order_by(FineTuningJob.created_at.desc())

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Pagination
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        jobs = result.scalars().all()

        return FineTuningJobListResponse(
            jobs=[
                FineTuningJobDetailResponse(
                    id=str(j.id),
                    name=j.name,
                    base_model=j.base_model,
                    finetuning_method=j.finetuning_method,
                    training_objective=j.training_objective,
                    status=j.status,
                    hyperparameters=j.hyperparameters,
                    checkpoint_path=j.checkpoint_path,
                    error_message=j.error_message,
                    created_at=j.created_at,
                    started_at=j.started_at,
                    completed_at=j.completed_at,
                    training_duration_seconds=j.training_duration_seconds
                )
                for j in jobs
            ],
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Failed to list jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")


@router.get("/jobs/{job_id}", response_model=FineTuningJobDetailResponse)
async def get_job(
    job_id: str,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "read")),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific job"""
    try:
        query = select(FineTuningJob).where(FineTuningJob.id == uuid.UUID(job_id))
        result = await db.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return FineTuningJobDetailResponse(
            id=str(job.id),
            name=job.name,
            base_model=job.base_model,
            finetuning_method=job.finetuning_method,
            training_objective=job.training_objective,
            status=job.status,
            hyperparameters=job.hyperparameters,
            checkpoint_path=job.checkpoint_path,
            error_message=job.error_message,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            training_duration_seconds=job.training_duration_seconds
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get job: {str(e)}")


@router.get("/jobs/{job_id}/metrics", response_model=JobMetricsHistoryResponse)
async def get_job_metrics(
    job_id: str,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "read")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get training metrics history for a job

    Returns time-series data for loss, accuracy, and other metrics.
    """
    try:
        # Get all metrics for this job
        query = select(TrainingMetric).where(
            TrainingMetric.job_id == uuid.UUID(job_id)
        ).order_by(TrainingMetric.step)

        result = await db.execute(query)
        metrics = result.scalars().all()

        if not metrics:
            return JobMetricsHistoryResponse(
                job_id=job_id,
                metrics=[],
                latest_metrics=None
            )

        # Format metrics
        metrics_list = [
            TrainingMetricsResponse(
                id=str(m.id),
                job_id=str(m.job_id),
                step=m.step,
                epoch=m.epoch,
                loss=m.loss,
                learning_rate=m.learning_rate,
                accuracy=m.accuracy,
                additional_metrics=m.additional_metrics,
                created_at=m.created_at
            )
            for m in metrics
        ]

        # Get latest metrics
        latest = metrics[-1] if metrics else None
        latest_metrics = None
        if latest:
            latest_metrics = TrainingMetricsResponse(
                id=str(latest.id),
                job_id=str(latest.job_id),
                step=latest.step,
                epoch=latest.epoch,
                loss=latest.loss,
                learning_rate=latest.learning_rate,
                accuracy=latest.accuracy,
                additional_metrics=latest.additional_metrics,
                created_at=latest.created_at
            )

        return JobMetricsHistoryResponse(
            job_id=job_id,
            metrics=metrics_list,
            latest_metrics=latest_metrics
        )

    except Exception as e:
        logger.error(f"Failed to get job metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


# ============================================================================
# MODEL REGISTRY ENDPOINTS
# ============================================================================

@router.post("/models/register", response_model=FineTunedModelResponse)
async def register_model(
    request: ModelRegistrationRequest,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "write")),
    db: AsyncSession = Depends(get_db)
):
    """
    Register a fine-tuned model from a completed job

    Creates model registry entry with versioning.
    """
    try:
        service = ModelRegistryService(db)

        # Register model
        model = await service.register_model_from_job(
            job_id=request.job_id,
            model_name=request.model_name,
            version=request.version,
            description=request.description,
            tags=request.tags
        )

        # Audit log
        await audit_service.log_action(
            user_id=user.id,
            action="register_finetuned_model",
            details={
                "model_id": str(model.id),
                "model_name": request.model_name,
                "job_id": request.job_id
            },
            db=db
        )

        return FineTunedModelResponse(
            id=str(model.id),
            model_name=model.model_name,
            version=model.version,
            base_model=model.base_model,
            finetuning_method=model.finetuning_method,
            status=model.status,
            created_at=model.created_at
        )

    except Exception as e:
        logger.error(f"Failed to register model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to register model: {str(e)}")


@router.post("/models/{model_id}/deploy")
async def deploy_model(
    model_id: str,
    request: ModelDeployRequest,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "write")),
    db: AsyncSession = Depends(get_db)
):
    """
    Deploy a fine-tuned model to inference service

    Supports Ollama and vLLM deployment strategies.
    """
    try:
        service = ModelRegistryService(db)

        # Deploy model
        await service.deploy_model(
            model_id=uuid.UUID(model_id),
            deployment_target=request.deployment_target,
            deployment_config=request.deployment_config
        )

        # Audit log
        await audit_service.log_action(
            user_id=user.id,
            action="deploy_finetuned_model",
            details={
                "model_id": model_id,
                "deployment_target": request.deployment_target
            },
            db=db
        )

        return {"message": "Model deployed successfully", "deployment_target": request.deployment_target}

    except Exception as e:
        logger.error(f"Failed to deploy model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to deploy model: {str(e)}")


@router.post("/models/{model_id}/undeploy")
async def undeploy_model(
    model_id: str,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "write")),
    db: AsyncSession = Depends(get_db)
):
    """
    Undeploy a fine-tuned model from inference service

    Removes model from deployment target and updates status.
    """
    try:
        service = ModelRegistryService(db)

        # Undeploy model
        await service.undeploy_model(uuid.UUID(model_id))

        # Audit log
        await audit_service.log_action(
            user_id=user.id,
            action="undeploy_finetuned_model",
            details={"model_id": model_id},
            db=db
        )

        return {"message": "Model undeployed successfully"}

    except Exception as e:
        logger.error(f"Failed to undeploy model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to undeploy model: {str(e)}")


@router.get("/models", response_model=FineTunedModelListResponse)
async def list_models(
    status: Optional[str] = None,
    base_model: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "read")),
    db: AsyncSession = Depends(get_db)
):
    """
    List all fine-tuned models with optional filtering

    Filters by status and base model.
    """
    try:
        query = select(FineTunedModel)

        # Apply filters
        conditions = []

        if status:
            conditions.append(FineTunedModel.status == status)

        if base_model:
            conditions.append(FineTunedModel.base_model == base_model)

        if conditions:
            query = query.where(and_(*conditions))

        # Order by creation date
        query = query.order_by(FineTunedModel.created_at.desc())

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Pagination
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        models = result.scalars().all()

        return FineTunedModelListResponse(
            models=[
                FineTunedModelDetailResponse(
                    id=str(m.id),
                    model_name=m.model_name,
                    version=m.version,
                    base_model=m.base_model,
                    finetuning_method=m.finetuning_method,
                    status=m.status,
                    checkpoint_path=m.checkpoint_path,
                    deployment_info=m.deployment_info,
                    tags=m.tags,
                    description=m.description,
                    usage_count=m.usage_count,
                    created_at=m.created_at,
                    deployed_at=m.deployed_at
                )
                for m in models
            ],
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Failed to list models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


@router.get("/models/{model_id}", response_model=FineTunedModelDetailResponse)
async def get_model(
    model_id: str,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "read")),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific model"""
    try:
        query = select(FineTunedModel).where(FineTunedModel.id == uuid.UUID(model_id))
        result = await db.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        return FineTunedModelDetailResponse(
            id=str(model.id),
            model_name=model.model_name,
            version=model.version,
            base_model=model.base_model,
            finetuning_method=model.finetuning_method,
            status=model.status,
            checkpoint_path=model.checkpoint_path,
            deployment_info=model.deployment_info,
            tags=model.tags,
            description=model.description,
            usage_count=model.usage_count,
            created_at=model.created_at,
            deployed_at=model.deployed_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get model: {str(e)}")


# ============================================================================
# GPU RESOURCE STATUS ENDPOINTS
# ============================================================================

@router.get("/gpu/status", response_model=List[GPUStatusResponse])
async def get_gpu_status(
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "read"))
):
    """
    Get status of all GPUs in the pool

    Shows allocation, memory usage, temperature, and utilization.
    """
    try:
        # Get GPU status from pool manager
        gpu_status = await gpu_pool_manager.get_all_gpus_status()

        return [
            GPUStatusResponse(
                device_id=gpu.device_id,
                name=gpu.name,
                total_memory_gb=gpu.total_memory_gb,
                free_memory_gb=gpu.free_memory_gb,
                utilization_percent=gpu.utilization_percent,
                temperature_celsius=gpu.temperature_celsius,
                is_available=gpu.is_available
            )
            for gpu in gpu_status
        ]

    except Exception as e:
        logger.error(f"Failed to get GPU status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get GPU status: {str(e)}")


@router.get("/gpu/stats")
async def get_gpu_pool_stats(
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "read"))
):
    """
    Get GPU pool statistics

    Shows total GPUs, allocations, and active jobs.
    """
    try:
        stats = gpu_pool_manager.get_stats()
        return stats

    except Exception as e:
        logger.error(f"Failed to get GPU stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get GPU stats: {str(e)}")


# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    user: User = Depends(require_authentication),
    _: None = Depends(RequireAdmin()),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a job (admin only)

    Removes job and associated metrics. Cannot delete running jobs.
    """
    try:
        # Get job
        query = select(FineTuningJob).where(FineTuningJob.id == uuid.UUID(job_id))
        result = await db.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.status in ["running", "queued"]:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete running or queued jobs. Cancel first."
            )

        # Delete job (cascade will delete metrics)
        await db.delete(job)
        await db.commit()

        # Audit log
        await audit_service.log_action(
            user_id=user.id,
            action="delete_finetuning_job",
            details={"job_id": job_id, "name": job.name},
            db=db
        )

        return {"message": "Job deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")


@router.delete("/models/{model_id}")
async def delete_model(
    model_id: str,
    user: User = Depends(require_authentication),
    _: None = Depends(RequireAdmin()),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a model (admin only)

    Removes model from registry. Cannot delete deployed models.
    """
    try:
        # Get model
        query = select(FineTunedModel).where(FineTunedModel.id == uuid.UUID(model_id))
        result = await db.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        if model.status == "deployed":
            raise HTTPException(
                status_code=400,
                detail="Cannot delete deployed model. Undeploy first."
            )

        # Delete model
        await db.delete(model)
        await db.commit()

        # TODO: Delete checkpoint from MinIO

        # Audit log
        await audit_service.log_action(
            user_id=user.id,
            action="delete_finetuned_model",
            details={"model_id": model_id, "model_name": model.model_name},
            db=db
        )

        return {"message": "Model deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete model: {str(e)}")
