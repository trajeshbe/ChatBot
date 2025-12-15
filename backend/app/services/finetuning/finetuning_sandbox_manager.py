"""
Fine-Tuning Sandbox Manager

Extends AgentSandboxManager to support GPU-accelerated model fine-tuning.
Leverages existing container infrastructure while adding GPU management.

Key Features:
- GPU allocation and isolation
- Resource limits (VRAM, CPU, memory)
- Workspace management (datasets, checkpoints)
- Real-time monitoring
- Automatic cleanup

Design Pattern: Extends existing AgentSandboxManager (~70% code reuse!)
"""

import asyncio
import docker
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import shutil

from app.services.agent_sandbox_manager import AgentSandboxManager
from app.core.config import settings

logger = logging.getLogger(__name__)


class FineTuningSandboxManager(AgentSandboxManager):
    """
    GPU-enabled sandbox manager for model fine-tuning.

    Extends AgentSandboxManager with:
    - GPU device allocation
    - Higher resource limits for training
    - Training-specific volume mounts
    - Checkpoint management
    """

    def __init__(self):
        """Initialize with GPU support"""
        super().__init__()

        # Override image for fine-tuning
        self.finetuning_image = "chatbot-finetuning-runtime:latest"

        # Training-specific resource limits (much higher than agent tasks)
        self.training_resource_limits = {
            "mem_limit": "24g",  # 24GB RAM for training
            "cpu_period": 100000,
            "cpu_quota": 800000,  # 8 CPUs
            "pids_limit": 500,  # More processes for training
        }

        logger.info("🔥 Fine-tuning sandbox manager initialized")

    async def create_training_workspace(
        self,
        job_id: str,
        dataset_path: Optional[str] = None
    ) -> Dict[str, Path]:
        """
        Create workspace for training job

        Structure:
        /tmp/finetuning_workspaces/{job_id}/
        ├── input/              # Dataset, config
        ├── output/             # Model checkpoints
        ├── logs/               # Training logs
        └── temp/               # Temporary files

        Args:
            job_id: Unique job identifier
            dataset_path: Optional path to dataset in MinIO

        Returns:
            Dictionary of workspace paths
        """
        workspace_base = Path(f"/tmp/finetuning_workspaces/{job_id}")

        # Create directory structure
        dirs = {
            "base": workspace_base,
            "input": workspace_base / "input",
            "output": workspace_base / "output",
            "logs": workspace_base / "logs",
            "temp": workspace_base / "temp",
        }

        for dir_path in dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"📁 Created training workspace: {workspace_base}")

        # Copy dataset if provided
        if dataset_path:
            await self._copy_dataset_to_workspace(dataset_path, dirs["input"])

        return dirs

    async def _copy_dataset_to_workspace(
        self,
        dataset_path: str,
        input_dir: Path
    ):
        """Copy dataset from MinIO to workspace"""
        # TODO: Implement MinIO download
        # For now, assume dataset_path is local
        logger.info(f"📦 Copying dataset from {dataset_path} to {input_dir}")
        pass

    async def execute_training(
        self,
        job_id: str,
        trainer_script: str,
        config: Dict[str, Any],
        gpu_devices: str = "0",
        memory_limit: str = "24g",
        timeout_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Execute training in GPU-enabled container

        Args:
            job_id: Job identifier
            trainer_script: Training script to run (peft_trainer.py, sft_trainer.py, etc.)
            config: Training configuration
            gpu_devices: Comma-separated GPU IDs (e.g., "0" or "0,1")
            memory_limit: Memory limit (e.g., "24g")
            timeout_hours: Training timeout in hours

        Returns:
            Training result with metrics and paths
        """
        logger.info(f"🚀 Starting training job {job_id} on GPU {gpu_devices}")

        # Create workspace
        workspace = await self.create_training_workspace(job_id)

        # Save training config
        config_file = workspace["input"] / "training_config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        # Build environment variables
        env_vars = {
            "JOB_ID": job_id,
            "CUDA_VISIBLE_DEVICES": gpu_devices,
            "PYTHONUNBUFFERED": "1",
            "TRAINING_CONFIG": "/workspace/input/training_config.json",
            "OUTPUT_DIR": "/workspace/output",
            "LOG_DIR": "/workspace/logs",

            # Ollama for base model loading (if needed)
            "OLLAMA_BASE_URL": settings.OLLAMA_BASE_URL,

            # HuggingFace cache
            "HF_HOME": "/workspace/temp/.cache/huggingface",
            "TRANSFORMERS_CACHE": "/workspace/temp/.cache/transformers",
        }

        # Add API keys if configured
        if settings.OPENAI_API_KEY:
            env_vars["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
        if settings.ANTHROPIC_API_KEY:
            env_vars["ANTHROPIC_API_KEY"] = settings.ANTHROPIC_API_KEY

        # Launch container with GPU
        container = None
        try:
            logger.info(f"🐳 Creating GPU container with image {self.finetuning_image}")

            # GPU device requests (NVIDIA Docker runtime)
            device_requests = []
            if gpu_devices and gpu_devices != "none":
                device_requests.append(
                    docker.types.DeviceRequest(
                        device_ids=gpu_devices.split(","),
                        capabilities=[['gpu']]
                    )
                )

            container = self.docker_client.containers.run(
                image=self.finetuning_image,
                name=f"finetuning-{job_id}",
                detach=True,
                remove=False,  # Keep for inspection
                network=self.network_name,
                environment=env_vars,

                # GPU allocation
                device_requests=device_requests,

                # Resource limits
                mem_limit=memory_limit,
                cpu_period=self.training_resource_limits["cpu_period"],
                cpu_quota=self.training_resource_limits["cpu_quota"],
                pids_limit=self.training_resource_limits["pids_limit"],

                # Volume mounts
                volumes={
                    str(workspace["base"]): {
                        'bind': '/workspace',
                        'mode': 'rw'
                    }
                },

                # Command: run trainer script
                command=[
                    "python", f"/app/trainers/{trainer_script}",
                    "--config", "/workspace/input/training_config.json",
                    "--output", "/workspace/output",
                    "--log-dir", "/workspace/logs"
                ],

                stdin_open=False,
            )

            logger.info(f"✅ Training container {container.short_id} started")

            # Wait for completion (with timeout)
            timeout_seconds = timeout_hours * 3600

            logger.info(f"⏳ Waiting for training to complete (timeout: {timeout_hours}h)...")

            exit_status = await asyncio.to_thread(
                container.wait,
                timeout=timeout_seconds
            )

            # Get logs
            logs = await asyncio.to_thread(container.logs, stdout=True, stderr=True)
            logs_text = logs.decode('utf-8')

            # Save logs
            log_file = workspace["logs"] / "training.log"
            with open(log_file, 'w') as f:
                f.write(logs_text)

            logger.info(f"📋 Training completed with exit code: {exit_status['StatusCode']}")

            # Read result
            result_file = workspace["output"] / "result.json"
            if result_file.exists():
                with open(result_file, 'r') as f:
                    result = json.load(f)
            else:
                result = {
                    "success": exit_status["StatusCode"] == 0,
                    "exit_code": exit_status["StatusCode"],
                }

            # Add paths to result
            result.update({
                "workspace_path": str(workspace["base"]),
                "checkpoint_path": str(workspace["output"]),
                "log_path": str(log_file),
                "logs": logs_text[-5000:] if len(logs_text) > 5000 else logs_text  # Last 5000 chars
            })

            return result

        except docker.errors.ContainerError as e:
            logger.error(f"❌ Container error: {e}")
            return {
                "success": False,
                "error": f"Container error: {str(e)}",
                "workspace_path": str(workspace["base"])
            }

        except docker.errors.ImageNotFound:
            logger.error(f"❌ Image not found: {self.finetuning_image}")
            return {
                "success": False,
                "error": f"Fine-tuning runtime image not found: {self.finetuning_image}",
                "hint": "Run: docker build -t chatbot-finetuning-runtime:latest -f Dockerfile.finetuning-runtime ."
            }

        except asyncio.TimeoutError:
            logger.error(f"❌ Training timeout after {timeout_hours} hours")
            if container:
                await asyncio.to_thread(container.kill)
            return {
                "success": False,
                "error": f"Training timeout after {timeout_hours} hours",
                "workspace_path": str(workspace["base"])
            }

        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return {
                "success": False,
                "error": str(e),
                "workspace_path": str(workspace["base"])
            }

        finally:
            # Cleanup container (but keep workspace for artifact retrieval)
            if container:
                try:
                    await asyncio.to_thread(container.remove, force=True)
                    logger.info(f"🧹 Removed container {container.short_id}")
                except Exception as e:
                    logger.warning(f"Failed to remove container: {e}")

    async def get_training_logs(
        self,
        job_id: str,
        tail: int = 100
    ) -> List[str]:
        """
        Get training logs for a job

        Args:
            job_id: Job identifier
            tail: Number of lines to return from end

        Returns:
            List of log lines
        """
        workspace = Path(f"/tmp/finetuning_workspaces/{job_id}")
        log_file = workspace / "logs" / "training.log"

        if not log_file.exists():
            return []

        with open(log_file, 'r') as f:
            lines = f.readlines()

        return lines[-tail:] if tail else lines

    async def cleanup_workspace(
        self,
        job_id: str,
        keep_checkpoints: bool = True
    ):
        """
        Clean up training workspace

        Args:
            job_id: Job identifier
            keep_checkpoints: If True, only delete temp files
        """
        workspace = Path(f"/tmp/finetuning_workspaces/{job_id}")

        if not workspace.exists():
            return

        try:
            if keep_checkpoints:
                # Only delete temp and input directories
                for subdir in ["temp", "input"]:
                    dir_path = workspace / subdir
                    if dir_path.exists():
                        shutil.rmtree(dir_path)
                logger.info(f"🧹 Cleaned temp files for job {job_id}")
            else:
                # Delete entire workspace
                shutil.rmtree(workspace)
                logger.info(f"🧹 Removed workspace for job {job_id}")

        except Exception as e:
            logger.warning(f"Failed to cleanup workspace {job_id}: {e}")

    async def upload_checkpoint_to_minio(
        self,
        job_id: str,
        minio_path: str
    ) -> bool:
        """
        Upload trained model checkpoint to MinIO

        Args:
            job_id: Job identifier
            minio_path: Destination path in MinIO

        Returns:
            Success status
        """
        workspace = Path(f"/tmp/finetuning_workspaces/{job_id}")
        checkpoint_dir = workspace / "output"

        if not checkpoint_dir.exists():
            logger.error(f"Checkpoint directory not found: {checkpoint_dir}")
            return False

        try:
            # TODO: Implement MinIO upload
            # For now, log the action
            logger.info(f"📤 Uploading checkpoint from {checkpoint_dir} to MinIO: {minio_path}")

            # Placeholder for actual implementation:
            # from minio import Minio
            # minio_client = Minio(...)
            # for file in checkpoint_dir.iterdir():
            #     minio_client.fput_object(bucket, f"{minio_path}/{file.name}", str(file))

            return True

        except Exception as e:
            logger.error(f"Failed to upload checkpoint: {e}")
            return False

    async def stream_training_metrics(
        self,
        job_id: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream real-time training metrics

        Reads metrics from workspace/logs/metrics.jsonl

        Args:
            job_id: Job identifier

        Yields:
            Training metrics dictionaries
        """
        workspace = Path(f"/tmp/finetuning_workspaces/{job_id}")
        metrics_file = workspace / "logs" / "metrics.jsonl"

        # Wait for file to exist
        for _ in range(30):  # 30 seconds timeout
            if metrics_file.exists():
                break
            await asyncio.sleep(1)

        if not metrics_file.exists():
            logger.warning(f"Metrics file not found: {metrics_file}")
            return

        # Stream new lines as they're written
        with open(metrics_file, 'r') as f:
            # Read existing lines
            for line in f:
                if line.strip():
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue

            # Watch for new lines (simplified - production would use inotify)
            while True:
                line = f.readline()
                if line:
                    if line.strip():
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            continue
                else:
                    # Check if container still running
                    try:
                        container = self.docker_client.containers.get(f"finetuning-{job_id}")
                        if container.status != "running":
                            break
                    except docker.errors.NotFound:
                        break

                    await asyncio.sleep(1)


# Singleton instance
finetuning_sandbox_manager = FineTuningSandboxManager()
