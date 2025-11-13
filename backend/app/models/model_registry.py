"""
Model Registry

Centralized registry of all available LLM models with metadata.
Supports proprietary APIs (OpenAI, Claude) and local models (vLLM, llama.cpp).
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Literal
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """Model deployment type"""
    PROPRIETARY = "proprietary"  # API-based (OpenAI, Claude)
    LOCAL_GPU = "local-gpu"       # GPU-accelerated (vLLM)
    LOCAL_CPU = "local-cpu"       # CPU-based (llama.cpp)


class ModelProvider(str, Enum):
    """Model provider/backend"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    VLLM = "vllm"
    LLAMA_CPP = "llama.cpp"


@dataclass
class ModelInfo:
    """Model metadata"""
    id: str                          # Unique identifier
    name: str                        # Display name
    provider: ModelProvider          # Backend provider
    model_type: ModelType            # Deployment type
    model_path: str                  # API model name or local path
    context_length: int              # Maximum context tokens
    cost_per_1k_tokens: float        # Cost in USD (0 for local)
    requires_gpu: bool               # Requires GPU
    min_gpu_memory_gb: float         # Minimum GPU memory required
    description: str                 # Human-readable description
    available: bool = True           # Is model currently available
    recommended: bool = False        # Recommended for general use

    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider.value,
            "type": self.model_type.value,
            "context_length": self.context_length,
            "cost_per_1k_tokens": self.cost_per_1k_tokens,
            "requires_gpu": self.requires_gpu,
            "min_gpu_memory_gb": self.min_gpu_memory_gb,
            "description": self.description,
            "available": self.available,
            "recommended": self.recommended,
        }


