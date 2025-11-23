"""
RAG Pipeline Configuration

Settings specific to the robust RAG pipeline with hybrid retrieval,
reranking, self-critique, and adaptive context window management.
"""

from pydantic_settings import BaseSettings
from typing import Optional, Dict
from functools import lru_cache


class RagPipelineSettings(BaseSettings):
    """Configuration for robust RAG pipeline"""

    # ====================================================================
    # Model Configuration
    # ====================================================================

    # Embedding models
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # 🆕 Short name for cache versioning
    EMBEDDING_DIMENSION: int = 384

    # Generation models (with fallback chain)
    GENERATION_MODEL_NAME: str = "gpt-4-turbo-preview"  # Primary
    GENERATION_MODEL_OLLAMA: str = "mistral:latest"     # Fallback

    # Reranking model (Ollama-based)
    RERANK_MODEL_NAME: str = "mistral:latest"

    # Critique model (for self-RAG)
    CRITIQUE_MODEL_NAME: str = "gpt-4-turbo-preview"

    # ====================================================================
    # Retrieval Configuration
    # ====================================================================

    # Hybrid retrieval parameters
    RETRIEVAL_CANDIDATES: int = 20      # Initial retrieval pool
    RETRIEVAL_ALPHA: float = 0.7        # Semantic vs lexical weight (0.7 = 70% semantic)

    # 🆕 Hybrid search weights (for cache versioning)
    SEMANTIC_WEIGHT: float = 0.8        # 80% semantic (vector similarity)
    KEYWORD_WEIGHT: float = 0.2         # 20% keyword (lexical matching)

    # 🆕 Chunking parameters (for cache versioning)
    CHUNK_SIZE: int = 800               # Text chunk size in characters
    CHUNK_OVERLAP: int = 150            # Overlap between chunks

    # 🆕 Top-K results (for cache versioning)
    TOP_K_RESULTS: int = 5              # Number of top results to retrieve

    # Context window management
    CONTEXT_CHUNKS: int = 5             # Chunks to use for generation (post-reranking)
    MAX_CONTEXT_LENGTH: int = 8000      # Max tokens for context (model-dependent)

    # Similarity thresholds
    MIN_SIMILARITY_THRESHOLD: float = 0.1  # Minimum for any result
    SIMILARITY_THRESHOLD: float = 0.5      # 🆕 Standard similarity threshold for retrieval
    GOOD_SIMILARITY_THRESHOLD: float = 0.6 # Good match threshold

    # ====================================================================
    # Reranking Configuration
    # ====================================================================

    ENABLE_RERANKER: bool = True
    RERANK_TOP_K: int = 5               # Final top-k after reranking
    RERANK_BATCH_SIZE: int = 4          # Process candidates in batches

    # ====================================================================
    # Semantic Cache Configuration
    # ====================================================================

    ENABLE_SEMANTIC_CACHE: bool = True
    CACHE_SIMILARITY_THRESHOLD: float = 0.95  # Very high similarity for cache hit
    CACHE_TTL_SECONDS: int = 3600             # 1 hour

    # ====================================================================
    # Self-Critique Configuration
    # ====================================================================

    ENABLE_SELF_CRITIQUE: bool = True
    CRITIQUE_ON_LOW_CONFIDENCE: bool = True
    MIN_CONFIDENCE_THRESHOLD: float = 0.7

    # ====================================================================
    # Generation Configuration
    # ====================================================================

    GENERATION_TEMPERATURE: float = 0.7
    GENERATION_MAX_TOKENS: int = 1024
    REFINE_TEMPERATURE: float = 0.5     # Lower temperature for refinement

    # ====================================================================
    # Model-Specific Context Windows
    # ====================================================================

    # Context window sizes for different models (in tokens)
    MODEL_CONTEXT_WINDOWS: Dict[str, int] = {
        # OpenAI models
        "gpt-4-turbo-preview": 128000,
        "gpt-4": 8192,
        "gpt-3.5-turbo": 16385,
        "gpt-3.5-turbo-16k": 16385,

        # Anthropic Claude models
        "claude-3-opus-20240229": 200000,
        "claude-3-sonnet-20240229": 200000,
        "claude-3-haiku-20240307": 200000,
        "claude-2.1": 200000,
        "claude-2": 100000,

        # Ollama models (conservative estimates)
        "mistral:latest": 8000,
        "llama2:latest": 4096,
        "llama2:13b": 4096,
        "llama2:70b": 4096,
        "mixtral:latest": 32000,
        "codellama:latest": 16000,

        # vLLM models
        "meta-llama/Llama-2-7b-chat-hf": 4096,
        "meta-llama/Llama-2-13b-chat-hf": 4096,
        "meta-llama/Llama-2-70b-chat-hf": 4096,
    }

    # ====================================================================
    # Adaptive Strategy Configuration
    # ====================================================================

    # For large context window models (>100k tokens), maximize context
    USE_MAX_CONTEXT_FOR_LARGE_MODELS: bool = True
    LARGE_MODEL_THRESHOLD: int = 100000  # Context window size to be considered "large"

    # For small models, use more selective retrieval
    SMALL_MODEL_CHUNK_LIMIT: int = 3
    SMALL_MODEL_THRESHOLD: int = 10000   # Context window size to be considered "small"

    # ====================================================================
    # Observability Configuration
    # ====================================================================

    ENABLE_DETAILED_LOGGING: bool = True
    LOG_RETRIEVAL_SCORES: bool = True
    LOG_RERANK_SCORES: bool = True
    LOG_CRITIQUE_DETAILS: bool = True

    # ====================================================================
    # Tenant & Session Management
    # ====================================================================

    ENABLE_TENANT_ISOLATION: bool = True
    ENABLE_SESSION_MEMORY: bool = True
    SESSION_MEMORY_LIMIT: int = 10       # Max recent messages in session context

    # ====================================================================
    # Memory Hierarchy Configuration
    # ====================================================================

    # Short-term memory (session documents) takes precedence
    PRIORITIZE_SESSION_DOCUMENTS: bool = True
    SESSION_DOCUMENT_BOOST: float = 0.2  # Score boost for session docs

    # Cascading fallback strategy
    ENABLE_CASCADING_FALLBACK: bool = True
    FALLBACK_TO_LONG_TERM: bool = True
    FALLBACK_SIMILARITY_REDUCTION: float = 0.1  # Reduce threshold by this amount for fallback

    class Config:
        env_file = ".env"
        case_sensitive = True
        env_prefix = "RAG_"  # Environment variables should be prefixed with RAG_


