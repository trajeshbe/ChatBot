"""
High-level RAG Pipeline Orchestrator

Implements a robust RAG pipeline with:
- Query normalization and embedding
- Semantic caching
- Hybrid retrieval (semantic + lexical)
- Memory hierarchy (session → all documents)
- LLM-based reranking
- Grounded answer generation
- Self-critique and refinement
- Observability and metrics

Stages (graph-style):
1. normalize_query
2. embed_query
3. semantic_cache_check
4. hybrid_retrieval
5. rerank_candidates
6. generate_initial_answer
7. self_critique
8. refine_or_finalize

Everything is driven by RagState, which can be easily ported to LangGraph / Prefect.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_rag_settings
from .embeddings import embed_query
from .retrieval import retrieve_hybrid
from .reranker import rerank_with_ollama, Chunk
from .semantic_cache import get_cached_answer, store_answer, generate_config_hash
from .llm import generate_grounded_answer, critique_answer, refine_answer_with_critique
from .observability import (
    timed,
    log_rag_request,
    log_retrieval_results,
    log_rerank_results,
    log_cache_event,
    log_critique_results,
    log_error,
    get_metrics_collector
)

logger = logging.getLogger(__name__)


@dataclass
class CritiqueResult:
    """Result of self-critique / Self-RAG style check"""
    is_grounded: bool
    is_complete: bool
    issues: List[str] = field(default_factory=list)
    raw_critique: str = ""


@dataclass
class RagState:
    """State object that flows through the RAG pipeline"""

    # Input
    user_query: str
    session_id: Optional[str] = None
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    model_name: Optional[str] = None  # Specific model to use
    extra_meta: Dict[str, Any] = field(default_factory=dict)

    # Database session (passed through)
    db: Optional[AsyncSession] = None

    # Derived
    normalized_query: str = ""
    query_embedding: Optional[List[float]] = None

    # Retrieval
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    reranked_chunks: List[Dict[str, Any]] = field(default_factory=list)

    # Answers
    initial_answer: Optional[str] = None
    final_answer: Optional[str] = None
    citations: List[Dict[str, Any]] = field(default_factory=list)

    # Critique
    critique_result: Optional[CritiqueResult] = None

    # Flags
    cache_hit: bool = False
    refined: bool = False
    rerank_used: bool = False

    # Telemetry
    timings_ms: Dict[str, float] = field(default_factory=dict)

    # Internal / debug
    debug_info: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Stage 1: normalize_query
# ============================================================================

def normalize_query(state: RagState, settings) -> RagState:
    """
    Clean up user query: trimming, lowercasing where appropriate, etc.

    Can be extended to:
    - Expand domain acronyms
    - Detect language
    - Strip noise
    """
    q = state.user_query.strip()
    # Basic normalization
    state.normalized_query = q
    return state


# ============================================================================
# Stage 2: embed_query
# ============================================================================

@timed("embed_query")
async def embed_query_stage(state: RagState, settings) -> RagState:
    """Compute embedding for the normalized query"""
    try:
        state.query_embedding = await embed_query(
            state.normalized_query,
            normalize=True
        )
        logger.debug(f"Generated embedding (dim: {len(state.query_embedding)})")
    except Exception as e:
        log_error("embed_query", e, state.user_query)
        raise

    return state


# ============================================================================
# Stage 3: semantic_cache_check
# ============================================================================

@timed("semantic_cache_check")
async def semantic_cache_check(state: RagState, settings) -> RagState:
    """Check Redis-based semantic cache for a near-identical question with versioning"""
    if not settings.ENABLE_SEMANTIC_CACHE or state.query_embedding is None:
        return state

    try:
        # 🆕 Generate config hash for versioned cache keys
        config_hash = generate_config_hash(
            semantic_weight=settings.SEMANTIC_WEIGHT,
            keyword_weight=settings.KEYWORD_WEIGHT,
            top_k=settings.TOP_K_RESULTS,
            similarity_threshold=settings.SIMILARITY_THRESHOLD,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )

        # 🆕 Include model_name and config_hash for cache versioning
        cached = await get_cached_answer(
            embedding=state.query_embedding,
            tenant_id=state.tenant_id,
            similarity_threshold=settings.CACHE_SIMILARITY_THRESHOLD,
            model_name=settings.EMBEDDING_MODEL,  # Model name for versioning
            config_hash=config_hash  # Config hash for invalidation
        )

        if cached is None:
            log_cache_event("miss")
            return state

        # Cache hit: short-circuit most of the pipeline
        state.cache_hit = True
        state.final_answer = cached.answer
        state.citations = cached.citations
        state.debug_info["cache_match_score"] = cached.similarity

        log_cache_event("hit", cached.similarity)
        logger.info(f"Cache hit with similarity {cached.similarity:.4f} (versioned)")

    except Exception as e:
        logger.warning(f"Error in cache check: {e}")
        # Continue without cache on error

    return state


# ============================================================================
# Stage 4: hybrid_retrieval
# ============================================================================

@timed("hybrid_retrieval")
async def hybrid_retrieval_stage(state: RagState, settings) -> RagState:
    """
    Run hybrid retrieval (semantic + lexical) against Postgres+pgvector.

    Implements memory hierarchy:
    1. Try session documents first (short-term memory)
    2. Fall back to all documents (long-term memory)
    """
    if state.cache_hit:
        return state  # Skip retrieval if cache already satisfied the request

    if not state.db:
        raise ValueError("Database session is required for retrieval")

    try:
        raw_results = await retrieve_hybrid(
            query=state.normalized_query,
            query_embedding=state.query_embedding,
            top_k=settings.RETRIEVAL_CANDIDATES,
            alpha=settings.RETRIEVAL_ALPHA,
            db=state.db,
            session_id=state.session_id,
            tenant_id=state.tenant_id
        )

        state.candidates = raw_results

        if raw_results:
            log_retrieval_results(
                query=state.normalized_query,
                num_results=len(raw_results),
                top_score=raw_results[0].get("final_score", 0.0),
                search_type="hybrid",
                session_scoped=state.session_id is not None
            )

    except Exception as e:
        log_error("hybrid_retrieval", e, state.user_query)
        raise

    return state


# ============================================================================
# Stage 5: rerank_candidates
# ============================================================================

@timed("rerank")
async def rerank_stage(state: RagState, settings) -> RagState:
    """Optional reranking of candidates using an Ollama model"""
    if state.cache_hit:
        return state

    if not settings.ENABLE_RERANKER or not state.candidates:
        state.reranked_chunks = state.candidates
        return state

    try:
        state.rerank_used = True

        top_score_before = state.candidates[0].get("final_score", 0.0) if state.candidates else 0.0

        reranked = await rerank_with_ollama(
            query=state.normalized_query,
            candidates=state.candidates,
            model_name=settings.RERANK_MODEL_NAME,
            top_k=settings.RERANK_TOP_K
        )

        state.reranked_chunks = reranked

        if reranked:
            top_score_after = reranked[0].get("final_score", 0.0)
            log_rerank_results(
                input_count=len(state.candidates),
                output_count=len(reranked),
                top_score_before=top_score_before,
                top_score_after=top_score_after
            )

    except Exception as e:
        logger.warning(f"Error in reranking: {e}. Using original candidates.")
        state.reranked_chunks = state.candidates[:settings.RERANK_TOP_K]

    return state


# ============================================================================
# Stage 6: generate_initial_answer
# ============================================================================

@timed("generate_initial_answer")
async def generate_initial_answer_stage(state: RagState, settings) -> RagState:
    """Generate first draft answer grounded in retrieved chunks"""
    if state.cache_hit:
        return state

    if not state.reranked_chunks:
        # No context found
        state.initial_answer = (
            "I couldn't find relevant information in the documents to answer this question. "
            "Please try rephrasing your question or upload relevant documents."
        )
        state.citations = []
        return state

    try:
        # Determine model to use
        model_name = state.model_name or settings.GENERATION_MODEL_NAME

        answer, citations = await generate_grounded_answer(
            query=state.normalized_query,
            chunks=state.reranked_chunks,
            model_name=model_name,
            temperature=settings.GENERATION_TEMPERATURE,
            max_tokens=settings.GENERATION_MAX_TOKENS
        )

        state.initial_answer = answer
        state.citations = citations

    except Exception as e:
        log_error("generate_initial_answer", e, state.user_query)
        raise

    return state


# ============================================================================
# Stage 7: self_critique
# ============================================================================

@timed("self_critique")
async def self_critique_stage(state: RagState, settings) -> RagState:
    """Run Self-RAG style critique on the initial answer"""
    if state.cache_hit:
        return state

    if not settings.ENABLE_SELF_CRITIQUE:
        return state

    if not state.initial_answer:
        return state

    try:
        model_name = state.model_name or settings.CRITIQUE_MODEL_NAME

        critique = await critique_answer(
            query=state.normalized_query,
            chunks=state.reranked_chunks,
            answer=state.initial_answer,
            model_name=model_name
        )

        state.critique_result = CritiqueResult(
            is_grounded=critique.get("is_grounded", True),
            is_complete=critique.get("is_complete", True),
            issues=critique.get("issues", []),
            raw_critique=critique.get("raw_critique", "")
        )

        log_critique_results(
            is_grounded=state.critique_result.is_grounded,
            is_complete=state.critique_result.is_complete,
            num_issues=len(state.critique_result.issues)
        )

    except Exception as e:
        logger.warning(f"Error in critique: {e}. Skipping critique.")
        # Continue without critique on error

    return state


# ============================================================================
# Stage 8: refine_or_finalize
# ============================================================================

@timed("refine_or_finalize")
async def refine_or_finalize_stage(state: RagState, settings) -> RagState:
    """Decide whether to accept initial answer or refine based on critique"""
    if state.cache_hit:
        # Answer already final
        state.final_answer = state.final_answer or state.initial_answer
        return state

    # If no critique or self-critique disabled, accept initial
    if not settings.ENABLE_SELF_CRITIQUE or state.critique_result is None:
        state.final_answer = state.initial_answer
        return state

    cr = state.critique_result

    # Simple heuristic: refine if not grounded OR incomplete
    if not cr.is_grounded or not cr.is_complete:
        try:
            state.refined = True

            model_name = state.model_name or settings.GENERATION_MODEL_NAME

            refined_answer, refined_citations = await refine_answer_with_critique(
                query=state.normalized_query,
                chunks=state.reranked_chunks,
                initial_answer=state.initial_answer,
                critique=cr,
                model_name=model_name,
                temperature=settings.REFINE_TEMPERATURE,
                max_tokens=settings.GENERATION_MAX_TOKENS
            )

            state.final_answer = refined_answer
            state.citations = refined_citations or state.citations

            logger.info("Answer refined based on critique")

        except Exception as e:
            logger.warning(f"Error in refinement: {e}. Using initial answer.")
            state.final_answer = state.initial_answer

        return state

    # Critique says it's grounded and complete → accept initial
    state.final_answer = state.initial_answer
    return state


# ============================================================================
# Final orchestration function
# ============================================================================

async def rag_answer(
    user_query: str,
    db: AsyncSession,
    session_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    model_name: Optional[str] = None,
    extra_meta: Optional[Dict[str, Any]] = None
) -> Tuple[str, List[Dict[str, Any]], RagState]:
    """
    Top-level function used by FastAPI / GraphQL to answer a question.

    Returns:
        final_answer: str
        citations: list of dicts (doc_id, chunk_id, etc.)
        state: RagState (for debugging / logging)
    """
    settings = get_rag_settings()
    extra_meta = extra_meta or {}

    state = RagState(
        user_query=user_query,
        session_id=session_id,
        tenant_id=tenant_id,
        user_id=user_id,
        model_name=model_name,
        extra_meta=extra_meta,
        db=db
    )

    error_occurred = False

    try:
        # Run stages in order; each can short-circuit where appropriate
        state = normalize_query(state, settings)
        state = await embed_query_stage(state, settings)
        state = await semantic_cache_check(state, settings)

        if not state.cache_hit:
            state = await hybrid_retrieval_stage(state, settings)
            state = await rerank_stage(state, settings)
            state = await generate_initial_answer_stage(state, settings)
            state = await self_critique_stage(state, settings)
            state = await refine_or_finalize_stage(state, settings)

        # Ensure final_answer is set
        if state.final_answer is None:
            state.final_answer = state.initial_answer or (
                "I'm sorry, I couldn't generate an answer for this question."
            )

        # Write to semantic cache on miss (with versioning)
        if (not state.cache_hit and
            settings.ENABLE_SEMANTIC_CACHE and
            state.query_embedding):
            try:
                # 🆕 Generate config hash for versioned cache storage
                config_hash = generate_config_hash(
                    semantic_weight=settings.SEMANTIC_WEIGHT,
                    keyword_weight=settings.KEYWORD_WEIGHT,
                    top_k=settings.TOP_K_RESULTS,
                    similarity_threshold=settings.SIMILARITY_THRESHOLD,
                    chunk_size=settings.CHUNK_SIZE,
                    chunk_overlap=settings.CHUNK_OVERLAP
                )

                await store_answer(
                    embedding=state.query_embedding,
                    tenant_id=state.tenant_id,
                    normalized_query=state.normalized_query,
                    answer=state.final_answer,
                    citations=state.citations,
                    ttl_seconds=settings.CACHE_TTL_SECONDS,
                    model_name=settings.EMBEDDING_MODEL,  # 🆕 Model name for versioning
                    config_hash=config_hash  # 🆕 Config hash for invalidation
                )
                log_cache_event("store")
            except Exception as exc:
                # Avoid failing the request because of cache errors
                state.debug_info["cache_store_error"] = str(exc)
                logger.warning(f"Error storing to cache: {exc}")

    except Exception as e:
        error_occurred = True
        log_error("pipeline", e, state.user_query, {
            "session_id": session_id,
            "tenant_id": tenant_id
        })

        # Return a graceful error message
        state.final_answer = (
            "I encountered an error while processing your question. "
            "Please try again or contact support if the issue persists."
        )
        state.citations = []

        # Re-raise for proper error handling upstream
        raise

    finally:
        # Log structured info for observability
        try:
            log_rag_request(
                user_query=state.user_query,
                normalized_query=state.normalized_query,
                session_id=state.session_id,
                tenant_id=state.tenant_id,
                user_id=state.user_id,
                cache_hit=state.cache_hit,
                refined=state.refined,
                rerank_used=state.rerank_used,
                timings_ms=state.timings_ms,
                num_candidates=len(state.candidates),
                num_used_chunks=len(state.reranked_chunks),
                model_name_used=state.model_name or settings.GENERATION_MODEL_NAME,
                extra_meta=state.extra_meta
            )

            # Record metrics
            metrics = get_metrics_collector()
            metrics.record_request(
                cache_hit=state.cache_hit,
                refined=state.refined,
                error=error_occurred,
                timings=state.timings_ms
            )
        except Exception as e:
            logger.warning(f"Error logging request: {e}")

    return state.final_answer, state.citations, state
