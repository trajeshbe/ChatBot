import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Union
import logging
from app.tier_1.infrastructure.config import settings
import redis.asyncio as redis
import hashlib
import json
import time

# Tool usage tracking
try:
    from app.tier_1.platform_services.tool_usage_tracker import tool_tracker, ToolCategory
    from app.tier_1.infrastructure.database import AsyncSessionLocal
    TOOL_TRACKING_ENABLED = True
except ImportError:
    TOOL_TRACKING_ENABLED = False
    logging.warning("Tool usage tracking not available")

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

        start_time = time.time()
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=len(texts) > 10)
        result = embeddings.tolist()
        processing_time = (time.time() - start_time) * 1000

        # Track embedding generation
        if TOOL_TRACKING_ENABLED:
            try:
                async with AsyncSessionLocal() as track_db:
                    await tool_tracker.record_tool_usage(
                        category=ToolCategory.EMBEDDING,
                        tool_name=settings.EMBEDDING_MODEL.split('/')[-1],  # e.g., "all-MiniLM-L6-v2"
                        operation="generate_embeddings_batch",
                        db=track_db,
                        session_id=None,
                        success=True,
                        latency_ms=processing_time,
                        input_size=len(texts),
                        output_size=len(result),
                        metadata={
                            'model': settings.EMBEDDING_MODEL,
                            'dimension': settings.EMBEDDING_DIMENSION,
                            'num_texts': len(texts)
                        }
                    )
                    await track_db.commit()
            except Exception as track_err:
                logger.warning(f"Failed to track embedding generation: {track_err}")

        return result

    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        a_np = np.array(a)
        b_np = np.array(b)
        return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np)))


# Singleton instance
embedding_service = EmbeddingService()
