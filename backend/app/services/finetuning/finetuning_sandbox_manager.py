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
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, AsyncIterator
from datetime import datetime
import shutil
import traceback

from minio import Minio
from minio.error import S3Error

from app.services.agent_sandbox_manager import AgentSandboxManager
from app.services.finetuning.training_log_streamer import TrainingLogStreamer
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
        """Initialize with GPU support and MinIO client"""
        super().__init__()

        # Override image for fine-tuning (dedicated image with PEFT dependencies)
        # Use environment variable to support proper versioning and prevent image conflicts
        self.finetuning_image = os.getenv("FINETUNING_TRAINER_IMAGE", "chatbot-finetuning-trainer:v1.0.4")

        # Path to backend code (for mounting trainer scripts)
        # Use host's backend directory, not container's /app
        self.backend_path = os.getenv("BACKEND_CODE_PATH", "/mnt/c/AIML/ClaudeCode/chatbot/ChatBot/backend")

        # Training-specific resource limits (much higher than agent tasks)
        self.training_resource_limits = {
            "mem_limit": "24g",  # 24GB RAM for training
            "cpu_period": 100000,
            "cpu_quota": 800000,  # 8 CPUs
            "pids_limit": 500,  # More processes for training
        }

        # ✨ NEW: Initialize MinIO client for dataset/checkpoint storage
        try:
            self.minio_client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
            # ✅ FIX: Use documents bucket where datasets are actually uploaded
            self.minio_bucket = "documents"

            # Ensure bucket exists
            if not self.minio_client.bucket_exists(self.minio_bucket):
                self.minio_client.make_bucket(self.minio_bucket)
                logger.info(f"Created MinIO bucket: {self.minio_bucket}")

            logger.info(f"✅ MinIO client initialized (bucket: {self.minio_bucket})")
        except Exception as e:
            logger.warning(f"⚠️ MinIO initialization failed: {e}")
            self.minio_client = None
            self.minio_bucket = None

        logger.info("🔥 Fine-tuning sandbox manager initialized")

    def _log_debug(self, job_id: str, message: str):
        """
        Add timestamped debug message to job's debug_log array in database

        SYNCHRONOUS version for Celery tasks (no async/await)
        This allows us to trace the training pipeline even after container removal
        """
        try:
            from sqlalchemy import create_engine, text
            from app.core.config import settings

            # Create synchronous engine (already in psycopg2 format)
            database_url = settings.SYNC_SQLALCHEMY_DATABASE_URI
            engine = create_engine(database_url)

            with engine.connect() as conn:
                # Get current timestamp
                timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                log_entry = f"[{timestamp}] {message}"

                # Update job's debug_log array using PostgreSQL array append
                conn.execute(
                    text("""
                        UPDATE finetuning_jobs
                        SET debug_log = array_append(debug_log, :log_entry)
                        WHERE id = :job_id
                    """),
                    {"job_id": job_id, "log_entry": log_entry}
                )
                conn.commit()

            # Also log to console for immediate visibility
            logger.info(f"[{job_id[:8]}] {message}")

        except Exception as e:
            # Don't fail training if logging fails
            logger.warning(f"Debug logging failed: {e}")

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
        # Use environment variable for workspace base (configured in docker-compose.yml)
        workspace_root = os.getenv("FINETUNING_WORKSPACE_BASE", "/tmp/finetuning_workspaces")
        workspace_base = Path(f"{workspace_root}/{job_id}")

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
            # Explicitly set permissions to 777 for container write access
            os.chmod(dir_path, 0o777)

        logger.info(f"📁 Created training workspace: {workspace_base}")

        # Copy dataset if provided
        if dataset_path:
            await self._copy_dataset_to_workspace(dataset_path, dirs["input"], job_id)

        return dirs

    async def _copy_dataset_to_workspace(
        self,
        dataset_minio_path: str,
        input_dir: Path,
        job_id: str
    ):
        """
        Download dataset from MinIO to training workspace and preprocess it for training

        Args:
            dataset_minio_path: Path to dataset in MinIO (e.g., "technology/itm11/global/admin/finetuning/datasets/.../file.jsonl")
            input_dir: Local workspace input directory
            job_id: Training job ID for debug logging

        Raises:
            ValueError: If MinIO client not initialized
            S3Error: If download fails
            FileNotFoundError: If downloaded file not found after download
        """
        if not self.minio_client:
            raise ValueError("MinIO client not initialized")

        try:
            self._log_debug(job_id, "📦 Starting dataset download from MinIO")
            self._log_debug(job_id, f"   Bucket: {self.minio_bucket}")
            self._log_debug(job_id, f"   Object: {dataset_minio_path}")

            logger.info(f"📦 Starting dataset download from MinIO")
            logger.info(f"   Bucket: {self.minio_bucket}")
            logger.info(f"   Object path: {dataset_minio_path}")

            # Extract filename from MinIO path
            filename = Path(dataset_minio_path).name
            local_path = input_dir / filename
            logger.info(f"   Local target: {local_path}")

            # Download from MinIO synchronously (minio-py doesn't support async)
            await asyncio.to_thread(
                self.minio_client.fget_object,
                bucket_name=self.minio_bucket,
                object_name=dataset_minio_path,
                file_path=str(local_path)
            )

            # Verify download succeeded
            if not local_path.exists():
                raise FileNotFoundError(f"Download completed but file not found: {local_path}")

            file_size = local_path.stat().st_size
            self._log_debug(job_id, f"✅ Downloaded dataset: {filename} ({file_size:,} bytes)")
            logger.info(f"✅ Downloaded dataset: {filename} ({file_size:,} bytes)")

            # Verify file content (read first line to ensure it's readable)
            try:
                with open(local_path, 'r') as f:
                    first_line = f.readline()
                    preview = first_line[:100] + "..." if len(first_line) > 100 else first_line
                    self._log_debug(job_id, f"   Preview: {preview}")
                    logger.info(f"   First line preview: {preview}")
            except Exception as read_error:
                self._log_debug(job_id, f"⚠️ Could not read file: {read_error}")
                logger.warning(f"⚠️  Could not read file content: {read_error}")

            return local_path

        except S3Error as e:
            self._log_debug(job_id, f"❌ MinIO download failed: {e}")
            logger.error(f"❌ MinIO download failed!")
            logger.error(f"   Bucket: {self.minio_bucket}")
            logger.error(f"   Object: {dataset_minio_path}")
            logger.error(f"   Error: {e}")
            raise
        except Exception as e:
            self._log_debug(job_id, f"❌ Download failed: {e}")
            logger.error(f"❌ Failed to download dataset: {e}")
            logger.error(f"   Bucket: {self.minio_bucket}")
            logger.error(f"   Object: {dataset_minio_path}")
            raise

    async def _preprocess_dataset_for_training(
        self,
        dataset_file_path: Path,
        input_dir: Path,
        training_objective: str = "instruction"
    ):
        """
        Preprocess downloaded dataset and save as train.json for the trainer

        The trainer expects a directory with train.json inside, not a direct file path.
        This method processes the raw dataset (CSV/JSONL) and saves it in the expected format.

        Args:
            dataset_file_path: Path to downloaded raw dataset file
            input_dir: Input directory where train.json should be created
            training_objective: Training objective (qa, instruction, classification, etc.)

        Raises:
            ValueError: If preprocessing fails
        """
        try:
            logger.info(f"🔄 Preprocessing dataset: {dataset_file_path}")

            # Import here to avoid circular dependencies
            from app.services.finetuning.dataset_preprocessor import DatasetPreprocessor
            import json
            import pandas as pd

            # Check if file is already in messages format (direct pass-through)
            # This is for JSONL files with a "messages" column containing chat conversations
            if dataset_file_path.suffix == '.jsonl':
                # Try to detect messages format
                with open(dataset_file_path, 'r') as f:
                    first_line = json.loads(f.readline())
                    if 'messages' in first_line:
                        logger.info("📱 Detected 'messages' format - using direct pass-through")
                        # Load all lines and save directly as train.json
                        train_data = []
                        with open(dataset_file_path, 'r') as f:
                            for line in f:
                                train_data.append(json.loads(line))

                        # Split into train/validation (90/10)
                        split_idx = int(len(train_data) * 0.9)
                        train_split = train_data[:split_idx]
                        val_split = train_data[split_idx:]

                        # Save as train.json
                        train_json_path = input_dir / "train.json"
                        with open(train_json_path, 'w') as f:
                            json.dump(train_split, f, indent=2)
                        logger.info(f"✅ Saved messages-format dataset to {train_json_path} ({len(train_split)} train samples)")

                        # Save validation.json if we have validation samples
                        if val_split:
                            val_json_path = input_dir / "validation.json"
                            with open(val_json_path, 'w') as f:
                                json.dump(val_split, f, indent=2)
                            logger.info(f"✅ Validation set saved to {val_json_path} ({len(val_split)} samples)")

                        return  # Done!

            # Create preprocessor
            preprocessor = DatasetPreprocessor()

            # Load the raw dataset
            df = preprocessor.load_dataset(str(dataset_file_path))
            logger.info(f"📊 Loaded {len(df)} samples from dataset")

            # Use training_objective to determine format type
            # Map training_objective to DatasetPreprocessor format types
            objective_to_format = {
                "qa": "qa",
                "question_answering": "qa",
                "instruction": "instruction",
                "instruction_following": "instruction",
                "classification": "classification",
                "text_classification": "classification",
                "summarization": "summarization",
                "preference": "preference",
                "rlhf": "preference"
            }
            format_type = objective_to_format.get(training_objective.lower(), "instruction")
            logger.info(f"📝 Training objective: {training_objective} → Format type: {format_type}")

            # Auto-detect column mapping using the DatasetPreprocessor's built-in auto-detection
            # This is more robust than manual detection and handles many edge cases
            logger.info(f"🔍 Auto-detecting columns for format type: {format_type}")

            # Use empty columns dict to trigger auto-detection in validate_dataset
            validation_result = preprocessor.validate_dataset(df, format_type, columns={})

            if not validation_result["is_valid"]:
                # Auto-detection failed, log detailed error
                logger.error(f"❌ Dataset validation failed:")
                for error in validation_result.get("errors", []):
                    logger.error(f"   {error}")

                # Try to provide helpful suggestions
                for suggestion in validation_result.get("suggestions", []):
                    logger.info(f"   {suggestion}")

                # Try intelligent fallback: use first N columns based on format type
                logger.warning(f"⚠️  Attempting fallback column mapping...")
                columns = self._fallback_column_mapping(df, format_type)

                if not columns:
                    raise ValueError(
                        f"Dataset validation failed: Could not auto-detect column mapping. "
                        f"Available columns in CSV: {list(df.columns)}. "
                        f"Expected columns for '{format_type}': {preprocessor._get_expected_columns(format_type)}"
                    )

                logger.info(f"✅ Using fallback column mapping: {columns}")
            else:
                # Auto-detection succeeded
                columns = validation_result["diagnostics"]["applied_mapping"]
                logger.info(f"✅ Auto-detected column mapping: {columns}")

            # Process the dataset
            processed = preprocessor.process(
                dataset_path=str(dataset_file_path),
                format_type=format_type,
                columns=columns,
                train_split=0.9,  # Use 90% for training
                shuffle=True
            )

            # Save as train.json in HuggingFace datasets format
            train_json_path = input_dir / "train.json"
            train_data = []
            for text in processed["train"]:
                train_data.append({"text": text})

            with open(train_json_path, 'w') as f:
                json.dump(train_data, f, indent=2)

            logger.info(f"✅ Preprocessed dataset saved to {train_json_path} ({len(train_data)} train samples)")

            # Also save validation set if needed
            if processed["validation"]:
                val_json_path = input_dir / "validation.json"
                val_data = []
                for text in processed["validation"]:
                    val_data.append({"text": text})

                with open(val_json_path, 'w') as f:
                    json.dump(val_data, f, indent=2)

                logger.info(f"✅ Validation set saved to {val_json_path} ({len(val_data)} samples)")

        except Exception as e:
            logger.error(f"❌ Dataset preprocessing failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise ValueError(f"Failed to preprocess dataset: {e}")

    def _fallback_column_mapping(self, df, format_type: str) -> Optional[Dict[str, str]]:
        """
        Intelligent fallback for column mapping when auto-detection fails

        Tries multiple strategies:
        1. Case-insensitive matching
        2. Partial substring matching
        3. Position-based fallback (first N columns)

        Args:
            df: DataFrame to map
            format_type: Target format type

        Returns:
            Column mapping dict or None if no fallback possible
        """
        import pandas as pd
        from typing import Optional, Dict

        logger.info(f"🔍 Attempting intelligent fallback for format: {format_type}")

        cols = list(df.columns)
        cols_lower = {col.lower(): col for col in cols}

        # Strategy 1: Enhanced fuzzy matching with common synonyms
        synonyms = {
            "qa": {
                "question_col": ["question", "q", "query", "input", "prompt", "user", "user_query"],
                "answer_col": ["answer", "a", "response", "output", "assistant", "reply", "answer_text"]
            },
            "instruction": {
                "instruction_col": ["instruction", "question", "prompt", "input", "query", "task"],
                "response_col": ["response", "answer", "output", "completion", "reply", "assistant"]
            },
            "classification": {
                "text_col": ["text", "content", "sentence", "document", "input"],
                "label_col": ["label", "category", "class", "tag", "target"]
            },
            "summarization": {
                "document_col": ["document", "text", "article", "content", "source"],
                "summary_col": ["summary", "abstract", "synopsis", "tldr"]
            },
            "preference": {
                "prompt_col": ["prompt", "question", "instruction", "input"],
                "chosen_col": ["chosen", "preferred", "positive", "winner"],
                "rejected_col": ["rejected", "negative", "loser"]
            }
        }

        if format_type not in synonyms:
            logger.warning(f"No fallback strategy for format: {format_type}")
            return None

        mapping = {}
        expected_fields = synonyms[format_type]

        # Try to match each expected field
        for field_name, possible_names in expected_fields.items():
            matched = False
            for possible in possible_names:
                # Direct case-insensitive match
                if possible.lower() in cols_lower:
                    mapping[field_name] = cols_lower[possible.lower()]
                    matched = True
                    break

                # Partial match (column contains synonym)
                for col_lower, col_original in cols_lower.items():
                    if possible in col_lower or col_lower in possible:
                        mapping[field_name] = col_original
                        matched = True
                        break

                if matched:
                    break

        # Strategy 2: Position-based fallback if we have enough columns
        required_fields = [f for f in expected_fields.keys() if "input" not in f]  # input_col is optional

        if len(mapping) < len(required_fields) and len(cols) >= len(required_fields):
            logger.warning(f"⚠️  Fuzzy matching incomplete ({len(mapping)}/{len(required_fields)}), using position-based fallback")

            # Map first N columns to required fields
            mapping = {}
            for i, field_name in enumerate(required_fields):
                if i < len(cols):
                    mapping[field_name] = cols[i]
                    logger.info(f"   Mapping column {i} ('{cols[i]}') → {field_name}")

        if len(mapping) >= len(required_fields):
            logger.info(f"✅ Fallback mapping successful: {mapping}")
            return mapping

        logger.error(f"❌ Fallback failed: mapped {len(mapping)}/{len(required_fields)} required fields")
        return None

    def _infer_format_type(self, columns: list) -> str:
        """
        Infer the training format type from dataset columns

        Args:
            columns: List of column names

        Returns:
            Format type string (qa, instruction, classification, etc.)
        """
        cols_lower = set(col.lower() for col in columns)

        # QA detection
        if "question" in cols_lower and "answer" in cols_lower:
            return "qa"

        # Instruction detection
        if "instruction" in cols_lower and "response" in cols_lower:
            return "instruction"

        # Classification detection
        if "text" in cols_lower and "label" in cols_lower:
            return "classification"

        # Default to instruction (most flexible)
        logger.warning(f"Could not infer format from columns: {columns}, defaulting to 'instruction'")
        return "instruction"

    async def execute_training(
        self,
        job_id: str,
        trainer_script: str,
        config: Dict[str, Any],
        memory_required_gb: float = 6.0,
        memory_limit: str = "24g",
        timeout_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Execute training in GPU-enabled container with automatic GPU allocation

        Args:
            job_id: Job identifier
            trainer_script: Training script to run (peft_trainer.py, sft_trainer.py, etc.)
            config: Training configuration
            memory_required_gb: GPU memory required in GB (default: 6GB for 7B models with 4-bit quant)
            memory_limit: Container memory limit (e.g., "24g")
            timeout_hours: Training timeout in hours

        Returns:
            Training result with metrics and paths
        """
        from app.services.finetuning.gpu_pool_manager import gpu_pool_manager

        logger.info(f"🚀 Starting training job {job_id} (requires {memory_required_gb}GB GPU VRAM)")

        # ✨ NEW: Allocate GPU from pool
        gpu_devices_list = await gpu_pool_manager.allocate_gpu(
            job_id=job_id,
            count=1,
            memory_required_gb=memory_required_gb
        )

        # If no GPU available, wait in queue
        if not gpu_devices_list:
            logger.info(f"⏳ No GPU available, waiting in queue for job {job_id}...")
            gpu_devices_list = await gpu_pool_manager.wait_for_gpu(
                job_id=job_id,
                count=1,
                memory_required_gb=memory_required_gb,
                timeout_seconds=3600  # 1 hour wait timeout
            )

        if not gpu_devices_list:
            logger.error(f"❌ GPU allocation timeout for job {job_id}")
            return {
                "success": False,
                "error": f"GPU allocation timeout - no GPU available after 1 hour wait",
                "job_id": job_id
            }

        # Convert list to comma-separated string for CUDA_VISIBLE_DEVICES
        gpu_devices = ",".join(gpu_devices_list)
        logger.info(f"✅ Allocated GPU {gpu_devices} to job {job_id}")

        # ✅ FIX: Validate dataset exists in MinIO BEFORE starting training
        dataset_minio_path = config.get("dataset_minio_path")
        if dataset_minio_path:
            self._log_debug(job_id, "🔍 Validating dataset exists in MinIO")
            logger.info(f"🔍 Validating dataset exists in MinIO before training...")
            try:
                stat = await asyncio.to_thread(
                    self.minio_client.stat_object,
                    bucket_name=self.minio_bucket,
                    object_name=dataset_minio_path
                )
                self._log_debug(job_id, f"✅ Dataset found: {dataset_minio_path} ({stat.size:,} bytes)")
                logger.info(f"✅ Dataset found in MinIO: {dataset_minio_path}")
                logger.info(f"   Size: {stat.size:,} bytes")
                logger.info(f"   Last modified: {stat.last_modified}")
            except Exception as e:
                self._log_debug(job_id, f"❌ Dataset NOT found: {dataset_minio_path}")
                logger.error(f"❌ Dataset NOT found in MinIO!")
                logger.error(f"   Bucket: {self.minio_bucket}")
                logger.error(f"   Object: {dataset_minio_path}")
                logger.error(f"   Error: {e}")

                # Release GPU before returning
                await gpu_pool_manager.release_gpu(job_id)

                return {
                    "success": False,
                    "error": f"Dataset not found in MinIO: {dataset_minio_path}. Error: {str(e)}",
                    "job_id": job_id
                }

        # Create workspace with dataset download
        # Use dataset_minio_path for download (MinIO object path)
        # dataset_path contains the local filesystem path for the trainer
        workspace = await self.create_training_workspace(job_id, dataset_path=dataset_minio_path)

        # ✅ FIX #3: Preprocess the dataset with comprehensive verification
        if dataset_minio_path:
            # List ALL files in input directory for debugging
            dataset_files = list(workspace["input"].glob("*"))
            self._log_debug(job_id, f"📁 Files in input directory: {[f.name for f in dataset_files]}")
            logger.info(f"📁 Files in input directory after download: {[f.name for f in dataset_files]}")

            if not dataset_files:
                self._log_debug(job_id, f"❌ No files found in input directory!")
                logger.error(f"❌ No files found in input directory after dataset download!")
                logger.error(f"   Dataset path: {dataset_minio_path}")
                logger.error(f"   Input directory: {workspace['input']}")

                # Release GPU before returning
                await gpu_pool_manager.release_gpu(job_id)

                return {
                    "success": False,
                    "error": f"Dataset download failed - no files in input directory after downloading {dataset_minio_path}",
                    "job_id": job_id
                }

            # Filter to find the dataset file (exclude train.json which we'll create)
            dataset_file = None
            for f in dataset_files:
                if f.suffix in ['.csv', '.jsonl', '.json'] and 'train.json' not in f.name:
                    dataset_file = f
                    break

            if not dataset_file:
                self._log_debug(job_id, f"❌ Could not find dataset file!")
                logger.error(f"❌ Could not find dataset file in input directory!")
                logger.error(f"   Files present: {[f.name for f in dataset_files]}")
                logger.error(f"   Looking for: .csv, .jsonl, or .json files (excluding train.json)")

                # Release GPU before returning
                await gpu_pool_manager.release_gpu(job_id)

                return {
                    "success": False,
                    "error": f"Dataset file not found after download. Files present: {[f.name for f in dataset_files]}",
                    "job_id": job_id
                }

            self._log_debug(job_id, f"✅ Found dataset file: {dataset_file.name} ({dataset_file.stat().st_size:,} bytes)")
            logger.info(f"✅ Found dataset file: {dataset_file.name} ({dataset_file.stat().st_size:,} bytes)")

            # Preprocess the dataset
            training_objective = config.get("training_objective", "instruction")
            self._log_debug(job_id, f"🔄 Preprocessing dataset (objective: {training_objective})")
            logger.info(f"🔄 Preprocessing dataset for training_objective: {training_objective}")

            try:
                await self._preprocess_dataset_for_training(
                    dataset_file,
                    workspace["input"],
                    training_objective
                )

                # ✅ VERIFY: Check that train.json was created
                train_json = workspace["input"] / "train.json"
                if not train_json.exists():
                    self._log_debug(job_id, f"❌ Preprocessing failed - train.json not created!")
                    logger.error(f"❌ Preprocessing failed - train.json not created!")
                    logger.error(f"   Dataset file: {dataset_file}")
                    logger.error(f"   Expected output: {train_json}")

                    # Release GPU before returning
                    await gpu_pool_manager.release_gpu(job_id)

                    return {
                        "success": False,
                        "error": "Dataset preprocessing failed - train.json not created",
                        "job_id": job_id
                    }

                train_json_size = train_json.stat().st_size
                self._log_debug(job_id, f"✅ Preprocessing complete: train.json ({train_json_size:,} bytes)")
                logger.info(f"✅ Preprocessing complete: train.json created ({train_json_size:,} bytes)")

                # Try to count samples (for informational logging)
                try:
                    with open(train_json, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            self._log_debug(job_id, f"   Dataset contains {len(data)} samples")
                            logger.info(f"   Dataset contains {len(data)} samples")
                        elif isinstance(data, dict):
                            logger.info(f"   Dataset keys: {list(data.keys())}")
                except Exception as count_error:
                    logger.warning(f"⚠️  Could not count samples: {count_error}")

            except Exception as e:
                self._log_debug(job_id, f"❌ Preprocessing failed: {e}")
                logger.error(f"❌ Dataset preprocessing failed with error!")
                logger.error(f"   Dataset file: {dataset_file}")
                logger.error(f"   Training objective: {training_objective}")
                logger.error(f"   Error: {e}")

                # Release GPU before returning
                await gpu_pool_manager.release_gpu(job_id)

                return {
                    "success": False,
                    "error": f"Dataset preprocessing failed: {str(e)}",
                    "job_id": job_id
                }

        # ✅ FIX #7: Override dataset_path AND log every step to debug why it's not persisting
        logger.info(f"🔍 DEBUG FIX #7: BEFORE override, config['dataset_path'] = {config.get('dataset_path')}")
        config["dataset_path"] = f"/workspace/finetuning/{job_id}/input"
        logger.info(f"🔍 DEBUG FIX #7: AFTER override, config['dataset_path'] = {config['dataset_path']}")

        # Save training config
        config_file = workspace["input"] / "training_config.json"
        logger.info(f"🔍 DEBUG FIX #7: About to write config to {config_file}")
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"🔍 DEBUG FIX #7: Config file written successfully")

        # Verify what was actually written
        with open(config_file, 'r') as f:
            written_config = json.load(f)
            logger.info(f"🔍 DEBUG FIX #7: VERIFICATION - File contains dataset_path = {written_config.get('dataset_path')}")
            if written_config.get('dataset_path') != f"/workspace/finetuning/{job_id}/input":
                logger.error(f"❌ DEBUG FIX #7: MISMATCH! We set it to /workspace/finetuning/{job_id}/input but file has {written_config.get('dataset_path')}")

        # Build environment variables
        env_vars = {
            "JOB_ID": job_id,
            "CUDA_VISIBLE_DEVICES": gpu_devices,
            "PYTHONUNBUFFERED": "1",
            "DATASET_PATH": f"/workspace/finetuning/{job_id}/input",  # ✅ FIX: Explicit dataset path
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
            self._log_debug(job_id, f"🚀 Starting training container")
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
                # Mount the same Docker volume that celery worker uses
                volumes={
                    "chatbot_finetuning_workspaces": {  # Docker volume name from docker-compose.yml
                        'bind': '/workspace/finetuning',
                        'mode': 'rw'
                    }
                    # ✅ FIX: Removed backend mount - use trainers baked into finetuning-runtime image
                    # This prevents agent runtime code from overwriting finetuning trainer code
                },

                # Override default entrypoint to run trainer directly
                entrypoint=[],

                # Command: run trainer script (Python script handles logging internally)
                # Use full paths since we mount the entire volume, not just the job directory
                command=[
                    "python",
                    f"/app/app/services/finetuning/trainers/{trainer_script}",
                    "--config", f"/workspace/finetuning/{job_id}/input/training_config.json",
                    "--output", f"/workspace/finetuning/{job_id}/output",
                    "--log-dir", f"/workspace/finetuning/{job_id}/logs"
                ],

                stdin_open=False,
            )

            self._log_debug(job_id, f"✅ Container started: {container.short_id}")
            logger.info(f"✅ Training container {container.short_id} started")

            # Create log file path
            log_file = workspace["logs"] / "training.log"

            # Create database update callback for real-time progress tracking
            async def update_job_progress(**kwargs):
                """Update job progress in database in real-time"""
                try:
                    from app.models.finetuning_models import FineTuningJob
                    from app.core.database import get_async_session_maker
                    from sqlalchemy import update

                    SessionLocal = get_async_session_maker()
                    async with SessionLocal() as db:
                        stmt = update(FineTuningJob).where(
                            FineTuningJob.id == job_id
                        ).values(**kwargs)
                        await db.execute(stmt)
                        await db.commit()
                        logger.debug(f"Updated job {job_id} progress: {kwargs}")
                except Exception as e:
                    logger.error(f"Failed to update job progress: {e}")

            # Start log streamer in background
            log_streamer = TrainingLogStreamer(
                container=container,
                log_file=log_file,
                job_id=job_id,
                db_callback=update_job_progress
            )

            # Launch log streaming as background task
            log_task = asyncio.create_task(log_streamer.stream_logs())

            logger.info(f"📡 Log streaming started for job {job_id}")

            # Wait for completion (with timeout)
            timeout_seconds = timeout_hours * 3600
            logger.info(f"⏳ Waiting for training to complete (timeout: {timeout_hours}h)...")

            exit_status = await asyncio.to_thread(
                container.wait,
                timeout=timeout_seconds
            )

            # Stop log streaming
            log_streamer.stop()
            await log_task

            # Read logs from file (now contains all logs written in real-time)
            logs_text = log_file.read_text() if log_file.exists() else ""

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
            # Stop log streaming
            if 'log_streamer' in locals():
                log_streamer.stop()
            if 'log_task' in locals():
                await log_task
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
            # ✨ NEW: Always release GPU
            try:
                await gpu_pool_manager.release_gpu(job_id)
                logger.info(f"🔓 Released GPU allocation for job {job_id}")
            except Exception as e:
                logger.warning(f"Failed to release GPU for job {job_id}: {e}")

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
        minio_base_path: str
    ) -> Dict[str, Any]:
        """
        Upload trained model checkpoint to MinIO

        Args:
            job_id: Job identifier
            minio_base_path: Base path in MinIO (e.g., "finetuning/checkpoints/job-123")

        Returns:
            Dictionary with upload status and file list

        Raises:
            ValueError: If MinIO client not initialized or checkpoint dir missing
        """
        if not self.minio_client:
            raise ValueError("MinIO client not initialized")

        workspace = Path(f"/tmp/finetuning_workspaces/{job_id}")
        checkpoint_dir = workspace / "output"

        if not checkpoint_dir.exists():
            logger.error(f"Checkpoint directory not found: {checkpoint_dir}")
            raise ValueError(f"Checkpoint directory not found: {checkpoint_dir}")

        try:
            logger.info(f"📤 Uploading checkpoint from {checkpoint_dir} to MinIO: {minio_base_path}")

            uploaded_files = []
            total_size = 0

            # Upload all files in checkpoint directory
            for file_path in checkpoint_dir.rglob("*"):
                if file_path.is_file():
                    # Calculate relative path within checkpoint dir
                    relative_path = file_path.relative_to(checkpoint_dir)
                    minio_object_path = f"{minio_base_path}/{relative_path}"

                    # Upload file
                    await asyncio.to_thread(
                        self.minio_client.fput_object,
                        bucket_name=self.minio_bucket,
                        object_name=minio_object_path,
                        file_path=str(file_path)
                    )

                    file_size = file_path.stat().st_size
                    total_size += file_size
                    uploaded_files.append({
                        "filename": str(relative_path),
                        "minio_path": minio_object_path,
                        "size_bytes": file_size
                    })

                    logger.debug(f"  ✓ Uploaded {relative_path} ({file_size} bytes)")

            logger.info(
                f"✅ Successfully uploaded {len(uploaded_files)} files "
                f"({total_size / 1024 / 1024:.2f} MB) to MinIO"
            )

            return {
                "success": True,
                "uploaded_files": uploaded_files,
                "total_files": len(uploaded_files),
                "total_size_bytes": total_size,
                "base_path": minio_base_path
            }

        except S3Error as e:
            logger.error(f"❌ MinIO upload failed: {e}")
            return {
                "success": False,
                "error": f"MinIO upload failed: {str(e)}",
                "uploaded_files": uploaded_files  # Partial upload list
            }
        except Exception as e:
            logger.error(f"❌ Failed to upload checkpoint: {e}")
            return {
                "success": False,
                "error": str(e),
                "uploaded_files": uploaded_files
            }

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
