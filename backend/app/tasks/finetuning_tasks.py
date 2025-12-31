"""
Fine-Tuning Celery Tasks

Production-ready distributed training tasks with:
- GPU allocation and management
- Progress tracking and database updates
- Checkpoint storage to MinIO
- Comprehensive error handling
- Automatic cleanup
"""

import asyncio
import glob
import json
import logging
import os
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from uuid import UUID

from celery import Task
from minio import Minio
from minio.error import S3Error
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import text

from app.celery_app import celery_app
from app.core.database import sync_engine
from app.models.finetuning_models import FineTuningJob, TrainingMetric, FineTuningDataset
from app.models.database import User

# Create sync session for Celery tasks (Celery tasks are synchronous)
SessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)
from app.services.finetuning.finetuning_sandbox_manager import FineTuningSandboxManager
from app.services.finetuning.gpu_pool_manager import GPUPoolManager
from app.services.finetuning.trainer_factory import TrainerFactory
from app.services.minio_path_builder import MinIOPathBuilder
from app.core.config import settings

# Import Prometheus metrics from shared metrics module
# This allows both the backend (/metrics endpoint) and celery worker to use the same metrics
from app.metrics.finetuning_metrics import (
    finetuning_train_loss,
    finetuning_eval_loss,
    finetuning_current_epoch,
    finetuning_progress_percent,
    finetuning_total_steps,
    finetuning_job_status,
)

logger = logging.getLogger(__name__)


def update_prometheus_metrics(job: FineTuningJob):
    """
    Update Prometheus metrics for a training job.

    This function exports current training metrics to Prometheus so they can be
    visualized in Grafana dashboards in real-time.

    Args:
        job: FineTuningJob instance with current training state
    """
    try:
        job_id_str = str(job.id)
        job_name = job.name or "unknown"
        model = job.base_model or "unknown"

        # Update training loss
        if job.train_loss is not None:
            finetuning_train_loss.labels(
                job_id=job_id_str,
                job_name=job_name,
                model=model
            ).set(float(job.train_loss))

        # Update eval loss
        if job.eval_loss is not None:
            finetuning_eval_loss.labels(
                job_id=job_id_str,
                job_name=job_name,
                model=model
            ).set(float(job.eval_loss))

        # Update current epoch
        if job.current_epoch is not None:
            finetuning_current_epoch.labels(
                job_id=job_id_str,
                job_name=job_name
            ).set(float(job.current_epoch))

        # Update progress
        if job.progress is not None:
            finetuning_progress_percent.labels(
                job_id=job_id_str,
                job_name=job_name
            ).set(float(job.progress))

        # Update total steps
        if job.total_steps is not None:
            finetuning_total_steps.labels(
                job_id=job_id_str,
                job_name=job_name
            ).set(float(job.total_steps))

        # Update job status
        status = job.status or "unknown"
        status_value = 1.0 if status == "running" else 0.0
        finetuning_job_status.labels(
            job_id=job_id_str,
            job_name=job_name,
            status=status
        ).set(status_value)

        logger.debug(f"Updated Prometheus metrics for job {job_id_str}")

    except Exception as e:
        # Don't fail the task if metrics update fails
        logger.warning(f"Failed to update Prometheus metrics: {e}")


class FineTuningTask(Task):
    """Base task with progress tracking and error handling"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        job_id = args[0] if args else None
        if job_id:
            with SessionLocal() as db:
                job = db.query(FineTuningJob).filter(
                    FineTuningJob.id == UUID(job_id)
                ).first()
                if job:
                    job.status = "failed"
                    job.error_message = str(exc)
                    job.training_end_time = datetime.now(timezone.utc)
                    db.commit()
                    logger.error(f"Training job {job_id} failed: {exc}")

    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success"""
        job_id = args[0] if args else None
        if job_id:
            logger.info(f"Training job {job_id} completed successfully")


def update_job_progress(
    db: Session,
    job_id: UUID,
    progress: float,
    current_epoch: Optional[int] = None,
    current_step: Optional[int] = None,
    train_loss: Optional[float] = None,
    eval_loss: Optional[float] = None,
    learning_rate: Optional[float] = None,
    status: Optional[str] = None
):
    """Update job progress in database"""
    try:
        job = db.query(FineTuningJob).filter(
            FineTuningJob.id == job_id
        ).first()

        if not job:
            logger.error(f"Job {job_id} not found for progress update")
            return

        # Update progress fields
        job.progress = progress
        if current_epoch is not None:
            job.current_epoch = current_epoch
        if current_step is not None:
            job.current_step = current_step
        if train_loss is not None:
            job.train_loss = train_loss
        if eval_loss is not None:
            job.eval_loss = eval_loss
        if learning_rate is not None:
            job.learning_rate = learning_rate
        if status:
            job.status = status

        db.commit()
        logger.debug(f"Updated job {job_id} progress: {progress}%")

    except Exception as e:
        logger.error(f"Failed to update job progress: {e}")
        db.rollback()


