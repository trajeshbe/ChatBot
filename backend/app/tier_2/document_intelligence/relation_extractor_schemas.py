"""
Relation Extractor Schemas
Tier 2 Module: Document Intelligence

Extracts structured relationships between entities in documents.
Example: "Company A acquired Company B for $X million" →
         (Company A, ACQUIRED, Company B, {amount: $X million, date: ...})
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class RelationType(str, Enum):
    """Common relationship types"""
    # Business relationships
    ACQUIRED = "acquired"
    MERGED_WITH = "merged_with"
    PARTNERED_WITH = "partnered_with"
    INVESTED_IN = "invested_in"
    SUBSIDIARY_OF = "subsidiary_of"
    COMPETITOR_OF = "competitor_of"
    SUPPLIER_OF = "supplier_of"
    CUSTOMER_OF = "customer_of"

    # Employment relationships
    EMPLOYED_BY = "employed_by"
    CEO_OF = "ceo_of"
    FOUNDER_OF = "founder_of"
    BOARD_MEMBER_OF = "board_member_of"

    # Location relationships
    LOCATED_IN = "located_in"
    HEADQUARTERED_IN = "headquartered_in"
    OPERATES_IN = "operates_in"

    # Legal relationships
    SUED = "sued"
    SETTLED_WITH = "settled_with"
    REGULATED_BY = "regulated_by"

    # Project relationships
    DEVELOPED = "developed"
    OWNS = "owns"
    LICENSED = "licensed"

    # Generic
    RELATED_TO = "related_to"
    MENTIONED_WITH = "mentioned_with"


class EntityType(str, Enum):
    """Entity types in relationships"""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    PRODUCT = "product"
    EVENT = "event"
    DATE = "date"
    MONEY = "money"
    PERCENT = "percent"
    QUANTITY = "quantity"
    OTHER = "other"


class Entity(BaseModel):
    """An entity in a relationship"""
    text: str = Field(..., description="Entity text as it appears in document")
    type: EntityType = Field(..., description="Entity type")
    normalized: Optional[str] = Field(None, description="Normalized/canonical form")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional entity metadata")


class Relation(BaseModel):
    """A structured relationship between entities"""
    subject: Entity = Field(..., description="Subject entity (from)")
    relation: RelationType = Field(..., description="Relationship type")
    object: Entity = Field(..., description="Object entity (to)")

    # Context
    context: str = Field(..., description="Original sentence/paragraph containing relation")
    source_page: Optional[int] = Field(None, description="Page number in source document")

    # Attributes
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Relation attributes (date, amount, etc.)")

    # Quality metrics
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall relation confidence")
    extraction_method: str = Field(..., description="Method used (llm/pattern/hybrid)")

    # Temporal information
    temporal_info: Optional[Dict[str, Any]] = Field(None, description="When did this relation occur")


class RelationExtractionRequest(BaseModel):
    """Request to extract relations from document"""
    document_id: str = Field(..., description="Document ID from upload")

    # Extraction configuration
    relation_types: Optional[List[RelationType]] = Field(
        None,
        description="Specific relation types to extract (None = all)"
    )
    entity_types: Optional[List[EntityType]] = Field(
        None,
        description="Specific entity types to focus on (None = all)"
    )

    # Extraction modes
    extraction_mode: str = Field(
        default="auto",
        description="Extraction strategy: auto, text, vision, hybrid"
    )

    # Quality controls
    min_confidence: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for relations"
    )
    deduplicate: bool = Field(
        default=True,
        description="Remove duplicate/similar relations"
    )

    # Context
    session_id: Optional[str] = Field(None, description="User session ID")
    project_id: Optional[str] = Field(None, description="Project ID for isolation")


class RelationGraph(BaseModel):
    """Graph representation of relations"""
    nodes: List[Entity] = Field(default_factory=list, description="Unique entities")
    edges: List[Relation] = Field(default_factory=list, description="Relations between entities")

    # Statistics
    num_entities: int = Field(default=0)
    num_relations: int = Field(default=0)
    relation_type_counts: Dict[str, int] = Field(default_factory=dict)
    entity_type_counts: Dict[str, int] = Field(default_factory=dict)


class RelationExtractionResponse(BaseModel):
    """Response with extracted relations"""
    extraction_id: str = Field(..., description="Unique extraction ID")
    document_id: str = Field(..., description="Source document ID")

    # Results
    relations: List[Relation] = Field(default_factory=list, description="Extracted relations")
    graph: RelationGraph = Field(..., description="Graph representation")

    # Metadata
    total_relations_found: int = Field(default=0)
    relations_after_filtering: int = Field(default=0)
    extraction_time_seconds: float = Field(default=0.0)

    # Extraction details
    extraction_mode: str = Field(...)
    tier_1_services_used: List[str] = Field(default_factory=list)

    # Quality
    avg_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    high_confidence_count: int = Field(default=0, description="Relations with confidence > 0.8")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExportFormat(str, Enum):
    """Export formats for relations"""
    JSON = "json"
    CSV = "csv"
    GRAPH_JSON = "graph_json"  # JSON suitable for graph visualization (D3.js, Cytoscape, etc.)
    NEO4J_CYPHER = "neo4j_cypher"  # Cypher statements for Neo4j import
    RDF_TURTLE = "rdf_turtle"  # RDF Turtle format for semantic web


class RelationExportRequest(BaseModel):
    """Request to export extracted relations"""
    extraction_id: str = Field(..., description="Extraction ID to export")
    format: ExportFormat = Field(..., description="Export format")

    # Format-specific options
    include_low_confidence: bool = Field(
        default=False,
        description="Include relations below confidence threshold"
    )
    group_by_type: bool = Field(
        default=False,
        description="Group relations by type in export"
    )


class RelationSearchRequest(BaseModel):
    """Search for specific relations in extracted data"""
    extraction_id: str = Field(..., description="Extraction ID to search")

    # Search filters
    subject_text: Optional[str] = Field(None, description="Filter by subject entity text")
    object_text: Optional[str] = Field(None, description="Filter by object entity text")
    relation_types: Optional[List[RelationType]] = Field(None, description="Filter by relation types")
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Pagination
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class RelationSearchResponse(BaseModel):
    """Search results for relations"""
    total_count: int = Field(..., description="Total matching relations")
    returned_count: int = Field(..., description="Relations in this response")
    relations: List[Relation] = Field(default_factory=list)

    # Pagination
    limit: int
    offset: int
    has_more: bool = Field(default=False)
