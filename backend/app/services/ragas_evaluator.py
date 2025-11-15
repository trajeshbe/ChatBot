"""
RAGAS Evaluation Service
========================
Comprehensive RAG evaluation using the RAGAS framework.

Provides metrics for:
- Faithfulness: How factually accurate is the answer based on the context
- Answer Relevancy: How relevant is the answer to the question
- Context Precision: How precise is the retrieved context
- Context Recall: How well does the context support the answer

Usage:
    evaluator = RAGASEvaluator()
    await evaluator.initialize()

    metrics = await evaluator.evaluate(
        question="What is TCS revenue?",
        answer="TCS revenue was $X billion",
        contexts=["TCS reported revenue of $X billion..."],
        ground_truth="TCS revenue was $X billion"  # Optional
    )
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class RAGASMetrics:
    """RAGAS evaluation metrics"""
    faithfulness: Optional[float] = None
    answer_relevancy: Optional[float] = None
    context_precision: Optional[float] = None
    context_recall: Optional[float] = None
    answer_similarity: Optional[float] = None
    answer_correctness: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "faithfulness": self.faithfulness,
            "answer_relevancy": self.answer_relevancy,
            "context_precision": self.context_precision,
            "context_recall": self.context_recall,
            "answer_similarity": self.answer_similarity,
            "answer_correctness": self.answer_correctness,
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        scores = [
            v for v in [
                self.faithfulness,
                self.answer_relevancy,
                self.context_precision,
                self.context_recall
            ] if v is not None
        ]

        if not scores:
            return {"average": None, "min": None, "max": None}

        return {
            "average": sum(scores) / len(scores),
            "min": min(scores),
            "max": max(scores),
            "count": len(scores)
        }


class RAGASEvaluator:
    """
    RAGAS-based RAG evaluation service
    """

    def __init__(self):
        self._initialized = False
        self._ragas_available = False

        # RAGAS components
        self.faithfulness_scorer = None
        self.answer_relevancy_scorer = None
        self.context_precision_scorer = None
        self.context_recall_scorer = None

    async def initialize(self) -> bool:
        """
        Initialize RAGAS components

        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return self._ragas_available

        try:
            # Import RAGAS components
            from ragas import evaluate
            from ragas.metrics import (
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
            )
            from datasets import Dataset

            # Store metrics
            self.faithfulness_metric = faithfulness
            self.answer_relevancy_metric = answer_relevancy
            self.context_precision_metric = context_precision
            self.context_recall_metric = context_recall
            self.ragas_evaluate = evaluate
            self.Dataset = Dataset

            self._ragas_available = True
            logger.info("✓ RAGAS evaluator initialized successfully")

        except ImportError as e:
            logger.warning(f"RAGAS not available: {e}")
            logger.warning("Install with: pip install ragas")
            self._ragas_available = False
        except Exception as e:
            logger.error(f"Failed to initialize RAGAS: {e}")
            self._ragas_available = False

        self._initialized = True
        return self._ragas_available

    async def evaluate(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None
    ) -> RAGASMetrics:
        """
        Evaluate a RAG response using RAGAS metrics

        Args:
            question: The user's question
            answer: The generated answer
            contexts: List of retrieved context chunks
            ground_truth: Optional reference answer for comparison

        Returns:
            RAGASMetrics object with evaluation scores
        """
        if not self._initialized:
            await self.initialize()

        if not self._ragas_available:
            logger.warning("RAGAS not available, returning empty metrics")
            return RAGASMetrics()

        try:
            # Prepare data for RAGAS
            data = {
                "question": [question],
                "answer": [answer],
                "contexts": [contexts],
            }

            # Add ground truth if available
            if ground_truth:
                data["ground_truth"] = [ground_truth]

            # Create dataset
            dataset = self.Dataset.from_dict(data)

            # Select metrics based on available data
            metrics = [
                self.faithfulness_metric,
                self.answer_relevancy_metric,
            ]

            if ground_truth:
                metrics.extend([
                    self.context_precision_metric,
                    self.context_recall_metric,
                ])

            # Run evaluation
            logger.info(f"Evaluating with RAGAS (metrics: {len(metrics)})")
            result = await asyncio.to_thread(
                self.ragas_evaluate,
                dataset,
                metrics=metrics
            )

            # Extract scores
            metrics_obj = RAGASMetrics(
                faithfulness=result.get("faithfulness"),
                answer_relevancy=result.get("answer_relevancy"),
                context_precision=result.get("context_precision") if ground_truth else None,
                context_recall=result.get("context_recall") if ground_truth else None,
            )

            logger.info(f"RAGAS evaluation complete: {metrics_obj.get_summary()}")
            return metrics_obj

        except Exception as e:
            logger.error(f"RAGAS evaluation failed: {e}")
            import traceback
            traceback.print_exc()
            return RAGASMetrics()

    async def evaluate_batch(
        self,
        questions: List[str],
        answers: List[str],
        contexts_list: List[List[str]],
        ground_truths: Optional[List[str]] = None
    ) -> List[RAGASMetrics]:
        """
        Evaluate multiple RAG responses

        Args:
            questions: List of questions
            answers: List of generated answers
            contexts_list: List of context lists (one per question)
            ground_truths: Optional list of reference answers

        Returns:
            List of RAGASMetrics objects
        """
        if not self._initialized:
            await self.initialize()

        if not self._ragas_available:
            return [RAGASMetrics() for _ in questions]

        try:
            # Prepare data
            data = {
                "question": questions,
                "answer": answers,
                "contexts": contexts_list,
            }

            if ground_truths:
                data["ground_truth"] = ground_truths

            # Create dataset
            dataset = self.Dataset.from_dict(data)

            # Select metrics
            metrics = [
                self.faithfulness_metric,
                self.answer_relevancy_metric,
            ]

            if ground_truths:
                metrics.extend([
                    self.context_precision_metric,
                    self.context_recall_metric,
                ])

            # Run evaluation
            result = await asyncio.to_thread(
                self.ragas_evaluate,
                dataset,
                metrics=metrics
            )

            # Convert to list of metrics
            results = []
            for i in range(len(questions)):
                metrics_obj = RAGASMetrics(
                    faithfulness=result["faithfulness"][i] if "faithfulness" in result else None,
                    answer_relevancy=result["answer_relevancy"][i] if "answer_relevancy" in result else None,
                    context_precision=result["context_precision"][i] if "context_precision" in result and ground_truths else None,
                    context_recall=result["context_recall"][i] if "context_recall" in result and ground_truths else None,
                )
                results.append(metrics_obj)

            return results

        except Exception as e:
            logger.error(f"Batch RAGAS evaluation failed: {e}")
            return [RAGASMetrics() for _ in questions]


# Global singleton
ragas_evaluator = RAGASEvaluator()