@lru_cache()
def get_rag_settings() -> RagPipelineSettings:
    """Get cached RAG pipeline settings"""
    return RagPipelineSettings()


# Convenience function to get context window for a model
def get_model_context_window(model_name: str) -> int:
    """
    Get the context window size for a given model.
    Returns a conservative default if model is not in the list.
    """
    settings = get_rag_settings()
    return settings.MODEL_CONTEXT_WINDOWS.get(model_name, 4096)  # Safe default


def is_large_context_model(model_name: str) -> bool:
    """Check if a model has a large context window (>100k tokens)"""
    settings = get_rag_settings()
    context_window = get_model_context_window(model_name)
    return context_window >= settings.LARGE_MODEL_THRESHOLD


def get_optimal_chunk_count(model_name: str) -> int:
    """
    Get optimal number of chunks to use based on model's context window.

    Large models (>100k tokens): Use more chunks for maximum context
    Medium models (10k-100k): Use standard chunk count
    Small models (<10k): Use fewer, more selective chunks
    """
    settings = get_rag_settings()
    context_window = get_model_context_window(model_name)

    if context_window >= settings.LARGE_MODEL_THRESHOLD:
        # Large models: maximize context utilization
        # Assuming ~200 tokens per chunk, use up to 50% of context window
        return min(int(context_window * 0.5 / 200), 100)
    elif context_window <= settings.SMALL_MODEL_THRESHOLD:
        # Small models: be selective
        return settings.SMALL_MODEL_CHUNK_LIMIT
    else:
        # Medium models: use standard count
        return settings.CONTEXT_CHUNKS
