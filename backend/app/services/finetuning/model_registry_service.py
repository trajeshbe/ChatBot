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

from app.models.finetuning_models import (
    FineTunedModel,
    FineTuningJob
)

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
    """Deployment strategy for Ollama"""

    async def deploy(
        self,
        model: FineTunedModel,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deploy model to Ollama"""
        # TODO: Implement Ollama deployment
        # 1. Load model adapter from MinIO
        # 2. Merge with base model (or keep as adapter)
        # 3. Create Ollama modelfile
        # 4. Push to Ollama

        ollama_model_name = f"{model.name}-{model.version}".lower().replace(" ", "-")

        logger.info(f"Deploying model {model.id} to Ollama as {ollama_model_name}")

        return {
            "deployment_url": "http://localhost:11434/api/generate",
            "ollama_model_name": ollama_model_name,
            "status": "deployed"
        }

    async def undeploy(self, model: FineTunedModel) -> Dict[str, Any]:
        """Undeploy from Ollama"""
        # TODO: Implement Ollama undeployment
        logger.info(f"Undeploying model {model.id} from Ollama")

        return {"status": "undeployed"}


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
