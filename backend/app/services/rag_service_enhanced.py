"""
Enhanced RAG Service with Memory Hierarchy and Session Management

Memory Hierarchy:
1. Short-term memory: Session-specific documents (highest priority)
2. Long-term memory: All documents in vector store (lower priority)
3. Conversation context: Recent messages in session

This ensures recently uploaded documents in a session are prioritized.
"""

from typing import Dict, List, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text as sql_text, and_, func
from app.services.embedding_service import embedding_service
from app.services.document_service import document_service
from app.services.query_classifier import query_classifier
from app.services.quality_metrics import quality_metrics_service
from app.core.config import settings
import time
import uuid

logger = logging.getLogger(__name__)

# Import LLM service
try:
    from app.services.llm_service_enhanced import llm_service
except ImportError:
    from app.services.llm_service import llm_service


class EnhancedRAGService:
    """
    Enhanced RAG service with memory hierarchy:
    - Short-term memory (session documents)
    - Long-term memory (all documents)
    - Session context tracking
    - Audit logging integration
    """

    async def query(
        self,
        query_text: str,
        session_id: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        conversation_history: Optional[List[Dict]] = None,
        use_cache: bool = True,
        model_id: Optional[str] = None,
        db: AsyncSession = None,
        # RAG configuration parameters (override defaults from settings)
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        min_similarity_threshold: Optional[float] = None,
        no_relevant_docs_threshold: Optional[float] = None
    ) -> Dict:
        """
        Process query with memory hierarchy:
        1. Check semantic cache
        2. Search short-term memory (session documents) first
        3. Search long-term memory (all documents) if needed
        4. Generate response with context
        5. Log to audit trail
        """
        start_time = time.time()

        try:
            # Use provided RAG config parameters or fall back to settings
            _top_k = top_k if top_k is not None else settings.TOP_K_RESULTS
            _similarity_threshold = similarity_threshold if similarity_threshold is not None else settings.SIMILARITY_THRESHOLD
            _min_similarity_threshold = min_similarity_threshold if min_similarity_threshold is not None else settings.MIN_SIMILARITY_THRESHOLD
            _no_relevant_docs_threshold = no_relevant_docs_threshold if no_relevant_docs_threshold is not None else settings.NO_RELEVANT_DOCS_THRESHOLD

            logger.info(f"🔧 RAG Config: top_k={_top_k}, sim_threshold={_similarity_threshold:.2f}, min_sim={_min_similarity_threshold:.2f}, no_relevant={_no_relevant_docs_threshold:.2f}")

            # Ensure session exists
            if session_id:
                await self._ensure_session_exists(session_id, user_id, db)

            # STEP 0: Preprocess query for better retrieval and classification
            preprocessing = query_classifier.preprocess_query(query_text)
            processed_query = preprocessing['processed_query']
            recommended_threshold = preprocessing['recommended_threshold']

            # Log preprocessing
            if preprocessing['preprocessing_applied']:
                logger.info(f"🔄 Query preprocessing applied:")
                logger.info(f"   Original: '{query_text}'")
                logger.info(f"   Processed: '{processed_query}'")
                if preprocessing['has_proper_nouns']:
                    logger.info(f"   Proper nouns detected: {preprocessing['proper_nouns']}")
                logger.info(f"   Recommended threshold: {recommended_threshold:.2f}")

            # Use adaptive threshold if preprocessing detected special cases
            if preprocessing['preprocessing_applied'] or preprocessing['has_proper_nouns']:
                _similarity_threshold = recommended_threshold
                logger.info(f"🎯 Using adaptive threshold: {_similarity_threshold:.2f}")

            # STEP 1: Classify query using PREPROCESSED query for better accuracy
            classification = await query_classifier.classify(processed_query)  # Use processed query!
            logger.info(f"📊 Query classification: {classification['query_type']} (confidence: {classification['confidence']:.2f}) - {classification['reason']}")

            # If this is an AI-personal question, skip RAG entirely
            if classification['query_type'] == 'ai_personal':
                logger.info("⚡ Skipping RAG for AI-personal question - using direct LLM response")

                # Use a system message appropriate for AI-personal questions
                system_message = (
                    "You are a helpful AI assistant. Answer questions about yourself naturally and accurately. "
                    "You are an enterprise RAG (Retrieval-Augmented Generation) chatbot that can answer questions "
                    "using uploaded documents. You support multiple AI models including OpenAI, Claude, and local models. "
                    "Be friendly and informative when answering questions about your capabilities."
                )

                response = await llm_service.generate(
                    prompt=query_text,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": query_text}
                    ],
                    model_id=model_id
                )

                result = {
                    'answer': response['content'],
                    'sources': [],
                    'model': response['model'],
                    'model_name': response.get('model_name', response['model']),
                    'tokens_used': response['tokens'],
                    'latency_ms': (time.time() - start_time) * 1000,
                    'num_sources': 0,
                    'num_short_term_sources': 0,
                    'num_long_term_sources': 0,
                    'session_id': session_id,
                    'cached': False,
                    'context_info': 'Direct answer (AI-personal question)',
                    'query_classification': classification['query_type']
                }

                # Still save to conversation history
                if session_id:
                    await self._save_conversation_message(
                        session_id=session_id,
                        role='user',
                        content=query_text,
                        db=db
                    )
                    await self._save_conversation_message(
                        session_id=session_id,
                        role='assistant',
                        content=response['content'],
                        model_id=response['model'],
                        model_name=response.get('model_name'),
                        tokens=response.get('tokens', 0),
                        latency_ms=(time.time() - start_time) * 1000,
                        sources=[],
                        db=db
                    )

                return result

            # STEP 2: Check semantic cache first (use ORIGINAL query for cache key)
            if use_cache:
                cached_result = await self._check_semantic_cache(query_text, db)
                if cached_result:
                    logger.info(f"✅ Cache hit for query in session {session_id}")
                    cached_result['cached'] = True
                    cached_result['latency_ms'] = (time.time() - start_time) * 1000
                    return cached_result

            # STEP 3: Generate embedding for the PROCESSED query
            logger.info(f"🔍 Generating embedding for query (session: {session_id})")
            query_embedding = await embedding_service.get_embedding(processed_query)

            # STEP 4: Search short-term memory first (session documents)
            short_term_chunks = []
            if session_id:
                short_term_chunks = await self._search_session_documents(
                    session_id=session_id,
                    query_embedding=query_embedding,
                    query_text=query_text,  # For keyword matching
                    top_k=_top_k,
                    threshold=_similarity_threshold - 0.05,  # Slightly lower threshold for session docs
                    use_hybrid=True,  # Enable hybrid search
                    use_cascading_fallback=True,  # Enable cascading fallback
                    db=db
                )
                if short_term_chunks:
                    logger.info(f"✅ Found {len(short_term_chunks)} chunks in short-term memory (session documents) - hybrid search")
                    logger.info(f"📄 Session documents used: {list(set([c['filename'] for c in short_term_chunks]))}")
                else:
                    logger.info(f"⚠️ No session-specific documents found for session {session_id}")

            # Step 3: Search long-term memory (all documents) using hybrid search with cascading fallback
            long_term_chunks = await document_service.search_similar_chunks(
                query_embedding=query_embedding,
                query_text=query_text,  # For keyword matching
                top_k=_top_k,
                threshold=_similarity_threshold,
                use_hybrid=True,  # Enable hybrid search
                use_cascading_fallback=True,  # Enable cascading fallback
                db=db
            )
            logger.info(f"Found {len(long_term_chunks)} chunks in long-term memory - hybrid search with fallback")

            # Step 4: Combine and deduplicate results (short-term has priority)
            combined_chunks = self._combine_memory_results(
                short_term_chunks,
                long_term_chunks,
                max_chunks=_top_k
            )
            logger.info(f"Combined to {len(combined_chunks)} total chunks")

            # Step 5: Get conversation context if session_id provided
            conversation_context = []
            if session_id:
                conversation_context = await self._get_conversation_context(
                    session_id=session_id,
                    max_messages=10,
                    db=db
                )
                logger.info(f"Retrieved {len(conversation_context)} messages from conversation history")

            # Step 6: Generate response with context
            if combined_chunks or conversation_context:
                logger.info(f"🎯 Generating response with {len(combined_chunks)} chunks and {len(conversation_context)} conversation messages")
                logger.debug(f"Context chunks summary: {[{'filename': c.get('filename'), 'memory_type': c.get('memory_type'), 'similarity': c.get('similarity')} for c in combined_chunks]}")
                response = await llm_service.generate_with_context(
                    query=query_text,
                    context_chunks=combined_chunks,
                    conversation_history=conversation_context,
                    model_id=model_id
                )
            else:
                # No context found - use pure LLM with helpful warning message
                logger.warning(f"⚠️ No relevant context found for query: '{query_text[:100]}...'")
                if preprocessing['preprocessing_applied']:
                    logger.warning(f"   Even after preprocessing: '{processed_query[:100]}...'")

                # Check if there are ANY documents in the database
                count_query = sql_text("SELECT COUNT(*) FROM documents WHERE processed = true")
                count_result = await db.execute(count_query)
                doc_count = count_result.scalar()

                if doc_count == 0:
                    # No documents at all - guide user to upload
                    warning_prefix = (
                        "⚠️ **No Documents Available**: I don't have any documents in my knowledge base yet. "
                        "Please upload documents or scrape URLs to enable document-based answers.\n\n"
                    )
                    system_message = (
                        "You are a helpful enterprise RAG assistant. "
                        "Currently, there are no documents in your knowledge base. "
                        "Start your response with the warning message provided, then answer "
                        "the question using your general knowledge if appropriate. "
                        "Keep your answer concise and helpful."
                    )
                else:
                    # Documents exist but none are relevant to the query
                    warning_prefix = (
                        f"⚠️ **No Relevant Documents Found**: I searched through {doc_count} document(s) "
                        f"but couldn't find information relevant to your query. "
                        "My response is based on general knowledge, not your uploaded documents.\n\n"
                    )
                    system_message = (
                        "You are a helpful enterprise RAG assistant. "
                        "The user has uploaded documents, but none appear directly relevant "
                        "to this specific query. Start your response with the warning message provided, "
                        "then provide the best answer you can based on your general knowledge. "
                        "Suggest that the user might want to upload more relevant documents if they need specific information."
                    )

                response = await llm_service.generate(
                    prompt=f"System: {system_message}\n\nWarning prefix to use: {warning_prefix}\n\nUser: {query_text}\n\nAssistant:",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": f"{warning_prefix}User query: {query_text}"}
                    ],
                    model_id=model_id
                )

            # Step 7: Format sources with memory indicators
            sources = self._format_sources(combined_chunks, short_term_chunks, _no_relevant_docs_threshold)

            num_short_term = len([s for s in sources if s.get('memory_type') == 'short-term'])
            num_long_term = len([s for s in sources if s.get('memory_type') == 'long-term'])

            result = {
                'answer': response['content'],
                'sources': sources,
                'model': response['model'],
                'model_name': response.get('model_name', response['model']),
                'tokens_used': response['tokens'],
                'latency_ms': (time.time() - start_time) * 1000,
                'num_sources': len(sources),
                'num_short_term_sources': num_short_term,
                'num_long_term_sources': num_long_term,
                'session_id': session_id,
                'cached': False,
                'context_info': f"Used {num_short_term} session document(s) and {num_long_term} global document(s)" if sources else "No documents found",
                'query_classification': classification['query_type'],
                # 🆕 Include RAG settings used for this query
                'rag_settings': {
                    'top_k': _top_k,
                    'similarity_threshold': _similarity_threshold,
                    'min_similarity_threshold': _min_similarity_threshold,
                    'no_relevant_docs_threshold': _no_relevant_docs_threshold,
                    'chunk_size': settings.CHUNK_SIZE,
                    'chunk_overlap': settings.CHUNK_OVERLAP,
                    'search_type': 'hybrid',  # Indicates we're using hybrid search
                    'memory_type': 'hierarchical'  # Indicates two-tier memory hierarchy
                }
            }

            # Step 7.5: Calculate quality metrics for the response
            if combined_chunks:  # Only evaluate if we used RAG
                try:
                    quality_metrics = await quality_metrics_service.evaluate_response(
                        query=query_text,
                        answer=response['content'],
                        context_chunks=combined_chunks
                    )
                    result['quality_metrics'] = quality_metrics
                    logger.info(f"📊 Quality: {quality_metrics.get('quality_level', 'unknown')} (score: {quality_metrics.get('rag_score', 0):.2f})")

                    # Log warning if quality is poor
                    if quality_metrics.get('rag_score', 1) < 0.4:
                        logger.warning(f"⚠️ LOW QUALITY RESPONSE detected! Score: {quality_metrics.get('rag_score', 0):.2f}")
                        logger.warning(quality_metrics_service.generate_quality_report(quality_metrics))
                except Exception as e:
                    logger.error(f"Error calculating quality metrics: {e}")
                    result['quality_metrics'] = None

            # Step 8: Save conversation message
            if session_id:
                await self._save_conversation_message(
                    session_id=session_id,
                    role='user',
                    content=query_text,
                    db=db
                )
                await self._save_conversation_message(
                    session_id=session_id,
                    role='assistant',
                    content=response['content'],
                    model_id=response['model'],
                    model_name=response.get('model_name'),
                    tokens=response.get('tokens', 0),
                    latency_ms=(time.time() - start_time) * 1000,
                    sources=sources,
                    db=db
                )

            # Step 9: Cache the result
            if use_cache and settings.USE_SEMANTIC_CACHE:
                await self._cache_result(query_text, query_embedding, result, db)

            return result

        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            raise

    async def associate_document_with_session(
        self,
        session_id: str,
        document_id: uuid.UUID,
        priority: int = 0,
        db: AsyncSession = None
    ):
        """Add a document to a session's short-term memory"""
        try:
            # Import here to avoid circular dependency
            from app.models.database_enhanced import SessionDocument, ChatSession

            # Ensure session exists
            session_query = select(ChatSession).where(ChatSession.session_id == session_id)
            session_result = await db.execute(session_query)
            session = session_result.scalar_one_or_none()

            if not session:
                logger.warning(f"Session {session_id} not found, creating...")
                session = ChatSession(session_id=session_id)
                db.add(session)
                await db.flush()  # Flush to get ID without committing
                await db.refresh(session)

            # Check if association already exists
            existing_query = select(SessionDocument).where(
                and_(
                    SessionDocument.session_id == session.id,
                    SessionDocument.document_id == document_id
                )
            )
            existing_result = await db.execute(existing_query)
            existing = existing_result.scalar_one_or_none()

            if not existing:
                session_doc = SessionDocument(
                    session_id=session.id,
                    document_id=document_id,
                    priority=priority
                )
                db.add(session_doc)
                await db.flush()  # Flush to database without committing transaction
                logger.info(f"Associated document {document_id} with session {session_id}")

        except Exception as e:
            logger.error(f"Error associating document with session: {e}")
            # Don't rollback here - let the calling code handle it
            raise

    async def _search_session_documents(
        self,
        session_id: str,
        query_embedding: List[float],
        query_text: str = None,
        top_k: int = 5,
        threshold: float = 0.6,
        use_hybrid: bool = True,
        use_cascading_fallback: bool = True,
        db: AsyncSession = None
    ) -> List[Dict]:
        """
        Search only documents associated with this session (short-term memory)
        with optional hybrid search and cascading fallback
        """
        try:
            from app.models.database_enhanced import SessionDocument, ChatSession
            from app.models.database import DocumentChunk

            # Get session
            session_query = select(ChatSession).where(ChatSession.session_id == session_id)
            session_result = await db.execute(session_query)
            session = session_result.scalar_one_or_none()

            if not session:
                return []

            # Check if there are any session documents
            count_query = select(func.count()).select_from(SessionDocument).where(
                SessionDocument.session_id == session.id
            )
            count_result = await db.execute(count_query)
            session_doc_count = count_result.scalar()

            if session_doc_count == 0:
                logger.info(f"No documents associated with session {session_id}")
                return []

            # Check chunks with embeddings for session documents
            embedding_count_query = sql_text(f"""
                SELECT COUNT(*)
                FROM document_chunks dc
                JOIN session_documents sd ON dc.document_id = sd.document_id
                WHERE sd.session_id = :session_id AND dc.embedding IS NOT NULL
            """)
            embedding_count_result = await db.execute(
                embedding_count_query,
                {"session_id": session.id}
            )
            embedding_count = embedding_count_result.scalar()

            logger.info(f"📊 Session {session_id}: {session_doc_count} documents, {embedding_count} chunks with embeddings")

            if embedding_count == 0:
                logger.warning(f"No embeddings found for session {session_id} documents")
                return []

            # Cascading fallback strategy - reduced aggressiveness to prevent irrelevant results
            thresholds_to_try = [threshold]
            if use_cascading_fallback:
                # Only fallback by small amounts, don't go too low
                if threshold > settings.MIN_SIMILARITY_THRESHOLD + 0.1:
                    thresholds_to_try.append(threshold - 0.1)
                if threshold > settings.MIN_SIMILARITY_THRESHOLD:
                    thresholds_to_try.append(settings.MIN_SIMILARITY_THRESHOLD)

            chunks = []
            for current_threshold in thresholds_to_try:
                if current_threshold < 0:
                    continue

                logger.info(f"🔍 Session search with threshold={current_threshold:.2f}")

                chunks = await self._execute_session_search(
                    session_id=session.id,
                    query_embedding=query_embedding,
                    query_text=query_text,
                    threshold=current_threshold,
                    top_k=top_k,
                    use_hybrid=use_hybrid,
                    db=db
                )

                if chunks:
                    logger.info(f"✅ Found {len(chunks)} session chunks with threshold={current_threshold:.2f}")
                    break
                else:
                    logger.warning(f"⚠️ No session results with threshold={current_threshold:.2f}")

            # Final fallback: keyword search on session documents
            if not chunks and query_text and use_hybrid:
                logger.info("🔍 Session fallback: trying keyword-only search...")
                chunks = await self._keyword_only_session_search(
                    session_id=session.id,
                    query_text=query_text,
                    top_k=top_k,
                    db=db
                )
                if chunks:
                    logger.info(f"✅ Found {len(chunks)} session chunks with keyword search")

            return chunks

        except Exception as e:
            logger.error(f"Error searching session documents: {e}", exc_info=True)
            await db.rollback()
            return []

    async def _execute_session_search(
        self,
        session_id: uuid.UUID,
        query_embedding: List[float],
        query_text: Optional[str],
        threshold: float,
        top_k: int,
        use_hybrid: bool,
        db: AsyncSession
    ) -> List[Dict]:
        """Execute session document search with given parameters"""
        try:
            embedding_str = f"[{','.join(map(str, query_embedding))}]"

            # Hybrid search: combine semantic and keyword search
            if use_hybrid and query_text:
                keywords = document_service._extract_keywords(query_text)
                if not keywords:
                    return await self._execute_session_search(
                        session_id, query_embedding, None, threshold, top_k, False, db
                    )

                keyword_condition = " OR ".join([f"dc.content ILIKE '%{kw}%'" for kw in keywords])

                query = sql_text(f"""
                    WITH semantic_search AS (
                        SELECT
                            dc.id,
                            dc.document_id,
                            dc.content,
                            dc.meta_info::jsonb as meta_info,
                            d.filename,
                            d.source_type,
                            d.source_url,
                            sd.priority,
                            1 - (dc.embedding <=> '{embedding_str}'::vector) as semantic_score
                        FROM document_chunks dc
                        JOIN documents d ON dc.document_id = d.id
                        JOIN session_documents sd ON d.id = sd.document_id
                        WHERE sd.session_id = :session_id
                            AND dc.embedding IS NOT NULL
                    ),
                    keyword_search AS (
                        SELECT
                            id,
                            CASE
                                WHEN ({keyword_condition}) THEN 1.0
                                ELSE 0.0
                            END as keyword_score
                        FROM document_chunks dc
                    )
                    SELECT
                        ss.id,
                        ss.document_id,
                        ss.content,
                        ss.meta_info,
                        ss.filename,
                        ss.source_type,
                        ss.source_url,
                        ss.priority,
                        ss.semantic_score,
                        COALESCE(ks.keyword_score, 0) as keyword_score,
                        (ss.semantic_score * 0.6 + COALESCE(ks.keyword_score, 0) * 0.4) as combined_score
                    FROM semantic_search ss
                    LEFT JOIN keyword_search ks ON ss.id = ks.id
                    WHERE (ss.semantic_score * 0.6 + COALESCE(ks.keyword_score, 0) * 0.4) > :threshold
                    ORDER BY ss.priority DESC, combined_score DESC
                    LIMIT :limit
                """)
            else:
                # Standard semantic search only
                query = sql_text(f"""
                    SELECT
                        dc.id,
                        dc.document_id,
                        dc.content,
                        dc.meta_info::jsonb as meta_info,
                        d.filename,
                        d.source_type,
                        d.source_url,
                        sd.priority,
                        1 - (dc.embedding <=> '{embedding_str}'::vector) as semantic_score,
                        0.0 as keyword_score,
                        1 - (dc.embedding <=> '{embedding_str}'::vector) as combined_score
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                    JOIN session_documents sd ON d.id = sd.document_id
                    WHERE sd.session_id = :session_id
                        AND dc.embedding IS NOT NULL
                        AND 1 - (dc.embedding <=> '{embedding_str}'::vector) > :threshold
                    ORDER BY sd.priority DESC, dc.embedding <=> '{embedding_str}'::vector
                    LIMIT :limit
                """)

            result = await db.execute(
                query,
                {
                    "session_id": session_id,
                    "threshold": threshold,
                    "limit": top_k
                }
            )

            chunks = []
            for row in result:
                chunks.append({
                    'id': str(row.id),
                    'document_id': str(row.document_id),
                    'content': row.content,
                    'meta_info': row.meta_info,
                    'filename': row.filename,
                    'source_type': row.source_type,
                    'source_url': row.source_url,
                    'similarity': float(row.combined_score),
                    'semantic_score': float(row.semantic_score),
                    'keyword_score': float(row.keyword_score),
                    'memory_type': 'short-term',
                    'priority': row.priority
                })

            return chunks

        except Exception as e:
            logger.error(f"Error in _execute_session_search: {e}", exc_info=True)
            await db.rollback()
            return []

    async def _keyword_only_session_search(
        self,
        session_id: uuid.UUID,
        query_text: str,
        top_k: int,
        db: AsyncSession
    ) -> List[Dict]:
        """Pure keyword search for session documents"""
        try:
            keywords = document_service._extract_keywords(query_text)
            if not keywords:
                return []

            keyword_conditions = [f"dc.content ILIKE :kw{i}" for i in range(len(keywords))]
            keyword_clause = " OR ".join(keyword_conditions)

            query = sql_text(f"""
                SELECT
                    dc.id,
                    dc.document_id,
                    dc.content,
                    dc.meta_info::jsonb as meta_info,
                    d.filename,
                    d.source_type,
                    d.source_url,
                    sd.priority
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                JOIN session_documents sd ON d.id = sd.document_id
                WHERE sd.session_id = :session_id
                    AND ({keyword_clause})
                ORDER BY sd.priority DESC
                LIMIT :limit
            """)

            params = {f"kw{i}": f"%{kw}%" for i, kw in enumerate(keywords)}
            params["session_id"] = session_id
            params["limit"] = top_k

            result = await db.execute(query, params)

            chunks = []
            for row in result:
                chunks.append({
                    'id': str(row.id),
                    'document_id': str(row.document_id),
                    'content': row.content,
                    'meta_info': row.meta_info,
                    'filename': row.filename,
                    'source_type': row.source_type,
                    'source_url': row.source_url,
                    'keyword_score': 1.0,
                    'semantic_score': 0.1,
                    'combined_score': 0.5,
                    'similarity': 0.5,
                    'memory_type': 'short-term',
                    'priority': row.priority,
                    'search_type': 'keyword_only'
                })

            return chunks

        except Exception as e:
            logger.error(f"Error in keyword-only session search: {e}", exc_info=True)
            await db.rollback()
            return []

    def _combine_memory_results(
        self,
        short_term_chunks: List[Dict],
        long_term_chunks: List[Dict],
        max_chunks: int = 5
    ) -> List[Dict]:
        """
        Combine short-term and long-term memory results.
        Short-term memory gets priority.
        """
        # Add memory_type to long-term chunks
        for chunk in long_term_chunks:
            if 'memory_type' not in chunk:
                chunk['memory_type'] = 'long-term'

        # Deduplicate by chunk ID
        seen_ids = set()
        combined = []

        # Add short-term chunks first (highest priority)
        for chunk in short_term_chunks:
            if chunk['id'] not in seen_ids:
                combined.append(chunk)
                seen_ids.add(chunk['id'])

        # Add long-term chunks up to max_chunks
        for chunk in long_term_chunks:
            if len(combined) >= max_chunks:
                break
            if chunk['id'] not in seen_ids:
                combined.append(chunk)
                seen_ids.add(chunk['id'])

        # Sort by similarity (highest first) while preserving short-term priority
        combined.sort(key=lambda x: (
            0 if x.get('memory_type') == 'short-term' else 1,  # Short-term first
            -x.get('similarity', 0)  # Then by similarity
        ))

        return combined[:max_chunks]

    async def _get_conversation_context(
        self,
        session_id: str,
        max_messages: int = 10,
        db: AsyncSession = None
    ) -> List[Dict]:
        """Retrieve recent conversation messages for context"""
        try:
            from app.models.database_enhanced import ConversationMessage, ChatSession

            # Get session
            session_query = select(ChatSession).where(ChatSession.session_id == session_id)
            session_result = await db.execute(session_query)
            session = session_result.scalar_one_or_none()

            if not session:
                return []

            # Get recent messages
            messages_query = select(ConversationMessage).where(
                ConversationMessage.session_id == session.id
            ).order_by(ConversationMessage.created_at.desc()).limit(max_messages)

            messages_result = await db.execute(messages_query)
            messages = messages_result.scalars().all()

            # Convert to conversation history format (reverse to chronological order)
            conversation = []
            for msg in reversed(messages):
                conversation.append({
                    "role": msg.role,
                    "content": msg.content
                })

            return conversation

        except Exception as e:
            logger.error(f"Error retrieving conversation context: {e}")
            await db.rollback()
            return []

    async def _ensure_session_exists(
        self,
        session_id: str,
        user_id: Optional[uuid.UUID],
        db: AsyncSession
    ):
        """Ensure chat session exists in database"""
        try:
            from app.models.database_enhanced import ChatSession

            session_query = select(ChatSession).where(ChatSession.session_id == session_id)
            result = await db.execute(session_query)
            session = result.scalar_one_or_none()

            if not session:
                session = ChatSession(
                    session_id=session_id,
                    user_id=user_id
                )
                db.add(session)
                await db.commit()
                logger.info(f"Created new session: {session_id}")

        except Exception as e:
            logger.error(f"Error ensuring session exists: {e}")
            await db.rollback()

    async def _save_conversation_message(
        self,
        session_id: str,
        role: str,
        content: str,
        model_id: Optional[str] = None,
        model_name: Optional[str] = None,
        tokens: int = 0,
        latency_ms: float = 0,
        sources: Optional[List[Dict]] = None,
        db: AsyncSession = None
    ):
        """Save a message to the conversation history"""
        try:
            from app.models.database_enhanced import ConversationMessage, ChatSession

            # Get session
            session_query = select(ChatSession).where(ChatSession.session_id == session_id)
            session_result = await db.execute(session_query)
            session = session_result.scalar_one_or_none()

            if not session:
                logger.warning(f"Session {session_id} not found for message save")
                return

            message = ConversationMessage(
                session_id=session.id,
                role=role,
                content=content,
                model_id=model_id,
                model_name=model_name,
                total_tokens=tokens,
                latency_ms=latency_ms,
                sources=sources
            )
            db.add(message)

            # Update session last_activity
            session.last_activity = func.now()

            await db.commit()

        except Exception as e:
            logger.error(f"Error saving conversation message: {e}")
            await db.rollback()

    def _format_sources(self, chunks: List[Dict], short_term_chunks: List[Dict], relevance_threshold: float = None) -> List[Dict]:
        """Format source references with memory type indicators, filtering by relevance"""
        # Use provided threshold or fall back to settings
        threshold = relevance_threshold if relevance_threshold is not None else settings.NO_RELEVANT_DOCS_THRESHOLD

        sources = []
        seen_docs = set()
        short_term_doc_ids = {chunk['document_id'] for chunk in short_term_chunks}

        for chunk in chunks:
            doc_id = chunk['document_id']
            similarity = chunk.get('similarity', 0)

            # Only include sources that meet the relevance threshold
            if similarity < threshold:
                logger.debug(f"Filtered out source {chunk['filename']} with similarity {similarity:.2f} (below threshold {threshold})")
                continue

            if doc_id not in seen_docs:
                memory_type = chunk.get('memory_type', 'long-term')
                sources.append({
                    'id': chunk['document_id'],
                    'filename': chunk['filename'],
                    'source_type': chunk['source_type'],
                    'source_url': chunk.get('source_url'),
                    'relevance': chunk['similarity'],
                    'memory_type': memory_type,
                    'excerpt': chunk['content'][:200] + "..." if len(chunk['content']) > 200 else chunk['content']
                })
                seen_docs.add(doc_id)

        return sources

    async def _check_semantic_cache(self, query_text: str, db: AsyncSession) -> Optional[Dict]:
        """Check semantic cache for similar queries"""
        try:
            # Reuse from original RAG service
            from app.services.rag_service import rag_service
            return await rag_service._check_semantic_cache(query_text, db)
        except Exception as e:
            logger.warning(f"Error checking semantic cache: {e}")
            await db.rollback()
            return None

    async def _cache_result(
        self,
        query_text: str,
        query_embedding: List[float],
        result: Dict,
        db: AsyncSession
    ):
        """Cache query result"""
        try:
            # Reuse from original RAG service
            from app.services.rag_service import rag_service
            await rag_service._cache_result(query_text, query_embedding, result, db)
        except Exception as e:
            logger.warning(f"Error caching result: {e}")
            await db.rollback()


# Singleton instance
enhanced_rag_service = EnhancedRAGService()
