"""
Intelligent Retrieval Service - Query-Time Strategy Matching

Analyzes user queries and matches them to optimal embedding strategy for retrieval:
- Table queries → table_embedding column
- Visual queries → visual_embedding column
- Code queries → code_embedding column
- Text queries → embedding column

Philosophy:
- Analyze query intent (what is the user looking for?)
- Match query type to content type
- Search in appropriate vector column
- Use correct similarity metric
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_
import numpy as np

from app.models.database import DocumentChunk
from app.services.intelligent_embedding_service import intelligent_embedding_service
from app.services.content_analyzer import SimilarityMetric

logger = logging.getLogger(__name__)


class QueryType:
    """Query type classification for strategy matching"""
    TEXT = "text"               # General text queries
    TABLE = "table"             # Queries about tables, data, numbers
    VISUAL = "visual"           # Queries about images, diagrams, charts
    CODE = "code"               # Queries about code, functions, algorithms
    NUMERICAL = "numerical"     # Queries about statistics, calculations
    MULTI_MODAL = "multi_modal" # Queries spanning multiple types


class IntelligentRetrievalService:
    """
    Intelligent retrieval service with query-time strategy matching

    Analyzes query → Selects strategy → Searches appropriate vector column
    """

    def __init__(self):
        """Initialize intelligent retrieval service"""
        self.query_type_keywords = {
            QueryType.TABLE: [
                "table", "row", "column", "data", "spreadsheet", "excel",
                "csv", "numbers", "values", "entries", "records", "fields"
            ],
            QueryType.VISUAL: [
                "image", "images", "diagram", "diagrams", "chart", "charts",
                "graph", "graphs", "picture", "pictures", "figure", "figures",
                "illustration", "illustrations", "visual", "visuals",
                "screenshot", "screenshots", "photo", "photos", "drawing", "drawings"
            ],
            QueryType.CODE: [
                "code", "function", "class", "method", "algorithm", "implementation",
                "script", "program", "variable", "syntax", "python", "javascript",
                "java", "c++", "programming"
            ],
            QueryType.NUMERICAL: [
                "calculate", "sum", "average", "mean", "median", "statistics",
                "total", "count", "percentage", "ratio", "analysis"
            ]
        }

        # Strategy to vector column mapping
        self.strategy_to_column = {
            "text_semantic": "embedding",
            "table_structure": "table_embedding",
            "vision": "visual_embedding",
            "code": "code_embedding",
            "numerical": "numerical_embedding"
        }

        # Strategy to similarity metric mapping
        self.strategy_to_metric = {
            "text_semantic": SimilarityMetric.COSINE,
            "table_structure": SimilarityMetric.STRUCTURAL,
            "vision": SimilarityMetric.DOT_PRODUCT,
            "code": SimilarityMetric.COSINE,
            "numerical": SimilarityMetric.STATISTICAL
        }

        # Hybrid classification configuration
        self.keyword_confidence_threshold = 0.8  # Use LLM if keyword confidence < 0.8
        self.llm_fallback_enabled = True  # Enable LLM fallback for ambiguous queries

    async def classify_query(self, query: str) -> Dict[str, Any]:
        """
        🔀 HYBRID Query Classification: Keywords (fast) + LLM (smart)

        Flow:
        1. Try keyword matching (0ms) - Fast path for obvious queries
        2. If confidence < threshold, use LLM (~500ms) - Smart path for ambiguous queries

        Args:
            query: User query text

        Returns:
            {
                "query_type": str,          # Detected query type
                "strategy": str,            # Embedding strategy to use
                "vector_column": str,       # Database column to search
                "similarity_metric": str,   # Similarity metric to use
                "confidence": float,        # Classification confidence
                "reasoning": str,           # Why this classification
                "method": str               # "keyword" or "llm"
            }
        """
        # STEP 1: Try keyword matching (FAST PATH - 0ms)
        keyword_result = self._keyword_classify(query)

        # STEP 2: If confidence is high, use keyword result
        if keyword_result["confidence"] >= self.keyword_confidence_threshold:
            logger.info(
                f"⚡ FAST PATH - Keyword Classification:\n"
                f"   Query: {query[:100]}...\n"
                f"   Strategy: {keyword_result['strategy']}\n"
                f"   Confidence: {keyword_result['confidence']:.2f}\n"
                f"   Reasoning: {keyword_result['reasoning']}"
            )
            return keyword_result

        # STEP 3: Low confidence - fallback to LLM (SMART PATH - ~500ms)
        if self.llm_fallback_enabled:
            logger.info(
                f"🧠 SMART PATH - LLM Classification (keyword confidence {keyword_result['confidence']:.2f} < {self.keyword_confidence_threshold}):\n"
                f"   Query: {query[:100]}..."
            )

            try:
                llm_result = await self._llm_classify_embedding_strategy(query)
                logger.info(
                    f"✅ LLM Classification:\n"
                    f"   Strategy: {llm_result['strategy']}\n"
                    f"   Confidence: {llm_result['confidence']:.2f}\n"
                    f"   Reasoning: {llm_result['reasoning']}"
                )
                return llm_result
            except Exception as e:
                logger.warning(f"⚠️  LLM classification failed: {e}, using keyword result")
                return keyword_result
        else:
            # LLM fallback disabled - use keyword result
            logger.info(
                f"⚡ Using keyword result (LLM fallback disabled):\n"
                f"   Strategy: {keyword_result['strategy']}\n"
                f"   Confidence: {keyword_result['confidence']:.2f}"
            )
            return keyword_result

    def _keyword_classify(self, query: str) -> Dict[str, Any]:
        """
        Keyword-based query classification (FAST - 0ms)

        Returns classification dict with method="keyword"
        """
        query_lower = query.lower()

        # Count keyword matches for each query type
        type_scores = {}
        for query_type, keywords in self.query_type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                type_scores[query_type] = score

        # Determine query type
        if not type_scores:
            # Default to text semantic
            query_type = QueryType.TEXT
            confidence = 0.5
            reasoning = "No keywords detected (keyword matching)"
        elif len(type_scores) > 1:
            # Multi-modal query
            query_type = QueryType.MULTI_MODAL
            confidence = 0.7
            reasoning = f"Multiple keywords matched: {', '.join(type_scores.keys())}"
        else:
            # Single type detected
            query_type = list(type_scores.keys())[0]
            confidence = min(0.95, 0.6 + (type_scores[query_type] * 0.1))
            reasoning = f"Keyword matched: {query_type} ({type_scores[query_type]} matches)"

        # Map query type to strategy
        if query_type == QueryType.TEXT:
            strategy = "text_semantic"
        elif query_type == QueryType.TABLE:
            strategy = "table_structure"
        elif query_type == QueryType.VISUAL:
            strategy = "vision"
        elif query_type == QueryType.CODE:
            strategy = "code"
        elif query_type == QueryType.NUMERICAL:
            strategy = "numerical"
        elif query_type == QueryType.MULTI_MODAL:
            strategy = "text_semantic"  # Default for multi-modal
        else:
            strategy = "text_semantic"

        vector_column = self.strategy_to_column.get(strategy, "embedding")
        similarity_metric = self.strategy_to_metric.get(
            strategy,
            SimilarityMetric.COSINE
        )

        return {
            "query_type": query_type,
            "strategy": strategy,
            "vector_column": vector_column,
            "similarity_metric": similarity_metric.value,
            "confidence": confidence,
            "reasoning": reasoning,
            "method": "keyword"  # Classification method
        }

    async def _llm_classify_embedding_strategy(self, query: str) -> Dict[str, Any]:
        """
        LLM-based embedding strategy classification (SMART - ~500ms)

        Uses LLM to intelligently determine retrieval strategy for ambiguous queries
        like "describe what's illustrated" or "explain the visual concepts".

        Returns classification dict with method="llm"
        """
        import json
        from app.services.llm_service import llm_service

        prompt = f"""Analyze this query and determine the best retrieval strategy for a document search system.

