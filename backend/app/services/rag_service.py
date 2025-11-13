from typing import Dict, List, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.embedding_service import embedding_service
from app.services.llm_service import llm_service
from app.services.document_service import document_service
from app.core.config import settings
import time

logger = logging.getLogger(__name__)


class RAGService:
    """RAG (Retrieval-Augmented Generation) Service"""

    async def query(
        self,
        query_text: str,
        conversation_history: Optional[List[Dict]] = None,
        use_cache: bool = True,
        db: AsyncSession = None
    ) -> Dict:
        """
        Process a query using RAG pipeline:
        1. Generate query embedding
        2. Search for similar document chunks
        3. Generate response with context
        4. Return response with source references
        """
        start_time = time.time()

        try:
            # Check semantic cache first
            if use_cache:
                cached_result = await self._check_semantic_cache(query_text, db)
                if cached_result:
                    logger.info("Cache hit for query")
                    cached_result['cached'] = True
                    cached_result['latency_ms'] = (time.time() - start_time) * 1000
                    return cached_result

            # Step 1: Generate embedding for the query
            logger.info(f"Processing query: {query_text[:100]}...")
            query_embedding = await embedding_service.get_embedding(query_text)

            # Step 2: Search for similar chunks
            similar_chunks = await document_service.search_similar_chunks(
                query_embedding=query_embedding,
                top_k=settings.TOP_K_RESULTS,
                threshold=settings.SIMILARITY_THRESHOLD,
                db=db
            )

            logger.info(f"Found {len(similar_chunks)} relevant chunks")

            # Step 3: Generate response with context
            if similar_chunks:
                response = await llm_service.generate_with_context(
                    query=query_text,
                    context_chunks=similar_chunks,
                    conversation_history=conversation_history
                )
            else:
                # No relevant context found - inform user about uploading documents
                logger.warning("No relevant context found, generating response without RAG")
                system_message = ("You are a helpful enterprise RAG assistant. "
                                "Currently, there are no documents in your knowledge base. "
                                "Politely inform the user that they should upload documents "
                                "or scrape URLs first to enable document-based answers. "
                                "Still answer their question if it's a general one.")
                response = await llm_service.generate(
                    prompt=f"System: {system_message}\n\nUser: {query_text}\n\nAssistant:",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": query_text}
                    ]
                )

            # Step 4: Extract and format sources
            sources = self._format_sources(similar_chunks)

            result = {
                'answer': response['content'],
                'sources': sources,
                'model': response['model'],
                'tokens_used': response['tokens'],
                'latency_ms': (time.time() - start_time) * 1000,
                'num_sources': len(sources),
                'cached': False
            }

            # Cache the result
            if use_cache and settings.USE_SEMANTIC_CACHE:
                await self._cache_result(query_text, query_embedding, result, db)

            return result

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise

    def _format_sources(self, chunks: List[Dict]) -> List[Dict]:
        """Format source references for the response"""
        sources = []
        seen_docs = set()

        for i, chunk in enumerate(chunks):
            doc_id = chunk['document_id']
            if doc_id not in seen_docs:
                sources.append({
                    'id': chunk['document_id'],
                    'filename': chunk['filename'],
                    'source_type': chunk['source_type'],
                    'source_url': chunk.get('source_url'),
                    'relevance': chunk['similarity'],
                    'excerpt': chunk['content'][:200] + "..." if len(chunk['content']) > 200 else chunk['content']
                })
                seen_docs.add(doc_id)

        return sources

    async def _check_semantic_cache(
        self,
        query_text: str,
        db: AsyncSession
    ) -> Optional[Dict]:
        """Check semantic cache for similar queries"""
        try:
            from sqlalchemy import text as sql_text, func

            # Generate embedding for query
            query_embedding = await embedding_service.get_embedding(query_text)
            embedding_str = f"[{','.join(map(str, query_embedding))}]"

            # Search for similar cached queries
            # Note: Embedding is embedded directly in SQL since asyncpg doesn't support vector params
            query = sql_text(f"""
                SELECT
                    id,
                    response,
                    sources,
                    1 - (query_embedding <=> '{embedding_str}'::vector) as similarity,
                    EXTRACT(EPOCH FROM (NOW() - created_at)) as age_seconds,
                    ttl_seconds
                FROM query_cache
                WHERE 1 - (query_embedding <=> '{embedding_str}'::vector) > 0.95
                    AND EXTRACT(EPOCH FROM (NOW() - created_at)) < ttl_seconds
                ORDER BY similarity DESC
                LIMIT 1
            """)

            result = await db.execute(query)
            row = result.first()

            if row:
                # Update hit count
                update_query = sql_text("""
                    UPDATE query_cache
                    SET hit_count = hit_count + 1, last_accessed = NOW()
                    WHERE id = :cache_id
                """)
                await db.execute(update_query, {"cache_id": row.id})
                await db.commit()

                logger.info(f"Cache hit with similarity {row.similarity}")
                return row.response

            return None

        except Exception as e:
            logger.warning(f"Error checking semantic cache: {e}")
            # Rollback on error to prevent transaction-aborted state
            await db.rollback()
            return None

    async def _cache_result(
        self,
        query_text: str,
        query_embedding: List[float],
        result: Dict,
        db: AsyncSession
    ):
        """Cache query result for future use"""
        try:
            from sqlalchemy import text as sql_text
            import json

            embedding_str = f"[{','.join(map(str, query_embedding))}]"

            # Note: Embedding is embedded directly in SQL since asyncpg doesn't support vector params
            query = sql_text(f"""
                INSERT INTO query_cache (query_text, query_embedding, response, sources, ttl_seconds)
                VALUES (:query_text, '{embedding_str}'::vector, :response, :sources, :ttl)
            """)

            await db.execute(
                query,
                {
                    "query_text": query_text,
                    "response": json.dumps(result),
                    "sources": json.dumps(result.get('sources', [])),
                    "ttl": 3600  # 1 hour
                }
            )
            await db.commit()

            logger.info("Cached query result")

        except Exception as e:
            logger.warning(f"Error caching result: {e}")
            await db.rollback()


# Singleton instance
rag_service = RAGService()
