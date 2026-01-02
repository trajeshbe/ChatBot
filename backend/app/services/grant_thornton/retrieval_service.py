"""
Grant Thornton Retrieval Service

Two-stage retrieval system for financial document search:
1. Initial Context: 3 financial statement queries → 6 chunks (2 per query)
2. Agentic Search: Dynamic search tool for agent to use during extraction

Leverages existing infrastructure:
- BAAI/bge-large-en-v1.5 embeddings (1024-dim)
- BAAI/bge-reranker-large cross-encoder (from existing reranker_service)
- In-memory vector cache with MD5 indexing (per GT spec)

Author: Claude Code
Date: 2026-01-01
"""

import logging
from typing import List, Dict, Any, Optional
import time

from .vector_store import get_vector_store, GrantThorntonVectorStore
from .embedding_service import get_grant_thornton_embeddings
from .config import load_config, load_prompts
from app.tier_1.embeddings.reranker_service import get_reranker

logger = logging.getLogger(__name__)


class GrantThorntonRetriever:
    """
    Two-stage retrieval for Grant Thornton financial analysis.

    Stage 1 (Initial Context):
    - 3 predefined financial statement queries
    - Retrieve 2 chunks per query (6 total)
    - Provides baseline context for extraction

    Stage 2 (Agentic Search):
    - LangGraph agent calls search_financial_details() tool
    - Dynamic queries based on datapoint being extracted
    - MMR search for diverse, relevant chunks
    """

    def __init__(self):
        self.config = load_config()
        self.prompts = load_prompts()

        # Get services
        self.vector_store: Optional[GrantThorntonVectorStore] = None
        self.embedding_service = None
        self.reranker = None

        self._initialized = False

    async def initialize(self):
        """Initialize retrieval components"""
        if self._initialized:
            return

        logger.info("Initializing Grant Thornton retriever...")

        # Initialize vector store
        self.vector_store = get_vector_store()

        # Initialize embedding service
        self.embedding_service = await get_grant_thornton_embeddings()

        # Initialize reranker (use existing "accurate" mode = BAAI/bge-reranker-large)
        self.reranker = get_reranker(model_name="accurate")

        logger.info(
            f"✅ Grant Thornton retriever ready\n"
            f"   - Vector store: In-memory MD5 cache\n"
            f"   - Embeddings: {self.config.embed_model_name} (1024-dim)\n"
            f"   - Reranker: {self.config.reranker_model_name}\n"
            f"   - Initial queries: {len(self.config.initial_context_queries)}"
        )

        self._initialized = True

    async def get_initial_context(
        self,
        md5_hash: str
    ) -> List[Dict[str, Any]]:
        """
        Stage 1: Get initial context using predefined financial queries.

        Args:
            md5_hash: MD5 hash of the PDF

        Returns:
            List of 6 chunks (2 per query) with context about financial statements
        """
        if not self._initialized:
            await self.initialize()

        start_time = time.time()

        # Use initial context queries from config
        queries = self.config.initial_context_queries
        logger.info(f"📋 Getting initial context with {len(queries)} queries")

        all_chunks = []

        for query in queries:
            # Get embedding for query
            query_embedding = await self.embedding_service.get_embedding(query)

            # Search vector store
            chunks = self.vector_store.similarity_search(
                md5_hash=md5_hash,
                query_embedding=query_embedding,
                top_k=self.config.retrieval_top_k,  # Get candidates (20)
                min_similarity=0.3
            )

            # Rerank using BAAI/bge-reranker-large
            if chunks and self.reranker.is_available():
                reranked = self.reranker.rerank(
                    query=query,
                    chunks=chunks,
                    top_k=2,  # Take top 2 per query
                    score_threshold=None
                )
                all_chunks.extend(reranked)
            else:
                # Fallback: take top 2 by similarity
                all_chunks.extend(chunks[:2])

        # Deduplicate (same chunk might appear in multiple queries)
        seen_ids = set()
        unique_chunks = []
        for chunk in all_chunks:
            chunk_id = chunk.get('page_content', '') + str(chunk.get('metadata', {}).get('page', ''))
            if chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                unique_chunks.append(chunk)

        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(
            f"✅ Initial context: {len(unique_chunks)} unique chunks in {elapsed_ms:.0f}ms"
        )

        return unique_chunks

    async def search_financial_details(
        self,
        md5_hash: str,
        query: str,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Stage 2: Dynamic search for specific financial datapoint.

        This function is exposed as a LangGraph agent tool.

        Args:
            md5_hash: MD5 hash of the PDF
            query: Natural language query for financial detail
            top_k: Number of results (default from config)

        Returns:
            List of relevant chunks with reranking scores
        """
        if not self._initialized:
            await self.initialize()

        top_k = top_k or self.config.rerank_top_n

        start_time = time.time()
        logger.info(f"🔍 Financial search: '{query}' (top_k={top_k})")

        # Get query embedding
        query_embedding = await self.embedding_service.get_embedding(query)

        # MMR search for diversity (avoid redundant chunks)
        chunks = self.vector_store.mmr_search(
            md5_hash=md5_hash,
            query_embedding=query_embedding,
            top_k=self.config.retrieval_top_k,  # Fetch candidates (20)
            fetch_k=self.config.retrieval_top_k,
            lambda_mult=0.7,  # Favor relevance over diversity
            min_similarity=0.25  # Lower threshold for financial details
        )

        # Rerank using BAAI/bge-reranker-large
        if chunks and self.reranker.is_available():
            reranked = self.reranker.rerank(
                query=query,
                chunks=chunks,
                top_k=top_k,
                score_threshold=None
            )

            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(
                f"✅ Found {len(reranked)} results in {elapsed_ms:.0f}ms "
                f"(avg rerank_score: {sum(c['rerank_score'] for c in reranked) / len(reranked):.3f})"
            )

            return reranked
        else:
            # Fallback: take top-k by similarity
            results = chunks[:top_k]

            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(
                f"✅ Found {len(results)} results in {elapsed_ms:.0f}ms "
                f"(avg similarity: {sum(c['similarity'] for c in results) / len(results):.3f})"
            )

            return results

    async def add_document_to_cache(
        self,
        md5_hash: str,
        chunks: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add parsed and embedded document to vector cache.

        Args:
            md5_hash: MD5 hash of the PDF
            chunks: List of chunks with 'embedding' field (1024-dim)
            metadata: Optional document metadata
        """
        if not self._initialized:
            await self.initialize()

        self.vector_store.add_document(
            md5_hash=md5_hash,
            chunks=chunks,
            metadata=metadata
        )

        logger.info(f"📦 Cached {len(chunks)} chunks for MD5 {md5_hash[:8]}...")

    def document_cached(self, md5_hash: str) -> bool:
        """
        Check if document is already cached.

        Args:
            md5_hash: MD5 hash of the PDF

        Returns:
            True if document exists in cache
        """
        if not self.vector_store:
            return False

        return self.vector_store.document_exists(md5_hash)

    async def get_document_info(self, md5_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get information about cached document.

        Args:
            md5_hash: MD5 hash of the PDF

        Returns:
            Document info dict or None if not cached
        """
        if not self.vector_store:
            return None

        return self.vector_store.get_document_info(md5_hash)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.vector_store:
            return {"error": "Vector store not initialized"}

        return self.vector_store.get_cache_stats()

    def clear_cache(self, md5_hash: Optional[str] = None):
        """
        Clear cache.

        Args:
            md5_hash: If provided, clear only this document. Otherwise clear all.
        """
        if self.vector_store:
            self.vector_store.clear_cache(md5_hash)


# Singleton instance
_retriever = None


async def get_retriever() -> GrantThorntonRetriever:
    """
    Get or create Grant Thornton retriever singleton.

    Returns:
        Initialized GrantThorntonRetriever
    """
    global _retriever

    if _retriever is None:
        _retriever = GrantThorntonRetriever()
        await _retriever.initialize()

    return _retriever


# Convenience functions for LangGraph agent

async def get_initial_context(md5_hash: str) -> List[Dict[str, Any]]:
    """
    Get initial financial statement context.

    Args:
        md5_hash: MD5 hash of the PDF

    Returns:
        List of initial context chunks (6 chunks from 3 queries)
    """
    retriever = await get_retriever()
    return await retriever.get_initial_context(md5_hash)


async def search_financial_details(
    md5_hash: str,
    query: str,
    top_k: int = 2
) -> List[Dict[str, Any]]:
    """
    Search for specific financial details (agent tool function).

    Args:
        md5_hash: MD5 hash of the PDF
        query: Natural language query
        top_k: Number of results

    Returns:
        List of relevant chunks
    """
    retriever = await get_retriever()
    return await retriever.search_financial_details(
        md5_hash=md5_hash,
        query=query,
        top_k=top_k
    )
