"""
Semantic Cache Module

Uses Redis with Vector Similarity Search (VSS) to cache RAG query results.
Caches based on semantic similarity of queries rather than exact matches.
"""

from typing import List, Dict, Any, Optional
import logging
import json
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime
import redis.asyncio as redis
import numpy as np

from .config import get_rag_settings

logger = logging.getLogger(__name__)


def generate_config_hash(
    semantic_weight: float = 0.8,
    keyword_weight: float = 0.2,
    top_k: int = 5,
    similarity_threshold: float = 0.5,
    chunk_size: int = 800,
    chunk_overlap: int = 150
) -> str:
    """
    Generate deterministic hash from RAG configuration parameters.

    This hash is used to version cache keys - when any of these parameters
    change, the cache will be invalidated.

    Args:
        semantic_weight: Hybrid search semantic weight
        keyword_weight: Hybrid search keyword weight
        top_k: Number of results to retrieve
        similarity_threshold: Minimum similarity threshold
        chunk_size: Text chunk size
        chunk_overlap: Chunk overlap size

    Returns:
        MD5 hash of the configuration (8 characters)
    """
    config_dict = {
        "semantic_weight": round(semantic_weight, 2),
        "keyword_weight": round(keyword_weight, 2),
        "top_k": top_k,
        "similarity_threshold": round(similarity_threshold, 2),
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap
    }

    # Create deterministic JSON string (sorted keys)
    config_str = json.dumps(config_dict, sort_keys=True)
    config_hash = hashlib.md5(config_str.encode()).hexdigest()[:8]

    logger.debug(f"Generated config hash: {config_hash} for config: {config_dict}")
    return config_hash


