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
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from uuid import UUID

from celery import Task
from minio import Minio
from minio.error import S3Error
from sqlalchemy.orm import Session, sessionmaker

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
                    job.training_end_time = datetime.utcnow()
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

            # Get trainer script
            trainer_script = TrainerFactory.get_trainer_script(job.finetuning_method)

            # Prepare training configuration
            training_config = {
                "job_id": job_id,
                "base_model": job.base_model,
                "finetuning_method": job.finetuning_method,
                "training_objective": job.training_objective,
                "dataset_id": str(job.dataset_id),
                "hyperparameters": job.hyperparameters,
                "output_dir": f"/workspace/output/{job_id}",
                "checkpoint_dir": f"/workspace/output/{job_id}/checkpoints",
                "log_dir": f"/workspace/logs/{job_id}"
            }

            # Initialize sandbox manager
            sandbox_manager = FineTuningSandboxManager()

            # Memory limit (default 24GB)
            memory_limit = job.hyperparameters.get("max_memory_gb", 24)

            # Training timeout (default 24 hours)
            timeout_hours = job.hyperparameters.get("max_training_hours", 24)

            logger.info(f"Launching training container with {memory_limit}GB memory, {timeout_hours}h timeout")

            # Execute training
            result = asyncio.run(sandbox_manager.execute_training(
                job_id=job_id,
                trainer_script=trainer_script,
                config=training_config,
                memory_required_gb=min_memory_gb,
                memory_limit=f"{memory_limit}g",
                timeout_hours=timeout_hours
            ))

            logger.info(f"Training completed. Uploading checkpoints to MinIO...")

            # Fetch dataset name for path linkage
            dataset = db.query(FineTuningDataset).filter(
                FineTuningDataset.id == job.dataset_id
            ).first()
            dataset_name = dataset.name if dataset else "unknown-dataset"

            # Fetch user's organizational info (department, team, project) from database
            user = db.query(User).filter(User.id == job.created_by).first() if job.created_by else None

            # Query department name
            department_name = "Technology"  # Default
            if user and user.department_id:
                from app.models.database_enhanced import Department
                dept = db.query(Department).filter(Department.id == user.department_id).first()
                if dept:
                    department_name = dept.name

            # Query team name from user_teams table
            team_name = "Backend Development"  # Default
            if user:
                from app.models.database_enhanced import UserTeam, Team
                user_team = db.query(UserTeam).filter(UserTeam.user_id == user.id).first()
                if user_team:
                    team = db.query(Team).filter(Team.id == user_team.team_id).first()
                    if team:
                        team_name = team.name

            username = user.username if user else "admin"

            # Query project name
            project_name = "global"  # Default
            if job.project_id:
                from app.models.database_enhanced import Project
                project = db.query(Project).filter(Project.id == job.project_id).first()
                if project:
                    project_name = project.name

            # Upload checkpoints to MinIO using dataset-linked organizational path structure
            checkpoint_dir = training_config["checkpoint_dir"]
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
            job.training_end_time = datetime.utcnow()
            job.progress = 100.0
            job.minio_checkpoint_path = minio_checkpoint_path
            job.train_loss = result.get("final_loss") or job.train_loss
            job.eval_loss = result.get("final_eval_loss") or job.eval_loss
            job.total_steps = result.get("total_steps")
            db.commit()

            # Update Prometheus metrics
            update_prometheus_metrics(job)

            logger.info(f"Job {job_id} completed successfully")
            logger.info(f"Checkpoint saved to: {job.minio_checkpoint_path}")

            return {
                "job_id": job_id,
                "status": "completed",
                "checkpoint_path": job.minio_checkpoint_path,
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
                job.training_end_time = datetime.utcnow()
                db.commit()

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

        # Cleanup: Remove sandbox
        if sandbox_manager:
            try:
                asyncio.run(sandbox_manager.cleanup(job_id))
                logger.info(f"Cleaned up sandbox for job {job_id}")
            except Exception as e:
                logger.error(f"Failed to cleanup sandbox: {e}")


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
                job.training_end_time = datetime.utcnow()
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
