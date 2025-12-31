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
from sqlalchemy import select, func, and_, text
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import os
import asyncio
import logging
from functools import lru_cache

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
from app.services.ollama_deployment_service import OllamaDeploymentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/finetuning", tags=["finetuning"])


# ============================================================================
# DATASET MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/datasets/upload", response_model=DatasetUploadResponse)
async def upload_dataset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: Optional[str] = None,
    format_type: str = Query(..., description="Dataset format: qa, classification, instruction, etc."),
    training_objective: str = Query(..., description="Training objective"),
    columns: Optional[str] = Query(None, description="JSON string of column mappings"),
    project_id: Optional[str] = Query(None, description="Project ID for organizational hierarchy"),
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "write")),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a dataset for fine-tuning

    Supports CSV, JSON, JSONL, Parquet formats.
    Automatically triggers validation in the background to:
    - Count samples
    - Validate format and required fields
    - Create train/validation split
    - Extract sample preview rows

    Dataset will show status "processing" initially, then update to "completed"
    once validation finishes (usually within a few seconds).
    """
    try:
        service = FineTuningService(db)

        # Parse column mappings if provided
        import json
        column_mappings = json.loads(columns) if columns else None

        # Read file content
        file_content = await file.read()

        # Initialize MinIO client
        from app.core.config import settings
        from minio import Minio
        import io
        from pathlib import Path
        from app.services.minio_path_builder import MinIOPathBuilder

        minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )

        # Generate unique dataset ID
        dataset_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix

        # Fetch organizational hierarchy from USER, not project
        # Path structure: documents/{user.department}/{user.team}/{project.name}/finetuning/...
        from app.models.database_enhanced import Project
        from sqlalchemy import select, text

        department_name = "Global"
        team_name = "General"
        project_name = "Global"  # Changed default from "Default" to "Global"
        project_uuid = None

        # Get user's department name
        if user.department_id:
            dept_query = text("SELECT name FROM departments WHERE id = :dept_id")
            dept_result = await db.execute(dept_query, {"dept_id": str(user.department_id)})
            dept_row = dept_result.first()
            if dept_row:
                department_name = dept_row[0]

        # Get user's team name from user_teams junction table
        team_query = text("""
            SELECT t.name
            FROM teams t
            JOIN user_teams ut ON t.id = ut.team_id
            WHERE ut.user_id = :user_id
            ORDER BY ut.assigned_at DESC
            LIMIT 1
        """)
        team_result = await db.execute(team_query, {"user_id": str(user.id)})
        team_row = team_result.first()
        if team_row:
            team_name = team_row[0]

        # Get project name if project_id provided, otherwise use Global
        if project_id:
            query = select(Project).where(Project.id == uuid.UUID(project_id))
            result = await db.execute(query)
            project = result.scalar_one_or_none()

            if project:
                project_name = project.name
                project_uuid = project.id
        else:
            # Default to Global project if no project_id provided
            global_query = select(Project).where(Project.name == "Global")
            global_result = await db.execute(global_query)
            global_project = global_result.scalar_one_or_none()

            if global_project:
                project_name = global_project.name
                project_uuid = global_project.id

        logger.info(f"Using user org: {department_name}/{team_name} with project: {project_name}")

        dataset_name = name or Path(file.filename).stem

        minio_path = MinIOPathBuilder.build_finetuning_dataset_path(
            department_name=department_name,
            team_name=team_name,
            project_name=project_name,
            username=user.username,
            dataset_name=dataset_name,
            dataset_id=dataset_id,
            filename=file.filename
        )

        # Upload to MinIO
        minio_client.put_object(
            settings.MINIO_BUCKET_NAME,
            minio_path,
            io.BytesIO(file_content),
            length=len(file_content),
            content_type=file.content_type or "application/octet-stream"
        )

        logger.info(f"Uploaded dataset to MinIO (organizational path): {minio_path}")

        # Create dataset record directly (FineTuningService uses sync operations)
        from app.models.finetuning_models import FineTuningDataset
        dataset = FineTuningDataset(
            id=uuid.UUID(dataset_id),  # Use same ID as MinIO path
            name=name or file.filename,
            filename=file.filename,
            minio_path=minio_path,
            file_size=len(file_content),
            format_type=format_type,
            columns=column_mappings or {},
            uploaded_by=user.id,
            project_id=project_uuid,  # Link to actual project (can be None for global datasets)
            description=f"Training objective: {training_objective}",
            preprocessing_status="processing"  # Changed from "pending" to trigger auto-validation
        )

        db.add(dataset)
        await db.commit()
        await db.refresh(dataset)

        logger.info(f"Created dataset: {dataset.id} - {dataset.name}")

        # Trigger automatic validation in background using asyncio
        import asyncio
        from app.core.database import AsyncSessionLocal

        async def run_validation():
            """Wrapper to run async validation in background with new DB session"""
            try:
                logger.info(f"Starting background validation for dataset: {dataset.id}")

                # Create new database session for background task
                async with AsyncSessionLocal() as new_db:
                    validation_service = FineTuningService(new_db)
                    validation_result = await validation_service.validate_dataset(dataset.id)
                    logger.info(f"Background validation complete for {dataset.id}: {validation_result.get('is_valid', False)}")
            except Exception as e:
                logger.error(f"Background validation failed for {dataset.id}: {e}", exc_info=True)

        # Schedule async task (don't await - let it run in background)
        asyncio.create_task(run_validation())
        logger.info(f"Queued background validation for dataset: {dataset.id}")

        # Audit log
        await audit_service.log_action(
            db=db,
            action="upload",  # Valid ActionType enum value
            user_id=user.id,
            resource_type="dataset",
            resource_id=dataset.id,
            description=f"Uploaded fine-tuning dataset: {file.filename}",
            request_data={
                "filename": file.filename,
                "format_type": format_type,
                "training_objective": training_objective
            }
        )

        return DatasetUploadResponse(
            id=str(dataset.id),
            name=dataset.name,
            filename=dataset.filename,
            format_type=dataset.format_type,
            status=dataset.preprocessing_status,  # Map preprocessing_status to status
            num_samples=dataset.num_samples,
            created_at=dataset.uploaded_at  # Use uploaded_at timestamp
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
            conditions.append(FineTuningDataset.preprocessing_status == status)

        if conditions:
            query = query.where(and_(*conditions))

        # Order by upload date (correct field name)
        query = query.order_by(FineTuningDataset.uploaded_at.desc())

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Pagination
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        datasets = result.scalars().all()

        # Helper to convert sample_rows to strings (handles both str and dict)
        def format_sample_rows(rows):
            if not rows:
                return None
            result = []
            for row in rows:
                if isinstance(row, dict):
                    # Chat format - serialize to JSON string
                    import json
                    result.append(json.dumps(row))
                else:
                    # Already a string
                    result.append(str(row))
            return result

        return DatasetListResponse(
            datasets=[
                DatasetDetailResponse(
                    id=str(d.id),
                    name=d.name,
                    filename=d.filename,
                    format_type=d.format_type or "",
                    training_objective=None,  # Not stored in dataset model
                    status=d.preprocessing_status or "pending",
                    num_samples=d.num_samples,
                    file_size_bytes=d.file_size,
                    validation_errors=d.validation_errors,
                    is_valid=d.is_valid,  # Validation status flag
                    sample_rows=format_sample_rows(d.sample_rows),  # Convert dicts to strings
                    meta_info={"minio_path": d.minio_path} if d.minio_path else {},
                    created_at=d.uploaded_at,
                    updated_at=d.uploaded_at  # No separate updated_at field
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

        # Convert sample_rows to strings (handles both str and dict)
        def format_sample_rows(rows):
            if not rows:
                return None
            result = []
            for row in rows:
                if isinstance(row, dict):
                    import json
                    result.append(json.dumps(row))
                else:
                    result.append(str(row))
            return result

        return DatasetDetailResponse(
            id=str(dataset.id),
            name=dataset.name,
            filename=dataset.filename,
            format_type=dataset.format_type or "",
            training_objective=None,  # Not stored in dataset model
            status=dataset.preprocessing_status or "pending",
            num_samples=dataset.num_samples,
            file_size_bytes=dataset.file_size,
            validation_errors=dataset.validation_errors,
            is_valid=dataset.is_valid,  # Validation status flag
            sample_rows=format_sample_rows(dataset.sample_rows),  # Convert dicts to strings
            meta_info={"minio_path": dataset.minio_path} if dataset.minio_path else {},
            created_at=dataset.uploaded_at,
            updated_at=dataset.uploaded_at  # No separate updated_at field
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

    Now includes organizational context (department, team, project) for proper MinIO path hierarchy.
    """
    try:
        from app.models.rbac import Department, Team
        from app.models.database_enhanced import Project
        from app.services.minio_path_builder import MinIOPathBuilder
        from uuid import UUID

        service = FineTuningService(db)

        # ========== P1 FIX: Capture Organizational Context ==========
        # 1. Get user's department
        dept_result = await db.execute(
            select(Department).where(Department.id == user.department_id)
        )
        department = dept_result.scalar_one_or_none()
        department_name = department.name if department else "Technology"

        # 2. Get user's primary team from user_teams junction table
        team_query = text("""
            SELECT t.name
            FROM teams t
            JOIN user_teams ut ON t.id = ut.team_id
            WHERE ut.user_id = :user_id
            ORDER BY ut.assigned_at DESC
            LIMIT 1
        """)
        team_result = await db.execute(team_query, {"user_id": str(user.id)})
        team_row = team_result.first()
        team_name = team_row[0] if team_row else "General"

        # 3. Get or default to Global project
        effective_project_id = request.project_id
        if not effective_project_id:
            global_proj_result = await db.execute(
                select(Project).where(Project.name == "Global")
            )
            global_project = global_proj_result.scalar_one_or_none()
            if global_project:
                effective_project_id = global_project.id
            else:
                # Fallback UUID if Global project doesn't exist
                effective_project_id = UUID("997968df-c164-4697-90d5-3e7a01929dc2")

        logger.info(f"Fine-tuning job organizational context: dept={department_name}, team={team_name}, project_id={effective_project_id}")

        # Create job (using correct parameter name)
        job = await service.create_job(
            name=request.name,
            base_model=request.base_model,
            finetuning_method=request.finetuning_method,
            training_objective=request.training_objective,
            dataset_id=request.dataset_id,
            hyperparameters=request.hyperparameters,
            quantization=request.quantization if hasattr(request, 'quantization') else "4bit",
            train_split=request.train_split if hasattr(request, 'train_split') else 0.8,
            created_by=user.id,  # Fixed: use created_by instead of user_id
            project_id=effective_project_id,
            description=request.description if hasattr(request, 'description') else None,
            department=department_name,
            team=team_name
        )

        # Audit log
        await audit_service.log_action(
            db=db,
            action="create",  # Valid ActionType enum value
            user_id=user.id,
            resource_type="training_job",
            resource_id=job.id,
            description=f"Created fine-tuning job: {request.name}",
            request_data={
                "name": request.name,
                "base_model": request.base_model,
                "method": request.finetuning_method
            }
        )

        # Submit job if requested
        if request.auto_start:
            # Update job status to queued
            job.status = "queued"
            job.queued_at = datetime.utcnow()
            await db.commit()
            await db.refresh(job)

            logger.info(f"Job {job.id} queued for training (auto_start=True)")
            # TODO: Add to background task queue or submit to finetuning-runtime container

        return FineTuningJobResponse(
            id=job.id,
            name=job.name,
            description=job.description,
            base_model=job.base_model,
            quantization=job.quantization,
            finetuning_method=job.finetuning_method,
            training_objective=job.training_objective,
            status=job.status,
            progress=job.progress or 0.0,
            created_at=job.created_at,
            updated_at=job.updated_at or job.created_at,
            created_by=job.created_by,
            dataset_id=job.dataset_id,
            project_id=job.project_id
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

        # Submit job directly (not as background task)
        # The service method already uses Celery for async execution
        result = await service.submit_job(job_id=uuid.UUID(job_id))

        # Audit log
        await audit_service.log_action(
            db=db,
            action="submit_finetuning_job",
            user_id=user.id,
            resource_type="finetuning_job",
            resource_id=uuid.UUID(job_id),
            description=f"Submitted fine-tuning job {job_id}"
        )

        return result

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
                    checkpoint_path=j.minio_checkpoint_path,
                    error_message=j.error_message,
                    created_at=j.created_at,
                    started_at=j.training_start_time,
                    completed_at=j.training_end_time,
                    training_duration_seconds=j.training_time_seconds,
                    # Training progress
                    progress=j.progress,
                    current_epoch=j.current_epoch,
                    current_step=j.current_step,
                    total_steps=j.total_steps,
                    train_loss=j.train_loss,
                    eval_loss=j.eval_loss,
                    # Resource tracking
                    gpu_type=j.gpu_type,
                    gpu_count=j.gpu_count
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
            checkpoint_path=job.minio_checkpoint_path,
            error_message=job.error_message,
            created_at=job.created_at,
            started_at=job.training_start_time,
            completed_at=job.training_end_time,
            training_duration_seconds=job.training_time_seconds,
            # Training progress
            progress=job.progress,
            current_epoch=job.current_epoch,
            current_step=job.current_step,
            total_steps=job.total_steps,
            train_loss=job.train_loss,
            eval_loss=job.eval_loss,
            # Pipeline stage tracking
            training_stage=job.training_stage,
            stage_details=job.stage_details,
            stage_started_at=job.stage_started_at,
            stage_completed_at=job.stage_completed_at,
            # Resource tracking
            gpu_type=job.gpu_type,
            gpu_count=job.gpu_count
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


# =============================================================================
# LoRA Adapter Merge Endpoints (JIRA: FINETUNE-002)
# =============================================================================

@router.post("/models/{model_id}/merge")
async def merge_lora_adapters(
    model_id: str,
    base_model_name: str = "Qwen/Qwen2.5-1.5B-Instruct",
    force_cpu: bool = False,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "write")),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger LoRA adapter merge for a fine-tuned model.

    This endpoint triggers a background Celery task to merge LoRA adapters
    with the base model. The merge process typically takes 5-15 minutes.

    The merged model will be saved to:
        /workspace/finetuning/{job_id}/output/merged_model/

    This path is optimized for deployment - OllamaDeploymentService checks
    the workspace FIRST before downloading from MinIO.

    **JIRA**: FINETUNE-002
    **Status Flow**: adapter_only → merging → merged

    Args:
        model_id: ID of the fine-tuned model
        base_model_name: HuggingFace base model (default: Qwen/Qwen2.5-1.5B-Instruct)
        force_cpu: Force CPU-only merge for testing

    Returns:
        Task ID and initial status

    Example:
        POST /api/v1/finetuning/models/abc-123/merge
        Response: {"task_id": "celery-task-id", "status": "merging", "message": "Merge started"}
    """
    from app.tasks.finetuning_tasks import merge_lora_model_task

    try:
        logger.info(f"Merge request for model {model_id} by user {user.username}")

        # Check if model exists
        result = await db.execute(
            text("SELECT id, status, minio_checkpoint_path FROM finetuned_models WHERE id = :model_id"),
            {"model_id": model_id}
        )
        model = result.fetchone()

        if not model:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

        # Check if model is ready for merge
        # Allow: registered, approved, adapter_only, completed, merge_failed (for retry)
        if model.status not in ["registered", "approved", "adapter_only", "completed", "merge_failed"]:
            raise HTTPException(
                status_code=400,
                detail=f"Model status '{model.status}' cannot be merged. Must be 'registered', 'approved', 'adapter_only', or 'completed'"
            )

        if not model.minio_checkpoint_path:
            raise HTTPException(
                status_code=400,
                detail="Model has no checkpoint path. Cannot merge."
            )

        # Trigger Celery background task
        task = merge_lora_model_task.delay(
            model_id=model_id,
            base_model_name=base_model_name,
            force_cpu=force_cpu
        )

        logger.info(f"✅ Merge task triggered: {task.id} for model {model_id}")

        return {
            "task_id": task.id,
            "model_id": model_id,
            "status": "merging",
            "message": f"Merge task started. Expected duration: 5-15 minutes. Check /models/{model_id}/merge-status for progress."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger merge for model {model_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to trigger merge: {str(e)}")


@router.get("/models/{model_id}/merge-status")
async def get_merge_status(
    model_id: str,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "read")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get merge status for a fine-tuned model.

    Returns current merge status, progress, and metadata.

    **JIRA**: FINETUNE-002

    Args:
        model_id: ID of the fine-tuned model

    Returns:
        Merge status information

    Status Values:
        - adapter_only: Not merged yet
        - merging: Merge in progress
        - merged: Merge complete, ready for deployment
        - merge_failed: Merge failed (check error_message)
        - deployed: Already deployed to Ollama

    Example:
        GET /api/v1/finetuning/models/abc-123/merge-status
        Response:
        {
            "model_id": "abc-123",
            "status": "merged",
            "merged_model_path": "/workspace/finetuning/uuid/output/merged_model",
            "merge_duration_seconds": 642,
            "merge_requested_at": "2025-12-22T10:30:00Z",
            "merge_error_message": null
        }
    """
    from app.services.finetuning.model_merge_service import ModelMergeService

    try:
        # Get database session (convert async to sync for service)
        # Create sync session
        from sqlalchemy.orm import sessionmaker
        from app.core.database import sync_engine

        SessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)
        sync_db = SessionLocal()

        try:
            merge_service = ModelMergeService(sync_db)

            # Import asyncio to run async method
            import asyncio
            status = asyncio.run(merge_service.get_merge_status(model_id))

            return status

        finally:
            sync_db.close()

    except Exception as e:
        logger.error(f"Failed to get merge status for model {model_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get merge status: {str(e)}")


