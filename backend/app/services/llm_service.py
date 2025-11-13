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
        self.vllm_client = httpx.AsyncClient(timeout=60.0)
        self.llama_cpp_client = httpx.AsyncClient(timeout=60.0)
        self._initialized = False

    async def initialize(self):
        """Initialize LLM clients"""
        if self._initialized:
            return

        if settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("OpenAI client initialized")

        self._initialized = True

    async def close(self):
        """Close HTTP clients"""
        await self.vllm_client.aclose()
        await self.llama_cpp_client.aclose()

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=4))
    async def _call_vllm(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> Dict:
        """Call vLLM service"""
        try:
            response = await self.vllm_client.post(
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
                "tokens": response.json().get("usage", {}).get("total_tokens", 0)
            }
        except Exception as e:
            logger.warning(f"vLLM call failed: {e}")
            raise

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=4))
    async def _call_llama_cpp(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> Dict:
        """Call llama.cpp service as CPU fallback"""
        try:
            response = await self.llama_cpp_client.post(
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
                "tokens": response.json().get("tokens_evaluated", 0)
            }
        except Exception as e:
            logger.warning(f"llama.cpp call failed: {e}")
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
                "tokens": response.usage.total_tokens
            }
        except Exception as e:
            logger.error(f"OpenAI call failed: {e}")
            raise

    async def generate(
        self,
        prompt: str,
        messages: Optional[List[Dict]] = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
        use_fallback: bool = True
    ) -> Dict:
        """
        Generate response with automatic fallback chain:
        vLLM -> llama.cpp -> OpenAI
        """
        start_time = time.time()

        # Try vLLM first if enabled
        if settings.USE_VLLM:
            try:
                result = await self._call_vllm(prompt, max_tokens, temperature)
                result["latency_ms"] = (time.time() - start_time) * 1000
                return result
            except Exception as e:
                logger.warning(f"vLLM failed, trying fallback: {e}")

        # Try llama.cpp CPU fallback
        if use_fallback:
            try:
                result = await self._call_llama_cpp(prompt, max_tokens, temperature)
                result["latency_ms"] = (time.time() - start_time) * 1000
                return result
            except Exception as e:
                logger.warning(f"llama.cpp failed, trying OpenAI: {e}")

        # Final fallback to OpenAI
        if self.openai_client and use_fallback:
            if not messages:
                messages = [{"role": "user", "content": prompt}]
            result = await self._call_openai(messages, max_tokens, temperature)
            result["latency_ms"] = (time.time() - start_time) * 1000
            return result

        raise Exception("All LLM backends failed")

    async def generate_with_context(
        self,
        query: str,
        context_chunks: List[Dict],
        conversation_history: Optional[List[Dict]] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
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

        # Convert to single prompt for vLLM/llama.cpp
        prompt = "\n\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages])
        prompt += "\n\nASSISTANT:"

        return await self.generate(
            prompt=prompt,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )


# Singleton instance
llm_service = LLMService()