@dataclass
class CachedAnswer:
    """Cached answer representation"""
    query: str
    normalized_query: str
    answer: str
    citations: List[Dict[str, Any]]
    embedding: List[float]
    tenant_id: Optional[str]
    similarity: float  # Similarity score when retrieved
    cached_at: str
    ttl_seconds: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class SemanticCache:
    """Semantic cache using Redis"""

    def __init__(self):
        self.settings = get_rag_settings()
        self.redis_client = None
        self._initialized = False

    async def initialize(self):
        """Initialize Redis connection"""
        if self._initialized:
            return

        try:
            from app.core.config import settings as app_settings
            self.redis_client = await redis.from_url(
                app_settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True  # Auto decode to strings
            )
            logger.info("Semantic cache Redis connected")
            self._initialized = True

        except Exception as e:
            logger.error(f"Error initializing semantic cache: {e}")
            raise

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()

    def _get_cache_key(
        self,
        embedding: List[float],
        tenant_id: Optional[str] = None,
        model_name: Optional[str] = None,
        config_hash: Optional[str] = None
    ) -> str:
        """
        Generate versioned cache key from embedding and configuration.

        Uses hash of embedding + model version + config for deterministic key generation.

        Args:
            embedding: Query embedding vector
            tenant_id: Optional tenant ID
            model_name: Embedding model name (e.g., 'all-MiniLM-L6-v2')
            config_hash: Hash of RAG configuration affecting results

        Returns:
            Versioned cache key string
        """
        # Create a deterministic hash from embedding
        embedding_bytes = json.dumps(embedding).encode()
        embedding_hash = hashlib.sha256(embedding_bytes).hexdigest()[:16]

        # 🆕 Add model version to cache key (default if not provided)
        model_version = model_name or "all-MiniLM-L6-v2"
        model_hash = hashlib.md5(model_version.encode()).hexdigest()[:8]

        # 🆕 Add config hash to cache key (default if not provided)
        config_version = config_hash or "default"

        if tenant_id:
            return f"rag_cache:v2:tenant:{tenant_id}:{model_hash}:{config_version}:{embedding_hash}"
        return f"rag_cache:v2:global:{model_hash}:{config_version}:{embedding_hash}"

    async def get_cached_answer(
        self,
        embedding: List[float],
        tenant_id: Optional[str] = None,
        similarity_threshold: Optional[float] = None,
        model_name: Optional[str] = None,
        config_hash: Optional[str] = None
    ) -> Optional[CachedAnswer]:
        """
        Get cached answer if a similar query exists.

        Args:
            embedding: Query embedding vector
            tenant_id: Optional tenant ID for isolation
            similarity_threshold: Minimum similarity for cache hit
            model_name: Embedding model name for versioning
            config_hash: RAG configuration hash for versioning

        Returns:
            CachedAnswer if found, None otherwise
        """
        if not self.settings.ENABLE_SEMANTIC_CACHE:
            return None

        if not self._initialized:
            await self.initialize()

        similarity_threshold = similarity_threshold or self.settings.CACHE_SIMILARITY_THRESHOLD

        try:
            # 🆕 Get cache keys for the specific model + config version
            model_version = model_name or "all-MiniLM-L6-v2"
            model_hash = hashlib.md5(model_version.encode()).hexdigest()[:8]
            config_version = config_hash or "default"

            # Get all cache keys for the tenant with matching model + config
            if tenant_id:
                pattern = f"rag_cache:v2:tenant:{tenant_id}:{model_hash}:{config_version}:*"
            else:
                pattern = f"rag_cache:v2:global:{model_hash}:{config_version}:*"

            keys = await self.redis_client.keys(pattern)

            if not keys:
                logger.debug("No cached entries found")
                return None

            # Check each cached entry for similarity
            best_match = None
            best_similarity = 0.0

            for key in keys:
                try:
                    cached_data = await self.redis_client.get(key)
                    if not cached_data:
                        continue

                    cached = json.loads(cached_data)
                    cached_embedding = cached.get("embedding")

                    if not cached_embedding:
                        continue

                    # Calculate cosine similarity
                    similarity = self._cosine_similarity(embedding, cached_embedding)

                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = cached

                except Exception as e:
                    logger.warning(f"Error processing cache key {key}: {e}")
                    continue

            # Check if we have a good enough match
            if best_match and best_similarity >= similarity_threshold:
                logger.info(f"Cache hit! Similarity: {best_similarity:.4f}")

                return CachedAnswer(
                    query=best_match.get("query", ""),
                    normalized_query=best_match.get("normalized_query", ""),
                    answer=best_match.get("answer", ""),
                    citations=best_match.get("citations", []),
                    embedding=best_match.get("embedding", []),
                    tenant_id=best_match.get("tenant_id"),
                    similarity=best_similarity,
                    cached_at=best_match.get("cached_at", ""),
                    ttl_seconds=best_match.get("ttl_seconds", 0)
                )

            logger.debug(f"No cache hit (best similarity: {best_similarity:.4f}, threshold: {similarity_threshold:.4f})")
            return None

        except Exception as e:
            logger.warning(f"Error retrieving from semantic cache: {e}")
            return None

    async def store_answer(
        self,
        embedding: List[float],
        tenant_id: Optional[str],
        normalized_query: str,
        answer: str,
        citations: List[Dict[str, Any]],
        ttl_seconds: Optional[int] = None,
        original_query: Optional[str] = None,
        model_name: Optional[str] = None,
        config_hash: Optional[str] = None
    ):
        """
        Store answer in semantic cache with versioning.

        Args:
            embedding: Query embedding vector
            tenant_id: Optional tenant ID
            normalized_query: Normalized query text
            answer: Generated answer
            citations: Source citations
            ttl_seconds: Time to live in seconds
            original_query: Original query before normalization
            model_name: Embedding model name for versioning
            config_hash: RAG configuration hash for versioning
        """
        if not self.settings.ENABLE_SEMANTIC_CACHE:
            return

        if not self._initialized:
            await self.initialize()

        ttl_seconds = ttl_seconds or self.settings.CACHE_TTL_SECONDS

        try:
            cache_key = self._get_cache_key(embedding, tenant_id, model_name, config_hash)

            cache_data = {
                "query": original_query or normalized_query,
                "normalized_query": normalized_query,
                "answer": answer,
                "citations": citations,
                "embedding": embedding,
                "tenant_id": tenant_id,
                "cached_at": datetime.utcnow().isoformat(),
                "ttl_seconds": ttl_seconds
            }

            # Store with TTL
            await self.redis_client.setex(
                cache_key,
                ttl_seconds,
                json.dumps(cache_data)
            )

            logger.info(f"Stored answer in semantic cache (TTL: {ttl_seconds}s)")

        except Exception as e:
            logger.warning(f"Error storing to semantic cache: {e}")
            # Don't fail the request if caching fails

    async def invalidate_tenant_cache(self, tenant_id: str):
        """Invalidate all cache entries for a tenant"""
        if not self._initialized:
            await self.initialize()

        try:
            pattern = f"rag_cache:tenant:{tenant_id}:*"
            keys = await self.redis_client.keys(pattern)

            if keys:
                await self.redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries for tenant {tenant_id}")

        except Exception as e:
            logger.warning(f"Error invalidating tenant cache: {e}")

    async def clear_all_cache(self):
        """Clear all semantic cache entries (use with caution!)"""
        if not self._initialized:
            await self.initialize()

        try:
            pattern = "rag_cache:*"
            keys = await self.redis_client.keys(pattern)

            if keys:
                await self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries")

        except Exception as e:
            logger.warning(f"Error clearing cache: {e}")

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        a_np = np.array(a)
        b_np = np.array(b)

        dot_product = np.dot(a_np, b_np)
        norm_a = np.linalg.norm(a_np)
        norm_b = np.linalg.norm(b_np)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(dot_product / (norm_a * norm_b))