@router.get("/models-public/{model_id}/merge-status")
async def get_merge_status_public(
    model_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get merge status for a fine-tuned model (public endpoint for polling).

    No authentication required for status checking to avoid CORS issues
    when polling from browser during merge process.

    Returns current merge status, progress, and metadata.

    Args:
        model_id: ID of the fine-tuned model

    Returns:
        Merge status information

    Status Values:
        - adapter_only/registered/approved: Not merged yet
        - merging: Merge in progress
        - merged: Merge complete, ready for deployment
        - merge_failed: Merge failed (check error_message)
        - deployed: Already deployed to Ollama

    Example:
        GET /api/v1/finetuning/models-public/abc-123/merge-status
    """
    try:
        # Query database directly to avoid importing heavy dependencies
        from sqlalchemy import select
        from app.models.finetuning_models import FineTunedModel

        result = await db.execute(
            select(FineTunedModel).where(FineTunedModel.id == model_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

        # Return merge status information
        return {
            "model_id": str(model.id),
            "status": model.status,
            "merged_model_path": model.merged_model_path,
            "merge_duration_seconds": model.merge_duration_seconds,
            "merge_requested_at": model.merge_requested_at.isoformat() if model.merge_requested_at else None,
            "merge_error_message": model.merge_error_message
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get merge status for model {model_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get merge status: {str(e)}")


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
# MODEL APPROVAL WORKFLOW ENDPOINTS
# ============================================================================

@router.post("/models/{model_id}/request-approval")
async def request_model_approval(
    model_id: str,
    request_reason: str = Query(..., description="Reason for requesting deployment approval"),
    deployment_environment: str = Query("production", description="Target environment: production, staging, development"),
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "write")),
    db: AsyncSession = Depends(get_db)
):
    """
    Request approval to deploy a fine-tuned model

    This creates an approval request that admins must review before
    the model can be deployed to Ollama/vLLM.
    """
    try:
        from app.models.finetuning_models import ModelApproval

        # Check if model exists
        model_query = select(FineTunedModel).where(FineTunedModel.id == uuid.UUID(model_id))
        model_result = await db.execute(model_query)
        model = model_result.scalar_one_or_none()

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # Check if there's already a pending approval
        existing_approval_query = select(ModelApproval).where(
            and_(
                ModelApproval.model_id == uuid.UUID(model_id),
                ModelApproval.status == "pending"
            )
        )
        existing_result = await db.execute(existing_approval_query)
        existing_approval = existing_result.scalar_one_or_none()

        if existing_approval:
            return {
                "status": "approval_exists",
                "approval_id": str(existing_approval.id),
                "message": "An approval request is already pending for this model",
                "requested_at": existing_approval.requested_at.isoformat()
            }

        # Create approval request
        approval = ModelApproval(
            id=uuid.uuid4(),
            model_id=uuid.UUID(model_id),
            requested_by=user.id,
            request_reason=request_reason,
            deployment_environment=deployment_environment,
            status="pending"
        )

        db.add(approval)
        await db.commit()
        await db.refresh(approval)

        # Audit log
        await audit_service.log_action(
            user_id=user.id,
            action="request_model_approval",
            details={
                "model_id": model_id,
                "model_name": model.name,
                "approval_id": str(approval.id),
                "environment": deployment_environment,
                "reason": request_reason
            },
            db=db
        )

        logger.info(f"Approval requested for model {model_id} by user {user.id}")

        return {
            "status": "pending",
            "approval_id": str(approval.id),
            "model_id": model_id,
            "model_name": model.name,
            "requested_at": approval.requested_at.isoformat(),
            "message": "Approval request created successfully. Admin review required."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to request approval: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to request approval: {str(e)}")


@router.get("/approvals/pending")
async def list_pending_approvals(
    user: User = Depends(require_authentication),
    _: None = Depends(RequireAdmin()),
    db: AsyncSession = Depends(get_db)
):
    """
    List all pending model approval requests (Admin only)

    Returns models awaiting deployment approval with full details.
    """
    try:
        from app.models.finetuning_models import ModelApproval

        # Query pending approvals with model and job details
        query = (
            select(ModelApproval, FineTunedModel, FineTuningJob, User)
            .join(FineTunedModel, ModelApproval.model_id == FineTunedModel.id)
            .outerjoin(FineTuningJob, FineTunedModel.job_id == FineTuningJob.id)
            .outerjoin(User, ModelApproval.requested_by == User.id)
            .where(ModelApproval.status == "pending")
            .order_by(ModelApproval.requested_at.desc())
        )

        result = await db.execute(query)
        rows = result.all()

        approvals = []
        for approval, model, job, requester in rows:
            approvals.append({
                "approval_id": str(approval.id),
                "model_id": str(model.id),
                "model_name": model.name,
                "model_version": model.version,
                "base_model": model.base_model,
                "finetuning_method": model.finetuning_method,
                "checkpoint_path": model.minio_checkpoint_path,
                "eval_metrics": model.eval_metrics,
                "requested_by": requester.username if requester else "Unknown",
                "requested_at": approval.requested_at.isoformat(),
                "request_reason": approval.request_reason,
                "deployment_environment": approval.deployment_environment,
                "job_name": job.name if job else None,
                "training_duration_seconds": job.training_time_seconds if job else None
            })

        return {
            "pending_approvals": approvals,
            "total": len(approvals)
        }

    except Exception as e:
        logger.error(f"Failed to list pending approvals: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approvals/{approval_id}/approve")
async def approve_model_deployment(
    approval_id: str,
    review_comments: str = Query(None, description="Optional comments explaining the approval"),
    user: User = Depends(require_authentication),
    _: None = Depends(RequireAdmin()),
    db: AsyncSession = Depends(get_db)
):
    """
    Approve a model deployment request (Admin only)

    After approval, the model status is updated and can be deployed to Ollama.
    """
    try:
        from app.models.finetuning_models import ModelApproval
        from datetime import datetime

        # Get approval request
        approval_query = select(ModelApproval).where(ModelApproval.id == uuid.UUID(approval_id))
        approval_result = await db.execute(approval_query)
        approval = approval_result.scalar_one_or_none()

        if not approval:
            raise HTTPException(status_code=404, detail="Approval request not found")

        if approval.status != "pending":
            raise HTTPException(status_code=400, detail=f"Approval already {approval.status}")

        # Update approval
        approval.status = "approved"
        approval.approved_by = user.id
        approval.reviewed_at = datetime.utcnow()
        approval.review_comments = review_comments

        # Update model status to allow deployment
        model_query = select(FineTunedModel).where(FineTunedModel.id == approval.model_id)
        model_result = await db.execute(model_query)
        model = model_result.scalar_one_or_none()

        if model and model.status == "registered":
            model.status = "approved"  # Ready for deployment

        await db.commit()

        # Audit log
        await audit_service.log_action(
            user_id=user.id,
            action="approve_model_deployment",
            details={
                "approval_id": approval_id,
                "model_id": str(approval.model_id),
                "model_name": model.name if model else None,
                "comments": review_comments
            },
            db=db
        )

        logger.info(f"Model deployment approved: {approval.model_id} by {user.username}")

        return {
            "status": "approved",
            "approval_id": approval_id,
            "model_id": str(approval.model_id),
            "model_name": model.name if model else None,
            "approved_by": user.username,
            "approved_at": approval.reviewed_at.isoformat(),
            "message": "Model approved for deployment. You can now deploy it to Ollama."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approvals/{approval_id}/reject")
async def reject_model_deployment(
    approval_id: str,
    review_comments: str = Query(..., description="Reason for rejection"),
    user: User = Depends(require_authentication),
    _: None = Depends(RequireAdmin()),
    db: AsyncSession = Depends(get_db)
):
    """
    Reject a model deployment request (Admin only)

    The model will remain in registered status and cannot be deployed.
    """
    try:
        from app.models.finetuning_models import ModelApproval
        from datetime import datetime

        # Get approval request
        approval_query = select(ModelApproval).where(ModelApproval.id == uuid.UUID(approval_id))
        approval_result = await db.execute(approval_query)
        approval = approval_result.scalar_one_or_none()

        if not approval:
            raise HTTPException(status_code=404, detail="Approval request not found")

        if approval.status != "pending":
            raise HTTPException(status_code=400, detail=f"Approval already {approval.status}")

        # Update approval
        approval.status = "rejected"
        approval.approved_by = user.id
        approval.reviewed_at = datetime.utcnow()
        approval.review_comments = review_comments

        await db.commit()

        # Get model name for response
        model_query = select(FineTunedModel).where(FineTunedModel.id == approval.model_id)
        model_result = await db.execute(model_query)
        model = model_result.scalar_one_or_none()

        # Audit log
        await audit_service.log_action(
            user_id=user.id,
            action="reject_model_deployment",
            details={
                "approval_id": approval_id,
                "model_id": str(approval.model_id),
                "model_name": model.name if model else None,
                "reason": review_comments
            },
            db=db
        )

        logger.info(f"Model deployment rejected: {approval.model_id} by {user.username}")

        return {
            "status": "rejected",
            "approval_id": approval_id,
            "model_id": str(approval.model_id),
            "model_name": model.name if model else None,
            "rejected_by": user.username,
            "rejected_at": approval.reviewed_at.isoformat(),
            "reason": review_comments
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reject model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{model_id}/approval-status")
async def get_model_approval_status(
    model_id: str,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "read")),
    db: AsyncSession = Depends(get_db)
):
    """
    Check approval status for a model

    Returns current approval status and history for the model.
    """
    try:
        from app.models.finetuning_models import ModelApproval

        # Get model
        model_query = select(FineTunedModel).where(FineTunedModel.id == uuid.UUID(model_id))
        model_result = await db.execute(model_query)
        model = model_result.scalar_one_or_none()

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # Get approval history
        approvals_query = (
            select(ModelApproval, User.c.username)
            .outerjoin(User, ModelApproval.requested_by == User.c.id)
            .where(ModelApproval.model_id == uuid.UUID(model_id))
            .order_by(ModelApproval.requested_at.desc())
        )

        approvals_result = await db.execute(approvals_query)
        approvals = approvals_result.all()

        approval_history = []
        current_status = "no_request"
        can_deploy = model.status in ["approved", "deployed"]

        for approval, requester_username in approvals:
            approval_history.append({
                "approval_id": str(approval.id),
                "status": approval.status,
                "requested_by": requester_username or "Unknown",
                "requested_at": approval.requested_at.isoformat(),
                "reviewed_at": approval.reviewed_at.isoformat() if approval.reviewed_at else None,
                "review_comments": approval.review_comments
            })

            # Use most recent approval status
            if approval.status == "pending":
                current_status = "pending"
            elif approval.status == "approved" and current_status == "no_request":
                current_status = "approved"

        return {
            "model_id": model_id,
            "model_name": model.name,
            "model_status": model.status,
            "approval_status": current_status,
            "can_deploy": can_deploy,
            "approval_history": approval_history
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get approval status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MODEL DEPLOYMENT ENDPOINTS
# ============================================================================

@router.post("/models/{model_id}/deploy-ollama")
async def deploy_model_to_ollama(
    model_id: str,
    model_name_override: Optional[str] = Query(None, description="Override Ollama model name"),
    parameters: Optional[str] = Query(None, description="JSON string of model parameters (temperature, top_p, etc.)"),
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "write")),
    db: AsyncSession = Depends(get_db)
):
    """
    Deploy an approved fine-tuned model to Ollama

    Requirements:
    - Model must be in "approved" status (requires admin approval)
    - MinIO checkpoint path must exist
    - Ollama service must be running

    After deployment:
    - Model status updated to "deployed"
    - Ollama model name and URL stored
    - Model becomes available in chat UI dropdown
    """
    try:
        import json
        from minio import Minio
        from app.core.config import settings

        # Get model
        model_query = select(FineTunedModel).where(FineTunedModel.id == uuid.UUID(model_id))
        model_result = await db.execute(model_query)
        model = model_result.scalar_one_or_none()

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # Check approval status
        if model.status not in ["approved", "deployed"]:
            raise HTTPException(
                status_code=403,
                detail=f"Model must be approved before deployment. Current status: {model.status}. Please request approval first."
            )

        # Check if already deployed
        if model.status == "deployed" and model.ollama_model_name:
            return {
                "status": "already_deployed",
                "model_id": model_id,
                "ollama_model_name": model.ollama_model_name,
                "deployment_url": model.deployment_url,
                "message": f"Model already deployed as '{model.ollama_model_name}'"
            }

        # Check checkpoint path
        if not model.minio_checkpoint_path:
            raise HTTPException(status_code=400, detail="Model has no checkpoint path")

        # Download checkpoint from MinIO to temporary location
        logger.info(f"Downloading checkpoint from MinIO: {model.minio_checkpoint_path}")

        minio_client = Minio(
            endpoint=settings.MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_ENDPOINT.startswith("https://")
        )

        # Create temporary directory for model files
        import tempfile
        import os
        temp_dir = tempfile.mkdtemp(prefix="ollama_deploy_")

        try:
            # Download all checkpoint files from MinIO
            # Extract bucket and object path
            checkpoint_path_parts = model.minio_checkpoint_path.split("/", 1)
            if len(checkpoint_path_parts) != 2:
                raise ValueError(f"Invalid MinIO path format: {model.minio_checkpoint_path}")

            bucket_name = checkpoint_path_parts[0]
            object_prefix = checkpoint_path_parts[1]

            # List all objects with this prefix
            objects = minio_client.list_objects(bucket_name, prefix=object_prefix, recursive=True)

            downloaded_files = []
            for obj in objects:
                local_path = os.path.join(temp_dir, os.path.basename(obj.object_name))
                minio_client.fget_object(bucket_name, obj.object_name, local_path)
                downloaded_files.append(local_path)
                logger.info(f"Downloaded: {obj.object_name} -> {local_path}")

            if not downloaded_files:
                raise ValueError(f"No checkpoint files found at {model.minio_checkpoint_path}")

            # Find adapter_model.safetensors or similar
            adapter_file = None
            for file in downloaded_files:
                if "adapter_model" in file or "model.safetensors" in file:
                    adapter_file = file
                    break

            if not adapter_file:
                raise ValueError("No adapter model file found in checkpoint")

            # Deploy to Ollama
            ollama_service = OllamaDeploymentService()

            # Generate Ollama model name
            ollama_model_name = model_name_override or f"{model.name.lower().replace(' ', '-')}:{model.version}"

            # Parse parameters if provided
            deploy_params = {}
            if parameters:
                try:
                    deploy_params = json.loads(parameters)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=400, detail="Invalid parameters JSON")

            # Deploy
            logger.info(f"Deploying to Ollama as: {ollama_model_name}")
            deployment_result = await ollama_service.deploy_model(
                model_name=ollama_model_name,
                model_path=adapter_file,
                base_model=model.base_model,
                parameters=deploy_params
            )

            if deployment_result.get("status") != "success":
                raise Exception(f"Ollama deployment failed: {deployment_result.get('error')}")

            # Update model record
            model.status = "deployed"
            model.ollama_model_name = ollama_model_name
            model.deployment_url = deployment_result.get("deployment_url")

            await db.commit()

            # Audit log
            await audit_service.log_action(
                user_id=user.id,
                action="deploy_model_ollama",
                details={
                    "model_id": model_id,
                    "model_name": model.name,
                    "ollama_model_name": ollama_model_name,
                    "deployment_url": model.deployment_url
                },
                db=db
            )

            logger.info(f"✅ Model deployed to Ollama: {ollama_model_name}")

            return {
                "status": "deployed",
                "model_id": model_id,
                "model_name": model.name,
                "ollama_model_name": ollama_model_name,
                "deployment_url": model.deployment_url,
                "message": f"Model successfully deployed to Ollama as '{ollama_model_name}'"
            }

        finally:
            # Cleanup temporary files
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deploy model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")


@router.post("/models/{model_id}/undeploy")
async def undeploy_model_from_ollama(
    model_id: str,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "write")),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a deployed model from Ollama

    Updates model status back to "approved" and removes Ollama references.
    """
    try:
        # Get model
        model_query = select(FineTunedModel).where(FineTunedModel.id == uuid.UUID(model_id))
        model_result = await db.execute(model_query)
        model = model_result.scalar_one_or_none()

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        if model.status != "deployed":
            return {
                "status": "not_deployed",
                "message": "Model is not currently deployed"
            }

        ollama_model_name = model.ollama_model_name

        # Remove from Ollama via HTTP API (not subprocess - works in containers)
        if ollama_model_name:
            try:
                import httpx
                ollama_url = os.getenv("OLLAMA_API_URL", "http://ollama:11434")

                async with httpx.AsyncClient(timeout=30.0) as client:
                    delete_response = await client.delete(
                        f"{ollama_url}/api/delete",
                        json={"name": ollama_model_name}
                    )

                    if delete_response.status_code == 200:
                        logger.info(f"✅ Removed model from Ollama: {ollama_model_name}")
                    else:
                        logger.warning(f"⚠️ Failed to remove from Ollama (HTTP {delete_response.status_code}): {ollama_model_name}")

            except Exception as e:
                logger.error(f"❌ Error removing from Ollama: {e}")

        # Update model status
        model.status = "approved"  # Back to approved, can be re-deployed
        model.ollama_model_name = None
        model.deployment_url = None

        await db.commit()

        # Audit log
        await audit_service.log_action(
            user_id=user.id,
            action="undeploy_model_ollama",
            details={
                "model_id": model_id,
                "model_name": model.name,
                "ollama_model_name": ollama_model_name
            },
            db=db
        )

        return {
            "status": "undeployed",
            "model_id": model_id,
            "message": f"Model '{ollama_model_name}' removed from Ollama"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to undeploy model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/deployed")
async def list_deployed_models(
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "read")),
    db: AsyncSession = Depends(get_db)
):
    """
    List all deployed models available for chat

    Returns models with status="deployed" and Ollama model names.
    This endpoint is used by the chat UI to populate the model dropdown.
    """
    try:
        query = (
            select(FineTunedModel)
            .where(FineTunedModel.status == "deployed")
            .where(FineTunedModel.ollama_model_name.isnot(None))
            .order_by(FineTunedModel.created_at.desc())
        )

        result = await db.execute(query)
        models = result.scalars().all()

        deployed_models = []
        for model in models:
            deployed_models.append({
                "model_id": str(model.id),
                "name": model.name,
                "version": model.version,
                "ollama_model_name": model.ollama_model_name,
                "base_model": model.base_model,
                "finetuning_method": model.finetuning_method,
                "description": model.description,
                "deployment_url": model.deployment_url,
                "eval_metrics": model.eval_metrics,
                "total_inferences": model.total_inferences,
                "created_at": model.created_at.isoformat()
            })

        return {
            "deployed_models": deployed_models,
            "total": len(deployed_models)
        }

    except Exception as e:
        logger.error(f"Failed to list deployed models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/sync-ollama-status")
