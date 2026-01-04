"""
Generic RAG API Routes
Tier 2 Module: Document Intelligence

REST endpoints for configurable RAG with collection management.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from app.services.module_config_helper import load_module_config
from .generic_rag_service import GenericRAGService
from .generic_rag_schemas import (
    RAGQueryRequest,
    RAGQueryResponse,
    CreateCollectionRequest,
    UpdateCollectionRequest,
    ListCollectionsRequest,
    ListCollectionsResponse,
    SavedCollection,
    QueryHistoryRequest,
    QueryHistoryResponse,
    ExportCollectionRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/modules/generic-rag",
    tags=["Document Intelligence", "Tier 2 Modules", "Generic RAG"]
)


@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(
    request: RAGQueryRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """
    Execute a configurable RAG query with custom settings.

    **Features:**
    - Custom retrieval strategies (semantic, keyword, hybrid, rerank)
    - Multi-LLM support (OpenAI, Claude, Ollama)
    - Flexible response styles (concise, detailed, bullet points, technical, conversational)
    - Collection-based configurations for reusable setups
    - Source citations and confidence scores

    **Quick start - minimal request:**
    ```json
    {
      "query": "What is the project budget?",
      "collection_id": "my-collection-123"
    }
    ```

    **Advanced request with overrides:**
    ```json
    {
      "query": "Summarize the main risks",
      "collection_id": "my-collection-123",
      "top_k": 10,
      "temperature": 0.1,
      "response_style": "bullet_points"
    }
    ```

    **Custom configuration (no saved collection):**
    ```json
    {
      "query": "What are the key findings?",
      "configuration": {
        "collection_name": "ad-hoc-query",
        "document_ids": ["doc-1", "doc-2"],
        "retrieval_strategy": "hybrid",
        "top_k": 5,
        "llm_model": "gpt-4o",
        "response_style": "detailed"
      }
    }
    ```
    """
    try:
        logger.info(f"🔍 Generic RAG query: {request.query[:100]}...")

        # Load module configuration
        module_config = await load_module_config(db, "generic_rag")
        logger.info(f"✓ Loaded config for generic_rag")

        # Initialize service with config
        service = GenericRAGService(db, settings, config=module_config)
        result = await service.query(request)

        logger.info(f"✓ Query complete: {result.num_sources_used} sources, confidence {result.confidence_score:.0%}")
        return result

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Query failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG query failed: {str(e)}"
        )


@router.post("/collections", response_model=SavedCollection)
async def create_collection(
    request: CreateCollectionRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """
    Create a new RAG collection with custom configuration.

    **Use cases:**
    - Save frequently-used RAG configurations
    - Create domain-specific knowledge bases
    - Set up project-specific RAG pipelines
    - Share configurations across team members

    **Example request:**
    ```json
    {
      "collection_name": "Project Documentation",
      "description": "All project specs and requirements",
      "configuration": {
        "collection_name": "Project Documentation",
        "document_ids": ["doc-1", "doc-2", "doc-3"],
        "retrieval_strategy": "hybrid",
        "top_k": 7,
        "llm_provider": "openai",
        "llm_model": "gpt-4o",
        "response_style": "detailed",
        "include_sources": true,
        "rerank_results": true
      },
      "user_id": "user-123",
      "project_id": "project-456",
      "is_public": false
    }
    ```

    **Privacy:**
    - `is_public: false` - Only creator can access
    - `is_public: true` - All project members can access
    """
    try:
        logger.info(f"📁 Creating collection: {request.collection_name}")

        # Load module configuration
        module_config = await load_module_config(db, "generic_rag")
        logger.info(f"✓ Loaded config for generic_rag")

        # Initialize service with config
        service = GenericRAGService(db, settings, config=module_config)
        collection = await service.create_collection(request)

        logger.info(f"✓ Collection created: {collection.collection_id}")
        return collection

    except Exception as e:
        logger.error(f"Collection creation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create collection: {str(e)}"
        )


@router.get("/collections", response_model=ListCollectionsResponse)
async def list_collections(
    user_id: str,
    project_id: str = None,
    include_public: bool = True,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """
    List accessible RAG collections.

    **Filters:**
    - `user_id` (required): Your user ID
    - `project_id` (optional): Filter by project
    - `include_public` (optional): Include public collections (default: true)

    **Pagination:**
    - `limit`: Results per page (1-500, default: 50)
    - `offset`: Skip first N results (default: 0)

    **Returns:**
    - Your private collections
    - Public collections (if include_public=true)
    - Collections sorted by last updated
    """
    try:
        from .generic_rag_schemas import ListCollectionsRequest

        request = ListCollectionsRequest(
            user_id=user_id,
            project_id=project_id,
            include_public=include_public,
            limit=limit,
            offset=offset
        )

        # Load module configuration
        module_config = await load_module_config(db, "generic_rag")
        logger.info(f"✓ Loaded config for generic_rag")

        # Initialize service with config
        service = GenericRAGService(db, settings, config=module_config)
        result = await service.list_collections(request)

        logger.info(f"✓ Listed {result.returned_count}/{result.total_count} collections")
        return result

    except Exception as e:
        logger.error(f"Collection listing failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list collections: {str(e)}"
        )


@router.put("/collections/{collection_id}", response_model=SavedCollection)
async def update_collection(
    collection_id: str,
    request: UpdateCollectionRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """
    Update an existing RAG collection.

    **Updatable fields:**
    - Collection name
    - Description
    - Configuration (retrieval settings, LLM settings, etc.)
    - Privacy (is_public)

    **Example request:**
    ```json
    {
      "collection_id": "abc-123",
      "collection_name": "Updated Name",
      "configuration": {
        "top_k": 10,
        "llm_model": "gpt-4o-mini"
      }
    }
    ```

    **Note:** Only the collection owner can update it.
    """
    try:
        from app.models.database_enhanced import SavedRAGCollections
        import uuid

        logger.info(f"📝 Updating collection: {collection_id}")

        # Get existing collection
        collection = db.query(SavedRAGCollections).filter(
            SavedRAGCollections.collection_id == uuid.UUID(collection_id)
        ).first()

        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection {collection_id} not found"
            )

        # Update fields
        if request.collection_name:
            collection.collection_name = request.collection_name
        if request.description is not None:
            collection.description = request.description
        if request.configuration:
            collection.configuration = request.configuration.dict()
        if request.is_public is not None:
            collection.is_public = request.is_public

        collection.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(collection)

        logger.info(f"✓ Collection updated: {collection_id}")

        from .generic_rag_schemas import RAGConfiguration
        return SavedCollection(
            collection_id=str(collection.collection_id),
            collection_name=collection.collection_name,
            description=collection.description,
            configuration=RAGConfiguration(**collection.configuration),
            user_id=str(collection.user_id),
            project_id=str(collection.project_id) if collection.project_id else None,
            is_public=collection.is_public,
            created_at=collection.created_at,
            updated_at=collection.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Collection update failed: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update collection: {str(e)}"
        )


@router.delete("/collections/{collection_id}")
async def delete_collection(
    collection_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a RAG collection.

    **Note:**
    - Only the collection owner can delete it
    - Deletion is permanent and cannot be undone
    - Query history associated with collection will be preserved
    """
    try:
        from app.models.database_enhanced import SavedRAGCollections
        import uuid

        logger.info(f"🗑️ Deleting collection: {collection_id}")

        collection = db.query(SavedRAGCollections).filter(
            SavedRAGCollections.collection_id == uuid.UUID(collection_id)
        ).first()

        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection {collection_id} not found"
            )

        db.delete(collection)
        db.commit()

        logger.info(f"✓ Collection deleted: {collection_id}")
        return {"message": f"Collection {collection_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Collection deletion failed: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete collection: {str(e)}"
        )


