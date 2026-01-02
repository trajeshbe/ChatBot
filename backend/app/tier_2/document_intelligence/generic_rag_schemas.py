"""
Generic RAG Schemas
Tier 2 Module: Document Intelligence

Configurable RAG (Retrieval-Augmented Generation) for any document collection.
Allows users to create custom RAG pipelines with flexible configuration.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class RetrievalStrategy(str, Enum):
    """Retrieval strategies"""
    SEMANTIC = "semantic"  # Vector similarity search
    KEYWORD = "keyword"  # BM25 keyword search
    HYBRID = "hybrid"  # Combined semantic + keyword
    RERANK = "rerank"  # Retrieval with reranking


class LLMProvider(str, Enum):
    """LLM providers"""
    OPENAI = "openai"
    CLAUDE = "claude"
    OLLAMA = "ollama"
    CUSTOM = "custom"


class ResponseStyle(str, Enum):
    """Response formatting styles"""
    CONCISE = "concise"  # Brief, to-the-point answers
    DETAILED = "detailed"  # Comprehensive explanations
    BULLET_POINTS = "bullet_points"  # Structured lists
    TECHNICAL = "technical"  # Technical documentation style
    CONVERSATIONAL = "conversational"  # Natural dialogue


class RAGConfiguration(BaseModel):
    """RAG pipeline configuration"""
    # Collection settings
    collection_name: str = Field(..., description="Name for this RAG collection")
    collection_description: Optional[str] = Field(None, description="Description of collection purpose")

    # Document sources
    document_ids: List[str] = Field(..., description="Documents to include in RAG context")
    session_id: Optional[str] = Field(None, description="Limit to session documents only")
    project_id: Optional[str] = Field(None, description="Limit to project documents only")

    # Retrieval configuration
    retrieval_strategy: RetrievalStrategy = Field(
        default=RetrievalStrategy.HYBRID,
        description="How to retrieve relevant chunks"
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Number of chunks to retrieve"
    )
    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score for chunks"
    )

    # LLM configuration
    llm_provider: LLMProvider = Field(
        default=LLMProvider.OPENAI,
        description="LLM provider to use"
    )
    llm_model: str = Field(
        default="gpt-4o",
        description="Specific model name"
    )
    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="LLM temperature (0=deterministic, 2=creative)"
    )
    max_tokens: int = Field(
        default=2000,
        ge=100,
        le=16000,
        description="Maximum response length"
    )

    # Response configuration
    response_style: ResponseStyle = Field(
        default=ResponseStyle.DETAILED,
        description="How to format responses"
    )
    include_sources: bool = Field(
        default=True,
        description="Include source citations in response"
    )
    include_confidence: bool = Field(
        default=True,
        description="Include confidence scores"
    )

    # Advanced options
    use_semantic_cache: bool = Field(
        default=True,
        description="Enable Redis semantic cache for speed"
    )
    rerank_results: bool = Field(
        default=True,
        description="Apply reranking for better relevance"
    )
    chunk_overlap: int = Field(
        default=200,
        ge=0,
        le=500,
        description="Character overlap between chunks"
    )


class RAGQueryRequest(BaseModel):
    """Query request for generic RAG"""
    # Query
    query: str = Field(..., min_length=1, max_length=2000, description="User question")

    # Configuration (can override collection defaults)
    configuration: Optional[RAGConfiguration] = Field(
        None,
        description="Override default configuration for this query"
    )

    # Quick overrides (for common adjustments)
    top_k: Optional[int] = Field(None, ge=1, le=50, description="Override top_k")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Override temperature")
    response_style: Optional[ResponseStyle] = Field(None, description="Override response style")

    # Context
    collection_id: Optional[str] = Field(
        None,
        description="Use saved collection configuration"
    )
    session_id: Optional[str] = Field(None, description="Session for context")
    project_id: Optional[str] = Field(None, description="Project for isolation")
    user_id: Optional[str] = Field(None, description="User ID")


class SourceChunk(BaseModel):
    """Retrieved source chunk with metadata"""
    chunk_id: str = Field(..., description="Unique chunk ID")
    document_id: str = Field(..., description="Source document ID")
    document_name: str = Field(..., description="Source document filename")

    # Content
    content: str = Field(..., description="Chunk text content")
    page_number: Optional[int] = Field(None, description="Page number in document")

    # Relevance
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity")
    rerank_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Reranking score")
    relevance_explanation: Optional[str] = Field(
        None,
        description="Why this chunk is relevant"
    )

    # Metadata
    chunk_metadata: Dict[str, Any] = Field(default_factory=dict)


class RAGQueryResponse(BaseModel):
    """Response from generic RAG query"""
    query_id: str = Field(..., description="Unique query ID")

    # Response
    answer: str = Field(..., description="Generated answer")
    response_style: ResponseStyle = Field(..., description="Style used for formatting")

    # Sources
    sources: List[SourceChunk] = Field(default_factory=list, description="Retrieved chunks")
    num_sources_retrieved: int = Field(default=0)
    num_sources_used: int = Field(default=0)

    # Confidence & quality
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence in answer"
    )
    quality_indicators: Dict[str, Any] = Field(
        default_factory=dict,
        description="Quality metrics (completeness, relevance, etc.)"
    )

    # Performance
    retrieval_time_ms: float = Field(default=0.0)
    llm_time_ms: float = Field(default=0.0)
    total_time_ms: float = Field(default=0.0)

    # Configuration used
    configuration: RAGConfiguration = Field(..., description="Actual configuration used")

    # Cache info
    cached_response: bool = Field(default=False, description="Was response cached?")
    cache_key: Optional[str] = Field(None, description="Cache key if cached")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tier_1_services_used: List[str] = Field(default_factory=list)


class CollectionStats(BaseModel):
    """Statistics for a RAG collection"""
    collection_id: str
    collection_name: str

    # Documents
    num_documents: int = Field(default=0)
    total_chunks: int = Field(default=0)
    avg_chunk_size: float = Field(default=0.0)

    # Usage
    num_queries: int = Field(default=0)
    avg_query_time_ms: float = Field(default=0.0)
    cache_hit_rate: float = Field(default=0.0, ge=0.0, le=1.0)

    # Quality
    avg_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_sources_per_query: float = Field(default=0.0)

    # Timestamps
    created_at: datetime
    last_query_at: Optional[datetime] = None
    last_updated_at: Optional[datetime] = None


class SavedCollection(BaseModel):
    """Saved RAG collection configuration"""
    collection_id: str = Field(..., description="Unique collection ID")
    collection_name: str = Field(..., description="Collection name")
    description: Optional[str] = Field(None, description="Collection purpose")

    # Configuration
    configuration: RAGConfiguration = Field(..., description="Default configuration")

    # Ownership
    user_id: str = Field(..., description="Collection owner")
    project_id: Optional[str] = Field(None, description="Associated project")
    is_public: bool = Field(default=False, description="Accessible to other users?")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None

    # Stats
    stats: Optional[CollectionStats] = None


class CreateCollectionRequest(BaseModel):
    """Request to create a new RAG collection"""
    collection_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    configuration: RAGConfiguration
    is_public: bool = Field(default=False)

    # Context
    user_id: str = Field(...)
    project_id: Optional[str] = None


class UpdateCollectionRequest(BaseModel):
    """Request to update existing collection"""
    collection_id: str = Field(...)
    collection_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    configuration: Optional[RAGConfiguration] = None
    is_public: Optional[bool] = None


class ListCollectionsRequest(BaseModel):
    """Request to list collections"""
    user_id: str = Field(..., description="Filter by user")
    project_id: Optional[str] = Field(None, description="Filter by project")
    include_public: bool = Field(default=True, description="Include public collections")

    # Pagination
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class ListCollectionsResponse(BaseModel):
    """Response with collection list"""
    collections: List[SavedCollection] = Field(default_factory=list)
    total_count: int = Field(default=0)
    returned_count: int = Field(default=0)
    has_more: bool = Field(default=False)


class QueryHistoryRequest(BaseModel):
    """Request to get query history for collection"""
    collection_id: str = Field(...)

    # Filters
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

    # Pagination
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class QueryHistoryResponse(BaseModel):
    """Response with query history"""
    queries: List[RAGQueryResponse] = Field(default_factory=list)
    total_count: int = Field(default=0)
    returned_count: int = Field(default=0)
    has_more: bool = Field(default=False)


class ExportCollectionRequest(BaseModel):
    """Request to export collection data"""
    collection_id: str = Field(...)
    export_format: str = Field(default="json", description="json, csv, or markdown")
    include_queries: bool = Field(default=True, description="Include query history")
    include_documents: bool = Field(default=False, description="Include full document text")
