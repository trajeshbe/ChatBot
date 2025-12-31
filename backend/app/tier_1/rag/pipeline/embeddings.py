"""
Embeddings Module for RAG Pipeline

Handles query and document embedding generation with caching.
"""

from typing import List
import logging
from sentence_transformers import SentenceTransformer
import redis.asyncio as redis
import hashlib
import json
import numpy as np

from .config import get_rag_settings

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Manages embedding generation with caching"""

    def __init__(self):
        self.model = None
        self.redis_client = None
        self._initialized = False
        self.settings = get_rag_settings()

    async def initialize(self):
        """Initialize embedding model and Redis connection"""
        if self._initialized:
            return

        try:
            logger.info(f"Loading embedding model: {self.settings.EMBEDDING_MODEL_NAME}")
            self.model = SentenceTransformer(self.settings.EMBEDDING_MODEL_NAME)
            logger.info(f"Embedding model loaded (dimension: {self.settings.EMBEDDING_DIMENSION})")

            # Initialize Redis for embedding caching
            if self.settings.ENABLE_SEMANTIC_CACHE:
                from app.tier_1.infrastructure.config import settings as app_settings
                self.redis_client = await redis.from_url(
                    app_settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=False
                )
                logger.info("Redis embedding cache connected")

            self._initialized = True

        except Exception as e:
            logger.error(f"Error initializing embedding manager: {e}")
            raise

    async def close(self):
        """Close connections"""
        if self.redis_client:
            await self.redis_client.close()

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        return f"emb:v1:{text_hash}"

    async def embed_query(
        self,
        query: str,
        normalize: bool = True
    ) -> List[float]:
        """
        Generate embedding for a query with caching.

        Args:
            query: Query text to embed
            normalize: Whether to normalize the query text before embedding

        Returns:
            List of floats representing the embedding vector
        """
        if not self._initialized:
            await self.initialize()

        # Normalize query if requested
        if normalize:
            query = self._normalize_text(query)

        # Try cache first
        if self.redis_client:
            cache_key = self._get_cache_key(query)
            try:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    logger.debug("Embedding cache hit")
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Error reading from embedding cache: {e}")

        # Generate embedding
        try:
            embedding = self.model.encode(
                query,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            embedding_list = embedding.tolist()

            # Cache the result
            if self.redis_client:
                try:
                    await self.redis_client.setex(
                        cache_key,
                        self.settings.CACHE_TTL_SECONDS,
                        json.dumps(embedding_list)
                    )
                except Exception as e:
                    logger.warning(f"Error writing to embedding cache: {e}")

            return embedding_list

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def embed_documents(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple documents.

        Args:
            texts: List of document texts
            batch_size: Batch size for encoding

        Returns:
            List of embedding vectors
        """
        if not self._initialized:
            await self.initialize()

        try:
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 10,
                batch_size=batch_size
            )
            return embeddings.tolist()

        except Exception as e:
            logger.error(f"Error generating document embeddings: {e}")
            raise

    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        Normalize query text for better embedding quality.

        - Trim whitespace
        - Remove extra newlines
        - Normalize spacing
        """
        # Remove extra whitespace and newlines
        text = " ".join(text.split())
        return text.strip()

    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        a_np = np.array(a)
        b_np = np.array(b)
        dot_product = np.dot(a_np, b_np)
        norm_a = np.linalg.norm(a_np)
        norm_b = np.linalg.norm(b_np)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(dot_product / (norm_a * norm_b))


# Global singleton instance
_embedding_manager = None


async def get_embedding_manager() -> EmbeddingManager:
    """Get or create global embedding manager instance"""
    global _embedding_manager
    if _embedding_manager is None:
        _embedding_manager = EmbeddingManager()
        await _embedding_manager.initialize()
    return _embedding_manager


# Convenience function for the pipeline
async def embed_query(
    query: str,
    model_name: str = None,  # For compatibility with reference skeleton
    normalize: bool = True
) -> List[float]:
    """
    Generate embedding for a query.

    Args:
        query: Query text
        model_name: Model name (ignored, uses configured model)
        normalize: Whether to normalize text

    Returns:
        Embedding vector as list of floats
    """
    manager = await get_embedding_manager()
    return await manager.embed_query(query, normalize=normalize)