Query: "{query}"

Available Strategies:
- **text_semantic**: Standard text search (e.g., "explain the process", "what is X", "summarize")
- **vision**: Visual content search (e.g., "show diagrams", "describe images", "what's illustrated", "visual concepts", "pictures showing")
- **table**: Structured data search (e.g., "data in table", "show values", "spreadsheet content")
- **code**: Code search (e.g., "find function", "show implementation", "code snippet")

Respond with ONLY a JSON object (no markdown, no code blocks):
{{
    "strategy": "text_semantic|vision|table|code",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of why this strategy"
}}
"""

        try:
            # Call LLM service
            response = await llm_service.generate(
                prompt=prompt,
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=150
            )

            # Parse JSON response
            response_text = response.get("response", "").strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:].strip()

            result = json.loads(response_text)

            strategy = result.get("strategy", "text_semantic")
            confidence = float(result.get("confidence", 0.8))
            reasoning = result.get("reasoning", "LLM classification")

            # Map to query type
            if strategy == "vision":
                query_type = QueryType.VISUAL
            elif strategy == "table":
                query_type = QueryType.TABLE
            elif strategy == "code":
                query_type = QueryType.CODE
            else:
                query_type = QueryType.TEXT

            vector_column = self.strategy_to_column.get(strategy, "embedding")
            similarity_metric = self.strategy_to_metric.get(
                strategy,
                SimilarityMetric.COSINE
            )

            return {
                "query_type": query_type,
                "strategy": strategy,
                "vector_column": vector_column,
                "similarity_metric": similarity_metric.value,
                "confidence": confidence,
                "reasoning": f"LLM: {reasoning}",
                "method": "llm"  # Classification method
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            raise ValueError(f"LLM returned invalid JSON: {response_text}")
        except Exception as e:
            logger.error(f"LLM classification error: {e}")
            raise

    async def retrieve(
        self,
        query: str,
        db: Session,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Intelligent retrieval with query-time strategy matching

        Args:
            query: User query text
            db: Database session
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
            session_id: Session ID for filtering
            project_id: Project ID for filtering
            user_id: User ID for access control

        Returns:
            {
                "results": List[Dict],       # Retrieved chunks with scores
                "query_classification": Dict, # Query analysis results
                "strategy_used": str,         # Strategy actually used
                "total_searched": int,        # Total chunks searched
                "total_returned": int         # Total results returned
            }
        """
        # Step 1: Classify query (hybrid: keywords + LLM)
        classification = await self.classify_query(query)
        strategy = classification["strategy"]
        vector_column = classification["vector_column"]
        similarity_metric = classification["similarity_metric"]

        logger.info(f"🎯 Retrieving with strategy: {strategy}")

        # Step 2: Generate query embedding with appropriate strategy
        query_embedding = await intelligent_embedding_service.get_embedding(
            text=query,
            strategy=strategy
        )

        # Step 3: Build database query
        # First, check if any chunks use this strategy
        stmt = select(DocumentChunk).where(
            and_(
                getattr(DocumentChunk, vector_column).isnot(None),
                # Access control filters
                *self._build_access_filters(session_id, project_id, user_id)
            )
        )

        chunks = db.execute(stmt).scalars().all()
        total_searched = len(chunks)

        if total_searched == 0:
            # No chunks with this embedding strategy - fallback to text semantic
            logger.warning(
                f"⚠️  No chunks found with {strategy} embeddings, "
                f"falling back to text_semantic"
            )

            # Fallback to text semantic (force keyword classification to avoid extra LLM call)
            classification = self._keyword_classify(query)
            classification["strategy"] = "text_semantic"
            classification["vector_column"] = "embedding"
            classification["similarity_metric"] = SimilarityMetric.COSINE.value

            query_embedding = await intelligent_embedding_service.get_embedding(
                text=query,
                strategy="text_semantic"
            )

            stmt = select(DocumentChunk).where(
                and_(
                    DocumentChunk.embedding.isnot(None),
                    *self._build_access_filters(session_id, project_id, user_id)
                )
            )

            chunks = db.execute(stmt).scalars().all()
            total_searched = len(chunks)
            vector_column = "embedding"

        # Step 4: Calculate similarities
        results = []
        for chunk in chunks:
            chunk_embedding = getattr(chunk, vector_column)
            if chunk_embedding is None:
                continue

            # Calculate similarity
            similarity = intelligent_embedding_service.calculate_similarity(
                embedding_a=query_embedding,
                embedding_b=chunk_embedding,
                metric=similarity_metric.replace("_", "")  # Convert to method format
            )

            # Filter by threshold
            if similarity >= similarity_threshold:
                results.append({
                    "chunk_id": str(chunk.id),
                    "document_id": str(chunk.document_id),
                    "content": chunk.content,
                    "similarity": similarity,
                    "chunk_index": chunk.chunk_index,
                    "embedding_strategy": chunk.embedding_strategy,
                    "meta_info": chunk.meta_info
                })

        # Step 5: Sort by similarity and return top_k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        top_results = results[:top_k]

        logger.info(
            f"✅ Retrieved {len(top_results)} results "
            f"(searched {total_searched} chunks, "
            f"{len(results)} above threshold)"
        )

        return {
            "results": top_results,
            "query_classification": classification,
            "strategy_used": classification["strategy"],
            "total_searched": total_searched,
            "total_returned": len(top_results)
        }

    def _build_access_filters(
        self,
        session_id: Optional[str],
        project_id: Optional[str],
        user_id: Optional[str]
    ) -> List:
        """
        Build access control filters for query

        Args:
            session_id: Session ID for session-scoped search
            project_id: Project ID for project-scoped search
            user_id: User ID for user-scoped search

        Returns:
            List of SQLAlchemy filter conditions
        """
        filters = []

        # TODO: Implement full RBAC filtering
        # For now, basic filtering by project and user

        if project_id:
            filters.append(DocumentChunk.project_id == project_id)

        if user_id:
            filters.append(DocumentChunk.uploaded_by == user_id)

        return filters

    async def retrieve_multi_strategy(
        self,
        query: str,
        db: Session,
        strategies: List[str],
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve using multiple strategies and merge results

        Args:
            query: User query text
            db: Database session
            strategies: List of strategies to use
            top_k: Number of results per strategy
            similarity_threshold: Minimum similarity score
            session_id: Session ID for filtering
            project_id: Project ID for filtering
            user_id: User ID for access control

        Returns:
            {
                "results": List[Dict],           # Merged results
                "strategy_results": Dict[str, List], # Results per strategy
                "strategies_used": List[str]     # Strategies actually used
            }
        """
        logger.info(f"🔍 Multi-strategy retrieval: {strategies}")

        all_results = {}
        strategies_used = []

        for strategy in strategies:
            # Temporarily override classification
            vector_column = self.strategy_to_column.get(strategy, "embedding")
            similarity_metric = self.strategy_to_metric.get(
                strategy,
                SimilarityMetric.COSINE
            )

            # Generate query embedding for this strategy
            query_embedding = await intelligent_embedding_service.get_embedding(
                text=query,
                strategy=strategy
            )

            # Query database
            stmt = select(DocumentChunk).where(
                and_(
                    getattr(DocumentChunk, vector_column).isnot(None),
                    *self._build_access_filters(session_id, project_id, user_id)
                )
            )

            chunks = db.execute(stmt).scalars().all()

            # Calculate similarities
            results = []
            for chunk in chunks:
                chunk_embedding = getattr(chunk, vector_column)
                if chunk_embedding is None:
                    continue

                similarity = intelligent_embedding_service.calculate_similarity(
                    embedding_a=query_embedding,
                    embedding_b=chunk_embedding,
                    metric=similarity_metric.value.replace("_", "")
                )

                if similarity >= similarity_threshold:
                    results.append({
                        "chunk_id": str(chunk.id),
                        "document_id": str(chunk.document_id),
                        "content": chunk.content,
                        "similarity": similarity,
                        "strategy": strategy,
                        "chunk_index": chunk.chunk_index
                    })

            # Sort and take top_k
            results.sort(key=lambda x: x["similarity"], reverse=True)
            all_results[strategy] = results[:top_k]
            strategies_used.append(strategy)

            logger.info(
                f"   Strategy {strategy}: {len(results[:top_k])} results "
                f"(searched {len(chunks)} chunks)"
            )

        # Merge results (remove duplicates by chunk_id, keep highest similarity)
        merged = {}
        for strategy, results in all_results.items():
            for result in results:
                chunk_id = result["chunk_id"]
                if chunk_id not in merged or result["similarity"] > merged[chunk_id]["similarity"]:
                    merged[chunk_id] = result

        # Sort merged results by similarity
        final_results = sorted(merged.values(), key=lambda x: x["similarity"], reverse=True)

        logger.info(f"✅ Multi-strategy retrieval: {len(final_results)} unique results")

        return {
            "results": final_results[:top_k],
            "strategy_results": all_results,
            "strategies_used": strategies_used
        }


# Singleton instance
intelligent_retrieval_service = IntelligentRetrievalService()
