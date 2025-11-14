"""
Observability Utilities for RAG Pipeline

Provides timing decorators and structured logging for monitoring
pipeline performance and debugging.
"""

from typing import Callable, Any, Dict, Optional
import time
import logging
from functools import wraps
import json

logger = logging.getLogger(__name__)


class PipelineTimer:
    """Context manager for timing operations"""

    def __init__(self, operation_name: str, state: Optional[Any] = None):
        self.operation_name = operation_name
        self.state = state
        self.start_time = None
        self.duration_ms = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration_ms = (time.time() - self.start_time) * 1000

        # Store timing in state if provided
        if self.state and hasattr(self.state, 'timings_ms'):
            self.state.timings_ms[self.operation_name] = self.duration_ms

        # Log timing
        if exc_type is None:
            logger.info(f"[TIMING] {self.operation_name}: {self.duration_ms:.2f}ms")
        else:
            logger.error(f"[TIMING] {self.operation_name}: FAILED after {self.duration_ms:.2f}ms")

        return False  # Don't suppress exceptions


def timed(operation_name: str):
    """
    Decorator to time async functions and store results in state.

    Usage:
        @timed("embed_query")
        async def embed_query_stage(state: RagState, settings: Settings) -> RagState:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract state from args (usually first arg)
            state = None
            if args and hasattr(args[0], 'timings_ms'):
                state = args[0]

            with PipelineTimer(operation_name, state):
                result = await func(*args, **kwargs)

            return result

        return wrapper
    return decorator


def log_rag_request(
    user_query: str,
    normalized_query: str,
    session_id: Optional[str],
    tenant_id: Optional[str],
    user_id: Optional[str],
    cache_hit: bool,
    refined: bool,
    rerank_used: bool,
    timings_ms: Dict[str, float],
    num_candidates: int,
    num_used_chunks: int,
    model_name_used: str,
    extra_meta: Optional[Dict[str, Any]] = None
):
    """
    Log structured RAG request information for observability.

    This creates a structured log entry that can be ingested by
    observability tools like Grafana Loki.
    """
    total_time_ms = sum(timings_ms.values())

    log_data = {
        "event": "rag_request",
        "user_query": user_query[:100],  # Truncate for privacy
        "normalized_query": normalized_query[:100],
        "session_id": session_id,
        "tenant_id": tenant_id,
        "user_id": user_id,
        "cache_hit": cache_hit,
        "refined": refined,
        "rerank_used": rerank_used,
        "num_candidates": num_candidates,
        "num_used_chunks": num_used_chunks,
        "model_name": model_name_used,
        "total_time_ms": total_time_ms,
        "timings": timings_ms,
        "extra_meta": extra_meta or {}
    }

    logger.info(f"RAG_REQUEST: {json.dumps(log_data)}")

    # Also log a human-readable summary
    logger.info(
        f"RAG Query completed: "
        f"query_length={len(user_query)}, "
        f"cache_hit={cache_hit}, "
        f"chunks={num_used_chunks}, "
        f"model={model_name_used}, "
        f"total_time={total_time_ms:.0f}ms"
    )

    # Log detailed timing breakdown if enabled
    from .config import get_rag_settings
    settings = get_rag_settings()

    if settings.ENABLE_DETAILED_LOGGING:
        logger.debug(f"Timing breakdown: {json.dumps(timings_ms, indent=2)}")


def log_retrieval_results(
    query: str,
    num_results: int,
    top_score: float,
    search_type: str,
    session_scoped: bool
):
    """Log retrieval results for monitoring"""
    logger.info(
        f"[RETRIEVAL] {search_type}: "
        f"query_length={len(query)}, "
        f"results={num_results}, "
        f"top_score={top_score:.3f}, "
        f"session_scoped={session_scoped}"
    )


def log_rerank_results(
    input_count: int,
    output_count: int,
    top_score_before: float,
    top_score_after: float
):
    """Log reranking results"""
    score_change = top_score_after - top_score_before

    logger.info(
        f"[RERANK] "
        f"input={input_count}, "
        f"output={output_count}, "
        f"score_change={score_change:+.3f} "
        f"({top_score_before:.3f} -> {top_score_after:.3f})"
    )


def log_critique_results(
    is_grounded: bool,
    is_complete: bool,
    num_issues: int
):
    """Log critique results"""
    logger.info(
        f"[CRITIQUE] "
        f"grounded={is_grounded}, "
        f"complete={is_complete}, "
        f"issues={num_issues}"
    )


def log_cache_event(event_type: str, similarity: Optional[float] = None):
    """
    Log cache events (hit, miss, store).

    Args:
        event_type: 'hit', 'miss', or 'store'
        similarity: Similarity score for cache hits
    """
    if event_type == "hit":
        logger.info(f"[CACHE] HIT (similarity={similarity:.4f})")
    elif event_type == "miss":
        logger.info("[CACHE] MISS")
    elif event_type == "store":
        logger.info("[CACHE] STORED")
    else:
        logger.warning(f"[CACHE] Unknown event type: {event_type}")


def log_error(
    stage: str,
    error: Exception,
    query: str,
    context: Optional[Dict[str, Any]] = None
):
    """
    Log errors with structured context.

    Args:
        stage: Pipeline stage where error occurred
        error: The exception
        query: User query
        context: Additional context
    """
    error_data = {
        "event": "rag_error",
        "stage": stage,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "query_length": len(query),
        "context": context or {}
    }

    logger.error(f"RAG_ERROR: {json.dumps(error_data)}", exc_info=True)


class MetricsCollector:
    """
    Collects metrics during pipeline execution.

    Can be extended to integrate with Prometheus or other metrics systems.
    """

    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "refinements": 0,
            "errors": 0,
            "total_latency_ms": 0.0,
            "embedding_latency_ms": 0.0,
            "retrieval_latency_ms": 0.0,
            "generation_latency_ms": 0.0,
            "rerank_latency_ms": 0.0
        }

    def record_request(
        self,
        cache_hit: bool,
        refined: bool,
        error: bool,
        timings: Dict[str, float]
    ):
        """Record a completed request"""
        self.metrics["total_requests"] += 1

        if cache_hit:
            self.metrics["cache_hits"] += 1
        else:
            self.metrics["cache_misses"] += 1

        if refined:
            self.metrics["refinements"] += 1

        if error:
            self.metrics["errors"] += 1

        # Aggregate latencies
        total_latency = sum(timings.values())
        self.metrics["total_latency_ms"] += total_latency

        # Stage-specific latencies
        self.metrics["embedding_latency_ms"] += timings.get("embed_query", 0)
        self.metrics["retrieval_latency_ms"] += timings.get("hybrid_retrieval", 0)
        self.metrics["generation_latency_ms"] += timings.get("generate_initial_answer", 0)
        self.metrics["rerank_latency_ms"] += timings.get("rerank", 0)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        metrics = self.metrics.copy()

        # Calculate averages
        if metrics["total_requests"] > 0:
            metrics["avg_latency_ms"] = metrics["total_latency_ms"] / metrics["total_requests"]
            metrics["cache_hit_rate"] = metrics["cache_hits"] / metrics["total_requests"]
            metrics["refinement_rate"] = metrics["refinements"] / metrics["total_requests"]
            metrics["error_rate"] = metrics["errors"] / metrics["total_requests"]

        return metrics

    def reset(self):
        """Reset all metrics"""
        for key in self.metrics:
            if isinstance(self.metrics[key], (int, float)):
                self.metrics[key] = 0 if isinstance(self.metrics[key], int) else 0.0


# Global metrics collector
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector"""
    return _metrics_collector
