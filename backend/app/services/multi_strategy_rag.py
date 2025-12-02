"""
Multi-Strategy RAG with Answer Fusion

Architecture:
1. Execute multiple strategies in parallel:
   - Direct LLM (no RAG)
   - RAG with short-term memory (session documents) - HIGHEST WEIGHT
   - RAG with long-term memory (all documents)
   - Tool-based answers (navigation, OCR, web scraping, etc.)

2. Score each candidate answer based on:
   - Source quality (short-term > long-term > no source)
   - Confidence/relevance scores
   - Answer completeness
   - Factuality signals

3. Select best answer or fuse multiple answers

Benefits:
- No single point of failure (classification errors don't break system)
- Context-aware weighting (recent uploads get priority)
- Multi-modal (combines LLM, RAG, and tools)
- Robust to edge cases

Author: AI Assistant
Date: 2025-11-24
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class AnswerStrategy(str, Enum):
    """Different strategies for generating answers"""
    DIRECT_LLM = "direct_llm"  # LLM without RAG
    RAG_SHORT_TERM = "rag_short_term"  # Session documents only
    RAG_LONG_TERM = "rag_long_term"  # All documents
    RAG_HYBRID = "rag_hybrid"  # Short-term + long-term combined
    TOOL_NAVIGATION = "tool_navigation"  # Web navigation tool
    TOOL_OCR = "tool_ocr"  # OCR for images
    TOOL_WEB_SCRAPING = "tool_web_scraping"  # Web scraping
    TOOL_DOCLING = "tool_docling"  # Complex PDF extraction


@dataclass
class CandidateAnswer:
    """Represents a candidate answer from a strategy"""
    strategy: AnswerStrategy
    answer: str
    confidence: float  # 0.0 to 1.0
    sources: List[Dict[str, Any]] = field(default_factory=list)
    num_sources: int = 0
    source_quality_score: float = 0.0  # Based on recency, relevance
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Scoring components
    relevance_score: float = 0.0  # How relevant to query
    completeness_score: float = 0.0  # How complete the answer is
    factuality_score: float = 0.0  # Signals of factual accuracy

    # Final weighted score
    final_score: float = 0.0


class MultiStrategyRAG:
    """
    Multi-Strategy RAG with Answer Fusion

    Executes multiple answer strategies in parallel and selects the best one.
    Gives higher weight to short-term memory (recent uploads).
    """

    def __init__(self):
        """Initialize multi-strategy RAG"""
        # Strategy weights (how much to trust each strategy)
        self.strategy_weights = {
            AnswerStrategy.RAG_SHORT_TERM: 1.0,  # HIGHEST - recent uploads
            AnswerStrategy.RAG_HYBRID: 0.95,
            AnswerStrategy.RAG_LONG_TERM: 0.85,
            AnswerStrategy.DIRECT_LLM: 0.75,  # Lower weight (no sources)
            AnswerStrategy.TOOL_NAVIGATION: 0.90,
            AnswerStrategy.TOOL_OCR: 0.90,
            AnswerStrategy.TOOL_WEB_SCRAPING: 0.85,
            AnswerStrategy.TOOL_DOCLING: 0.90
        }

        # Source quality weights (recency matters!)
        self.source_weights = {
            "short_term": 1.0,  # Session documents (uploaded recently)
            "long_term": 0.7,   # Historical documents
            "web": 0.6,         # Web scraped content
            "general": 0.5      # No specific source
        }

    async def query(
        self,
        query_text: str,
        session_id: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        model_id: Optional[str] = None,
        db = None,
        # Strategy selection
        enable_direct_llm: bool = True,
        enable_rag_short_term: bool = True,
        enable_rag_long_term: bool = True,
        enable_tools: bool = False,
        # Scoring parameters
        min_confidence: float = 0.3,  # Minimum confidence to consider
        diversity_bonus: float = 0.1  # Bonus for answers with sources
    ) -> Dict[str, Any]:
        """
        Execute multiple strategies and return the best answer

        Args:
            query_text: User query
            session_id: Session ID for short-term memory
            user_id: User ID
            model_id: LLM model to use
            db: Database session
            enable_*: Flags to enable/disable strategies
            min_confidence: Minimum confidence threshold
            diversity_bonus: Bonus score for answers with sources

        Returns:
            Best answer with metadata about strategy used
        """
        start_time = time.time()

        logger.info(f"🔀 Multi-Strategy RAG for query: {query_text[:50]}...")

        # Step 1: Execute all enabled strategies in parallel
        candidates = await self._execute_strategies(
            query_text=query_text,
            session_id=session_id,
            user_id=user_id,
            model_id=model_id,
            db=db,
            enable_direct_llm=enable_direct_llm,
            enable_rag_short_term=enable_rag_short_term,
            enable_rag_long_term=enable_rag_long_term,
            enable_tools=enable_tools
        )

        # Step 2: Score and rank candidates
        ranked_candidates = self._score_and_rank(
            candidates=candidates,
            query_text=query_text,
            min_confidence=min_confidence,
            diversity_bonus=diversity_bonus
        )

        # Step 3: Select best answer
        if not ranked_candidates:
            logger.warning("No valid candidates found, using fallback")
            return await self._fallback_answer(query_text, model_id)

        best_answer = ranked_candidates[0]

        # Step 4: Log strategy selection
        total_time = (time.time() - start_time) * 1000

        logger.info(
            f"✅ Selected strategy: {best_answer.strategy.value} "
            f"(score: {best_answer.final_score:.3f}, "
            f"confidence: {best_answer.confidence:.3f}, "
            f"sources: {best_answer.num_sources})"
        )

        # Return result with metadata
        return {
            "answer": best_answer.answer,
            "strategy_used": best_answer.strategy.value,
            "confidence": best_answer.confidence,
            "final_score": best_answer.final_score,
            "sources": best_answer.sources,
            "num_sources": best_answer.num_sources,
            "latency_ms": total_time,
            "metadata": {
                **best_answer.metadata,
                "candidates_evaluated": len(candidates),
                "top_3_strategies": [
                    {
                        "strategy": c.strategy.value,
                        "score": c.final_score,
                        "confidence": c.confidence
                    }
                    for c in ranked_candidates[:3]
                ],
                "strategy_weights_used": {
                    k.value: v for k, v in self.strategy_weights.items()
                }
            }
        }

    async def _execute_strategies(
        self,
        query_text: str,
        session_id: Optional[str],
        user_id: Optional[uuid.UUID],
        model_id: Optional[str],
        db,
        enable_direct_llm: bool,
        enable_rag_short_term: bool,
        enable_rag_long_term: bool,
        enable_tools: bool
    ) -> List[CandidateAnswer]:
        """
        Execute all enabled strategies in parallel

        Returns list of candidate answers
        """
        tasks = []

        # Strategy 1: Direct LLM (no RAG)
        if enable_direct_llm:
            tasks.append(self._execute_direct_llm(query_text, model_id))

        # Strategy 2: RAG with short-term memory (session docs)
        if enable_rag_short_term and session_id:
            tasks.append(self._execute_rag_short_term(query_text, session_id, model_id, db))

        # Strategy 3: RAG with long-term memory (all docs)
        if enable_rag_long_term:
            tasks.append(self._execute_rag_long_term(query_text, model_id, db))

        # Strategy 4: Hybrid RAG (short + long term combined)
        if enable_rag_short_term and enable_rag_long_term and session_id:
            tasks.append(self._execute_rag_hybrid(query_text, session_id, model_id, db))

        # Strategy 5-N: Tool-based strategies (if enabled)
        if enable_tools:
            # Add tool strategies here
            pass

        # Execute all strategies in parallel
        logger.info(f"Executing {len(tasks)} strategies in parallel...")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out failures
        candidates = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Strategy {i} failed: {result}")
            elif result:
                candidates.append(result)

        logger.info(f"✓ Got {len(candidates)} valid candidate answers")

        return candidates

    async def _execute_direct_llm(
        self,
        query_text: str,
        model_id: Optional[str]
    ) -> CandidateAnswer:
        """Execute direct LLM strategy (no RAG)"""
        start_time = time.time()

        try:
            # Import LLM service
            from app.services.llm_service import llm_service

            # Generate answer directly
            result = await llm_service.generate(
                prompt=query_text,
                model_id=model_id,
                max_tokens=500,
                temperature=0.7
            )

            answer = result.get('content', '')
            latency_ms = (time.time() - start_time) * 1000

            # Estimate confidence based on answer length and coherence
            confidence = self._estimate_confidence(answer)

            candidate = CandidateAnswer(
                strategy=AnswerStrategy.DIRECT_LLM,
                answer=answer,
                confidence=confidence,
                sources=[],
                num_sources=0,
                source_quality_score=self.source_weights["general"],
                latency_ms=latency_ms,
                metadata={
                    "model": model_id,
                    "tokens": result.get('tokens', 0)
                }
            )

            logger.debug(f"Direct LLM: confidence={confidence:.2f}, latency={latency_ms:.0f}ms")

            return candidate

        except Exception as e:
            logger.error(f"Direct LLM strategy failed: {e}")
            raise

    async def _execute_rag_short_term(
        self,
        query_text: str,
        session_id: str,
        model_id: Optional[str],
        db
    ) -> CandidateAnswer:
        """Execute RAG with short-term memory (session documents only)"""
        start_time = time.time()

        try:
            from app.services.rag_service import rag_service

            # Query with session documents only
            result = await rag_service.query(
                query_text=query_text,
                session_id=session_id,
                model_id=model_id,
                db=db,
                use_cache=False  # Fresh results for comparison
            )

            latency_ms = (time.time() - start_time) * 1000

            # Extract sources and calculate quality
            sources = result.get('sources', [])
            num_sources = len(sources)

            # Short-term memory gets HIGHEST source quality score
            source_quality = self.source_weights["short_term"] if num_sources > 0 else 0.0

            candidate = CandidateAnswer(
                strategy=AnswerStrategy.RAG_SHORT_TERM,
                answer=result.get('answer', ''),
                confidence=result.get('confidence', 0.5),
                sources=sources,
                num_sources=num_sources,
                source_quality_score=source_quality,
                latency_ms=latency_ms,
                metadata={
                    "model": result.get('model', model_id),
                    "chunks_retrieved": result.get('metadata', {}).get('chunks_retrieved', 0),
                    "memory_type": "short_term"
                }
            )

            logger.debug(
                f"RAG Short-Term: sources={num_sources}, "
                f"confidence={candidate.confidence:.2f}, "
                f"latency={latency_ms:.0f}ms"
            )

            return candidate

        except Exception as e:
            logger.error(f"RAG short-term strategy failed: {e}")
            raise

    async def _execute_rag_long_term(
        self,
        query_text: str,
        model_id: Optional[str],
        db
    ) -> CandidateAnswer:
        """Execute RAG with long-term memory (all documents)"""
        start_time = time.time()

        try:
            from app.services.rag_service import rag_service

            # Query all documents (no session filter)
            result = await rag_service.query(
                query_text=query_text,
                session_id=None,  # No session filter
                model_id=model_id,
                db=db,
                use_cache=False
            )

            latency_ms = (time.time() - start_time) * 1000

            sources = result.get('sources', [])
            num_sources = len(sources)

            # Long-term memory gets lower weight than short-term
            source_quality = self.source_weights["long_term"] if num_sources > 0 else 0.0

            candidate = CandidateAnswer(
                strategy=AnswerStrategy.RAG_LONG_TERM,
                answer=result.get('answer', ''),
                confidence=result.get('confidence', 0.5),
                sources=sources,
                num_sources=num_sources,
                source_quality_score=source_quality,
                latency_ms=latency_ms,
                metadata={
                    "model": result.get('model', model_id),
                    "chunks_retrieved": result.get('metadata', {}).get('chunks_retrieved', 0),
                    "memory_type": "long_term"
                }
            )

            logger.debug(
                f"RAG Long-Term: sources={num_sources}, "
                f"confidence={candidate.confidence:.2f}, "
                f"latency={latency_ms:.0f}ms"
            )

            return candidate

        except Exception as e:
            logger.error(f"RAG long-term strategy failed: {e}")
            raise

    async def _execute_rag_hybrid(
        self,
        query_text: str,
        session_id: str,
        model_id: Optional[str],
        db
    ) -> CandidateAnswer:
        """Execute hybrid RAG (combines short-term and long-term)"""
        # This would merge results from both short-term and long-term
        # For now, just a placeholder
        # In production, this would intelligently merge and rerank
        pass

    def _score_and_rank(
        self,
        candidates: List[CandidateAnswer],
        query_text: str,
        min_confidence: float,
        diversity_bonus: float
    ) -> List[CandidateAnswer]:
        """
        Score and rank candidate answers

        Scoring formula:
        final_score = (
            strategy_weight * 0.3 +
            confidence * 0.25 +
            source_quality_score * 0.25 +
            relevance_score * 0.15 +
            completeness_score * 0.05
        ) + diversity_bonus (if has sources)

        Returns candidates sorted by final_score (highest first)
        """
        for candidate in candidates:
            # Get strategy weight
            strategy_weight = self.strategy_weights.get(candidate.strategy, 0.5)

            # Calculate relevance (placeholder - could use semantic similarity)
            relevance = self._calculate_relevance(candidate.answer, query_text)

            # Calculate completeness (answer length, structure)
            completeness = self._calculate_completeness(candidate.answer)

            # Apply diversity bonus for answers with sources
            diversity = diversity_bonus if candidate.num_sources > 0 else 0.0

            # Final weighted score
            candidate.final_score = (
                strategy_weight * 0.30 +
                candidate.confidence * 0.25 +
                candidate.source_quality_score * 0.25 +
                relevance * 0.15 +
                completeness * 0.05 +
                diversity
            )

            # Store component scores
            candidate.relevance_score = relevance
            candidate.completeness_score = completeness

        # Filter by minimum confidence
        valid_candidates = [
            c for c in candidates
            if c.confidence >= min_confidence
        ]

        # Sort by final score (descending)
        ranked = sorted(valid_candidates, key=lambda c: c.final_score, reverse=True)

        # Log ranking
        logger.info(f"📊 Ranked {len(ranked)} candidates:")
        for i, c in enumerate(ranked[:5]):  # Top 5
            logger.info(
                f"  {i+1}. {c.strategy.value}: "
                f"score={c.final_score:.3f} "
                f"(conf={c.confidence:.2f}, sources={c.num_sources})"
            )

        return ranked

    def _calculate_relevance(self, answer: str, query: str) -> float:
        """
        Calculate relevance of answer to query

        Simple implementation: keyword overlap
        Could be enhanced with semantic similarity
        """
        if not answer or not query:
            return 0.0

        # Normalize
        answer_words = set(answer.lower().split())
        query_words = set(query.lower().split())

        # Calculate overlap
        overlap = len(answer_words & query_words)
        max_possible = len(query_words)

        if max_possible == 0:
            return 0.5

        relevance = min(1.0, overlap / max_possible)

        return relevance

    def _calculate_completeness(self, answer: str) -> float:
        """
        Calculate completeness of answer

        Based on length and structure
        """
        if not answer:
            return 0.0

        # Length score (longer answers are more complete, up to a point)
        length = len(answer)
        if length < 50:
            length_score = length / 50  # Scale 0-1 for short answers
        elif length < 500:
            length_score = 1.0  # Ideal length
        else:
            length_score = max(0.7, 1.0 - (length - 500) / 1000)  # Penalty for very long

        # Structure score (has sentences, punctuation)
        has_sentences = '.' in answer or '!' in answer or '?' in answer
        has_paragraphs = '\n' in answer

        structure_score = 0.5
        if has_sentences:
            structure_score += 0.25
        if has_paragraphs:
            structure_score += 0.25

        completeness = (length_score + structure_score) / 2

        return min(1.0, completeness)

    def _estimate_confidence(self, answer: str) -> float:
        """
        Estimate confidence for answers without explicit confidence scores

        Based on answer characteristics
        """
        if not answer:
            return 0.0

        confidence = 0.5  # Base confidence

        # Boost for length
        if len(answer) > 100:
            confidence += 0.1

        # Boost for structure
        if '.' in answer:
            confidence += 0.1

        # Penalty for uncertainty words
        uncertainty_words = ['maybe', 'might', 'possibly', 'perhaps', 'uncertain']
        if any(word in answer.lower() for word in uncertainty_words):
            confidence -= 0.2

        # Penalty for "I don't know" type responses
        if 'don\'t know' in answer.lower() or 'no information' in answer.lower():
            confidence -= 0.3

        return max(0.0, min(1.0, confidence))

    async def _fallback_answer(self, query_text: str, model_id: Optional[str]) -> Dict[str, Any]:
        """Fallback answer when all strategies fail"""
        from app.services.llm_service import llm_service

        try:
            result = await llm_service.generate(
                prompt=query_text,
                model_id=model_id,
                max_tokens=300,
                temperature=0.5
            )

            return {
                "answer": result.get('content', 'I apologize, but I could not generate a satisfactory answer.'),
                "strategy_used": "fallback",
                "confidence": 0.3,
                "sources": [],
                "num_sources": 0,
                "metadata": {"fallback": True}
            }
        except Exception as e:
            logger.error(f"Fallback answer failed: {e}")
            return {
                "answer": "I apologize, but I encountered an error processing your query.",
                "strategy_used": "error",
                "confidence": 0.0,
                "sources": [],
                "num_sources": 0,
                "metadata": {"error": str(e)}
            }


# Singleton
multi_strategy_rag = MultiStrategyRAG()