class ModelRegistry:
    """Registry of all available models"""

    def __init__(self):
        self._models: Dict[str, ModelInfo] = {}
        self._initialize_models()

    def _initialize_models(self):
        """Initialize model registry with all supported models"""

        # ============================================================================
        # PROPRIETARY MODELS (API-based)
        # ============================================================================

        # OpenAI Models
        self.register(ModelInfo(
            id="gpt-4-turbo",
            name="GPT-4 Turbo",
            provider=ModelProvider.OPENAI,
            model_type=ModelType.PROPRIETARY,
            model_path="gpt-4-turbo-preview",
            context_length=128000,
            cost_per_1k_tokens=0.03,  # $0.01 input + $0.03 output average
            requires_gpu=False,
            min_gpu_memory_gb=0,
            description="OpenAI's most capable model. Best for complex reasoning, coding, and analysis.",
            recommended=True
        ))

        self.register(ModelInfo(
            id="gpt-4",
            name="GPT-4",
            provider=ModelProvider.OPENAI,
            model_type=ModelType.PROPRIETARY,
            model_path="gpt-4",
            context_length=8192,
            cost_per_1k_tokens=0.06,
            requires_gpu=False,
            min_gpu_memory_gb=0,
            description="OpenAI GPT-4. High quality for most tasks."
        ))

        self.register(ModelInfo(
            id="gpt-3.5-turbo",
            name="GPT-3.5 Turbo",
            provider=ModelProvider.OPENAI,
            model_type=ModelType.PROPRIETARY,
            model_path="gpt-3.5-turbo",
            context_length=16385,
            cost_per_1k_tokens=0.002,
            requires_gpu=False,
            min_gpu_memory_gb=0,
            description="Fast and cost-effective. Good for simple tasks and high-volume use."
        ))

        # Anthropic Claude Models
        self.register(ModelInfo(
            id="claude-3.5-sonnet",
            name="Claude 3.5 Sonnet",
            provider=ModelProvider.ANTHROPIC,
            model_type=ModelType.PROPRIETARY,
            model_path="claude-3-5-sonnet-20241022",
            context_length=200000,
            cost_per_1k_tokens=0.015,  # $0.003 input + $0.015 output average
            requires_gpu=False,
            min_gpu_memory_gb=0,
            description="Anthropic's latest model. Excellent for coding, analysis, and long documents.",
            recommended=True
        ))

        self.register(ModelInfo(
            id="claude-3-opus",
            name="Claude 3 Opus",
            provider=ModelProvider.ANTHROPIC,
            model_type=ModelType.PROPRIETARY,
            model_path="claude-3-opus-20240229",
            context_length=200000,
            cost_per_1k_tokens=0.075,
            requires_gpu=False,
            min_gpu_memory_gb=0,
            description="Anthropic's most powerful model. Best for complex tasks requiring deep reasoning."
        ))

        self.register(ModelInfo(
            id="claude-3-haiku",
            name="Claude 3 Haiku",
            provider=ModelProvider.ANTHROPIC,
            model_type=ModelType.PROPRIETARY,
            model_path="claude-3-haiku-20240307",
            context_length=200000,
            cost_per_1k_tokens=0.00125,
            requires_gpu=False,
            min_gpu_memory_gb=0,
            description="Fast and affordable. Good for simple queries and high-volume use."
        ))

        # ============================================================================
        # LOCAL GPU MODELS (vLLM)
        # ============================================================================

        self.register(ModelInfo(
            id="llama-3.1-70b",
            name="Llama 3.1 70B (Local)",
            provider=ModelProvider.VLLM,
            model_type=ModelType.LOCAL_GPU,
            model_path="meta-llama/Meta-Llama-3.1-70B-Instruct",
            context_length=128000,
            cost_per_1k_tokens=0.0,
            requires_gpu=True,
            min_gpu_memory_gb=80,
            description="Meta's flagship open model. Excellent quality, requires high-end GPU.",
            recommended=False
        ))

        self.register(ModelInfo(
            id="llama-3.1-8b",
            name="Llama 3.1 8B (Local)",
            provider=ModelProvider.VLLM,
            model_type=ModelType.LOCAL_GPU,
            model_path="meta-llama/Meta-Llama-3.1-8B-Instruct",
            context_length=128000,
            cost_per_1k_tokens=0.0,
            requires_gpu=True,
            min_gpu_memory_gb=16,
            description="Balanced local model. Good quality with moderate GPU requirements.",
            recommended=True
        ))

        self.register(ModelInfo(
            id="llama-3.2-3b",
            name="Llama 3.2 3B (Local)",
            provider=ModelProvider.VLLM,
            model_type=ModelType.LOCAL_GPU,
            model_path="meta-llama/Llama-3.2-3B-Instruct",
            context_length=128000,
            cost_per_1k_tokens=0.0,
            requires_gpu=True,
            min_gpu_memory_gb=8,
            description="Lightweight local model. Works on modest GPUs.",
            recommended=True
        ))

        self.register(ModelInfo(
            id="qwen-2.5-7b",
            name="Qwen 2.5 7B (Local)",
            provider=ModelProvider.VLLM,
            model_type=ModelType.LOCAL_GPU,
            model_path="Qwen/Qwen2.5-7B-Instruct",
            context_length=32768,
            cost_per_1k_tokens=0.0,
            requires_gpu=True,
            min_gpu_memory_gb=16,
            description="Alibaba's Qwen model. Strong multilingual capabilities.",
            recommended=False
        ))

        # ============================================================================
        # LOCAL CPU MODELS (llama.cpp)
        # ============================================================================

        self.register(ModelInfo(
            id="llama-3.2-3b-cpu",
            name="Llama 3.2 3B (CPU)",
            provider=ModelProvider.LLAMA_CPP,
            model_type=ModelType.LOCAL_CPU,
            model_path="/models/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
            context_length=128000,
            cost_per_1k_tokens=0.0,
            requires_gpu=False,
            min_gpu_memory_gb=0,
            description="CPU-optimized Llama 3.2. Decent quality, slower inference.",
            recommended=True
        ))

        self.register(ModelInfo(
            id="qwen-1.5b-cpu",
            name="Qwen 1.5B (CPU)",
            provider=ModelProvider.LLAMA_CPP,
            model_type=ModelType.LOCAL_CPU,
            model_path="/models/qwen2.5-1.5b-instruct-q4_k_m.gguf",
            context_length=32768,
            cost_per_1k_tokens=0.0,
            requires_gpu=False,
            min_gpu_memory_gb=0,
            description="Lightweight Qwen model for CPU. Fast on lower-end hardware.",
            recommended=True
        ))

        self.register(ModelInfo(
            id="tinyllama-cpu",
            name="TinyLlama 1.1B (CPU)",
            provider=ModelProvider.LLAMA_CPP,
            model_type=ModelType.LOCAL_CPU,
            model_path="/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
            context_length=2048,
            cost_per_1k_tokens=0.0,
            requires_gpu=False,
            min_gpu_memory_gb=0,
            description="Tiny model for testing. Very fast but basic quality.",
            recommended=False
        ))

    def register(self, model: ModelInfo):
        """Register a model"""
        self._models[model.id] = model
        logger.debug(f"Registered model: {model.name} ({model.id})")

    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """Get model by ID"""
        return self._models.get(model_id)

    def get_all_models(self) -> List[ModelInfo]:
        """Get all registered models"""
        return list(self._models.values())

    def get_available_models(self, gpu_available: bool = False, gpu_memory_gb: float = 0) -> List[ModelInfo]:
        """
        Get models available for current hardware

        Args:
            gpu_available: Whether GPU is available
            gpu_memory_gb: Available GPU memory in GB

        Returns:
            List of available models
        """
        available = []

        for model in self._models.values():
            # Proprietary models always available (if API key exists)
            if model.model_type == ModelType.PROPRIETARY:
                available.append(model)
                continue

            # GPU models
            if model.model_type == ModelType.LOCAL_GPU:
                if gpu_available and gpu_memory_gb >= model.min_gpu_memory_gb:
                    available.append(model)
                continue

            # CPU models always available
            if model.model_type == ModelType.LOCAL_CPU:
                available.append(model)

        return available

    def get_models_by_type(self, model_type: ModelType) -> List[ModelInfo]:
        """Get all models of a specific type"""
        return [m for m in self._models.values() if m.model_type == model_type]

    def get_models_by_provider(self, provider: ModelProvider) -> List[ModelInfo]:
        """Get all models from a specific provider"""
        return [m for m in self._models.values() if m.provider == provider]

    def get_recommended_models(self) -> List[ModelInfo]:
        """Get recommended models"""
        return [m for m in self._models.values() if m.recommended]

    def update_availability(self, model_id: str, available: bool):
        """Update model availability status"""
        if model_id in self._models:
            self._models[model_id].available = available
            logger.info(f"Model {model_id} availability: {available}")

    def get_models_grouped(self) -> Dict[str, List[Dict]]:
        """Get models grouped by type for UI display"""
        return {
            "proprietary": [m.to_dict() for m in self.get_models_by_type(ModelType.PROPRIETARY) if m.available],
            "local_gpu": [m.to_dict() for m in self.get_models_by_type(ModelType.LOCAL_GPU) if m.available],
            "local_cpu": [m.to_dict() for m in self.get_models_by_type(ModelType.LOCAL_CPU) if m.available],
        }


# Global singleton
_model_registry: Optional[ModelRegistry] = None


def get_model_registry() -> ModelRegistry:
    """Get global model registry instance"""
    global _model_registry
    if _model_registry is None:
        _model_registry = ModelRegistry()
    return _model_registry
