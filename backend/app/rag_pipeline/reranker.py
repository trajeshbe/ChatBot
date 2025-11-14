"""
Reranker Module

Uses Ollama LLM to rerank retrieved chunks for better relevance.
Implements batch processing for efficiency.
"""

from typing import List, Dict, Any
import logging
import httpx
import asyncio
from dataclasses import dataclass

from .config import get_rag_settings

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Chunk representation for reranking"""
    id: Any
    doc_id: Any
    text: str
    metadata: Dict[str, Any]
    semantic_score: float
    lexical_score: float
    final_score: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Chunk":
        """Create Chunk from dictionary"""
        return cls(
            id=data.get("id"),
            doc_id=data.get("doc_id") or data.get("document_id"),
            text=data.get("text") or data.get("content"),
            metadata=data.get("metadata", {}),
            semantic_score=data.get("semantic_score", 0.0),
            lexical_score=data.get("lexical_score", 0.0),
            final_score=data.get("final_score") or data.get("similarity", 0.0)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "doc_id": self.doc_id,
            "document_id": self.doc_id,
            "text": self.text,
            "content": self.text,
            "metadata": self.metadata,
            "semantic_score": self.semantic_score,
            "lexical_score": self.lexical_score,
            "final_score": self.final_score,
            "similarity": self.final_score,
            "filename": self.metadata.get("filename", "Unknown"),
            "source": self.metadata.get("filename", "Unknown"),
            "source_type": self.metadata.get("source_type", "unknown"),
            "source_url": self.metadata.get("source_url")
        }


class OllamaReranker:
    """Reranks chunks using Ollama LLM"""

    def __init__(self):
        self.settings = get_rag_settings()
        self.client = None

    async def initialize(self):
        """Initialize HTTP client"""
        if self.client is None:
            from app.core.config import settings as app_settings
            self.client = httpx.AsyncClient(
                base_url=app_settings.OLLAMA_ENDPOINT,
                timeout=30.0
            )

    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()

    async def rerank_with_ollama(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        model_name: str = None,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Rerank candidates using Ollama LLM.

        Uses the LLM to score relevance of each chunk to the query.

        Args:
            query: User query
            candidates: List of candidate chunks
            model_name: Ollama model name (default from settings)
            top_k: Number of top results to return (default from settings)

        Returns:
            Reranked list of chunks
        """
        if not self.settings.ENABLE_RERANKER:
            logger.info("Reranker disabled, returning original candidates")
            return candidates[:top_k or self.settings.RERANK_TOP_K]

        if not candidates:
            return []

        await self.initialize()

        model_name = model_name or self.settings.RERANK_MODEL_NAME
        top_k = top_k or self.settings.RERANK_TOP_K

        logger.info(f"Reranking {len(candidates)} candidates with Ollama ({model_name})")

        try:
            # Convert to Chunk objects
            chunks = [Chunk.from_dict(c) for c in candidates]

            # Rerank in batches for efficiency
            batch_size = self.settings.RERANK_BATCH_SIZE
            reranked_chunks = []

            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                batch_results = await self._rerank_batch(query, batch, model_name)
                reranked_chunks.extend(batch_results)

            # Sort by rerank score
            reranked_chunks.sort(key=lambda x: x.final_score, reverse=True)

            # Take top-k
            top_chunks = reranked_chunks[:top_k]

            if self.settings.LOG_RERANK_SCORES and top_chunks:
                logger.info(
                    f"Reranking complete. Top score: {top_chunks[0].final_score:.3f}, "
                    f"Bottom score: {top_chunks[-1].final_score:.3f}"
                )

            # Convert back to dictionaries
            return [chunk.to_dict() for chunk in top_chunks]

        except Exception as e:
            logger.warning(f"Error in reranking: {e}. Returning original candidates.")
            # Fallback to original ranking
            return candidates[:top_k]

    async def _rerank_batch(
        self,
        query: str,
        chunks: List[Chunk],
        model_name: str
    ) -> List[Chunk]:
        """
        Rerank a batch of chunks.

        Uses a simple prompt asking the LLM to score relevance 0-10.
        """
        tasks = [
            self._score_chunk(query, chunk, model_name)
            for chunk in chunks
        ]
        scored_chunks = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out errors
        valid_chunks = []
        for chunk, result in zip(chunks, scored_chunks):
            if isinstance(result, Exception):
                logger.warning(f"Error scoring chunk: {result}")
                # Keep original score
                valid_chunks.append(chunk)
            else:
                valid_chunks.append(result)

        return valid_chunks

    async def _score_chunk(
        self,
        query: str,
        chunk: Chunk,
        model_name: str
    ) -> Chunk:
        """
        Score a single chunk's relevance to the query.

        Returns the chunk with an updated final_score based on LLM assessment.
        """
        # Truncate text if too long (to avoid token limits)
        text_preview = chunk.text[:500] if len(chunk.text) > 500 else chunk.text

        prompt = f"""On a scale of 0-10, how relevant is the following text to answering the query?

Query: {query}

Text: {text_preview}

Respond with ONLY a number between 0 and 10, where:
- 0 = completely irrelevant
- 5 = somewhat relevant
- 10 = highly relevant and directly answers the query

Score:"""

        try:
            response = await self.client.post(
                "/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistent scoring
                        "num_predict": 10    # We only need a short response
                    }
                }
            )
            response.raise_for_status()

            result = response.json()
            score_text = result.get("response", "").strip()

            # Extract numeric score
            score = self._extract_score(score_text)

            # Normalize to 0-1 range and blend with original score
            normalized_score = score / 10.0

            # Weighted combination: 70% LLM rerank, 30% original
            chunk.final_score = 0.7 * normalized_score + 0.3 * chunk.final_score

            return chunk

        except Exception as e:
            logger.warning(f"Error scoring chunk with LLM: {e}")
            # Return chunk with original score
            return chunk

    @staticmethod
    def _extract_score(text: str) -> float:
        """
        Extract numeric score from LLM response.

        Handles various formats like "7", "Score: 7", "7/10", etc.
        """
        import re

        # Remove common prefixes
        text = text.replace("Score:", "").replace("score:", "")
        text = text.strip()

        # Try to find a number
        match = re.search(r'(\d+(?:\.\d+)?)', text)
        if match:
            score = float(match.group(1))
            # Clamp to 0-10 range
            return max(0.0, min(10.0, score))

        # Default to 5 if we can't parse
        logger.warning(f"Could not parse score from: {text}")
        return 5.0


# Global singleton
_reranker = None


async def get_reranker() -> OllamaReranker:
    """Get or create global reranker instance"""
    global _reranker
    if _reranker is None:
        _reranker = OllamaReranker()
        await _reranker.initialize()
    return _reranker


# Convenience function for the pipeline
async def rerank_with_ollama(
    query: str,
    candidates: List[Any],  # Can be Dict or Chunk
    model_name: str = None,
    top_k: int = None
) -> List[Dict[str, Any]]:
    """
    Rerank candidates using Ollama.

    Args:
        query: User query
        candidates: List of candidate chunks (dict or Chunk objects)
        model_name: Ollama model name
        top_k: Number of top results to return

    Returns:
        Reranked list of chunks as dictionaries
    """
    reranker = await get_reranker()

    # Convert to dicts if needed
    if candidates and isinstance(candidates[0], Chunk):
        candidates = [c.to_dict() for c in candidates]

    return await reranker.rerank_with_ollama(
        query=query,
        candidates=candidates,
        model_name=model_name,
        top_k=top_k
    )
