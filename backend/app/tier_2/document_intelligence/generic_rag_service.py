"""
Generic RAG Service
Tier 2 Module: Document Intelligence

Configurable RAG with collection management using tier_1 services.
100% tier_1 service reuse - zero new dependencies.
"""

import uuid
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import time

from app.tier_1.infrastructure.config import Settings
from app.tier_1.rag.rag_service import RAGService
from app.tier_1.llm.llm_service import LLMService
from app.tier_1.embeddings.embedding_service import EmbeddingService
from app.tier_1.embeddings.reranker_service import CrossEncoderReranker

from .generic_rag_schemas import (
    RAGQueryRequest,
    RAGQueryResponse,
    RAGConfiguration,
    SourceChunk,
    SavedCollection,
    CreateCollectionRequest,
    UpdateCollectionRequest,
    ListCollectionsRequest,
    ListCollectionsResponse,
    CollectionStats,
    QueryHistoryRequest,
    QueryHistoryResponse,
    ResponseStyle
)

logger = logging.getLogger(__name__)


class GenericRAGService:
    """
    Configurable RAG service with collection management.

    Key Features:
    1. Collection Management - Save/load custom RAG configurations
    2. Flexible Retrieval - Semantic, keyword, hybrid, rerank strategies
    3. Multi-LLM Support - OpenAI, Claude, Ollama integration
    4. Response Styling - Format answers based on use case
    5. Performance Tracking - Query analytics and cache metrics
    """

    def __init__(self, db: Session, settings: Settings, config: Optional[Dict[str, Any]] = None):
        self.db = db
        self.settings = settings
        self.config = config or {}

        # Tier 1 service dependencies
        self.rag_service = RAGService()
        self.llm_service = LLMService()
        self.embedding_service = EmbeddingService(settings)
        self.reranker_service = CrossEncoderReranker(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")

        logger.info("✓ GenericRAGService initialized with tier_1 services")
        if config:
            logger.info(f"✓ Using module config with model: {config.get(\'llm\', {}).get(\'default\', {}).get(\'model\', \'default\')}")

    async def query(self, request: RAGQueryRequest) -> RAGQueryResponse:
        """
        Execute RAG query with custom configuration.

        Args:
            request: Query request with configuration

        Returns:
            RAGQueryResponse with answer and sources
        """
        start_time = time.time()
        query_id = str(uuid.uuid4())

        logger.info(f"🔍 Generic RAG query: {request.query[:100]}...")

        try:
            # Step 1: Get configuration (from collection or request)
            config = await self._get_configuration(request)
            logger.info(f"   Using configuration: {config.collection_name}")

            # Step 2: Apply quick overrides
            if request.top_k:
                config.top_k = request.top_k
            if request.temperature is not None:
                config.temperature = request.temperature
            if request.response_style:
                config.response_style = request.response_style

            # Step 3: Retrieve relevant chunks
            retrieval_start = time.time()
            sources = await self._retrieve_sources(request.query, config)
            retrieval_time_ms = (time.time() - retrieval_start) * 1000
            logger.info(f"   Retrieved {len(sources)} sources in {retrieval_time_ms:.0f}ms")

            # Step 4: Generate answer
            llm_start = time.time()
            answer, confidence = await self._generate_answer(
                query=request.query,
                sources=sources,
                config=config
            )
            llm_time_ms = (time.time() - llm_start) * 1000
            logger.info(f"   Generated answer in {llm_time_ms:.0f}ms")

            # Step 5: Build response
            total_time_ms = (time.time() - start_time) * 1000

            response = RAGQueryResponse(
                query_id=query_id,
                answer=answer,
                response_style=config.response_style,
                sources=sources,
                num_sources_retrieved=len(sources),
                num_sources_used=len(sources),  # TODO: track actual usage
                confidence_score=confidence,
                quality_indicators=self._calculate_quality_indicators(sources, answer),
                retrieval_time_ms=retrieval_time_ms,
                llm_time_ms=llm_time_ms,
                total_time_ms=total_time_ms,
                configuration=config,
                cached_response=False,  # TODO: implement cache checking
                tier_1_services_used=[
                    "RAGService",
                    "LLMService",
                    "EmbeddingService",
                    "RerankerService" if config.rerank_results else None
                ]
            )

            # Step 6: Update collection stats
            if request.collection_id:
                await self._update_collection_stats(request.collection_id, response)

            logger.info(f"✓ Query complete in {total_time_ms:.0f}ms, confidence: {confidence:.2f}")
            return response

        except Exception as e:
            logger.error(f"❌ Generic RAG query failed: {str(e)}", exc_info=True)
            raise

    async def _get_configuration(
        self,
        request: RAGQueryRequest
    ) -> RAGConfiguration:
        """Get configuration from collection or request."""
        if request.configuration:
            return request.configuration

        if request.collection_id:
            # Load from saved collection
            from app.models.database_enhanced import SavedRAGCollections

            collection = self.db.query(SavedRAGCollections).filter(
                SavedRAGCollections.collection_id == uuid.UUID(request.collection_id)
            ).first()

            if collection:
                return RAGConfiguration(**collection.configuration)

        # Default configuration
        return RAGConfiguration(
            collection_name="default",
            document_ids=[]  # Will use all accessible documents
        )

    async def _retrieve_sources(
        self,
        query: str,
        config: RAGConfiguration
    ) -> List[SourceChunk]:
        """Retrieve relevant source chunks using RAGService."""
        try:
            # Build filter for document IDs
            filter_conditions = {}
            if config.document_ids:
                filter_conditions["document_id"] = config.document_ids

            # Use RAG service for retrieval
            from app.services.rag_service import QueryRequest

            rag_request = QueryRequest(
                query=query,
                top_k=config.top_k,
                session_id=config.session_id,
                project_id=config.project_id
            )

            # Get chunks from RAG service
            chunks = await self.rag_service.retrieve_relevant_chunks(
                query=query,
                top_k=config.top_k,
                session_id=config.session_id
            )

            # Convert to SourceChunk format
            sources = []
            for chunk in chunks:
                source = SourceChunk(
                    chunk_id=str(chunk.id),
                    document_id=str(chunk.document_id),
                    document_name=chunk.document_name if hasattr(chunk, 'document_name') else "Unknown",
                    content=chunk.content,
                    page_number=chunk.page_number if hasattr(chunk, 'page_number') else None,
                    similarity_score=chunk.similarity_score if hasattr(chunk, 'similarity_score') else 0.0,
                    chunk_metadata={}
                )
                sources.append(source)

            # Apply reranking if requested
            if config.rerank_results and len(sources) > 1:
                sources = await self._rerank_sources(query, sources)

            # Filter by similarity threshold
            sources = [
                s for s in sources
                if s.similarity_score >= config.similarity_threshold
            ]

            return sources[:config.top_k]

        except Exception as e:
            logger.error(f"Source retrieval failed: {str(e)}")
            return []

    async def _rerank_sources(
        self,
        query: str,
        sources: List[SourceChunk]
    ) -> List[SourceChunk]:
        """Rerank sources using RerankerService."""
        try:
            # Prepare documents for reranking
            docs = [s.content for s in sources]

            # Use reranker service
            reranked_docs = await self.reranker_service.rerank(
                query=query,
                documents=docs
            )

            # Update sources with rerank scores
            for i, source in enumerate(sources):
                if i < len(reranked_docs):
                    source.rerank_score = reranked_docs[i].get("score", 0.0)

            # Sort by rerank score
            sources.sort(key=lambda x: x.rerank_score or 0.0, reverse=True)

            return sources

        except Exception as e:
            logger.warning(f"Reranking failed, using original order: {str(e)}")
            return sources

    async def _generate_answer(
        self,
        query: str,
        sources: List[SourceChunk],
        config: RAGConfiguration
    ) -> tuple[str, float]:
        """Generate answer using LLMService with response styling."""

        # Build context from sources
        context = self._build_context(sources, config)

        # Build prompt with response style instructions
        style_instructions = self._get_style_instructions(config.response_style)

        prompt = f"""You are a helpful AI assistant. Answer the following question based on the provided context.

{style_instructions}

Context:
{context}

Question: {query}

Answer:"""

        try:
            # Use LLM service
            answer = await self.llm_service.generate_response(
                prompt=prompt,
                model=config.llm_model,
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )

            # Calculate confidence based on source quality
            confidence = self._calculate_confidence(sources, answer)

            # Add source citations if requested
            if config.include_sources and sources:
                answer = self._add_source_citations(answer, sources)

            # Add confidence indicator if requested
            if config.include_confidence:
                answer += f"\n\n*Confidence: {confidence:.0%}*"

            return answer, confidence

        except Exception as e:
            logger.error(f"Answer generation failed: {str(e)}")
            return "I apologize, but I encountered an error generating the answer.", 0.0

    def _build_context(
        self,
        sources: List[SourceChunk],
        config: RAGConfiguration
    ) -> str:
        """Build context string from sources."""
        if not sources:
            return "No relevant context found."

        context_parts = []
        for i, source in enumerate(sources, 1):
            context_parts.append(
                f"[Source {i}] {source.document_name} "
                f"(relevance: {source.similarity_score:.0%})\n"
                f"{source.content}\n"
            )

        return "\n".join(context_parts)

    def _get_style_instructions(self, style: ResponseStyle) -> str:
        """Get prompt instructions for response style."""
        instructions = {
            ResponseStyle.CONCISE: "Provide a brief, direct answer. Be concise and to-the-point.",
            ResponseStyle.DETAILED: "Provide a comprehensive, detailed answer with explanations.",
            ResponseStyle.BULLET_POINTS: "Structure your answer as clear bullet points.",
            ResponseStyle.TECHNICAL: "Use technical language and provide implementation details.",
            ResponseStyle.CONVERSATIONAL: "Use natural, conversational language as if explaining to a colleague."
        }
        return instructions.get(style, instructions[ResponseStyle.DETAILED])

    def _calculate_confidence(
        self,
        sources: List[SourceChunk],
        answer: str
    ) -> float:
        """Calculate confidence score for answer."""
        if not sources:
            return 0.0

        # Average source similarity
        avg_similarity = sum(s.similarity_score for s in sources) / len(sources)

        # Bonus if multiple high-quality sources
        high_quality_sources = sum(1 for s in sources if s.similarity_score > 0.8)
        multi_source_bonus = min(high_quality_sources * 0.1, 0.2)

        # Answer length factor (very short answers might be incomplete)
        length_factor = min(len(answer) / 200, 1.0)

        confidence = (avg_similarity * 0.6 + multi_source_bonus + length_factor * 0.2)
        return min(confidence, 1.0)

    def _add_source_citations(
        self,
        answer: str,
        sources: List[SourceChunk]
    ) -> str:
        """Add source citations to answer."""
        if not sources:
            return answer

        citations = "\n\n**Sources:**\n"
        for i, source in enumerate(sources, 1):
            page_info = f", Page {source.page_number}" if source.page_number else ""
            citations += f"{i}. {source.document_name}{page_info} (relevance: {source.similarity_score:.0%})\n"

        return answer + citations

    def _calculate_quality_indicators(
        self,
        sources: List[SourceChunk],
        answer: str
    ) -> Dict[str, Any]:
        """Calculate quality metrics for response."""
        return {
            "num_sources": len(sources),
            "avg_source_relevance": (
                sum(s.similarity_score for s in sources) / len(sources)
                if sources else 0.0
            ),
            "answer_length_chars": len(answer),
            "has_multiple_sources": len(sources) > 1,
            "has_high_relevance_source": any(s.similarity_score > 0.8 for s in sources)
        }

    async def _update_collection_stats(
        self,
        collection_id: str,
        response: RAGQueryResponse
    ):
        """Update collection statistics after query."""
        # TODO: Implement stats tracking in database
        pass

    # Collection management methods

    async def create_collection(
        self,
        request: CreateCollectionRequest
    ) -> SavedCollection:
        """Create a new RAG collection."""
        try:
            from app.models.database_enhanced import SavedRAGCollections

            collection_id = str(uuid.uuid4())

            collection_record = SavedRAGCollections(
                collection_id=uuid.UUID(collection_id),
                collection_name=request.collection_name,
                description=request.description,
                configuration=request.configuration.dict(),
                user_id=uuid.UUID(request.user_id),
                project_id=uuid.UUID(request.project_id) if request.project_id else None,
                is_public=request.is_public,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(collection_record)
            self.db.commit()

            logger.info(f"✓ Created collection: {request.collection_name} (ID: {collection_id})")

            return SavedCollection(
                collection_id=collection_id,
                collection_name=request.collection_name,
                description=request.description,
                configuration=request.configuration,
                user_id=request.user_id,
                project_id=request.project_id,
                is_public=request.is_public,
                created_at=collection_record.created_at,
                updated_at=collection_record.updated_at
            )

        except Exception as e:
            logger.error(f"Failed to create collection: {str(e)}")
            self.db.rollback()
            raise

    async def list_collections(
        self,
        request: ListCollectionsRequest
    ) -> ListCollectionsResponse:
        """List accessible RAG collections."""
        try:
            from app.models.database_enhanced import SavedRAGCollections

            # Build query
            query = self.db.query(SavedRAGCollections)

            # Filter by user or public
            if request.include_public:
                query = query.filter(
                    (SavedRAGCollections.user_id == uuid.UUID(request.user_id)) |
                    (SavedRAGCollections.is_public == True)
                )
            else:
                query = query.filter(SavedRAGCollections.user_id == uuid.UUID(request.user_id))

            # Filter by project if specified
            if request.project_id:
                query = query.filter(SavedRAGCollections.project_id == uuid.UUID(request.project_id))

            # Get total count
            total_count = query.count()

            # Apply pagination
            collections_records = query.order_by(
                SavedRAGCollections.updated_at.desc()
            ).limit(request.limit).offset(request.offset).all()

            # Convert to response models
            collections = [
                SavedCollection(
                    collection_id=str(c.collection_id),
                    collection_name=c.collection_name,
                    description=c.description,
                    configuration=RAGConfiguration(**c.configuration),
                    user_id=str(c.user_id),
                    project_id=str(c.project_id) if c.project_id else None,
                    is_public=c.is_public,
                    created_at=c.created_at,
                    updated_at=c.updated_at
                )
                for c in collections_records
            ]

            return ListCollectionsResponse(
                collections=collections,
                total_count=total_count,
                returned_count=len(collections),
                has_more=(request.offset + request.limit) < total_count
            )

        except Exception as e:
            logger.error(f"Failed to list collections: {str(e)}")
            raise
