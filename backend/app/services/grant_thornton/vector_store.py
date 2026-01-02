"""
Grant Thornton Vector Store

In-memory vector cache with MD5-based indexing for Grant Thornton.
Uses cosine similarity search with MMR (Maximal Marginal Relevance) for diversity.

This avoids DB schema changes while maintaining Grant Thornton spec compliance.
For production, can migrate to PGVector column: financial_embedding VECTOR(1024)

Author: Claude Code
Date: 2026-01-01
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from collections import defaultdict
import time

logger = logging.getLogger(__name__)


class GrantThorntonVectorStore:
    """
    In-memory vector store for Grant Thornton financial documents.

    Uses MD5-based caching per Grant Thornton spec:
    - Key: MD5 hash of PDF
    - Value: List of chunks with 1024-dim embeddings

    Features:
    - Cosine similarity search
    - MMR (Maximal Marginal Relevance) for diversity
    - Fast retrieval (<100ms for cached documents)
    """

    def __init__(self):
        # Cache structure: {md5_hash: {"chunks": [...], "metadata": {...}}}
        self.cache: Dict[str, Dict[str, Any]] = {}

    def add_document(
        self,
        md5_hash: str,
        chunks: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add document chunks to vector store.

        Args:
            md5_hash: MD5 hash of the PDF (cache key)
            chunks: List of chunks with 'embedding' field (1024-dim)
            metadata: Optional document metadata
        """
        start_time = time.time()

        # Validate embeddings
        for i, chunk in enumerate(chunks):
            if 'embedding' not in chunk:
                logger.warning(f"Chunk {i} missing embedding, skipping")
                continue

            embedding = chunk['embedding']
            if not isinstance(embedding, list) or len(embedding) != 1024:
                logger.warning(f"Chunk {i} has invalid embedding dimension: {len(embedding)}")

        # Store in cache
        self.cache[md5_hash] = {
            "chunks": chunks,
            "metadata": metadata or {},
            "created_at": time.time()
        }

        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(
            f"✅ Added {len(chunks)} chunks for MD5 {md5_hash[:8]}... "
            f"({elapsed_ms:.0f}ms)"
        )

    def document_exists(self, md5_hash: str) -> bool:
        """Check if document is already cached"""
        return md5_hash in self.cache

    def get_document_info(self, md5_hash: str) -> Optional[Dict[str, Any]]:
        """Get metadata for cached document"""
        if md5_hash not in self.cache:
            return None

        cached = self.cache[md5_hash]
        return {
            "md5_hash": md5_hash,
            "chunk_count": len(cached["chunks"]),
            "metadata": cached["metadata"],
            "created_at": cached.get("created_at")
        }

    def similarity_search(
        self,
        md5_hash: str,
        query_embedding: List[float],
        top_k: int = 20,
        min_similarity: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks using cosine similarity.

        Args:
            md5_hash: MD5 hash of the document
            query_embedding: Query embedding (1024-dim)
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of chunks with similarity scores
        """
        if md5_hash not in self.cache:
            logger.warning(f"MD5 {md5_hash[:8]}... not in cache")
            return []

        start_time = time.time()

        chunks = self.cache[md5_hash]["chunks"]
        query_vec = np.array(query_embedding)

        # Calculate cosine similarities
        results = []
        for chunk in chunks:
            # Handle both dict and Document object formats
            if isinstance(chunk, dict):
                embedding = chunk.get('embedding')
                chunk_data = chunk
            else:
                # LangChain Document object
                embedding = getattr(chunk, 'embedding', None) or chunk.metadata.get('embedding')
                chunk_data = {
                    'content': chunk.page_content,
                    'metadata': chunk.metadata,
                    'embedding': embedding
                }

            if not embedding:
                continue

            chunk_vec = np.array(embedding)
            similarity = self._cosine_similarity(query_vec, chunk_vec)

            if similarity >= min_similarity:
                result = {
                    **chunk_data,  # Include all chunk fields
                    "similarity": float(similarity),
                    "score": float(similarity)  # Alias for compatibility
                }
                results.append(result)

        # Sort by similarity (descending)
        results.sort(key=lambda x: x['similarity'], reverse=True)

        # Take top-k
        results = results[:top_k]

        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(
            f"🔍 Similarity search: {len(results)} results in {elapsed_ms:.0f}ms "
            f"(avg similarity: {np.mean([r['similarity'] for r in results]):.3f})"
        )

        return results

    def mmr_search(
        self,
        md5_hash: str,
        query_embedding: List[float],
        top_k: int = 6,
        fetch_k: int = 20,
        lambda_mult: float = 0.5,
        min_similarity: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Maximal Marginal Relevance (MMR) search for diversity.

        MMR balances relevance (similarity to query) and diversity
        (dissimilarity to already selected chunks).

        Args:
            md5_hash: MD5 hash of the document
            query_embedding: Query embedding (1024-dim)
            top_k: Number of final results
            fetch_k: Number of candidates to fetch initially
            lambda_mult: Relevance vs diversity weight (0=pure diversity, 1=pure relevance)
            min_similarity: Minimum similarity threshold

        Returns:
            List of diverse chunks with similarity scores
        """
        # First, get initial candidates using similarity search
        candidates = self.similarity_search(
            md5_hash=md5_hash,
            query_embedding=query_embedding,
            top_k=fetch_k,
            min_similarity=min_similarity
        )

        if not candidates:
            return []

        if len(candidates) <= top_k:
            return candidates

        start_time = time.time()

        # Extract embeddings
        query_vec = np.array(query_embedding)
        candidate_vecs = np.array([c['embedding'] for c in candidates])

        # MMR algorithm
        selected_indices = []
        remaining_indices = list(range(len(candidates)))

        # Select first result (highest similarity)
        selected_indices.append(remaining_indices.pop(0))

        # Iteratively select diverse results
        while len(selected_indices) < top_k and remaining_indices:
            mmr_scores = []

            selected_vecs = candidate_vecs[selected_indices]

            for idx in remaining_indices:
                # Relevance: similarity to query
                relevance = self._cosine_similarity(query_vec, candidate_vecs[idx])

                # Diversity: max similarity to already selected chunks
                diversity_scores = [
                    self._cosine_similarity(candidate_vecs[idx], selected_vec)
                    for selected_vec in selected_vecs
                ]
                diversity = max(diversity_scores) if diversity_scores else 0

                # MMR score
                mmr = lambda_mult * relevance - (1 - lambda_mult) * diversity
                mmr_scores.append((idx, mmr))

            # Select chunk with highest MMR score
            best_idx, best_score = max(mmr_scores, key=lambda x: x[1])
            selected_indices.append(best_idx)
            remaining_indices.remove(best_idx)

        # Get selected chunks
        results = [candidates[i] for i in selected_indices]

        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(
            f"🎯 MMR search: {len(results)} diverse results in {elapsed_ms:.0f}ms "
            f"(lambda={lambda_mult:.2f})"
        )

        return results

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(np.dot(a, b) / (norm_a * norm_b))

    def clear_cache(self, md5_hash: Optional[str] = None):
        """
        Clear cache.

        Args:
            md5_hash: If provided, clear only this document. Otherwise clear all.
        """
        if md5_hash:
            if md5_hash in self.cache:
                del self.cache[md5_hash]
                logger.info(f"Cleared cache for MD5 {md5_hash[:8]}...")
        else:
            self.cache.clear()
            logger.info("Cleared all cache")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_chunks = sum(len(doc["chunks"]) for doc in self.cache.values())

        return {
            "document_count": len(self.cache),
            "total_chunks": total_chunks,
            "average_chunks_per_doc": total_chunks / len(self.cache) if self.cache else 0,
            "cache_keys": list(self.cache.keys())
        }


# Singleton instance
_vector_store = None


def get_vector_store() -> GrantThorntonVectorStore:
    """
    Get or create Grant Thornton vector store singleton.

    Returns:
        GrantThorntonVectorStore instance
    """
    global _vector_store

    if _vector_store is None:
        _vector_store = GrantThorntonVectorStore()
        logger.info("✅ Grant Thornton vector store initialized")

    return _vector_store
