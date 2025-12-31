"""
LLM Module for RAG Pipeline

Handles:
1. Grounded answer generation with context
2. Self-critique (Self-RAG style)
3. Answer refinement based on critique
4. Multi-provider support (OpenAI, Anthropic Claude, Ollama)
"""

from typing import List, Dict, Any, Tuple, Optional
import logging
import httpx
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from .config import get_rag_settings, get_optimal_chunk_count, is_large_context_model
from .reranker import Chunk

logger = logging.getLogger(__name__)


class LLMClient:
    """Multi-provider LLM client with fallback support"""

    def __init__(self):
        self.settings = get_rag_settings()
        self.openai_client = None
        self.anthropic_client = None
        self.ollama_client = None
        self._initialized = False

    async def initialize(self):
        """Initialize LLM clients"""
        if self._initialized:
            return

        try:
            # Initialize OpenAI
            from app.tier_1.infrastructure.config import settings as app_settings
            if app_settings.OPENAI_API_KEY:
                self.openai_client = AsyncOpenAI(api_key=app_settings.OPENAI_API_KEY)
                logger.info("OpenAI client initialized")

            # Initialize Anthropic
            if app_settings.ANTHROPIC_API_KEY:
                self.anthropic_client = AsyncAnthropic(api_key=app_settings.ANTHROPIC_API_KEY)
                logger.info("Anthropic client initialized")

            # Initialize Ollama
            self.ollama_client = httpx.AsyncClient(
                base_url=app_settings.OLLAMA_ENDPOINT,
                timeout=60.0
            )
            logger.info("Ollama client initialized")

            self._initialized = True

        except Exception as e:
            logger.error(f"Error initializing LLM clients: {e}")
            raise

    async def close(self):
        """Close HTTP clients"""
        if self.ollama_client:
            await self.ollama_client.aclose()

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model_name: str,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> Tuple[str, int]:
        """
        Generate response using specified model with fallback.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model_name: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Tuple of (generated_text, tokens_used)
        """
        if not self._initialized:
            await self.initialize()

        # Determine provider from model name
        if model_name.startswith("gpt-"):
            return await self._call_openai(messages, model_name, temperature, max_tokens)
        elif model_name.startswith("claude-"):
            return await self._call_anthropic(messages, model_name, temperature, max_tokens)
        else:
            # Assume Ollama for other models
            return await self._call_ollama(messages, model_name, temperature, max_tokens)

    async def _call_openai(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Tuple[str, int]:
        """Call OpenAI API"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")

        try:
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            content = response.choices[0].message.content
            tokens = response.usage.total_tokens

            return content, tokens

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            # Fallback to Ollama
            logger.info("Falling back to Ollama")
            return await self._call_ollama(
                messages,
                self.settings.GENERATION_MODEL_OLLAMA,
                temperature,
                max_tokens
            )

    async def _call_anthropic(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Tuple[str, int]:
        """Call Anthropic Claude API"""
        if not self.anthropic_client:
            raise ValueError("Anthropic client not initialized")

        try:
            # Extract system message if present
            system_msg = None
            chat_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    chat_messages.append(msg)

            # Call Anthropic API
            kwargs = {
                "model": model,
                "messages": chat_messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            if system_msg:
                kwargs["system"] = system_msg

            response = await self.anthropic_client.messages.create(**kwargs)

            content = response.content[0].text
            tokens = response.usage.input_tokens + response.usage.output_tokens

            return content, tokens

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            # Fallback to Ollama
            logger.info("Falling back to Ollama")
            return await self._call_ollama(
                messages,
                self.settings.GENERATION_MODEL_OLLAMA,
                temperature,
                max_tokens
            )

    async def _call_ollama(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Tuple[str, int]:
        """Call Ollama API"""
        try:
            # Strip "ollama/" prefix if present
            ollama_model = model.replace("ollama/", "")

            logger.info(f"🔧 Calling Ollama with model: {ollama_model}")
            logger.info(f"🔧 Messages count: {len(messages)}")
            logger.info(f"🔧 Ollama client base_url: {self.ollama_client.base_url}")

            response = await self.ollama_client.post(
                "/api/chat",
                json={
                    "model": ollama_model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                }
            )

            logger.info(f"🔧 Response status: {response.status_code}")
            response.raise_for_status()

            result = response.json()
            content = result["message"]["content"]

            # Estimate tokens (Ollama doesn't always return token count)
            tokens = result.get("eval_count", 0) + result.get("prompt_eval_count", 0)
            if tokens == 0:
                # Rough estimate: ~4 chars per token
                tokens = len(content) // 4

            return content, tokens

        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise


# Global client instance
_llm_client = None


async def get_llm_client() -> LLMClient:
    """Get or create global LLM client"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
        await _llm_client.initialize()
    return _llm_client


async def generate_grounded_answer(
    query: str,
    chunks: List[Any],  # List of Chunk objects or dicts
    model_name: str,
    temperature: float = 0.7,
    max_tokens: int = 1024
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Generate grounded answer from retrieved chunks.

    Args:
        query: User query
        chunks: Retrieved chunks (Chunk objects or dicts)
        model_name: Model to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens

    Returns:
        Tuple of (answer, citations)
    """
    client = await get_llm_client()

    # Adapt chunk count based on model context window
    optimal_chunk_count = get_optimal_chunk_count(model_name)
    chunks = chunks[:optimal_chunk_count]

    # Build context from chunks
    context_parts = []
    citations = []

    for i, chunk in enumerate(chunks):
        # Handle both dict and Chunk object
        if isinstance(chunk, dict):
            text = chunk.get("text") or chunk.get("content", "")
            filename = chunk.get("filename", "Unknown")
            source_url = chunk.get("source_url")
        else:
            text = chunk.text
            filename = chunk.metadata.get("filename", "Unknown")
            source_url = chunk.metadata.get("source_url")

        context_parts.append(f"[Source {i+1}: {filename}]\n{text}\n")

        citations.append({
            "source_number": i + 1,
            "filename": filename,
            "source_url": source_url,
            "excerpt": text[:200] + "..." if len(text) > 200 else text
        })

    context_text = "\n".join(context_parts)

    # Build prompt - optimized for large context models
    if is_large_context_model(model_name):
        # For large models, provide extensive context
        system_prompt = """You are a highly accurate AI assistant with access to relevant documents.
Your task is to answer questions based ONLY on the provided context.

IMPORTANT RULES:
1. Ground your answer in the provided sources
2. Cite sources using [Source N] notation
3. If the context doesn't fully answer the question, acknowledge it
4. Be comprehensive and detailed in your response
5. Maintain accuracy - do not make up information"""
    else:
        # For smaller models, be more concise
        system_prompt = """You are an AI assistant. Answer questions based ONLY on the provided context.
Cite sources using [Source N] notation. Be accurate and concise."""

    user_prompt = f"""Context:
{context_text}

Question: {query}

Provide a detailed, well-structured answer based on the context above. Cite your sources."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    # Generate answer
    answer, tokens = await client.generate(
        messages=messages,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens
    )

    logger.info(f"Generated answer ({tokens} tokens, {len(chunks)} chunks)")

    return answer, citations


async def critique_answer(
    query: str,
    chunks: List[Any],
    answer: str,
    model_name: str
) -> Dict[str, Any]:
    """
    Critique the generated answer for groundedness and completeness.

    Implements Self-RAG style critique.

    Args:
        query: Original query
        chunks: Retrieved chunks
        answer: Generated answer
        model_name: Model to use for critique

    Returns:
        Dict with critique results
    """
    client = await get_llm_client()

    # Build concise context summary
    context_summary = []
    for i, chunk in enumerate(chunks[:5]):  # Use top 5 for critique
        if isinstance(chunk, dict):
            text = chunk.get("text") or chunk.get("content", "")
        else:
            text = chunk.text

        context_summary.append(f"Source {i+1}: {text[:150]}...")

    context_text = "\n".join(context_summary)

    critique_prompt = f"""Evaluate the following answer for groundedness and completeness.

Question: {query}

Available Context:
{context_text}

Generated Answer:
{answer}

Evaluate the answer on:
1. GROUNDEDNESS: Is the answer based on the provided context? (Yes/No)
2. COMPLETENESS: Does the answer fully address the question? (Yes/No)
3. ISSUES: List any specific problems (or "None" if satisfactory)

Respond in this EXACT format:
GROUNDED: [Yes/No]
COMPLETE: [Yes/No]
ISSUES: [List issues or "None"]"""

    messages = [
        {"role": "system", "content": "You are a critical evaluator assessing answer quality."},
        {"role": "user", "content": critique_prompt}
    ]

    critique_text, _ = await client.generate(
        messages=messages,
        model_name=model_name,
        temperature=0.1,  # Low temperature for consistent evaluation
        max_tokens=300
    )

    # Parse critique
    is_grounded = "yes" in critique_text.lower().split("grounded:")[1].split("\n")[0].lower()
    is_complete = "yes" in critique_text.lower().split("complete:")[1].split("\n")[0].lower()

    issues_line = critique_text.lower().split("issues:")[1].strip() if "issues:" in critique_text.lower() else ""
    issues = [] if "none" in issues_line else [issues_line]

    result = {
        "is_grounded": is_grounded,
        "is_complete": is_complete,
        "issues": issues,
        "raw_critique": critique_text
    }

    if get_rag_settings().LOG_CRITIQUE_DETAILS:
        logger.info(f"Critique: grounded={is_grounded}, complete={is_complete}, issues={len(issues)}")

    return result


async def refine_answer_with_critique(
    query: str,
    chunks: List[Any],
    initial_answer: str,
    critique: Any,  # CritiqueResult or dict
    model_name: str,
    temperature: float = 0.5,
    max_tokens: int = 1024
) -> Tuple[str, Optional[List[Dict[str, Any]]]]:
    """
    Refine answer based on critique feedback.

    Args:
        query: Original query
        chunks: Retrieved chunks
        initial_answer: Initial generated answer
        critique: Critique results
        model_name: Model to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens

    Returns:
        Tuple of (refined_answer, citations)
    """
    client = await get_llm_client()

    # Extract critique info
    if isinstance(critique, dict):
        issues = critique.get("issues", [])
        is_grounded = critique.get("is_grounded", True)
        is_complete = critique.get("is_complete", True)
    else:
        issues = critique.issues
        is_grounded = critique.is_grounded
        is_complete = critique.is_complete

    # Build context
    context_parts = []
    for i, chunk in enumerate(chunks[:get_optimal_chunk_count(model_name)]):
        if isinstance(chunk, dict):
            text = chunk.get("text") or chunk.get("content", "")
            filename = chunk.get("filename", "Unknown")
        else:
            text = chunk.text
            filename = chunk.metadata.get("filename", "Unknown")

        context_parts.append(f"[Source {i+1}: {filename}]\n{text}\n")

    context_text = "\n".join(context_parts)

    # Build refinement prompt
    refinement_issues = []
    if not is_grounded:
        refinement_issues.append("Ensure the answer is grounded in the provided context")
    if not is_complete:
        refinement_issues.append("Address all aspects of the question more completely")
    if issues:
        refinement_issues.extend(issues)

    issues_text = "\n".join(f"- {issue}" for issue in refinement_issues)

    refine_prompt = f"""Your previous answer needs improvement. Please refine it.

Question: {query}

Context:
{context_text}

Previous Answer:
{initial_answer}

Issues to Address:
{issues_text}

Provide an improved answer that addresses these issues. Ground your answer in the provided sources and cite them using [Source N] notation."""

    messages = [
        {"role": "system", "content": "You are an AI assistant improving a previous answer based on feedback."},
        {"role": "user", "content": refine_prompt}
    ]

    refined_answer, tokens = await client.generate(
        messages=messages,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens
    )

    logger.info(f"Refined answer ({tokens} tokens)")

    # Citations remain the same
    return refined_answer, None  # Caller should use original citations
