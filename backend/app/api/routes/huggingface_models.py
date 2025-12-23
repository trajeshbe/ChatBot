"""
HuggingFace Models Registry API

Provides endpoints for listing and filtering available HuggingFace models for fine-tuning.
Reads from huggingface_models.yaml configuration file.
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import yaml
from pathlib import Path
import logging

from app.middleware.rbac_middleware import RequirePermission, require_authentication
from app.models.database_enhanced import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/finetuning", tags=["finetuning", "huggingface-models"])


# ============================================================================
# Response Models
# ============================================================================

class HuggingFaceModel(BaseModel):
    id: str
    display_name: str
    architecture: str
    size_params: int
    size_gb: float
    quantization_support: List[str]
    recommended_vram_gb: int
    license: str
    use_cases: List[str]
    tags: List[str]
    description: str
    huggingface_url: str


class HuggingFaceModelsResponse(BaseModel):
    models: List[HuggingFaceModel]
    total: int
    recommendations: Dict[str, List[str]]
    training_methods: Optional[Dict[str, Any]] = None


class ModelRecommendationsResponse(BaseModel):
    vram_gb: int
    recommended_models: List[str]
    model_details: List[HuggingFaceModel]


# ============================================================================
# Helper Functions
# ============================================================================

def load_models_registry() -> Dict[str, Any]:
    """Load HuggingFace models registry from YAML file"""
    try:
        # Path to config file
        config_path = Path(__file__).parent.parent.parent / "config" / "huggingface_models.yaml"

        if not config_path.exists():
            logger.error(f"HuggingFace models registry not found at {config_path}")
            raise FileNotFoundError("HuggingFace models registry not found")

        with open(config_path, 'r') as f:
            registry = yaml.safe_load(f)

        logger.info(f"Loaded {len(registry.get('models', []))} models from registry")
        return registry

    except Exception as e:
        logger.error(f"Error loading HuggingFace models registry: {e}")
        raise


def filter_models(
    models: List[Dict[str, Any]],
    architecture: Optional[str] = None,
    max_vram_gb: Optional[int] = None,
    use_case: Optional[str] = None,
    tag: Optional[str] = None,
    quantization: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Filter models based on criteria"""
    filtered = models

    if architecture:
        filtered = [m for m in filtered if m.get("architecture") == architecture]

    if max_vram_gb:
        filtered = [m for m in filtered if m.get("recommended_vram_gb", 999) <= max_vram_gb]

    if use_case:
        filtered = [m for m in filtered if use_case in m.get("use_cases", [])]

    if tag:
        filtered = [m for m in filtered if tag in m.get("tags", [])]

    if quantization:
        filtered = [m for m in filtered if quantization in m.get("quantization_support", [])]

    return filtered


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/models/huggingface", response_model=HuggingFaceModelsResponse)
async def list_huggingface_models(
    architecture: Optional[str] = Query(None, description="Filter by architecture (qwen2.5, mistral, llama2)"),
    max_vram_gb: Optional[int] = Query(None, description="Filter by max VRAM (e.g., 8, 12, 16)"),
    use_case: Optional[str] = Query(None, description="Filter by use case (instruction, qa, chat, reasoning)"),
    tag: Optional[str] = Query(None, description="Filter by tag (small, medium, fast, unsloth, optimized)"),
    quantization: Optional[str] = Query(None, description="Filter by quantization support (4bit, 8bit)"),
    include_training_methods: bool = Query(False, description="Include training method compatibility info"),
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "read"))
):
    """
    List available HuggingFace models for fine-tuning

    Returns models from huggingface_models.yaml with filtering options.
    Users can filter by:
    - architecture: Model architecture (qwen2.5, mistral, llama2)
    - max_vram_gb: Maximum VRAM available (filters models that fit)
    - use_case: Training use case (instruction, qa, chat, reasoning)
    - tag: Model tags (small, medium, fast, unsloth, optimized)
    - quantization: Quantization support (4bit, 8bit)

    Examples:
    - `/models/huggingface?max_vram_gb=8` - Models that fit in 8GB VRAM
    - `/models/huggingface?tag=unsloth` - Unsloth-optimized models
    - `/models/huggingface?architecture=qwen2.5&max_vram_gb=12` - Qwen models for 12GB GPUs
    """
    try:
        # Load registry
        registry = load_models_registry()

        # Get models
        models = registry.get("models", [])

        # Apply filters
        filtered_models = filter_models(
            models,
            architecture=architecture,
            max_vram_gb=max_vram_gb,
            use_case=use_case,
            tag=tag,
            quantization=quantization
        )

        # Convert to Pydantic models
        model_objects = [HuggingFaceModel(**model) for model in filtered_models]

        # Get recommendations
        recommendations = registry.get("recommendations", {})

        # Optionally include training methods
        training_methods = None
        if include_training_methods:
            training_methods = registry.get("training_methods", {})

        logger.info(f"Returning {len(model_objects)} HuggingFace models (filtered from {len(models)} total)")

        return HuggingFaceModelsResponse(
            models=model_objects,
            total=len(model_objects),
            recommendations=recommendations,
            training_methods=training_methods
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing HuggingFace models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing models: {str(e)}")


@router.get("/models/huggingface/recommendations", response_model=ModelRecommendationsResponse)
async def get_model_recommendations(
    vram_gb: int = Query(..., description="Available VRAM in GB"),
    use_fastest: bool = Query(False, description="Prioritize fastest training (Unsloth models)"),
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "read"))
):
    """
    Get model recommendations based on available VRAM

    Recommends models that will fit within the specified VRAM budget.
    Optionally prioritize Unsloth-optimized models for fastest training.

    Examples:
    - `/models/huggingface/recommendations?vram_gb=8` - Models for 8GB VRAM
    - `/models/huggingface/recommendations?vram_gb=16&use_fastest=true` - Fastest models for 16GB VRAM
    """
    try:
        # Load registry
        registry = load_models_registry()

        # Get models
        models = registry.get("models", [])

        # Filter by VRAM
        compatible_models = filter_models(models, max_vram_gb=vram_gb)

        # If use_fastest, prioritize Unsloth models
        if use_fastest:
            compatible_models = sorted(
                compatible_models,
                key=lambda m: ("unsloth" in m.get("tags", [])),
                reverse=True
            )
        else:
            # Sort by size (smaller first for efficiency)
            compatible_models = sorted(
                compatible_models,
                key=lambda m: m.get("size_params", 0)
            )

        # Get IDs
        recommended_model_ids = [m["id"] for m in compatible_models[:5]]  # Top 5

        # Get model details
        model_details = [HuggingFaceModel(**m) for m in compatible_models[:5]]

        logger.info(f"Recommended {len(recommended_model_ids)} models for {vram_gb}GB VRAM")

        return ModelRecommendationsResponse(
            vram_gb=vram_gb,
            recommended_models=recommended_model_ids,
            model_details=model_details
        )

    except Exception as e:
        logger.error(f"Error getting model recommendations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")


@router.get("/models/huggingface/{model_id:path}")
async def get_model_details(
    model_id: str,
    user: User = Depends(require_authentication),
    _: None = Depends(RequirePermission("model_finetuning", "read"))
):
    """
    Get detailed information about a specific HuggingFace model

    Example:
    - `/models/huggingface/Qwen/Qwen2.5-1.5B-Instruct` - Details for Qwen 2.5 1.5B
    """
    try:
        # Load registry
        registry = load_models_registry()

        # Find model
        models = registry.get("models", [])
        model = next((m for m in models if m["id"] == model_id), None)

        if not model:
            raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")

        logger.info(f"Retrieved details for model: {model_id}")

        return HuggingFaceModel(**model)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting model details: {str(e)}")