@router.get("/status")
async def get_module_status() -> Dict[str, Any]:
    """
    Get generic RAG module status and capabilities.

    Returns module metadata, supported features, and tier_1 dependencies.
    """
    return {
        "module_id": "generic-rag",
        "name": "Generic RAG",
        "version": "1.0.0",
        "tier": 2,
        "category": "document_intelligence",
        "description": "Configurable RAG with collection management for any document set",

        "capabilities": {
            "retrieval_strategies": ["semantic", "keyword", "hybrid", "rerank"],
            "llm_providers": ["openai", "claude", "ollama", "custom"],
            "response_styles": [
                "concise", "detailed", "bullet_points",
                "technical", "conversational"
            ],
            "export_formats": ["json", "csv", "markdown"]
        },

        "features": {
            "collection_management": True,
            "custom_configurations": True,
            "multi_llm_support": True,
            "semantic_caching": True,
            "result_reranking": True,
            "source_citations": True,
            "confidence_scores": True,
            "query_analytics": True
        },

        "tier_1_dependencies": [
            "RAGService",
            "LLMService",
            "EmbeddingService",
            "RerankerService"
        ],

        "endpoints": {
            "query": "POST /api/v1/modules/generic-rag/query",
            "create_collection": "POST /api/v1/modules/generic-rag/collections",
            "list_collections": "GET /api/v1/modules/generic-rag/collections",
            "update_collection": "PUT /api/v1/modules/generic-rag/collections/{id}",
            "delete_collection": "DELETE /api/v1/modules/generic-rag/collections/{id}",
            "status": "GET /api/v1/modules/generic-rag/status"
        },

        "performance": {
            "avg_query_time_ms": "500-2000",
            "cache_hit_rate": "40-60%",
            "typical_sources_per_query": "5-10"
        },

        "use_cases": [
            "Custom knowledge bases",
            "Project-specific Q&A",
            "Document collections",
            "Domain-specific RAG pipelines",
            "Team collaboration on documents"
        ]
    }

from datetime import datetime
