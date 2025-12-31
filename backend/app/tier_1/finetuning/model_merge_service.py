"""
LoRA Adapter Merge Service

Merges LoRA adapters with base models to create full model weights.

JIRA: FINETUNE-002
Author: AI Assistant
Date: 2025-12-22
"""

import logging
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from sqlalchemy.orm import Session
from sqlalchemy import update

from app.models.finetuning_models import FineTunedModel
from minio import Minio
from minio.error import S3Error
from app.core.config import settings

logger = logging.getLogger(__name__)


class ModelMergeService:
    """
    Service for merging LoRA adapters with base models.

    Key Features:
    - Works with local workspace paths (/workspace/finetuning)
    - Loads base model from HuggingFace
    - Merges using PEFT's merge_and_unload()
    - Saves to workspace for deployment optimization
    - Updates database with merge status
    """

    def __init__(self, db: Session):
        self.db = db
        self.minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.workspace_root = Path("/workspace/finetuning")

    async def merge_lora_adapters(
        self,
        model_id: str,
        base_model_name: str = "Qwen/Qwen2.5-1.5B-Instruct",
        force_cpu: bool = False
    ) -> Dict[str, Any]:
        """
        Merge LoRA adapters with base model.

        Args:
            model_id: ID of the fine-tuned model
            base_model_name: HuggingFace model name
            force_cpu: Force CPU-only merge (for testing)

        Returns:
            dict: Merge result with status, path, duration

        Critical Path:
            Must save to /workspace/finetuning/{job_id}/output/merged_model
            OllamaDeploymentService checks this path FIRST!
        """
        start_time = time.time()

        try:
            # 1. Get model record
            model = self.db.query(FineTunedModel).filter(
                FineTunedModel.id == model_id
            ).first()

            if not model:
                raise ValueError(f"Model {model_id} not found")

            if not model.minio_checkpoint_path:
                raise ValueError(f"Model {model_id} has no checkpoint path")

            # Update status to 'merging'
            await self._update_merge_status(
                model_id=model_id,
                status="merging",
                merge_requested_at=datetime.utcnow()
            )

            logger.info(f"🔄 Starting merge for model {model_id}")
            logger.info(f"   Base model: {base_model_name}")
            logger.info(f"   Adapter path: {model.minio_checkpoint_path}")

            # 2. Extract job_id from MinIO path
            job_id = self._extract_job_id(model.minio_checkpoint_path)
            workspace_path = self.workspace_root / job_id / "output"
            merged_output_path = workspace_path / "merged_model"

            # Create output directory
            merged_output_path.mkdir(parents=True, exist_ok=True)

            logger.info(f"📁 Workspace: {workspace_path}")
            logger.info(f"📁 Merge output: {merged_output_path}")

            # 3. Download adapter from MinIO
            adapter_local_path = await self._download_adapter(
                minio_path=model.minio_checkpoint_path,
                local_path=workspace_path / "adapter_model"
            )

            logger.info(f"✅ Adapter downloaded to: {adapter_local_path}")

            # 4. Determine device
            device = self._get_device(force_cpu)
            logger.info(f"🖥️  Device: {device}")

            # 5. Load base model
            logger.info(f"📦 Loading base model: {base_model_name}")
            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_name,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map="auto" if device == "cuda" else None,
                trust_remote_code=True
            )

            tokenizer = AutoTokenizer.from_pretrained(
                base_model_name,
                trust_remote_code=True
            )

            logger.info(f"✅ Base model loaded")

            # 6. Load adapter
            logger.info(f"🔗 Loading LoRA adapter from: {adapter_local_path}")
            model_with_adapter = PeftModel.from_pretrained(
                base_model,
                str(adapter_local_path),
                torch_dtype=torch.float16 if device == "cuda" else torch.float32
            )

            logger.info(f"✅ Adapter loaded")

            # 7. Merge adapter with base model
            logger.info(f"🔄 Merging adapter with base model...")
            merged_model = model_with_adapter.merge_and_unload()

            logger.info(f"✅ Merge complete!")

            # 8. Save merged model
            logger.info(f"💾 Saving merged model to: {merged_output_path}")
            merged_model.save_pretrained(str(merged_output_path))
            tokenizer.save_pretrained(str(merged_output_path))

            logger.info(f"✅ Merged model saved")

            # 9. Calculate duration
            duration_seconds = int(time.time() - start_time)

            # 10. Update database
            merged_model_path = f"/workspace/finetuning/{job_id}/output/merged_model"
            await self._update_merge_status(
                model_id=model_id,
                status="merged",
                merged_model_path=merged_model_path,
                merge_duration_seconds=duration_seconds
            )

            logger.info(f"✅ Merge complete for model {model_id}")
            logger.info(f"   Duration: {duration_seconds}s")
            logger.info(f"   Output: {merged_model_path}")

            return {
                "status": "success",
                "model_id": model_id,
                "merged_model_path": merged_model_path,
                "duration_seconds": duration_seconds,
                "message": f"Model merged successfully in {duration_seconds}s"
            }

        except Exception as e:
            logger.error(f"❌ Merge failed for model {model_id}: {e}", exc_info=True)

            # Update database with error
            await self._update_merge_status(
                model_id=model_id,
                status="merge_failed",
                merge_error_message=str(e)
            )

            return {
                "status": "error",
                "model_id": model_id,
                "error": str(e),
                "message": f"Merge failed: {e}"
            }

    async def _download_adapter(
        self,
        minio_path: str,
        local_path: Path
    ) -> Path:
        """
        Download adapter from MinIO.

        Args:
            minio_path: MinIO path (e.g., minio://documents/...)
            local_path: Local destination path

        Returns:
            Path: Local path to downloaded adapter
        """
        # Create local directory
        local_path.mkdir(parents=True, exist_ok=True)

        # Parse MinIO path
        if minio_path.startswith("minio://"):
            minio_path = minio_path[8:]  # Remove minio:// prefix

        # Download from MinIO
        # Format: documents/technology/itm11/global/admin/finetuning/datasets/.../checkpoints/{job_name}/{job_id}/final/adapter_model/
        logger.info(f"📥 Downloading adapter from MinIO: {minio_path}")

        # Get list of files in adapter directory
        bucket_name = minio_path.split("/")[0]
        object_prefix = "/".join(minio_path.split("/")[1:])

        # Fix: If path ends with a filename (e.g., adapter_model.safetensors), remove it to get directory
        # Database stores: .../adapter_model/adapter_model.safetensors
        # We need: .../adapter_model/
        if object_prefix.endswith(".safetensors") or object_prefix.endswith(".json"):
            # Remove trailing filename to get directory path
            object_prefix = "/".join(object_prefix.split("/")[:-1])
            logger.info(f"📁 Extracted directory path: {object_prefix}")

        # Download all files in adapter_model directory
        adapter_files = [
            "adapter_model.safetensors",
            "adapter_config.json",
            "tokenizer_config.json",
            "tokenizer.json",
            "special_tokens_map.json",
            "vocab.json",
            "merges.txt"
        ]

        for filename in adapter_files:
            object_path = f"{object_prefix}/{filename}"
            local_file = local_path / filename

            try:
                self.minio_client.fget_object(
                    bucket_name,
                    object_path,
                    str(local_file)
                )
                logger.info(f"   ✓ Downloaded: {filename}")
            except Exception as e:
                # Some files may not exist (e.g., vocab.json for some tokenizers)
                logger.warning(f"   ⚠️  Could not download {filename}: {e}")

        return local_path

    def _extract_job_id(self, minio_path: str) -> str:
        """
        Extract job_id from MinIO checkpoint path.

        Args:
            minio_path: MinIO path with job_id

        Returns:
            str: Job ID (UUID format)

        Example:
            Input: minio://documents/.../checkpoints/training36/427b1025-57db-45de-826c-3713fc8ecb19/final/adapter_model/
            Output: 427b1025-57db-45de-826c-3713fc8ecb19
        """
        import re

        # Extract UUID pattern
        uuid_pattern = r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
        match = re.search(uuid_pattern, minio_path)

        if match:
            return match.group(1)

        raise ValueError(f"Could not extract job_id from path: {minio_path}")

    def _get_device(self, force_cpu: bool = False) -> str:
        """
        Determine device for merge operation.

        Args:
            force_cpu: Force CPU-only merge

        Returns:
            str: 'cuda' or 'cpu'
        """
        if force_cpu:
            return "cpu"

        if torch.cuda.is_available():
            return "cuda"

        return "cpu"

    async def _update_merge_status(
        self,
        model_id: str,
        status: str,
        merged_model_path: Optional[str] = None,
        merge_duration_seconds: Optional[int] = None,
        merge_requested_at: Optional[datetime] = None,
        merge_error_message: Optional[str] = None
    ):
        """
        Update merge status in database.

        Args:
            model_id: Model ID
            status: Merge status (merging, merged, merge_failed)
            merged_model_path: Path to merged model
            merge_duration_seconds: Duration of merge operation
            merge_requested_at: Timestamp when merge was requested
            merge_error_message: Error message if failed
        """
        update_data = {"status": status}

        if merged_model_path:
            update_data["merged_model_path"] = merged_model_path

        if merge_duration_seconds is not None:
            update_data["merge_duration_seconds"] = merge_duration_seconds

        if merge_requested_at:
            update_data["merge_requested_at"] = merge_requested_at

        if merge_error_message:
            update_data["merge_error_message"] = merge_error_message

        stmt = (
            update(FineTunedModel)
            .where(FineTunedModel.id == model_id)
            .values(**update_data)
        )

        self.db.execute(stmt)
        self.db.commit()

        logger.info(f"📝 Database updated: model={model_id}, status={status}")

    async def get_merge_status(self, model_id: str) -> Dict[str, Any]:
        """
        Get merge status for a model.

        Args:
            model_id: Model ID

        Returns:
            dict: Merge status information
        """
        model = self.db.query(FineTunedModel).filter(
            FineTunedModel.id == model_id
        ).first()

        if not model:
            return {
                "status": "not_found",
                "error": f"Model {model_id} not found"
            }

        return {
            "model_id": model_id,
            "status": model.status,
            "merged_model_path": model.merged_model_path,
            "merge_duration_seconds": model.merge_duration_seconds,
            "merge_requested_at": model.merge_requested_at.isoformat() if model.merge_requested_at else None,
            "merge_error_message": model.merge_error_message
        }
