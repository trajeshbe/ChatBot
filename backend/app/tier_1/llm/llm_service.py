"""
Enhanced LLM Service with Multi-Model Support

Supports intelligent model selection across:
- Proprietary APIs: OpenAI, Claude/Anthropic
- Local GPU: vLLM with auto-detection
- Local CPU: llama.cpp fallback

Features:
- Automatic GPU detection
- Dynamic model switching
- Cost tracking
- Unified API across all providers
"""

import httpx
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from typing import Dict, List, Optional, Any
import logging
from app.tier_1.infrastructure.config import settings
from app.tier_1.infrastructure.database import get_db
from app.models.model_registry import get_model_registry, ModelInfo, ModelProvider
from app.utils.gpu_detector import get_gpu_detector
from app.utils.resource_checker import resource_checker
from app.tier_1.platform_services.secrets_service import get_secrets_service
from tenacity import retry, stop_after_attempt, wait_exponential
import time

logger = logging.getLogger(__name__)


class LLMService:
    """Enhanced LLM service with multi-model support"""

    def __init__(self):
        # API clients
        self.openai_client: Optional[AsyncOpenAI] = None
        self.anthropic_client: Optional[AsyncAnthropic] = None

        # HTTP clients for local models (lazy initialization to avoid stale connections)
        self.vllm_client = None
        self.ollama_client = None
        self.llama_cpp_client = None

        # Model registry and GPU detector
        self.model_registry = get_model_registry()
        self.gpu_detector = get_gpu_detector()

        # State
        self._initialized = False
        self._default_model_id: Optional[str] = None
        self._gpu_info = None

        # Cache for Ollama model list (refreshed periodically)
        self._ollama_models_cache = None
        self._ollama_models_cache_time = 0

    async def _get_available_ollama_models(self) -> List[Dict]:
        """
        Get list of available Ollama models dynamically from API

        Returns:
            List of model dicts with name and size
        """
        import time

        # Cache for 5 minutes
        cache_duration = 300  # seconds
        current_time = time.time()

        if self._ollama_models_cache and (current_time - self._ollama_models_cache_time) < cache_duration:
            logger.debug(f"📦 Using cached Ollama models ({len(self._ollama_models_cache)} models)")
            return self._ollama_models_cache

        try:
            # Query Ollama API for available models
            if not self.ollama_client:
                self.ollama_client = httpx.AsyncClient(
                    base_url=settings.OLLAMA_BASE_URL,
                    timeout=30.0
                )

            response = await self.ollama_client.get("/api/tags")
            response.raise_for_status()
            data = response.json()

            models = []
            for model in data.get("models", []):
                name = model.get("name", "")
                size_bytes = model.get("size", 0)
                size_mb = size_bytes / (1024 * 1024)

                models.append({
                    "name": name,
                    "size_mb": size_mb,
                    "size_gb": size_mb / 1024,
                    "modified": model.get("modified_at", "")
                })

            # Sort by size (ascending) for fallback selection
            models.sort(key=lambda m: m["size_mb"])

            self._ollama_models_cache = models
            self._ollama_models_cache_time = current_time

            logger.info(f"📦 Loaded {len(models)} Ollama models from API")
            return models

        except Exception as e:
            logger.error(f"❌ Failed to get Ollama models: {e}")
            return []

    async def _select_model_with_memory_check(self, model_id: str) -> Dict[str, any]:
        """
        Check if model fits in available memory, fallback to best available lighter model if needed

        Args:
            model_id: Requested model ID

        Returns:
            Dict with:
                - model_id: Model to use (original or fallback)
                - fallback: True if fallback was used
                - reason: Reason for fallback
                - original_model: Original requested model
                - available_memory_mb: Available memory
                - required_memory_mb: Required memory for original model
        """
        # Get available memory
        resources = resource_checker.get_resource_summary()
        available_mb = resources["memory"]["available_mb"]

        # Get all available Ollama models
        available_models = await self._get_available_ollama_models()

        if not available_models:
            logger.warning("⚠️  Could not get Ollama models, using requested model")
            return {
                "model_id": model_id,
                "fallback": False,
                "reason": "Could not query Ollama API",
                "original_model": model_id,
                "available_memory_mb": available_mb,
                "required_memory_mb": None
            }

        # Find requested model in available models
        requested_model = next((m for m in available_models if m["name"] == model_id), None)

        if not requested_model:
            logger.warning(f"⚠️  Requested model {model_id} not found in Ollama, using as-is")
            return {
                "model_id": model_id,
                "fallback": False,
                "reason": "Model not found in Ollama list",
                "original_model": model_id,
                "available_memory_mb": available_mb,
                "required_memory_mb": None
            }

        required_mb = requested_model["size_mb"]
        # Add 20% safety buffer for runtime overhead
        required_with_buffer = required_mb * 1.2

        logger.info(
            f"💾 Memory check: {model_id} "
            f"requires {required_mb:.0f}MB (+20% buffer = {required_with_buffer:.0f}MB), "
            f"available: {available_mb:.0f}MB"
        )

        # Check if requested model fits
        if required_with_buffer <= available_mb:
            logger.info(f"✅ Memory check passed for {model_id}")
            return {
                "model_id": model_id,
                "fallback": False,
                "reason": None,
                "original_model": model_id,
                "available_memory_mb": available_mb,
                "required_memory_mb": required_mb
            }

        # Requested model doesn't fit - find best alternative
        logger.warning(
            f"⚠️  Model {model_id} requires {required_mb:.0f}MB "
            f"(+buffer: {required_with_buffer:.0f}MB) "
            f"but only {available_mb:.0f}MB available"
        )

        # Filter models that fit in memory (with 20% buffer)
        # 🆕 CRITICAL FIX: Exclude coder-specific models from fallback (coder, code-, -code)
        excluded_keywords = ['coder', 'code-', '-code']
        fitting_models = [
            m for m in available_models
            if (m["size_mb"] * 1.2) <= available_mb and
            not any(keyword in m["name"].lower() for keyword in excluded_keywords)
        ]

        if not fitting_models:
            logger.error("❌ No chat-appropriate Ollama models fit in available memory!")
            logger.error(f"   (Coder models excluded: {excluded_keywords})")
            return {
                "model_id": model_id,
                "fallback": False,
                "reason": "No chat-appropriate models fit in available memory",
                "original_model": model_id,
                "available_memory_mb": available_mb,
                "required_memory_mb": required_mb
            }

        # Select LARGEST chat model that fits (best quality within constraints)
        best_fit = max(fitting_models, key=lambda m: m["size_mb"])
        logger.info(f"🔍 Filtered out coder models, selected best chat model: {best_fit['name']}")

        logger.info(
            f"✅ Falling back to best available model: {best_fit['name']} "
            f"(size: {best_fit['size_mb']:.0f}MB, with buffer: {best_fit['size_mb']*1.2:.0f}MB)"
        )

        return {
            "model_id": best_fit["name"],
            "fallback": True,
            "reason": f"insufficient_memory (requested: {required_mb:.0f}MB, available: {available_mb:.0f}MB)",
            "original_model": model_id,
            "available_memory_mb": available_mb,
            "required_memory_mb": required_mb,
            "fallback_model_size_mb": best_fit["size_mb"]
        }

    async def _get_api_key_with_fallback(self, provider: str, env_key: Optional[str] = None) -> Optional[str]:
        """
        Get API key from database first, fallback to environment variable

        Args:
            provider: Provider name (openai, anthropic)
            env_key: Environment variable value as fallback

        Returns:
            API key string or None
        """
        try:
            # Try to get key from database first
            secrets_service = get_secrets_service()

            # Create temporary database session
            async for db in get_db():
                try:
                    db_key = await secrets_service.get_api_key(db, provider)
                    if db_key:
                        logger.info(f"✓ Using {provider} API key from database")
                        return db_key
                finally:
                    await db.close()
                break  # Only need one iteration
        except Exception as e:
            logger.warning(f"Could not load {provider} key from database: {e}")

        # Fallback to environment variable
        if env_key and env_key.strip():
            logger.info(f"✓ Using {provider} API key from environment")
            return env_key

        return None

    async def initialize(self):
        """Initialize LLM clients and detect hardware"""
        if self._initialized:
            return

        logger.info("Initializing Enhanced LLM Service...")

        # Detect GPU
        self._gpu_info = self.gpu_detector.detect()
        logger.info(f"GPU Detection: {self._gpu_info.type} ({'available' if self._gpu_info.available else 'not available'})")

        # Initialize OpenAI (check database first, then environment)
        openai_key = await self._get_api_key_with_fallback('openai', settings.OPENAI_API_KEY)
        if openai_key:
            self.openai_client = AsyncOpenAI(api_key=openai_key)
            logger.info("✓ OpenAI client initialized")
        else:
            logger.info("OpenAI API key not configured")

        # Initialize Anthropic/Claude (check database first, then environment)
        anthropic_env_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        anthropic_key = await self._get_api_key_with_fallback('anthropic', anthropic_env_key)
        if anthropic_key:
            self.anthropic_client = AsyncAnthropic(api_key=anthropic_key)
            logger.info("✓ Anthropic/Claude client initialized")
        else:
            logger.info("Anthropic API key not configured")

        # Initialize HuggingFace token (check database first, then environment)
        # This is used by vLLM and huggingface_hub for downloading models
        import os
        hf_env_key = getattr(settings, 'HUGGING_FACE_HUB_TOKEN', None)
        hf_token = await self._get_api_key_with_fallback('huggingface', hf_env_key)
        if hf_token:
            # Set as environment variable for huggingface_hub library
            os.environ['HUGGING_FACE_HUB_TOKEN'] = hf_token
            os.environ['HF_TOKEN'] = hf_token  # Alternative env var name
            logger.info("✓ HuggingFace token configured for model downloads")
        else:
            logger.info("HuggingFace token not configured (optional - needed for private/gated models)")

        # Update model availability based on hardware and API keys
        self._update_model_availability()

        # Check which Ollama models are actually installed (async check)
        installed_ollama_models = await self._check_ollama_model_availability()
        if installed_ollama_models:
            # Update Ollama model availability based on what's actually installed
            for model in self.model_registry.get_models_by_provider(ModelProvider.OLLAMA):
                # Check if the model's path is in the installed models
                is_available = model.model_path in installed_ollama_models
                self.model_registry.update_availability(model.id, is_available)
                if is_available:
                    logger.info(f"   ✅ {model.name} ({model.model_path}) - Available")
                else:
                    logger.warning(f"   ❌ {model.name} ({model.model_path}) - Not installed")

        # Set default model
        self._set_default_model()

        self._initialized = True
        logger.info(f"✓ LLM Service initialized. Default model: {self._default_model_id}")

    async def _check_ollama_model_availability(self) -> set:
        """
        Check which Ollama models are actually installed
        AUTO-REGISTERS any unknown models discovered in Ollama

        Returns:
            Set of installed model names
        """
        try:
            client = httpx.AsyncClient(timeout=10.0)
            try:
                response = await client.get(f"{settings.OLLAMA_ENDPOINT}/api/tags")
                response.raise_for_status()
                data = response.json()

                # Extract model names and auto-register unknown ones
                installed_models = set()
                for model in data.get("models", []):
                    model_name = model.get("name", "")
                    model_size = model.get("size", 0)
                    installed_models.add(model_name)

                    # AUTO-REGISTER if not already in registry
                    if not self.model_registry.get_model(model_name):
                        logger.info(f"🆕 Auto-registering new Ollama model: {model_name}")
                        self._auto_register_ollama_model(model_name, model_size)

                logger.info(f"🔍 Ollama installed models: {installed_models}")
                return installed_models
            finally:
                await client.aclose()
        except Exception as e:
            logger.warning(f"⚠️  Failed to check Ollama model availability: {e}")
            logger.warning("    Assuming all registered Ollama models are available")
            return set()  # Return empty set, will mark all as unavailable

    def _auto_register_ollama_model(self, model_name: str, model_size: int):
        """
        Auto-register a discovered Ollama model with intelligent defaults

        Args:
            model_name: Model name from Ollama (e.g., "llama3.1:8b", "mistral:7b")
            model_size: Model size in bytes
        """
        import re
        from app.models.model_registry import ModelInfo, ModelProvider, ModelType

        # Extract parameter size from name (e.g., "8b", "7b", "3b", "1.5b")
        size_match = re.search(r'(\d+\.?\d*)b', model_name.lower())
        param_size = float(size_match.group(1)) if size_match else 0

        # Determine if GPU model based on size
        # Models > 3GB are likely GPU models (Q4 quantized 7B+ models)
        size_gb = model_size / (1024 ** 3)
        is_gpu_model = size_gb > 3.0 or param_size >= 7.0

        # Extract model family (e.g., "llama3.1" from "llama3.1:8b")
        family = model_name.split(':')[0] if ':' in model_name else model_name
        family_title = family.replace('.', ' ').replace('-', ' ').title()

        # Create friendly display name
        display_name = f"{family_title}"
        if param_size > 0:
            display_name += f" {param_size:.1f}B".replace('.0B', 'B')
        display_name += " (Ollama"
        if is_gpu_model:
            display_name += " GPU"
        display_name += ")"

        # Determine context length based on model family
        context_length = 128000  # Default for newer models
        if 'llama3' in model_name:
            context_length = 128000
        elif 'qwen' in model_name:
            context_length = 32768
        elif 'mistral' in model_name or 'mixtral' in model_name:
            context_length = 32768
        elif 'phi' in model_name:
            context_length = 128000

        # Create intelligent description
        description = f"Auto-registered Ollama model. "
        if is_gpu_model:
            description += f"GPU-accelerated. ~{size_gb:.1f}GB VRAM. "
        else:
            description += f"CPU model. ~{size_gb:.1f}GB RAM. "

        if param_size > 0:
            description += f"{param_size:.1f}B parameters. "

        # Add family-specific notes
        if 'llama' in model_name:
            description += "Good for general tasks and RAG."
        elif 'qwen' in model_name:
            description += "Multilingual support, good reasoning."
        elif 'mistral' in model_name:
            description += "Fast inference, balanced quality."
        elif 'deepseek' in model_name:
            description += "Specialized for coding tasks."
        elif 'phi' in model_name:
            description += "Compact model with good reasoning."

        # Register the model
        # Note: Ollama models don't require backend GPU since Ollama handles GPU inference
        model_info = ModelInfo(
            id=model_name,
            name=display_name,
            provider=ModelProvider.OLLAMA,
            model_type=ModelType.LOCAL_GPU if is_gpu_model else ModelType.LOCAL_CPU,
            model_path=model_name,
            context_length=context_length,
            cost_per_1k_tokens=0.0,  # Free local model
            requires_gpu=False,  # Ollama handles GPU internally, backend doesn't need GPU
            min_gpu_memory_gb=0,  # Ollama manages its own GPU memory
            description=description,
            recommended=param_size >= 7.0  # Recommend 7B+ models
        )

        self.model_registry.register(model_info)
        logger.info(f"   ✅ Auto-registered: {display_name} ({size_gb:.1f}GB, GPU={is_gpu_model})")

    def _update_model_availability(self):
        """Update model availability based on API keys and hardware"""

        # Update OpenAI models
        for model in self.model_registry.get_models_by_provider(ModelProvider.OPENAI):
            available = self.openai_client is not None
            self.model_registry.update_availability(model.id, available)

        # Update Claude models
        for model in self.model_registry.get_models_by_provider(ModelProvider.ANTHROPIC):
            available = self.anthropic_client is not None
            self.model_registry.update_availability(model.id, available)

        # Update vLLM models (GPU required)
        for model in self.model_registry.get_models_by_provider(ModelProvider.VLLM):
            available = (self._gpu_info.available and
                        self._gpu_info.memory_gb >= model.min_gpu_memory_gb and
                        settings.USE_VLLM)
            self.model_registry.update_availability(model.id, available)

        # Ollama models: Dynamically check what's actually installed
        # Note: This is synchronous init, actual check happens in initialize()
        for model in self.model_registry.get_models_by_provider(ModelProvider.OLLAMA):
            # Set to True initially, will be updated during async initialize()
            self.model_registry.update_availability(model.id, True)

        # llama.cpp models (deprecated - use Ollama instead)
        for model in self.model_registry.get_models_by_provider(ModelProvider.LLAMA_CPP):
            self.model_registry.update_availability(model.id, True)

    def _set_default_model(self):
        """Set the default model based on availability - dynamically selects best GPU model"""

        # Get all available models
        available_models = self.model_registry.get_available_models(
            gpu_available=self._gpu_info.available if self._gpu_info else False,
            gpu_memory_gb=self._gpu_info.memory_gb if self._gpu_info else 0
        )

        if not available_models:
            logger.warning("No models available!")
            return

        # CRITICAL: Filter out coder-specific models from default selection
        # Coder models (deepseek-coder, codellama, etc.) should ONLY be used in agent tasks, NOT in chat UI
        excluded_keywords = ['coder', 'code-', '-code']
        chat_models = [
            m for m in available_models
            if not any(keyword in m.id.lower() for keyword in excluded_keywords)
        ]

        if not chat_models:
            logger.warning("⚠️  All models are coder-specific! Falling back to proprietary models.")
            available_models = available_models  # Use all models as last resort
        else:
            available_models = chat_models
            logger.info(f"📋 Filtered to {len(chat_models)} chat-appropriate models (excluded coder-specific models)")

        # Priority: Qwen VL > GPU models > CPU models, larger parameter count > smaller
        # Rank models by desirability
        def rank_model(model):
            score = 0
            model_id = model.id.lower()

            # 🔍 HIGHEST PRIORITY: Qwen 2.5 VL (Vision-Language model)
            # This is the user's preferred default model
            if 'qwen2.5vl' in model_id or model_id == 'qwen2.5vl:latest':
                score += 10000  # Highest priority
                logger.info(f"🔍 Qwen VL model found with highest priority: {model.id}")

            # GPU models get priority
            if model.requires_gpu or 'gpu' in model_id:
                score += 1000

            # Extract parameter size (8b > 7b > 3b > 1.5b)
            import re
            size_match = re.search(r'(\d+\.?\d*)b', model_id)
            if size_match:
                size = float(size_match.group(1))
                score += size * 10  # 8b gets 80 points, 3b gets 30 points

            # Prefer qwen models (optimized for GPU, multilingual)
            if 'qwen' in model_id:
                score += 10

            # Prefer recommended models from registry
            if model.recommended:
                score += 100

            # Prefer instruct/chat variants
            if any(x in model_id for x in ['instruct', 'chat', 'turbo']):
                score += 2

            # Ollama models are local and free
            if 'ollama/' in model_id or model.model_type.value == 'local':
                score += 3

            return score

        # Sort by rank and pick the best
        available_models.sort(key=rank_model, reverse=True)
        best_model = available_models[0]
        self._default_model_id = best_model.id
        logger.info(f"🚀 Default model auto-selected: {best_model.name} (score: {rank_model(best_model)})")

        # Fallback to proprietary if no local models
        if not self._default_model_id:
            fallback_priority = ["gpt-4-turbo", "claude-3.5-sonnet", "gpt-3.5-turbo"]
            for model_id in fallback_priority:
                model = self.model_registry.get_model(model_id)
                if model and model.available:
                    self._default_model_id = model_id
                    logger.info(f"Default model set to fallback: {model.name}")
                    return

            logger.warning("No models available!")

    async def _ensure_ollama_client(self):
        """Create fresh Ollama client for each request (no caching)

        CRITICAL FIX: Always create a NEW client to avoid stale connections and event loop issues.
        This ensures each request gets a fresh httpx client with proper async context binding.
        Similar to how direct curl calls work - new connection per request.
        """
        # Always create NEW client - do not cache
        client = httpx.AsyncClient(timeout=120.0)
        logger.debug("🔄 Ollama httpx client created (fresh per request)")
        return client

    async def _ensure_vllm_client(self):
        """Ensure vLLM client is initialized with fresh connection"""
        if self.vllm_client is None:
            self.vllm_client = httpx.AsyncClient(timeout=120.0)
            logger.debug("🔄 vLLM httpx client initialized (runtime)")
        return self.vllm_client

    async def _ensure_llama_cpp_client(self):
        """Ensure llama.cpp client is initialized with fresh connection"""
        if self.llama_cpp_client is None:
            self.llama_cpp_client = httpx.AsyncClient(timeout=120.0)
            logger.debug("🔄 llama.cpp httpx client initialized (runtime)")
        return self.llama_cpp_client

    async def close(self):
        """Close HTTP clients"""
        if self.vllm_client:
            await self.vllm_client.aclose()
        if self.ollama_client:
            await self.ollama_client.aclose()
        if self.llama_cpp_client:
            await self.llama_cpp_client.aclose()

    # ============================================================================
    # PROVIDER-SPECIFIC IMPLEMENTATIONS
    # ============================================================================

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=4))
    async def _call_openai(
        self,
        model_info: ModelInfo,
        messages: List[Dict],
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> Dict:
        """Call OpenAI API"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")

        try:
            response = await self.openai_client.chat.completions.create(
                model=model_info.model_path,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return {
                "content": response.choices[0].message.content,
                "model": model_info.id,
                "model_name": model_info.name,
                "provider": "openai",
                "tokens": response.usage.total_tokens,
                "cost": (response.usage.total_tokens / 1000) * model_info.cost_per_1k_tokens
            }
        except Exception as e:
            logger.error(f"OpenAI call failed: {e}")
            raise

    async def call_openai_vision(
        self,
        model: str,
        prompt: str,
        image_base64: str,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Call OpenAI vision models (gpt-4o, gpt-4o-mini, gpt-4-vision-preview)

        Args:
            model: Model ID (e.g., "gpt-4o-mini")
            prompt: Text prompt for vision analysis
            image_base64: Base64 encoded image string
            max_tokens: Maximum tokens for completion

        Returns:
            Dict with content, usage, and model info
        """
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")

        try:
            logger.info(f"🎨 Calling OpenAI vision model: {model}")

            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=max_tokens
            )

            logger.info(f"✅ OpenAI vision call successful - {response.usage.total_tokens} tokens")

            return {
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model
            }

        except Exception as e:
            logger.error(f"❌ OpenAI vision call failed: {e}")
            raise

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=4))
    async def _call_anthropic(
        self,
        model_info: ModelInfo,
        messages: List[Dict],
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> Dict:
        """Call Anthropic Claude API"""
        if not self.anthropic_client:
            raise ValueError("Anthropic client not initialized")

        try:
            # Convert OpenAI-style messages to Claude format
            system_message = None
            claude_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    claude_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

            # Call Claude API
            response = await self.anthropic_client.messages.create(
                model=model_info.model_path,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message if system_message else "You are a helpful AI assistant.",
                messages=claude_messages
            )

            total_tokens = response.usage.input_tokens + response.usage.output_tokens

            return {
                "content": response.content[0].text,
                "model": model_info.id,
                "model_name": model_info.name,
                "provider": "anthropic",
                "tokens": total_tokens,
                "cost": (total_tokens / 1000) * model_info.cost_per_1k_tokens
            }
        except Exception as e:
            logger.error(f"Anthropic call failed: {e}")
            raise

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=4))
    async def _call_vllm(
        self,
        model_info: ModelInfo,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> Dict:
        """Call vLLM service (local GPU)"""
        try:
            client = await self._ensure_vllm_client()
            response = await client.post(
                f"{settings.VLLM_ENDPOINT}/v1/completions",
                json={
                    "model": model_info.model_path,
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": 0.9,
                }
            )
            response.raise_for_status()
            result = response.json()

            return {
                "content": result["choices"][0]["text"],
                "model": model_info.id,
                "model_name": model_info.name,
                "provider": "vllm",
                "tokens": result.get("usage", {}).get("total_tokens", 0),
                "cost": 0.0  # Local, no cost
            }
        except Exception as e:
            logger.warning(f"vLLM call failed: {e}")
            raise

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=4))
    async def _call_ollama(
        self,
        model_info: ModelInfo,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> Dict:
        """Call Ollama service (local CPU/GPU)"""
        # CRITICAL: Get fresh httpx client for this request
        client = await self._ensure_ollama_client()

        try:
            logger.info(f"🔧 Calling Ollama: model={model_info.model_path}, endpoint={settings.OLLAMA_ENDPOINT}")
            logger.info(f"🔧 Prompt length: {len(prompt)} chars, max_tokens: {max_tokens}")

            response = await client.post(
                f"{settings.OLLAMA_ENDPOINT}/api/generate",
                json={
                    "model": model_info.model_path,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature,
                        "top_p": 0.9,
                        "stop": ["</s>", "Human:", "User:"],
                    }
                }
            )

            logger.info(f"🔧 Response status: {response.status_code}")
            response.raise_for_status()
            result = response.json()

            logger.info(f"✅ Ollama response received: {len(result.get('response', ''))} chars")

            return {
                "content": result["response"],
                "model": model_info.id,
                "model_name": model_info.name,
                "provider": "ollama",
                "tokens": result.get("eval_count", 0) + result.get("prompt_eval_count", 0),
                "cost": 0.0  # Local, no cost
            }
        except Exception as e:
            logger.error(f"❌ Ollama call failed: {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            if hasattr(e, 'response'):
                logger.error(f"❌ Response status: {e.response.status_code}")
                logger.error(f"❌ Response body: {e.response.text[:500]}")
            raise
        finally:
            # Always close the fresh client after use (no caching)
            await client.aclose()
            logger.debug("🔒 Ollama httpx client closed")

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=4))
    async def _call_llama_cpp(
        self,
        model_info: ModelInfo,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> Dict:
        """Call llama.cpp service (local CPU) - DEPRECATED, use Ollama instead"""
        try:
            response = await self.llama_cpp_client.post(
                f"{settings.LLAMA_CPP_ENDPOINT}/completion",
                json={
                    "prompt": prompt,
                    "n_predict": max_tokens,
                    "temperature": temperature,
                    "top_p": 0.9,
                    "stop": ["</s>", "Human:", "User:"],
                }
            )
            response.raise_for_status()
            result = response.json()

            return {
                "content": result["content"],
                "model": model_info.id,
                "model_name": model_info.name,
                "provider": "llama.cpp",
                "tokens": result.get("tokens_evaluated", 0),
                "cost": 0.0  # Local, no cost
            }
        except Exception as e:
            logger.warning(f"llama.cpp call failed: {e}")
            raise

    # ============================================================================
    # STREAMING METHODS
    # ============================================================================

    async def _call_openai_stream(
        self,
        model_info: ModelInfo,
        messages: List[Dict],
        max_tokens: int = 512,
        temperature: float = 0.7
    ):
        """Stream responses from OpenAI API"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")

        try:
            stream = await self.openai_client.chat.completions.create(
                model=model_info.model_path,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {
                        "type": "content",
                        "content": chunk.choices[0].delta.content,
                        "model": model_info.id
                    }

        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "model": model_info.id
            }

    async def _call_anthropic_stream(
        self,
        model_info: ModelInfo,
        messages: List[Dict],
        max_tokens: int = 512,
        temperature: float = 0.7
    ):
        """Stream responses from Anthropic Claude API"""
        if not self.anthropic_client:
            raise ValueError("Anthropic client not initialized")

        try:
            # Convert OpenAI-style messages to Claude format
            system_message = None
            claude_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    claude_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

            # Call Claude API with streaming
            async with self.anthropic_client.messages.stream(
                model=model_info.model_path,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message if system_message else "You are a helpful AI assistant.",
                messages=claude_messages
            ) as stream:
                async for text in stream.text_stream:
                    yield {
                        "type": "content",
                        "content": text,
                        "model": model_info.id
                    }

        except Exception as e:
            logger.error(f"Anthropic streaming failed: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "model": model_info.id
            }

    async def _call_ollama_stream(
        self,
        model_info: ModelInfo,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7
    ):
        """Stream responses from Ollama service"""
        client = await self._ensure_ollama_client()

        try:
            logger.info(f"🔧 Streaming from Ollama: model={model_info.model_path}")

            response = await client.post(
                f"{settings.OLLAMA_ENDPOINT}/api/generate",
                json={
                    "model": model_info.model_path,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature,
                        "top_p": 0.9,
                        "stop": ["</s>", "Human:", "User:"],
                    }
                }
            )

            response.raise_for_status()

            # Stream line by line
            async for line in response.aiter_lines():
                if line:
                    try:
                        import json
                        chunk = json.loads(line)
                        if "response" in chunk and chunk["response"]:
                            yield {
                                "type": "content",
                                "content": chunk["response"],
                                "model": model_info.id
                            }
                        if chunk.get("done", False):
                            logger.info("✅ Ollama stream completed")
                            break
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in Ollama stream: {line}")
                        continue

        except Exception as e:
            logger.error(f"❌ Ollama streaming failed: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "model": model_info.id
            }
        finally:
            await client.aclose()

    async def generate_stream(
        self,
        prompt: str,
        messages: Optional[List[Dict]] = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
        model_id: Optional[str] = None
    ):
        """
        Stream response generation using specified or default model

        Args:
            prompt: Text prompt
            messages: Chat messages (for chat models)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            model_id: Optional model ID (uses default if not specified)

        Yields:
            Dict with type ('content' or 'error'), content, and model info
        """
        # Lazy initialization
        if not self._initialized:
            logger.warning("⚠️  LLM service not initialized, initializing now (lazy init)")
            await self.initialize()

        # Get model info
        if model_id is None:
            model_id = self._default_model_id
            logger.info(f"🎯 No model specified, using default: {model_id}")

        # Strip "ollama/" prefix if present (chat UI sends "ollama/model-name")
        if model_id and model_id.startswith("ollama/"):
            original_id = model_id
            model_id = model_id.replace("ollama/", "")
            logger.info(f"🔧 Stripped ollama prefix: {original_id} -> {model_id}")

        model_info = self.model_registry.get_model(model_id)

        # If not found and doesn't have :latest tag, try adding it (Ollama models default to :latest)
        if not model_info and not ":" in model_id:
            model_id_with_tag = f"{model_id}:latest"
            model_info = self.model_registry.get_model(model_id_with_tag)
            if model_info:
                logger.info(f"🔧 Found model with :latest tag: {model_id} -> {model_id_with_tag}")
                model_id = model_id_with_tag

        if not model_info:
            yield {
                "type": "error",
                "error": f"Model not found: {model_id}",
                "model": model_id
            }
            return

        if not model_info.available:
            yield {
                "type": "error",
                "error": f"Model not available: {model_info.name}",
                "model": model_id
            }
            return

        logger.info(f"✅ Streaming from: {model_info.name} via {model_info.provider.value} provider")

        # Convert prompt to messages if needed
        if not messages:
            messages = [{"role": "user", "content": prompt}]

        # Route to appropriate provider streaming method
        try:
            if model_info.provider == ModelProvider.OPENAI:
                async for chunk in self._call_openai_stream(model_info, messages, max_tokens, temperature):
                    yield chunk

            elif model_info.provider == ModelProvider.ANTHROPIC:
                async for chunk in self._call_anthropic_stream(model_info, messages, max_tokens, temperature):
                    yield chunk

            elif model_info.provider == ModelProvider.OLLAMA:
                prompt_text = self._messages_to_prompt(messages)
                async for chunk in self._call_ollama_stream(model_info, prompt_text, max_tokens, temperature):
                    yield chunk

            else:
                # For providers that don't support streaming, fall back to non-streaming
                logger.warning(f"Streaming not supported for {model_info.provider.value}, using non-streaming fallback")
                result = await self.generate(prompt, messages, max_tokens, temperature, model_id)
                yield {
                    "type": "content",
                    "content": result["content"],
                    "model": model_info.id
                }

        except Exception as e:
            logger.error(f"❌ Streaming failed with {model_info.name}: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "model": model_info.id
            }

    # ============================================================================
    # PUBLIC API
    # ============================================================================

    async def generate(
        self,
        prompt: str,
        messages: Optional[List[Dict]] = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
        model_id: Optional[str] = None,
        allow_fallback: bool = False  # 🆕 Control automatic model fallback
    ) -> Dict:
        """
        Generate response using specified or default model

        Args:
            prompt: Text prompt
            messages: Chat messages (for chat models)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            model_id: Optional model ID (uses default if not specified)
            allow_fallback: Allow automatic model fallback for memory constraints (default: False for chat UI)

        Returns:
            Dict with content, model, tokens, cost
        """
        # Import model registry classes at function start to ensure they're in scope
        from app.models.model_registry import ModelInfo, ModelProvider, ModelType

        # DEBUG: Log entry to this method
        logger.info(f"🚀 generate() called with model_id={model_id}, prompt_len={len(prompt)}")

        # Lazy initialization - ensure service is initialized before first use
        # This handles cases where uvicorn --reload prevents lifespan from running
        if not self._initialized:
            logger.warning("⚠️  LLM service not initialized, initializing now (lazy init)")
            await self.initialize()
            logger.info("✅ Lazy init completed")

        start_time = time.time()

        # Get model info
        requested_model_id = model_id  # Store original request for logging
        if model_id is None:
            model_id = self._default_model_id
            logger.info(f"🎯 No model specified, using default: {model_id}")
        else:
            logger.info(f"🎯 Model requested: {model_id}")

        # Strip "ollama/" prefix if present (chat UI sends "ollama/model-name")
        if model_id and model_id.startswith("ollama/"):
            original_id = model_id
            model_id = model_id.replace("ollama/", "")
            logger.info(f"🔧 Stripped ollama prefix: {original_id} -> {model_id}")

        model_info = self.model_registry.get_model(model_id)

        # If not found and doesn't have :latest tag, try adding it (Ollama models default to :latest)
        if not model_info and not ":" in model_id:
            model_id_with_tag = f"{model_id}:latest"
            model_info = self.model_registry.get_model(model_id_with_tag)
            if model_info:
                logger.info(f"🔧 Found model with :latest tag: {model_id} -> {model_id_with_tag}")
                model_id = model_id_with_tag

        # If still not found, check if it exists in Ollama dynamically (for fine-tuned models)
        if not model_info:
            logger.info(f"🔍 Model not in registry, checking Ollama API for: {model_id}")
            try:
                ollama_models = await self._get_available_ollama_models()
                # Check both with and without :latest tag
                model_names_to_check = [model_id]
                if not ":" in model_id:
                    model_names_to_check.append(f"{model_id}:latest")

                for ollama_model in ollama_models:
                    if ollama_model["name"] in model_names_to_check:
                        logger.info(f"✅ Found model in Ollama: {ollama_model['name']} ({ollama_model['size_gb']:.2f} GB)")
                        # Create a dynamic ModelInfo for this Ollama model
                        model_info = ModelInfo(
                            id=ollama_model["name"],
                            name=f"{ollama_model['name']} (Fine-tuned)",
                            provider=ModelProvider.OLLAMA,
                            model_type=ModelType.LOCAL_GPU,  # Assume GPU for fine-tuned models
                            model_path=ollama_model["name"],
                            context_length=32768,
                            cost_per_1k_tokens=0.0,
                            requires_gpu=True,
                            min_gpu_memory_gb=ollama_model["size_gb"],
                            description=f"Fine-tuned model deployed to Ollama ({ollama_model['size_gb']:.2f} GB)",
                            recommended=False,
                            available=True
                        )
                        model_id = ollama_model["name"]
                        break
            except Exception as e:
                logger.error(f"Error checking Ollama API: {e}")
                import traceback
                logger.error(traceback.format_exc())

        if not model_info:
            logger.error(f"❌ Model not found in registry or Ollama: {model_id}")
            raise ValueError(f"Model not found: {model_id}")

        if not model_info.available:
            logger.error(f"❌ Model not available: {model_info.name} (provider: {model_info.provider.value})")
            logger.error(f"   Reasons: API key missing or hardware insufficient")
            raise ValueError(f"Model not available: {model_info.name}")

        logger.info(f"✅ Routing to: {model_info.name} via {model_info.provider.value} provider")

        # MEMORY CHECK: For Ollama models, check if model fits in available memory
        # 🆕 CRITICAL FIX: Only fallback if allow_fallback=True (agent tasks)
        # For chat UI (allow_fallback=False), raise error instead of silently switching models
        memory_check_result = None
        if model_info.provider == ModelProvider.OLLAMA and allow_fallback:
            original_model_id = model_id
            memory_check_result = await self._select_model_with_memory_check(model_id)
            model_id = memory_check_result["model_id"]

            # If model changed due to memory constraints, update model_info and log audit trail
            if memory_check_result["fallback"]:
                logger.warning(
                    f"🔄 MODEL FALLBACK (AGENT TASK ONLY): Memory constraints detected\n"
                    f"   Requested: {original_model_id} (requires {memory_check_result.get('required_memory_mb', 0):.0f}MB)\n"
                    f"   Available memory: {memory_check_result['available_memory_mb']:.0f}MB\n"
                    f"   Fallback: {model_id} (requires {memory_check_result.get('fallback_model_size_mb', 0):.0f}MB)\n"
                    f"   Reason: {memory_check_result['reason']}\n"
                    f"   Strategy: Selected LARGEST chat model that fits in available memory\n"
                    f"   Audit: User selected {original_model_id}, system used {model_id} for this agent task only"
                )

                model_info = self.model_registry.get_model(model_id)
                if not model_info:
                    logger.error(f"❌ Fallback model not found in registry: {model_id}")
                    raise ValueError(f"Fallback model not found: {model_id}")
            else:
                logger.info(f"✅ Using user-selected model: {model_id} (no fallback needed)")
        elif model_info.provider == ModelProvider.OLLAMA and not allow_fallback:
            # 🆕 For chat UI: Just use the selected model as-is (no fallback)
            logger.info(f"✅ Using user-selected model: {model_id} (fallback disabled for chat UI)")

        # Convert prompt to messages if needed
        if not messages:
            messages = [{"role": "user", "content": prompt}]

        # Route to appropriate provider
        try:
            if model_info.provider == ModelProvider.OPENAI:
                result = await self._call_openai(model_info, messages, max_tokens, temperature)

            elif model_info.provider == ModelProvider.ANTHROPIC:
                result = await self._call_anthropic(model_info, messages, max_tokens, temperature)

            elif model_info.provider == ModelProvider.VLLM:
                # vLLM works better with raw prompts
                prompt_text = self._messages_to_prompt(messages)
                result = await self._call_vllm(model_info, prompt_text, max_tokens, temperature)

            elif model_info.provider == ModelProvider.OLLAMA:
                # Ollama works with raw prompts
                prompt_text = self._messages_to_prompt(messages)
                result = await self._call_ollama(model_info, prompt_text, max_tokens, temperature)

            elif model_info.provider == ModelProvider.LLAMA_CPP:
                # llama.cpp works with raw prompts (deprecated - use Ollama)
                prompt_text = self._messages_to_prompt(messages)
                result = await self._call_llama_cpp(model_info, prompt_text, max_tokens, temperature)

            else:
                raise ValueError(f"Unknown provider: {model_info.provider}")

            # Add latency
            result["latency_ms"] = (time.time() - start_time) * 1000

            # Add memory check audit information if fallback occurred
            if memory_check_result and memory_check_result["fallback"]:
                result["model_fallback"] = {
                    "occurred": True,
                    "user_selected_model": memory_check_result["original_model"],
                    "system_used_model": memory_check_result["model_id"],
                    "reason": memory_check_result["reason"],
                    "available_memory_mb": memory_check_result["available_memory_mb"],
                    "required_memory_mb": memory_check_result.get("required_memory_mb"),
                    "fallback_model_size_mb": memory_check_result.get("fallback_model_size_mb"),
                    "strategy": "selected_largest_fitting_model"
                }
                logger.info(
                    f"📊 AUDIT: Model fallback metadata added to response for transparency\n"
                    f"   User will see that {memory_check_result['original_model']} was requested\n"
                    f"   but {memory_check_result['model_id']} was used due to memory constraints"
                )
            else:
                result["model_fallback"] = {"occurred": False}

            # Log successful generation with detailed model info
            logger.info(f"✅ SUCCESS: Generated {result['tokens']} tokens in {result['latency_ms']:.0f}ms using {result['model_name']} (${result.get('cost', 0):.4f})")

            # Validation: Ensure the model used matches what was requested (or fallback)
            if requested_model_id and result['model'] != model_id:
                logger.warning(f"⚠️ Model mismatch: requested={requested_model_id}, used={result['model']}")
            else:
                logger.debug(f"✅ Model routing validated: requested={requested_model_id or 'default'}, used={result['model']}")

            return result

        except Exception as e:
            logger.error(f"❌ Generation FAILED with {model_info.name} ({model_info.provider.value}): {e}")
            raise

    def _messages_to_prompt(self, messages: List[Dict]) -> str:
        """Convert chat messages to a single prompt string"""
        prompt_parts = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)

    def get_available_models(self) -> Dict:
        """Get all available models grouped by type"""
        available = self.model_registry.get_available_models(
            gpu_available=self._gpu_info.available if self._gpu_info else False,
            gpu_memory_gb=self._gpu_info.memory_gb if self._gpu_info else 0
        )

        return {
            "models": [m.to_dict() for m in available],
            "grouped": self.model_registry.get_models_grouped(),
            "default": self._default_model_id,
            "gpu_info": {
                "available": self._gpu_info.available if self._gpu_info else False,
                "type": self._gpu_info.type if self._gpu_info else "cpu",
                "memory_gb": self._gpu_info.memory_gb if self._gpu_info else 0
            }
        }

    def set_default_model(self, model_id: str):
        """Set the default model"""
        model = self.model_registry.get_model(model_id)
        if not model:
            raise ValueError(f"Model not found: {model_id}")
        if not model.available:
            raise ValueError(f"Model not available: {model.name}")

        self._default_model_id = model_id
        logger.info(f"Default model changed to: {model.name}")

    async def generate_with_context(
        self,
        query: str,
        context_chunks: List[Dict],
        conversation_history: Optional[List[Dict]] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        model_id: Optional[str] = None,
        allow_fallback: bool = False  # 🆕 Control automatic model fallback
    ) -> Dict:
        """Generate response with RAG context"""
        # Build context from chunks
        context_parts = []
        for i, chunk in enumerate(context_chunks):
            # Get source info from chunk metadata
            source_info = chunk.get('filename', chunk.get('source', 'unknown'))
            memory_type = chunk.get('memory_type', '')
            memory_indicator = f" [Session Document]" if memory_type == 'short-term' else ""

            context_parts.append(
                f"[Source {i+1}: {source_info}{memory_indicator}]\n{chunk['content']}"
            )

        context_text = "\n\n".join(context_parts)

        # Build prompt with clear instructions
        system_prompt = """You are a helpful AI assistant with access to relevant documents and information.

IMPORTANT INSTRUCTIONS:
- Use the provided context documents to answer questions accurately and comprehensively
- Always cite your sources using [Source N] notation when referencing information
- Documents marked as [Session Document] are specifically uploaded for this conversation
- If the context contains the answer, provide it in detail
- If the context doesn't contain enough information, say so clearly
- Be conversational and helpful in your responses"""

        user_prompt = f"""Here are the relevant documents to help answer the question:

{context_text}

Question: {query}

Based on the documents provided above, please give a detailed and accurate answer. Cite your sources using [Source N] format."""

        # Prepare messages with conversation history
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        # Include conversation history for context continuity
        if conversation_history:
            # Include last 6 messages (3 exchanges) for context window management
            messages.extend(conversation_history[-6:])

        # Add the current query with context
        messages.append({"role": "user", "content": user_prompt})

        # Convert to single prompt for compatibility with non-chat models
        prompt = self._messages_to_prompt(messages)

        return await self.generate(
            prompt=prompt,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            model_id=model_id,
            allow_fallback=allow_fallback  # 🆕 Pass through fallback control
        )


# Global singleton
llm_service = LLMService()


def get_llm_service() -> LLMService:
    """Get the global LLM service instance"""
    return llm_service
