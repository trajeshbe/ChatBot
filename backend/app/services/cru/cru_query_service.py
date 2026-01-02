"""
CRU Query Service - Multi-Pipeline RAG Orchestrator

Orchestrates full query flow:
1. Classify query → route to pipeline(s)
2. Retrieve from pgvector and/or Elasticsearch
3. Fuse rankings with RRF (if hybrid)
4. Rerank with cross-encoder
5. Calculate confidence score
6. LLM synthesis with citations

Reuses:
- tier_1.rag.intelligent_retrieval_service: pgvector semantic search
- tier_1.rag.elasticsearch_service: BM25 keyword search
- tier_1.rag.rank_fusion_service: RRF score fusion
- tier_1.rag.confidence_scorer: Calibrated confidence
- tier_1.embeddings.reranker_service: Cross-encoder reranking
- tier_1.llm.llm_service: Answer synthesis
- services.cru.multi_pipeline_router: Query classification

Author: Claude Code
Date: 2026-01-02
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging
from sqlalchemy.orm import Session

from app.tier_1.rag.intelligent_retrieval_service import IntelligentRetrievalService
from app.tier_1.rag.elasticsearch_service import get_elasticsearch_service
from app.tier_1.rag.rank_fusion_service import get_rank_fusion_service
from app.tier_1.rag.confidence_scorer import get_confidence_scorer
from app.tier_1.embeddings.reranker_service import get_reranker_service
from app.tier_1.llm.llm_service import get_llm_service
from app.services.cru.multi_pipeline_router import (
    get_multi_pipeline_router,
    PipelineType,
    QueryType
)

logger = logging.getLogger(__name__)


class CRUQueryResponse(BaseModel):
    """Response from CRU multi-pipeline query."""

    answer: str = Field(description="Synthesized answer from LLM")
    confidence: float = Field(description="Calibrated confidence score (0.0-1.0)")
    confidence_level: str = Field(description="Human-readable confidence level")
    confidence_description: str = Field(description="Explanation of confidence level")
    sources: List[Dict[str, Any]] = Field(description="Source documents with scores")
    pipeline_used: str = Field(description="Pipeline strategy used")
    query_type: str = Field(description="Classified query type")
    processing_time_ms: Optional[int] = Field(default=None, description="Total processing time")

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "The estimated capex for Gold Valley project is $125M (Feasibility Report 2024, Section 5.3)",
                "confidence": 0.89,
                "confidence_level": "high",
                "confidence_description": "Confident - answer is likely correct",
                "sources": [
                    {
                        "document_id": "uuid-123",
                        "document_name": "Feasibility Report 2024.pdf",
                        "page": 47,
                        "score": 0.92,
                        "snippet": "Total capital expenditure estimated at $125M..."
                    }
                ],
                "pipeline_used": "hybrid",
                "query_type": "hybrid",
                "processing_time_ms": 3200
            }
        }


class CRUQueryService:
    """
    Main orchestrator for CRU multi-pipeline RAG.

    Combines pgvector (semantic) + Elasticsearch (keyword) + RRF fusion
    with reranking and confidence scoring.

    Example:
        service = CRUQueryService(db)
        result = await service.query(
            query="What is the capex for Gold Valley project?",
            filters={"project_name": "Gold Valley"},
            top_k=5
        )
    """

    def __init__(
        self,
        db: Session,
        retrieval_service=None,
        elasticsearch_service=None,
        router_service=None,
        fusion_service=None,
        reranker_service=None,
        confidence_scorer=None,
        llm_service=None
    ):
        """
        Initialize CRU query service.

        Args:
            db: Database session
            retrieval_service: Optional IntelligentRetrievalService (uses default if None)
            elasticsearch_service: Optional ElasticsearchService (uses singleton if None)
            router_service: Optional MultiPipelineRouter (uses singleton if None)
            fusion_service: Optional RankFusionService (uses singleton if None)
            reranker_service: Optional RerankerService (uses singleton if None)
            confidence_scorer: Optional ConfidenceScorer (uses singleton if None)
            llm_service: Optional LLMService (uses singleton if None)
        """
        self.db = db
        self.retrieval = retrieval_service or IntelligentRetrievalService()
        self.elasticsearch = elasticsearch_service or get_elasticsearch_service()
        self.router = router_service or get_multi_pipeline_router()
        self.fusion = fusion_service or get_rank_fusion_service()
        self.reranker = reranker_service or get_reranker_service()
        self.confidence_scorer = confidence_scorer or get_confidence_scorer()
        self.llm = llm_service or get_llm_service()

        logger.info("🎯 CRUQueryService initialized with multi-pipeline support")

    async def query(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        session_id: Optional[str] = None,
        company: str = "cru",
        usecase: str = "mining_intelligence"
    ) -> CRUQueryResponse:
        """
        Execute multi-pipeline query with full RAG flow.

        Args:
            query: User query string
            filters: Optional Elasticsearch filters (project_name, document_type, etc.)
            top_k: Number of final results to return
            session_id: Optional session ID for filtering
            company: Company name for MinIO path (default: cru)
            usecase: Use case name for MinIO path (default: mining_intelligence)

        Returns:
            CRUQueryResponse with answer, confidence, sources, etc.

        Example:
            result = await service.query(
                query="What is the capex for Gold Valley?",
                filters={"project_name": "Gold Valley", "document_type": "feasibility_report"},
                top_k=5
            )
        """
        import time
        start_time = time.time()

        logger.info(f"🔍 Processing CRU query: {query[:100]}...")

        try:
            # Step 1: Classify query and route to pipeline(s)
            query_type = await self.router.classify_query(query)
            pipelines = await self.router.route_query(query, query_type)

            logger.info(f"📊 Query type: {query_type.value}, Pipelines: {[p.value for p in pipelines]}")

            # Step 2: Retrieve from pipeline(s)
            results = await self._retrieve_from_pipelines(
                query=query,
                pipelines=pipelines,
                filters=filters,
                session_id=session_id,
                company=company,
                usecase=usecase
            )

            if not results:
                logger.warning("⚠️ No results found from retrieval pipelines")
                return self._create_empty_response(query_type, pipelines)

            logger.info(f"📚 Retrieved {len(results)} documents from pipelines")

            # Step 3: Rerank with cross-encoder
            reranked_results = await self._rerank_results(query, results, top_k)

            logger.info(f"🏆 Reranked to top {len(reranked_results)} results")

            # Step 4: Calculate confidence
            confidence_result = self._calculate_confidence(reranked_results)

            # Step 5: LLM synthesis
            answer = await self._synthesize_answer(query, reranked_results)

            # Step 6: Format response
            processing_time_ms = int((time.time() - start_time) * 1000)

            response = CRUQueryResponse(
                answer=answer,
                confidence=confidence_result["confidence"],
                confidence_level=confidence_result["level"],
                confidence_description=confidence_result["description"],
                sources=self._format_sources(reranked_results),
                pipeline_used="+".join([p.value for p in pipelines]),
                query_type=query_type.value,
                processing_time_ms=processing_time_ms
            )

            logger.info(f"✅ Query processed successfully in {processing_time_ms}ms "
                       f"(confidence: {confidence_result['confidence']:.2f})")

            return response

        except Exception as e:
            logger.error(f"❌ CRU query failed: {e}")
            raise

    async def _retrieve_from_pipelines(
        self,
        query: str,
        pipelines: List[PipelineType],
        filters: Optional[Dict[str, Any]],
        session_id: Optional[str],
        company: str,
        usecase: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents from selected pipeline(s).

        Returns:
            List of retrieved documents with scores and metadata
        """
        if PipelineType.HYBRID in pipelines:
            # Hybrid: retrieve from both, then fuse
            logger.info("🔄 Hybrid retrieval: pgvector + Elasticsearch + RRF fusion")

            # Parallel retrieval from both pipelines
            pgvector_results = await self._retrieve_from_pgvector(
                query=query,
                session_id=session_id,
                company=company,
                usecase=usecase,
                top_k=20
            )

            elasticsearch_results = await self._retrieve_from_elasticsearch(
                query=query,
                filters=filters,
                top_k=20
            )

            # Fuse rankings with RRF
            fused_results = self.fusion.fuse_rankings(
                pgvector_results=pgvector_results,
                elasticsearch_results=elasticsearch_results
            )

            logger.info(f"🔗 Fused {len(pgvector_results)} pgvector + "
                       f"{len(elasticsearch_results)} Elasticsearch results")

            return fused_results[:20]  # Top 20 for reranking

        elif PipelineType.PGVECTOR in pipelines:
            # pgvector only
            logger.info("🎯 pgvector retrieval (semantic search)")
            return await self._retrieve_from_pgvector(
                query=query,
                session_id=session_id,
                company=company,
                usecase=usecase,
                top_k=20
            )

        elif PipelineType.ELASTICSEARCH in pipelines:
            # Elasticsearch only
            logger.info("🔎 Elasticsearch retrieval (keyword search)")
            return await self._retrieve_from_elasticsearch(
                query=query,
                filters=filters,
                top_k=20
            )

        else:
            logger.warning("⚠️ No valid pipeline specified, defaulting to pgvector")
            return await self._retrieve_from_pgvector(
                query=query,
                session_id=session_id,
                company=company,
                usecase=usecase,
                top_k=20
            )

    async def _retrieve_from_pgvector(
        self,
        query: str,
        session_id: Optional[str],
        company: str,
        usecase: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Retrieve documents from pgvector using IntelligentRetrievalService."""
        results = await self.retrieval.intelligent_search(
            db=self.db,
            query=query,
            top_k=top_k,
            session_id=session_id,
            company=company,
            usecase=usecase
        )

        # Format results
        return [
            {
                "document_id": r.get("document_id"),
                "content": r.get("content", ""),
                "score": r.get("score", 0.0),
                "metadata": r.get("metadata", {}),
                "source": "pgvector"
            }
            for r in results
        ]

    async def _retrieve_from_elasticsearch(
        self,
        query: str,
        filters: Optional[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Retrieve documents from Elasticsearch using keyword search."""
        results = await self.elasticsearch.search(
            query=query,
            filters=filters or {},
            top_k=top_k,
            index_name="cru_mining_intelligence"
        )

        # Format results
        return [
            {
                "document_id": r.get("document_id"),
                "content": r.get("content", ""),
                "score": r.get("score", 0.0),
                "metadata": r.get("metadata", {}),
                "source": "elasticsearch"
            }
            for r in results
        ]

    async def _rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Rerank results using cross-encoder."""
        if not results:
            return []

        # Extract documents for reranking
        documents = [r.get("content", "") for r in results]

        # Rerank with BAAI/bge-reranker-large
        reranked = await self.reranker.rerank(
            query=query,
            documents=documents,
            top_k=top_k,
            model="accurate"  # Use best reranker model
        )

        # Map reranked scores back to original results
        reranked_results = []
        for rerank_item in reranked:
            idx = rerank_item.get("index", 0)
            if idx < len(results):
                result = results[idx].copy()
                result["reranker_score"] = rerank_item.get("score", 0.0)
                result["original_score"] = result.get("score", 0.0)
                result["score"] = rerank_item.get("score", 0.0)  # Use reranker score
                reranked_results.append(result)

        return reranked_results

    def _calculate_confidence(self, reranked_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate calibrated confidence score."""
        if not reranked_results:
            return {
                "confidence": 0.0,
                "level": "low",
                "description": "No supporting documents found"
            }

        # Extract features for confidence scoring
        top_result = reranked_results[0]
        features = {
            "embedding_score": top_result.get("original_score", 0.5),
            "reranker_score": top_result.get("reranker_score", 0.5),
            "num_supporting_docs": len([r for r in reranked_results if r.get("reranker_score", 0) > 0.5]),
            "answer_length": len(top_result.get("content", "").split()),
            "source_quality": 0.8  # Placeholder (could be based on document metadata)
        }

        # Calculate confidence
        confidence_result = self.confidence_scorer.calculate(features, explain=False)

        return confidence_result

    async def _synthesize_answer(
        self,
        query: str,
        reranked_results: List[Dict[str, Any]]
    ) -> str:
        """Synthesize answer from retrieved contexts using LLM."""
        # Build context from top results
        context = "\n\n".join([
            f"[Document {i+1}: {r.get('metadata', {}).get('filename', 'Unknown')}]\n{r.get('content', '')}"
            for i, r in enumerate(reranked_results[:5])  # Top 5 contexts
        ])

        # Synthesis prompt
        prompt = f"""You are a mining document analyst specializing in extracting insights from technical reports.

Answer this question based ONLY on the provided context. Be specific and cite sources.

Question: {query}

Context:
{context}

Instructions:
1. Provide a concise, specific answer with numbers, names, dates where applicable
2. Cite sources like (Feasibility Report 2024, Section 5.3)
3. If the context doesn't contain the answer, say "Information not available in provided documents."
4. DO NOT make up information not present in the context

Answer:"""

        # Generate answer
        response = await self.llm.generate(
            prompt=prompt,
            model_id="gpt-4o-mini",
            temperature=0.0,  # Deterministic for factual extraction
            max_tokens=300
        )

        answer = response.get("content", "Unable to generate answer").strip()

        return answer

    def _format_sources(self, reranked_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format sources for response."""
        sources = []
        for r in reranked_results:
            metadata = r.get("metadata", {})
            sources.append({
                "document_id": r.get("document_id"),
                "document_name": metadata.get("filename", "Unknown"),
                "page": metadata.get("page_no"),
                "score": round(r.get("reranker_score", 0.0), 3),
                "snippet": r.get("content", "")[:200] + "..."  # First 200 chars
            })

        return sources

    def _create_empty_response(
        self,
        query_type: QueryType,
        pipelines: List[PipelineType]
    ) -> CRUQueryResponse:
        """Create empty response when no results found."""
        return CRUQueryResponse(
            answer="No relevant information found in the document repository.",
            confidence=0.0,
            confidence_level="low",
            confidence_description="No supporting documents found",
            sources=[],
            pipeline_used="+".join([p.value for p in pipelines]),
            query_type=query_type.value,
            processing_time_ms=0
        )


# Factory function
def get_cru_query_service(db: Session) -> CRUQueryService:
    """
    Get CRUQueryService instance.

    Args:
        db: Database session

    Returns:
        CRUQueryService instance
    """
    return CRUQueryService(db)
