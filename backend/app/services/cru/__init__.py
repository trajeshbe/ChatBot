"""
CRU (Mining Intelligence) POC - Multi-Pipeline RAG

Services:
- MultiPipelineRouter: Query classification and routing
- CRUQueryService: Orchestrator for multi-pipeline retrieval

Reuses:
- tier_1.rag.elasticsearch_service: BM25 keyword search
- tier_1.rag.rank_fusion_service: RRF score fusion
- tier_1.rag.confidence_scorer: Calibrated confidence scoring
- tier_1.rag.intelligent_retrieval_service: pgvector semantic search
- tier_1.embeddings.reranker_service: Cross-encoder reranking
- tier_1.llm.llm_service: Multi-LLM support

MinIO Path: cru/mining_intelligence/{document_id}

Author: Claude Code
Date: 2026-01-02
"""

from app.services.cru.multi_pipeline_router import (
    MultiPipelineRouter,
    PipelineType,
    QueryType,
    get_multi_pipeline_router
)

from app.services.cru.cru_query_service import (
    CRUQueryService,
    get_cru_query_service
)

__all__ = [
    "MultiPipelineRouter",
    "PipelineType",
    "QueryType",
    "get_multi_pipeline_router",
    "CRUQueryService",
    "get_cru_query_service"
]
