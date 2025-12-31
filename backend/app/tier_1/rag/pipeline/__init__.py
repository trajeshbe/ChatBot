"""
RAG Pipeline Package

A robust RAG (Retrieval-Augmented Generation) pipeline with:
- Hybrid retrieval (semantic + lexical)
- Memory hierarchy (session → all documents)
- LLM-based reranking
- Self-critique and refinement
- Semantic caching
- Comprehensive observability

Usage:
    from app.rag_pipeline import rag_answer

    answer, citations, state = await rag_answer(
        user_query="What is the project about?",
        db=db_session,
        session_id="session-123"
    )
"""

from .pipeline import rag_answer, RagState, CritiqueResult
from .config import get_rag_settings, get_model_context_window, is_large_context_model
from .embeddings import embed_query, get_embedding_manager
from .retrieval import retrieve_hybrid, get_retriever
from .reranker import rerank_with_ollama, get_reranker
from .semantic_cache import get_cached_answer, store_answer, get_semantic_cache
from .llm import (
    generate_grounded_answer,
    critique_answer,
    refine_answer_with_critique,
    get_llm_client
)
from .observability import get_metrics_collector

__all__ = [
    # Main pipeline function
    "rag_answer",

    # State and data classes
    "RagState",
    "CritiqueResult",

    # Configuration
    "get_rag_settings",
    "get_model_context_window",
    "is_large_context_model",

    # Core functions
    "embed_query",
    "retrieve_hybrid",
    "rerank_with_ollama",
    "get_cached_answer",
    "store_answer",
    "generate_grounded_answer",
    "critique_answer",
    "refine_answer_with_critique",

    # Manager instances
    "get_embedding_manager",
    "get_retriever",
    "get_reranker",
    "get_semantic_cache",
    "get_llm_client",
    "get_metrics_collector",
]

__version__ = "1.0.0"