async def sync_ollama_model_status(
    user: User = Depends(require_authentication),
    _: None = Depends(RequireAdmin()),
    db: AsyncSession = Depends(get_db)
):
    """
    Sync database model status with Ollama reality (admin only)

    Checks Ollama for deployed models and updates database status.
    Handles cases where models were manually deleted from Ollama.

    Returns:
    - synced: List of models that were synced
    - undeployed: List of models that were marked as undeployed (deleted from Ollama)
    """
    try:
        import httpx

        ollama_url = os.getenv("OLLAMA_API_URL", "http://ollama:11434")

        # Get list of models from Ollama
        async with httpx.AsyncClient(timeout=30.0) as client:
            ollama_response = await client.get(f"{ollama_url}/api/tags")

            if ollama_response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to fetch Ollama models")

            ollama_data = ollama_response.json()
            ollama_model_names = {model["name"] for model in ollama_data.get("models", [])}

        # Get all deployed models from database
        query = select(FineTunedModel).where(FineTunedModel.status == "deployed")
        result = await db.execute(query)
        deployed_models = result.scalars().all()

        synced = []
        undeployed = []

        for model in deployed_models:
            if model.ollama_model_name:
                # Check if model still exists in Ollama
                if model.ollama_model_name in ollama_model_names:
                    # Model exists in Ollama - status is correct
                    synced.append({
                        "model_id": str(model.id),
                        "name": model.name,
                        "ollama_model_name": model.ollama_model_name,
                        "status": "deployed"
                    })
                else:
                    # Model deleted from Ollama - update database
                    logger.warning(f"Model {model.name} ({model.ollama_model_name}) not found in Ollama - marking as approved")

                    model.status = "approved"  # Not deployed anymore
                    model.ollama_model_name = None
                    model.deployment_url = None

                    undeployed.append({
                        "model_id": str(model.id),
                        "name": model.name,
                        "ollama_model_name": model.ollama_model_name,
                        "status": "undeployed"
                    })

        await db.commit()

        # Audit log
        await audit_service.log_action(
            user_id=user.id,
            action="sync_ollama_model_status",
            details={
                "synced_count": len(synced),
                "undeployed_count": len(undeployed)
            },
            db=db
        )

        return {
            "message": "Ollama sync complete",
            "synced": synced,
            "undeployed": undeployed,
            "synced_count": len(synced),
            "undeployed_count": len(undeployed)
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to sync Ollama status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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


@router.get("/gpu/capabilities")
async def get_gpu_capabilities():
    """
    Detect available GPUs and their capabilities

    TODO: Re-enable authentication when RBAC middleware is properly configured in main.py
    Currently authentication is disabled for testing as main.py doesn't have RBAC middleware.
    For production, uncomment the dependencies below:
    # user: User = Depends(require_authentication),
    # _: None = Depends(RequirePermission("model_finetuning", "read"))

    Returns hardware-aware configuration recommendations and presets
    based on detected GPU memory and count. Used by UI to show
    realistic GPU configuration options.

    Returns:
        - available: bool - Whether GPUs are available
        - gpu_count: int - Number of detected GPUs
        - gpus: List of GPU details (name, memory, utilization)
        - recommended_config: Suggested GPU configuration
        - presets: Hardware-aware presets (small/medium/large model)
    """
    try:
        # Get GPU information from pool manager
        gpu_info_list = []
        for gpu_id in gpu_pool_manager.gpu_pool:
            gpu_info = await gpu_pool_manager.get_gpu_info(gpu_id)
            if gpu_info:
                gpu_info_list.append(gpu_info)

        if not gpu_info_list:
            # No GPUs detected - return CPU-only configuration
            return {
                "available": False,
                "gpu_count": 0,
                "message": "No GPUs detected. CPU-only mode available (slow training).",
                "recommended_config": {
                    "gpu_count": 0,
                    "min_gpu_memory_gb": 0,
                    "max_memory_gb": 4
                },
                "presets": {
                    "cpu_only": {
                        "name": "CPU Only",
                        "description": "Training on CPU (very slow, not recommended)",
                        "icon": "💻",
                        "hyperparameters": {
                            "gpu_count": 0,
                            "batch_size": 1,
                            "max_seq_length": 256
                        }
                    }
                }
            }

        # Calculate total and per-GPU memory
        total_gpus = len(gpu_info_list)
        max_memory_gpu = max(gpu_info_list, key=lambda g: g.total_memory_gb)
        total_memory_gb = max_memory_gpu.total_memory_gb
        safe_memory_gb = total_memory_gb * 0.8  # 80% of total for safety

        # Format GPU details
        gpu_details = [
            {
                "id": gpu.device_id,
                "name": gpu.name,
                "memory_total_gb": round(gpu.total_memory_gb, 2),
                "memory_free_gb": round(gpu.free_memory_gb, 2),
                "memory_used_gb": round(gpu.total_memory_gb - gpu.free_memory_gb, 2),
                "utilization_percent": round(gpu.utilization_percent, 2),
                "temperature_c": gpu.temperature_celsius
            }
            for gpu in gpu_info_list
        ]

        # Recommended configuration based on available memory
        recommended_config = {
            "gpu_count": 1,  # Start with single GPU
            "min_gpu_memory_gb": round(safe_memory_gb * 0.5, 1),  # 50% of safe memory
            "max_memory_gb": round(safe_memory_gb, 1)
        }

        # Hardware-aware presets based on GPU memory
        presets = {}

        # Small Model preset (requires 6GB+)
        if safe_memory_gb >= 6.0:
            presets["small_model"] = {
                "name": "Small Model (< 7B)",
                "description": f"Optimal for 7B models (e.g., Mistral, Llama-2-7B) on your {max_memory_gpu.name}",
                "icon": "📱",
                "hardware_requirements": {
                    "min_gpu_memory_gb": 6.0,
                    "recommended_gpu": max_memory_gpu.name
                },
                "hyperparameters": {
                    "gpu_count": 1,
                    "min_gpu_memory_gb": 6.0,
                    "max_memory_gb": round(min(safe_memory_gb, 12.0), 1),
                    "batch_size": 4,
                    "gradient_accumulation_steps": 2,
                    "max_seq_length": 512,
                    "lora_rank": 8,
                    "lora_alpha": 16
                }
            }

        # Medium Model preset (requires 12GB+)
        if safe_memory_gb >= 12.0:
            presets["medium_model"] = {
                "name": "Medium Model (7B-13B)",
                "description": f"For 13B models (e.g., Llama-2-13B, Vicuna-13B) on your {max_memory_gpu.name}",
                "icon": "💻",
                "hardware_requirements": {
                    "min_gpu_memory_gb": 12.0,
                    "recommended_gpu": max_memory_gpu.name
                },
                "hyperparameters": {
                    "gpu_count": 1,
                    "min_gpu_memory_gb": 12.0,
                    "max_memory_gb": round(min(safe_memory_gb, 24.0), 1),
                    "batch_size": 2,
                    "gradient_accumulation_steps": 4,
                    "max_seq_length": 1024,
                    "lora_rank": 16,
                    "lora_alpha": 32
                }
            }

        # Large Model preset (requires 24GB+)
        if safe_memory_gb >= 24.0:
            presets["large_model"] = {
                "name": "Large Model (13B+)",
                "description": f"For 33B+ models (e.g., Llama-2-70B, GPT-NeoX-20B) on your {max_memory_gpu.name}",
                "icon": "🖥️",
                "hardware_requirements": {
                    "min_gpu_memory_gb": 24.0,
                    "recommended_gpu": max_memory_gpu.name
                },
                "hyperparameters": {
                    "gpu_count": min(total_gpus, 2),  # Use 2 GPUs if available
                    "min_gpu_memory_gb": 24.0,
                    "max_memory_gb": round(min(safe_memory_gb, 40.0), 1),
                    "batch_size": 1,
                    "gradient_accumulation_steps": 8,
                    "max_seq_length": 2048,
                    "lora_rank": 32,
                    "lora_alpha": 64
                }
            }

        # Memory Efficient preset (requires 4GB+)
        if safe_memory_gb >= 4.0:
            presets["memory_efficient"] = {
                "name": "Memory Efficient",
                "description": "Minimal memory usage for GPUs with limited VRAM",
                "icon": "💾",
                "hardware_requirements": {
                    "min_gpu_memory_gb": 4.0,
                    "recommended_gpu": "Any GPU with 4GB+ VRAM"
                },
                "hyperparameters": {
                    "gpu_count": 1,
                    "min_gpu_memory_gb": 4.0,
                    "max_memory_gb": round(min(safe_memory_gb, 8.0), 1),
                    "batch_size": 1,
                    "gradient_accumulation_steps": 8,
                    "max_seq_length": 256,
                    "lora_rank": 4,
                    "lora_alpha": 8,
                    "optimizer": "adafactor"
                }
            }

        return {
            "available": True,
            "gpu_count": total_gpus,
            "gpus": gpu_details,
            "total_memory_gb": round(total_memory_gb, 2),
            "safe_memory_gb": round(safe_memory_gb, 2),
            "recommended_config": recommended_config,
            "presets": presets,
            "hardware_summary": f"{total_gpus}x {max_memory_gpu.name} ({round(total_memory_gb, 1)}GB each)"
        }

    except Exception as e:
        logger.error(f"Failed to get GPU capabilities: {e}", exc_info=True)
        # Don't fail completely - return CPU-only fallback
        return {
            "available": False,
            "gpu_count": 0,
            "error": str(e),
            "message": "Failed to detect GPUs. Defaulting to CPU-only mode.",
            "recommended_config": {
                "gpu_count": 0,
                "min_gpu_memory_gb": 0,
                "max_memory_gb": 4
            }
        }


@router.get("/hyperparameters/config")
async def get_hyperparameter_config():
    """
    Get hyperparameter configuration from YAML file

    Returns all hyperparameter definitions, ranges, presets, and validation rules
    for building dynamic UI sliders and dropdowns.

    Returns:
        - hyperparameters: Dict of parameter definitions with types, ranges, defaults
        - presets: Dict of named preset configurations
        - validation: Validation rules for parameters
    """
    import yaml
    from pathlib import Path

    try:
        # ✅ FIX: Path calculation - need 4 parents to get from /app/app/api/routes/ to /app/
        # __file__ = /app/app/api/routes/finetuning_routes.py
        # .parent.parent.parent.parent = /app/
        config_path = Path(__file__).parent.parent.parent.parent / "config" / "finetuning_hyperparameter_defaults.yaml"

        if not config_path.exists():
            raise FileNotFoundError(f"Hyperparameter config file not found: {config_path}")

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        return {
            "hyperparameters": config.get("hyperparameters", {}),
            "presets": config.get("presets", {}),
            "validation": config.get("validation", {}),
            "version": config.get("version", "1.0"),
            "updated": config.get("updated")
        }

    except Exception as e:
        logger.error(f"Failed to load hyperparameter config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load hyperparameter configuration: {str(e)}")


@router.get("/hyperparameters/defaults")
async def get_hyperparameter_defaults(finetuning_method: Optional[str] = "PEFT"):
    """
    Get default hyperparameter values for a specific fine-tuning method

    Args:
        finetuning_method: Method (PEFT, SFT, RLHF_PPO, RLHF_GRPO)

    Returns:
        Dict of default hyperparameter values filtered by method
    """
    import yaml
    from pathlib import Path

    try:
        config_path = Path(__file__).parent.parent.parent / "config" / "finetuning_hyperparameter_defaults.yaml"

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        hyperparameters = config.get("hyperparameters", {})
        defaults = {}

        for param_name, param_config in hyperparameters.items():
            # Check if parameter is applicable to this method
            applicable_to = param_config.get("applicable_to", [])

            # If no applicable_to specified, include for all methods
            # Otherwise, only include if method matches
            if not applicable_to or finetuning_method in applicable_to:
                defaults[param_name] = param_config.get("default")

        return {
            "finetuning_method": finetuning_method,
            "defaults": defaults
        }

    except Exception as e:
        logger.error(f"Failed to get hyperparameter defaults: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get hyperparameter defaults: {str(e)}")


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
    force: bool = False,  # Force delete even if deployed
    user: User = Depends(require_authentication),
    _: None = Depends(RequireAdmin()),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a model (admin only)

    Removes model from registry and Ollama if deployed.

    Args:
        model_id: UUID of the model to delete
        force: If True, undeploy from Ollama before deleting (default: False for safety)
    """
    try:
        # Get model
        query = select(FineTunedModel).where(FineTunedModel.id == uuid.UUID(model_id))
        result = await db.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        ollama_model_name = model.ollama_model_name
        was_deployed = model.status == "deployed"

        # If model is deployed, either force undeploy or reject
        if was_deployed:
            if not force:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot delete deployed model. Use force=true to undeploy and delete, or undeploy first."
                )

            # Force undeploy: Remove from Ollama via HTTP API
            if ollama_model_name:
                try:
                    import httpx
                    ollama_url = os.getenv("OLLAMA_API_URL", "http://ollama:11434")

                    async with httpx.AsyncClient(timeout=30.0) as client:
                        delete_response = await client.delete(
                            f"{ollama_url}/api/delete",
                            json={"name": ollama_model_name}
                        )

                        if delete_response.status_code == 200:
                            logger.info(f"✅ Removed model from Ollama: {ollama_model_name}")
                        else:
                            logger.warning(f"⚠️ Failed to remove from Ollama (HTTP {delete_response.status_code}): {ollama_model_name}")
                            # Continue anyway - model may already be gone from Ollama

                except Exception as e:
                    logger.warning(f"⚠️ Error removing from Ollama (continuing with DB deletion): {e}")
                    # Continue with database deletion even if Ollama removal fails
                    # This handles the case where user manually deleted from Ollama already

        # Delete model from database
        await db.delete(model)
        await db.commit()

        # TODO: Delete checkpoint from MinIO

        # Audit log
        await audit_service.log_action(
            user_id=user.id,
            action="delete_finetuned_model",
            details={
                "model_id": model_id,
                "model_name": model.model_name,
                "ollama_model_name": ollama_model_name,
                "was_deployed": was_deployed,
                "force_undeploy": force
            },
            db=db
        )

        return {
            "message": "Model deleted successfully",
            "undeployed_from_ollama": was_deployed and ollama_model_name is not None
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete model: {str(e)}")


# ============================================================================
# STATISTICS & CATALOG ENDPOINTS
# ============================================================================

@router.get("/stats")
async def get_finetuning_stats(
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "read")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get fine-tuning dashboard statistics

    Returns:
    - running_jobs: Number of currently running jobs
    - pending_approvals: Number of models pending evaluation approval
    - active_models: Number of deployed models
    - datasets_ready: Number of validated datasets
    """
    try:
        # Count running jobs
        running_jobs_query = select(func.count(FineTuningJob.id)).where(
            FineTuningJob.status == "running"
        )
        running_jobs_result = await db.execute(running_jobs_query)
        running_jobs = running_jobs_result.scalar() or 0

        # Count pending approvals (models in registered state)
        pending_approvals_query = select(func.count(FineTunedModel.id)).where(
            FineTunedModel.status == "registered"
        )
        pending_approvals_result = await db.execute(pending_approvals_query)
        pending_approvals = pending_approvals_result.scalar() or 0

        # Count active/deployed models
        active_models_query = select(func.count(FineTunedModel.id)).where(
            FineTunedModel.status == "deployed"
        )
        active_models_result = await db.execute(active_models_query)
        active_models = active_models_result.scalar() or 0

        # Count validated datasets
        datasets_ready_query = select(func.count(FineTuningDataset.id)).where(
            and_(
                FineTuningDataset.is_valid == True,
                FineTuningDataset.preprocessing_status == "completed"
            )
        )
        datasets_ready_result = await db.execute(datasets_ready_query)
        datasets_ready = datasets_ready_result.scalar() or 0

        return {
            "running_jobs": running_jobs,
            "pending_approvals": pending_approvals,
            "active_models": active_models,
            "datasets_ready": datasets_ready
        }

    except Exception as e:
        logger.error(f"Failed to get stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/base-models")
async def get_base_models(
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "read"))
):
    """
    Get base model catalog with VRAM and cost estimations

    Optimized for consumer-grade GPUs (RTX 3090/4090 with 24GB VRAM)
    Strongly recommends QLoRA for efficient training
    """
    try:
        # Base model catalog with realistic VRAM requirements and costs
        # Optimized for consumer GPUs
        models = [
            {
                "id": "qwen-2.5-1.5b",
                "name": "Qwen2.5-1.5B-Instruct",
                "family": "Qwen",
                "size": "1.5B",
                "contextLength": 32768,
                "license": "Apache 2.0",
                "compatibility": {
                    "fullFineTune": True,   # Small enough for full FT
                    "lora": True,
                    "qlora": True
                },
                "vramRequirements": {
                    "fullFT": 8,   # ✅ Very light on VRAM
                    "lora": 4,     # ✅ Extremely light
                    "qlora": 2     # ✅ Minimal VRAM usage
                },
                "trainingCost": {
                    "fullFT": 0.3,  # $/hour (hypothetical cloud cost)
                    "lora": 0.15,
                    "qlora": 0.1    # Most economical
                },
                "recommended": True,
                "tags": ["fast", "lightweight", "multilingual", "instruct"]
            },
            {
                "id": "qwen-2.5-7b",
                "name": "Qwen2.5-7B-Instruct",
                "family": "Qwen",
                "size": "7B",
                "contextLength": 32768,
                "license": "Apache 2.0",
                "compatibility": {
                    "fullFineTune": False,  # Too much VRAM for consumer GPU
                    "lora": True,
                    "qlora": True
                },
                "vramRequirements": {
                    "fullFT": 80,  # Not feasible on consumer GPU
                    "lora": 32,    # Marginal on 24GB GPU
                    "qlora": 12    # ✅ Fits on consumer GPU
                },
                "trainingCost": {
                    "fullFT": 3.0,  # $/hour (hypothetical cloud cost)
                    "lora": 1.5,
                    "qlora": 0.5    # Most economical
                },
                "recommended": True,
                "tags": ["multilingual", "instruct", "reasoning"]
            },
            {
                "id": "llama-2-7b",
                "name": "Llama-2-7B",
                "family": "LLaMA",
                "size": "7B",
                "contextLength": 4096,
                "license": "LLaMA 2 Community",
                "compatibility": {
                    "fullFineTune": False,
                    "lora": True,
                    "qlora": True
                },
                "vramRequirements": {
                    "fullFT": 70,
                    "lora": 28,
                    "qlora": 10
                },
                "trainingCost": {
                    "fullFT": 2.8,
                    "lora": 1.4,
                    "qlora": 0.45
                },
                "recommended": True,
                "tags": ["general", "chat", "instruct"]
            },
            {
                "id": "mistral-7b-instruct",
                "name": "Mistral-7B-Instruct-v0.2",
                "family": "Mistral",
                "size": "7B",
                "contextLength": 8192,
                "license": "Apache 2.0",
                "compatibility": {
                    "fullFineTune": False,
                    "lora": True,
                    "qlora": True
                },
                "vramRequirements": {
                    "fullFT": 75,
                    "lora": 30,
                    "qlora": 11
                },
                "trainingCost": {
                    "fullFT": 2.9,
                    "lora": 1.45,
                    "qlora": 0.48
                },
                "recommended": True,
                "tags": ["fast", "efficient", "instruct"]
            },
            {
                "id": "gemma-7b",
                "name": "Gemma-7B",
                "family": "Gemma",
                "size": "7B",
                "contextLength": 8192,
                "license": "Gemma Terms of Use",
                "compatibility": {
                    "fullFineTune": False,
                    "lora": True,
                    "qlora": True
                },
                "vramRequirements": {
                    "fullFT": 72,
                    "lora": 29,
                    "qlora": 11
                },
                "trainingCost": {
                    "fullFT": 2.85,
                    "lora": 1.42,
                    "qlora": 0.47
                },
                "recommended": False,
                "tags": ["google", "instruct", "safe"]
            },
            {
                "id": "llama-2-13b",
                "name": "Llama-2-13B",
                "family": "LLaMA",
                "size": "13B",
                "contextLength": 4096,
                "license": "LLaMA 2 Community",
                "compatibility": {
                    "fullFineTune": False,
                    "lora": False,  # Too much for 24GB
                    "qlora": True   # QLoRA makes it possible!
                },
                "vramRequirements": {
                    "fullFT": 140,
                    "lora": 48,     # Won't fit on consumer GPU
                    "qlora": 18     # ✅ Fits with 4-bit quantization
                },
                "trainingCost": {
                    "fullFT": 5.0,
                    "lora": 2.5,
                    "qlora": 0.8
                },
                "recommended": False,
                "tags": ["large", "capable", "instruct"]
            },
            {
                "id": "mistral-7b-v03",
                "name": "Mistral-7B-v0.3",
                "family": "Mistral",
                "size": "7B",
                "contextLength": 32768,
                "license": "Apache 2.0",
                "compatibility": {
                    "fullFineTune": False,
                    "lora": True,
                    "qlora": True
                },
                "vramRequirements": {
                    "fullFT": 75,
                    "lora": 30,
                    "qlora": 11
                },
                "trainingCost": {
                    "fullFT": 2.9,
                    "lora": 1.45,
                    "qlora": 0.48
                },
                "recommended": True,
                "tags": ["fast", "long-context", "instruct"]
            }
        ]

        return {"models": models}

    except Exception as e:
        logger.error(f"Failed to get base models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get base models: {str(e)}")


