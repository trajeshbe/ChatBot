import httpx
from openai import AsyncOpenAI
from typing import Dict, List, Optional, AsyncGenerator
import logging
from app.core.config import settings
from tenacity import retry, stop_after_attempt, wait_exponential
import time

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.openai_client = None
        self.vllm_client = None
        self.llama_cpp_client = None
        self.ollama_client = None
        self._initialized = False

    async def initialize(self):
        """Initialize LLM clients"""
        if self._initialized:
            return

        if settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("OpenAI client initialized")

        self._initialized = True

    async def _ensure_ollama_client(self):
        """Ensure Ollama client is initialized with fresh connection"""
        if self.ollama_client is None:
            # CRITICAL: Initialize httpx client at runtime to avoid stale connections
            # This follows the same pattern as Playwright fix in PLAYWRIGHT_INVESTIGATION.md
            self.ollama_client = httpx.AsyncClient(timeout=120.0)
            logger.debug("🔄 Ollama httpx client initialized (runtime)")
        return self.ollama_client

    async def _ensure_vllm_client(self):
        """Ensure vLLM client is initialized with fresh connection"""
        if self.vllm_client is None:
            self.vllm_client = httpx.AsyncClient(timeout=60.0)
            logger.debug("🔄 vLLM httpx client initialized (runtime)")
        return self.vllm_client

    async def _ensure_llama_cpp_client(self):
        """Ensure llama.cpp client is initialized with fresh connection"""
        if self.llama_cpp_client is None:
            self.llama_cpp_client = httpx.AsyncClient(timeout=60.0)
            logger.debug("🔄 llama.cpp httpx client initialized (runtime)")
        return self.llama_cpp_client

    async def close(self):
        """Close HTTP clients"""
        if self.vllm_client:
            await self.vllm_client.aclose()
        if self.llama_cpp_client:
            await self.llama_cpp_client.aclose()
        if self.ollama_client:
            await self.ollama_client.aclose()

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=4))
    async def _call_vllm(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> Dict:
        """Call vLLM service"""
        try:
            client = await self._ensure_vllm_client()
            response = await client.post(
                f"{settings.VLLM_ENDPOINT}/v1/completions",
                json={
                    "model": settings.VLLM_MODEL,
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": 0.9,
                }
            )
            response.raise_for_status()
            return {
                "content": response.json()["choices"][0]["text"],
                "model": "vllm",
                "model_name": "Local GPU (vLLM)",
                "tokens": response.json().get("usage", {}).get("total_tokens", 0)
            }
        except Exception as e:
            logger.warning(f"vLLM call failed: {e}")
            raise

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=4))
    async def _call_llama_cpp(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> Dict:
        """Call llama.cpp service as CPU fallback (DEPRECATED - use Ollama instead)"""
        try:
            client = await self._ensure_llama_cpp_client()
            response = await client.post(
                f"{settings.LLAMA_CPP_ENDPOINT}/completion",
                json={
                    "prompt": prompt,
                    "n_predict": max_tokens,
                    "temperature": temperature,
                    "top_p": 0.9,
                }
            )
            response.raise_for_status()
            return {
                "content": response.json()["content"],
                "model": "llama-cpp",
                "model_name": "Local CPU (llama.cpp)",
                "tokens": response.json().get("tokens_evaluated", 0)
            }
        except Exception as e:
            logger.warning(f"llama.cpp call failed: {e}")
            raise

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=4))
    async def _call_ollama(self, prompt: str, messages: Optional[List[Dict]] = None, max_tokens: int = 512, temperature: float = 0.7) -> Dict:
        """Call Ollama service for local LLM inference"""
        try:
            # CRITICAL: Ensure fresh httpx client (runtime initialization)
            client = await self._ensure_ollama_client()

            # Ollama endpoint (from settings or default)
            ollama_endpoint = getattr(settings, 'OLLAMA_ENDPOINT', 'http://ollama:11434')
            # Default model (can be configured in settings)
            ollama_model = getattr(settings, 'OLLAMA_MODEL', 'llama3.2:3b')

            logger.info(f"🦙 Calling Ollama at {ollama_endpoint}")
            logger.info(f"📦 Using model: {ollama_model}")

            # Ollama supports chat API (preferred)
            if messages:
                logger.info(f"💬 Using Ollama chat API with {len(messages)} messages")
                response = await client.post(
                    f"{ollama_endpoint}/api/chat",
                    json={
                        "model": ollama_model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                        }
                    }
                )
            else:
                # Fallback to generate API
                logger.info(f"📝 Using Ollama generate API")
                response = await client.post(
                    f"{ollama_endpoint}/api/generate",
                    json={
                        "model": ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                        }
                    }
                )

            response.raise_for_status()
            result_json = response.json()

            # Extract content based on API used
            if messages:
                content = result_json.get("message", {}).get("content", "")
            else:
                content = result_json.get("response", "")

            logger.info(f"✅ Ollama response received ({len(content)} chars)")

            return {
                "content": content,
                "model": "ollama",
                "model_name": f"Ollama ({ollama_model})",
                "tokens": result_json.get("eval_count", 0) + result_json.get("prompt_eval_count", 0)
            }

        except httpx.ConnectError as e:
            logger.error(f"❌ Ollama connection failed: {e}")
            logger.error("💡 Is Ollama service running? Check: docker ps | grep ollama")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Ollama HTTP error: {e}")
            logger.error(f"💡 Status: {e.response.status_code}")
            if e.response.status_code == 404:
                logger.error(f"💡 Model '{ollama_model}' not found. Pull it with: ollama pull {ollama_model}")
            raise
        except Exception as e:
            logger.error(f"❌ Ollama call failed: {e}")
            raise

    async def _call_openai(self, messages: List[Dict], max_tokens: int = 512, temperature: float = 0.7) -> Dict:
        """Call OpenAI API as final fallback"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")

        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return {
                "content": response.choices[0].message.content,
                "model": "openai",
                "model_name": f"OpenAI ({settings.OPENAI_MODEL})",
                "tokens": response.usage.total_tokens
            }
        except Exception as e:
            error_str = str(e).lower()
            if "api_key" in error_str or "authentication" in error_str or "401" in error_str:
                logger.error(f"OpenAI authentication failed: {e}. Please check OPENAI_API_KEY in .env")
            elif "rate_limit" in error_str or "429" in error_str:
                logger.error(f"OpenAI rate limit exceeded: {e}")
            else:
                logger.error(f"OpenAI call failed: {e}")
            raise

    async def generate(
        self,
        prompt: str,
        messages: Optional[List[Dict]] = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
        use_fallback: bool = True,
        model_id: Optional[str] = None
    ) -> Dict:
        """
        Generate response with automatic fallback chain:
        OpenAI -> Ollama -> vLLM -> llama.cpp

        Prioritizes OpenAI for speed and reliability, with local LLM fallback

        Args:
            model_id: Optional model identifier (for enhanced service compatibility)
        """
        start_time = time.time()

        logger.info("="*60)
        logger.info("🤖 LLM GENERATION REQUEST")
        logger.info(f"📝 Prompt length: {len(prompt)} chars")
        logger.info(f"💬 Messages: {len(messages) if messages else 0}")
        logger.info(f"🎯 Max tokens: {max_tokens}")
        logger.info(f"🌡️  Temperature: {temperature}")
        logger.info("="*60)

        # Note: Basic service uses automatic fallback chain
        # model_id parameter accepted for compatibility with enhanced service

        # Try OpenAI first (fastest and most reliable)
        if self.openai_client:
            try:
                logger.info("🔵 Trying OpenAI...")
                if not messages:
                    messages = [{"role": "user", "content": prompt}]
                result = await self._call_openai(messages, max_tokens, temperature)
                result["latency_ms"] = (time.time() - start_time) * 1000
                logger.info(f"✅ Using OpenAI (latency: {result['latency_ms']:.0f}ms)")
                return result
            except Exception as e:
                logger.warning(f"⚠️  OpenAI failed, trying Ollama: {e}")

        # Fallback to Ollama (local LLM - preferred for privacy)
        if use_fallback:
            try:
                logger.info("🦙 Trying Ollama (local LLM)...")
                if not messages:
                    messages = [{"role": "user", "content": prompt}]
                result = await self._call_ollama(prompt, messages, max_tokens, temperature)
                result["latency_ms"] = (time.time() - start_time) * 1000
                logger.info(f"✅ Using Ollama fallback (latency: {result['latency_ms']:.0f}ms)")
                return result
            except Exception as e:
                logger.warning(f"⚠️  Ollama failed, trying vLLM: {e}")

        # Fallback to vLLM if enabled (GPU-accelerated)
        if use_fallback and getattr(settings, 'USE_VLLM', False):
            try:
                logger.info("🚀 Trying vLLM (GPU)...")
                result = await self._call_vllm(prompt, max_tokens, temperature)
                result["latency_ms"] = (time.time() - start_time) * 1000
                logger.info(f"✅ Using vLLM fallback (latency: {result['latency_ms']:.0f}ms)")
                return result
            except Exception as e:
                logger.warning(f"⚠️  vLLM failed, trying llama.cpp: {e}")

        # Final fallback to llama.cpp CPU (DEPRECATED)
        if use_fallback:
            try:
                logger.info("🔧 Trying llama.cpp (deprecated, use Ollama instead)...")
                result = await self._call_llama_cpp(prompt, max_tokens, temperature)
                result["latency_ms"] = (time.time() - start_time) * 1000
                logger.info(f"✅ Using llama.cpp fallback (latency: {result['latency_ms']:.0f}ms)")
                return result
            except Exception as e:
                logger.warning(f"⚠️  llama.cpp failed: {e}")

        # No LLM backend available
        error_msg = (
            "❌ No LLM backend available. Please configure one of the following:\n\n"
            "1. 🔵 OpenAI (Recommended - Fast & Reliable)\n"
            "   - Get your key from: https://platform.openai.com/api-keys\n"
            "   - Add to .env file: OPENAI_API_KEY=sk-...\n\n"
            "2. 🦙 Ollama (Recommended for local/privacy)\n"
            "   - Start service: docker-compose up -d ollama\n"
            "   - Pull a model: docker exec ollama ollama pull llama3.2:3b\n"
            "   - Configure in .env: OLLAMA_ENDPOINT=http://ollama:11434\n\n"
            "3. 🚀 vLLM (For GPU acceleration)\n"
            "   - Set USE_VLLM=true in .env\n"
            "   - Requires NVIDIA GPU with CUDA\n\n"
            "4. 🔧 llama.cpp (DEPRECATED - use Ollama instead)\n"
            "   - Configure LLAMA_CPP_ENDPOINT in .env\n\n"
            "💡 Note: Some features will use fallback analysis when LLM is unavailable."
        )
        logger.error(error_msg)
        raise Exception(error_msg)

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
        # Build context from chunks with quality indicators
        context_text = "\n\n".join([
            f"Source {i+1} - {chunk.get('filename', 'unknown')} (Relevance: {chunk.get('similarity', 0):.0%}):\n{chunk['content']}"
            for i, chunk in enumerate(context_chunks)
        ])

        # Build improved prompt
        system_prompt = """You are a helpful AI assistant with access to relevant documents and information.
Your task is to answer questions based ONLY on the provided context.

IMPORTANT RULES:
1. Use ONLY information from the provided sources to answer the question
2. Always cite your sources using [Source N] notation when using information
3. If the sources don't contain enough information to answer the question completely, say so clearly
4. Do not make up information or use knowledge outside the provided context
5. Focus on the most relevant sources (those with higher relevance scores)
6. Be concise and accurate"""

        user_prompt = f"""Context (sources with relevance scores):
{context_text}

Question: {query}

Based on the context above, provide a clear and accurate answer. Cite your sources using [Source N] format. If the sources don't fully answer the question, acknowledge this limitation."""

        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        if conversation_history:
            messages.extend(conversation_history[-6:])  # Last 3 turns

        messages.append({"role": "user", "content": user_prompt})

        # Convert to single prompt for vLLM/llama.cpp
        prompt = "\n\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages])
        prompt += "\n\nASSISTANT:"

        return await self.generate(
            prompt=prompt,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            model_id=model_id
        )


# Singleton instance
llm_service = LLMService()
