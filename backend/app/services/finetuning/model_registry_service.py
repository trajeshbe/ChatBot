"""
Model Registry Service

Manages the registry of fine-tuned models including:
- Model registration from training jobs
- Model versioning and lineage tracking
- Deployment to Ollama/vLLM
- Usage tracking and analytics
- Model deprecation and archival

Extensible Design:
- Support for multiple deployment targets (via strategy pattern)
- Pluggable model loaders
- Version control and rollback capabilities
"""

from typing import Optional, Dict, Any, List
from uuid import UUID
import logging
from sqlalchemy.orm import Session
from datetime import datetime
import semver
import httpx
import asyncio
import os

from app.models.finetuning_models import (
    FineTunedModel,
    FineTuningJob
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class ModelDeploymentStrategy:
    """
    Base class for model deployment strategies

    Extend this class to add support for new deployment targets
    """

    async def deploy(
        self,
        model: FineTunedModel,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deploy a model

        Args:
            model: Model to deploy
            config: Deployment configuration

        Returns:
            Deployment result with URL and metadata
        """
        raise NotImplementedError("Subclasses must implement deploy()")

    async def undeploy(self, model: FineTunedModel) -> Dict[str, Any]:
        """Undeploy a model"""
        raise NotImplementedError("Subclasses must implement undeploy()")


class OllamaDeploymentStrategy(ModelDeploymentStrategy):
    """
    Deployment strategy for Ollama

    Supports two deployment modes:
    1. PEFT/LoRA: Keeps adapter separate, references base model
    2. Full FT: Deploys merged model
    """

    def __init__(self):
        self.ollama_base_url = settings.OLLAMA_BASE_URL or "http://rag-ollama:11434"
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 min timeout for model operations

    async def deploy(
        self,
        model: FineTunedModel,
        config: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        Deploy fine-tuned model to Ollama

        Process:
        1. Generate Ollama-compatible model name
        2. Check if base model exists in Ollama
        3. Create Modelfile with fine-tuned parameters
        4. Register model with Ollama

        For PEFT models: References base model + adapter info in system prompt
        For Full FT: Would need to merge and push (not implemented for consumer GPUs)

        Args:
            model: FineTunedModel to deploy
            config: Deployment configuration (temperature, context_length, etc.)
            db: Database session

        Returns:
            Deployment result with ollama_model_name and deployment_url
        """
        try:
            # Generate Ollama model name
            ollama_model_name = self._generate_model_name(model)

            logger.info(f"🚀 Deploying model {model.name} to Ollama as {ollama_model_name}")

            # Step 1: Check if base model exists in Ollama
            base_model_available = await self._check_base_model(model.base_model)

            if not base_model_available:
                logger.warning(f"Base model {model.base_model} not found in Ollama")
                # Attempt to pull base model
                await self._pull_base_model(model.base_model)

            # Step 2: Create Modelfile
            modelfile = await self._create_modelfile(model, config)

            # Step 3: Register with Ollama
            success = await self._register_with_ollama(ollama_model_name, modelfile)

            if success:
                logger.info(f"✅ Successfully deployed {ollama_model_name} to Ollama")

                return {
                    "status": "deployed",
                    "ollama_model_name": ollama_model_name,
                    "deployment_url": f"{self.ollama_base_url}/api/generate",
                    "deployment_target": "ollama",
                    "message": f"Model deployed successfully as {ollama_model_name}"
                }
            else:
                raise Exception("Failed to register model with Ollama")

        except Exception as e:
            logger.error(f"❌ Failed to deploy model to Ollama: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "deployment_target": "ollama"
            }

    async def undeploy(self, model: FineTunedModel) -> Dict[str, Any]:
        """
        Remove model from Ollama

        Args:
            model: FineTunedModel to undeploy

        Returns:
            Undeploy result
        """
        try:
            if not model.ollama_model_name:
                return {
                    "status": "success",
                    "message": "Model was not deployed to Ollama"
                }

            logger.info(f"🗑️  Undeploying model {model.ollama_model_name} from Ollama")

            # Call Ollama delete API
            response = await self.client.delete(
                f"{self.ollama_base_url}/api/delete",
                json={"name": model.ollama_model_name}
            )

            if response.status_code == 200:
                logger.info(f"✅ Successfully undeployed {model.ollama_model_name}")
                return {
                    "status": "success",
                    "message": f"Model {model.ollama_model_name} removed from Ollama"
                }
            else:
                raise Exception(f"Ollama returned status {response.status_code}")

        except Exception as e:
            logger.error(f"❌ Failed to undeploy model: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    def _generate_model_name(self, model: FineTunedModel) -> str:
        """
        Generate Ollama-compatible model name

        Format: {sanitized_name}-{version}
        Example: customer-support-qa-v1.0.0
        """
        # Sanitize model name
        sanitized = model.name.lower().replace(" ", "-").replace("_", "-")
        # Remove special characters
        sanitized = ''.join(c for c in sanitized if c.isalnum() or c == '-')

        return f"{sanitized}-{model.version}"

    async def _check_base_model(self, base_model: str) -> bool:
        """Check if base model exists in Ollama"""
        try:
            response = await self.client.get(f"{self.ollama_base_url}/api/tags")

            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])

                # Check if base model name exists
                for m in models:
                    if base_model.lower() in m.get("name", "").lower():
                        logger.info(f"✅ Base model {base_model} found in Ollama")
                        return True

                logger.warning(f"⚠️  Base model {base_model} not found in Ollama")
                return False

            return False
        except Exception as e:
            logger.error(f"Error checking base model: {e}")
            return False

    async def _pull_base_model(self, base_model: str):
        """Attempt to pull base model from Ollama library"""
        try:
            logger.info(f"📥 Attempting to pull base model {base_model}")

            # Try common model name mappings
            model_mappings = {
                "qwen-2.5-7b": "qwen2.5:7b",
                "llama-2-7b": "llama2:7b",
                "mistral-7b": "mistral:7b",
                "gemma-7b": "gemma:7b"
            }

            ollama_name = model_mappings.get(base_model.lower(), base_model)

            response = await self.client.post(
                f"{self.ollama_base_url}/api/pull",
                json={"name": ollama_name},
                timeout=600.0  # 10 min for model download
            )

            logger.info(f"Pull initiated for {ollama_name}")

        except Exception as e:
            logger.warning(f"Could not pull base model: {e}")

    async def _create_modelfile(self, model: FineTunedModel, config: Dict[str, Any]) -> str:
        """
        Create Ollama Modelfile for the fine-tuned model

        P0 FIX: Uses merged model directly from workspace (no MinIO download needed).
        Workspace is preserved after training for efficient deployment.

        Args:
            model: FineTunedModel to create Modelfile for
            config: Deployment configuration

        Returns:
            Modelfile content as string
        """
        # ========== P0 FIX: Use merged model directly from workspace ==========
        model_reference = None

        if model.job_id:
            # Check if merged model exists in workspace
            workspace_merged_path = f"/workspace/finetuning/{model.job_id}/output/merged_model"

            if os.path.exists(workspace_merged_path):
                logger.info(f"✅ Using merged fine-tuned model from workspace: {workspace_merged_path}")
                model_reference = workspace_merged_path
            else:
                logger.warning(f"⚠️  Workspace not found at {workspace_merged_path}")
                logger.warning(f"   This may happen if workspace was cleaned up before deployment")
                logger.warning(f"   Falling back to base model")

        if not model_reference:
            # Fallback to base model if workspace doesn't exist
            base_model_name = self._map_base_model_name(model.base_model)
            logger.warning(f"⚠️  Using base model: {base_model_name}")
            model_reference = base_model_name

        # Build Modelfile
        modelfile_lines = [
            f"FROM {model_reference}",
            "",
            "# Fine-tuned model configuration",
            f"# Original base: {model.base_model}",
            f"# Fine-tuning method: {model.finetuning_method}",
            f"# Version: {model.version}",
            "",
        ]

        # Add system prompt with fine-tuning context
        system_prompt = config.get("system_prompt", "") or self._generate_system_prompt(model)
        if system_prompt:
            modelfile_lines.append(f'SYSTEM """{system_prompt}"""')
            modelfile_lines.append("")

        # Add parameters
        temperature = config.get("temperature", 0.7)
        top_p = config.get("top_p", 0.9)
        top_k = config.get("top_k", 40)
        repeat_penalty = config.get("repeat_penalty", 1.1)

        modelfile_lines.extend([
            "# Model parameters",
            f"PARAMETER temperature {temperature}",
            f"PARAMETER top_p {top_p}",
            f"PARAMETER top_k {top_k}",
            f"PARAMETER repeat_penalty {repeat_penalty}",
            "",
        ])

        # Add stop sequences if provided
        stop_sequences = config.get("stop_sequences", [])
        for stop_seq in stop_sequences:
            modelfile_lines.append(f'PARAMETER stop "{stop_seq}"')

        return "\n".join(modelfile_lines)

    def _map_base_model_name(self, base_model: str) -> str:
        """Map our base model names to Ollama model names"""
        mappings = {
            "qwen-2.5-1.5b": "qwen2.5:1.5b",
            "qwen-2.5-1.5b-instruct": "qwen2.5:1.5b-instruct",
            "qwen-2.5-7b": "qwen2.5:7b",
            "qwen-2.5-7b-instruct": "qwen2.5:7b-instruct",
            "llama-2-7b": "llama2:7b",
            "llama-2-7b-chat": "llama2:7b-chat",
            "llama-2-13b": "llama2:13b",
            "mistral-7b": "mistral:7b",
            "mistral-7b-instruct": "mistral:7b-instruct",
            "gemma-7b": "gemma:7b",
            "gemma-2b": "gemma:2b",
        }

        return mappings.get(base_model.lower(), base_model)

    def _generate_system_prompt(self, model: FineTunedModel) -> str:
        """Generate system prompt that includes fine-tuning context"""
        prompt = f"You are a specialized AI assistant based on {model.base_model}. "

        if model.description:
            prompt += f"{model.description} "

        prompt += f"This model was fine-tuned using {model.finetuning_method.upper()} method"

        if model.eval_metrics:
            # Add performance context
            accuracy = model.eval_metrics.get("accuracy")
            if accuracy:
                prompt += f" with {accuracy*100:.1f}% accuracy"

        prompt += "."

        return prompt

    async def _register_with_ollama(self, model_name: str, modelfile: str) -> bool:
        """
        Register model with Ollama using Modelfile

        Args:
            model_name: Name to register model as
            modelfile: Modelfile content

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"📝 Registering model {model_name} with Ollama")
            logger.debug(f"Modelfile:\n{modelfile}")

            response = await self.client.post(
                f"{self.ollama_base_url}/api/create",
                json={
                    "name": model_name,
                    "modelfile": modelfile
                },
                timeout=300.0  # 5 min timeout
            )

            if response.status_code == 200:
                logger.info(f"✅ Model {model_name} registered successfully")
                return True
            else:
                logger.error(f"❌ Ollama returned status {response.status_code}: {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to register with Ollama: {e}")
            return False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()


class VLLMDeploymentStrategy(ModelDeploymentStrategy):
    """Deployment strategy for vLLM"""

    async def deploy(
        self,
        model: FineTunedModel,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deploy model to vLLM"""
        # TODO: Implement vLLM deployment
        vllm_model_name = f"{model.name}-{model.version}"

        logger.info(f"Deploying model {model.id} to vLLM as {vllm_model_name}")

        return {
            "deployment_url": "http://localhost:8000/v1/completions",
            "vllm_model_name": vllm_model_name,
            "status": "deployed"
        }

    async def undeploy(self, model: FineTunedModel) -> Dict[str, Any]:
        """Undeploy from vLLM"""
        logger.info(f"Undeploying model {model.id} from vLLM")

        return {"status": "undeployed"}


class ModelRegistryService:
    """
    Service for managing fine-tuned models

    This service provides:
    - Model registration from training jobs
    - Deployment management
    - Version control
    - Usage tracking
    """

    def __init__(self, db: Session):
        """
        Initialize model registry service

        Args:
            db: Database session
        """
        self.db = db

        # Deployment strategies
        self.deployment_strategies = {
            "ollama": OllamaDeploymentStrategy(),
            "vllm": VLLMDeploymentStrategy()
        }

        logger.info("Initialized ModelRegistryService")

    # ========================================================================
    # Model Registration
    # ========================================================================

    async def register_model(
        self,
        job_id: UUID,
        name: str,
        version: str = "v1.0.0",
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        created_by: Optional[UUID] = None
    ) -> FineTunedModel:
        """
        Register a model from a completed training job

        Args:
            job_id: Training job ID
            name: Model name
            version: Semantic version
            description: Optional description
            tags: Optional tags for categorization
            created_by: User ID

        Returns:
            Registered model
        """
        # Validate job exists and completed successfully
        job = self.db.query(FineTuningJob).filter(
            FineTuningJob.id == job_id
        ).first()

        if not job:
            raise ValueError(f"Job not found: {job_id}")

        if job.status != "completed":
            raise ValueError(f"Job is not completed: {job.status}")

        # Validate semantic versioning
        try:
            semver.VersionInfo.parse(version.lstrip('v'))
        except ValueError:
            raise ValueError(f"Invalid semantic version: {version}")

        # Check if model with same name and version exists
        existing = self.db.query(FineTunedModel).filter(
            FineTunedModel.name == name,
            FineTunedModel.version == version
        ).first()

        if existing:
            raise ValueError(f"Model {name} version {version} already exists")

        # Create model entry
        model = FineTunedModel(
            name=name,
            version=version,
            description=description,
            job_id=job_id,
            base_model=job.base_model,
            finetuning_method=job.finetuning_method,
            mlflow_run_id=job.mlflow_run_id,
            minio_checkpoint_path=job.minio_checkpoint_path,
            status="registered",
            created_by=created_by,
            project_id=job.project_id,
            tags=tags or []
        )

        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)

        logger.info(f"Registered model: {model.id} - {name} {version}")
        return model

    async def auto_increment_version(
        self,
        base_name: str,
        bump: str = "patch"
    ) -> str:
        """
        Automatically increment version for a model

        Args:
            base_name: Base model name
            bump: Version component to bump (major, minor, patch)

        Returns:
            New version string
        """
        # Get latest version for this model name
        latest = self.db.query(FineTunedModel).filter(
            FineTunedModel.name == base_name
        ).order_by(FineTunedModel.created_at.desc()).first()

        if not latest:
            return "v1.0.0"

        # Parse current version
        current_version = semver.VersionInfo.parse(latest.version.lstrip('v'))

        # Bump version
        if bump == "major":
            new_version = current_version.bump_major()
        elif bump == "minor":
            new_version = current_version.bump_minor()
        else:  # patch
            new_version = current_version.bump_patch()

        return f"v{new_version}"

    # ========================================================================
    # Deployment Management
    # ========================================================================

    async def deploy_model(
        self,
        model_id: UUID,
        deployment_target: str = "ollama",
        deployment_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Deploy a model to a deployment target

        Args:
            model_id: Model ID to deploy
            deployment_target: Target (ollama, vllm)
            deployment_config: Optional deployment configuration

        Returns:
            Deployment result
        """
        model = self.db.query(FineTunedModel).filter(
            FineTunedModel.id == model_id
        ).first()

        if not model:
            raise ValueError(f"Model not found: {model_id}")

        if model.status == "deployed":
            logger.warning(f"Model {model_id} is already deployed")
            return {"status": "already_deployed"}

        # Get deployment strategy
        if deployment_target not in self.deployment_strategies:
            raise ValueError(f"Unsupported deployment target: {deployment_target}")

        strategy = self.deployment_strategies[deployment_target]

        # Execute deployment
        deployment_config = deployment_config or {}
        result = await strategy.deploy(model, deployment_config)

        # Update model status
        model.status = "deployed"
        model.deployment_url = result.get("deployment_url")

        if deployment_target == "ollama":
            model.ollama_model_name = result.get("ollama_model_name")
        elif deployment_target == "vllm":
            model.vllm_model_name = result.get("vllm_model_name")

        self.db.commit()
        self.db.refresh(model)

        logger.info(f"Deployed model {model_id} to {deployment_target}")
        return result

    async def undeploy_model(self, model_id: UUID) -> Dict[str, Any]:
        """
        Undeploy a model

        Args:
            model_id: Model ID to undeploy

        Returns:
            Undeploy result
        """
        model = self.db.query(FineTunedModel).filter(
            FineTunedModel.id == model_id
        ).first()

        if not model:
            raise ValueError(f"Model not found: {model_id}")

        if model.status != "deployed":
            return {"status": "not_deployed"}

        # Determine which target to undeploy from
        if model.ollama_model_name:
            strategy = self.deployment_strategies["ollama"]
        elif model.vllm_model_name:
            strategy = self.deployment_strategies["vllm"]
        else:
            raise ValueError("Cannot determine deployment target")

        # Execute undeployment
        result = await strategy.undeploy(model)

        # Update model status
        model.status = "archived"
        model.deployment_url = None

        self.db.commit()

        logger.info(f"Undeployed model {model_id}")
        return result

    # ========================================================================
    # Model Listing and Search
    # ========================================================================

    async def list_models(
        self,
        status: Optional[str] = None,
        project_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None
    ) -> List[FineTunedModel]:
        """
        List models with filtering

        Args:
            status: Filter by status
            project_id: Filter by project
            tags: Filter by tags
            search: Search in name/description

        Returns:
            List of models
        """
        query = self.db.query(FineTunedModel)

        if status:
            query = query.filter(FineTunedModel.status == status)

        if project_id:
            query = query.filter(FineTunedModel.project_id == project_id)

        if tags:
            # Filter models that have all specified tags
            for tag in tags:
                query = query.filter(FineTunedModel.tags.contains([tag]))

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (FineTunedModel.name.ilike(search_term)) |
                (FineTunedModel.description.ilike(search_term))
            )

        return query.order_by(FineTunedModel.created_at.desc()).all()

    async def get_model(self, model_id: UUID) -> Optional[FineTunedModel]:
        """Get model by ID"""
        return self.db.query(FineTunedModel).filter(
            FineTunedModel.id == model_id
        ).first()

    async def get_model_by_name(
        self,
        name: str,
        version: Optional[str] = None
    ) -> Optional[FineTunedModel]:
        """
        Get model by name and optionally version

        Args:
            name: Model name
            version: Optional version (defaults to latest)

        Returns:
            Model or None
        """
        query = self.db.query(FineTunedModel).filter(
            FineTunedModel.name == name
        )

        if version:
            query = query.filter(FineTunedModel.version == version)
        else:
            # Get latest version
            query = query.order_by(FineTunedModel.created_at.desc())

        return query.first()

    # ========================================================================
    # Model Deprecation and Archival
    # ========================================================================

    async def deprecate_model(
        self,
        model_id: UUID,
        reason: str,
        deprecated_by: UUID
    ) -> FineTunedModel:
        """
        Deprecate a model

        Args:
            model_id: Model ID to deprecate
            reason: Deprecation reason
            deprecated_by: User ID who deprecated

        Returns:
            Updated model
        """
        model = await self.get_model(model_id)

        if not model:
            raise ValueError(f"Model not found: {model_id}")

        model.status = "deprecated"
        model.deprecated_at = datetime.utcnow()
        model.deprecated_by = deprecated_by
        model.deprecation_reason = reason

        self.db.commit()
        self.db.refresh(model)

        logger.info(f"Deprecated model {model_id}: {reason}")
        return model

    # ========================================================================
    # Usage Tracking
    # ========================================================================

    async def update_usage_stats(
        self,
        model_name: str,
        latency_ms: float
    ):
        """
        Update model usage statistics

        Args:
            model_name: Model name (ollama_model_name or vllm_model_name)
            latency_ms: Request latency in milliseconds
        """
        # Find model by deployment name
        model = self.db.query(FineTunedModel).filter(
            (FineTunedModel.ollama_model_name == model_name) |
            (FineTunedModel.vllm_model_name == model_name)
        ).first()

        if not model:
            logger.warning(f"Model not found for usage tracking: {model_name}")
            return

        # Update stats
        model.total_inferences += 1
        model.last_inference_at = datetime.utcnow()

        # Update rolling average latency
        if model.avg_latency_ms:
            # Weighted average (give more weight to recent data)
            model.avg_latency_ms = (
                0.9 * model.avg_latency_ms + 0.1 * latency_ms
            )
        else:
            model.avg_latency_ms = latency_ms

        self.db.commit()

        logger.debug(f"Updated usage stats for model {model_name}")
