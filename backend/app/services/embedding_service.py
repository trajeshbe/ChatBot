import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Union
import logging
from app.core.config import settings
import redis.asyncio as redis
import hashlib
import json

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        self.model = None
        self.redis_client = None
        self._initialized = False

    async def initialize(self):
        """Initialize the embedding model and Redis connection"""
        if self._initialized:
            return

        try:
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Embedding model loaded successfully")

            # Initialize Redis for caching
            if settings.USE_SEMANTIC_CACHE:
                self.redis_client = await redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=False
                )
                logger.info("Redis cache connected")

            self._initialized = True
        except Exception as e:
            logger.error(f"Error initializing embedding service: {e}")
            raise

    async def close(self):
        """Close connections"""
        if self.redis_client:
            await self.redis_client.close()

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        return f"emb:{hashlib.md5(text.encode()).hexdigest()}"

    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text with caching"""
        if not self._initialized:
            await self.initialize()

        # Try cache first
        if self.redis_client:
            cache_key = self._get_cache_key(text)
            cached = await self.redis_client.get(cache_key)
            if cached:
                logger.debug("Embedding cache hit")
                return json.loads(cached)

        # Generate embedding
        embedding = self.model.encode(text, convert_to_numpy=True)
        embedding_list = embedding.tolist()

        # Cache the result
        if self.redis_client:
            await self.redis_client.setex(
                cache_key,
                3600,  # 1 hour TTL
                json.dumps(embedding_list)
            )

        return embedding_list

    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts"""
        if not self._initialized:
            await self.initialize()

        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=len(texts) > 10)
        return embeddings.tolist()

    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        a_np = np.array(a)
        b_np = np.array(b)
        return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np)))


# Singleton instance
embedding_service = EmbeddingService()
