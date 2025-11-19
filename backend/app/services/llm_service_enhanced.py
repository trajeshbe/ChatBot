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

        Returns:
            Set of installed model names
        """
        try:
            client = httpx.AsyncClient(timeout=10.0)
            try:
                response = await client.get(f"{settings.OLLAMA_ENDPOINT}/api/tags")
                response.raise_for_status()
                data = response.json()

                # Extract model names from response
                installed_models = set()
                for model in data.get("models", []):
                    model_name = model.get("name", "")
                    installed_models.add(model_name)

                logger.info(f"🔍 Ollama installed models: {installed_models}")
                return installed_models
            finally:
                await client.aclose()
        except Exception as e:
            logger.warning(f"⚠️  Failed to check Ollama model availability: {e}")
            logger.warning("    Assuming all registered Ollama models are available")
            return set()  # Return empty set, will mark all as unavailable

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
        """Set the default model based on availability"""

        # Priority order for default model
        # 🔄 CHANGED 2025-11-18: Prioritize local Ollama models (no API key needed)
        priority_models = [
            "llama3.2:3b",           # ✅ Best local model (Ollama) - FREE
            "qwen2.5:1.5b",          # ✅ Fast local model (Ollama) - FREE
            "llama-3.1-8b",          # Best local GPU (if GPU available)
            "gpt-4-turbo",           # Best quality (requires OpenAI API key)
            "claude-3.5-sonnet",     # Best alternative (requires Anthropic API key)
            "llama-3.2-3b-cpu",      # Fallback local CPU
            "tinyllama-cpu",         # Final fallback
        ]

        for model_id in priority_models:
            model = self.model_registry.get_model(model_id)
            if model and model.available:
                self._default_model_id = model_id
                logger.info(f"Default model set to: {model.name}")
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

        model_info = self.model_registry.get_model(model_id)
        if not model_info:
            logger.error(f"❌ Model not found in registry: {model_id}")
            raise ValueError(f"Model not found: {model_id}")

        if not model_info.available:
            logger.error(f"❌ Model not available: {model_info.name} (provider: {model_info.provider.value})")
            logger.error(f"   Reasons: API key missing or hardware insufficient")
            raise ValueError(f"Model not available: {model_info.name}")

        logger.info(f"✅ Routing to: {model_info.name} via {model_info.provider.value} provider")

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

            # Log successful generation with detailed model info
            logger.info(f"✅ SUCCESS: Generated {result['tokens']} tokens in {result['latency_ms']:.0f}ms using {result['model_name']} (${result.get('cost', 0):.4f})")

            # Validation: Ensure the model used matches what was requested
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
        model_id: Optional[str] = None
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
            model_id=model_id
        )


# Global singleton
llm_service = EnhancedLLMService()
