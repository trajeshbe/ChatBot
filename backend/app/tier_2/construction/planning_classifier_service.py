"""
Planning Classifier Service
Tier 2 Module: Construction

Classifies planning documents by type and purpose using tier_1 services.
100% tier_1 service reuse - zero new dependencies.
"""

import uuid
import json
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from app.tier_1.document_processing.vision_service import VisionService
from app.tier_1.document_processing.document_service import DocumentService
from app.tier_1.document_processing.ocr_service import OCRService

from .planning_classifier_schemas import (
    PlanningClassificationRequest,
    PlanningClassificationResponse,
    BulkClassificationRequest,
    BulkClassificationResponse,
    ClassificationSearchRequest,
    ClassificationSearchResponse,
    DrawingClassification,
    ExtractedMetadata,
    PlanningDocumentType,
    PlanningDocumentPurpose,
    ClassificationStats
)

logger = logging.getLogger(__name__)


class PlanningClassifierService:
    """
    Classify planning documents by type and purpose.

    Classification Pipeline:
    1. Document Processing → Get document content (text/images)
    2. Feature Extraction → Extract visual and textual features
    3. Type Classification → Determine document type (architectural, structural, etc.)
    4. Purpose Classification → Determine purpose/phase (concept, construction docs, etc.)
    5. Metadata Extraction → Extract drawing number, revision, scale, etc.
    6. Validation → Confidence scoring and quality checks
    """

    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings

        # Tier 1 service dependencies
        self.llm_service = LLMService(db, settings)
        self.vision_service = VisionService(db, settings)
        self.document_service = DocumentService(db, settings)
        self.ocr_service = OCRService(settings)

        logger.info("✓ PlanningClassifierService initialized with tier_1 services")

    async def classify_document(
        self,
        request: PlanningClassificationRequest
    ) -> PlanningClassificationResponse:
        """
        Classify a single planning document.

        Args:
            request: Classification configuration

        Returns:
            PlanningClassificationResponse with classification results
        """
        start_time = datetime.utcnow()
        classification_id = str(uuid.uuid4())

        logger.info(f"📐 Classifying planning document {request.document_id}")

        try:
            # Step 1: Get document content
            document_content = await self._get_document_content(request.document_id)

            # Step 2: Determine classification method
            method = self._determine_method(request, document_content)
            logger.info(f"   Using method: {method}")

            # Step 3: Extract features
            features = await self._extract_features(
                document_content,
                method,
                request
            )

            # Step 4: Classify document type and purpose
            primary_classification = await self._classify_document_type_and_purpose(
                features,
                document_content
            )

            # Step 5: Get alternative classifications
            alternative_classifications = await self._get_alternative_classifications(
                features,
                document_content,
                primary_classification
            )

            # Step 6: Extract metadata if requested
            extracted_metadata = None
            if request.extract_metadata:
                extracted_metadata = await self._extract_metadata(
                    document_content,
                    features
                )

            # Step 7: Quality checks
            quality_indicators = self._assess_quality(document_content, features)

            # Step 8: Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()

            # Build response
            response = PlanningClassificationResponse(
                classification_id=classification_id,
                document_id=request.document_id,
                primary_classification=primary_classification,
                alternative_classifications=alternative_classifications,
                extracted_metadata=extracted_metadata,
                classification_method=method,
                processing_time_seconds=processing_time,
                tier_1_services_used=self._get_services_used(method),
                **quality_indicators
            )

            # Store in database
            await self._store_classification(request, response)

            logger.info(f"✓ Classification complete: {primary_classification.document_type.value} / {primary_classification.purpose.value} (confidence: {primary_classification.confidence:.2f})")

            return response

        except Exception as e:
            logger.error(f"❌ Classification failed: {str(e)}", exc_info=True)
            raise

    async def bulk_classify(
        self,
        request: BulkClassificationRequest
    ) -> BulkClassificationResponse:
        """Classify multiple documents in batch."""
        start_time = datetime.utcnow()
        batch_id = str(uuid.uuid4())

        logger.info(f"📐 Bulk classification: {len(request.document_ids)} documents")

        results = []
        errors = []

        if request.parallel_processing:
            # Process in parallel
            tasks = []
            for doc_id in request.document_ids:
                single_request = PlanningClassificationRequest(
                    document_id=doc_id,
                    session_id=request.session_id,
                    project_id=request.project_id,
                    use_vision=request.use_vision,
                    use_text=request.use_text,
                    extract_metadata=request.extract_metadata,
                    min_confidence=request.min_confidence
                )
                tasks.append(self.classify_document(single_request))

            # Run with semaphore to limit concurrency
            semaphore = asyncio.Semaphore(request.max_workers)
            async def bounded_classify(task):
                async with semaphore:
                    return await task

            completed = await asyncio.gather(
                *[bounded_classify(task) for task in tasks],
                return_exceptions=True
            )

            for i, result in enumerate(completed):
                if isinstance(result, Exception):
                    errors.append({
                        "document_id": request.document_ids[i],
                        "error": str(result)
                    })
                else:
                    results.append(result)
        else:
            # Process sequentially
            for doc_id in request.document_ids:
                try:
                    single_request = PlanningClassificationRequest(
                        document_id=doc_id,
                        session_id=request.session_id,
                        project_id=request.project_id,
                        use_vision=request.use_vision,
                        use_text=request.use_text,
                        extract_metadata=request.extract_metadata,
                        min_confidence=request.min_confidence
                    )
                    result = await self.classify_document(single_request)
                    results.append(result)
                except Exception as e:
                    errors.append({"document_id": doc_id, "error": str(e)})

        total_time = (datetime.utcnow() - start_time).total_seconds()

        return BulkClassificationResponse(
            batch_id=batch_id,
            total_documents=len(request.document_ids),
            successful_classifications=len(results),
            failed_classifications=len(errors),
            results=results,
            errors=errors,
            total_processing_time_seconds=total_time,
            avg_time_per_document_seconds=total_time / len(request.document_ids) if request.document_ids else 0
        )

    async def _get_document_content(self, document_id: str) -> Dict[str, Any]:
        """Get document content using DocumentService."""
        try:
            from app.models.database import Document
            doc = self.db.query(Document).filter(Document.id == document_id).first()

            if not doc:
                raise ValueError(f"Document {document_id} not found")

            content = {
                "document_id": document_id,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "file_path": doc.file_path,
                "text": "",
                "has_images": False
            }

            # Get text content
            chunks = await self.document_service.get_document_chunks(document_id)
            content["text"] = "\n\n".join([chunk.content for chunk in chunks[:5]])  # First 5 chunks

            # Check for images
            if doc.file_type.lower() in ["pdf", "png", "jpg", "jpeg", "tiff", "dwg"]:
                content["has_images"] = True

            return content

        except Exception as e:
            logger.error(f"Failed to get document content: {str(e)}")
            raise

    def _determine_method(
        self,
        request: PlanningClassificationRequest,
        document_content: Dict[str, Any]
    ) -> str:
        """Determine classification method based on request and content."""
        if request.use_vision and request.use_text and document_content.get("has_images"):
            return "hybrid"
        elif request.use_vision and document_content.get("has_images"):
            return "vision"
        elif request.use_text:
            return "text"
        else:
            return "auto"

    async def _extract_features(
        self,
        document_content: Dict[str, Any],
        method: str,
        request: PlanningClassificationRequest
    ) -> Dict[str, Any]:
        """Extract classification features from document."""
        features = {
            "filename": document_content["filename"],
            "file_type": document_content["file_type"],
            "text_keywords": [],
            "visual_features": [],
            "detected_elements": []
        }

        # Text-based feature extraction
        if method in ["text", "hybrid"]:
            text = document_content.get("text", "")
            features["text_keywords"] = self._extract_text_keywords(text)

        # Vision-based feature extraction
        if method in ["vision", "hybrid"] and document_content.get("has_images"):
            visual_features = await self._extract_visual_features(document_content)
            features["visual_features"] = visual_features

        return features

    def _extract_text_keywords(self, text: str) -> List[str]:
        """Extract keywords from text that indicate document type."""
        keywords = []
        text_lower = text.lower()

        # Document type indicators
        type_keywords = {
            "architectural": ["architectural", "floor plan", "elevation", "section"],
            "structural": ["structural", "beam", "column", "foundation", "rebar"],
            "electrical": ["electrical", "lighting", "power", "circuit", "panel"],
            "mechanical": ["mechanical", "hvac", "duct", "air conditioning"],
            "plumbing": ["plumbing", "water", "drain", "fixture", "pipe"],
            "civil": ["civil", "grading", "drainage", "site work"],
            "landscape": ["landscape", "planting", "irrigation"],
        }

        for doc_type, terms in type_keywords.items():
            if any(term in text_lower for term in terms):
                keywords.append(doc_type)

        return keywords

    async def _extract_visual_features(
        self,
        document_content: Dict[str, Any]
    ) -> List[str]:
        """Extract visual features using VisionService."""
        try:
            # Use vision service to analyze drawing
            prompt = """Analyze this technical drawing and identify:
1. Type of drawing (architectural, structural, electrical, etc.)
2. Drawing elements visible (walls, doors, dimensions, symbols, etc.)
3. Title block information if visible

Return a JSON array of detected features."""

            vision_result = await self.vision_service.analyze_image(
                document_id=document_content["document_id"],
                prompt=prompt
            )

            # Parse visual features
            if vision_result:
                return [vision_result]  # Simplified for now
            return []

        except Exception as e:
            logger.warning(f"Visual feature extraction failed: {str(e)}")
            return []

    async def _classify_document_type_and_purpose(
        self,
        features: Dict[str, Any],
        document_content: Dict[str, Any]
    ) -> DrawingClassification:
        """Classify document type and purpose using LLMService."""

        prompt = f"""Classify this planning/construction document based on the following information:

Filename: {features['filename']}
Text Keywords: {', '.join(features['text_keywords'])}
Visual Features: {', '.join(features['visual_features'])}
Detected Elements: {', '.join(features['detected_elements'])}

Classify into:
1. Document Type: architectural, structural, electrical, mechanical, plumbing, civil, landscape, interior, fire_safety, bim_model, site_plan, floor_plan, elevation, section, detail, schedule, specification
2. Purpose/Phase: concept, schematic_design, design_development, construction_documents, as_built, permit_submission, bid, shop_drawings, rfi, change_order, closeout

Return JSON:
{{
    "document_type": "type",
    "purpose": "purpose",
    "confidence": 0.95,
    "detected_features": ["feature1", "feature2"],
    "reasoning": "brief explanation"
}}

Return ONLY the JSON, no explanation."""

        try:
            llm_response = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.0,
                max_tokens=500
            )

            classification_data = json.loads(llm_response.strip())

            return DrawingClassification(
                document_type=PlanningDocumentType(classification_data.get("document_type", "unknown")),
                purpose=PlanningDocumentPurpose(classification_data.get("purpose", "unknown")),
                confidence=classification_data.get("confidence", 0.7),
                detected_features=classification_data.get("detected_features", []),
                metadata={"reasoning": classification_data.get("reasoning", "")}
            )

        except Exception as e:
            logger.error(f"Classification failed: {str(e)}")
            # Return default classification
            return DrawingClassification(
                document_type=PlanningDocumentType.UNKNOWN,
                purpose=PlanningDocumentPurpose.UNKNOWN,
                confidence=0.5,
                detected_features=[],
                metadata={"error": str(e)}
            )

    async def _get_alternative_classifications(
        self,
        features: Dict[str, Any],
        document_content: Dict[str, Any],
        primary: DrawingClassification
    ) -> List[DrawingClassification]:
        """Get alternative classifications with lower confidence."""
        # Simplified: return empty list for now
        # In production, this would return top 2-3 alternatives
        return []

    async def _extract_metadata(
        self,
        document_content: Dict[str, Any],
        features: Dict[str, Any]
    ) -> ExtractedMetadata:
        """Extract metadata from document using LLMService."""

        text = document_content.get("text", "")[:2000]

        prompt = f"""Extract metadata from this planning document:

{text}

Extract:
- Drawing number
- Drawing title
- Revision number
- Scale
- Date
- Project name
- Architect/Engineer name
- Sheet size
- Discipline

Return JSON:
{{
    "drawing_number": "A-101",
    "drawing_title": "First Floor Plan",
    "revision": "R3",
    "scale": "1/4\" = 1'-0\"",
    "date": "2024-01-15",
    "project_name": "Office Building",
    "architect": "ABC Architects",
    "sheet_size": "24x36",
    "discipline": "Architecture"
}}

If information not found, use null. Return ONLY JSON."""

        try:
            llm_response = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.0,
                max_tokens=500
            )

            metadata_dict = json.loads(llm_response.strip())
            return ExtractedMetadata(**metadata_dict)

        except Exception as e:
            logger.warning(f"Metadata extraction failed: {str(e)}")
            return ExtractedMetadata()

    def _assess_quality(
        self,
        document_content: Dict[str, Any],
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess quality indicators of document."""
        return {
            "has_clear_title_block": "drawing_number" in str(features),
            "has_scale_indicator": "scale" in document_content.get("text", "").lower(),
            "has_revision_info": "revision" in document_content.get("text", "").lower(),
            "image_quality_score": 0.85  # Placeholder
        }

    def _get_services_used(self, method: str) -> List[str]:
        """Get list of tier_1 services used."""
        services = ["DocumentService", "LLMService"]
        if method in ["vision", "hybrid"]:
            services.append("VisionService")
        return services

    async def _store_classification(
        self,
        request: PlanningClassificationRequest,
        response: PlanningClassificationResponse
    ):
        """Store classification results in database."""
        try:
            from app.models.database_enhanced import ClassificationResults

            classification_record = ClassificationResults(
                id=uuid.uuid4(),
                classification_id=uuid.UUID(response.classification_id),
                module_id="planning-classifier",
                document_id=uuid.UUID(request.document_id),
                session_id=request.session_id,
                project_id=uuid.UUID(request.project_id) if request.project_id else None,
                result_data={
                    "primary_classification": response.primary_classification.dict(),
                    "alternative_classifications": [c.dict() for c in response.alternative_classifications],
                    "extracted_metadata": response.extracted_metadata.dict() if response.extracted_metadata else None,
                    "quality_indicators": {
                        "has_clear_title_block": response.has_clear_title_block,
                        "has_scale_indicator": response.has_scale_indicator,
                        "has_revision_info": response.has_revision_info,
                        "image_quality_score": response.image_quality_score
                    }
                },
                classification_method=response.classification_method,
                confidence_score=response.primary_classification.confidence,
                created_at=datetime.utcnow()
            )

            self.db.add(classification_record)
            self.db.commit()

            logger.info(f"✓ Stored classification results in database")

        except Exception as e:
            logger.error(f"Failed to store classification: {str(e)}")
            # Non-critical error, don't raise

    async def search_classifications(
        self,
        request: ClassificationSearchRequest
    ) -> ClassificationSearchResponse:
        """Search for classified documents."""
        try:
            from app.models.database_enhanced import ClassificationResults

            # Build query
            query = self.db.query(ClassificationResults).filter(
                ClassificationResults.module_id == "planning-classifier"
            )

            # Apply filters
            if request.session_id:
                query = query.filter(ClassificationResults.session_id == request.session_id)

            if request.project_id:
                query = query.filter(ClassificationResults.project_id == uuid.UUID(request.project_id))

            if request.min_confidence:
                query = query.filter(ClassificationResults.confidence_score >= request.min_confidence)

            # Get total count
            total_count = query.count()

            # Apply pagination
            records = query.order_by(
                ClassificationResults.created_at.desc()
            ).limit(request.limit).offset(request.offset).all()

            # Convert to response models
            results = []
            for record in records:
                # Reconstruct response from stored data
                primary_classification = DrawingClassification(**record.result_data["primary_classification"])

                result = PlanningClassificationResponse(
                    classification_id=str(record.classification_id),
                    document_id=str(record.document_id),
                    primary_classification=primary_classification,
                    alternative_classifications=[],
                    extracted_metadata=ExtractedMetadata(**record.result_data["extracted_metadata"]) if record.result_data.get("extracted_metadata") else None,
                    classification_method=record.classification_method,
                    processing_time_seconds=0.0,  # Not stored
                    tier_1_services_used=[],
                    has_clear_title_block=record.result_data["quality_indicators"].get("has_clear_title_block", False),
                    has_scale_indicator=record.result_data["quality_indicators"].get("has_scale_indicator", False),
                    has_revision_info=record.result_data["quality_indicators"].get("has_revision_info", False),
                    image_quality_score=record.result_data["quality_indicators"].get("image_quality_score"),
                    created_at=record.created_at
                )
                results.append(result)

            # Calculate aggregations
            type_counts = {}
            purpose_counts = {}
            for result in results:
                doc_type = result.primary_classification.document_type.value
                purpose = result.primary_classification.purpose.value
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
                purpose_counts[purpose] = purpose_counts.get(purpose, 0) + 1

            return ClassificationSearchResponse(
                total_count=total_count,
                returned_count=len(results),
                results=results,
                type_counts=type_counts,
                purpose_counts=purpose_counts,
                limit=request.limit,
                offset=request.offset,
                has_more=(request.offset + request.limit) < total_count
            )

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise
