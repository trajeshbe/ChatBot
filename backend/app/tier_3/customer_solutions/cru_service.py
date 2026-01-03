"""CRU POC - Enhanced Multi-Pipeline RAG for Mining Intelligence"""
import logging
import json
from time import time
from sqlalchemy.orm import Session
from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService, get_llm_service
from app.tier_1.rag.intelligent_retrieval_service import IntelligentRetrievalService
from app.tier_1.embeddings.reranker_service import CrossEncoderReranker, get_reranker
from app.tier_1.rag.confidence_scorer import ConfidenceScorer, get_confidence_scorer
from .cru_schemas import *

logger = logging.getLogger(__name__)

# Optional Elasticsearch support - gracefully degrade if not available
try:
    from app.tier_1.rag.elasticsearch_service import ElasticsearchService, get_elasticsearch_service
    from app.tier_1.rag.rank_fusion_service import RankFusionService, get_rank_fusion_service
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False
    logger.warning("⚠️ Elasticsearch not available - CRU will use pgvector-only mode")

class MultiPipelineRouter:
    """Classifies queries and routes to optimal pipeline"""

    def __init__(self):
        self.llm = get_llm_service()

    async def classify_query(self, query: str) -> QueryType:
        prompt = f"""Classify this mining query into ONE type:
1. SEMANTIC - meaning-based (e.g., "What are environmental risks?")
2. KEYWORD - exact terms (e.g., "Find Gold Valley documents")
3. HYBRID - both (e.g., "Capex for Gold Valley 2024")
4. TABLE_DATA - structured data (e.g., "Iron ore grades by site")

Query: "{query}"
Return ONLY: SEMANTIC, KEYWORD, HYBRID, or TABLE_DATA"""

        response = await self.llm.generate_response(prompt, model="gpt-4o-mini", temperature=0.0, max_tokens=20)
        classification = response.strip().upper().replace("_", "")

        try:
            if "SEMANTIC" in classification:
                return QueryType.SEMANTIC
            elif "KEYWORD" in classification:
                return QueryType.KEYWORD
            elif "HYBRID" in classification:
                return QueryType.HYBRID
            elif "TABLE" in classification or "DATA" in classification:
                return QueryType.TABLE_DATA
        except:
            pass

        return QueryType.HYBRID  # Default to hybrid


