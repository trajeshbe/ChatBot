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
    OLLAMA = "ollama"
    LLAMA_CPP = "llama.cpp"  # Deprecated


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
        # LOCAL GPU MODELS (vLLM with quantization support)
        # Max 7B models, optimized for speed and efficiency
        # ============================================================================

        self.register(ModelInfo(
            id="llama-3.1-8b-gpu",
            name="Llama 3.1 8B (GPU)",
            provider=ModelProvider.VLLM,
            model_type=ModelType.LOCAL_GPU,
            model_path="meta-llama/Meta-Llama-3.1-8B-Instruct",
            context_length=128000,
            cost_per_1k_tokens=0.0,
            requires_gpu=True,
            min_gpu_memory_gb=12,  # With quantization
            description="Best quality in 7B range. Fast inference with AWQ/GPTQ quantization.",
            recommended=True
        ))

        self.register(ModelInfo(
            id="llama-3.2-3b-gpu",
            name="Llama 3.2 3B (GPU)",
            provider=ModelProvider.VLLM,
            model_type=ModelType.LOCAL_GPU,
            model_path="meta-llama/Llama-3.2-3B-Instruct",
            context_length=128000,
            cost_per_1k_tokens=0.0,
            requires_gpu=True,
            min_gpu_memory_gb=6,  # Lightweight
            description="Lightweight and fast. Excellent speed/quality balance.",
            recommended=True
        ))

        self.register(ModelInfo(
            id="qwen-2.5-7b-gpu",
            name="Qwen 2.5 7B (GPU)",
            provider=ModelProvider.VLLM,
            model_type=ModelType.LOCAL_GPU,
            model_path="Qwen/Qwen2.5-7B-Instruct",
            context_length=32768,
            cost_per_1k_tokens=0.0,
            requires_gpu=True,
            min_gpu_memory_gb=12,
            description="Multilingual powerhouse. Excellent for non-English queries.",
            recommended=False
        ))

        # ============================================================================
        # LOCAL CPU MODELS (Ollama - better WSL2 compatibility)
        # Optimized for CPU inference with 4-bit quantization
        # ============================================================================

        # QWEN MODELS (Ollama - Recommended for GPU)
        # Superior multilingual and coding capabilities
        self.register(ModelInfo(
            id="qwen2.5:1.5b-instruct-q4_K_M",
            name="Qwen 2.5 1.5B (Ollama GPU)",
            provider=ModelProvider.OLLAMA,
            model_type=ModelType.LOCAL_CPU,  # Ollama handles GPU internally
            model_path="qwen2.5:1.5b-instruct-q4_K_M",
            context_length=32768,
            cost_per_1k_tokens=0.0,
            requires_gpu=False,  # Ollama handles GPU internally
            min_gpu_memory_gb=0,
            description="🥇 #1 FAST GPU model. Balanced speed/quality. 25-35 tok/s on RTX 5060. Best for 8GB VRAM.",
            recommended=True
        ))

        self.register(ModelInfo(
            id="qwen2.5:0.5b",
            name="Qwen 2.5 0.5B (Ollama GPU - Ultra Fast)",
            provider=ModelProvider.OLLAMA,
            model_type=ModelType.LOCAL_CPU,
            model_path="qwen2.5:0.5b",
            context_length=32768,
            cost_per_1k_tokens=0.0,
            requires_gpu=False,
            min_gpu_memory_gb=0,
            description="⚡ Ultra-fast. 40-60 tok/s. Great for simple queries and testing.",
            recommended=False
        ))

        self.register(ModelInfo(
            id="qwen2.5:3b-instruct-q4_K_M",
            name="Qwen 2.5 3B (Ollama GPU - High Quality)",
            provider=ModelProvider.OLLAMA,
            model_type=ModelType.LOCAL_CPU,
            model_path="qwen2.5:3b-instruct-q4_K_M",
            context_length=32768,
            cost_per_1k_tokens=0.0,
            requires_gpu=False,
            min_gpu_memory_gb=0,
            description="💎 High quality. 15-25 tok/s. Better reasoning for complex queries.",
            recommended=False
        ))

        self.register(ModelInfo(
            id="qwen2.5:7b-instruct-q4_K_M",
            name="Qwen 2.5 7B (Ollama GPU - Max Quality)",
            provider=ModelProvider.OLLAMA,
            model_type=ModelType.LOCAL_CPU,
            model_path="qwen2.5:7b-instruct-q4_K_M",
            context_length=32768,
            cost_per_1k_tokens=0.0,
            requires_gpu=False,
            min_gpu_memory_gb=0,
            description="🏆 Maximum quality. 10-15 tok/s. Best for production (requires ~5.5GB VRAM).",
            recommended=False
        ))

        # LLAMA MODELS (Removed from Ollama but kept for reference)
        self.register(ModelInfo(
            id="llama3.1:8b",
            name="Llama 3.1 8B (Ollama GPU) - REMOVED",
            provider=ModelProvider.OLLAMA,
            model_type=ModelType.LOCAL_CPU,
            model_path="llama3.1:8b",
            context_length=128000,
            cost_per_1k_tokens=0.0,
            requires_gpu=False,
            min_gpu_memory_gb=0,
            description="⚠️ Model removed - use Qwen 2.5 instead",
            available=False,
            recommended=False
        ))

        self.register(ModelInfo(
            id="llama3.2:3b",
            name="Llama 3.2 3B (Ollama) - REMOVED",
            provider=ModelProvider.OLLAMA,
            model_type=ModelType.LOCAL_CPU,
            model_path="llama3.2:3b",
            context_length=128000,
            cost_per_1k_tokens=0.0,
            requires_gpu=False,
            min_gpu_memory_gb=0,
            description="⚠️ Model removed - use Qwen 2.5 instead",
            available=False,
            recommended=False
        ))

        # 🔍 Vision Model - Multimodal (Text + Images)
        self.register(ModelInfo(
            id="llama3.2-vision:11b",
            name="LLaMA 3.2 Vision 11B (Ollama GPU) 🔍",
            provider=ModelProvider.OLLAMA,
            model_type=ModelType.LOCAL_CPU,  # Ollama handles GPU internally
            model_path="llama3.2-vision:11b",
            context_length=131072,
            cost_per_1k_tokens=0.0,
            requires_gpu=False,  # Ollama manages GPU
            min_gpu_memory_gb=0,
            description="🔍 Vision + Text multimodal model. Analyzes images, construction drawings, floor plans, architectural diagrams. Extracts text from images. Can also handle text-only conversations. ~7.8GB. Supports construction document analysis.",
            available=True,
            recommended=True
        ))

        self.register(ModelInfo(
            id="qwen2.5:1.5b",
            name="Qwen 2.5 1.5B (Ollama)",
            provider=ModelProvider.OLLAMA,
            model_type=ModelType.LOCAL_CPU,
            model_path="qwen2.5:1.5b",
            context_length=32768,
            cost_per_1k_tokens=0.0,
            requires_gpu=False,
            min_gpu_memory_gb=0,
            description="Base model (non-instruct). Use qwen2.5:1.5b-instruct-q4_K_M instead.",
            recommended=False
        ))

        self.register(ModelInfo(
            id="mistral:latest",
            name="Mistral 7B (Ollama)",
            provider=ModelProvider.OLLAMA,
            model_type=ModelType.LOCAL_CPU,
            model_path="mistral:latest",
            context_length=32768,
            cost_per_1k_tokens=0.0,
            requires_gpu=False,
            min_gpu_memory_gb=0,
            description="Powerful 7B model. Good reasoning. ~4.4GB RAM.",
            recommended=False
        ))

        self.register(ModelInfo(
            id="phi3:mini",
            name="Phi-3 Mini (Ollama)",
            provider=ModelProvider.OLLAMA,
            model_type=ModelType.LOCAL_CPU,
            model_path="phi3:mini",
            context_length=128000,
            cost_per_1k_tokens=0.0,
            requires_gpu=False,
            min_gpu_memory_gb=0,
            description="Microsoft's compact model. ~2.2GB RAM.",
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

    def get_recommended_model(self) -> Optional[ModelInfo]:
        """Get the first recommended and available model (for single model selection)

        Returns:
            First recommended and available model, or None if no recommended models available
        """
        recommended = [m for m in self._models.values() if m.recommended and m.available]
        if recommended:
            # Sort by provider preference: Ollama > vLLM > proprietary
            recommended.sort(key=lambda m: (
                0 if m.provider == ModelProvider.OLLAMA else
                1 if m.provider == ModelProvider.VLLM else 2
            ))
            return recommended[0]

        # Fallback to any available Ollama model
        ollama_models = [m for m in self._models.values()
                        if m.provider == ModelProvider.OLLAMA and m.available]
        if ollama_models:
            return ollama_models[0]

        return None

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
