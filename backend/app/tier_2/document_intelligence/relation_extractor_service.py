"""
Relation Extractor Service
Tier 2 Module: Document Intelligence

Extracts structured relationships between entities using tier_1 services.
100% tier_1 service reuse - zero new dependencies.
"""

import uuid
import json
import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from app.tier_1.document_processing.vision_service import VisionService
from app.tier_1.document_processing.document_service import DocumentService
from app.tier_1.document_processing.hybrid_extraction_service import HybridExtractionService
from app.tier_1.document_processing.ocr_service import OCRService

from .relation_extractor_schemas import (
    RelationExtractionRequest,
    RelationExtractionResponse,
    Relation,
    Entity,
    RelationType,
    EntityType,
    RelationGraph,
    RelationSearchRequest,
    RelationSearchResponse
)

logger = logging.getLogger(__name__)


class RelationExtractorService:
    """
    Extract structured relationships from documents using tier_1 services.

    Extraction Pipeline:
    1. Document Processing → DocumentService (get text/images)
    2. Entity Recognition → LLMService (find entities)
    3. Relation Extraction → LLMService/VisionService (extract relations)
    4. Graph Construction → Build relation graph
    5. Deduplication → Remove similar relations
    6. Validation → Confidence filtering
    """

    def __init__(self, db: Session, settings: Settings, config: Optional[Dict[str, Any]] = None):
        self.db = db
        self.settings = settings
        self.config = config or {}

        # Tier 1 service dependencies
        self.llm_service = LLMService()
        self.vision_service = VisionService()  # Fixed: VisionService only takes ollama_base_url (optional)
        self.document_service = DocumentService()  # Fixed: DocumentService takes no arguments
        self.hybrid_service = HybridExtractionService()  # Fixed: HybridExtractionService takes no arguments
        self.ocr_service = OCRService()  # Fixed: OCRService takes no arguments

        logger.info("✓ RelationExtractorService initialized with tier_1 services")
        if config:
            model = config.get('llm', {}).get('default', {}).get('model', 'default')
            logger.info(f"✓ Using module config with model: {model}")

    def _extract_json_from_llm_response(self, llm_response: str) -> str:
        """
        Extract JSON from LLM response, handling markdown code blocks and malformed responses.

        Args:
            llm_response: Raw LLM response string

        Returns:
            Cleaned JSON string ready for parsing
        """
        # Remove leading/trailing whitespace
        cleaned = llm_response.strip()

        # Handle markdown code blocks
        if cleaned.startswith("```"):
            # Extract content between code fences
            pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
            match = re.search(pattern, cleaned)
            if match:
                cleaned = match.group(1).strip()
            else:
                # Fallback: just remove the backticks
                cleaned = cleaned.strip("`").strip()
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:].strip()

        # Try to find JSON array in the response (between [ and ])
        if not cleaned.startswith("["):
            # Search for JSON array in the text
            pattern = r'\[\s*{[\s\S]*}\s*\]'
            match = re.search(pattern, cleaned)
            if match:
                cleaned = match.group(0)

        return cleaned

    async def extract_relations(
        self,
        request: RelationExtractionRequest
    ) -> RelationExtractionResponse:
        """
        Extract structured relationships from document.

        Args:
            request: Extraction configuration

        Returns:
            RelationExtractionResponse with extracted relations and graph
        """
        start_time = datetime.utcnow()
        extraction_id = str(uuid.uuid4())

        logger.info(f"🔗 Starting relation extraction for document {request.document_id}")
        logger.info(f"   Mode: {request.extraction_mode}, Min confidence: {request.min_confidence}")

        try:
            # Step 1: Get document content
            document_content = await self._get_document_content(
                request.document_id,
                request.extraction_mode
            )

            # Step 2: Extract entities
            entities = await self._extract_entities(
                document_content,
                request.entity_types
            )
            logger.info(f"   Extracted {len(entities)} entities")

            # Step 3: Extract relations
            raw_relations = await self._extract_relations_from_content(
                document_content,
                entities,
                request.relation_types,
                request.extraction_mode
            )
            logger.info(f"   Extracted {len(raw_relations)} raw relations")

            # Step 4: Filter by confidence
            filtered_relations = [
                r for r in raw_relations
                if r.confidence >= request.min_confidence
            ]
            logger.info(f"   {len(filtered_relations)} relations after confidence filtering")

            # Step 5: Deduplicate if requested
            if request.deduplicate:
                filtered_relations = self._deduplicate_relations(filtered_relations)
                logger.info(f"   {len(filtered_relations)} relations after deduplication")

            # Step 6: Build relation graph
            graph = self._build_relation_graph(filtered_relations)

            # Step 7: Calculate metrics
            tier_1_services = self._get_services_used(request.extraction_mode)
            avg_confidence = (
                sum(r.confidence for r in filtered_relations) / len(filtered_relations)
                if filtered_relations else 0.0
            )
            high_confidence_count = sum(1 for r in filtered_relations if r.confidence > 0.8)

            extraction_time = (datetime.utcnow() - start_time).total_seconds()

            response = RelationExtractionResponse(
                extraction_id=extraction_id,
                document_id=request.document_id,
                relations=filtered_relations,
                graph=graph,
                total_relations_found=len(raw_relations),
                relations_after_filtering=len(filtered_relations),
                extraction_time_seconds=extraction_time,
                extraction_mode=request.extraction_mode,
                tier_1_services_used=tier_1_services,
                avg_confidence=avg_confidence,
                high_confidence_count=high_confidence_count
            )

            # Step 8: Store in database (using existing tables)
            await self._store_extraction_results(request, response)

            logger.info(f"✓ Relation extraction complete in {extraction_time:.2f}s")
            logger.info(f"   Relations: {len(filtered_relations)}, Avg confidence: {avg_confidence:.2f}")

            return response

        except Exception as e:
            logger.error(f"❌ Relation extraction failed: {str(e)}", exc_info=True)
            raise

    async def _get_document_content(
        self,
        document_id: str,
        mode: str
    ) -> Dict[str, Any]:
        """Get document content using DocumentService."""
        try:
            # Get document from database
            from app.models.database import Document
            result = await self.db.execute(select(Document).filter(Document.id == document_id))
            doc = result.scalar_one_or_none()

            if not doc:
                raise ValueError(f"Document {document_id} not found")

            content = {
                "document_id": document_id,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "text": "",
                "pages": []
            }

            # Get text content
            if mode in ["auto", "text", "hybrid"]:
                # Get document chunks from database
                from app.models.database import DocumentChunk
                result = await self.db.execute(
                    select(DocumentChunk)
                    .filter(DocumentChunk.document_id == document_id)
                    .order_by(DocumentChunk.chunk_index)
                )
                chunks = result.scalars().all()
                content["text"] = "\n\n".join([chunk.content for chunk in chunks])

            # Get image content for vision/hybrid modes
            if mode in ["auto", "vision", "hybrid"]:
                # Get document file path and convert to images if needed
                if doc.file_type.lower() in ["pdf", "png", "jpg", "jpeg", "tiff"]:
                    content["has_images"] = True
                    content["file_path"] = doc.file_path

            return content

        except Exception as e:
            logger.error(f"Failed to get document content: {str(e)}")
            raise

    async def _extract_entities(
        self,
        document_content: Dict[str, Any],
        entity_types: Optional[List[EntityType]] = None
    ) -> List[Entity]:
        """Extract named entities using LLMService."""

        entity_types_str = (
            ", ".join([et.value for et in entity_types])
            if entity_types
            else "all types (person, organization, location, product, date, money, etc.)"
        )

        # Get prompt from config or use default
        prompt_config = self.config.get('prompts', {})
        entity_extraction_prompt = prompt_config.get('entity_extraction', None)

        if entity_extraction_prompt:
            # Use custom prompt from UI, with template variables
            prompt = entity_extraction_prompt.format(
                entity_types=entity_types_str,
                document_text=document_content.get('text', '')[:8000]
            )
        else:
            # Use default prompt
            prompt = f"""Extract all named entities from the following document.

Entity types to extract: {entity_types_str}

Document:
{document_content.get('text', '')[:8000]}

Return a JSON array of entities with this structure:
[
  {{
    "text": "entity text as it appears",
    "type": "entity_type (person/organization/location/product/date/money/percent/quantity/other)",
    "normalized": "canonical form (optional)",
    "confidence": 0.95
  }}
]

Focus on entities that are likely to be involved in relationships.
Return ONLY the JSON array, no explanation.
"""

        try:
            # Get LLM config from UI or use defaults
            llm_config = self.config.get('llm', {}).get('default', {})
            model_id = llm_config.get('model', 'gpt-4o-mini')
            temperature = llm_config.get('temperature', 0.0)
            max_tokens = llm_config.get('max_tokens', 4000)

            # Use LLM service for entity extraction
            llm_result = await self.llm_service.generate(
                prompt=prompt,
                model_id=model_id,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Extract content from LLM response
            llm_response = llm_result.get("content", "")

            # Debug logging
            logger.info(f"Entity Extraction - LLM Model Used: {model_id}")
            logger.info(f"Entity Extraction - LLM Response Length: {len(llm_response)}")
            logger.info(f"Entity Extraction - LLM Response (first 500 chars): {llm_response[:500]}")
            logger.info(f"Entity Extraction - Full LLM Result Keys: {llm_result.keys()}")

            if not llm_response:
                logger.error(f"Empty LLM response! Full result: {llm_result}")
                raise ValueError("LLM returned empty content")

            # Extract JSON from LLM response using robust method
            cleaned_response = self._extract_json_from_llm_response(llm_response)
            logger.info(f"Entity Extraction - Cleaned Response (first 200 chars): {cleaned_response[:200]}")

            # Save full responses for debugging (temporary)
            try:
                with open("/tmp/entity_llm_response.txt", "w") as f:
                    f.write(f"RAW RESPONSE:\n{llm_response}\n\nCLEANED RESPONSE:\n{cleaned_response}")
            except:
                pass

            # Parse JSON response
            entities_data = json.loads(cleaned_response)
            logger.info(f"Entity Extraction - Successfully parsed JSON with {len(entities_data)} entities")

            # Convert to Entity objects
            entities = []
            for entity_dict in entities_data:
                try:
                    entity = Entity(
                        text=entity_dict["text"],
                        type=EntityType(entity_dict["type"]),
                        normalized=entity_dict.get("normalized"),
                        confidence=entity_dict.get("confidence", 0.8),
                        metadata={}
                    )
                    entities.append(entity)
                except Exception as e:
                    logger.warning(f"Skipping invalid entity: {entity_dict}, error: {e}")
                    continue

            logger.info(f"Entity Extraction - Created {len(entities)} Entity objects from {len(entities_data)} parsed entities")
            return entities

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse entity JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}")
            return []

    async def _extract_relations_from_content(
        self,
        document_content: Dict[str, Any],
        entities: List[Entity],
        relation_types: Optional[List[RelationType]] = None,
        mode: str = "auto"
    ) -> List[Relation]:
        """Extract relations between entities using LLMService."""

        relation_types_str = (
            ", ".join([rt.value for rt in relation_types])
            if relation_types
            else "all types (acquired, merged_with, employed_by, located_in, developed, etc.)"
        )

        # Create entity reference list
        entity_list = "\n".join([
            f"- {e.text} ({e.type.value})"
            for e in entities[:100]  # Limit to first 100 entities
        ])

        # Get prompt from config or use default
        prompt_config = self.config.get('prompts', {})
        relation_extraction_prompt = prompt_config.get('relation_extraction', None)

        if relation_extraction_prompt:
            # Use custom prompt from UI, with template variables
            prompt = relation_extraction_prompt.format(
                entity_list=entity_list,
                relation_types=relation_types_str,
                document_text=document_content.get('text', '')[:8000]
            )
        else:
            # Use default prompt
            prompt = f"""Extract structured relationships between entities from the document.

Known entities:
{entity_list}

Relationship types to extract: {relation_types_str}

Document:
{document_content.get('text', '')[:8000]}

Return a JSON array of relationships with this structure:
[
  {{
    "subject": {{"text": "Entity A", "type": "organization", "confidence": 0.95}},
    "relation": "acquired",
    "object": {{"text": "Entity B", "type": "organization", "confidence": 0.90}},
    "context": "Original sentence from document",
    "source_page": 1,
    "attributes": {{"amount": "$50M", "date": "2024-01-15"}},
    "confidence": 0.92,
    "extraction_method": "llm"
  }}
]

Instructions:
1. Extract only explicit relationships stated in the document
2. Include surrounding context (full sentence)
3. Add attributes like dates, amounts, locations when present
4. Assign confidence based on clarity and evidence
5. Return ONLY the JSON array, no explanation
"""

        try:
            # Get LLM config from UI or use defaults
            llm_config = self.config.get('llm', {}).get('default', {})
            model_id = llm_config.get('model', 'gpt-4o')
            temperature = llm_config.get('temperature', 0.1)
            max_tokens = llm_config.get('max_tokens', 6000)

            # Debug: Log the actual config values being used
            logger.info(f"Relation Extraction - Config loaded: model={model_id}, temp={temperature}, max_tokens={max_tokens}")
            logger.info(f"Relation Extraction - Full llm_config: {llm_config}")

            # Use LLM service for relation extraction
            llm_result = await self.llm_service.generate(
                prompt=prompt,
                model_id=model_id,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Extract content from LLM response
            llm_response = llm_result.get("content", "")

            # Debug logging
            logger.info(f"Relation Extraction - LLM Model Used: {model_id}")
            logger.info(f"Relation Extraction - LLM Response Length: {len(llm_response)}")
            logger.info(f"Relation Extraction - LLM Response (first 500 chars): {llm_response[:500]}")
            logger.info(f"Relation Extraction - Full LLM Result Keys: {llm_result.keys()}")

            if not llm_response:
                logger.error(f"Empty LLM response! Full result: {llm_result}")
                raise ValueError("LLM returned empty content for relation extraction")

            # Extract JSON from LLM response using robust method
            cleaned_response = self._extract_json_from_llm_response(llm_response)
            logger.info(f"Relation Extraction - Cleaned Response (first 200 chars): {cleaned_response[:200]}")

            # Save full responses for debugging (temporary)
            try:
                with open("/tmp/relation_llm_response.txt", "w") as f:
                    f.write(f"RAW RESPONSE:\n{llm_response}\n\nCLEANED RESPONSE:\n{cleaned_response}")
            except:
                pass

            # Parse JSON response
            relations_data = json.loads(cleaned_response)

            # Convert to Relation objects
            relations = []
            for rel_dict in relations_data:
                try:
                    relation = Relation(
                        subject=Entity(**rel_dict["subject"]),
                        relation=RelationType(rel_dict["relation"]),
                        object=Entity(**rel_dict["object"]),
                        context=rel_dict["context"],
                        source_page=rel_dict.get("source_page"),
                        attributes=rel_dict.get("attributes", {}),
                        confidence=rel_dict.get("confidence", 0.7),
                        extraction_method=rel_dict.get("extraction_method", mode),
                        temporal_info=rel_dict.get("temporal_info")
                    )
                    relations.append(relation)
                except Exception as e:
                    logger.warning(f"Skipping invalid relation: {rel_dict}, error: {e}")
                    continue

            return relations

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse relation JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Relation extraction failed: {str(e)}")
            return []

    def _deduplicate_relations(self, relations: List[Relation]) -> List[Relation]:
        """Remove duplicate/similar relations."""
        # Simple deduplication: keep highest confidence for each (subject, relation, object) triple
        unique_relations = {}

        for rel in relations:
            # Create key from normalized entities
            key = (
                rel.subject.normalized or rel.subject.text.lower(),
                rel.relation.value,
                rel.object.normalized or rel.object.text.lower()
            )

            # Keep highest confidence relation for this key
            if key not in unique_relations or rel.confidence > unique_relations[key].confidence:
                unique_relations[key] = rel

        return list(unique_relations.values())

    def _build_relation_graph(self, relations: List[Relation]) -> RelationGraph:
        """Build graph representation from relations."""
        # Extract unique entities
        entities_map = {}

        for rel in relations:
            # Add subject
            subj_key = rel.subject.normalized or rel.subject.text.lower()
            if subj_key not in entities_map:
                entities_map[subj_key] = rel.subject

            # Add object
            obj_key = rel.object.normalized or rel.object.text.lower()
            if obj_key not in entities_map:
                entities_map[obj_key] = rel.object

        unique_entities = list(entities_map.values())

        # Count relation and entity types
        relation_type_counts = {}
        entity_type_counts = {}

        for rel in relations:
            rel_type = rel.relation.value
            relation_type_counts[rel_type] = relation_type_counts.get(rel_type, 0) + 1

        for entity in unique_entities:
            ent_type = entity.type.value
            entity_type_counts[ent_type] = entity_type_counts.get(ent_type, 0) + 1

        return RelationGraph(
            nodes=unique_entities,
            edges=relations,
            num_entities=len(unique_entities),
            num_relations=len(relations),
            relation_type_counts=relation_type_counts,
            entity_type_counts=entity_type_counts
        )

    def _get_services_used(self, mode: str) -> List[str]:
        """Get list of tier_1 services used based on mode."""
        services = ["DocumentService", "LLMService"]

        if mode == "vision":
            services.append("VisionService")
        elif mode == "hybrid":
            services.extend(["VisionService", "HybridExtractionService"])

        return services

    async def _store_extraction_results(
        self,
        request: RelationExtractionRequest,
        response: RelationExtractionResponse
    ):
        """Store extraction results in database (reusing existing tables)."""
        try:
            from app.models.database_enhanced import ExtractionResults

            # Store in extraction_results table (reuse from docu-extract)
            extraction_record = ExtractionResults(
                id=uuid.uuid4(),
                extraction_id=uuid.UUID(response.extraction_id),
                module_id="relation-extractor",
                document_id=uuid.UUID(request.document_id),
                session_id=request.session_id,
                project_id=uuid.UUID(request.project_id) if request.project_id else None,
                result_data={
                    "relations": [r.dict() for r in response.relations],
                    "graph": response.graph.dict(),
                    "metadata": {
                        "total_relations": response.total_relations_found,
                        "filtered_relations": response.relations_after_filtering,
                        "avg_confidence": response.avg_confidence,
                        "extraction_time": response.extraction_time_seconds
                    }
                },
                extraction_mode=request.extraction_mode,
                confidence_score=response.avg_confidence,
                created_at=datetime.utcnow()
            )

            self.db.add(extraction_record)
            self.db.commit()

            logger.info(f"✓ Stored extraction results in database")

        except Exception as e:
            logger.error(f"Failed to store extraction results: {str(e)}")
            # Non-critical error, don't raise

    async def search_relations(
        self,
        request: RelationSearchRequest
    ) -> RelationSearchResponse:
        """Search for specific relations in extracted data."""
        try:
            from app.models.database_enhanced import ExtractionResults

            # Get extraction record
            result = await self.db.execute(
                select(ExtractionResults).filter(
                    ExtractionResults.extraction_id == uuid.UUID(request.extraction_id)
                )
            )
            extraction = result.scalar_one_or_none()

            if not extraction:
                return RelationSearchResponse(
                    total_count=0,
                    returned_count=0,
                    relations=[],
                    limit=request.limit,
                    offset=request.offset,
                    has_more=False
                )

            # Parse stored relations
            relations_data = extraction.result_data.get("relations", [])
            all_relations = [
                Relation(**rel_dict) for rel_dict in relations_data
            ]

            # Apply filters
            filtered_relations = all_relations

            if request.subject_text:
                filtered_relations = [
                    r for r in filtered_relations
                    if request.subject_text.lower() in r.subject.text.lower()
                ]

            if request.object_text:
                filtered_relations = [
                    r for r in filtered_relations
                    if request.object_text.lower() in r.object.text.lower()
                ]

            if request.relation_types:
                filtered_relations = [
                    r for r in filtered_relations
                    if r.relation in request.relation_types
                ]

            if request.min_confidence is not None:
                filtered_relations = [
                    r for r in filtered_relations
                    if r.confidence >= request.min_confidence
                ]

            # Apply pagination
            total_count = len(filtered_relations)
            paginated_relations = filtered_relations[
                request.offset : request.offset + request.limit
            ]

            return RelationSearchResponse(
                total_count=total_count,
                returned_count=len(paginated_relations),
                relations=paginated_relations,
                limit=request.limit,
                offset=request.offset,
                has_more=(request.offset + request.limit) < total_count
            )

        except Exception as e:
            logger.error(f"Relation search failed: {str(e)}")
            raise
