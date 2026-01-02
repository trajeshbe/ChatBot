"""
Confidence Scorer - Calibrated Answer Reliability

Provides calibrated confidence scores for RAG answers based on multiple signals:
- Retrieval scores (embedding similarity, BM25, RRF)
- Re-ranker scores (cross-encoder)
- Number of supporting documents
- Answer characteristics (length, coherence)

Output: P(correct | features) - calibrated probability that answer is reliable

Use cases:
- Show confidence intervals to users
- Filter low-confidence answers
- Route to human review when confidence < threshold
- A/B testing between retrieval strategies

Author: Claude Code
Date: 2026-01-02
"""

from typing import Dict, Any, Optional, List
from enum import Enum
import logging
import math

logger = logging.getLogger(__name__)


class ConfidenceLevel(str, Enum):
    """Human-readable confidence levels"""
    VERY_HIGH = "very_high"  # >= 0.9
    HIGH = "high"            # >= 0.75
    MEDIUM = "medium"        # >= 0.5
    LOW = "low"              # < 0.5


class ConfidenceScorer:
    """
    Calibrated confidence scoring for RAG answers.

    Provides P(correct | features) using feature-based scoring.
    Can be extended with trained calibration models per POC.
    """

    def __init__(
        self,
        feature_weights: Optional[Dict[str, float]] = None,
        calibration_params: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize confidence scorer.

        Args:
            feature_weights: Custom feature weights (default: balanced)
            calibration_params: POC-specific calibration parameters
        """
        # Default feature weights (sum to 1.0)
        self.feature_weights = feature_weights or {
            "embedding_score": 0.20,      # Semantic similarity
            "reranker_score": 0.35,       # Cross-encoder (most important)
            "num_supporting_docs": 0.20,  # Evidence breadth
            "answer_length": 0.10,        # Completeness proxy
            "source_quality": 0.15        # Source recency/reliability
        }

        # Calibration parameters (can be tuned per POC)
        self.calibration = calibration_params or {
            "min_docs_threshold": 2,      # Minimum docs for high confidence
            "max_docs_for_scoring": 5,    # Diminishing returns after N docs
            "min_answer_length": 50,      # Minimum tokens for complete answer
            "optimal_answer_length": 150, # Optimal length (not too short/long)
            "reranker_high_threshold": 0.7,  # Reranker score for high confidence
            "source_recency_weight": 0.3     # Weight for recent documents
        }

        logger.info("📊 ConfidenceScorer initialized")

    def calculate(
        self,
        features: Dict[str, float],
        explain: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate calibrated confidence score.

        Args:
            features: Feature dict with keys:
                - embedding_score: Cosine similarity (0-1)
                - reranker_score: Cross-encoder score (0-1)
                - num_supporting_docs: Number of retrieved docs
                - answer_length: Number of tokens in answer
                - source_quality: Optional source quality score (0-1)
                - rrf_score: Optional RRF score (if using multi-pipeline)

            explain: If True, return detailed explanation

        Returns:
            {
                "confidence": float (0-1),
                "level": ConfidenceLevel,
                "description": str,
                "explanation": Dict (if explain=True)
            }

        Example:
            features = {
                "embedding_score": 0.85,
                "reranker_score": 0.78,
                "num_supporting_docs": 4,
                "answer_length": 120,
                "source_quality": 0.90
            }

            result = scorer.calculate(features, explain=True)
            # Returns:
            # {
            #     "confidence": 0.82,
            #     "level": "high",
            #     "description": "Confident - answer is likely correct",
            #     "explanation": {...}
            # }
        """
        # Normalize features
        normalized = self._normalize_features(features)

        # Calculate weighted score
        raw_score = self._calculate_weighted_score(normalized)

        # Apply calibration adjustments
        calibrated_score = self._calibrate(raw_score, features)

        # Ensure [0, 1] bounds
        confidence = min(max(calibrated_score, 0.0), 1.0)

        # Get human-readable level
        level = self._get_confidence_level(confidence)
        description = self._get_description(level)

        result = {
            "confidence": round(confidence, 3),
            "level": level.value,
            "description": description
        }

        # Add explanation if requested
        if explain:
            result["explanation"] = {
                "normalized_features": normalized,
                "feature_contributions": self._get_feature_contributions(normalized),
                "raw_score": round(raw_score, 3),
                "calibration_adjustments": self._get_calibration_adjustments(features),
                "final_confidence": round(confidence, 3)
            }

        return result

    def _normalize_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """
        Normalize features to [0, 1] scale.

        Different features have different scales:
        - embedding_score: already [0, 1]
        - reranker_score: already [0, 1]
        - num_supporting_docs: normalize to [0, 1] with diminishing returns
        - answer_length: normalize with optimal length
        - source_quality: already [0, 1]
        """
        normalized = {}

        # Embedding score (already normalized)
        normalized["embedding_score"] = min(features.get("embedding_score", 0.5), 1.0)

        # Reranker score (already normalized)
        normalized["reranker_score"] = min(features.get("reranker_score", 0.5), 1.0)

        # Number of supporting docs (with diminishing returns)
        num_docs = features.get("num_supporting_docs", 1)
        max_docs = self.calibration["max_docs_for_scoring"]
        normalized["num_supporting_docs"] = min(num_docs / max_docs, 1.0)

        # Answer length (optimal at ~150 tokens, penalty for too short/long)
        answer_len = features.get("answer_length", 50)
        optimal = self.calibration["optimal_answer_length"]
        min_len = self.calibration["min_answer_length"]

        if answer_len < min_len:
            # Too short - linearly penalize
            normalized["answer_length"] = answer_len / min_len
        elif answer_len <= optimal:
            # Optimal range
            normalized["answer_length"] = 1.0
        else:
            # Too long - slight penalty (might be verbose)
            excess = answer_len - optimal
            penalty = min(excess / optimal, 0.3)  # Max 30% penalty
            normalized["answer_length"] = 1.0 - penalty

        # Source quality (already normalized, default to moderate if missing)
        normalized["source_quality"] = features.get("source_quality", 0.7)

        return normalized

    def _calculate_weighted_score(self, normalized: Dict[str, float]) -> float:
        """Calculate weighted average of normalized features"""
        score = 0.0
        for feature, weight in self.feature_weights.items():
            score += weight * normalized.get(feature, 0.5)

        return score

    def _calibrate(self, raw_score: float, original_features: Dict[str, float]) -> float:
        """
        Apply calibration adjustments based on specific conditions.

        Adjustments:
        - Boost if reranker score very high (strong signal)
        - Penalize if too few supporting docs
        - Penalize if source quality very low
        """
        calibrated = raw_score

        # Boost for very high reranker score
        reranker_score = original_features.get("reranker_score", 0.5)
        if reranker_score >= self.calibration["reranker_high_threshold"]:
            boost = (reranker_score - self.calibration["reranker_high_threshold"]) * 0.1
            calibrated += boost

        # Penalty for insufficient supporting documents
        num_docs = original_features.get("num_supporting_docs", 1)
        if num_docs < self.calibration["min_docs_threshold"]:
            penalty = (self.calibration["min_docs_threshold"] - num_docs) * 0.1
            calibrated -= penalty

        # Penalty for very low source quality
        source_quality = original_features.get("source_quality", 0.7)
        if source_quality < 0.5:
            penalty = (0.5 - source_quality) * 0.2
            calibrated -= penalty

        return calibrated

    def _get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Convert numeric confidence to categorical level"""
        if confidence >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif confidence >= 0.75:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.5:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def _get_description(self, level: ConfidenceLevel) -> str:
        """Get human-readable description for confidence level"""
        descriptions = {
            ConfidenceLevel.VERY_HIGH: "Very confident - answer is highly reliable",
            ConfidenceLevel.HIGH: "Confident - answer is likely correct",
            ConfidenceLevel.MEDIUM: "Moderately confident - verify if critical",
            ConfidenceLevel.LOW: "Low confidence - manual verification recommended"
        }
        return descriptions[level]

    def _get_feature_contributions(self, normalized: Dict[str, float]) -> Dict[str, float]:
        """Calculate how much each feature contributed to final score"""
        contributions = {}
        for feature, weight in self.feature_weights.items():
            contribution = weight * normalized.get(feature, 0.5)
            contributions[feature] = round(contribution, 3)
        return contributions

    def _get_calibration_adjustments(self, features: Dict[str, float]) -> List[str]:
        """Get list of calibration adjustments applied"""
        adjustments = []

        reranker_score = features.get("reranker_score", 0.5)
        if reranker_score >= self.calibration["reranker_high_threshold"]:
            adjustments.append(f"Boost for high reranker score ({reranker_score:.2f})")

        num_docs = features.get("num_supporting_docs", 1)
        if num_docs < self.calibration["min_docs_threshold"]:
            adjustments.append(f"Penalty for few supporting docs ({num_docs})")

        source_quality = features.get("source_quality", 0.7)
        if source_quality < 0.5:
            adjustments.append(f"Penalty for low source quality ({source_quality:.2f})")

        if not adjustments:
            adjustments.append("No calibration adjustments applied")

        return adjustments

    def should_escalate(
        self,
        confidence: float,
        threshold: float = 0.5
    ) -> bool:
        """
        Determine if answer should be escalated to human review.

        Args:
            confidence: Confidence score (0-1)
            threshold: Minimum confidence threshold

        Returns:
            True if confidence < threshold (needs escalation)
        """
        return confidence < threshold


# Singleton instance
_confidence_scorer = None

def get_confidence_scorer(
    feature_weights: Optional[Dict[str, float]] = None,
    calibration_params: Optional[Dict[str, Any]] = None
) -> ConfidenceScorer:
    """
    Get singleton ConfidenceScorer instance.

    Args:
        feature_weights: Custom feature weights
        calibration_params: POC-specific calibration

    Returns:
        ConfidenceScorer instance
    """
    global _confidence_scorer
    if _confidence_scorer is None:
        _confidence_scorer = ConfidenceScorer(feature_weights, calibration_params)
    return _confidence_scorer