class CruService:
    """Enhanced CRU POC - Multi-pipeline RAG for mining document intelligence"""

    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.router = MultiPipelineRouter()
        self.pgvector = IntelligentRetrievalService()
        self.reranker = get_reranker()
        self.confidence = get_confidence_scorer()
        self.llm = get_llm_service()

        # Optional Elasticsearch initialization
        if ELASTICSEARCH_AVAILABLE:
            self.elasticsearch = get_elasticsearch_service()
            self.fusion = get_rank_fusion_service()
        else:
            self.elasticsearch = None
            self.fusion = None
            logger.info("🔍 CRU running in pgvector-only mode (Elasticsearch not available)")

    async def process_request(self, request: CruRequest) -> CruResponse:
        """Process multi-pipeline query with auto-routing"""
        try:
            start_time = time()
            logger.info(f"⛏️ CRU query: {request.query[:100]}")

            # Step 1: Classify and route
            query_type = await self.router.classify_query(request.query)
            logger.info(f"📊 Query classified as: {query_type.value}")

            # Step 2: Retrieve from appropriate pipeline(s)
            if query_type == QueryType.SEMANTIC or not ELASTICSEARCH_AVAILABLE:
                results = await self._retrieve_pgvector(request.query)
                pipeline_used = "pgvector" if ELASTICSEARCH_AVAILABLE else "pgvector (ES unavailable)"
            elif query_type in [QueryType.KEYWORD, QueryType.TABLE_DATA]:
                if ELASTICSEARCH_AVAILABLE:
                    results = await self._retrieve_elasticsearch(request.query)
                    pipeline_used = "elasticsearch"
                else:
                    # Fallback to pgvector for keyword queries
                    results = await self._retrieve_pgvector(request.query)
                    pipeline_used = "pgvector (ES unavailable)"
            else:  # HYBRID
                if ELASTICSEARCH_AVAILABLE:
                    pgv_results = await self._retrieve_pgvector(request.query)
                    es_results = await self._retrieve_elasticsearch(request.query)
                    results = self.fusion.fuse_rankings(pgv_results, es_results, k=60)[:10]
                    pipeline_used = "hybrid (pgvector + elasticsearch + RRF)"
                else:
                    # Fallback to pgvector-only
                    results = await self._retrieve_pgvector(request.query)
                    pipeline_used = "pgvector (ES unavailable)"

            # Step 3: Rerank
            if results:
                results = await self.reranker.rerank(request.query, results, top_k=5)

            # Step 4: Calculate confidence
            conf_score = self.confidence.calculate_confidence(results) if results else 0.3

            # Step 5: Generate answer
            answer = await self._synthesize_answer(request.query, results) if results else "No documents found in database yet. Upload mining documents to enable queries."

            processing_time = int((time() - start_time) * 1000)

            # Format sources
            sources = [
                SourceDocument(
                    document_id=r.get("metadata", {}).get("document_id", "unknown"),
                    document_name=r.get("metadata", {}).get("file_name", "Unknown"),
                    page=r.get("metadata", {}).get("page_number"),
                    score=r.get("score", 0.0),
                    snippet=r.get("content", "")[:200]
                )
                for r in results[:3]
            ] if results else []

            insights = f"Query classified as {query_type.value}. Used {pipeline_used}. Confidence: {int(conf_score*100)}%. {len(results)} sources analyzed."

            recommendations = [
                f"Review {len(sources)} source documents" if sources else "Upload mining documents to database",
                f"Confidence level: {self.confidence.get_confidence_level(conf_score)}"
            ]

            return CruResponse(
                success=True,
                session_id=request.session_id,
                result={
                    "answer": answer,
                    "confidence": conf_score,
                    "sources": [s.dict() for s in sources],
                    "pipeline_used": pipeline_used,
                    "query_type": query_type.value,
                    "processing_time_ms": processing_time
                },
                insights=insights,
                recommendations=recommendations
            )

        except Exception as e:
            logger.error(f"CRU POC error: {e}", exc_info=True)
            return CruResponse(
                success=False,
                session_id=request.session_id,
                result={"error": str(e)},
                insights=f"Error: {str(e)}",
                recommendations=["Please try again"]
            )

    async def _retrieve_pgvector(self, query: str) -> list:
        """Semantic search with pgvector"""
        try:
            return await self.pgvector.intelligent_search(
                query_text=query,
                company="cru",
                usecase="mining_intelligence",
                top_k=10,
                db=self.db
            )
        except Exception as e:
            logger.warning(f"pgvector retrieval error: {e}")
            return []

    async def _retrieve_elasticsearch(self, query: str) -> list:
        """Keyword search with Elasticsearch"""
        try:
            es_results = await self.elasticsearch.search(query, index_name="cru_mining", size=10)
            return [{"content": r.get("_source", {}).get("content", ""), "score": r.get("_score", 0), "metadata": r.get("_source", {})} for r in es_results]
        except Exception as e:
            logger.warning(f"Elasticsearch retrieval error: {e}")
            return []

    async def _synthesize_answer(self, query: str, results: list) -> str:
        """Generate answer from retrieved documents"""
        try:
            context = "\n\n".join([f"[{i+1}] {r.get('content', '')[:300]}" for i, r in enumerate(results[:3])])
            prompt = f"""Based on these mining documents, answer the query.

Query: {query}

Documents:
{context}

Provide a concise answer with citations [1], [2], [3]."""

            return await self.llm.generate_response(prompt, model="gpt-4o-mini", temperature=0.2, max_tokens=300)
        except:
            return "Unable to generate answer from available documents."

    async def get_status(self) -> StatusResponse:
        """Get POC status"""
        if ELASTICSEARCH_AVAILABLE:
            description = "Multi-pipeline RAG for mining intelligence with automatic query routing"
            modules = [
                "intelligent-retrieval (pgvector)",
                "elasticsearch (BM25)",
                "rank-fusion-service (RRF k=60)",
                "reranker (BAAI/bge-reranker-large)",
                "confidence-scorer",
                "llm-service (GPT-4o-mini)"
            ]
            capabilities = [
                "LLM-based query classification (4 types)",
                "pgvector semantic search",
                "Elasticsearch BM25 keyword search",
                "Hybrid pipeline with RRF fusion",
                "Cross-encoder reranking",
                "Calibrated confidence scoring",
                "Automatic pipeline selection",
                "MinIO path: cru/mining_intelligence/{doc_id}"
            ]
        else:
            description = "Single-pipeline RAG for mining intelligence (pgvector-only mode)"
            modules = [
                "intelligent-retrieval (pgvector)",
                "reranker (BAAI/bge-reranker-large)",
                "confidence-scorer",
                "llm-service (GPT-4o-mini)"
            ]
            capabilities = [
                "LLM-based query classification (4 types)",
                "pgvector semantic search",
                "Cross-encoder reranking",
                "Calibrated confidence scoring",
                "Automatic query routing (pgvector fallback)",
                "MinIO path: cru/mining_intelligence/{doc_id}",
                "⚠️ Elasticsearch unavailable - running in degraded mode"
            ]

        return StatusResponse(
            success=True,
            status="operational",
            description=description,
            tier_2_modules_used=modules,
            capabilities=capabilities
        )
