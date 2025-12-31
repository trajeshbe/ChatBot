"""
Enhanced RAG Service with Memory Hierarchy and Session Management

Memory Hierarchy:
1. Short-term memory: Session-specific documents (highest priority)
2. Long-term memory: All documents in vector store (lower priority)
3. Conversation context: Recent messages in session

This ensures recently uploaded documents in a session are prioritized.
"""

from typing import Dict, List, Optional, Any
import logging
import re  # 🆕 For URL detection
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text as sql_text, and_, func
from app.services.embedding_service import embedding_service
from app.services.intelligent_retrieval_service import intelligent_retrieval_service
from app.services.intelligent_embedding_service import intelligent_embedding_service
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
    from app.services.llm_service import llm_service
except ImportError:
    from app.services.llm_service import llm_service


class RAGService:
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
        force_rag: bool = False,  # 🆕 Force RAG search even for ai_personal/general queries
        unified_config: Optional[Dict[str, Any]] = None  # 🧠 Unified config for Brain View and all RAG parameters
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

        # 🔍 DEBUG: Log incoming project_id parameter
        logger.info(f"🔍 DEBUG [RAG Service query()]: project_id parameter = {project_id}")

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

            # 🧠 BRAIN VIEW: Extract enable_brain_view flag from unified_config
            enable_brain_view = False
            strategy_weights = {}  # Initialize to empty dict to avoid UnboundLocalError
            if unified_config:
                logger.info(f"🧠 DEBUG [RAGService.query]: unified_config received = {unified_config is not None}")
                strategy_weights = unified_config.get('strategy_weights', {})
                enable_brain_view = strategy_weights.get('enable_brain_view', False)
                if enable_brain_view:
                    logger.info("🧠 Brain View ENABLED via unified_config")
                else:
                    logger.debug("🧠 Brain View disabled (enable_brain_view=False or not in unified_config)")

            # Use provided RAG config parameters or fall back to settings
            _top_k = top_k if top_k is not None else settings.TOP_K_RESULTS
            _similarity_threshold = similarity_threshold if similarity_threshold is not None else settings.SIMILARITY_THRESHOLD
            _min_similarity_threshold = min_similarity_threshold if min_similarity_threshold is not None else settings.MIN_SIMILARITY_THRESHOLD
            _no_relevant_docs_threshold = no_relevant_docs_threshold if no_relevant_docs_threshold is not None else settings.NO_RELEVANT_DOCS_THRESHOLD
            _semantic_weight = semantic_weight if semantic_weight is not None else settings.SEMANTIC_WEIGHT
            _keyword_weight = keyword_weight if keyword_weight is not None else settings.KEYWORD_WEIGHT

            logger.info(f"🔧 RAG Config: top_k={_top_k}, sim_threshold={_similarity_threshold:.2f}, min_sim={_min_similarity_threshold:.2f}, no_relevant={_no_relevant_docs_threshold:.2f}, semantic_weight={_semantic_weight:.2f}, keyword_weight={_keyword_weight:.2f}")

            # Ensure session exists and get project_id if not already provided
            # 🔧 FIX: Don't overwrite project_id if it was passed as a parameter
            if session_id:
                await self._ensure_session_exists(session_id, user_id, db, project_id=project_id)

                # Only get project_id from session if not already provided via parameter
                if project_id is None:
                    from app.models.database_enhanced import ChatSession
                    session_query = select(ChatSession).where(ChatSession.session_id == session_id)
                    session_result = await db.execute(session_query)
                    session = session_result.scalar_one_or_none()
                    if session and session.project_id:
                        project_id = str(session.project_id)
                        logger.info(f"📁 Query scoped to project from session: {project_id}")
                else:
                    logger.info(f"📁 Query scoped to project from parameter: {project_id}")

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

            # 🆕 URL DETECTION + UI SETTINGS OVERRIDE LAYER
            # Check if query contains URL and navigation threshold is set
            # This allows UI settings to OVERRIDE LLM classification for web scraping
            track_tool("url_detection", "Check for URLs and navigation threshold")

            # URL regex pattern (matches http:// and https://)
            url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
            detected_urls = re.findall(url_pattern, query_text)

            # Extract navigation threshold from unified_config
            navigation_threshold = None
            if unified_config and 'strategy_weights' in unified_config:
                strategy_weights = unified_config.get('strategy_weights', {})
                # Navigation threshold could be stored as 'navigation_threshold' or similar
                navigation_threshold = strategy_weights.get('navigation_threshold')
                # Also check for alternative names
                if navigation_threshold is None:
                    navigation_threshold = strategy_weights.get('navigation_confidence')
                if navigation_threshold is None:
                    navigation_threshold = unified_config.get('navigation_threshold')

            # Check if we should force route to web scraper
            force_web_scraper = False
            if detected_urls and navigation_threshold is not None:
                logger.info(f"🔍 URL Detection: Found {len(detected_urls)} URL(s): {detected_urls}")
                logger.info(f"🎚️ Navigation threshold from UI: {navigation_threshold}")

                # If navigation threshold > 0.8 (or configured value), route to web scraper
                # This gives UI settings priority over LLM classification
                if navigation_threshold > 0.8:
                    force_web_scraper = True
                    logger.info(f"🌐 UI OVERRIDE: Navigation threshold ({navigation_threshold}) > 0.8 AND URL detected")
                    logger.info(f"   → Forcing route to web scraper tool (UI settings override LLM classification)")
            elif detected_urls:
                logger.info(f"🔍 URL Detection: Found {len(detected_urls)} URL(s) but no navigation threshold set in UI")

            # If forcing web scraper, trigger actual web scraping
            if force_web_scraper:
                track_tool("web_scraper_routing", f"UI override: navigation threshold ({navigation_threshold}) triggered scraper")

                logger.info(f"🌐 Triggering web scraper for URL(s): {detected_urls}")

                # Import scraper service
                from app.services.scraper_service import scraper_service

                # Scrape each detected URL
                scrape_results = []
                for url in detected_urls:
                    try:
                        logger.info(f"🔍 Scraping URL: {url}")

                        # Call scraper service with auto strategy
                        scrape_result = await scraper_service.scrape_url(
                            url=url,
                            session_id=session_id,
                            project_id=project_id,
                            scrape_prompt=query_text,  # Use the full query as scrape prompt
                            strategy="auto",  # Let scraper decide best strategy
                            db=db
                        )

                        scrape_results.append({
                            'url': url,
                            'status': 'success',
                            'document_id': scrape_result.get('document_id'),
                            'filename': scrape_result.get('filename'),
                            'content_preview': scrape_result.get('content', '')[:500] + '...' if scrape_result.get('content') else 'Processing...'
                        })

                        logger.info(f"✅ Successfully scraped: {url} → {scrape_result.get('filename')}")

                    except Exception as scrape_error:
                        logger.error(f"❌ Error scraping {url}: {scrape_error}")
                        scrape_results.append({
                            'url': url,
                            'status': 'error',
                            'error': str(scrape_error)
                        })

                # Build response with scraping results
                if any(r['status'] == 'success' for r in scrape_results):
                    successful_scrapes = [r for r in scrape_results if r['status'] == 'success']
                    answer = (
                        f"✅ I successfully scraped {len(successful_scrapes)} URL(s) based on your navigation threshold ({navigation_threshold:.2f}):\n\n"
                    )
                    for result in successful_scrapes:
                        answer += f"• {result['url']}\n  → Saved as: {result.get('filename', 'Unknown')}\n  → Preview: {result.get('content_preview', 'No preview available')}\n\n"

                    if any(r['status'] == 'error' for r in scrape_results):
                        failed_scrapes = [r for r in scrape_results if r['status'] == 'error']
                        answer += f"\n⚠️ {len(failed_scrapes)} URL(s) failed to scrape:\n"
                        for result in failed_scrapes:
                            answer += f"• {result['url']}: {result.get('error', 'Unknown error')}\n"
                else:
                    answer = (
                        f"❌ Failed to scrape the detected URL(s). Errors:\n" +
                        "\n".join([f"• {r['url']}: {r.get('error', 'Unknown error')}" for r in scrape_results])
                    )

                result = {
                    'answer': answer,
                    'sources': [],
                    'model': 'url_detection_override',
                    'model_name': 'URL Detection + UI Override + Web Scraper',
                    'tokens_used': 0,
                    'latency_ms': (time.time() - start_time) * 1000,
                    'num_sources': 0,
                    'num_short_term_sources': 0,
                    'num_long_term_sources': 0,
                    'cached': False,
                    'search_strategy': 'url_detection_override',
                    'ui_override_triggered': True,
                    'detected_urls': detected_urls,
                    'navigation_threshold': navigation_threshold,
                    'scrape_results': scrape_results,
                    'tools_used': tools_used
                }

                logger.info(f"✅ Web scraping complete (UI override mode)")
                return result

            # 🆕 FIXED ARCHITECTURE: ALWAYS classify first to detect general knowledge/AI-personal queries
            # This prevents wrong answers for questions like "What is the capital of France?"
            track_tool("query_classification", "Classify query type")
            classification = await query_classifier.classify(processed_query)
            logger.info(f"📊 Classification: {classification['query_type']} (confidence: {classification['confidence']:.2f}) - {classification['reason']}")

            # 🎚️ UI UNIFIED CONFIG OVERRIDE CHECK (EARLY BYPASS PREVENTION)
            # Check if user has set RAG weights > 0.8 in the UI
            # This OVERRIDES query classification when user explicitly wants RAG
            force_rag_override_early = False

            # 🔍 DEBUG: Log unified_config to understand why override isn't working
            logger.info(f"🔍 DEBUG: About to check UI override - unified_config exists: {unified_config is not None}")
            if unified_config:
                logger.info(f"🔍 DEBUG: unified_config type: {type(unified_config)}")
                logger.info(f"🔍 DEBUG: unified_config keys: {list(unified_config.keys()) if hasattr(unified_config, 'keys') else 'N/A'}")
                logger.info(f"🔍 DEBUG: strategy_weights in config: {'strategy_weights' in unified_config if hasattr(unified_config, '__contains__') else 'N/A'}")
                if 'strategy_weights' in unified_config:
                    logger.info(f"🔍 DEBUG: strategy_weights value: {unified_config.get('strategy_weights')}")

            if unified_config and 'strategy_weights' in unified_config:
                strategy_weights_config = unified_config.get('strategy_weights', {})
                rag_short_term_weight = strategy_weights_config.get('rag_short_term', 0.0)
                rag_long_term_weight = strategy_weights_config.get('rag_long_term', 0.0)
                rag_hybrid_weight = strategy_weights_config.get('rag_hybrid', 0.0)

                # If ANY RAG weight > 0.8, user wants to force RAG retrieval
                if rag_short_term_weight > 0.8 or rag_long_term_weight > 0.8 or rag_hybrid_weight > 0.8:
                    force_rag_override_early = True
                    logger.info(f"🎚️ UI OVERRIDE (EARLY): User set RAG weights > 0.8 (short={rag_short_term_weight:.2f}, long={rag_long_term_weight:.2f}, hybrid={rag_hybrid_weight:.2f})")
                    logger.info(f"   → Will search documents EVEN IF classified as {classification['query_type']} (UI settings override classification)")

            # If it's general knowledge or AI-personal, skip RAG entirely (UNLESS force_rag is True OR UI override is active)
            if classification['query_type'] in ['general', 'ai_personal'] and classification['confidence'] >= 0.75 and not force_rag and not force_rag_override_early:
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

            # STEP 3: Classify query and generate intelligent embeddings (hybrid: keywords + LLM)
            track_tool("query_classification", "Classify query type for optimal embedding strategy")
            logger.info(f"🔍 Classifying query to determine optimal retrieval strategy...")
            query_type_result = await intelligent_retrieval_service.classify_query(query_text)
            query_type = query_type_result['query_type']
            embedding_strategy = query_type_result['strategy']
            vector_column = query_type_result['vector_column']

            logger.info(f"📊 Query Classification:")
            logger.info(f"   Query Type: {query_type}")
            logger.info(f"   Embedding Strategy: {embedding_strategy}")
            logger.info(f"   Vector Column: {vector_column}")
            logger.info(f"   Confidence: {query_type_result.get('confidence', 0):.2%}")

            # STEP 3.5: Generate embeddings using intelligent strategy
            track_tool("embedding_generation", f"Generate {embedding_strategy} embeddings for {len(query_variations)} variation(s)")
            logger.info(f"🔍 Generating embeddings for {len(query_variations)} query variation(s) using {embedding_strategy} strategy...")
            query_embeddings = []

            for variation in query_variations:
                # Use intelligent embedding service for vision/table/code queries
                if embedding_strategy in ['vision', 'table_structure', 'numerical', 'code', 'hybrid']:
                    logger.info(f"🧠 Using IntelligentEmbeddingService ({embedding_strategy})")
                    embedding_result = await intelligent_embedding_service.get_embeddings_batch(
                        texts=[variation],
                        strategy=embedding_strategy
                    )
                    embedding = embedding_result[0]  # Returns list directly
                else:
                    # Use standard embedding service for text queries
                    logger.info(f"📝 Using standard EmbeddingService (text_semantic)")
                    embedding = await embedding_service.get_embedding(variation)

                query_embeddings.append({
                    'query': variation,
                    'embedding': embedding,
                    'strategy': embedding_strategy
                })

            # Use first (original processed query) as primary
            query_embedding = query_embeddings[0]['embedding']

            # STEP 4: Search project-scoped documents (replaces session-scoped approach)
            # All documents in the same project as the session are now accessible
            # This eliminates the need for manual session_documents associations
            project_chunks = []
            if project_id:
                # Search all documents in the project
                search_scope = f"project '{project_id}'"
                track_tool("project_document_search", f"Search {search_scope} documents (hybrid + cascading fallback)")
                logger.info(f"🔍 Searching all documents in project {project_id}")

                project_chunks = await document_service.search_similar_chunks(
                    query_embedding=query_embedding,
                    query_text=query_text,  # For keyword matching
                    top_k=_top_k * 3,  # Get more candidates for reranking
                    threshold=_similarity_threshold - 0.05,  # Slightly lower threshold for project docs
                    use_hybrid=True,  # Enable hybrid search
                    use_cascading_fallback=True,  # Enable cascading fallback
                    semantic_weight=_semantic_weight,  # UI-provided or config default
                    keyword_weight=_keyword_weight,    # UI-provided or config default
                    project_id=project_id,  # Scope to project
                    vector_column=vector_column,  # 🆕 Use intelligent embedding strategy column
                    db=db
                )

                if project_chunks:
                    logger.info(f"✅ Found {len(project_chunks)} chunks in project documents - hybrid search")
                    logger.info(f"📄 Project documents used: {list(set([c['filename'] for c in project_chunks]))}")
                else:
                    logger.info(f"⚠️ No documents found in project {project_id}")
            else:
                # Fallback: Search all documents if no project specified
                logger.info(f"⚠️ No project_id provided, searching all documents")
                track_tool("global_document_search", "Search all documents (no project filter)")

                project_chunks = await document_service.search_similar_chunks(
                    query_embedding=query_embedding,
                    query_text=query_text,
                    top_k=_top_k * 3,
                    threshold=_similarity_threshold,
                    use_hybrid=True,
                    use_cascading_fallback=True,
                    semantic_weight=_semantic_weight,
                    keyword_weight=_keyword_weight,
                    project_id=None,  # No project filter
                    vector_column=vector_column,
                    db=db
                )
                logger.info(f"Found {len(project_chunks)} chunks in global search")

            # Use project_chunks directly (no need to combine short/long-term anymore)
            combined_chunks = project_chunks
            logger.info(f"Using {len(combined_chunks)} project-scoped chunks (before reranking)")

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

                # 🎚️ UI UNIFIED CONFIG OVERRIDE CHECK
                # Check if user has set RAG weights > 0.8 in the UI
                # This OVERRIDES query classification when user explicitly wants RAG
                force_rag_override = False
                if unified_config and 'strategy_weights' in unified_config:
                    strategy_weights_config = unified_config.get('strategy_weights', {})
                    rag_short_term_weight = strategy_weights_config.get('rag_short_term', 0.0)
                    rag_long_term_weight = strategy_weights_config.get('rag_long_term', 0.0)
                    rag_hybrid_weight = strategy_weights_config.get('rag_hybrid', 0.0)

                    # If ANY RAG weight > 0.8, user wants to force RAG retrieval
                    if rag_short_term_weight > 0.8 or rag_long_term_weight > 0.8 or rag_hybrid_weight > 0.8:
                        force_rag_override = True
                        logger.info(f"🎚️ UI OVERRIDE: User set RAG weights > 0.8 (short={rag_short_term_weight:.2f}, long={rag_long_term_weight:.2f}, hybrid={rag_hybrid_weight:.2f})")
                        logger.info(f"   → Will search documents EVEN IF classified as ai_personal (UI settings override classification)")

                # If high confidence personal query BUT user didn't force RAG via UI, use direct LLM
                if classification['query_type'] == 'ai_personal' and classification['confidence'] >= 0.85 and not force_rag_override:
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
                count_query = sql_text("SELECT COUNT(*) FROM documents WHERE processing_status = 'completed'")
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

            # Step 7: Format sources (all are now project-scoped)
            sources = self._format_sources(combined_chunks, [], _no_relevant_docs_threshold)

            # All documents are now project-scoped (no short-term/long-term distinction)
            num_project = len(sources)
            num_short_term = 0  # Deprecated with project-scoped approach
            num_long_term = 0   # Deprecated with project-scoped approach

            result = {
                'answer': response['content'],
                'sources': sources,
                'model': response['model'],
                'model_name': response.get('model_name', response['model']),
                'tokens_used': response['tokens'],
                'latency_ms': (time.time() - start_time) * 1000,
                'num_sources': len(sources),
                'num_short_term_sources': num_short_term,  # Deprecated (kept for backward compatibility)
                'num_long_term_sources': num_long_term,    # Deprecated (kept for backward compatibility)
                'num_project_sources': num_project,        # New: project-scoped document count
                'session_id': session_id,
                'cached': False,
                'context_info': f"Used {num_project} project document(s)" if sources else "No documents found",
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
                    'memory_type': 'project-scoped'  # Updated from 'hierarchical' to 'project-scoped'
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

            # 🧠 Step 8.5: Assemble Brain View debug context (if enabled)
            # Extract Brain View toggle from strategy_weights (passed from frontend)
            enable_brain_view = strategy_weights.get('enable_brain_view', False)

            if enable_brain_view:
                logger.info("🧠 Brain View enabled - assembling debug context")

                # Query document processing tools used for retrieved documents
                document_processing_tools = []
                if sources and db:
                    try:
                        # sql_text already imported at module level (line 15)
                        # Get document IDs from sources
                        document_ids = [src.get('id') for src in sources if src.get('id')]

                        if document_ids:
                            # Query tool_usage_stats for document processing tools
                            tool_query = sql_text("""
                                SELECT
                                    tool_category,
                                    tool_name,
                                    operation,
                                    latency_ms,
                                    success,
                                    quality_score,
                                    error_message,
                                    metadata,
                                    created_at
                                FROM tool_usage_stats
                                WHERE tool_category IN ('document_processing', 'vision_service', 'ocr_service')
                                  AND (metadata->>'document_id')::text = ANY(:doc_ids)
                                ORDER BY created_at DESC
                                LIMIT 50
                            """)

                            tool_result = await db.execute(
                                tool_query,
                                {'doc_ids': [str(doc_id) for doc_id in document_ids]}
                            )

                            for row in tool_result:
                                metadata_json = row.metadata if hasattr(row, 'metadata') and row.metadata else {}
                                document_processing_tools.append({
                                    'tool_id': f"{row.tool_name}_{hash(str(row.created_at))}",
                                    'tool_name': row.tool_name.replace('_', ' ').title() if row.tool_name else 'Unknown',
                                    'category': row.tool_category,
                                    'operation': row.operation,
                                    'status': 'success' if row.success else 'failure',
                                    'latency_ms': round(row.latency_ms, 1) if row.latency_ms else 0,
                                    'document_id': metadata_json.get('document_id') if isinstance(metadata_json, dict) else None,
                                    'created_at': row.created_at.isoformat() if hasattr(row.created_at, 'isoformat') else str(row.created_at),
                                    'quality_score': row.quality_score,
                                    'error_message': row.error_message
                                })

                            logger.debug(f"🧠 Brain View: Found {len(document_processing_tools)} document processing tools")

                    except Exception as e:
                        logger.warning(f"Could not fetch document processing tools for Brain View: {e}")

                # Assemble complete debug context for Brain View
                result['debug_context'] = {
                    "routing_decision": {
                        "strategy": classification.get('query_type', 'unknown') if classification else 'unknown',
                        "reason": f"Query classified as {classification.get('query_type')} with {classification.get('confidence', 0):.0%} confidence" if classification else 'N/A',
                        "strategy_weights": result.get('rag_settings', {}).get('weights', {}),
                        "classification_confidence": classification.get('confidence', 0) if classification else 0
                    },
                    "conversation_history": {
                        "messages_used": 0,  # Frontend manages conversation history
                        "note": "Conversation history managed by frontend (sent with each request)"
                    },
                    "tools_executed": {
                        "query_time_tools": tools_used,  # Query execution tools (already tracked)
                        "document_processing_tools": document_processing_tools  # Tools used during document upload
                    },
                    "documents_retrieved": {
                        "total_chunks": len(sources),
                        "chunks": [
                            {
                                "document_id": src.get('id', 'unknown'),
                                "filename": src.get('filename', 'unknown'),
                                "similarity_score": src.get('relevance', 0.0),
                                "memory_type": src.get('memory_type', 'unknown'),
                                "content_preview": src.get('excerpt', '')[:200] + '...' if len(src.get('excerpt', '')) > 200 else src.get('excerpt', '')
                            }
                            for src in sources[:10]  # Limit to top 10 for performance
                        ]
                    },
                    "performance_metrics": {
                        "total_latency_ms": result.get('latency_ms', 0),
                        "breakdown": {
                            "security_check": tools_used[0]['latency_ms'] if len(tools_used) > 0 and 'Security' in tools_used[0].get('tool_name', '') else 0,
                            "embedding_generation": next((t['latency_ms'] for t in tools_used if 'Embedding' in t.get('tool_name', '')), 0),
                            "vector_search": next((t['latency_ms'] for t in tools_used if 'Search' in t.get('tool_name', '')), 0),
                            "llm_generation": next((t['latency_ms'] for t in tools_used if 'LLM' in t.get('tool_name', '') or 'Generate' in t.get('tool_name', '')), 0)
                        },
                        "model_used": result.get('model_name', result.get('model', 'unknown')),
                        "tokens_used": result.get('tokens_used', 0)
                    }
                }
            else:
                logger.debug("🧠 Brain View disabled - skipping debug context assembly")

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
                    SessionDocument.session_id == session.session_id,
                    SessionDocument.document_id == document_id
                )
            )
            existing_result = await db.execute(existing_query)
            existing = existing_result.scalar_one_or_none()

            if not existing:
                session_doc = SessionDocument(
                    session_id=session.session_id,
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
        vector_column: str = "embedding",  # 🆕 Which vector column to search
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
                SessionDocument.session_id == session.session_id
            )
            count_result = await db.execute(count_query)
            session_doc_count = count_result.scalar()

            if session_doc_count == 0:
                logger.info(f"No documents associated with session {session_id}")
                return []

            # Check chunks with embeddings for session documents (use dynamic vector_column)
            embedding_count_query = sql_text(f"""
                SELECT COUNT(*)
                FROM document_chunks dc
                JOIN session_documents sd ON dc.document_id = sd.document_id
                WHERE sd.session_id = :session_id AND dc.{vector_column} IS NOT NULL
            """)
            embedding_count_result = await db.execute(
                embedding_count_query,
                {"session_id": session.id}
            )
            embedding_count = embedding_count_result.scalar()

            logger.info(f"📊 Session {session_id}: {session_doc_count} documents, {embedding_count} chunks with {vector_column} embeddings")

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
                    vector_column=vector_column,  # 🆕 Pass vector column
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
        vector_column: str,  # 🆕 Which vector column to search
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
                        session_id, query_embedding, None, threshold, top_k, False, semantic_weight, keyword_weight, vector_column, db
                    )

                keyword_condition = " OR ".join([f"dc.content ILIKE '%{kw}%'" for kw in keywords])

                # 🆕 Use dynamic vector column (visual_embedding, table_embedding, etc.)
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
                            1 - (dc.{vector_column} <=> '{embedding_str}'::vector) as semantic_score
                        FROM document_chunks dc
                        JOIN documents d ON dc.document_id = d.id
                        JOIN session_documents sd ON d.id = sd.document_id
                        WHERE sd.session_id = :session_id
                            AND dc.{vector_column} IS NOT NULL
                    ),
                    keyword_search AS (
                        SELECT
                            dc.id,
                            CASE
                                WHEN ({keyword_condition}) THEN 1.0
                                ELSE 0.0
                            END as keyword_score
                        FROM document_chunks dc
                        JOIN documents d ON dc.document_id = d.id
                        JOIN session_documents sd ON d.id = sd.document_id
                        WHERE sd.session_id = :session_id
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
                # 🆕 Use dynamic vector column (visual_embedding, table_embedding, etc.)
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
                        1 - (dc.{vector_column} <=> '{embedding_str}'::vector) as semantic_score,
                        0.0 as keyword_score,
                        1 - (dc.{vector_column} <=> '{embedding_str}'::vector) as combined_score
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                    JOIN session_documents sd ON d.id = sd.document_id
                    WHERE sd.session_id = :session_id
                        AND dc.{vector_column} IS NOT NULL
                        AND 1 - (dc.{vector_column} <=> '{embedding_str}'::vector) > :threshold
                    ORDER BY sd.priority DESC, dc.{vector_column} <=> '{embedding_str}'::vector
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
        db: AsyncSession,
        project_id: Optional[str] = None
    ):
        """Ensure chat session exists in database"""
        try:
            from app.models.database_enhanced import ChatSession

            session_query = select(ChatSession).where(ChatSession.session_id == session_id)
            result = await db.execute(session_query)
            session = result.scalar_one_or_none()

            if not session:
                # 🔧 FIX: Create session with project_id
                session_data = {
                    "session_id": session_id,
                    "user_id": user_id
                }

                # Add project_id if provided
                if project_id:
                    try:
                        session_data["project_id"] = uuid.UUID(project_id)
                        logger.info(f"Creating new session with project_id: {project_id}")
                    except (ValueError, AttributeError):
                        logger.warning(f"Invalid project_id format: {project_id}, creating session without project")

                session = ChatSession(**session_data)
                db.add(session)
                await db.commit()
                logger.info(f"Created new session: {session_id}" + (f" (project: {project_id})" if project_id else ""))
            elif project_id and not session.project_id:
                # 🔧 FIX: Update existing session with project_id if it doesn't have one
                try:
                    session.project_id = uuid.UUID(project_id)
                    await db.commit()
                    logger.info(f"Updated session {session_id} with project_id: {project_id}")
                except (ValueError, AttributeError):
                    logger.warning(f"Invalid project_id format: {project_id}")

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
rag_service = RAGService()
