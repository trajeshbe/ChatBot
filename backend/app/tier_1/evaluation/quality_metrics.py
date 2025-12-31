"""
RAG Quality Metrics Service

Implements enterprise-grade quality evaluation metrics inspired by RAGAS:
1. Faithfulness: Answer is grounded in retrieved context
2. Answer Relevancy: Answer directly addresses the query
3. Context Relevancy: Retrieved chunks are relevant to query
4. Context Precision: Relevant chunks ranked highly
5. Answer Correctness: Semantic similarity with expected answer (if provided)

These metrics help monitor and validate RAG system performance.
"""

import re
from typing import Dict, List, Optional
import logging
from app.services.embedding_service import embedding_service
import numpy as np

logger = logging.getLogger(__name__)


class QualityMetricsService:
    """Evaluate RAG response quality with multiple metrics"""

    async def evaluate_response(
        self,
        query: str,
        answer: str,
        context_chunks: List[Dict],
        expected_answer: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Evaluate a RAG response across multiple quality dimensions

        Args:
            query: User's question
            answer: Generated answer
            context_chunks: Retrieved document chunks used
            expected_answer: Optional ground truth answer (for testing)

        Returns:
            Dict with metrics scores (0-1 scale, higher is better)
        """
        metrics = {}

        try:
            # 1. Faithfulness: Is answer grounded in context?
            if context_chunks:
                faithfulness_result = await self._calculate_faithfulness(answer, context_chunks)
                metrics['faithfulness'] = faithfulness_result['score']
                metrics['faithfulness_details'] = faithfulness_result['details']
            else:
                metrics['faithfulness'] = 0.0  # No context means no grounding
                metrics['faithfulness_details'] = None

            # 2. Answer Relevancy: Does answer address the query?
            metrics['answer_relevancy'] = await self._calculate_answer_relevancy(query, answer)

            # 3. Context Relevancy: Are retrieved chunks relevant to query?
            if context_chunks:
                context_relevancy_result = self._calculate_context_relevancy(context_chunks)
                metrics['context_relevancy'] = context_relevancy_result['score']
                metrics['context_relevancy_details'] = context_relevancy_result['details']
            else:
                metrics['context_relevancy'] = 0.0
                metrics['context_relevancy_details'] = None

            # 4. Context Precision: Are most relevant chunks ranked high?
            if context_chunks:
                context_precision_result = self._calculate_context_precision(context_chunks)
                metrics['context_precision'] = context_precision_result['score']
                metrics['context_precision_details'] = context_precision_result['details']
            else:
                metrics['context_precision'] = 0.0
                metrics['context_precision_details'] = None

            # 5. Answer Correctness (if expected answer provided)
            if expected_answer:
                metrics['answer_correctness'] = await self._calculate_answer_correctness(answer, expected_answer)

            # 6. Overall RAG Score (weighted average)
            metrics['rag_score'] = self._calculate_overall_score(metrics)

            # 7. Quality Level
            metrics['quality_level'] = self._get_quality_level(metrics['rag_score'])

            logger.info(f"📊 Quality Metrics - RAG Score: {metrics['rag_score']:.2f}, Level: {metrics['quality_level']}")

            return metrics

        except Exception as e:
            logger.error(f"Error calculating quality metrics: {e}")
            return {
                'faithfulness': 0.0,
                'answer_relevancy': 0.0,
                'context_relevancy': 0.0,
                'context_precision': 0.0,
                'rag_score': 0.0,
                'quality_level': 'error',
                'error': str(e)
            }

    async def _calculate_faithfulness(self, answer: str, context_chunks: List[Dict]) -> Dict:
        """
        Faithfulness: Proportion of answer that can be verified from context

        Method:
        1. Split answer into claims (sentences)
        2. Check if each claim is supported by context
        3. Return proportion of supported claims with detailed analysis

        Returns:
            Dict with 'score' and 'details' containing claim-by-claim analysis
        """
        # Split answer into sentences (claims)
        sentences = re.split(r'[.!?]+', answer)
        claims = [s.strip() for s in sentences if len(s.strip()) > 10]

        if not claims:
            return {
                'score': 0.5,
                'details': {
                    'total_claims': 0,
                    'supported_claims': 0,
                    'claims_analysis': []
                }
            }

        # Combine context
        context_text = " ".join([chunk['content'] for chunk in context_chunks])

        # Calculate embedding similarity between each claim and context
        supported_count = 0
        claims_analysis = []

        for claim in claims:
            # Simple check: is claim mentioned in context? (can be enhanced with embeddings)
            claim_lower = claim.lower()
            context_lower = context_text.lower()

            # Check for keyword overlap (simple heuristic)
            claim_words = set(re.findall(r'\b\w+\b', claim_lower))
            context_words = set(re.findall(r'\b\w+\b', context_lower))

            # Ignore common stop words
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            claim_words = claim_words - stop_words
            context_words = context_words - stop_words

            # Check overlap
            overlap = 0
            is_supported = False
            supporting_chunks = []

            if claim_words:
                overlap = len(claim_words & context_words) / len(claim_words)
                is_supported = overlap > 0.3  # At least 30% word overlap
                if is_supported:
                    supported_count += 1

                    # Find which chunks support this claim
                    for chunk in context_chunks:
                        chunk_words = set(re.findall(r'\b\w+\b', chunk['content'].lower()))
                        chunk_words = chunk_words - stop_words
                        claim_chunk_overlap = len(claim_words & chunk_words) / len(claim_words) if claim_words else 0
                        if claim_chunk_overlap > 0.2:  # At least 20% overlap with this chunk
                            supporting_chunks.append({
                                'content': chunk['content'][:200] + '...' if len(chunk['content']) > 200 else chunk['content'],
                                'filename': chunk.get('filename', 'Unknown'),
                                'overlap': claim_chunk_overlap
                            })

            claims_analysis.append({
                'claim': claim,
                'supported': is_supported,
                'overlap_score': overlap,
                'supporting_chunks': supporting_chunks[:2]  # Limit to top 2 supporting chunks
            })

        faithfulness_score = supported_count / len(claims) if claims else 0.5
        logger.debug(f"Faithfulness: {supported_count}/{len(claims)} claims supported = {faithfulness_score:.2f}")

        return {
            'score': faithfulness_score,
            'details': {
                'total_claims': len(claims),
                'supported_claims': supported_count,
                'claims_analysis': claims_analysis
            }
        }

    async def _calculate_answer_relevancy(self, query: str, answer: str) -> float:
        """
        Answer Relevancy: How well does the answer address the query?

        Method:
        1. Calculate semantic similarity between query and answer embeddings
        2. Higher similarity means answer is more relevant to query
        """
        try:
            # Get embeddings
            query_embedding = await embedding_service.get_embedding(query)
            answer_embedding = await embedding_service.get_embedding(answer)

            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_embedding, answer_embedding)

            logger.debug(f"Answer Relevancy: {similarity:.2f}")
            return max(0.0, min(1.0, similarity))  # Clamp to [0, 1]

        except Exception as e:
            logger.warning(f"Error calculating answer relevancy: {e}")
            return 0.5  # Neutral on error

    def _calculate_context_relevancy(self, context_chunks: List[Dict]) -> Dict:
        """
        Context Relevancy: Average relevance score of retrieved chunks

        Uses the similarity scores from the retrieval

        Returns:
            Dict with 'score' and 'details' containing per-chunk analysis
        """
        if not context_chunks:
            return {'score': 0.0, 'details': None}

        relevance_scores = [chunk.get('similarity', 0) for chunk in context_chunks]
        avg_relevance = sum(relevance_scores) / len(relevance_scores)

        # Prepare detailed breakdown
        chunks_breakdown = [
            {
                'filename': chunk.get('filename', 'Unknown'),
                'similarity': chunk.get('similarity', 0),
                'semantic_score': chunk.get('semantic_score', 0),
                'keyword_score': chunk.get('keyword_score', 0),
                'memory_type': chunk.get('memory_type', 'long-term'),
                'excerpt': chunk['content'][:150] + '...' if len(chunk['content']) > 150 else chunk['content']
            }
            for chunk in context_chunks
        ]

        logger.debug(f"Context Relevancy: {avg_relevance:.2f} (avg of {len(relevance_scores)} chunks)")

        return {
            'score': avg_relevance,
            'details': {
                'chunks_count': len(context_chunks),
                'avg_similarity': avg_relevance,
                'min_similarity': min(relevance_scores) if relevance_scores else 0,
                'max_similarity': max(relevance_scores) if relevance_scores else 0,
                'chunks_breakdown': chunks_breakdown
            }
        }

    def _calculate_context_precision(self, context_chunks: List[Dict]) -> Dict:
        """
        Context Precision: Are the most relevant chunks ranked highest?

        Method:
        1. Check if chunks are sorted by relevance
        2. Calculate precision@k for different k values
        3. Reward configurations where high-relevance chunks come first

        Returns:
            Dict with 'score' and 'details' containing ranking analysis
        """
        if not context_chunks:
            return {'score': 0.0, 'details': None}

        # Get relevance scores
        scores = [chunk.get('similarity', 0) for chunk in context_chunks]

        # Check if scores are in descending order (ideal)
        is_sorted = all(scores[i] >= scores[i+1] for i in range(len(scores)-1))

        if is_sorted:
            precision = 1.0
        else:
            # Calculate how close to ideal ordering
            # Use Spearman rank correlation or simpler metric
            ideal_order = sorted(scores, reverse=True)
            matches = sum(1 for i, score in enumerate(scores) if score == ideal_order[i])
            precision = matches / len(scores)

        # Prepare ranking details
        ranking_details = [
            {
                'rank': i + 1,
                'filename': chunk.get('filename', 'Unknown'),
                'similarity': chunk.get('similarity', 0),
                'ideal_rank': sorted(range(len(scores)), key=lambda x: scores[x], reverse=True).index(i) + 1
            }
            for i, chunk in enumerate(context_chunks)
        ]

        logger.debug(f"Context Precision: {precision:.2f}")

        return {
            'score': precision,
            'details': {
                'is_perfectly_sorted': is_sorted,
                'total_chunks': len(context_chunks),
                'correctly_ranked': int(precision * len(context_chunks)),
                'ranking_details': ranking_details
            }
        }

    async def _calculate_answer_correctness(self, answer: str, expected_answer: str) -> float:
        """
        Answer Correctness: Semantic similarity with ground truth

        Only used for testing/evaluation when ground truth is available
        """
        try:
            answer_embedding = await embedding_service.get_embedding(answer)
            expected_embedding = await embedding_service.get_embedding(expected_answer)

            similarity = self._cosine_similarity(answer_embedding, expected_embedding)

            logger.debug(f"Answer Correctness: {similarity:.2f}")
            return max(0.0, min(1.0, similarity))

        except Exception as e:
            logger.warning(f"Error calculating answer correctness: {e}")
            return 0.0

    def _calculate_overall_score(self, metrics: Dict[str, float]) -> float:
        """
        Calculate weighted overall RAG score

        Weights:
        - Faithfulness: 30% (most important - answer must be grounded)
        - Answer Relevancy: 30% (answer must address query)
        - Context Relevancy: 20% (retrieved context must be relevant)
        - Context Precision: 20% (relevant context must rank high)
        """
        weights = {
            'faithfulness': 0.30,
            'answer_relevancy': 0.30,
            'context_relevancy': 0.20,
            'context_precision': 0.20
        }

        score = 0.0
        total_weight = 0.0

        for metric, weight in weights.items():
            if metric in metrics and metrics[metric] is not None:
                score += metrics[metric] * weight
                total_weight += weight

        # Normalize by total weight used
        if total_weight > 0:
            score = score / total_weight

        return max(0.0, min(1.0, score))

    def _get_quality_level(self, score: float) -> str:
        """
        Convert numerical score to quality level

        - Excellent: >= 0.8
        - Good: >= 0.6
        - Fair: >= 0.4
        - Poor: < 0.4
        """
        if score >= 0.8:
            return 'excellent'
        elif score >= 0.6:
            return 'good'
        elif score >= 0.4:
            return 'fair'
        else:
            return 'poor'

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            v1 = np.array(vec1)
            v2 = np.array(vec2)

            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)
            return float(similarity)

        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0

    def generate_quality_report(self, metrics: Dict[str, float]) -> str:
        """
        Generate human-readable quality report

        Returns formatted string with metrics and recommendations
        """
        report = []
        report.append("=" * 60)
        report.append("RAG QUALITY METRICS REPORT")
        report.append("=" * 60)

        # Overall Score
        rag_score = metrics.get('rag_score', 0)
        quality_level = metrics.get('quality_level', 'unknown')
        report.append(f"\n📊 Overall RAG Score: {rag_score:.2f} ({quality_level.upper()})")

        # Individual Metrics
        report.append("\n📈 Detailed Metrics:")
        report.append(f"   • Faithfulness:       {metrics.get('faithfulness', 0):.2f} - Answer grounded in context")
        report.append(f"   • Answer Relevancy:   {metrics.get('answer_relevancy', 0):.2f} - Answer addresses query")
        report.append(f"   • Context Relevancy:  {metrics.get('context_relevancy', 0):.2f} - Retrieved chunks relevant")
        report.append(f"   • Context Precision:  {metrics.get('context_precision', 0):.2f} - Relevant chunks ranked high")

        if 'answer_correctness' in metrics:
            report.append(f"   • Answer Correctness: {metrics.get('answer_correctness', 0):.2f} - Match with ground truth")

        # Recommendations
        report.append("\n💡 Recommendations:")

        if metrics.get('faithfulness', 1) < 0.6:
            report.append("   ⚠ LOW FAITHFULNESS: Answer contains claims not supported by context")
            report.append("      → Review context retrieval or tune LLM prompt")

        if metrics.get('answer_relevancy', 1) < 0.6:
            report.append("   ⚠ LOW ANSWER RELEVANCY: Answer doesn't directly address query")
            report.append("      → Improve query understanding or LLM instruction")

        if metrics.get('context_relevancy', 1) < 0.6:
            report.append("   ⚠ LOW CONTEXT RELEVANCY: Retrieved chunks have low relevance")
            report.append("      → Increase similarity threshold or improve embeddings")

        if metrics.get('context_precision', 1) < 0.6:
            report.append("   ⚠ LOW CONTEXT PRECISION: Most relevant chunks not ranked high")
            report.append("      → Review ranking algorithm or hybrid search weights")

        if rag_score >= 0.8:
            report.append("   ✅ Excellent quality - no major issues detected")

        report.append("=" * 60)

        return "\n".join(report)


# Singleton
quality_metrics_service = QualityMetricsService()
