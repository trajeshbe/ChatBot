"""
CRU Multi-Pipeline Router - Query Classification and Routing

Routes queries to optimal retrieval pipeline:
- SEMANTIC → pgvector (meaning-based, no exact keywords)
- KEYWORD → Elasticsearch (exact term match, filters)
- HYBRID → Both + RRF fusion
- TABLE_DATA → Elasticsearch (structured data)

Reuses:
- tier_1.llm.llm_service: LLM for query classification

Author: Claude Code
Date: 2026-01-02
"""

from enum import Enum
from typing import List, Optional
import logging

from app.tier_1.llm.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class PipelineType(str, Enum):
    """Available retrieval pipelines."""
    PGVECTOR = "pgvector"          # Semantic search with pgvector
    ELASTICSEARCH = "elasticsearch"  # Keyword search with BM25
    HYBRID = "hybrid"                # Both pipelines + RRF fusion


class QueryType(str, Enum):
    """Query classification categories."""
    SEMANTIC = "semantic"      # Meaning-based, no exact keywords needed
    KEYWORD = "keyword"        # Exact term match needed
    HYBRID = "hybrid"          # Both semantic meaning and specific terms
    TABLE_DATA = "table_data"  # Looking for structured data/tables


class MultiPipelineRouter:
    """
    Route queries to optimal retrieval pipeline(s).

    Uses LLM to classify query intent and select best pipeline strategy.

    Example:
        router = MultiPipelineRouter()

        # Semantic query
        query_type = await router.classify_query("What are the key risks in this project?")
        # Returns: QueryType.SEMANTIC

        pipelines = await router.route_query("What are the key risks?")
        # Returns: [PipelineType.PGVECTOR]

        # Hybrid query
        pipelines = await router.route_query("Capex for Gold Valley project 2024")
        # Returns: [PipelineType.HYBRID]
    """

    def __init__(self, llm_service=None):
        """
        Initialize router.

        Args:
            llm_service: Optional LLM service (uses singleton if not provided)
        """
        self.llm = llm_service or get_llm_service()
        logger.info("🔀 MultiPipelineRouter initialized")

    async def classify_query(self, query: str) -> QueryType:
        """
        Classify query type using LLM.

        Args:
            query: User query string

        Returns:
            QueryType enum value

        Examples:
            "What are the key risks?" → SEMANTIC
            "Find documents mentioning Gold Valley" → KEYWORD
            "Capex for Gold Valley 2024" → HYBRID
            "Iron ore grades by drilling site" → TABLE_DATA
        """
        logger.info(f"🔍 Classifying query: {query[:100]}...")

        prompt = f"""Classify this mining industry query into ONE of these types:

1. SEMANTIC - Meaning-based, no exact keywords needed
   Examples: "What are the main environmental risks?", "Explain the project challenges"

2. KEYWORD - Exact term match needed (proper nouns, project names, specific terminology)
   Examples: "Find documents mentioning Gold Valley", "Documents about feasibility studies"

3. HYBRID - Both semantic meaning AND specific terms (most common)
   Examples: "Capex for Gold Valley project 2024", "Iron ore production targets in Phase 2"

4. TABLE_DATA - Looking for structured data, tables, or numerical comparisons
   Examples: "Iron ore grades by drilling site", "Compare capex across all projects"

Query: "{query}"

Return ONLY the classification type (SEMANTIC, KEYWORD, HYBRID, or TABLE_DATA). No explanation."""

        try:
            response = await self.llm.generate(
                prompt=prompt,
                model_id="gpt-4o-mini",
                temperature=0.0,  # Deterministic classification
                max_tokens=20
            )

            classification = response.get("content", "SEMANTIC").strip().upper()

            # Validate classification
            try:
                query_type = QueryType[classification]
                logger.info(f"✅ Query classified as: {query_type.value}")
                return query_type
            except KeyError:
                logger.warning(f"⚠️ Invalid classification '{classification}', defaulting to SEMANTIC")
                return QueryType.SEMANTIC

        except Exception as e:
            logger.error(f"❌ Query classification failed: {e}")
            # Default fallback: SEMANTIC (safest choice)
            return QueryType.SEMANTIC

    async def route_query(
        self,
        query: str,
        query_type: Optional[QueryType] = None
    ) -> List[PipelineType]:
        """
        Route query to appropriate pipeline(s).

        Args:
            query: User query string
            query_type: Optional pre-classified query type (auto-classifies if None)

        Returns:
            List of pipelines to use (in order of priority)

        Routing Logic:
            SEMANTIC → [PGVECTOR]
            KEYWORD → [ELASTICSEARCH]
            HYBRID → [HYBRID] (both pipelines + RRF)
            TABLE_DATA → [ELASTICSEARCH] (better for structured data)
        """
        # Classify if not provided
        if query_type is None:
            query_type = await self.classify_query(query)

        # Route based on classification
        if query_type == QueryType.SEMANTIC:
            logger.info("🎯 Routing to: PGVECTOR (semantic search)")
            return [PipelineType.PGVECTOR]

        elif query_type == QueryType.KEYWORD:
            logger.info("🎯 Routing to: ELASTICSEARCH (keyword search)")
            return [PipelineType.ELASTICSEARCH]

        elif query_type == QueryType.HYBRID:
            logger.info("🎯 Routing to: HYBRID (pgvector + Elasticsearch + RRF)")
            return [PipelineType.HYBRID]

        elif query_type == QueryType.TABLE_DATA:
            logger.info("🎯 Routing to: ELASTICSEARCH (structured data)")
            return [PipelineType.ELASTICSEARCH]

        else:
            # Default fallback
            logger.warning(f"⚠️ Unknown query type {query_type}, defaulting to PGVECTOR")
            return [PipelineType.PGVECTOR]

    def explain_routing(self, query_type: QueryType, pipelines: List[PipelineType]) -> str:
        """
        Generate human-readable explanation of routing decision.

        Args:
            query_type: Classified query type
            pipelines: Selected pipelines

        Returns:
            Explanation string
        """
        explanations = {
            (QueryType.SEMANTIC, [PipelineType.PGVECTOR]):
                "Using semantic search (pgvector) for meaning-based retrieval",

            (QueryType.KEYWORD, [PipelineType.ELASTICSEARCH]):
                "Using keyword search (Elasticsearch BM25) for exact term matching",

            (QueryType.HYBRID, [PipelineType.HYBRID]):
                "Using hybrid approach: combining pgvector (semantic) + Elasticsearch (keyword) with RRF fusion",

            (QueryType.TABLE_DATA, [PipelineType.ELASTICSEARCH]):
                "Using Elasticsearch for structured data and table retrieval"
        }

        key = (query_type, pipelines)
        return explanations.get(key, f"Using {', '.join(p.value for p in pipelines)} pipeline(s)")


# Singleton instance
_multi_pipeline_router = None

def get_multi_pipeline_router() -> MultiPipelineRouter:
    """
    Get singleton MultiPipelineRouter instance.

    Returns:
        MultiPipelineRouter instance
    """
    global _multi_pipeline_router
    if _multi_pipeline_router is None:
        _multi_pipeline_router = MultiPipelineRouter()
    return _multi_pipeline_router
