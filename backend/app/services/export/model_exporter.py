"""
Model Exporter Service

Exports fine-tuned models and model artifacts for standalone deployment.

This service handles:
1. Fine-tuned LLM models (LoRA adapters, full models)
2. Embedding models (if custom)
3. Model configuration and metadata
4. Model serving configuration (vLLM, TensorRT, etc.)

Author: Claude Code
Date: 2026-01-04
Phase: Model Export Enhancement
"""

import logging
import shutil
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.finetuning_models import FineTuningJob

logger = logging.getLogger(__name__)


@dataclass
class ModelExportInfo:
    """Information about an exported model."""
    model_type: str  # "llm", "embedding", "classifier"
    model_name: str
    model_path: str
    adapter_path: Optional[str] = None
    config_path: Optional[str] = None
    size_bytes: int = 0
    is_finetuned: bool = False
    base_model: Optional[str] = None


class ModelExporter:
    """Export fine-tuned models for standalone deployment."""

    def __init__(self, db: AsyncSession):
        """
        Initialize ModelExporter.

        Args:
            db: Async database session
        """
        self.db = db

    async def export_module_models(
        self,
        module_name: str,
        export_dir: Path,
        config: Dict[str, Any]
    ) -> List[ModelExportInfo]:
        """
        Export all models used by a module.

        Args:
            module_name: Module identifier
            export_dir: Directory to export models to
            config: Module configuration containing model references

        Returns:
            List of ModelExportInfo for exported models
        """
        logger.info(f"🤖 Exporting models for module: {module_name}")

        models_dir = export_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)

        exported_models = []

        # 1. Check if module uses fine-tuned LLM
        if "llm" in config and config["llm"].get("model_name"):
            llm_model = await self._export_llm_model(
                config["llm"],
                models_dir
            )
            if llm_model:
                exported_models.append(llm_model)

        # 2. Check if module uses custom embedding model
        if "embedding" in config and config["embedding"].get("model_name"):
            embedding_model = await self._export_embedding_model(
                config["embedding"],
                models_dir
            )
            if embedding_model:
                exported_models.append(embedding_model)

        # 3. Check for module-specific classifiers or custom models
        if "custom_models" in config:
            for model_config in config["custom_models"]:
                custom_model = await self._export_custom_model(
                    model_config,
                    models_dir
                )
                if custom_model:
                    exported_models.append(custom_model)

        # 4. Generate model serving configuration
        if exported_models:
            await self._generate_model_serving_config(
                models_dir,
                exported_models
            )

        total_size = sum(m.size_bytes for m in exported_models)
        logger.info(f"✅ Exported {len(exported_models)} models")
        logger.info(f"   Total size: {total_size / (1024**3):.2f} GB")

        return exported_models

    async def _export_llm_model(
        self,
        llm_config: Dict[str, Any],
        models_dir: Path
    ) -> Optional[ModelExportInfo]:
        """
        Export LLM model (fine-tuned or base model).

        Args:
            llm_config: LLM configuration from module config
            models_dir: Directory to export to

        Returns:
            ModelExportInfo if model exported, None if using API
        """
        model_name = llm_config.get("model_name", "")
        provider = llm_config.get("provider", "openai")

        logger.info(f"   LLM: {model_name} (provider: {provider})")

        # If using API providers (OpenAI, Claude), no export needed
        if provider in ["openai", "anthropic", "cohere"]:
            logger.info(f"   → Using API provider, no model export needed")
            return None

        # If using local model or fine-tuned model
        if provider in ["ollama", "vllm", "local"]:
            # Check if this is a fine-tuned model
            finetuned_job = await self._get_finetuned_job(model_name)

            if finetuned_job:
                return await self._export_finetuned_model(
                    finetuned_job,
                    models_dir
                )
            else:
                # Base model - just export configuration
                return await self._export_base_model_config(
                    model_name,
                    provider,
                    models_dir
                )

        return None

    async def _get_finetuned_job(
        self,
        model_name: str
    ) -> Optional[FineTuningJob]:
        """
        Get fine-tuning job by model name.

        Args:
            model_name: Name of the model

        Returns:
            FineTuningJob if found, None otherwise
        """
        try:
            result = await self.db.execute(
                select(FineTuningJob).where(
                    FineTuningJob.model_name == model_name,
                    FineTuningJob.status == "completed"
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.warning(f"   Error checking for fine-tuned model: {e}")
            return None

    async def _export_finetuned_model(
        self,
        job: FineTuningJob,
        models_dir: Path
    ) -> ModelExportInfo:
        """
        Export fine-tuned model artifacts.

        Args:
            job: Fine-tuning job record
            models_dir: Directory to export to

        Returns:
            ModelExportInfo with export details
        """
        logger.info(f"   → Exporting fine-tuned model: {job.model_name}")

        model_dir = models_dir / job.model_name
        model_dir.mkdir(parents=True, exist_ok=True)

        total_size = 0

        # 1. Export LoRA adapter (if using LoRA)
        adapter_path = None
        if job.training_config.get("use_lora", False):
            # LoRA adapters are typically small (few MB)
            adapter_source = Path(job.output_dir) / "adapter_model"
            if adapter_source.exists():
                adapter_dest = model_dir / "adapter_model"
                shutil.copytree(adapter_source, adapter_dest, dirs_exist_ok=True)
                adapter_path = str(adapter_dest.relative_to(models_dir))

                adapter_size = sum(
                    f.stat().st_size for f in adapter_dest.rglob('*') if f.is_file()
                )
                total_size += adapter_size
                logger.info(f"      ✓ LoRA adapter: {adapter_size / (1024**2):.1f} MB")

        # 2. Export full model (if available and not too large)
        model_path = None
        full_model_source = Path(job.output_dir) / "final_model"
        if full_model_source.exists():
            # Check size before copying (don't export if > 50GB)
            model_size = sum(
                f.stat().st_size for f in full_model_source.rglob('*') if f.is_file()
            )

            if model_size < 50 * 1024**3:  # 50 GB limit
                model_dest = model_dir / "model"
                shutil.copytree(full_model_source, model_dest, dirs_exist_ok=True)
                model_path = str(model_dest.relative_to(models_dir))
                total_size += model_size
                logger.info(f"      ✓ Full model: {model_size / (1024**3):.2f} GB")
            else:
                logger.warning(f"      ⚠️  Model too large ({model_size / (1024**3):.1f} GB), including download instructions instead")
                await self._create_model_download_instructions(
                    model_dir / "DOWNLOAD_MODEL.md",
                    job
                )

        # 3. Export model configuration
        config_path = model_dir / "config.json"
        with open(config_path, 'w') as f:
            json.dump({
                "model_name": job.model_name,
                "base_model": job.base_model,
                "model_type": job.model_type,
                "training_config": job.training_config,
                "training_metrics": job.training_metrics,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "use_lora": job.training_config.get("use_lora", False),
                "lora_rank": job.training_config.get("lora_rank"),
                "lora_alpha": job.training_config.get("lora_alpha"),
            }, indent=2)

        logger.info(f"      ✓ Configuration exported")

        return ModelExportInfo(
            model_type="llm",
            model_name=job.model_name,
            model_path=model_path if model_path else "download_required",
            adapter_path=adapter_path,
            config_path=str(config_path.relative_to(models_dir)),
            size_bytes=total_size,
            is_finetuned=True,
            base_model=job.base_model
        )

    async def _export_base_model_config(
        self,
        model_name: str,
        provider: str,
        models_dir: Path
    ) -> ModelExportInfo:
        """
        Export configuration for base model (not fine-tuned).

        Args:
            model_name: Model name
            provider: Model provider
            models_dir: Directory to export to

        Returns:
            ModelExportInfo
        """
        logger.info(f"   → Exporting base model config: {model_name}")

        config_path = models_dir / f"{model_name.replace('/', '_')}_config.json"
        with open(config_path, 'w') as f:
            json.dump({
                "model_name": model_name,
                "provider": provider,
                "is_finetuned": False,
                "deployment_instructions": {
                    "ollama": f"ollama pull {model_name}",
                    "vllm": f"Download from HuggingFace: {model_name}",
                    "docker": f"Use pre-built image with {model_name}"
                }
            }, indent=2)

        return ModelExportInfo(
            model_type="llm",
            model_name=model_name,
            model_path="base_model_download_required",
            config_path=str(config_path.relative_to(models_dir)),
            size_bytes=0,
            is_finetuned=False,
            base_model=model_name
        )

    async def _export_embedding_model(
        self,
        embedding_config: Dict[str, Any],
        models_dir: Path
    ) -> Optional[ModelExportInfo]:
        """
        Export custom embedding model.

        Args:
            embedding_config: Embedding configuration
            models_dir: Directory to export to

        Returns:
            ModelExportInfo if custom model, None if using standard model
        """
        model_name = embedding_config.get("model_name", "")

        # Standard models don't need export (will be downloaded)
        standard_models = [
            "all-MiniLM-L6-v2",
            "all-mpnet-base-v2",
            "text-embedding-ada-002",
            "text-embedding-3-small"
        ]

        if any(std in model_name for std in standard_models):
            logger.info(f"   Embedding: {model_name} (standard model, no export needed)")
            return None

        # Export custom embedding model
        logger.info(f"   → Exporting custom embedding model: {model_name}")

        # TODO: Implement custom embedding model export if needed
        return None

    async def _export_custom_model(
        self,
        model_config: Dict[str, Any],
        models_dir: Path
    ) -> Optional[ModelExportInfo]:
        """
        Export custom module-specific model (classifier, etc.).

        Args:
            model_config: Model configuration
            models_dir: Directory to export to

        Returns:
            ModelExportInfo if exported
        """
        # TODO: Implement custom model export for classifiers, etc.
        return None

    async def _generate_model_serving_config(
        self,
        models_dir: Path,
        exported_models: List[ModelExportInfo]
    ):
        """
        Generate configuration for model serving (vLLM, Ollama, etc.).

        Args:
            models_dir: Models directory
            exported_models: List of exported models
        """
        # Generate vLLM config
        vllm_config = {
            "models": []
        }

        # Generate Ollama Modelfile
        ollama_modelfile = []

        for model in exported_models:
            if model.model_type == "llm" and model.is_finetuned:
                # vLLM configuration
                vllm_config["models"].append({
                    "name": model.model_name,
                    "model_path": model.model_path,
                    "adapter_path": model.adapter_path,
                    "base_model": model.base_model
                })

                # Ollama Modelfile (if using LoRA adapter)
                if model.adapter_path:
                    ollama_modelfile.append(f"# {model.model_name}")
                    ollama_modelfile.append(f"FROM {model.base_model}")
                    ollama_modelfile.append(f"ADAPTER ./{model.adapter_path}")
                    ollama_modelfile.append("")

        # Write vLLM config
        with open(models_dir / "vllm_config.json", 'w') as f:
            json.dump(vllm_config, f, indent=2)

        # Write Ollama Modelfile
        if ollama_modelfile:
            with open(models_dir / "Modelfile", 'w') as f:
                f.write('\n'.join(ollama_modelfile))

        logger.info(f"   ✓ Model serving configuration generated")

    async def _create_model_download_instructions(
        self,
        output_path: Path,
        job: FineTuningJob
    ):
        """
        Create instructions for downloading large models.

        Args:
            output_path: Path to write instructions
            job: Fine-tuning job
        """
        instructions = f"""# Download Instructions for {job.model_name}

The fine-tuned model is too large to include in the export package.

## Option 1: Download from MinIO (Recommended)

If you have access to the original platform's MinIO instance:

```bash
# Install MinIO client
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
sudo mv mc /usr/local/bin/

# Configure MinIO
mc alias set platform http://PLATFORM_MINIO_URL ACCESS_KEY SECRET_KEY

# Download model
mc cp --recursive platform/models/{job.model_name}/ ./models/{job.model_name}/
```

## Option 2: Download from Cloud Storage

If the model was uploaded to cloud storage:

```bash
# AWS S3
aws s3 cp s3://YOUR_BUCKET/models/{job.model_name}/ ./models/{job.model_name}/ --recursive

# Google Cloud Storage
gsutil -m cp -r gs://YOUR_BUCKET/models/{job.model_name}/ ./models/{job.model_name}/

# Azure Blob Storage
az storage blob download-batch --source models --destination ./models/{job.model_name}/ --pattern "{job.model_name}/*"
```

## Option 3: Use Base Model + LoRA Adapter

If only the LoRA adapter is included (check `adapter_model/` directory):

```bash
# The adapter is already included in this export
# You just need to download the base model: {job.base_model}

# Using Hugging Face
huggingface-cli download {job.base_model} --local-dir ./models/base/{job.base_model}

# Or using Ollama
ollama pull {job.base_model}
```

Then load the adapter on top of the base model at runtime.

## Model Details

- **Model Name**: {job.model_name}
- **Base Model**: {job.base_model}
- **Model Type**: {job.model_type}
- **Size**: Large (> 50GB)
- **Training Date**: {job.created_at.isoformat() if job.created_at else 'Unknown'}

## After Download

Once downloaded, update your `.env` file:

```
MODEL_PATH=./models/{job.model_name}
BASE_MODEL_PATH=./models/base/{job.base_model}
ADAPTER_PATH=./models/{job.model_name}/adapter_model
```

For support, contact your account manager.
"""

        with open(output_path, 'w') as f:
            f.write(instructions)
