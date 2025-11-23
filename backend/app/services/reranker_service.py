"""
Cross-Encoder Reranker Service

Implements two-stage retrieval for state-of-the-art accuracy:
1. Stage 1 (Fast): Vector similarity search (top-N candidates)
2. Stage 2 (Precise): Cross-encoder reranking (top-K final results)

Expected improvement: +15-25% accuracy over vector-only retrieval

Models supported:
- ms-marco-MiniLM-L-6-v2 (fastest, 80MB)
- bge-reranker-base (better accuracy, 279MB)
- bge-reranker-large (best accuracy, 560MB)
"""

from typing import List, Dict, Optional, Tuple
import logging
import time
from functools import lru_cache
import torch
from sentence_transformers import CrossEncoder
import numpy as np

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """
    Cross-encoder reranker for precise document ranking.

    Uses transformer-based cross-encoder that jointly encodes
    query + document for superior ranking accuracy.
    """

    # Available models ranked by speed/accuracy tradeoff
    MODELS = {
        "fast": "cross-encoder/ms-marco-MiniLM-L-6-v2",  # 80MB, ~30ms per pair
        "balanced": "BAAI/bge-reranker-base",             # 279MB, ~50ms per pair
        "accurate": "BAAI/bge-reranker-large",            # 560MB, ~80ms per pair
    }

    def __init__(
        self,
        model_name: str = "balanced",
        device: Optional[str] = None,
        batch_size: int = 32
    ):
        """
        Initialize cross-encoder reranker.

        Args:
            model_name: "fast", "balanced", or "accurate"
            device: "cuda", "cpu", or None (auto-detect)
            batch_size: Batch size for inference (tune for your GPU)
        """
        self.model_name = model_name
        self.batch_size = batch_size

        # Auto-detect device if not specified
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        # Load model
        model_path = self.MODELS.get(model_name, self.MODELS["balanced"])
        logger.info(f"Loading cross-encoder model: {model_path} on {self.device}")

        try:
            self.model = CrossEncoder(model_path, device=self.device)
            logger.info(f"✅ Cross-encoder loaded successfully on {self.device}")
        except Exception as e:
            logger.error(f"❌ Failed to load cross-encoder: {e}")
            logger.warning("Falling back to no reranking - will use vector similarity only")
            self.model = None

    def is_available(self) -> bool:
        """Check if reranker model is loaded and available"""
        return self.model is not None

    def rerank(
        self,
        query: str,
        chunks: List[Dict],
        top_k: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        Rerank chunks using cross-encoder.

        Args:
            query: User query
            chunks: List of chunk dicts with 'content' field
            top_k: Number of top results to return
            score_threshold: Optional minimum reranking score (0-1)

        Returns:
            Reranked chunks with updated 'rerank_score' field
        """
        if not self.is_available():
            logger.warning("Reranker not available - returning chunks as-is")
            return chunks[:top_k]

        if not chunks:
            return []

        start_time = time.time()

        # Prepare query-document pairs for cross-encoder
        pairs = [[query, chunk['content']] for chunk in chunks]

        # Get cross-encoder scores (batched for efficiency)
        try:
            scores = self.model.predict(
                pairs,
                batch_size=self.batch_size,
                show_progress_bar=False
            )

            # Convert to list if numpy array
            if isinstance(scores, np.ndarray):
                scores = scores.tolist()

            # Add rerank scores to chunks
            for chunk, score in zip(chunks, scores):
                chunk['rerank_score'] = float(score)
                chunk['original_similarity'] = chunk.get('similarity', 0.0)

            # Filter by threshold if specified
            if score_threshold is not None:
                chunks = [c for c in chunks if c['rerank_score'] >= score_threshold]

            # Sort by rerank score (descending)
            chunks.sort(key=lambda x: x['rerank_score'], reverse=True)

            # Take top-k
            reranked = chunks[:top_k]

            elapsed_ms = (time.time() - start_time) * 1000

            logger.info(
                f"🔄 Reranked {len(chunks)} chunks → {len(reranked)} in {elapsed_ms:.0f}ms "
                f"(avg rerank_score: {np.mean([c['rerank_score'] for c in reranked]):.3f})"
            )

            return reranked

        except Exception as e:
            logger.error(f"Error during reranking: {e}")
            # Fallback to original order
            return chunks[:top_k]

    def rerank_with_fusion(
        self,
        query: str,
        chunks: List[Dict],
        top_k: int = 5,
        fusion_weight: float = 0.7
    ) -> List[Dict]:
        """
        Rerank with score fusion (combine vector similarity + rerank score).

        This can be more robust than pure reranking in some cases.

        Args:
            query: User query
            chunks: List of chunk dicts
            top_k: Number of top results
            fusion_weight: Weight for rerank score (0-1), 1-weight for vector similarity

        Returns:
            Reranked chunks with 'fusion_score' field
        """
        if not self.is_available():
            return chunks[:top_k]

        # First rerank to get cross-encoder scores
        reranked = self.rerank(query, chunks, top_k=len(chunks))

        # Normalize scores to 0-1 range
        rerank_scores = [c['rerank_score'] for c in reranked]
        vector_scores = [c.get('similarity', 0.0) for c in reranked]

        # Min-max normalization
        def normalize(scores):
            if not scores or max(scores) == min(scores):
                return scores
            min_s, max_s = min(scores), max(scores)
            return [(s - min_s) / (max_s - min_s) for s in scores]

        norm_rerank = normalize(rerank_scores)
        norm_vector = normalize(vector_scores)

        # Fuse scores
        for chunk, r_score, v_score in zip(reranked, norm_rerank, norm_vector):
            chunk['fusion_score'] = (
                fusion_weight * r_score +
                (1 - fusion_weight) * v_score
            )

        # Sort by fusion score
        reranked.sort(key=lambda x: x['fusion_score'], reverse=True)

        logger.info(
            f"🔀 Score fusion applied (rerank_weight={fusion_weight:.2f}, "
            f"vector_weight={1-fusion_weight:.2f})"
        )

        return reranked[:top_k]

    def get_model_info(self) -> Dict:
        """Get information about the loaded model"""
        return {
            "model_name": self.model_name,
            "model_path": self.MODELS.get(self.model_name, "unknown"),
            "device": self.device,
            "batch_size": self.batch_size,
            "is_available": self.is_available()
        }


# Singleton instance (lazy initialization)
_reranker_instance: Optional[CrossEncoderReranker] = None


@lru_cache(maxsize=1)
def get_reranker(
    model_name: str = "balanced",
    device: Optional[str] = None
) -> CrossEncoderReranker:
    """
    Get or create global reranker instance.

    Args:
        model_name: "fast", "balanced", or "accurate"
        device: "cuda", "cpu", or None (auto-detect)

    Returns:
        CrossEncoderReranker instance
    """
    global _reranker_instance

    if _reranker_instance is None:
        _reranker_instance = CrossEncoderReranker(
            model_name=model_name,
            device=device
        )

    return _reranker_instance


def rerank_chunks(
    query: str,
    chunks: List[Dict],
    top_k: int = 5,
    model_name: str = "balanced",
    use_fusion: bool = False,
    fusion_weight: float = 0.7
) -> List[Dict]:
    """
    Convenience function to rerank chunks.

    Args:
        query: User query
        chunks: List of chunk dicts
        top_k: Number of top results
        model_name: "fast", "balanced", or "accurate"
        use_fusion: If True, use score fusion instead of pure reranking
        fusion_weight: Weight for rerank score in fusion (0-1)

    Returns:
        Reranked chunks
    """
    reranker = get_reranker(model_name=model_name)

    if use_fusion:
        return reranker.rerank_with_fusion(
            query=query,
            chunks=chunks,
            top_k=top_k,
            fusion_weight=fusion_weight
        )
    else:
        return reranker.rerank(
            query=query,
            chunks=chunks,
            top_k=top_k
        )
