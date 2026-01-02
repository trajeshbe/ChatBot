"""
Rank Fusion Service - Reciprocal Rank Fusion (RRF)

Combines results from multiple retrieval sources (pgvector + Elasticsearch) using
Reciprocal Rank Fusion (RRF) algorithm.

RRF Formula:
    score(d) = Σ_r [ weight_r / (k + rank_r(d)) ]

where:
- d = document
- r = retrieval source (pgvector, Elasticsearch, etc.)
- k = constant (default 60, from Cormack et al., 2009)
- rank_r(d) = rank of document d in source r

Benefits:
- No score normalization needed (rank-based)
- Robust to score scale differences
- Simple and effective (+10-15% vs single source)

Reference: Cormack, Clarke & Buettcher (2009). "Reciprocal Rank Fusion outperforms Condorcet and individual rank learning methods"

Author: Claude Code
Date: 2026-01-02
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class RankFusionService:
    """
    Reciprocal Rank Fusion for combining multiple retrieval sources.

    Literature: k=60 is optimal across most datasets.
    """

    def __init__(self, k: int = 60):
        """
        Initialize RRF service.

        Args:
            k: RRF constant parameter (default: 60, from literature)
        """
        self.k = k
        logger.info(f"📊 RankFusionService initialized (k={k})")

    def fuse(
        self,
        results_list: List[List[Dict[str, Any]]],
        weights: Optional[List[float]] = None,
        source_names: Optional[List[str]] = None,
        deduplicate_by: str = "document_id"
    ) -> List[Dict[str, Any]]:
        """
        Fuse results from multiple sources using RRF.

        RRF formula:
        score(d) = Σ_r [ weight_r / (k + rank_r(d)) ]

        Args:
            results_list: List of result lists from different sources
                Each source returns: List[Dict] with keys:
                    - document_id (or chunk_id)
                    - content
                    - score (original score, preserved but not used in RRF)
                    - metadata (optional)

            weights: Optional weights per source (default: equal weights = 1.0)
                Example: [1.0, 0.8] gives pgvector more weight than Elasticsearch

            source_names: Optional names for sources (e.g., ["pgvector", "elasticsearch"])
                Used for attribution in results

            deduplicate_by: Field to use for deduplication (default: "document_id")

        Returns:
            Fused results sorted by RRF score

        Example:
            pgvector_results = [
                {"document_id": "A", "content": "...", "score": 0.95},
                {"document_id": "B", "content": "...", "score": 0.90}
            ]

            es_results = [
                {"document_id": "B", "content": "...", "score": 12.5},
                {"document_id": "C", "content": "...", "score": 10.0}
            ]

            fused = rank_fusion.fuse(
                [pgvector_results, es_results],
                weights=[1.0, 0.8],  # Prefer pgvector
                source_names=["pgvector", "elasticsearch"]
            )

            # Result: B ranks highest (appears in both), then A, then C
        """
        if not results_list:
            logger.warning("⚠️ No results to fuse")
            return []

        num_sources = len(results_list)

        # Default weights: equal for all sources
        if weights is None:
            weights = [1.0] * num_sources

        if len(weights) != num_sources:
            logger.warning(f"⚠️ Weights length ({len(weights)}) != sources ({num_sources}), using equal weights")
            weights = [1.0] * num_sources

        # Default source names
        if source_names is None:
            source_names = [f"source_{i}" for i in range(num_sources)]

        # Build document ID → aggregated score mapping
        scores = defaultdict(lambda: {
            "document_id": None,
            "content": "",
            "metadata": {},
            "rrf_score": 0.0,
            "source_ranks": {},  # Track rank from each source
            "source_scores": {},  # Track original scores
            "num_sources": 0
        })

        # Calculate RRF scores
        for source_idx, results in enumerate(results_list):
            source_name = source_names[source_idx]
            weight = weights[source_idx]

            for rank, result in enumerate(results, start=1):
                # Get document ID (try multiple field names)
                doc_id = (
                    result.get(deduplicate_by) or
                    result.get("document_id") or
                    result.get("chunk_id") or
                    result.get("id")
                )

                if not doc_id:
                    logger.warning(f"⚠️ Result missing ID field '{deduplicate_by}', skipping")
                    continue

                # RRF contribution: weight / (k + rank)
                rrf_contribution = weight / (self.k + rank)

                # Aggregate scores
                if scores[doc_id]["document_id"] is None:
                    # First time seeing this document
                    scores[doc_id]["document_id"] = doc_id
                    scores[doc_id]["content"] = result.get("content", "")
                    scores[doc_id]["metadata"] = result.get("metadata", {})

                scores[doc_id]["rrf_score"] += rrf_contribution
                scores[doc_id]["source_ranks"][source_name] = rank
                scores[doc_id]["source_scores"][source_name] = result.get("score", 0.0)
                scores[doc_id]["num_sources"] += 1

        # Convert to list and sort by RRF score
        fused_results = sorted(
            scores.values(),
            key=lambda x: x["rrf_score"],
            reverse=True
        )

        logger.info(
            f"🔀 Fused {len(fused_results)} unique docs from {num_sources} sources "
            f"(k={self.k}, weights={weights})"
        )

        return fused_results

    def fuse_weighted_by_confidence(
        self,
        results_list: List[List[Dict[str, Any]]],
        source_confidences: List[float],
        source_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fuse results with dynamic weights based on source confidence.

        Useful when some sources are more reliable for certain queries.

        Args:
            results_list: List of result lists
            source_confidences: Confidence per source (0-1)
                Example: [0.95, 0.70] if pgvector is more confident than ES
            source_names: Optional source names

        Returns:
            Fused results with confidence-weighted RRF

        Example:
            # Query classifier determines:
            # - pgvector confidence: 0.95 (semantic query)
            # - Elasticsearch confidence: 0.60 (weak keyword match)

            fused = rank_fusion.fuse_weighted_by_confidence(
                [pgvector_results, es_results],
                source_confidences=[0.95, 0.60]
            )
        """
        return self.fuse(
            results_list,
            weights=source_confidences,
            source_names=source_names
        )

    def explain_fusion(
        self,
        document_id: str,
        fused_results: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Explain how a document's RRF score was calculated.

        Useful for debugging and understanding fusion behavior.

        Args:
            document_id: Document to explain
            fused_results: Output from fuse()

        Returns:
            Explanation dict with score breakdown

        Example:
            explanation = rank_fusion.explain_fusion("doc_123", fused_results)
            # Returns:
            # {
            #     "document_id": "doc_123",
            #     "rrf_score": 0.0234,
            #     "num_sources": 2,
            #     "breakdown": {
            #         "pgvector": {"rank": 1, "score": 0.95, "rrf_contribution": 0.0164},
            #         "elasticsearch": {"rank": 3, "score": 12.5, "rrf_contribution": 0.0070}
            #     }
            # }
        """
        for result in fused_results:
            if result.get("document_id") == document_id:
                breakdown = {}
                for source_name, rank in result.get("source_ranks", {}).items():
                    # Reconstruct RRF contribution (assuming weight=1.0)
                    # In production, you'd need to store the weight used
                    rrf_contribution = 1.0 / (self.k + rank)

                    breakdown[source_name] = {
                        "rank": rank,
                        "original_score": result["source_scores"].get(source_name),
                        "rrf_contribution": round(rrf_contribution, 4)
                    }

                return {
                    "document_id": document_id,
                    "rrf_score": round(result["rrf_score"], 4),
                    "num_sources": result["num_sources"],
                    "breakdown": breakdown
                }

        logger.warning(f"⚠️ Document '{document_id}' not found in fused results")
        return None


# Singleton instance
_rank_fusion_service = None

def get_rank_fusion(k: int = 60) -> RankFusionService:
    """
    Get singleton RankFusionService instance.

    Args:
        k: RRF constant (default: 60)

    Returns:
        RankFusionService instance
    """
    global _rank_fusion_service
    if _rank_fusion_service is None:
        _rank_fusion_service = RankFusionService(k=k)
    return _rank_fusion_service