# Global singleton
_semantic_cache = None


async def get_semantic_cache() -> SemanticCache:
    """Get or create global semantic cache instance"""
    global _semantic_cache
    if _semantic_cache is None:
        _semantic_cache = SemanticCache()
        await _semantic_cache.initialize()
    return _semantic_cache


# Convenience functions for the pipeline
async def get_cached_answer(
    embedding: List[float],
    tenant_id: Optional[str] = None,
    similarity_threshold: Optional[float] = None,
    model_name: Optional[str] = None,
    config_hash: Optional[str] = None
) -> Optional[CachedAnswer]:
    """
    Get cached answer for a query embedding with versioning.

    Args:
        embedding: Query embedding vector
        tenant_id: Optional tenant ID
        similarity_threshold: Minimum similarity for cache hit
        model_name: Embedding model name for versioning
        config_hash: RAG configuration hash for versioning

    Returns:
        CachedAnswer if found, None otherwise
    """
    cache = await get_semantic_cache()
    return await cache.get_cached_answer(
        embedding=embedding,
        tenant_id=tenant_id,
        similarity_threshold=similarity_threshold,
        model_name=model_name,
        config_hash=config_hash
    )


async def store_answer(
    embedding: List[float],
    tenant_id: Optional[str],
    normalized_query: str,
    answer: str,
    citations: List[Dict[str, Any]],
    ttl_seconds: Optional[int] = None,
    model_name: Optional[str] = None,
    config_hash: Optional[str] = None
):
    """
    Store answer in semantic cache with versioning.

    Args:
        embedding: Query embedding vector
        tenant_id: Optional tenant ID
        normalized_query: Normalized query text
        answer: Generated answer
        citations: Source citations
        ttl_seconds: Time to live in seconds
        model_name: Embedding model name for versioning
        config_hash: RAG configuration hash for versioning
    """
    cache = await get_semantic_cache()
    await cache.store_answer(
        embedding=embedding,
        tenant_id=tenant_id,
        normalized_query=normalized_query,
        answer=answer,
        citations=citations,
        ttl_seconds=ttl_seconds,
        model_name=model_name,
        config_hash=config_hash
    )
