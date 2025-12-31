"""
Fine-Tuning Service - Main Orchestration Service

This service manages the entire fine-tuning lifecycle:
- Job creation and configuration
- Dataset validation and preprocessing
- Training job submission (Celery/Ray)
- Progress monitoring
- Model registration

Modular Design:
- Trainer selection based on method (via factory pattern)
- Async job submission with Celery
- Real-time progress tracking via WebSocket
- MLflow integration for experiment tracking
"""

from typing import Optional, Dict, Any, List
from uuid import UUID
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.models.finetuning_models import (
    FineTuningJob,
    FineTuningDataset,
    FineTunedModel,
    TrainingMetric,
    get_default_hyperparameters
)
from app.services.finetuning.dataset_preprocessor import DatasetPreprocessor

logger = logging.getLogger(__name__)


class FineTuningService:
    """
    Main service for managing fine-tuning operations

    This service coordinates all fine-tuning activities and provides
    a high-level API for the REST endpoints.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize fine-tuning service

        Args:
            db: Async database session
        """
        self.db = db
        self.preprocessor = DatasetPreprocessor()
        logger.info("Initialized FineTuningService")

    # ========================================================================
    # Dataset Management
    # ========================================================================

    async def create_dataset(
        self,
        name: str,
        filename: str,
        file_path: str,
        file_size: int,
        format_type: str,
        columns: Dict[str, str],
        uploaded_by: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        description: Optional[str] = None
    ) -> FineTuningDataset:
        """
        Create a new dataset entry

        Args:
            name: Dataset name
            filename: Original filename
            file_path: Path in MinIO
            file_size: File size in bytes
            format_type: Dataset format
            columns: Column mapping
            uploaded_by: User ID who uploaded
            project_id: Project ID
            description: Optional description

        Returns:
            Created dataset
        """
        dataset = FineTuningDataset(
            name=name,
            filename=filename,
            minio_path=file_path,
            file_size=file_size,
            format_type=format_type,
            columns=columns,
            uploaded_by=uploaded_by,
            project_id=project_id,
            description=description,
            preprocessing_status="pending"
        )

        self.db.add(dataset)
        await self.db.commit()
        await self.db.refresh(dataset)

        logger.info(f"Created dataset: {dataset.id} - {name}")
        return dataset

    async def validate_dataset(self, dataset_id: UUID) -> Dict[str, Any]:
        """
        Validate a dataset

        Args:
            dataset_id: Dataset ID to validate

        Returns:
            Validation results
        """
        # Use SQLAlchemy 2.x async syntax
        from sqlalchemy import select
        import tempfile
        from pathlib import Path
        from minio import Minio
        from app.core.config import settings

        stmt = select(FineTuningDataset).where(FineTuningDataset.id == dataset_id)
        result = await self.db.execute(stmt)
        dataset = result.scalar_one_or_none()

        if not dataset:
            raise ValueError(f"Dataset not found: {dataset_id}")

        # Download file from MinIO to temporary location
        minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )

        # Get file extension
        file_extension = Path(dataset.minio_path).suffix or '.csv'

        # Download to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_path = tmp_file.name

        try:
            # Download from MinIO
            minio_client.fget_object(
                bucket_name="documents",
                object_name=dataset.minio_path,
                file_path=tmp_path
            )

            # Run validation using temp local file
            validation_results = self.preprocessor.validate_dataset(
                df=self.preprocessor.load_dataset(tmp_path),
                format_type=dataset.format_type,
                columns=dataset.columns
            )

            # Update dataset with validation results
            dataset.is_valid = validation_results["is_valid"]

            # Build comprehensive error message with suggestions
            all_messages = []

            if validation_results.get("errors"):
                all_messages.extend(validation_results["errors"])

            if validation_results.get("warnings"):
                all_messages.extend(validation_results["warnings"])

            if validation_results.get("suggestions"):
                all_messages.extend(validation_results["suggestions"])

            dataset.validation_errors = all_messages
            dataset.num_samples = validation_results.get("num_samples")

            # If auto-fix was applied and dataset is now valid, update the columns
            diagnostics = validation_results.get("diagnostics", {})
            if diagnostics.get("auto_fix_applied") and validation_results["is_valid"]:
                # Save the auto-detected column mapping
                dataset.columns = diagnostics.get("applied_mapping", dataset.columns)
                logger.info(f"Auto-detected and saved column mapping: {dataset.columns}")

            # Get sample preview using temp file (only if valid)
            if validation_results["is_valid"]:
                try:
                    sample_preview = self.preprocessor.get_sample_preview(
                        dataset_path=tmp_path,
                        format_type=dataset.format_type,
                        columns=dataset.columns,
                        num_samples=5
                    )
                    dataset.sample_rows = [s["formatted"] for s in sample_preview]
                except Exception as e:
                    logger.warning(f"Failed to generate sample preview: {e}")
                    dataset.sample_rows = []

            # Mark preprocessing as completed
            dataset.preprocessing_status = "completed"

            # Use async commit and refresh
            await self.db.commit()
            await self.db.refresh(dataset)

            # Log comprehensive result
            if validation_results["is_valid"]:
                logger.info(f"✅ Validated dataset {dataset_id}: VALID - {validation_results.get('num_samples')} samples")
                if diagnostics.get("auto_fix_applied"):
                    logger.info(f"   Auto-fix applied: {diagnostics.get('applied_mapping')}")
            else:
                logger.warning(f"❌ Validated dataset {dataset_id}: INVALID")
                logger.warning(f"   Errors: {validation_results.get('errors')}")
                logger.warning(f"   Suggestions: {validation_results.get('suggestions')}")

            return validation_results

        finally:
            # Clean up temporary file
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to delete temp file {tmp_path}: {e}")

    async def list_datasets(
        self,
        project_id: Optional[UUID] = None,
        uploaded_by: Optional[UUID] = None,
        format_type: Optional[str] = None
    ) -> List[FineTuningDataset]:
        """
        List datasets with optional filtering

        Args:
            project_id: Filter by project
            uploaded_by: Filter by uploader
            format_type: Filter by format type

        Returns:
            List of datasets
        """
        query = self.db.query(FineTuningDataset)

        if project_id:
            query = query.filter(FineTuningDataset.project_id == project_id)
        if uploaded_by:
            query = query.filter(FineTuningDataset.uploaded_by == uploaded_by)
        if format_type:
            query = query.filter(FineTuningDataset.format_type == format_type)

        return query.order_by(FineTuningDataset.uploaded_at.desc()).all()

    # ========================================================================
    # Job Management
    # ========================================================================

    async def create_job(
        self,
        name: str,
        base_model: str,
        finetuning_method: str,
        training_objective: str,
        dataset_id: UUID,
        hyperparameters: Dict[str, Any],
        quantization: Optional[str] = "4bit",
        train_split: float = 0.8,
        created_by: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        description: Optional[str] = None,
        department: Optional[str] = None,
        team: Optional[str] = None
    ) -> FineTuningJob:
        """
        Create a fine-tuning job

        Args:
            name: Job name
            base_model: Base model identifier
            finetuning_method: Method (peft, sft, rlhf-ppo, rlhf-grpo)
            training_objective: Objective (qa, classification, etc.)
            dataset_id: Dataset to use
            hyperparameters: Training hyperparameters
            quantization: Quantization type
            train_split: Train/val split ratio
            created_by: User ID
            project_id: Project ID
            description: Optional description

        Returns:
            Created job
        """
        # Validate dataset exists (async)
        from sqlalchemy import select
        stmt = select(FineTuningDataset).where(FineTuningDataset.id == dataset_id)
        result = await self.db.execute(stmt)
        dataset = result.scalar_one_or_none()

        if not dataset:
            raise ValueError(f"Dataset not found: {dataset_id}")

        # Skip validation check - newly uploaded datasets won't be validated yet
        # Validation happens asynchronously after upload
        # if not dataset.is_valid:
        #     raise ValueError(f"Dataset is not valid: {dataset_id}")

        # Merge with default hyperparameters
        default_params = get_default_hyperparameters(finetuning_method)
        final_hyperparameters = {**default_params, **hyperparameters}

        # Create job
        job = FineTuningJob(
            name=name,
            base_model=base_model,
            quantization=quantization,
            finetuning_method=finetuning_method,
            training_objective=training_objective,
            dataset_id=dataset_id,
            train_split=train_split,
            hyperparameters=final_hyperparameters,
            created_by=created_by,
            project_id=project_id,
            description=description,
            department=department,
            team=team,
            status="pending",
            progress=0.0
        )

        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        logger.info(f"Created fine-tuning job: {job.id} - {name}")
        return job

    async def submit_job(self, job_id: UUID) -> Dict[str, Any]:
        """
        Submit job to training queue (Celery)

        Args:
            job_id: Job ID to submit

        Returns:
            Submission result with task ID
        """
        from sqlalchemy import select

        # Use async query
        result = await self.db.execute(
            select(FineTuningJob).filter(FineTuningJob.id == job_id)
        )
        job = result.scalar_one_or_none()

        if not job:
            raise ValueError(f"Job not found: {job_id}")

        if job.status != "pending":
            raise ValueError(f"Job is not in pending status: {job.status}")

        # Submit to Celery for async execution
        from app.tasks.finetuning_tasks import run_finetuning_job
        task = run_finetuning_job.delay(str(job_id))

        # Store Celery task ID
        job.celery_task_id = task.id
        job.status = "queued"
        job.queued_at = datetime.utcnow()
        await self.db.commit()

        logger.info(f"Submitted job {job_id} to Celery (task: {task.id})")

        return {
            "job_id": str(job_id),
            "celery_task_id": task.id,
            "status": "queued",
            "message": "Job submitted to training queue"
        }

    async def get_job(self, job_id: UUID) -> Optional[FineTuningJob]:
        """Get job by ID"""
        return self.db.query(FineTuningJob).filter(
            FineTuningJob.id == job_id
        ).first()

    async def list_jobs(
        self,
        status: Optional[str] = None,
        project_id: Optional[UUID] = None,
        created_by: Optional[UUID] = None,
        finetuning_method: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        List jobs with pagination and filtering

        Args:
            status: Filter by status
            project_id: Filter by project
            created_by: Filter by creator
            finetuning_method: Filter by method
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Dictionary with jobs and pagination info
        """
        query = self.db.query(FineTuningJob)

        if status:
            query = query.filter(FineTuningJob.status == status)
        if project_id:
            query = query.filter(FineTuningJob.project_id == project_id)
        if created_by:
            query = query.filter(FineTuningJob.created_by == created_by)
        if finetuning_method:
            query = query.filter(FineTuningJob.finetuning_method == finetuning_method)

        total = query.count()

        # Pagination
        offset = (page - 1) * page_size
        jobs = query.order_by(FineTuningJob.created_at.desc()).offset(offset).limit(page_size).all()

        return {
            "jobs": jobs,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    async def cancel_job(self, job_id: UUID) -> Dict[str, str]:
        """
        Cancel a running job

        Args:
            job_id: Job ID to cancel

        Returns:
            Cancellation result
        """
        job = await self.get_job(job_id)

        if not job:
            raise ValueError(f"Job not found: {job_id}")

        if job.status not in ["pending", "queued", "running"]:
            raise ValueError(f"Job cannot be cancelled in status: {job.status}")

        # TODO: Implement Celery task revocation
        # if job.celery_task_id:
        #     from celery import current_app
        #     current_app.control.revoke(job.celery_task_id, terminate=True)

        job.status = "cancelled"
        job.error_message = "Cancelled by user"
        self.db.commit()

        logger.info(f"Cancelled job {job_id}")

        return {
            "job_id": str(job_id),
            "status": "cancelled",
            "message": "Job cancelled successfully"
        }

    # ========================================================================
    # Metrics Management
    # ========================================================================

    async def add_metric(
        self,
        job_id: UUID,
        epoch: Optional[int],
        step: int,
        metrics: Dict[str, float]
    ) -> TrainingMetric:
        """
        Add a training metric data point

        Args:
            job_id: Job ID
            epoch: Current epoch
            step: Current step
            metrics: Dictionary of metrics

        Returns:
            Created metric
        """
        metric = TrainingMetric(
            job_id=job_id,
            epoch=epoch,
            step=step,
            train_loss=metrics.get("train_loss"),
            eval_loss=metrics.get("eval_loss"),
            learning_rate=metrics.get("learning_rate"),
            gpu_utilization=metrics.get("gpu_utilization"),
            gpu_memory_allocated=metrics.get("gpu_memory_allocated"),
            samples_per_second=metrics.get("samples_per_second"),
            tokens_per_second=metrics.get("tokens_per_second"),
            custom_metrics=metrics.get("custom_metrics")
        )

        self.db.add(metric)

        # Also update job's current metrics
        job = await self.get_job(job_id)
        if job:
            job.current_epoch = epoch
            job.current_step = step
            job.train_loss = metrics.get("train_loss")
            job.eval_loss = metrics.get("eval_loss")

            # Update progress based on steps
            if job.total_steps:
                job.progress = min(1.0, step / job.total_steps)

        self.db.commit()
        self.db.refresh(metric)

        return metric

    async def get_metrics(
        self,
        job_id: UUID,
        limit: int = 1000
    ) -> List[TrainingMetric]:
        """
        Get training metrics for a job

        Args:
            job_id: Job ID
            limit: Maximum number of metrics to return

        Returns:
            List of metrics
        """
        return self.db.query(TrainingMetric).filter(
            TrainingMetric.job_id == job_id
        ).order_by(TrainingMetric.timestamp.desc()).limit(limit).all()

    # ========================================================================
    # Utility Methods
    # ========================================================================

    async def get_base_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available base models

        Returns:
            List of base model information
        """
        # This would typically query Ollama or HuggingFace
        # For now, return a static list
        return [
            {
                "id": "Qwen/Qwen2.5-7B-Instruct",
                "name": "Qwen 2.5 7B Instruct",
                "size": "7B",
                "parameters": "7 billion",
                "quantization_options": ["4bit", "8bit", "none"],
                "recommended_vram": "12GB (4-bit), 16GB (8-bit), 28GB (full)"
            },
            {
                "id": "meta-llama/Llama-2-7b-hf",
                "name": "Llama 2 7B",
                "size": "7B",
                "parameters": "7 billion",
                "quantization_options": ["4bit", "8bit", "none"],
                "recommended_vram": "12GB (4-bit), 16GB (8-bit), 28GB (full)"
            },
            {
                "id": "mistralai/Mistral-7B-Instruct-v0.2",
                "name": "Mistral 7B Instruct v0.2",
                "size": "7B",
                "parameters": "7 billion",
                "quantization_options": ["4bit", "8bit", "none"],
                "recommended_vram": "12GB (4-bit), 16GB (8-bit), 28GB (full)"
            }
        ]