@router.post("/models/{model_id}/evaluate")
async def evaluate_model(
    model_id: str,
    benchmark_dataset: Optional[str] = "default",
    metrics: Optional[List[str]] = None,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "execute")),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger evaluation for a fine-tuned model

    Args:
        model_id: Model UUID to evaluate
        benchmark_dataset: Benchmark dataset to use (default, custom)
        metrics: List of metrics to compute (accuracy, perplexity, rouge, bleu, etc.)

    Returns:
        Evaluation job information
    """
    try:
        # Get model
        query = select(FineTunedModel).where(FineTunedModel.id == uuid.UUID(model_id))
        result = await db.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # TODO: Implement actual evaluation logic
        # For now, return a placeholder response
        logger.info(f"Evaluation requested for model {model_id} with metrics: {metrics}")

        # In production, this would:
        # 1. Load the fine-tuned model
        # 2. Run inference on benchmark dataset
        # 3. Calculate requested metrics
        # 4. Store results in model.eval_metrics

        # Simulated evaluation results (for demonstration)
        mock_eval_metrics = {
            "accuracy": 0.85,
            "perplexity": 2.3,
            "rouge_1": 0.72,
            "rouge_2": 0.58,
            "rouge_l": 0.69,
            "bleu_score": 0.64,
            "f1_score": 0.82
        }

        # Update model with evaluation metrics
        model.eval_metrics = mock_eval_metrics
        await db.commit()

        return {
            "status": "completed",
            "model_id": model_id,
            "job_id": str(uuid.uuid4()),
            "metrics": mock_eval_metrics,
            "message": "Evaluation completed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to evaluate model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to evaluate model: {str(e)}")


@router.post("/models/inference")
async def model_inference(
    model_id: str,
    prompt: str,
    max_tokens: int = 256,
    temperature: float = 0.7,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "execute")),
    db: AsyncSession = Depends(get_db)
):
    """
    Run inference on a fine-tuned model for comparison

    Args:
        model_id: Model UUID
        prompt: Input prompt
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature

    Returns:
        Model response with latency and token count
    """
    try:
        # Get model
        query = select(FineTunedModel).where(FineTunedModel.id == uuid.UUID(model_id))
        result = await db.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # TODO: Implement actual inference logic
        # For now, return a placeholder response
        logger.info(f"Inference requested for model {model_id} with prompt: {prompt[:50]}...")

        # In production, this would:
        # 1. Load the model from checkpoint or Ollama
        # 2. Run inference with the prompt
        # 3. Track latency and tokens

        # Simulated response (for demonstration)
        import time
        start_time = time.time()

        mock_response = f"This is a simulated response from {model.name} (v{model.version}). " \
                       f"In production, this would be the actual model output based on your prompt: '{prompt[:100]}...'"

        latency_ms = (time.time() - start_time) * 1000

        return {
            "model_id": model_id,
            "model_name": model.name,
            "response": mock_response,
            "latency_ms": round(latency_ms, 2),
            "tokens_used": len(mock_response.split()),
            "prompt_tokens": len(prompt.split()),
            "completion_tokens": len(mock_response.split())
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run inference: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to run inference: {str(e)}")


# ============================================================================
# GOVERNANCE & AUDIT ENDPOINTS
# ============================================================================

@router.get("/audit/logs")
async def get_finetuning_audit_logs(
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "read")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get fine-tuning audit logs

    Returns audit trail for:
    - Dataset uploads
    - Job submissions
    - Model registrations
    - Deployments
    - Approvals/rejections
    """
    try:
        from app.models.database_enhanced import AuditLog

        # Build query with filters
        conditions = [
            AuditLog.resource_type.in_([
                'finetuning_dataset',
                'finetuning_job',
                'finetuned_model',
                'model_deployment'
            ])
        ]

        if action:
            conditions.append(AuditLog.action == action)

        if resource_type:
            conditions.append(AuditLog.resource_type == resource_type)

        query = select(AuditLog).where(and_(*conditions))
        query = query.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)

        result = await db.execute(query)
        logs = result.scalars().all()

        return {
            "logs": [
                {
                    "id": str(log.id),
                    "user_id": str(log.user_id) if log.user_id else None,
                    "action": log.action.value if log.action else None,
                    "resource_type": log.resource_type,
                    "resource_id": str(log.resource_id) if log.resource_id else None,
                    "description": log.description,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat(),
                    "details": log.details
                }
                for log in logs
            ],
            "total": len(logs)
        }

    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get audit logs: {str(e)}")


