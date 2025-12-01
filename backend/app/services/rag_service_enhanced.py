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
from app.services.security_guardrails import check_query_safety  # 🆕 Security filters
from app.services.reranker_service import rerank_chunks  # 🆕 Cross-encoder reranker
from app.services.query_reformulation_service import reformulate_query  # 🆕 Query reformulation
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
        project_id: Optional[str] = None,  # 🆕 Project-based filtering for RAG queries
        conversation_history: Optional[List[Dict]] = None,
        use_cache: bool = True,
        model_id: Optional[str] = None,
        db: AsyncSession = None,
        # RAG configuration parameters (override defaults from settings)
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        min_similarity_threshold: Optional[float] = None,
        no_relevant_docs_threshold: Optional[float] = None,
        semantic_weight: Optional[float] = None,
        keyword_weight: Optional[float] = None,
        force_rag: bool = False  # 🆕 Force RAG search even for ai_personal/general queries
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

        # 🆕 Tool Usage Tracking - Record which tools/steps were used and in what order
        tools_used = []
        last_tool_time = start_time  # Track time of last tool for calculating deltas

        def track_tool(tool_name: str, details: Optional[str] = None, success: bool = True):
            """
            Helper to track tool usage in frontend-compatible format

            Frontend expects:
            - tool_id: unique identifier (e.g., "security_check_001")
            - tool_name: display name (e.g., "Security Check")
            - status: 'success' | 'failure'
            - latency_ms: execution time since last tool
            - order: execution order (1-indexed)
            """
            nonlocal last_tool_time
            current_time = time.time()

            # Calculate latency since last tool (delta timing)
            latency_ms = (current_time - last_tool_time) * 1000
            last_tool_time = current_time

            # Create tool entry in frontend-compatible format
            tool_entry = {
                'tool_id': f"{tool_name}_{len(tools_used) + 1:03d}",  # Unique ID
                'tool_name': tool_name.replace('_', ' ').title(),  # Human-readable name
                'status': 'success' if success else 'failure',
                'latency_ms': round(latency_ms, 1),
                'order': len(tools_used) + 1  # 1-indexed order
            }

            tools_used.append(tool_entry)
            logger.debug(
                f"🔧 Tool {'✅' if success else '❌'}: {tool_name} "
                f"(order={tool_entry['order']}, latency={latency_ms:.1f}ms)" +
                (f" - {details}" if details else "")
            )

        try:
            # 🆕 STEP 0: Security check - detect prompt injection and malicious queries
            track_tool("security_check", "Query safety validation")
            security_check = check_query_safety(query_text, strict_mode=False)

            if not security_check['is_safe']:
                logger.warning(
                    f"🚨 SECURITY ALERT: Unsafe query detected! "
                    f"Threat level: {security_check['threat_level']}, "
                    f"Risk score: {security_check['risk_score']}, "
                    f"Threats: {security_check['threats_detected']}"
                )
                return {
                    'answer': (
                        "⚠️ Your query was flagged as potentially unsafe and cannot be processed. "
                        "Please rephrase your question without attempting to override system instructions "
                        "or inject commands."
                    ),
                    'sources': [],
                    'num_sources': 0,
                    'cached': False,
                    'model_used': 'security_filter',
                    'latency_ms': (time.time() - start_time) * 1000,
                    'security_alert': True,
                    'threat_level': security_check['threat_level'],
                    'risk_score': security_check['risk_score'],
                    'recommendation': security_check['recommendation']
                }

            # Log if any threats detected but still safe to proceed
            if security_check['risk_score'] > 0:
                logger.info(
                    f"⚠️ Low-risk query detected: "
                    f"Risk score: {security_check['risk_score']}, "
                    f"Threat level: {security_check['threat_level']}"
                )

            # Use provided RAG config parameters or fall back to settings
            _top_k = top_k if top_k is not None else settings.TOP_K_RESULTS
            _similarity_threshold = similarity_threshold if similarity_threshold is not None else settings.SIMILARITY_THRESHOLD
            _min_similarity_threshold = min_similarity_threshold if min_similarity_threshold is not None else settings.MIN_SIMILARITY_THRESHOLD
            _no_relevant_docs_threshold = no_relevant_docs_threshold if no_relevant_docs_threshold is not None else settings.NO_RELEVANT_DOCS_THRESHOLD
            _semantic_weight = semantic_weight if semantic_weight is not None else settings.SEMANTIC_WEIGHT
            _keyword_weight = keyword_weight if keyword_weight is not None else settings.KEYWORD_WEIGHT

            logger.info(f"🔧 RAG Config: top_k={_top_k}, sim_threshold={_similarity_threshold:.2f}, min_sim={_min_similarity_threshold:.2f}, no_relevant={_no_relevant_docs_threshold:.2f}, semantic_weight={_semantic_weight:.2f}, keyword_weight={_keyword_weight:.2f}")

            # Ensure session exists and get project_id if session-based
            project_id = None
            if session_id:
                await self._ensure_session_exists(session_id, user_id, db)

                # Get project_id from session to scope retrieval
                from app.models.database_enhanced import ChatSession
                session_query = select(ChatSession).where(ChatSession.session_id == session_id)
                session_result = await db.execute(session_query)
                session = session_result.scalar_one_or_none()
                if session and session.project_id:
                    project_id = str(session.project_id)
                    logger.info(f"📁 Query scoped to project: {project_id}")

            # STEP 0: Preprocess query for better retrieval and classification
            track_tool("query_preprocessing", "Normalize and extract proper nouns")
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

            # 🆕 FIXED ARCHITECTURE: ALWAYS classify first to detect general knowledge/AI-personal queries
            # This prevents wrong answers for questions like "What is the capital of France?"
            track_tool("query_classification", "Classify query type")
            classification = await query_classifier.classify(processed_query)
            logger.info(f"📊 Classification: {classification['query_type']} (confidence: {classification['confidence']:.2f}) - {classification['reason']}")

            # If it's general knowledge or AI-personal, skip RAG entirely (UNLESS force_rag is True)
            if classification['query_type'] in ['general', 'ai_personal'] and classification['confidence'] >= 0.75 and not force_rag:
                track_tool("direct_llm", f"Classified as {classification['query_type']} - skipping RAG")
                logger.info(f"✨ {classification['query_type']} query detected → using direct LLM (no documents needed)")

                system_message = (
                    "You are a helpful AI assistant. " +
                    ("Answer this general knowledge question accurately and concisely." if classification['query_type'] == 'general'
                     else "Answer questions about yourself naturally and accurately. You are an enterprise RAG chatbot that can answer questions using uploaded documents.")
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
                    'context_info': f'Direct LLM ({classification["query_type"]} query)',
                    'query_classification': classification['query_type'],
                    'classification_confidence': classification['confidence'],
                    'tools_used': tools_used,
                    'quality_metrics': {
                        'quality_level': 'N/A',
                        'rag_score': None,
                        'note': f'Direct LLM response ({classification["query_type"]} query)',
                        'classification_type': classification['query_type'],
                        'classification_confidence': classification['confidence']
                    }
                }

                # Save to conversation history
                if session_id:
                    await self._save_conversation_message(session_id=session_id, role='user', content=query_text, db=db)
                    await self._save_conversation_message(
                        session_id=session_id, role='assistant', content=response['content'],
                        model_id=response['model'], model_name=response.get('model_name'),
                        tokens=response.get('tokens', 0), latency_ms=(time.time() - start_time) * 1000,
                        sources=[], db=db
                    )

                return result

            # Otherwise, proceed with RAG retrieval
            if force_rag and classification['query_type'] in ['general', 'ai_personal']:
                logger.info(f"⚠️ Query classified as {classification['query_type']}, but FORCE_RAG is enabled → will search documents anyway")

            logger.info(f"🔍 Proceeding with RAG retrieval for {classification['query_type']} query{' (FORCED)' if force_rag else ''}")

            # STEP 2: Check semantic cache first (use ORIGINAL query for cache key)
            if use_cache:
                track_tool("semantic_cache_check", "Check Redis for cached results")
                cached_result = await self._check_semantic_cache(query_text, db)
                if cached_result:
                    track_tool("cache_hit", "Returned cached result")
                    logger.info(f"✅ Cache hit for query in session {session_id}")
                    cached_result['cached'] = True
                    cached_result['latency_ms'] = (time.time() - start_time) * 1000
                    cached_result['tools_used'] = tools_used  # 🆕 Include tool usage even for cached results
                    return cached_result

            # 🆕 STEP 2.5: Query Reformulation for Improved Recall
            # Generate multiple query variations to catch documents with different terminology
            track_tool("query_reformulation", "Generate query variations (acronyms + synonyms)")
            query_variations = reformulate_query(
                query=processed_query,
                include_acronyms=True,
                include_synonyms=True,
                use_llm=False  # Disabled for speed (can enable for complex queries)
            )

            if len(query_variations) > 1:
                track_tool("multi_query", f"Generated {len(query_variations)} query variations")
                logger.info(
                    f"🔀 Query reformulation: '{processed_query}' → {len(query_variations)} variations: "
                    f"{[q[:50] + '...' if len(q) > 50 else q for q in query_variations]}"
                )

            # STEP 3: Generate embeddings for ALL query variations
            track_tool("embedding_generation", f"Generate embeddings for {len(query_variations)} variation(s)")
            logger.info(f"🔍 Generating embeddings for {len(query_variations)} query variation(s)")
            query_embeddings = []
            for variation in query_variations:
                embedding = await embedding_service.get_embedding(variation)
                query_embeddings.append({
                    'query': variation,
                    'embedding': embedding
                })

            # Use first (original processed query) as primary
            query_embedding = query_embeddings[0]['embedding']

            # STEP 4: Search short-term memory first (session documents)
            short_term_chunks = []
            if session_id:
                track_tool("short_term_memory_search", "Search session-specific documents (hybrid)")
                short_term_chunks = await self._search_session_documents(
                    session_id=session_id,
                    query_embedding=query_embedding,
                    query_text=query_text,  # For keyword matching
                    top_k=_top_k,
                    threshold=_similarity_threshold - 0.05,  # Slightly lower threshold for session docs
                    use_hybrid=True,  # Enable hybrid search
                    use_cascading_fallback=True,  # Enable cascading fallback
                    semantic_weight=_semantic_weight,  # UI-provided or config default
                    keyword_weight=_keyword_weight,    # UI-provided or config default
                    db=db
                )
                if short_term_chunks:
                    logger.info(f"✅ Found {len(short_term_chunks)} chunks in short-term memory (session documents) - hybrid search")
                    logger.info(f"📄 Session documents used: {list(set([c['filename'] for c in short_term_chunks]))}")
                else:
                    logger.info(f"⚠️ No session-specific documents found for session {session_id}")

            # Step 3: Search long-term memory (all documents) using hybrid search with cascading fallback
            # If project_id exists, scope to project documents only
            search_scope = f"project {project_id}" if project_id else "all documents"
            track_tool("long_term_memory_search", f"Search {search_scope} (hybrid + cascading fallback)")
            long_term_chunks = await document_service.search_similar_chunks(
                query_embedding=query_embedding,
                query_text=query_text,  # For keyword matching
                top_k=_top_k,
                threshold=_similarity_threshold,
                use_hybrid=True,  # Enable hybrid search
                use_cascading_fallback=True,  # Enable cascading fallback
                semantic_weight=_semantic_weight,  # UI-provided or config default
                keyword_weight=_keyword_weight,    # UI-provided or config default
                project_id=project_id,  # Scope to project if provided
                db=db
            )
            logger.info(f"Found {len(long_term_chunks)} chunks in long-term memory - hybrid search with fallback")

            # Step 4: Combine and deduplicate results (short-term has priority)
            combined_chunks = self._combine_memory_results(
                short_term_chunks,
                long_term_chunks,
                max_chunks=_top_k * 3  # 🆕 Get 3x candidates for reranking
            )
            logger.info(f"Combined to {len(combined_chunks)} total chunks (before reranking)")

            # 🆕 Step 4.5: Cross-Encoder Reranking for State-of-the-Art Accuracy
            # Two-stage retrieval: Fast vector search → Precise cross-encoder reranking
            if combined_chunks and len(combined_chunks) > _top_k:
                try:
                    track_tool("cross_encoder_reranking", f"Rerank {len(combined_chunks)} candidates → top {_top_k}")
                    logger.info(f"🔄 Applying cross-encoder reranking to {len(combined_chunks)} candidates...")

                    # Rerank using cross-encoder (balances speed and accuracy)
                    reranked_chunks = rerank_chunks(
                        query=query_text,
                        chunks=combined_chunks,
                        top_k=_top_k,
                        model_name="balanced",  # "fast", "balanced", or "accurate"
                        use_fusion=False  # Pure reranking for maximum accuracy
                    )

                    if reranked_chunks:
                        combined_chunks = reranked_chunks
                        logger.info(
                            f"✅ Reranking complete → {len(combined_chunks)} top chunks selected "
                            f"(avg rerank_score: {sum(c.get('rerank_score', 0) for c in combined_chunks) / len(combined_chunks):.3f})"
                        )

                except Exception as e:
                    logger.warning(f"⚠️ Reranking failed: {e} - using vector similarity ranking")
                    # Fallback to vector similarity ranking
                    combined_chunks = combined_chunks[:_top_k]
            else:
                # Not enough candidates for reranking, or already at target size
                combined_chunks = combined_chunks[:_top_k]

            # Step 5: Get conversation context if session_id provided
            conversation_context = []
            if session_id:
                conversation_context = await self._get_conversation_context(
                    session_id=session_id,
                    max_messages=10,
                    db=db
                )
                logger.info(f"Retrieved {len(conversation_context)} messages from conversation history")

            # 🆕 Step 5.5: Evaluate RAG quality BEFORE deciding on response strategy
            # Calculate quick quality estimate from retrieved chunks
            if combined_chunks:
                avg_similarity = sum(c.get('similarity', 0) for c in combined_chunks) / len(combined_chunks)
                logger.info(f"📊 Quick quality estimate: avg_similarity={avg_similarity:.3f}, num_chunks={len(combined_chunks)}")

                # Good quality if we have chunks with decent similarity
                has_good_quality = (len(combined_chunks) >= 2 and avg_similarity >= 0.4) or \
                                 (len(combined_chunks) >= 1 and avg_similarity >= 0.6)
            else:
                avg_similarity = 0.0
                has_good_quality = False
                logger.info(f"📊 No chunks found - quality is low")

            # Decision: Use RAG if quality is good, otherwise classify and decide
            classification = None
            if not has_good_quality:
                # Quality is low - classify query to see if it's a personal question
                logger.info(f"⚠️ RAG quality is low (similarity={avg_similarity:.3f}, chunks={len(combined_chunks)}) - running classification")
                classification = await query_classifier.classify(processed_query)
                logger.info(f"📊 Classification: {classification['query_type']} (confidence: {classification['confidence']:.2f})")

                # If high confidence personal query, use direct LLM
                if classification['query_type'] == 'ai_personal' and classification['confidence'] >= 0.85:
                    track_tool("query_classification", f"Classified as {classification['query_type']}")
                    track_tool("direct_llm", "High confidence AI-personal query")
                    logger.info("✨ High confidence AI-personal query with low RAG quality → using direct LLM")

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
                        'context_info': 'Direct LLM (AI-personal query, low RAG quality)',
                        'query_classification': classification['query_type'],
                        'classification_confidence': classification['confidence'],
                        'tools_used': tools_used,  # 🆕 Include tool usage tracking
                        'quality_metrics': {
                            'quality_level': 'N/A',
                            'rag_score': None,
                            'note': 'Direct LLM response (AI-personal query)',
                            'classification_type': classification['query_type'],
                            'classification_confidence': classification['confidence']
                        }
                    }

                    # Save to conversation history
                    if session_id:
                        await self._save_conversation_message(session_id=session_id, role='user', content=query_text, db=db)
                        await self._save_conversation_message(
                            session_id=session_id, role='assistant', content=response['content'],
                            model_id=response['model'], model_name=response.get('model_name'),
                            tokens=response.get('tokens', 0), latency_ms=(time.time() - start_time) * 1000,
                            sources=[], db=db
                        )

                    return result
                else:
                    # Not a personal query or low confidence - proceed with RAG despite low quality
                    logger.info(f"⚠️ Low RAG quality but not a personal query - proceeding with RAG + warning")
            else:
                # Good quality - proceed with RAG, skip classification for now
                logger.info(f"✅ Good RAG quality (similarity={avg_similarity:.3f}, chunks={len(combined_chunks)}) - proceeding with RAG")
                # Classification will be added later for metrics reporting
                classification = await query_classifier.classify(processed_query)

            # Step 6: Generate response with context
            if combined_chunks or conversation_context:
                track_tool("llm_generation_with_context", f"{len(combined_chunks)} chunks + {len(conversation_context)} messages")
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

                track_tool("llm_generation_no_context", "Generate response without context")
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
                'classification_confidence': classification['confidence'],  # Include confidence score
                # 🆕 Tool Usage Tracking - shows which tools were used and in what order
                'tools_used': tools_used,
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
            # Always attempt to add quality metrics (even if no chunks found)
            if combined_chunks:  # Full evaluation if we have context chunks
                try:
                    track_tool("quality_evaluation", "Calculate RAGAS metrics")
                    quality_metrics = await quality_metrics_service.evaluate_response(
                        query=query_text,
                        answer=response['content'],
                        context_chunks=combined_chunks
                    )
                    # Add classification info to quality metrics
                    quality_metrics['classification_type'] = classification['query_type']
                    quality_metrics['classification_confidence'] = classification['confidence']
                    result['quality_metrics'] = quality_metrics
                    logger.info(f"📊 Quality: {quality_metrics.get('quality_level', 'unknown')} (score: {quality_metrics.get('rag_score', 0):.2f})")

                    # Log warning if quality is poor
                    if quality_metrics.get('rag_score', 1) < 0.4:
                        logger.warning(f"⚠️ LOW QUALITY RESPONSE detected! Score: {quality_metrics.get('rag_score', 0):.2f}")
                        logger.warning(quality_metrics_service.generate_quality_report(quality_metrics))
                except Exception as e:
                    logger.error(f"Error calculating quality metrics: {e}")
                    # Provide basic metrics on error
                    result['quality_metrics'] = {
                        'quality_level': 'Error',
                        'rag_score': None,
                        'note': f'Error calculating metrics: {str(e)[:100]}',
                        'classification_type': classification['query_type'],
                        'classification_confidence': classification['confidence']
                    }
            else:
                # No chunks found - provide basic quality metrics
                logger.info("📊 No chunks found - providing basic quality metrics")
                result['quality_metrics'] = {
                    'quality_level': 'No Context',
                    'rag_score': 0.0,
                    'note': 'No relevant documents found for this query',
                    'classification_type': classification['query_type'],
                    'classification_confidence': classification['confidence'],
                    'num_documents_searched': 0
                }

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
        semantic_weight: Optional[float] = None,
        keyword_weight: Optional[float] = None,
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

            # Set weight defaults if not provided
            _semantic_weight = semantic_weight if semantic_weight is not None else settings.SEMANTIC_WEIGHT
            _keyword_weight = keyword_weight if keyword_weight is not None else settings.KEYWORD_WEIGHT

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
                    semantic_weight=_semantic_weight,
                    keyword_weight=_keyword_weight,
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
        semantic_weight: float,
        keyword_weight: float,
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
                        session_id, query_embedding, None, threshold, top_k, False, semantic_weight, keyword_weight, db
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
                        (ss.semantic_score * :semantic_weight + COALESCE(ks.keyword_score, 0) * :keyword_weight) as combined_score
                    FROM semantic_search ss
                    LEFT JOIN keyword_search ks ON ss.id = ks.id
                    WHERE (ss.semantic_score * :semantic_weight + COALESCE(ks.keyword_score, 0) * :keyword_weight) > :threshold
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
                    "limit": top_k,
                    "semantic_weight": semantic_weight,
                    "keyword_weight": keyword_weight
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
