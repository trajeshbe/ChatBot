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
from typing import Dict, List, Optional
import logging
from app.core.config import settings
from app.models.model_registry import get_model_registry, ModelInfo, ModelProvider
from app.utils.gpu_detector import get_gpu_detector
from tenacity import retry, stop_after_attempt, wait_exponential
import time

logger = logging.getLogger(__name__)


class EnhancedLLMService:
    """Enhanced LLM service with multi-model support"""

    def __init__(self):
        # API clients
        self.openai_client: Optional[AsyncOpenAI] = None
        self.anthropic_client: Optional[AsyncAnthropic] = None

        # HTTP clients for local models
        self.vllm_client = httpx.AsyncClient(timeout=120.0)
        self.llama_cpp_client = httpx.AsyncClient(timeout=120.0)

        # Model registry and GPU detector
        self.model_registry = get_model_registry()
        self.gpu_detector = get_gpu_detector()

        # State
        self._initialized = False
        self._default_model_id: Optional[str] = None
        self._gpu_info = None

    async def initialize(self):
        """Initialize LLM clients and detect hardware"""
        if self._initialized:
            return

        logger.info("Initializing Enhanced LLM Service...")

        # Detect GPU
        self._gpu_info = self.gpu_detector.detect()
        logger.info(f"GPU Detection: {self._gpu_info.type} ({'available' if self._gpu_info.available else 'not available'})")

        # Initialize OpenAI
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip():
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("✓ OpenAI client initialized")
        else:
            logger.info("OpenAI API key not configured")

        # Initialize Anthropic/Claude
        anthropic_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        if anthropic_key and anthropic_key.strip():
            self.anthropic_client = AsyncAnthropic(api_key=anthropic_key)
            logger.info("✓ Anthropic/Claude client initialized")
        else:
            logger.info("Anthropic API key not configured")

        # Update model availability based on hardware and API keys
        self._update_model_availability()

        # Set default model
        self._set_default_model()

        self._initialized = True
        logger.info(f"✓ LLM Service initialized. Default model: {self._default_model_id}")

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

        # Ollama models always available (CPU-based)
        for model in self.model_registry.get_models_by_provider(ModelProvider.OLLAMA):
            self.model_registry.update_availability(model.id, True)

        # llama.cpp models (deprecated - use Ollama instead)
        for model in self.model_registry.get_models_by_provider(ModelProvider.LLAMA_CPP):
            self.model_registry.update_availability(model.id, True)

    def _set_default_model(self):
        """Set the default model based on availability"""

        # Priority order for default model
        priority_models = [
            "gpt-4-turbo",           # Best quality (if API key exists)
            "claude-3.5-sonnet",     # Best alternative
            "llama-3.1-8b",          # Best local GPU
            "llama-3.2-3b-cpu",      # Best local CPU
            "tinyllama-cpu",         # Fallback
        ]

        for model_id in priority_models:
            model = self.model_registry.get_model(model_id)
            if model and model.available:
                self._default_model_id = model_id
                logger.info(f"Default model set to: {model.name}")
                return

        logger.warning("No models available!")

    async def close(self):
        """Close HTTP clients"""
        await self.vllm_client.aclose()
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
            response = await self.vllm_client.post(
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
        try:
            response = await self.llama_cpp_client.post(
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
            response.raise_for_status()
            result = response.json()

            return {
                "content": result["response"],
                "model": model_info.id,
                "model_name": model_info.name,
                "provider": "ollama",
                "tokens": result.get("eval_count", 0) + result.get("prompt_eval_count", 0),
                "cost": 0.0  # Local, no cost
            }
        except Exception as e:
            logger.warning(f"Ollama call failed: {e}")
            raise

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
    # PUBLIC API
    # ============================================================================

    async def generate(
        self,
        prompt: str,
        messages: Optional[List[Dict]] = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
        model_id: Optional[str] = None
    ) -> Dict:
        """
        Generate response using specified or default model

        Args:
            prompt: Text prompt
            messages: Chat messages (for chat models)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            model_id: Optional model ID (uses default if not specified)

        Returns:
            Dict with content, model, tokens, cost
        """
        start_time = time.time()

        # Get model info
        if model_id is None:
            model_id = self._default_model_id

        model_info = self.model_registry.get_model(model_id)
        if not model_info:
            raise ValueError(f"Model not found: {model_id}")

        if not model_info.available:
            raise ValueError(f"Model not available: {model_info.name}")

        logger.info(f"Generating with model: {model_info.name} ({model_info.provider.value})")

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
            logger.info(f"✓ Generated {result['tokens']} tokens in {result['latency_ms']:.0f}ms (${result.get('cost', 0):.4f})")

            return result

        except Exception as e:
            logger.error(f"Generation failed with {model_info.name}: {e}")
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
        model_id: Optional[str] = None
    ) -> Dict:
        """Generate response with RAG context"""
        # Build context from chunks
        context_text = "\n\n".join([
            f"Source {i+1} ({chunk.get('source', 'unknown')}):\n{chunk['content']}"
            for i, chunk in enumerate(context_chunks)
        ])

        # Build prompt
        system_prompt = """You are a helpful AI assistant with access to relevant documents and information.
Use the provided context to answer questions accurately. Always cite your sources using [Source N] notation.
If the context doesn't contain enough information to answer the question, say so clearly."""

        user_prompt = f"""Context:
{context_text}

Question: {query}

Please provide a detailed answer based on the context above, and cite your sources."""

        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        if conversation_history:
            messages.extend(conversation_history[-6:])  # Last 3 turns

        messages.append({"role": "user", "content": user_prompt})

        # Convert to single prompt for compatibility
        prompt = self._messages_to_prompt(messages)

        return await self.generate(
            prompt=prompt,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            model_id=model_id
        )


# Global singleton
llm_service = EnhancedLLMService()
