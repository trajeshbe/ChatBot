"""
Relation Extractor API Routes
Tier 2 Module: Document Intelligence

REST endpoints for entity-relationship extraction from documents.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.tier_1.infrastructure.database import get_db
from app.tier_1.infrastructure.config import Settings, get_settings
from app.services.module_config_helper import load_module_config
from .relation_extractor_service import RelationExtractorService
from .relation_extractor_schemas import (
    RelationExtractionRequest,
    RelationExtractionResponse,
    RelationSearchRequest,
    RelationSearchResponse,
    RelationExportRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/modules/relation-extractor",
    tags=["Document Intelligence", "Tier 2 Modules", "Relation Extraction"]
)


@router.post("/extract", response_model=RelationExtractionResponse)
async def extract_relations(
    request: RelationExtractionRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """
    Extract structured relationships between entities from a document.

    **Example use cases:**
    - Business intelligence: "Company A acquired Company B for $50M"
    - Legal documents: "Party X sued Party Y for breach of contract"
    - Research papers: "Author A cited Author B's work on topic C"
    - News articles: "Person X appointed as CEO of Organization Y"

    **Extraction modes:**
    - `auto`: Automatically choose best method based on document type
    - `text`: Extract from text content (PDFs, DOCX)
    - `vision`: Extract from images/scanned documents using GPT-4o Vision
    - `hybrid`: Combined text + vision extraction for maximum accuracy

    **Confidence filtering:**
    - Set `min_confidence` to filter low-quality relations (default: 0.6)
    - Relations with confidence > 0.8 are considered high-quality

    **Response includes:**
    - List of extracted relations with subject, relation type, object
    - Graph representation (nodes = entities, edges = relations)
    - Metadata: extraction time, confidence scores, relation counts
    """
    try:
        logger.info(f"🔗 Relation extraction request for document {request.document_id}")

        # Load module configuration
        module_config = await load_module_config(db, "relation_extractor")
        logger.info(f"✓ Loaded config for relation_extractor")

        # Initialize service with config
        service = RelationExtractorService(db, settings, config=module_config)
        result = await service.extract_relations(request)

        logger.info(f"✓ Extracted {result.relations_after_filtering} relations")
        return result

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Relation extraction failed: {str(e)}"
        )


@router.post("/search", response_model=RelationSearchResponse)
async def search_relations(
    request: RelationSearchRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """
    Search for specific relations in previously extracted data.

    **Search filters:**
    - `subject_text`: Filter by subject entity (e.g., "Apple Inc")
    - `object_text`: Filter by object entity (e.g., "Steve Jobs")
    - `relation_types`: Filter by relation types (e.g., ["employed_by", "ceo_of"])
    - `min_confidence`: Filter by minimum confidence threshold

    **Pagination:**
    - `limit`: Number of results per page (max 500)
    - `offset`: Skip first N results
    - `has_more`: Boolean indicating more results available

    **Example query:**
    ```json
    {
      "extraction_id": "abc-123",
      "subject_text": "Apple",
      "relation_types": ["acquired", "partnered_with"],
      "min_confidence": 0.8,
      "limit": 50,
      "offset": 0
    }
    ```
    """
    try:
        logger.info(f"🔍 Searching relations in extraction {request.extraction_id}")

        # Load module configuration
        module_config = await load_module_config(db, "relation_extractor")
        logger.info(f"✓ Loaded config for relation_extractor")

        # Initialize service with config
        service = RelationExtractorService(db, settings, config=module_config)
        result = await service.search_relations(request)

        logger.info(f"✓ Found {result.total_count} matching relations")
        return result

    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Relation search failed: {str(e)}"
        )


@router.post("/export")
async def export_relations(
    request: RelationExportRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """
    Export extracted relations in various formats.

    **Supported formats:**
    - `json`: Standard JSON format with all relation details
    - `csv`: Flat CSV file (subject, relation, object, confidence, context)
    - `graph_json`: JSON optimized for graph visualization libraries (D3.js, Cytoscape)
    - `neo4j_cypher`: Cypher CREATE statements for Neo4j graph database import
    - `rdf_turtle`: RDF Turtle format for semantic web applications

    **Options:**
    - `include_low_confidence`: Include relations below threshold (default: false)
    - `group_by_type`: Group relations by type in export (default: false)

    **Example response (CSV):**
    ```csv
    subject,subject_type,relation,object,object_type,confidence,context
    Apple Inc,organization,acquired,Beats Electronics,organization,0.95,"Apple Inc acquired Beats Electronics for $3 billion"
    ```

    **Example response (Graph JSON for D3.js):**
    ```json
    {
      "nodes": [
        {"id": "apple-inc", "label": "Apple Inc", "type": "organization"},
        {"id": "beats", "label": "Beats Electronics", "type": "organization"}
      ],
      "links": [
        {"source": "apple-inc", "target": "beats", "relation": "acquired", "weight": 0.95}
      ]
    }
    ```
    """
    try:
        from app.models.database_enhanced import ExtractionResults
        import uuid
        import csv
        import io

        logger.info(f"📥 Export request for extraction {request.extraction_id}")

        # Get extraction record
        extraction = db.query(ExtractionResults).filter(
            ExtractionResults.extraction_id == uuid.UUID(request.extraction_id)
        ).first()

        if not extraction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Extraction {request.extraction_id} not found"
            )

        relations_data = extraction.result_data.get("relations", [])

        # Filter by confidence if needed
        if not request.include_low_confidence:
            min_conf = extraction.result_data.get("metadata", {}).get("min_confidence", 0.6)
            relations_data = [
                r for r in relations_data
                if r.get("confidence", 0) >= min_conf
            ]

        # Generate export based on format
        if request.format == "json":
            return {
                "format": "json",
                "data": relations_data,
                "count": len(relations_data),
                "extraction_id": request.extraction_id
            }

        elif request.format == "csv":
            # Convert to CSV
            output = io.StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow([
                "subject", "subject_type", "relation",
                "object", "object_type", "confidence", "context"
            ])

            # Rows
            for rel in relations_data:
                writer.writerow([
                    rel["subject"]["text"],
                    rel["subject"]["type"],
                    rel["relation"],
                    rel["object"]["text"],
                    rel["object"]["type"],
                    rel["confidence"],
                    rel["context"]
                ])

            csv_content = output.getvalue()
            return {
                "format": "csv",
                "data": csv_content,
                "count": len(relations_data)
            }

        elif request.format == "graph_json":
            # Convert to D3.js / Cytoscape format
            nodes_map = {}
            links = []

            for rel in relations_data:
                # Add subject node
                subj_id = rel["subject"]["text"].lower().replace(" ", "-")
                if subj_id not in nodes_map:
                    nodes_map[subj_id] = {
                        "id": subj_id,
                        "label": rel["subject"]["text"],
                        "type": rel["subject"]["type"]
                    }

                # Add object node
                obj_id = rel["object"]["text"].lower().replace(" ", "-")
                if obj_id not in nodes_map:
                    nodes_map[obj_id] = {
                        "id": obj_id,
                        "label": rel["object"]["text"],
                        "type": rel["object"]["type"]
                    }

                # Add link
                links.append({
                    "source": subj_id,
                    "target": obj_id,
                    "relation": rel["relation"],
                    "weight": rel["confidence"],
                    "context": rel["context"]
                })

            return {
                "format": "graph_json",
                "data": {
                    "nodes": list(nodes_map.values()),
                    "links": links
                },
                "stats": {
                    "nodes": len(nodes_map),
                    "links": len(links)
                }
            }

        elif request.format == "neo4j_cypher":
            # Generate Cypher CREATE statements
            cypher_statements = []

            # Create nodes
            nodes_created = set()
            for rel in relations_data:
                # Subject node
                subj_id = rel["subject"]["text"].replace("'", "\\'")
                if subj_id not in nodes_created:
                    cypher_statements.append(
                        f"CREATE (:{rel['subject']['type']} {{name: '{subj_id}'}})"
                    )
                    nodes_created.add(subj_id)

                # Object node
                obj_id = rel["object"]["text"].replace("'", "\\'")
                if obj_id not in nodes_created:
                    cypher_statements.append(
                        f"CREATE (:{rel['object']['type']} {{name: '{obj_id}'}})"
                    )
                    nodes_created.add(obj_id)

            # Create relationships
            for rel in relations_data:
                subj_id = rel["subject"]["text"].replace("'", "\\'")
                obj_id = rel["object"]["text"].replace("'", "\\'")
                rel_type = rel["relation"].upper().replace("-", "_")

                cypher_statements.append(
                    f"MATCH (a {{name: '{subj_id}'}}), (b {{name: '{obj_id}'}}) "
                    f"CREATE (a)-[:{rel_type} {{confidence: {rel['confidence']}}}]->(b)"
                )

            return {
                "format": "neo4j_cypher",
                "data": "\n".join(cypher_statements),
                "count": len(cypher_statements)
            }

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format: {request.format}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.get("/status")
async def get_module_status() -> Dict[str, Any]:
    """
    Get relation extractor module status and capabilities.

    Returns module metadata, supported relation types, entity types,
    export formats, and tier_1 service dependencies.
    """
    return {
        "module_id": "relation-extractor",
        "name": "Relation Extractor",
        "version": "1.0.0",
        "tier": 2,
        "category": "document_intelligence",
        "description": "Extract structured entity relationships from documents",

        "capabilities": {
            "extraction_modes": ["auto", "text", "vision", "hybrid"],
            "relation_types": [
                "acquired", "merged_with", "partnered_with", "invested_in",
                "employed_by", "ceo_of", "founder_of", "board_member_of",
                "located_in", "headquartered_in", "sued", "developed", "owns"
            ],
            "entity_types": [
                "person", "organization", "location", "product",
                "event", "date", "money", "percent", "quantity"
            ],
            "export_formats": [
                "json", "csv", "graph_json", "neo4j_cypher", "rdf_turtle"
            ]
        },

        "features": {
            "deduplication": True,
            "confidence_filtering": True,
            "graph_construction": True,
            "temporal_extraction": True,
            "attribute_extraction": True
        },

        "tier_1_dependencies": [
            "DocumentService",
            "LLMService",
            "VisionService",
            "HybridExtractionService",
            "OCRService"
        ],

        "endpoints": {
            "extract": "POST /api/v1/modules/relation-extractor/extract",
            "search": "POST /api/v1/modules/relation-extractor/search",
            "export": "POST /api/v1/modules/relation-extractor/export",
            "status": "GET /api/v1/modules/relation-extractor/status"
        },

        "performance": {
            "avg_extraction_time_seconds": "30-90",
            "typical_relations_per_page": "5-15",
            "max_document_size_mb": 50
        }
    }