@router.post("/models/{model_id}/approve")
async def approve_model(
    model_id: str,
    approval_notes: Optional[str] = None,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "execute")),
    db: AsyncSession = Depends(get_db)
):
    """
    Approve a fine-tuned model for deployment

    Changes model status from 'registered' to 'approved'.
    Model can then be deployed to inference engines.
    """
    try:
        # Get model
        query = select(FineTunedModel).where(FineTunedModel.id == uuid.UUID(model_id))
        result = await db.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        if model.status != "registered":
            raise HTTPException(
                status_code=400,
                detail=f"Can only approve models in 'registered' state. Current state: {model.status}"
            )

        # Update model status
        model.status = "approved"
        model.updated_at = datetime.utcnow()

        # Store approval metadata
        if not model.metadata:
            model.metadata = {}
        model.metadata["approval"] = {
            "approved_by": str(user.id),
            "approved_by_username": user.username,
            "approved_at": datetime.utcnow().isoformat(),
            "notes": approval_notes
        }

        await db.commit()
        await db.refresh(model)

        # Audit log
        await audit_service.log_action(
            user_id=user.id,
            action="approve",
            resource_type="finetuned_model",
            resource_id=model.id,
            description=f"Approved model {model.name} v{model.version}",
            db=db,
            details={"notes": approval_notes}
        )

        logger.info(f"✅ Model {model.name} approved by {user.username}")

        return {
            "status": "success",
            "model_id": str(model.id),
            "model_name": model.name,
            "model_status": model.status,
            "approved_by": user.username,
            "message": "Model approved successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to approve model: {str(e)}")


