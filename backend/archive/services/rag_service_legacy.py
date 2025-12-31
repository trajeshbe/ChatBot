from typing import Dict, List, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.embedding_service import embedding_service

# Try to import enhanced LLM service, fallback to basic if it fails
try:
    from app.services.llm_service_enhanced import llm_service
except ImportError:
    from app.services.llm_service import llm_service

from app.services.document_service import document_service
from app.services.query_classifier import query_classifier
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
        model_id: Optional[str] = None,
        db: AsyncSession = None,
        # NEW: Optional threshold parameters from UI
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        min_similarity_threshold: Optional[float] = None,
        no_relevant_docs_threshold: Optional[float] = None,
        # NEW: Optional weight parameters from UI
        semantic_weight: Optional[float] = None,
        keyword_weight: Optional[float] = None
    ) -> Dict:
        """
        Process a query using intelligent RAG pipeline:
        1. Classify query (general knowledge vs document-specific vs personal)
        2. Route appropriately:
           - General knowledge → Direct LLM (no RAG)
           - Document-specific → Full RAG pipeline
           - Personal/AI → Direct LLM
        3. Return response with appropriate sources

        Args:
            query_text: The user's query
            conversation_history: Optional conversation history
            use_cache: Whether to use semantic cache
            model_id: Optional LLM model ID
            db: Database session
            top_k: Number of chunks to retrieve (from UI or defaults to settings.TOP_K_RESULTS)
            similarity_threshold: Minimum similarity score (from UI or defaults to settings.SIMILARITY_THRESHOLD)
            min_similarity_threshold: Fallback minimum threshold (from UI or defaults to settings.MIN_SIMILARITY_THRESHOLD)
            no_relevant_docs_threshold: Threshold to determine relevance (from UI or defaults to settings.NO_RELEVANT_DOCS_THRESHOLD)
        """
        start_time = time.time()

        # Use provided values or fall back to settings defaults
        top_k_to_use = top_k if top_k is not None else settings.TOP_K_RESULTS
        similarity_threshold_to_use = similarity_threshold if similarity_threshold is not None else settings.SIMILARITY_THRESHOLD
        no_relevant_threshold_to_use = no_relevant_docs_threshold if no_relevant_docs_threshold is not None else settings.NO_RELEVANT_DOCS_THRESHOLD
        semantic_weight_to_use = semantic_weight if semantic_weight is not None else settings.SEMANTIC_WEIGHT
        keyword_weight_to_use = keyword_weight if keyword_weight is not None else settings.KEYWORD_WEIGHT

        logger.info(f"RAG query with thresholds: top_k={top_k_to_use}, similarity={similarity_threshold_to_use:.2f}, no_relevant={no_relevant_threshold_to_use:.2f}, semantic_weight={semantic_weight_to_use:.2f}, keyword_weight={keyword_weight_to_use:.2f}")

        try:
            # Step 0: Classify the query BEFORE doing any retrieval
            classification = await query_classifier.classify(query_text)
            logger.info(
                f"Query classification: {classification['query_type']} "
                f"(confidence: {classification['confidence']:.2f}) - {classification['reason']}"
            )

            # If this is a general knowledge or AI-personal question, skip RAG entirely
            if not classification['use_documents']:
                logger.info(f"⚡ Skipping RAG for {classification['query_type']} query")

                # Generate appropriate system message based on query type
                if classification['query_type'] == 'ai_personal':
                    system_message = (
                        "You are a helpful enterprise RAG assistant. "
                        "Answer questions about yourself naturally and accurately."
                    )
                elif classification['query_type'] == 'general':
                    system_message = (
                        "You are a helpful AI assistant with general knowledge. "
                        "Answer this general knowledge question accurately and concisely. "
                        "Do not mention or reference any documents."
                    )
                else:
                    system_message = "You are a helpful AI assistant."

                response = await llm_service.generate(
                    prompt=f"System: {system_message}\n\nUser: {query_text}\n\nAssistant:",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": query_text}
                    ],
                    model_id=model_id
                )

                result = {
                    'answer': response['content'],
                    'sources': [],  # No sources for general knowledge
                    'model': response['model'],
                    'model_name': response.get('model_name', response['model']),
                    'tokens_used': response['tokens'],
                    'latency_ms': (time.time() - start_time) * 1000,
                    'num_sources': 0,
                    'cached': False,
                    'query_type': classification['query_type'],
                    'classification_confidence': classification['confidence'],
                    'skipped_rag': True,
                    # Add basic quality metrics even for non-RAG responses
                    'quality_metrics': {
                        'quality_level': 'N/A',
                        'rag_score': None,
                        'note': 'No RAG evaluation (non-document query)',
                        'classification_type': classification['query_type'],
                        'classification_confidence': classification['confidence']
                    }
                }
                return result

            # Continue with RAG for document-specific queries
            # Check semantic cache first
            if use_cache:
                cached_result = await self._check_semantic_cache(query_text, db)
                if cached_result:
                    logger.info("Cache hit for query")
                    cached_result['cached'] = True
                    cached_result['latency_ms'] = (time.time() - start_time) * 1000
                    return cached_result

            # Step 1: Generate embedding for the query
            logger.info(f"Processing document-specific query: {query_text[:100]}...")
            query_embedding = await embedding_service.get_embedding(query_text)

            # Step 2: Search for similar chunks using hybrid search (with UI or default thresholds)
            similar_chunks = await document_service.search_similar_chunks(
                query_embedding=query_embedding,
                query_text=query_text,  # For keyword matching
                top_k=top_k_to_use,  # Use UI value or default
                threshold=similarity_threshold_to_use,  # Use UI value or default
                use_hybrid=True,  # Enable hybrid search
                semantic_weight=semantic_weight_to_use,  # UI-provided or config default
                keyword_weight=keyword_weight_to_use,    # UI-provided or config default
                db=db
            )

            logger.info(f"Found {len(similar_chunks)} chunks (hybrid search)")

            # Filter chunks based on quality threshold (using UI or default value)
            # If best match is below NO_RELEVANT_DOCS_THRESHOLD, treat as no results
            filtered_chunks = []
            if similar_chunks:
                best_score = max(chunk.get('similarity', 0) for chunk in similar_chunks)
                if best_score >= no_relevant_threshold_to_use:  # Use UI value or default
                    filtered_chunks = similar_chunks
                    logger.info(f"✅ {len(filtered_chunks)} high-quality chunks (best score: {best_score:.3f}, threshold: {no_relevant_threshold_to_use:.2f})")
                else:
                    logger.warning(f"⚠️ Best match score {best_score:.3f} below threshold {no_relevant_threshold_to_use:.2f}, treating as no relevant docs")

            # Step 3: Generate response with context
            if filtered_chunks:
                # We have relevant documents - use RAG
                # Further filter to only use high-quality chunks for LLM context
                # This ensures the LLM only sees the most relevant information
                context_threshold = settings.SOURCE_DISPLAY_THRESHOLD
                high_quality_chunks = [
                    chunk for chunk in filtered_chunks
                    if chunk.get('similarity', 0) >= context_threshold
                ]

                # If no high-quality chunks, use all filtered chunks
                chunks_for_context = high_quality_chunks if high_quality_chunks else filtered_chunks

                logger.info(f"📝 Using {len(chunks_for_context)} chunks for LLM context (filtered from {len(filtered_chunks)})")

                response = await llm_service.generate_with_context(
                    query=query_text,
                    context_chunks=chunks_for_context,
                    conversation_history=conversation_history,
                    model_id=model_id
                )
            else:
                # No relevant context found - use pure LLM with helpful message
                logger.warning("No relevant context found, falling back to pure LLM")

                # Check if there are ANY documents in the database
                from sqlalchemy import text as sql_text, func
                count_query = sql_text("SELECT COUNT(*) FROM documents WHERE processed = true")
                count_result = await db.execute(count_query)
                doc_count = count_result.scalar()

                if doc_count == 0:
                    # No documents at all - guide user to upload
                    system_message = (
                        "You are a helpful enterprise RAG assistant. "
                        "Currently, there are no documents in your knowledge base. "
                        "Politely inform the user that they should upload documents "
                        "or scrape URLs first to enable document-based answers. "
                        "However, if they ask a general question that doesn't require "
                        "document context, answer it helpfully."
                    )
                else:
                    # Documents exist but none are relevant to the query
                    system_message = (
                        "You are a helpful enterprise RAG assistant. "
                        "The user has uploaded documents, but none appear directly relevant "
                        "to this specific query (all similarity scores were below 35%). "
                        "If this is a general question about you as an AI assistant, answer it naturally. "
                        "If this is a question about a specific topic, politely inform the user that "
                        "their uploaded documents don't contain information about this topic, and "
                        "suggest they upload relevant documents for better answers."
                    )

                response = await llm_service.generate(
                    prompt=f"System: {system_message}\n\nUser: {query_text}\n\nAssistant:",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": query_text}
                    ],
                    model_id=model_id
                )

            # Step 4: Extract and format sources with quality filtering
            # Only show high-quality sources that likely contributed to the answer
            all_sources = self._format_sources(filtered_chunks)

            # Filter sources by quality threshold
            high_quality_sources = self._filter_high_quality_sources(all_sources)

            # If we have high-quality sources, use them; otherwise show all above display threshold
            if high_quality_sources:
                sources = high_quality_sources
                logger.info(f"✨ Showing {len(sources)} high-quality sources (>={settings.HIGH_QUALITY_SOURCE_THRESHOLD:.0%})")
            else:
                # Fall back to showing sources above display threshold
                sources = [s for s in all_sources if s['relevance'] >= settings.SOURCE_DISPLAY_THRESHOLD]
                if sources:
                    logger.info(f"📊 Showing {len(sources)} sources above display threshold (>={settings.SOURCE_DISPLAY_THRESHOLD:.0%})")
                else:
                    # Last resort: show top 2 sources if any exist
                    sources = all_sources[:2] if all_sources else []
                    if sources:
                        logger.warning(f"⚠️ Showing top {len(sources)} sources (below quality thresholds)")

            result = {
                'answer': response['content'],
                'sources': sources,
                'model': response['model'],
                'model_name': response.get('model_name', response['model']),
                'tokens_used': response['tokens'],
                'latency_ms': (time.time() - start_time) * 1000,
                'num_sources': len(sources),
                'cached': False,
                'query_type': classification['query_type'],
                'classification_confidence': classification['confidence'],
                'skipped_rag': False,
                # Add basic quality metrics (basic RAG service doesn't have full evaluation)
                'quality_metrics': {
                    'quality_level': 'Basic' if filtered_chunks else 'No Context',
                    'rag_score': (sum(c.get('similarity', 0) for c in filtered_chunks) / len(filtered_chunks)) if filtered_chunks else 0.0,
                    'note': f'Basic RAG service - {len(filtered_chunks)} chunks used' if filtered_chunks else 'No relevant documents found',
                    'classification_type': classification['query_type'],
                    'classification_confidence': classification['confidence'],
                    'num_chunks_used': len(filtered_chunks)
                }
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

    def _filter_high_quality_sources(self, sources: List[Dict]) -> List[Dict]:
        """
        Filter sources to only include high-quality matches.
        High-quality sources are those with relevance scores above the threshold.
        """
        if not sources:
            return []

        # Filter by high quality threshold
        high_quality = [
            source for source in sources
            if source['relevance'] >= settings.HIGH_QUALITY_SOURCE_THRESHOLD
        ]

        # Sort by relevance descending
        high_quality.sort(key=lambda x: x['relevance'], reverse=True)

        return high_quality

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