def update_training_stage(
    db: Session,
    job_id: UUID,
    stage: str,
    stage_details: Optional[Dict[str, Any]] = None
):
    """
    Update the current training pipeline stage

    Args:
        db: Database session
        job_id: Job ID
        stage: New stage (queued, setup, tokenizer_load, model_download, model_load, dataset_prep, training, checkpoint_save, completed, failed)
        stage_details: Stage-specific metadata (e.g., download progress, current file, substep info)
    """
    try:
        job = db.query(FineTuningJob).filter(
            FineTuningJob.id == job_id
        ).first()

        if not job:
            logger.error(f"Job {job_id} not found for stage update")
            return

        # Mark previous stage as completed
        if job.training_stage != stage:
            job.stage_completed_at = datetime.utcnow()

        # Update to new stage
        job.training_stage = stage
        job.stage_started_at = datetime.utcnow()

        # Update stage details if provided
        if stage_details is not None:
            job.stage_details = stage_details

        db.commit()
        logger.info(f"📍 Job {job_id} stage updated: {stage}")
        if stage_details:
            logger.debug(f"   Stage details: {stage_details}")

    except Exception as e:
        logger.error(f"Failed to update training stage: {e}")
        db.rollback()


def add_debug_log(
    db: Session,
    job_id: UUID,
    stage: str,
    message: str,
    log_level: str = "INFO",
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Add a timestamped debug log entry to the job's debug_log array

    Args:
        db: Database session
        job_id: Job ID
        stage: Pipeline stage (training, merge, convert, deploy, evaluation)
        message: Log message
        log_level: Log level (INFO, WARNING, ERROR)
        metadata: Optional metadata dict
    """
    try:
        job = db.query(FineTuningJob).filter(
            FineTuningJob.id == job_id
        ).first()

        if not job:
            logger.error(f"Job {job_id} not found for debug log")
            return

        # Create log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "stage": stage,
            "level": log_level,
            "message": message
        }

        if metadata:
            log_entry["metadata"] = metadata

        # Append to debug_log array (PostgreSQL text[] array - stores JSON strings)
        if job.debug_log is None:
            job.debug_log = []

        # Encode log entry as JSON string before adding to text array
        current_logs = list(job.debug_log) if job.debug_log else []
        current_logs.append(json.dumps(log_entry))
        job.debug_log = current_logs

        db.commit()
        logger.debug(f"📝 Debug log added for job {job_id}: [{stage}] {message}")

    except Exception as e:
        logger.error(f"Failed to add debug log: {e}")
        db.rollback()


def save_training_metric(
    db: Session,
    job_id: UUID,
    step: int,
    epoch: int,
    metric_type: str,
    metric_value: float,
    additional_metrics: Optional[Dict[str, Any]] = None
):
    """Save training metric to database"""
    try:
        metric = TrainingMetric(
            job_id=job_id,
            step=step,
            epoch=epoch,
            metric_type=metric_type,
            metric_value=metric_value,
            additional_metrics=additional_metrics or {}
        )
        db.add(metric)
        db.commit()

    except Exception as e:
        logger.error(f"Failed to save training metric: {e}")
        db.rollback()


def trigger_automatic_evaluation(
    db: Session,
    model_id: str,
    job: FineTuningJob,
    num_samples: int = 50
) -> bool:
    """
    Trigger automatic evaluation after model training completes

    Note: Evaluation will only work if model is deployed to Ollama.
    For now, this logs that evaluation is available but doesn't run it.
    Full automatic evaluation requires either:
    1. Auto-deploy to Ollama after training (risky - needs approval first)
    2. Checkpoint loading for evaluation (not yet implemented)

    Args:
        db: Database session
        model_id: UUID of the registered model
        job: Completed FineTuningJob instance
        num_samples: Number of samples to evaluate (default: 50 for speed)

    Returns:
        True if evaluation succeeded, False otherwise
    """
    try:
        from app.models.finetuning_models import FineTunedModel, FineTuningDataset
        from app.services.finetuning.model_evaluation_service import ModelEvaluationService
        from minio import Minio
        from app.core.config import settings
        import tempfile
        import uuid

        logger.info(f"🔍 Automatic evaluation requested for model {model_id}")

        # Get model
        model = db.query(FineTunedModel).filter(
            FineTunedModel.id == uuid.UUID(model_id)
        ).first()

        if not model:
            logger.error(f"Model {model_id} not found for evaluation")
            return False

        # Check if model is deployed
        if not model.ollama_model_name:
            logger.warning(f"⏭️  Model {model.name} is not deployed to Ollama yet.")
            logger.warning(f"   Automatic evaluation skipped - will be available after deployment.")
            logger.warning(f"   User can manually evaluate from Evaluations tab after deploying.")
            return False

        # Get dataset
        dataset = db.query(FineTuningDataset).filter(
            FineTuningDataset.id == job.dataset_id
        ).first()

        if not dataset:
            logger.error(f"Dataset not found for evaluation")
            return False

        logger.info(f"📥 Downloading test dataset from MinIO: {dataset.minio_path}")

        # Download dataset from MinIO to temp location
        minio_client = Minio(
            endpoint=settings.MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_ENDPOINT.startswith("https://")
        )

        # Download dataset
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
            tmp_path = tmp_file.name

        # Synchronous call wrapped for async environment
        def download_sync():
            minio_client.fget_object(
                bucket_name="documents",
                object_name=dataset.minio_path,
                file_path=tmp_path
            )

        # Run download in executor
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.submit(download_sync).result()

        logger.info(f"✅ Dataset downloaded to {tmp_path}")

        # Run evaluation
        logger.info(f"🧪 Running automatic evaluation with {num_samples} samples...")

        eval_service = ModelEvaluationService()

        # Wrap async evaluation in event loop
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            evaluation_result = loop.run_until_complete(
                eval_service.evaluate_model(
                    model_path=model.minio_checkpoint_path or "",
                    test_dataset_path=tmp_path,
                    task_type=job.training_objective or "text-generation",
                    num_samples=num_samples,
                    ollama_model_name=model.ollama_model_name
                )
            )
        finally:
            loop.close()

        # Store metrics in model
        model.eval_metrics = evaluation_result.get("metrics", {})
        db.commit()

        logger.info(f"✅ Automatic evaluation complete for model {model.name}")
        logger.info(f"   Metrics: {list(evaluation_result.get('metrics', {}).keys())}")

        # Cleanup temp file
        import os
        try:
            os.remove(tmp_path)
        except:
            pass

        return True

    except Exception as e:
        logger.error(f"⚠️  Automatic evaluation failed: {e}")
        logger.error(traceback.format_exc())
        # Don't fail the training job if evaluation fails
        return False


def register_finetuned_model(
    db: Session,
    job: FineTuningJob,
    checkpoint_path: str
) -> Optional[str]:
    """
    Automatically register a fine-tuned model after training completes

    This creates an entry in the finetuned_models table with:
    - Model metadata (name, version, description)
    - Link to training job
    - Checkpoint path
    - Training hyperparameters

    Args:
        db: Database session
        job: Completed FineTuningJob instance
        checkpoint_path: MinIO path to model checkpoints

    Returns:
        Model ID as string, or None if registration failed
    """
    try:
        from app.models.finetuning_models import FineTunedModel
        import uuid

        # Generate model name from job name
        model_name = f"{job.name}_model"
        version = "v1.0.0"

        # Check if model already exists for this job
        existing_model = db.query(FineTunedModel).filter(
            FineTunedModel.job_id == job.id
        ).first()

        if existing_model:
            logger.info(f"Model already registered for job {job.id}: {existing_model.id}")
            return str(existing_model.id)

        # Create new model record
        model = FineTunedModel(
            id=uuid.uuid4(),
            name=model_name,
            version=version,
            description=f"Fine-tuned {job.base_model} using {job.finetuning_method} for {job.training_objective}",
            job_id=job.id,
            base_model=job.base_model,
            finetuning_method=job.finetuning_method,
            minio_checkpoint_path=checkpoint_path,
            adapter_config=job.hyperparameters,  # Store PEFT/LoRA config
            eval_metrics={
                "final_train_loss": job.train_loss,
                "final_eval_loss": job.eval_loss,
                "total_steps": job.total_steps,
                "training_time_seconds": job.training_time_seconds
            },
            status="registered",  # Initial status
            created_by=job.created_by,
            project_id=job.project_id,
            total_inferences=0,
            tags=[job.finetuning_method, job.training_objective]
        )

        db.add(model)
        db.commit()
        db.refresh(model)

        logger.info(f"✅ Model registered: {model.name} (ID: {model.id}, version: {model.version})")
        logger.info(f"   Base model: {model.base_model}")
        logger.info(f"   Method: {model.finetuning_method}")
        logger.info(f"   Checkpoint: {checkpoint_path}")

        return str(model.id)

    except Exception as e:
        logger.error(f"Failed to register fine-tuned model: {e}")
        logger.error(traceback.format_exc())
        db.rollback()
        return None


def upload_checkpoints_to_minio(
    job_id: str,
    job_name: str,
    checkpoint_dir: str,
    department_name: str,
    team_name: str,
    project_name: str,
    username: str,
    dataset_name: str,
    bucket_name: str = "documents"
) -> Optional[str]:
    """
    Upload training checkpoints to MinIO using dataset-linked organizational path structure

    Args:
        job_id: UUID of the training job
        job_name: Human-readable job name
        checkpoint_dir: Local directory containing checkpoints
        department_name: Department name (e.g., 'Technology')
        team_name: Team name (e.g., 'Backend Development')
        project_name: Project name (e.g., 'ChatBot RAG')
        username: Username who created the job
        dataset_name: Training dataset name (for path linkage)
        bucket_name: MinIO bucket name (default: 'documents')

    Returns:
        MinIO path to main checkpoint (adapter_model.safetensors or pytorch_model.bin)
        Returns None if upload fails

    Path Structure (Dataset-Linked):
        documents/{dept}/{team}/{project}/{user}/finetuning/datasets/{dataset}/checkpoints/{job}/{job_id}/final/{type}/{filename}
        Example: documents/technology/backend-development/global/admin/finetuning/datasets/story8/checkpoints/qwen-job/uuid/final/merged_model/adapter_model.safetensors
    """
    try:
        # Initialize MinIO client
        minio_client = Minio(
            endpoint=settings.MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_ENDPOINT.startswith("https://")
        )

        # Ensure bucket exists
        if not minio_client.bucket_exists(bucket_name):
            logger.info(f"Creating MinIO bucket: {bucket_name}")
            minio_client.make_bucket(bucket_name)

        # Find checkpoint files
        checkpoint_path = Path(checkpoint_dir)
        if not checkpoint_path.exists():
            logger.error(f"Checkpoint directory not found: {checkpoint_dir}")
            return None

        # Look for checkpoint files
        checkpoint_files = []

        # Common checkpoint file patterns
        patterns = [
            "**/*.safetensors",
            "**/*.bin",
            "**/adapter_config.json",
            "**/adapter_model.safetensors",
            "**/pytorch_model.bin",
            "**/config.json",
            "**/tokenizer.json",
            "**/tokenizer_config.json",
            "**/special_tokens_map.json",
            "**/training_args.bin"
        ]

        for pattern in patterns:
            checkpoint_files.extend(checkpoint_path.glob(pattern))

        if not checkpoint_files:
            logger.warning(f"No checkpoint files found in {checkpoint_dir}")
            return None

        logger.info(f"Found {len(checkpoint_files)} checkpoint files to upload")

        # Upload each file to MinIO using organizational path structure
        uploaded_files = []
        main_checkpoint_path = None

        for local_file in checkpoint_files:
            # Determine model type based on file name
            filename = local_file.name
            if 'adapter' in filename.lower():
                model_type = 'adapter_model'
            elif 'merged' in filename.lower() or 'model.safetensors' in filename.lower():
                model_type = 'merged_model'
            else:
                model_type = 'config'

            # Build MinIO path using dataset-linked path builder
            object_name = MinIOPathBuilder.build_finetuning_checkpoint_with_dataset(
                department_name=department_name,
                team_name=team_name,
                project_name=project_name,
                username=username,
                dataset_name=dataset_name,
                job_name=job_name,
                job_id=job_id,
                checkpoint_stage="final",
                model_type=model_type,
                filename=filename
            )

            # Upload file
            logger.info(f"Uploading {filename} to MinIO: {object_name}")
            minio_client.fput_object(
                bucket_name=bucket_name,
                object_name=object_name,
                file_path=str(local_file),
                content_type="application/octet-stream"
            )

            uploaded_files.append(object_name)

            # Track main checkpoint file
            if filename in ["adapter_model.safetensors", "pytorch_model.bin", "model.safetensors"]:
                main_checkpoint_path = f"minio://{bucket_name}/{object_name}"

        # If no main checkpoint found, use first uploaded file
        if not main_checkpoint_path and uploaded_files:
            main_checkpoint_path = f"minio://{bucket_name}/{uploaded_files[0]}"

        logger.info(f"Successfully uploaded {len(uploaded_files)} files to MinIO")
        logger.info(f"Main checkpoint: {main_checkpoint_path}")

        return main_checkpoint_path

    except S3Error as e:
        logger.error(f"MinIO S3 error during checkpoint upload: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to upload checkpoints to MinIO: {e}")
        logger.error(traceback.format_exc())
        return None


@celery_app.task(
    base=FineTuningTask,
    bind=True,
    name="app.tasks.finetuning_tasks.run_finetuning_job",
    max_retries=0,  # Don't auto-retry training failures
    time_limit=86400,  # 24 hours max
    soft_time_limit=82800  # 23 hours soft limit
)
def run_finetuning_job(self, job_id: str) -> Dict[str, Any]:
    """
    Run fine-tuning job with GPU allocation and progress tracking

    Args:
        job_id: UUID of the fine-tuning job

    Returns:
        Dict with job result details
    """
    job_uuid = UUID(job_id)
    gpu_devices = None
    sandbox_manager = None

    logger.info(f"Starting fine-tuning job: {job_id}")

    try:
        # Get database session
        with SessionLocal() as db:
            # Load job details
            job = db.query(FineTuningJob).filter(
                FineTuningJob.id == job_uuid
            ).first()

            if not job:
                raise ValueError(f"Job {job_id} not found")

            # Update status to running
            job.status = "running"
            job.training_start_time = datetime.utcnow()
            job.celery_task_id = self.request.id
            db.commit()

            # Update Prometheus metrics
            update_prometheus_metrics(job)

            logger.info(f"Job {job_id}: {job.name} - Method: {job.finetuning_method}")

            # Allocate GPU
            gpu_pool = GPUPoolManager()
            gpu_count = job.hyperparameters.get("gpu_count", 1)
            min_memory_gb = job.hyperparameters.get("min_gpu_memory_gb", 6.0)  # Default 6GB (safe for 7B models with 4-bit quant on 8GB GPU)

            logger.info(f"Allocating {gpu_count} GPU(s) with {min_memory_gb}GB minimum memory")

            gpu_devices = asyncio.run(gpu_pool.allocate_gpu(
                job_id=job_id,
                count=gpu_count,
                memory_required_gb=min_memory_gb
            ))

            if not gpu_devices:
                # Wait for GPU with timeout
                logger.info(f"No GPU available, queuing job {job_id}")
                job.status = "queued"
                db.commit()

                gpu_devices = asyncio.run(gpu_pool.wait_for_gpu(
                    job_id=job_id,
                    count=gpu_count,
                    memory_required_gb=min_memory_gb,
                    timeout_seconds=3600  # 1 hour wait
                ))

                if not gpu_devices:
                    raise RuntimeError("GPU allocation timeout after 1 hour")

                # Update status back to running
                job.status = "running"
                db.commit()

                # Update Prometheus metrics
                update_prometheus_metrics(job)

            gpu_str = ",".join(gpu_devices)
            gpu_info = asyncio.run(gpu_pool.get_gpu_info(gpu_devices[0]))
            job.gpu_type = gpu_info.name if gpu_info else "Unknown"
            job.gpu_count = len(gpu_devices)
            db.commit()

            logger.info(f"Allocated GPUs: {gpu_str} for job {job_id}")

            # Update stage: Setup
            update_training_stage(
                db=db,
                job_id=job_uuid,
                stage="setup",
                stage_details={
                    "gpu_allocated": gpu_str,
                    "gpu_type": job.gpu_type,
                    "gpu_count": job.gpu_count
                }
            )

            # Get trainer script
            trainer_script = TrainerFactory.get_trainer_script(job.finetuning_method)

            # Get dataset path from MinIO if dataset_id is provided
            dataset_minio_path = None
            dataset_local_path = None
            if job.dataset_id:
                dataset = db.query(FineTuningDataset).filter_by(id=job.dataset_id).first()
                if dataset and dataset.minio_path:
                    dataset_minio_path = dataset.minio_path
                    logger.info(f"✅ Found dataset in MinIO: {dataset_minio_path}")

                    # ✅ FIX #6: Use correct workspace path with job_id
                    # Dataset will be preprocessed and saved as train.json
                    dataset_local_path = f"/workspace/finetuning/{job_id}/input"
                    logger.info(f"📁 Dataset will be preprocessed and available at: {dataset_local_path}/train.json")

            # Prepare training configuration
            training_config = {
                "job_id": job_id,
                "base_model": job.base_model,
                "finetuning_method": job.finetuning_method,
                "training_objective": job.training_objective,
                "dataset_id": str(job.dataset_id),
                "dataset_path": dataset_local_path,  # ✅ FIX: Local filesystem path, not MinIO path
                "dataset_minio_path": dataset_minio_path,  # Keep MinIO path for download
                "hyperparameters": job.hyperparameters,
                "output_dir": f"/workspace/finetuning/{job_id}/output",
                "checkpoint_dir": f"/workspace/finetuning/{job_id}/output/checkpoints",
                "log_dir": f"/workspace/finetuning/{job_id}/logs"
            }

            # Initialize sandbox manager
            sandbox_manager = FineTuningSandboxManager()

            # Memory limit (default 24GB)
            memory_limit = job.hyperparameters.get("max_memory_gb", 24)

            # Training timeout (default 24 hours)
            timeout_hours = job.hyperparameters.get("max_training_hours", 24)

            logger.info(f"Launching training container with {memory_limit}GB memory, {timeout_hours}h timeout")

            # Update stage: Training
            update_training_stage(
                db=db,
                job_id=job_uuid,
                stage="training",
                stage_details={
                    "base_model": job.base_model,
                    "method": job.finetuning_method,
                    "epochs": job.hyperparameters.get("num_epochs", 3),
                    "batch_size": job.hyperparameters.get("batch_size", 4)
                }
            )

            # Execute training
            result = asyncio.run(sandbox_manager.execute_training(
                job_id=job_id,
                trainer_script=trainer_script,
                config=training_config,
                memory_required_gb=min_memory_gb,
                memory_limit=f"{memory_limit}g",
                timeout_hours=timeout_hours
            ))

            # ✅ FIX: Check if training actually succeeded before proceeding
            if not result.get("success", False):
                error_msg = result.get("error", "Unknown training error")
                logger.error(f"❌ Training failed: {error_msg}")

                add_debug_log(
                    db=db,
                    job_id=job_uuid,
                    stage="training",
                    message=f"Training failed: {error_msg}",
                    log_level="ERROR",
                    metadata={"error": error_msg, "result": result}
                )

                job.status = "failed"
                job.error_message = error_msg
                job.training_end_time = datetime.now(timezone.utc)
                db.commit()

                logger.error(f"❌ Training job {job.name} marked as failed")
                return

            # Only proceed if training succeeded
            logger.info(f"✅ Training succeeded. Uploading checkpoints to MinIO...")

            # Update stage: Checkpoint Save
            update_training_stage(
                db=db,
                job_id=job_uuid,
                stage="checkpoint_save",
                stage_details={
                    "final_loss": result.get("final_loss"),
                    "total_steps": result.get("total_steps")
                }
            )

            # Fetch dataset name for path linkage
            dataset = db.query(FineTuningDataset).filter(
                FineTuningDataset.id == job.dataset_id
            ).first()
            dataset_name = dataset.name if dataset else "unknown-dataset"

            # Fetch user's organizational info (department, team, project) from database
            user = db.query(User).filter(User.id == job.created_by).first() if job.created_by else None
            username = user.username if user else "admin"

            # ========== P1 FIX: Use org context from job record (not user query) ==========
            # Department name - use from job record if available, otherwise fallback to user query
            department_name = job.department if job.department else "Technology"
            if not job.department and user and user.department_id:
                from app.models.rbac import Department
                dept = db.query(Department).filter(Department.id == user.department_id).first()
                if dept:
                    department_name = dept.name

            # Team name - use from job record if available, otherwise query user's actual team
            team_name = job.team if job.team else "General"
            if not job.team and user:
                # Query user's actual team from user_teams table
                team_result = db.execute(text("""
                    SELECT t.name
                    FROM teams t
                    JOIN user_teams ut ON t.id = ut.team_id
                    WHERE ut.user_id = :user_id
                    ORDER BY ut.assigned_at DESC
                    LIMIT 1
                """), {"user_id": str(user.id)})
                team_row = team_result.first()
                if team_row:
                    team_name = team_row[0]

            # Project name - use from job record
            project_name = "global"  # Default
            if job.project_id:
                from app.models.database_enhanced import Project
                project = db.query(Project).filter(Project.id == job.project_id).first()
                if project:
                    project_name = project.name

            logger.info(f"📂 MinIO path context for job {job.name}: dept={department_name}, team={team_name}, project={project_name}, user={username}")

            # Upload checkpoints to MinIO using dataset-linked organizational path structure
            # Use actual checkpoint path from training result (not config)
            checkpoint_dir = result.get("checkpoint_path") or training_config["output_dir"]
            logger.info(f"Checkpoint directory for upload: {checkpoint_dir}")

            minio_checkpoint_path = upload_checkpoints_to_minio(
                job_id=job_id,
                job_name=job.name,
                checkpoint_dir=checkpoint_dir,
                department_name=department_name,
                team_name=team_name,
                project_name=project_name,
                username=username,
                dataset_name=dataset_name
            )

            if not minio_checkpoint_path:
                logger.warning(f"Failed to upload checkpoints to MinIO for job {job_id}")
                # Don't fail the job if MinIO upload fails - training was successful
                minio_checkpoint_path = result.get("checkpoint_path")
            else:
                logger.info(f"Checkpoints uploaded successfully to: {minio_checkpoint_path}")

            # Training completed successfully
            job.status = "completed"
            job.training_end_time = datetime.now(timezone.utc)
            job.progress = 100.0
            job.minio_checkpoint_path = minio_checkpoint_path

            # Extract training metrics from result
            final_metrics = result.get("final_metrics", {})
            job.train_loss = final_metrics.get("train_loss") or result.get("final_loss") or job.train_loss
            job.eval_loss = final_metrics.get("eval_loss") or result.get("final_eval_loss") or job.eval_loss
            job.total_steps = result.get("total_steps")

            # Store comprehensive evaluation metrics (BLEU, ROUGE, METEOR, BERTScore, etc.)
            eval_metrics = result.get("eval_metrics", {})
            if eval_metrics:
                job.eval_metrics = eval_metrics
                logger.info(f"📊 Stored evaluation metrics: {list(eval_metrics.keys())}")

                # Log evaluation completion
                add_debug_log(
                    db=db,
                    job_id=job_uuid,
                    stage="evaluation",
                    message=f"Post-training evaluation completed with {len(eval_metrics)} metrics",
                    metadata={
                        "metrics": list(eval_metrics.keys()),
                        "eval_loss": job.eval_loss,
                        "metric_values": {k: v for k, v in eval_metrics.items() if isinstance(v, (int, float))}
                    }
                )

            # Log training completion
            training_duration = (job.training_end_time - job.training_start_time).total_seconds() if job.training_start_time else None
            add_debug_log(
                db=db,
                job_id=job_uuid,
                stage="training",
                message=f"Training completed successfully in {training_duration:.1f}s" if training_duration else "Training completed successfully",
                metadata={
                    "final_train_loss": job.train_loss,
                    "final_eval_loss": job.eval_loss,
                    "total_steps": job.total_steps,
                    "duration_seconds": training_duration,
                    "checkpoint_path": minio_checkpoint_path
                }
            )

            db.commit()

            # Update stage: Completed
            update_training_stage(
                db=db,
                job_id=job_uuid,
                stage="completed",
                stage_details={
                    "checkpoint_path": minio_checkpoint_path,
                    "duration_seconds": (job.training_end_time - job.training_start_time).total_seconds(),
                    "final_loss": job.train_loss,
                    "eval_loss": job.eval_loss
                }
            )

            # Update Prometheus metrics
            update_prometheus_metrics(job)

            # Automatically register the fine-tuned model
            model_id = None
            if minio_checkpoint_path:
                model_id = register_finetuned_model(
                    db=db,
                    job=job,
                    checkpoint_path=minio_checkpoint_path
                )
                if model_id:
                    logger.info(f"📦 Model registered with ID: {model_id}")

                    # Trigger automatic evaluation (if model is deployed)
                    logger.info(f"🔍 Attempting automatic evaluation...")
                    evaluation_success = trigger_automatic_evaluation(
                        db=db,
                        model_id=model_id,
                        job=job,
                        num_samples=50  # Quick evaluation with 50 samples
                    )
                    if evaluation_success:
                        logger.info(f"✅ Automatic evaluation completed successfully")
                    else:
                        logger.info(f"⏭️  Automatic evaluation skipped (model not deployed yet)")

                    # ========== AUTO-MERGE LORA ADAPTERS ==========
                    # Merge LoRA adapters with base model immediately after training
                    # This makes the model ready for deployment without manual merge step
                    from app.tasks.auto_merge import auto_merge_lora_adapters, should_auto_merge

                    if should_auto_merge():
                        logger.info(f"🔄 Starting auto-merge for model {model_id}")

                        # Get adapter checkpoint path
                        adapter_final_path = result.get("final_checkpoint_path") or f"/workspace/finetuning/{job_id}/output/final"

                        # Log merge start
                        add_debug_log(
                            db=db,
                            job_id=UUID(job_id),
                            stage="merge",
                            message=f"Starting LoRA adapter merge with base model: {job.base_model}",
                            metadata={"adapter_path": adapter_final_path}
                        )

                        # Run auto-merge
                        merge_result = auto_merge_lora_adapters(
                            job_id=job_id,
                            adapter_path=adapter_final_path,
                            base_model_name=job.base_model,
                            workspace_path=Path(f"/workspace/finetuning/{job_id}"),
                            force_cpu=False  # Use GPU if available
                        )

                        if merge_result and merge_result["status"] == "success":
                            logger.info(f"✅ Auto-merge completed in {merge_result['duration_seconds']:.1f}s")
                            logger.info(f"📍 Merged model: {merge_result['merged_path']}")

                            # Log merge success
                            add_debug_log(
                                db=db,
                                job_id=UUID(job_id),
                                stage="merge",
                                message=f"Merge completed successfully in {merge_result['duration_seconds']:.1f}s",
                                metadata={
                                    "merged_path": merge_result["merged_path"],
                                    "duration_seconds": merge_result["duration_seconds"],
                                    "source": merge_result.get("source", "post_training_merge")
                                }
                            )

                            # Update model record with merged path and status
                            from app.models.finetuning_models import FineTunedModel
                            model = db.query(FineTunedModel).filter(FineTunedModel.id == model_id).first()
                            if model:
                                model.merged_model_path = merge_result["merged_path"]
                                model.status = "merged"  # Change from registered/adapter_only to merged
                                model.merge_duration_seconds = merge_result["duration_seconds"]
                                model.merge_requested_at = datetime.utcnow()
                                db.commit()
                                logger.info(f"✅ Model status updated to 'merged' (ready for deployment)")
                        else:
                            logger.warning(f"⚠️  Auto-merge failed or skipped. Model saved as adapters only.")
                            logger.info(f"   User can manually merge later from UI")

                            # Log merge failure
                            add_debug_log(
                                db=db,
                                job_id=UUID(job_id),
                                stage="merge",
                                message="Merge failed or skipped - model saved as adapters only",
                                log_level="WARNING",
                                metadata={"merge_result": merge_result if merge_result else None}
                            )
                    else:
                        logger.info(f"⏭️  Auto-merge disabled (FINETUNING_AUTO_MERGE=false)")
                    # ===============================================
                else:
                    logger.warning("Model registration failed, but training was successful")

            logger.info(f"Job {job_id} completed successfully")
            logger.info(f"Checkpoint saved to: {job.minio_checkpoint_path}")

            return {
                "job_id": job_id,
                "status": "completed",
                "checkpoint_path": job.minio_checkpoint_path,
                "model_id": model_id,  # Include registered model ID
                "final_loss": job.train_loss,
                "duration_seconds": (job.training_end_time - job.training_start_time).total_seconds()
            }

    except Exception as e:
        error_msg = f"Training failed: {str(e)}\n{traceback.format_exc()}"
        logger.error(f"Job {job_id} error: {error_msg}")

        # Update job status to failed
        with SessionLocal() as db:
            job = db.query(FineTuningJob).filter(
                FineTuningJob.id == job_uuid
            ).first()
            if job:
                job.status = "failed"
                job.error_message = str(e)
                job.training_end_time = datetime.now(timezone.utc)
                db.commit()

                # Update stage: Failed
                update_training_stage(
                    db=db,
                    job_id=job_uuid,
                    stage="failed",
                    stage_details={
                        "error": str(e),
                        "failed_at_stage": job.training_stage
                    }
                )

                # Update Prometheus metrics
                update_prometheus_metrics(job)

        raise

    finally:
        # Cleanup: Release GPU
        if gpu_devices:
            try:
                gpu_pool = GPUPoolManager()
                asyncio.run(gpu_pool.release_gpu(job_id))
                logger.info(f"Released GPUs for job {job_id}")
            except Exception as e:
                logger.error(f"Failed to release GPU: {e}")

        # DON'T cleanup workspace immediately - keep it for deployment
        # Workspace will be cleaned up by scheduled cleanup_old_workspaces task after 7 days
        # This allows deployment to use the merged model directly from workspace without re-downloading from MinIO
        logger.info(f"✅ Training complete. Workspace preserved at /workspace/finetuning/{job_id} for deployment")
        logger.info(f"   Workspace will be auto-cleaned after 7 days by scheduled task")


@celery_app.task(name="app.tasks.finetuning_tasks.cancel_finetuning_job")
def cancel_finetuning_job(job_id: str, celery_task_id: str) -> Dict[str, Any]:
    """
    Cancel a running fine-tuning job

    Args:
        job_id: UUID of the fine-tuning job
        celery_task_id: Celery task ID to revoke

    Returns:
        Dict with cancellation result
    """
    try:
        job_uuid = UUID(job_id)

        logger.info(f"Cancelling job {job_id} (task {celery_task_id})")

        # Revoke Celery task
        celery_app.control.revoke(celery_task_id, terminate=True, signal='SIGKILL')

        # Update job status
        with SessionLocal() as db:
            job = db.query(FineTuningJob).filter(
                FineTuningJob.id == job_uuid
            ).first()

            if job:
                job.status = "cancelled"
                job.training_end_time = datetime.now(timezone.utc)
                db.commit()

                # Update Prometheus metrics
                update_prometheus_metrics(job)

                logger.info(f"Job {job_id} marked as cancelled")

        # Release GPU
        gpu_pool = GPUPoolManager()
        asyncio.run(gpu_pool.release_gpu(job_id))

        # Cleanup sandbox
        sandbox_manager = FineTuningSandboxManager()
        asyncio.run(sandbox_manager.cleanup(job_id))

        return {
            "job_id": job_id,
            "status": "cancelled",
            "message": "Job cancelled successfully"
        }

    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}")
        raise


@celery_app.task(name="app.tasks.finetuning_tasks.cleanup_old_workspaces")
def cleanup_old_workspaces(days_old: int = 7) -> Dict[str, Any]:
    """
    Cleanup old training workspaces

    Args:
        days_old: Remove workspaces older than this many days

    Returns:
        Dict with cleanup statistics
    """
    try:
        import shutil
        from pathlib import Path
        from datetime import timedelta

        workspace_base = Path(settings.FINETUNING_WORKSPACE_BASE)
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        removed_count = 0
        freed_space_mb = 0

        for workspace_dir in workspace_base.iterdir():
            if not workspace_dir.is_dir():
                continue

            # Check modification time
            mtime = datetime.fromtimestamp(workspace_dir.stat().st_mtime)

            if mtime < cutoff_date:
                # Calculate size
                size_bytes = sum(
                    f.stat().st_size
                    for f in workspace_dir.rglob('*')
                    if f.is_file()
                )

                # Remove workspace
                shutil.rmtree(workspace_dir)

                removed_count += 1
                freed_space_mb += size_bytes / (1024 * 1024)

                logger.info(f"Removed old workspace: {workspace_dir.name}")

        logger.info(f"Cleanup complete: removed {removed_count} workspaces, freed {freed_space_mb:.2f}MB")

        return {
            "removed_count": removed_count,
            "freed_space_mb": round(freed_space_mb, 2),
            "cutoff_date": cutoff_date.isoformat()
        }

    except Exception as e:
        logger.error(f"Workspace cleanup failed: {e}")
        raise


@celery_app.task(name="merge_lora_model", bind=True)
def merge_lora_model_task(
    self,
    model_id: str,
    base_model_name: str = "Qwen/Qwen2.5-1.5B-Instruct",
    force_cpu: bool = False
):
    """
    Celery task for merging LoRA adapters with base model.

    This is a background task that can run for 5-15 minutes.
    Must be asynchronous to avoid blocking the API.

    JIRA: FINETUNE-002

    Args:
        model_id: ID of the fine-tuned model
        base_model_name: HuggingFace base model name
        force_cpu: Force CPU-only merge (for testing)

    Returns:
        Dict with merge status, path, and duration

    Critical Integration Point:
        Saves merged model to /workspace/finetuning/{job_id}/output/merged_model
        OllamaDeploymentService checks this path FIRST (workspace-first optimization)
    """
    from app.services.finetuning.model_merge_service import ModelMergeService

    logger.info(f"🔄 [CELERY] Starting merge task for model {model_id}")
    logger.info(f"   Task ID: {self.request.id}")
    logger.info(f"   Base model: {base_model_name}")

    # Create database session for this task
    db = SessionLocal()

    try:
        # Create merge service
        merge_service = ModelMergeService(db)

        # Run merge (this is async in the service, but Celery tasks are sync)
        import asyncio
        result = asyncio.run(
            merge_service.merge_lora_adapters(
                model_id=model_id,
                base_model_name=base_model_name,
                force_cpu=force_cpu
            )
        )

        if result["status"] == "success":
            logger.info(f"✅ [CELERY] Merge task completed successfully")
            logger.info(f"   Model ID: {model_id}")
            logger.info(f"   Duration: {result['duration_seconds']}s")
            logger.info(f"   Output: {result['merged_model_path']}")
        else:
            logger.error(f"❌ [CELERY] Merge task failed: {result.get('error')}")

        return result

    except Exception as e:
        logger.error(f"❌ [CELERY] Merge task exception: {e}", exc_info=True)

        # Update database with error status
        from sqlalchemy import update
        from app.models.database import FineTunedModel

        stmt = (
            update(FineTunedModel)
            .where(FineTunedModel.id == model_id)
            .values(
                status="merge_failed",
                merge_error_message=str(e)
            )
        )

        db.execute(stmt)
        db.commit()

        return {
            "status": "error",
            "model_id": model_id,
            "error": str(e),
            "message": f"Merge task failed: {e}"
        }

    finally:
        db.close()