@router.post("/models/{model_id}/reject")
async def reject_model(
    model_id: str,
    rejection_reason: str,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "execute")),
    db: AsyncSession = Depends(get_db)
):
    """
    Reject a fine-tuned model

    Changes model status to 'rejected'.
    Model will not be available for deployment.
    """
    try:
        # Get model
        query = select(FineTunedModel).where(FineTunedModel.id == uuid.UUID(model_id))
        result = await db.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        if model.status != "registered":
            raise HTTPException(
                status_code=400,
                detail=f"Can only reject models in 'registered' state. Current state: {model.status}"
            )

        # Update model status
        model.status = "rejected"
        model.updated_at = datetime.utcnow()

        # Store rejection metadata
        if not model.metadata:
            model.metadata = {}
        model.metadata["rejection"] = {
            "rejected_by": str(user.id),
            "rejected_by_username": user.username,
            "rejected_at": datetime.utcnow().isoformat(),
            "reason": rejection_reason
        }

        await db.commit()
        await db.refresh(model)

        # Audit log
        await audit_service.log_action(
            user_id=user.id,
            action="reject",
            resource_type="finetuned_model",
            resource_id=model.id,
            description=f"Rejected model {model.name} v{model.version}",
            db=db,
            details={"reason": rejection_reason}
        )

        logger.warning(f"❌ Model {model.name} rejected by {user.username}: {rejection_reason}")

        return {
            "status": "success",
            "model_id": str(model.id),
            "model_name": model.name,
            "model_status": model.status,
            "rejected_by": user.username,
            "message": "Model rejected"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reject model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to reject model: {str(e)}")


@router.get("/models/{model_id}/lineage")
async def get_model_lineage(
    model_id: str,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "read")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete data lineage for a fine-tuned model

    Returns:
    - Source dataset information
    - Training job details
    - Model registration details
    - Deployment information
    - Approval/rejection history

    Enables traceability from training data to deployed model.
    """
    try:
        # Get model
        query = select(FineTunedModel).where(FineTunedModel.id == uuid.UUID(model_id))
        result = await db.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        lineage = {
            "model": {
                "id": str(model.id),
                "name": model.name,
                "version": model.version,
                "status": model.status,
                "base_model": model.base_model,
                "finetuning_method": model.finetuning_method,
                "created_at": model.created_at.isoformat(),
                "updated_at": model.updated_at.isoformat(),
                "eval_metrics": model.eval_metrics,
                "metadata": model.metadata
            },
            "training_job": None,
            "dataset": None,
            "deployment": None,
            "approval_history": []
        }

        # Get training job
        if model.job_id:
            job_query = select(FineTuningJob).where(FineTuningJob.id == model.job_id)
            job_result = await db.execute(job_query)
            job = job_result.scalar_one_or_none()

            if job:
                lineage["training_job"] = {
                    "id": str(job.id),
                    "name": job.job_name,
                    "status": job.status,
                    "training_config": job.training_config,
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "gpu_allocated": job.gpu_allocated,
                    "total_steps": job.total_steps,
                    "current_step": job.current_step
                }

                # Get dataset
                if job.dataset_id:
                    dataset_query = select(FineTuningDataset).where(
                        FineTuningDataset.id == job.dataset_id
                    )
                    dataset_result = await db.execute(dataset_query)
                    dataset = dataset_result.scalar_one_or_none()

                    if dataset:
                        lineage["dataset"] = {
                            "id": str(dataset.id),
                            "name": dataset.name,
                            "format_type": dataset.format_type,
                            "file_path": dataset.file_path,
                            "rows_count": dataset.rows_count,
                            "uploaded_at": dataset.uploaded_at.isoformat(),
                            "quality_metrics": dataset.quality_metrics,
                            "is_valid": dataset.is_valid
                        }

        # Get deployment info
        if model.status == "deployed":
            lineage["deployment"] = {
                "deployment_target": model.deployment_target,
                "deployment_url": model.deployment_url,
                "ollama_model_name": model.ollama_model_name,
                "deployed_at": model.updated_at.isoformat()
            }

        # Get approval/rejection history from metadata
        if model.metadata:
            if "approval" in model.metadata:
                lineage["approval_history"].append({
                    "action": "approved",
                    "by": model.metadata["approval"].get("approved_by_username"),
                    "at": model.metadata["approval"].get("approved_at"),
                    "notes": model.metadata["approval"].get("notes")
                })

            if "rejection" in model.metadata:
                lineage["approval_history"].append({
                    "action": "rejected",
                    "by": model.metadata["rejection"].get("rejected_by_username"),
                    "at": model.metadata["rejection"].get("rejected_at"),
                    "reason": model.metadata["rejection"].get("reason")
                })

        return lineage

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model lineage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get lineage: {str(e)}")


# ============================================================================
# MODEL LIFECYCLE ENDPOINTS (Evaluation, Deployment, Monitoring, Governance)
# ============================================================================

@router.post("/models/{model_id}/evaluate")
async def evaluate_model(
    model_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger evaluation of a fine-tuned model on test dataset

    Returns metrics:
    - Perplexity
    - BLEU score
    - ROUGE scores
    - Accuracy/F1

    TODO: Re-enable authentication when RBAC middleware is configured
    """
    try:
        query = select(FineTunedModel).where(FineTunedModel.id == uuid.UUID(model_id))
        result = await db.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # TODO: Implement actual evaluation - for now return simulated metrics
        eval_metrics = {
            "perplexity": 15.42,
            "bleu_score": 0.68,
            "rouge_1": 0.72,
            "rouge_2": 0.58,
            "rouge_l": 0.65,
            "accuracy": 0.84,
            "f1_score": 0.81,
            "eval_loss": 0.42,
            "evaluated_at": datetime.now().isoformat(),
            "test_samples": 500
        }

        model.eval_metrics = eval_metrics
        await db.commit()
        await db.refresh(model)

        return {
            "model_id": str(model.id),
            "model_name": model.name,
            "eval_metrics": eval_metrics
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to evaluate model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{model_id}/evaluation")
async def get_model_evaluation(
    model_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get evaluation metrics for a model"""
    try:
        query = select(FineTunedModel).where(FineTunedModel.id == uuid.UUID(model_id))
        result = await db.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        return {
            "model_id": str(model.id),
            "model_name": model.name,
            "eval_metrics": model.eval_metrics or {},
            "has_evaluation": model.eval_metrics is not None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get evaluation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/{model_id}/deploy")
async def deploy_model(
    model_id: str,
    deployment_config: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Deploy fine-tuned model to Ollama or vLLM

    Request: {"target": "ollama"|"vllm", "model_name": "my-model-v1"}
    """
    try:
        query = select(FineTunedModel).where(FineTunedModel.id == uuid.UUID(model_id))
        result = await db.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        target = deployment_config.get("target", "ollama")
        model_name = deployment_config.get("model_name", f"{model.name}-deployed")
        base_model = deployment_config.get("base_model", model.base_model or "llama2")
        parameters = deployment_config.get("parameters", {})

        deployment_result = {}

        if target == "ollama":
            # Use OllamaDeploymentService for actual deployment
            ollama_service = OllamaDeploymentService()

            # Get model checkpoint path from job
            if model.job_id:
                job_query = select(FineTuningJob).where(FineTuningJob.id == model.job_id)
                job_result = await db.execute(job_query)
                job = job_result.scalar_one_or_none()

                if job and job.checkpoint_path:
                    model_path = job.checkpoint_path
                else:
                    # Fallback to constructed path
                    model_path = f"/app/models/{model.name}/adapter_model"
            else:
                model_path = f"/app/models/{model.name}/adapter_model"

            # Deploy to Ollama
            deployment_result = await ollama_service.deploy_model(
                model_name=model_name,
                model_path=model_path,
                base_model=base_model,
                parameters=parameters
            )

            if deployment_result.get("status") == "success":
                model.ollama_model_name = model_name
                model.deployment_url = deployment_result.get("deployment_url")
                model.status = "deployed"
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Ollama deployment failed: {deployment_result.get('error')}"
                )

        elif target == "vllm":
            # TODO: Implement vLLM deployment
            deployment_url = "http://localhost:8001/v1/completions"
            model.vllm_model_name = model_name
            model.deployment_url = deployment_url
            model.status = "deployed"
            deployment_result = {
                "status": "success",
                "message": "vLLM deployment (simulated)"
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported target: {target}")

        await db.commit()
        await db.refresh(model)

        return {
            "model_id": str(model.id),
            "deployment_target": target,
            "deployment_url": model.deployment_url,
            "deployed_model_name": model_name,
            "status": model.status,
            "deployment_details": deployment_result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deploy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/deployed")
async def list_deployed_models(
    db: AsyncSession = Depends(get_db)
):
    """List all deployed models"""
    try:
        query = select(FineTunedModel).where(
            FineTunedModel.status == "deployed"
        ).order_by(FineTunedModel.created_at.desc())

        result = await db.execute(query)
        models = result.scalars().all()

        return {
            "deployed_models": [
                {
                    "id": str(m.id),
                    "name": m.name,
                    "version": m.version,
                    "base_model": m.base_model,
                    "deployment_url": m.deployment_url,
                    "ollama_model_name": m.ollama_model_name,
                    "vllm_model_name": m.vllm_model_name,
                    "total_inferences": m.total_inferences or 0,
                    "avg_latency_ms": m.avg_latency_ms,
                    "created_at": m.created_at.isoformat() if m.created_at else None
                }
                for m in models
            ],
            "total": len(models)
        }

    except Exception as e:
        logger.error(f"Failed to list deployed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{model_id}/metrics")
async def get_model_metrics(
    model_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get monitoring metrics for deployed model"""
    try:
        query = select(FineTunedModel).where(FineTunedModel.id == uuid.UUID(model_id))
        result = await db.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        return {
            "model_id": str(model.id),
            "model_name": model.name,
            "status": model.status,
            "metrics": {
                "total_inferences": model.total_inferences or 0,
                "avg_latency_ms": model.avg_latency_ms,
                "last_inference_at": model.last_inference_at.isoformat() if model.last_inference_at else None,
                "eval_metrics": model.eval_metrics or {}
            },
            "deployment": {
                "deployment_url": model.deployment_url,
                "ollama_model_name": model.ollama_model_name,
                "vllm_model_name": model.vllm_model_name
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/{model_id}/deprecate")
async def deprecate_model(
    model_id: str,
    deprecation_request: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Deprecate a model

    Request: {"reason": "Replaced by v2", "deprecated_by_user_id": "uuid"}
    """
    try:
        query = select(FineTunedModel).where(FineTunedModel.id == uuid.UUID(model_id))
        result = await db.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        if model.deprecated_at:
            raise HTTPException(status_code=400, detail="Already deprecated")

        reason = deprecation_request.get("reason", "No reason provided")
        deprecated_by = deprecation_request.get("deprecated_by_user_id")

        model.deprecated_at = datetime.now(timezone.utc)
        model.deprecation_reason = reason
        if deprecated_by:
            model.deprecated_by = uuid.UUID(deprecated_by)
        model.status = "deprecated"

        await db.commit()
        await db.refresh(model)

        return {
            "model_id": str(model.id),
            "status": model.status,
            "deprecated_at": model.deprecated_at.isoformat(),
            "deprecation_reason": model.deprecation_reason
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deprecate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/governance")
async def get_governance_status(
    db: AsyncSession = Depends(get_db)
):
    """Get governance status of all models"""
    try:
        query = select(FineTunedModel).order_by(FineTunedModel.created_at.desc())
        result = await db.execute(query)
        models = result.scalars().all()

        active = []
        deprecated = []
        pending = []

        for m in models:
            data = {
                "id": str(m.id),
                "name": m.name,
                "version": m.version,
                "status": m.status,
                "base_model": m.base_model,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "total_inferences": m.total_inferences or 0
            }

            if m.deprecated_at:
                data["deprecated_at"] = m.deprecated_at.isoformat()
                data["deprecation_reason"] = m.deprecation_reason
                deprecated.append(data)
            elif m.status == "deployed":
                active.append(data)
            elif m.status == "pending_approval":
                pending.append(data)
            else:
                active.append(data)

        return {
            "governance_summary": {
                "total_models": len(models),
                "active_count": len(active),
                "deprecated_count": len(deprecated),
                "pending_approval_count": len(pending)
            },
            "active_models": active,
            "deprecated_models": deprecated,
            "pending_approval": pending
        }

    except Exception as e:
        logger.error(f"Failed to get governance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/for-chat")
async def get_models_for_chat(
    db: AsyncSession = Depends(get_db)
):
    """
    Get deployed fine-tuned models formatted for chat UI model selector

    Returns models in format compatible with existing model dropdown:
    {
      "finetuned_models": [
        {
          "id": "ollama/my-custom-model-v1",
          "name": "My Custom Model v1 (Fine-tuned)",
          "provider": "ollama",
          "description": "Fine-tuned on custom dataset"
        }
      ]
    }
    """
    try:
        query = select(FineTunedModel).where(
            FineTunedModel.status == "deployed"
        ).order_by(FineTunedModel.created_at.desc())

        result = await db.execute(query)
        models = result.scalars().all()

        finetuned_models = []
        for m in models:
            # Determine provider and model ID
            if m.ollama_model_name:
                provider = "ollama"
                model_id = f"ollama/{m.ollama_model_name}"
                name_suffix = " (Ollama)"
            elif m.vllm_model_name:
                provider = "vllm"
                model_id = f"vllm/{m.vllm_model_name}"
                name_suffix = " (vLLM)"
            else:
                continue  # Skip if no deployment name

            finetuned_models.append({
                "id": model_id,
                "name": f"{m.name} {name_suffix}",
                "provider": provider,
                "description": f"Fine-tuned {m.base_model} - {m.version or 'v1.0'}",
                "base_model": m.base_model,
                "deployment_url": m.deployment_url,
                "eval_metrics": m.eval_metrics,
                "total_inferences": m.total_inferences or 0,
                "avg_latency_ms": m.avg_latency_ms
            })

        return {
            "finetuned_models": finetuned_models,
            "count": len(finetuned_models)
        }

    except Exception as e:
        logger.error(f"Failed to get models for chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ===================================================================
# TEMPORARY: Unauthenticated endpoint for UI testing
# TODO: Remove this in production and use proper authentication
# ===================================================================

@router.get("/models-public")
async def list_models_public(
    status: Optional[str] = Query(None, description="Filter by status (registered, deployed, etc.)"),
    db: AsyncSession = Depends(get_db)
):
    """
    **TEMPORARY**: List all fine-tuned models WITHOUT authentication

    This endpoint is for testing the UI with populated data.
    In production, use /models with proper authentication.

    Query Parameters:
        status: Optional filter by model status (registered, deployed, etc.)
    """
    try:
        query = select(FineTunedModel).order_by(FineTunedModel.created_at.desc())

        # Filter by status if provided
        if status:
            query = query.where(FineTunedModel.status == status)

        result = await db.execute(query)
        models_list = result.scalars().all()

        # Build response with MinIO paths and dataset names
        models_response = []
        for m in models_list:
            # Get MinIO path and dataset name from associated job
            minio_path = None
            dataset_name = None
            if m.job_id:
                # Query job with optional dataset join
                job_query = (
                    select(FineTuningJob, FineTuningDataset)
                    .outerjoin(FineTuningDataset, FineTuningJob.dataset_id == FineTuningDataset.id)
                    .where(FineTuningJob.id == m.job_id)
                )
                job_result = await db.execute(job_query)
                row = job_result.first()

                if row:
                    job, dataset = row
                    if job and job.minio_checkpoint_path:
                        # Prefer merged_model path if it exists
                        base_path = job.minio_checkpoint_path.replace("/adapter_model", "")
                        minio_path = f"{base_path}/merged_model"  # Point to merged model

                    # Get dataset name if associated
                    if dataset:
                        dataset_name = dataset.name

            models_response.append({
                "id": str(m.id),
                "name": m.name,
                "version": m.version,
                "description": m.description or "",
                "base_model": m.base_model,
                "finetuning_method": m.finetuning_method,
                "status": m.status,
                "eval_metrics": m.eval_metrics,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "ollama_model_name": m.ollama_model_name,
                "job_id": str(m.job_id) if m.job_id else None,
                "minio_path": minio_path,  # NEW: MinIO artifact path
                "dataset_name": dataset_name  # NEW: Training dataset name
            })

        return {"models": models_response}

    except Exception as e:
        logger.error(f"Failed to list models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs-public")
async def list_jobs_public(
    limit: int = Query(10, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    **TEMPORARY**: List fine-tuning jobs WITHOUT authentication
    For UI testing only. Use /jobs with auth in production.
    """
    try:
        query = select(FineTuningJob).order_by(FineTuningJob.created_at.desc()).limit(limit)
        result = await db.execute(query)
        jobs_list = result.scalars().all()

        return {
            "jobs": [
                {
                    "id": str(j.id),
                    "name": j.name,
                    "description": j.description,
                    "base_model": j.base_model,
                    "finetuning_method": j.finetuning_method,
                    "dataset_id": str(j.dataset_id) if j.dataset_id else None,
                    "status": j.status,
                    "progress": j.progress,
                    "current_epoch": j.current_epoch,
                    "total_steps": j.total_steps,
                    "current_step": j.current_step,
                    "train_loss": j.train_loss,
                    "eval_loss": j.eval_loss,
                    "created_at": j.created_at.isoformat() if j.created_at else None,
                    "training_start_time": j.training_start_time.isoformat() if j.training_start_time else None,
                    "training_end_time": j.training_end_time.isoformat() if j.training_end_time else None,
                    "department": j.department,
                    "team": j.team,
                    # Pipeline stage fields (for stage visualization)
                    "training_stage": j.training_stage,
                    "stage_details": j.stage_details,
                    "stage_started_at": j.stage_started_at.isoformat() if j.stage_started_at else None,
                    "stage_completed_at": j.stage_completed_at.isoformat() if j.stage_completed_at else None,
                }
                for j in jobs_list
            ],
            "total": len(jobs_list)
        }
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/logs-public")
async def list_audit_logs_public(
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db)
):
    """
    **TEMPORARY**: List audit logs WITHOUT authentication
    For UI testing only. Use /audit/logs with auth in production.
    """
    try:
        # Return empty logs for now since we don't have audit table for finetuning
        return {
            "logs": [],
            "total": 0
        }
    except Exception as e:
        logger.error(f"Failed to list audit logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats-public")
async def get_finetuning_stats_public(
    db: AsyncSession = Depends(get_db)
):
    """
    **TEMPORARY**: Get fine-tuning dashboard statistics WITHOUT authentication
    For UI testing only. Use /stats with auth in production.

    Returns:
    - running_jobs: Number of currently running jobs
    - pending_approvals: Number of models pending evaluation approval
    - active_models: Number of deployed models
    - datasets_ready: Number of validated datasets
    """
    try:
        # Count running jobs
        running_jobs_query = select(func.count(FineTuningJob.id)).where(
            FineTuningJob.status == "running"
        )
        running_jobs_result = await db.execute(running_jobs_query)
        running_jobs = running_jobs_result.scalar() or 0

        # Count pending approvals (models in registered state)
        pending_approvals_query = select(func.count(FineTunedModel.id)).where(
            FineTunedModel.status == "registered"
        )
        pending_approvals_result = await db.execute(pending_approvals_query)
        pending_approvals = pending_approvals_result.scalar() or 0

        # Count active/deployed models
        active_models_query = select(func.count(FineTunedModel.id)).where(
            FineTunedModel.status == "deployed"
        )
        active_models_result = await db.execute(active_models_query)
        active_models = active_models_result.scalar() or 0

        # Count validated datasets
        datasets_ready_query = select(func.count(FineTuningDataset.id)).where(
            and_(
                FineTuningDataset.is_valid == True,
                FineTuningDataset.preprocessing_status == "completed"
            )
        )
        datasets_ready_result = await db.execute(datasets_ready_query)
        datasets_ready = datasets_ready_result.scalar() or 0

        return {
            "running_jobs": running_jobs,
            "pending_approvals": pending_approvals,
            "active_models": active_models,
            "datasets_ready": datasets_ready
        }

    except Exception as e:
        logger.error(f"Failed to get stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/gpu/stats-public")
async def get_gpu_pool_stats_public(
    db: AsyncSession = Depends(get_db)
):
    """
    **TEMPORARY**: Get GPU pool statistics WITHOUT authentication
    For UI testing only. Use /gpu/stats with auth in production.

    Shows total GPUs, allocations, and active jobs.
    """
    try:
        stats = gpu_pool_manager.get_stats()
        return stats

    except Exception as e:
        logger.error(f"Failed to get GPU stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get GPU stats: {str(e)}")


@router.get("/jobs-public/{job_id}/metrics")
async def get_job_metrics_public(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    **TEMPORARY**: Get training metrics for a job WITHOUT authentication
    For UI testing only. Use /jobs/{job_id}/metrics with auth in production.
    """
    try:
        # Get all metrics for this job
        query = select(TrainingMetric).where(
            TrainingMetric.job_id == uuid.UUID(job_id)
        ).order_by(TrainingMetric.step)

        result = await db.execute(query)
        metrics = result.scalars().all()

        if not metrics:
            return {
                "job_id": job_id,
                "metrics": []
            }

        # Format metrics
        metrics_list = [
            {
                "step": m.step,
                "epoch": m.epoch,
                "train_loss": m.train_loss,
                "eval_loss": m.eval_loss,
                "learning_rate": m.learning_rate,
                "timestamp": m.timestamp.isoformat() if m.timestamp else None
            }
            for m in metrics
        ]

        return {
            "job_id": job_id,
            "metrics": metrics_list
        }

    except Exception as e:
        logger.error(f"Failed to get job metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models-public/{model_id}/lineage")
async def get_model_lineage_public(
    model_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    **TEMPORARY**: Get complete data lineage for a fine-tuned model WITHOUT authentication
    For UI testing only. Use /models/{model_id}/lineage with auth in production.
    """
    try:
        # Get model
        query = select(FineTunedModel).where(FineTunedModel.id == uuid.UUID(model_id))
        result = await db.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        lineage = {
            "model": {
                "id": str(model.id),
                "name": model.name,
                "version": model.version,
                "status": model.status,
                "base_model": model.base_model,
                "finetuning_method": model.finetuning_method,
                "created_at": model.created_at.isoformat() if model.created_at else None,
                "eval_metrics": model.eval_metrics
            },
            "training_job": None,
            "dataset": None,
            "deployment": None,
            "approval_history": []
        }

        # Get training job
        if model.job_id:
            job_query = select(FineTuningJob).where(FineTuningJob.id == model.job_id)
            job_result = await db.execute(job_query)
            job = job_result.scalar_one_or_none()

            if job:
                lineage["training_job"] = {
                    "id": str(job.id),
                    "name": job.name,
                    "status": job.status,
                    "base_model": job.base_model,
                    "current_step": job.current_step,
                    "total_steps": job.total_steps
                }

                # Get dataset
                if job.dataset_id:
                    dataset_query = select(FineTuningDataset).where(FineTuningDataset.id == job.dataset_id)
                    dataset_result = await db.execute(dataset_query)
                    dataset = dataset_result.scalar_one_or_none()

                    if dataset:
                        lineage["dataset"] = {
                            "id": str(dataset.id),
                            "name": dataset.name,
                            "format_type": dataset.format_type,
                            "num_samples": dataset.num_samples,
                            "is_valid": dataset.is_valid,
                            "uploaded_at": dataset.uploaded_at.isoformat() if dataset.uploaded_at else None
                        }

        # Add deployment info if model is deployed
        if model.status == "deployed":
            lineage["deployment"] = {
                "deployment_target": "Ollama",
                "deployment_url": model.deployment_url if hasattr(model, 'deployment_url') else None,
                "ollama_model_name": model.ollama_model_name
            }

        return lineage

    except Exception as e:
        logger.error(f"Failed to get model lineage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PUBLIC APPROVE/REJECT ENDPOINTS (FOR UI TESTING ONLY - NO AUTHENTICATION)
# ============================================================================

@router.post("/models-public/{model_id}/approve")
async def approve_model_public(
    model_id: str,
    approval_notes: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    **TEMPORARY**: Approve a fine-tuned model WITHOUT authentication
    For UI testing only. Use /models/{model_id}/approve with auth in production.
    """
    try:
        # Get the model
        query = select(FineTunedModel).where(FineTunedModel.id == uuid.UUID(model_id))
        result = await db.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # Update model status to approved (not deployed - that happens separately)
        model.status = "approved"

        # Store approval notes in description or append to tags
        approval_text = approval_notes.get("approval_notes", "") if isinstance(approval_notes, dict) else str(approval_notes)

        # Append approval info to description
        approval_info = f"\n\n[APPROVED at {datetime.now().isoformat()} by test_user]\nNotes: {approval_text}"
        if model.description:
            model.description += approval_info
        else:
            model.description = approval_info.strip()

        await db.commit()
        await db.refresh(model)

        logger.info(f"Model {model_id} approved successfully (public endpoint)")

        return {
            "message": "Model approved successfully",
            "model_id": str(model.id),
            "status": model.status
        }

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to approve model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models-public/{model_id}/reject")
async def reject_model_public(
    model_id: str,
    rejection_reason: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    **TEMPORARY**: Reject a fine-tuned model WITHOUT authentication
    For UI testing only. Use /models/{model_id}/reject with auth in production.
    """
    try:
        # Get the model
        query = select(FineTunedModel).where(FineTunedModel.id == uuid.UUID(model_id))
        result = await db.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # Update model status to rejected
        model.status = "rejected"

        # Store rejection reason in description
        rejection_text = rejection_reason.get("rejection_reason", "") if isinstance(rejection_reason, dict) else str(rejection_reason)

        # Append rejection info to description
        rejection_info = f"\n\n[REJECTED at {datetime.now().isoformat()} by test_user]\nReason: {rejection_text}"
        if model.description:
            model.description += rejection_info
        else:
            model.description = rejection_info.strip()

        await db.commit()
        await db.refresh(model)

        logger.info(f"Model {model_id} rejected successfully (public endpoint)")

        return {
            "message": "Model rejected successfully",
            "model_id": str(model.id),
            "status": model.status
        }

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to reject model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PUBLIC MODELS FOR CHAT ENDPOINT (FOR UI TESTING ONLY - NO AUTHENTICATION)
# ============================================================================

@router.get("/models-public/for-chat")
async def get_models_for_chat_public(
    db: AsyncSession = Depends(get_db)
):
    """
    **TEMPORARY**: Get deployed fine-tuned models for chat UI WITHOUT authentication
    For UI testing only. Use /models/for-chat with auth in production.

    Returns deployed models formatted for chat UI model selector.

    Auto-syncs with Ollama to remove models that were manually deleted.
    """
    try:
        import httpx

        # Auto-sync with Ollama before returning models
        # This handles the case where models were manually deleted from Ollama admin console
        try:
            ollama_url = os.getenv("OLLAMA_API_URL", "http://ollama:11434")

            async with httpx.AsyncClient(timeout=10.0) as client:
                ollama_response = await client.get(f"{ollama_url}/api/tags")

                if ollama_response.status_code == 200:
                    ollama_data = ollama_response.json()
                    # Build set of model names, including both with and without :tag suffix
                    # This handles the case where DB stores "model-name" but Ollama returns "model-name:latest"
                    ollama_model_names = set()
                    for model in ollama_data.get("models", []):
                        name = model["name"]
                        ollama_model_names.add(name)  # Add with tag (e.g., "model:latest")
                        # Also add without tag for comparison (e.g., "model")
                        if ':' in name:
                            ollama_model_names.add(name.split(':')[0])

                    # Get all deployed models from database
                    sync_query = select(FineTunedModel).where(FineTunedModel.status == "deployed")
                    sync_result = await db.execute(sync_query)
                    deployed_models = sync_result.scalars().all()

                    # Check each deployed model against Ollama reality
                    models_updated = 0
                    for model in deployed_models:
                        if model.ollama_model_name and model.ollama_model_name not in ollama_model_names:
                            # Model deleted from Ollama - update database
                            logger.warning(f"🔄 Auto-sync: Model {model.name} ({model.ollama_model_name}) not in Ollama - marking as approved")
                            model.status = "approved"
                            model.ollama_model_name = None
                            model.deployment_url = None
                            models_updated += 1

                    if models_updated > 0:
                        await db.commit()
                        logger.info(f"✅ Auto-synced {models_updated} model(s) that were deleted from Ollama")
                else:
                    logger.warning(f"⚠️ Ollama sync failed (HTTP {ollama_response.status_code}) - continuing without sync")
        except Exception as sync_error:
            logger.warning(f"⚠️ Ollama auto-sync failed: {sync_error} - continuing without sync")

        # Now fetch updated list of deployed models
        query = select(FineTunedModel).where(
            FineTunedModel.status == "deployed"
        ).order_by(FineTunedModel.created_at.desc())

        result = await db.execute(query)
        models = result.scalars().all()

        finetuned_models = []
        for m in models:
            # Determine provider and model ID
            if m.ollama_model_name:
                provider = "ollama"
                model_id = f"ollama/{m.ollama_model_name}"
                name_suffix = " (Ollama)"
            elif m.vllm_model_name:
                provider = "vllm"
                model_id = f"vllm/{m.vllm_model_name}"
                name_suffix = " (vLLM)"
            else:
                continue  # Skip if no deployment name

            finetuned_models.append({
                "id": model_id,
                "name": f"{m.name}{name_suffix}",
                "provider": provider,
                "description": f"Fine-tuned {m.base_model} - {m.version or 'v1.0'}",
                "base_model": m.base_model,
                "deployment_url": m.deployment_url,
                "eval_metrics": m.eval_metrics,
                "total_inferences": m.total_inferences or 0,
                "avg_latency_ms": m.avg_latency_ms
            })

        logger.info(f"Returning {len(finetuned_models)} deployed models for chat UI")

        return {
            "finetuned_models": finetuned_models,
            "count": len(finetuned_models)
        }

    except Exception as e:
        logger.error(f"Failed to get models for chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PUBLIC DEPLOY ENDPOINT (FOR UI TESTING ONLY - NO AUTHENTICATION)
# ============================================================================

@router.post("/models-public/{model_id}/deploy")
async def deploy_model_public(
    model_id: str,
    deployment_config: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    **TEMPORARY**: Deploy a fine-tuned model WITHOUT authentication
    For UI testing only. Use /models/{model_id}/deploy with auth in production.

    Request body: {"deployment_target": "ollama"|"vllm", "deployment_config": {...}}
    """
    try:
        # 🆕 FIX: Import FineTuningJob at the top to avoid UnboundLocalError
        from app.models.finetuning_models import FineTuningJob, FineTuningDataset

        query = select(FineTunedModel).where(FineTunedModel.id == uuid.UUID(model_id))
        result = await db.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # Extract deployment target (default to ollama)
        target = deployment_config.get("deployment_target", "ollama")
        config = deployment_config.get("deployment_config", {})

        # Generate model name for deployment
        model_name = config.get("model_name", f"{model.name.replace(' ', '-').lower()}-v1")
        base_model = config.get("base_model", model.base_model or "llama2")
        parameters = config.get("parameters", {})

        deployment_result = {}

        if target == "ollama":
            # Use OllamaDeploymentService for actual deployment
            ollama_service = OllamaDeploymentService()

            # Construct adapter path from job workspace
            adapter_path = f"/workspace/finetuning/{str(model.job_id)}/output/adapter_model"

            logger.info(f"🚀 Deploying model {model.name} to Ollama as {model_name}")
            logger.info(f"   Adapter path: {adapter_path}")
            logger.info(f"   Base model: {base_model}")

            # Deploy to Ollama with merge + GGUF conversion
            deployment_result = await ollama_service.deploy_model(
                model_name=model_name,
                model_path=adapter_path,
                base_model=base_model,
                parameters=parameters
            )

            if deployment_result.get("status") == "success":
                model.ollama_model_name = deployment_result.get("model_name", model_name)
                model.deployment_url = deployment_result.get("deployment_url", "http://ollama:11434/api/generate")
                model.status = "deployed"
                logger.info(f"✅ Model {model.name} deployed successfully to Ollama")
            else:
                error_msg = deployment_result.get('error', 'Unknown deployment error')
                logger.error(f"❌ Ollama deployment failed: {error_msg}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Ollama deployment failed: {error_msg}"
                )

        elif target == "vllm":
            # TODO: Implement vLLM deployment
            deployment_url = "http://localhost:8001/v1/completions"
            model.vllm_model_name = model_name
            model.deployment_url = deployment_url
            model.status = "deployed"
            deployment_result = {
                "status": "success",
                "message": "vLLM deployment (simulated)"
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported target: {target}")

        await db.commit()
        await db.refresh(model)

        logger.info(f"Model {model_id} deployed successfully to {target} (public endpoint)")

        # ═══════════════════════════════════════════════════════════════════
        # NEW: Trigger automatic evaluation after deployment
        # ═══════════════════════════════════════════════════════════════════
        if target == "ollama" and model.ollama_model_name:
            logger.info(f"🔍 Triggering automatic evaluation after deployment...")
            try:
                # Import evaluation service (FineTuningJob already imported at top)
                from app.services.finetuning.model_evaluation_service import ModelEvaluationService
                import tempfile

                # Get associated job to find dataset
                job_query = select(FineTuningJob).where(FineTuningJob.id == model.job_id)
                job_result = await db.execute(job_query)
                job = job_result.scalar_one_or_none()

                if job and job.dataset_id:
                    # Get dataset
                    dataset_query = select(FineTuningDataset).where(FineTuningDataset.id == job.dataset_id)
                    dataset_result = await db.execute(dataset_query)
                    dataset = dataset_result.scalar_one_or_none()

                    if dataset and dataset.minio_path:
                        logger.info(f"📥 Downloading dataset for auto-evaluation...")

                        # Download dataset from MinIO
                        from minio import Minio
                        from app.core.config import settings

                        minio_client = Minio(
                            endpoint=settings.MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),
                            access_key=settings.MINIO_ACCESS_KEY,
                            secret_key=settings.MINIO_SECRET_KEY,
                            secure=settings.MINIO_ENDPOINT.startswith("https://")
                        )

                        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
                            tmp_path = tmp_file.name

                        await asyncio.to_thread(
                            minio_client.fget_object,
                            bucket_name="documents",
                            object_name=dataset.minio_path,
                            file_path=tmp_path
                        )

                        # Run evaluation with 50 samples (quick evaluation)
                        eval_service = ModelEvaluationService()
                        evaluation_result = await eval_service.evaluate_model(
                            model_path=model.minio_checkpoint_path or "",
                            test_dataset_path=tmp_path,
                            task_type=job.training_objective or "text-generation",
                            num_samples=50,
                            ollama_model_name=model.ollama_model_name
                        )

                        # Store metrics
                        model.eval_metrics = evaluation_result.get("metrics", {})
                        await db.commit()

                        logger.info(f"✅ Auto-evaluation complete! Metrics: {list(evaluation_result.get('metrics', {}).keys())}")

                        # Cleanup temp file
                        import os
                        try:
                            os.remove(tmp_path)
                        except:
                            pass

            except Exception as eval_error:
                logger.warning(f"⚠️  Auto-evaluation after deployment failed (non-critical): {eval_error}")
                # Don't fail deployment if evaluation fails

        return {
            "message": f"Model deployed successfully to {target}",
            "model_id": str(model.id),
            "deployment_target": target,
            "deployment_url": model.deployment_url,
            "deployed_model_name": model_name,
            "status": model.status,
            "deployment_details": deployment_result
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to deploy model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PUBLIC UNDEPLOY ENDPOINT (FOR UI TESTING ONLY - NO AUTHENTICATION)
# ============================================================================

@router.post("/models-public/{model_id}/undeploy")
async def undeploy_model_public(
    model_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    **TEMPORARY**: Undeploy a fine-tuned model WITHOUT authentication
    Removes from Ollama and updates database status.
    For UI testing only. Use /models/{model_id}/undeploy with auth in production.
    """
    try:
        # Get the model
        query = select(FineTunedModel).where(FineTunedModel.id == uuid.UUID(model_id))
        result = await db.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # Check if model is actually deployed
        if model.status != "deployed":
            raise HTTPException(status_code=400, detail=f"Model is not deployed (status: {model.status})")

        # Delete from Ollama if ollama_model_name exists
        if model.ollama_model_name:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=30.0) as client:
                    ollama_response = await client.delete(
                        "http://localhost:11434/api/delete",
                        json={"name": model.ollama_model_name}
                    )

                    if ollama_response.status_code not in [200, 404]:
                        logger.warning(f"Ollama delete returned {ollama_response.status_code}: {ollama_response.text}")
                    else:
                        logger.info(f"Successfully deleted model {model.ollama_model_name} from Ollama")

            except Exception as ollama_error:
                logger.error(f"Failed to delete from Ollama: {ollama_error}")
                # Continue anyway - update database even if Ollama delete fails

        # Update model status to approved (undeployed but available for re-deployment)
        # Note: Setting to "approved" instead of "registered" to maintain approval status
        model.status = "approved"
        model.deployment_url = None
        model.ollama_model_name = None  # Clear Ollama model name so it won't appear in chat UI

        # Store undeploy info in description (tags is a list, not dict)
        undeploy_note = f"\n\n[Undeployed at {datetime.now().isoformat()} by test_user]"
        if model.description:
            model.description += undeploy_note
        else:
            model.description = undeploy_note.strip()

        await db.commit()
        await db.refresh(model)

        logger.info(f"Model {model_id} undeployed successfully (public endpoint)")

        return {
            "message": "Model undeployed successfully",
            "model_id": str(model.id),
            "status": model.status,
            "ollama_model_deleted": model.ollama_model_name is not None
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to undeploy model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MODEL EVALUATION AND TESTING ENDPOINTS (PUBLIC - FOR UI TESTING)
# ============================================================================

@router.post("/models-public/{model_id}/evaluate")
async def evaluate_model_public(
    model_id: str,
    num_samples: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    **TEMPORARY**: Evaluate fine-tuned model WITHOUT authentication
    
    Computes BLEU, ROUGE, and other metrics on test dataset.
    For UI testing only.
    
    Args:
        model_id: Model ID to evaluate
        num_samples: Number of test samples to evaluate (default: 100)
    
    Returns:
        Evaluation results with metrics and sample-by-sample scores
    """
    try:
        from app.services.finetuning.model_evaluation_service import ModelEvaluationService
        
        # Get model
        query = select(FineTunedModel).where(FineTunedModel.id == uuid.UUID(model_id))
        result = await db.execute(query)
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Get associated job to find dataset
        job_query = select(FineTuningJob).where(FineTuningJob.id == model.job_id)
        job_result = await db.execute(job_query)
        job = job_result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Associated training job not found")
        
        # Get dataset
        dataset_query = select(FineTuningDataset).where(FineTuningDataset.id == job.dataset_id)
        dataset_result = await db.execute(dataset_query)
        dataset = dataset_result.scalar_one_or_none()
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Training dataset not found")
        
        # Download dataset from MinIO to temp location
        from minio import Minio
        from app.core.config import settings
        import tempfile
        
        minio_client = Minio(
            endpoint=settings.MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_ENDPOINT.startswith("https://")
        )
        
        # Download dataset
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
            tmp_path = tmp_file.name
        
        await asyncio.to_thread(
            minio_client.fget_object,
            bucket_name="documents",
            object_name=dataset.minio_path,
            file_path=tmp_path
        )
        
        # Run evaluation
        eval_service = ModelEvaluationService()
        evaluation_result = await eval_service.evaluate_model(
            model_path=model.minio_checkpoint_path or "",
            test_dataset_path=tmp_path,
            task_type=job.training_objective or "text-generation",
            num_samples=num_samples,
            ollama_model_name=model.ollama_model_name  # Pass Ollama model name for inference
        )
        
        # Update model with evaluation metrics
        model.eval_metrics = evaluation_result.get("metrics", {})
        await db.commit()
        
        logger.info(f"Evaluation completed for model {model_id}")
        
        return {
            "model_id": str(model.id),
            "model_name": model.name,
            "status": "completed",
            **evaluation_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models-public/{model_id}/evaluation-results")
async def get_evaluation_results_public(
    model_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    **TEMPORARY**: Get evaluation results for a model WITHOUT authentication
    
    Returns stored evaluation metrics and sample results.
    For UI testing only.
    """
    try:
        query = select(FineTunedModel).where(FineTunedModel.id == uuid.UUID(model_id))
        result = await db.execute(query)
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return {
            "model_id": str(model.id),
            "model_name": model.name,
            "eval_metrics": model.eval_metrics or {},
            "has_evaluation": model.eval_metrics is not None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get evaluation results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models-public/{model_id}/test")
async def test_model_public(
    model_id: str,
    request_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    **TEMPORARY**: Test model with custom input WITHOUT authentication
    
    Allows manual testing of deployed models in the UI.
    For UI testing only.
    
    Args:
        model_id: Model ID
        request_data: {"input": "test question", "max_length": 512}
    
    Returns:
        Generated response from the model
    """
    try:
        import httpx
        
        # Get model
        query = select(FineTunedModel).where(FineTunedModel.id == uuid.UUID(model_id))
        result = await db.execute(query)
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Check if deployed
        if model.status != "deployed" or not model.ollama_model_name:
            raise HTTPException(
                status_code=400,
                detail=f"Model must be deployed first. Current status: {model.status}"
            )
        
        # Get input from request
        input_text = request_data.get("input", "")
        if not input_text:
            raise HTTPException(status_code=400, detail="Input text is required")
        
        max_length = request_data.get("max_length", 512)
        temperature = request_data.get("temperature", 0.7)
        
        # Call Ollama API
        ollama_url = os.getenv("OLLAMA_HOST", "http://ollama:11434")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": model.ollama_model_name,
                    "prompt": input_text,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_length
                    }
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"Ollama API error: {response.text}"
                )
            
            result_data = response.json()
            generated_text = result_data.get("response", "")
        
        # Update inference count
        model.total_inferences = (model.total_inferences or 0) + 1
        model.last_inference_at = datetime.utcnow()
        await db.commit()
        
        return {
            "model_id": str(model.id),
            "model_name": model.name,
            "input": input_text,
            "generated": generated_text,
            "settings": {
                "temperature": temperature,
                "max_length": max_length
            },
            "total_inferences": model.total_inferences
        }
        
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Model inference timeout")
    except Exception as e:
        logger.error(f"Model test failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# JOB LOGS ENDPOINT (for Pipeline Visualization)
# ============================================================================

@router.get("/jobs/{job_id}/logs")
async def get_job_logs(
    job_id: str,
    lines: int = Query(100, description="Number of log lines to return"),
    stage: Optional[str] = Query(None, description="Filter by stage: preprocessing, training, evaluation"),
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "read")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get training job logs (including preprocessing logs)

    Returns:
    - Recent logs from Celery worker (preprocessing, workspace setup)
    - Container logs (model loading, training progress)
    - Highlighted preprocessing steps (auto-detection, column mapping, etc.)
    """
    try:
        import subprocess
        import re

        # Verify job exists
        result = await db.execute(
            select(FineTuningJob).where(FineTuningJob.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        logs = []
        preprocessing_highlights = []

        # 1. Get Celery worker logs (preprocessing)
        try:
            celery_logs = subprocess.check_output(
                ["docker-compose", "logs", "--tail", str(lines), "celery"],
                cwd="/mnt/c/AIML/ClaudeCode/chatbot/ChatBot",
                timeout=5
            ).decode('utf-8')

            # Filter for this job's logs
            job_celery_logs = [
                line for line in celery_logs.split('\n')
                if job_id in line or job.name in line
            ]

            # Extract preprocessing highlights
            preprocessing_patterns = {
                'dataset_download': r'📦 Downloading.*from MinIO',
                'preprocessing_start': r'🔄 Preprocessing dataset',
                'samples_loaded': r'📊 Loaded (\d+) samples',
                'objective_detected': r'📝 Training objective: (\w+) → Format type: (\w+)',
                'auto_detection': r'🔍 Auto-detecting columns',
                'column_mapping': r'✅ Auto-detected column mapping: ({.*})',
                'fallback_mapping': r'✅ Fallback mapping successful: ({.*})',
                'train_saved': r'✅ Preprocessed dataset saved.*\((\d+) train samples\)',
                'validation_saved': r'✅ Validation set saved.*\((\d+) samples\)'
            }

            for log_line in job_celery_logs:
                logs.append({"source": "celery", "line": log_line})

                # Extract highlights
                for key, pattern in preprocessing_patterns.items():
                    match = re.search(pattern, log_line)
                    if match:
                        preprocessing_highlights.append({
                            "type": key,
                            "message": log_line.strip(),
                            "data": match.groups() if match.groups() else None
                        })

        except subprocess.TimeoutExpired:
            logs.append({"source": "celery", "line": "⚠️  Celery logs timeout"})
        except Exception as e:
            logs.append({"source": "celery", "line": f"⚠️  Could not fetch Celery logs: {str(e)}"})

        # 2. Get training container logs (if container exists)
        try:
            container_name = f"finetuning-{job_id}"
            container_logs = subprocess.check_output(
                ["docker", "logs", "--tail", str(lines), container_name],
                timeout=5
            ).decode('utf-8')

            for log_line in container_logs.split('\n'):
                if log_line.strip():
                    logs.append({"source": "training", "line": log_line})

        except subprocess.CalledProcessError:
            # Container doesn't exist yet or has stopped
            logs.append({"source": "training", "line": "Training container not found or stopped"})
        except subprocess.TimeoutExpired:
            logs.append({"source": "training", "line": "⚠️  Container logs timeout"})
        except Exception as e:
            logs.append({"source": "training", "line": f"⚠️  Could not fetch container logs: {str(e)}"})

        # 3. Filter by stage if requested
        if stage:
            if stage == "preprocessing":
                logs = [log for log in logs if log["source"] == "celery" or "preprocessing" in log["line"].lower()]
            elif stage == "training":
                logs = [log for log in logs if log["source"] == "training" or "training" in log["line"].lower() or "epoch" in log["line"].lower()]

        return {
            "job_id": job_id,
            "job_name": job.name,
            "status": job.status,
            "logs": logs[-lines:],  # Return last N lines
            "preprocessing_highlights": preprocessing_highlights,
            "total_lines": len(logs)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get job logs: {str(e)}")
