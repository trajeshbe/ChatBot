"""
Hybrid Retrieval Module

Combines semantic (vector) and lexical (keyword) search for optimal retrieval.
Implements memory hierarchy: session documents (short-term) → all documents (long-term)
"""

from typing import List, Dict, Any, Optional
import logging
from sqlalchemy import text as sql_text, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from .config import get_rag_settings

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Handles hybrid retrieval with semantic and lexical search"""

    def __init__(self):
        self.settings = get_rag_settings()

    async def retrieve_hybrid(
        self,
        query: str,
        query_embedding: List[float],
        top_k: int,
        alpha: float,
        db: AsyncSession,
        session_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        min_similarity: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid retrieval combining semantic and lexical search.

        Implements cascading fallback:
        1. Try session documents first (short-term memory)
        2. Fall back to all documents (long-term memory)

        Args:
            query: Query text
            query_embedding: Query embedding vector
            top_k: Number of results to return
            alpha: Weight for semantic vs lexical (0.0 = pure lexical, 1.0 = pure semantic)
            db: Database session
            session_id: Optional session ID for memory hierarchy
            tenant_id: Optional tenant ID for multi-tenancy
            min_similarity: Minimum similarity threshold

        Returns:
            List of chunks with scores and metadata
        """
        min_similarity = min_similarity or self.settings.MIN_SIMILARITY_THRESHOLD

        # Try session documents first (short-term memory)
        if session_id and self.settings.ENABLE_SESSION_MEMORY:
            logger.info(f"Searching session documents for session {session_id}")
            session_results = await self._search_with_filters(
                query=query,
                query_embedding=query_embedding,
                top_k=top_k,
                alpha=alpha,
                db=db,
                session_id=session_id,
                tenant_id=tenant_id,
                min_similarity=min_similarity
            )

            # Apply session document boost
            if self.settings.PRIORITIZE_SESSION_DOCUMENTS:
                for result in session_results:
                    result['final_score'] += self.settings.SESSION_DOCUMENT_BOOST
                    result['from_session'] = True

            # If we have good results, return them
            if session_results and len(session_results) >= min(3, top_k):
                logger.info(f"Found {len(session_results)} results in session documents")
                return session_results

            logger.info(f"Session documents returned {len(session_results)} results, falling back to all documents")

        # Fallback to all documents (long-term memory)
        if self.settings.FALLBACK_TO_LONG_TERM:
            # Reduce threshold slightly for fallback
            fallback_threshold = max(
                min_similarity - self.settings.FALLBACK_SIMILARITY_REDUCTION,
                self.settings.MIN_SIMILARITY_THRESHOLD
            )

            logger.info(f"Searching all documents (threshold: {fallback_threshold:.2f})")
            all_results = await self._search_with_filters(
                query=query,
                query_embedding=query_embedding,
                top_k=top_k,
                alpha=alpha,
                db=db,
                session_id=None,  # Search all documents
                tenant_id=tenant_id,
                min_similarity=fallback_threshold
            )

            # Mark as from long-term memory
            for result in all_results:
                result['from_session'] = False

            return all_results

        # No results found
        return []

    async def _search_with_filters(
        self,
        query: str,
        query_embedding: List[float],
        top_k: int,
        alpha: float,
        db: AsyncSession,
        session_id: Optional[str],
        tenant_id: Optional[str],
        min_similarity: float
    ) -> List[Dict[str, Any]]:
        """
        Internal method to perform hybrid search with filters.
        """
        try:
            # Convert embedding to string for SQL
            embedding_str = f"[{','.join(map(str, query_embedding))}]"

            # Prepare query with optional filters
            session_filter = ""
            if session_id:
                session_filter = """
                    AND dc.document_id IN (
                        SELECT document_id FROM session_documents
                        WHERE session_id = :session_id
                    )
                """

            # Build hybrid search query
            # Semantic score: 1 - cosine_distance (pgvector <=> operator)
            # Lexical score: ts_rank (PostgreSQL full-text search)
            query_sql = sql_text(f"""
                WITH semantic_search AS (
                    SELECT
                        dc.id as chunk_id,
                        dc.document_id,
                        dc.content,
                        dc.chunk_index,
                        dc.meta_info as chunk_metadata,
                        1 - (dc.embedding <=> '{embedding_str}'::vector) as semantic_score,
                        d.filename,
                        d.source_type,
                        d.source_url,
                        d.meta_info as doc_metadata
                    FROM document_chunks dc
                    INNER JOIN documents d ON dc.document_id = d.id
                    WHERE d.processed = true
                        AND dc.embedding IS NOT NULL
                        {session_filter}
                    ORDER BY dc.embedding <=> '{embedding_str}'::vector
                    LIMIT :semantic_limit
                ),
                lexical_search AS (
                    SELECT
                        dc.id as chunk_id,
                        dc.document_id,
                        dc.content,
                        dc.chunk_index,
                        dc.meta_info as chunk_metadata,
                        ts_rank(
                            to_tsvector('english', dc.content),
                            plainto_tsquery('english', :query_text)
                        ) as lexical_score,
                        d.filename,
                        d.source_type,
                        d.source_url,
                        d.meta_info as doc_metadata
                    FROM document_chunks dc
                    INNER JOIN documents d ON dc.document_id = d.id
                    WHERE d.processed = true
                        AND to_tsvector('english', dc.content) @@ plainto_tsquery('english', :query_text)
                        {session_filter}
                    ORDER BY lexical_score DESC
                    LIMIT :lexical_limit
                )
                SELECT DISTINCT
                    COALESCE(s.chunk_id, l.chunk_id) as chunk_id,
                    COALESCE(s.document_id, l.document_id) as document_id,
                    COALESCE(s.content, l.content) as content,
                    COALESCE(s.chunk_index, l.chunk_index) as chunk_index,
                    COALESCE(s.chunk_metadata, l.chunk_metadata) as chunk_metadata,
                    COALESCE(s.filename, l.filename) as filename,
                    COALESCE(s.source_type, l.source_type) as source_type,
                    COALESCE(s.source_url, l.source_url) as source_url,
                    COALESCE(s.doc_metadata, l.doc_metadata) as doc_metadata,
                    COALESCE(s.semantic_score, 0.0) as semantic_score,
                    COALESCE(l.lexical_score, 0.0) as lexical_score,
                    (
                        :alpha * COALESCE(s.semantic_score, 0.0) +
                        (1 - :alpha) * COALESCE(l.lexical_score, 0.0)
                    ) as final_score
                FROM semantic_search s
                FULL OUTER JOIN lexical_search l ON s.chunk_id = l.chunk_id
                WHERE (
                    :alpha * COALESCE(s.semantic_score, 0.0) +
                    (1 - :alpha) * COALESCE(l.lexical_score, 0.0)
                ) >= :min_similarity
                ORDER BY final_score DESC
                LIMIT :top_k
            """)

            # Execute query
            params = {
                "query_text": query,
                "semantic_limit": top_k * 2,  # Get more candidates for hybrid fusion
                "lexical_limit": top_k * 2,
                "alpha": alpha,
                "top_k": top_k,
                "min_similarity": min_similarity
            }

            if session_id:
                params["session_id"] = session_id

            result = await db.execute(query_sql, params)
            rows = result.fetchall()

            # Format results
            chunks = []
            for row in rows:
                chunk = {
                    "id": str(row.chunk_id),
                    "doc_id": str(row.document_id),
                    "text": row.content,
                    "content": row.content,  # Alias for compatibility
                    "chunk_index": row.chunk_index,
                    "filename": row.filename,
                    "source_type": row.source_type,
                    "source_url": row.source_url,
                    "document_id": str(row.document_id),  # Alias for compatibility
                    "metadata": {
                        "chunk_metadata": row.chunk_metadata,
                        "doc_metadata": row.doc_metadata
                    },
                    "semantic_score": float(row.semantic_score),
                    "lexical_score": float(row.lexical_score),
                    "final_score": float(row.final_score),
                    "similarity": float(row.final_score),  # Alias for compatibility
                    "source": row.filename  # For compatibility with LLM prompts
                }
                chunks.append(chunk)

            logger.info(
                f"Hybrid search returned {len(chunks)} chunks "
                f"(alpha={alpha:.2f}, session={session_id is not None})"
            )

            if self.settings.LOG_RETRIEVAL_SCORES and chunks:
                logger.debug(f"Top result score - semantic: {chunks[0]['semantic_score']:.3f}, "
                           f"lexical: {chunks[0]['lexical_score']:.3f}, "
                           f"final: {chunks[0]['final_score']:.3f}")

            return chunks

        except Exception as e:
            logger.error(f"Error in hybrid retrieval: {e}", exc_info=True)
            raise


# Global singleton
_retriever = None


async def get_retriever() -> HybridRetriever:
    """Get or create global retriever instance"""
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever


# Convenience function for the pipeline
async def retrieve_hybrid(
    query: str,
    query_embedding: List[float],
    top_k: int,
    alpha: float,
    db: AsyncSession,
    session_id: Optional[str] = None,
    tenant_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Perform hybrid retrieval.

    Args:
        query: Query text
        query_embedding: Query embedding vector
        top_k: Number of results to return
        alpha: Semantic vs lexical weight (0.0-1.0)
        db: Database session
        session_id: Optional session ID
        tenant_id: Optional tenant ID

    Returns:
        List of retrieved chunks with scores
    """
    retriever = await get_retriever()
    return await retriever.retrieve_hybrid(
        query=query,
        query_embedding=query_embedding,
        top_k=top_k,
        alpha=alpha,
        db=db,
        session_id=session_id,
        tenant_id=tenant_id
    )
