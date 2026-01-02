"""
Document Intelligence Extraction Service

Extracts 18 structured fields from planning documents using tier_1 services.

Leverages:
- tier_1.llm.llm_service for GPT-4o Vision and text extraction
- tier_1.document_processing.vision_service for image analysis
- tier_1.document_processing.document_service for document parsing
- tier_1.document_processing.hybrid_extraction_service for combined extraction
- tier_1.document_processing.ocr_service for scanned documents
"""

import logging
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

# Import tier_1 services
from app.tier_1.llm.llm_service import LLMService
from app.tier_1.document_processing.vision_service import VisionService
from app.tier_1.document_processing.document_service import DocumentService
from app.tier_1.document_processing.hybrid_extraction_service import HybridExtractionService
from app.tier_1.document_processing.ocr_service import OCRService
from app.tier_1.infrastructure.config import Settings

# Import local schemas
from .schemas import (
    DocumentExtractionRequest,
    DocumentExtractionResult,
    DocumentExtractionResponse,
    ProjectStatus
)

logger = logging.getLogger(__name__)


class DocumentExtractionService:
    """
    Document Intelligence Extraction Service
    
    Extracts 18 structured data fields from planning documents and architectural drawings:
    
    Project Metadata (11 fields):
    1. Project Name, 2. Address, 3. Project Status, 4. Storeys, 5. GFA,
    6. Site Area, 7. Zoning, 8. Heritage Designation, 9. Architect,
    10. Developer, 11. Planning Consultant
    
    Building Information (7 fields):
    12. Residential Units, 13. Unit Types, 14. Commercial Uses, 15. Amenities,
    16. Parking Levels, 17. Parking Spaces, 18. Public Realm Features
    """
    
    # Extraction prompt template
    EXTRACTION_PROMPT = """
You are an AI assistant specialized in extracting structured data from planning documents and architectural drawings.

Analyze the provided document and extract the following 18 fields:

**Project Metadata (11 fields):**
1. **Project Name**: Name of the development project
2. **Address**: Complete street address including city
3. **Project Status**: Current status (approved, pending, rejected, in_progress, under_review, unknown)
4. **Storeys**: Number of building floors/storeys (integer)
5. **Gross Floor Area (GFA)**: Total GFA in square meters or square feet (number)
6. **Site Area**: Total site area in square meters or square feet (number)
7. **Zoning**: Zoning classification (e.g., R-4, C-2, M-1)
8. **Heritage Designation**: Heritage or conservation status
9. **Architect**: Architect firm name
10. **Developer**: Developer company name
11. **Planning Consultant**: Planning consultant name

**Building Information (7 fields):**
12. **Residential Units**: Total number of residential units (integer)
13. **Unit Types**: List of unit types (e.g., ["1BR", "2BR", "3BR", "penthouse"])
14. **Commercial Uses**: List of commercial uses (e.g., ["retail", "office", "restaurant"])
15. **Amenities**: List of amenities (e.g., ["gym", "pool", "rooftop terrace"])
16. **Parking Levels**: Number of parking levels, underground or above (integer)
17. **Parking Spaces**: Total parking spaces (integer)
18. **Public Realm Features**: List of public features (e.g., ["plaza", "park", "pathway"])

**Instructions:**
- Extract EXACT values from the document text or image
- For missing fields, return null (not empty string or 0)
- For list fields (unit_types, commercial_uses, amenities, public_realm_features), return as JSON arrays
- For numeric fields, return numbers (not strings)
- For project_status, use one of: "approved", "pending", "rejected", "in_progress", "under_review", "unknown"
- Be precise with units (specify if square meters or square feet)

**Return format:**
Return a valid JSON object with all 18 fields using these exact field names:
```json
{
  "project_name": "string or null",
  "address": "string or null",
  "project_status": "approved|pending|rejected|in_progress|under_review|unknown or null",
  "storeys": number or null,
  "gross_floor_area": number or null,
  "site_area": number or null,
  "zoning": "string or null",
  "heritage_designation": "string or null",
  "architect": "string or null",
  "developer": "string or null",
  "planning_consultant": "string or null",
  "residential_units": number or null,
  "unit_types": ["array"] or null,
  "commercial_uses": ["array"] or null,
  "amenities": ["array"] or null,
  "parking_levels": number or null,
  "parking_spaces": number or null,
  "public_realm_features": ["array"] or null
}
```

Now analyze the document and extract the data.
"""
    
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        
        # Initialize tier_1 services
        self.llm_service = LLMService(db, settings)
        self.vision_service = VisionService(db, settings)
        self.document_service = DocumentService(db, settings)
        self.hybrid_service = HybridExtractionService(db, settings)
        self.ocr_service = OCRService(settings)
        
        logger.info("DocumentExtractionService initialized with tier_1 services")
    
    async def extract_data(
        self,
        request: DocumentExtractionRequest
    ) -> DocumentExtractionResponse:
        """
        Extract 18 structured fields from a document
        
        Args:
            request: DocumentExtractionRequest with document_id and options
        
        Returns:
            DocumentExtractionResponse with extracted data
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting extraction for document: {request.document_id}")
            
            # 1. Fetch document from database
            document = await self._get_document(request.document_id)
            if not document:
                return DocumentExtractionResponse(
                    success=False,
                    document_id=request.document_id,
                    session_id=request.session_id,
                    error=f"Document not found: {request.document_id}"
                )
            
            # 2. Determine extraction mode
            extract_mode = await self._determine_extraction_mode(
                document, 
                request.extract_mode
            )
            
            logger.info(f"Using extraction mode: {extract_mode}")
            
            # 3. Extract data based on mode
            if extract_mode == "vision":
                extracted_data = await self._extract_with_vision(document, request)
            elif extract_mode == "text":
                extracted_data = await self._extract_with_text(document, request)
            elif extract_mode == "hybrid":
                extracted_data = await self._extract_with_hybrid(document, request)
            else:  # auto
                # Try text first, fall back to vision
                try:
                    extracted_data = await self._extract_with_text(document, request)
                    if self._is_extraction_sufficient(extracted_data):
                        logger.info("Text extraction successful")
                    else:
                        logger.info("Text extraction insufficient, trying vision")
                        extracted_data = await self._extract_with_vision(document, request)
                except Exception as e:
                    logger.warning(f"Text extraction failed: {e}, trying vision")
                    extracted_data = await self._extract_with_vision(document, request)
            
            # 4. Calculate metrics
            processing_time_ms = int((time.time() - start_time) * 1000)
            fields_extracted = self._count_extracted_fields(extracted_data)
            
            # 5. Build result
            result = DocumentExtractionResult(
                **extracted_data,
                fields_extracted=fields_extracted,
                total_fields=18,
                extraction_method=extract_mode,
                processing_time_ms=processing_time_ms
            )
            
            logger.info(f"Extraction completed: {fields_extracted}/18 fields in {processing_time_ms}ms")
            
            return DocumentExtractionResponse(
                success=True,
                document_id=request.document_id,
                session_id=request.session_id,
                data=result,
                extracted_at=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}", exc_info=True)
            return DocumentExtractionResponse(
                success=False,
                document_id=request.document_id,
                session_id=request.session_id,
                error=str(e)
            )
    
    async def _get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Fetch document from database"""
        # Use tier_1 document_service
        return await self.document_service.get_document(document_id, self.db)
    
    async def _determine_extraction_mode(
        self, 
        document: Dict[str, Any], 
        requested_mode: str
    ) -> str:
        """Determine best extraction mode based on document type"""
        if requested_mode != "auto":
            return requested_mode
        
        # Auto-detect based on file type
        file_type = document.get("file_type", "").lower()
        
        if file_type in ["pdf", "docx", "txt", "md"]:
            return "text"
        elif file_type in ["png", "jpg", "jpeg", "tiff", "bmp"]:
            return "vision"
        else:
            return "hybrid"
    
    async def _extract_with_text(
        self,
        document: Dict[str, Any],
        request: DocumentExtractionRequest
    ) -> Dict[str, Any]:
        """Extract using text-based LLM (GPT-4o text mode)"""
        logger.info("Extracting with text mode")
        
        # Get document text content
        text_content = await self.document_service.get_document_text(
            document["id"],
            self.db
        )
        
        if not text_content:
            raise ValueError("No text content available for extraction")
        
        # Prepare prompt
        prompt = f"{self.EXTRACTION_PROMPT}\n\nDocument text:\n{text_content[:15000]}"
        
        # Call LLM service
        model_id = request.model_id or "gpt-4o"
        response = await self.llm_service.generate(
            prompt=prompt,
            model_id=model_id,
            temperature=0.1,  # Low temperature for structured extraction
            max_tokens=2000,
            response_format="json_object"  # Force JSON output
        )
        
        # Parse JSON response
        extracted_data = json.loads(response["content"])
        extracted_data["model_used"] = model_id
        extracted_data["extraction_method"] = "text"
        
        return extracted_data
    
    async def _extract_with_vision(
        self,
        document: Dict[str, Any],
        request: DocumentExtractionRequest
    ) -> Dict[str, Any]:
        """Extract using Vision (GPT-4o vision mode)"""
        logger.info("Extracting with vision mode")
        
        # Use tier_1 vision_service
        model_id = request.model_id or "gpt-4o"
        
        result = await self.vision_service.analyze_document(
            document_id=document["id"],
            query=self.EXTRACTION_PROMPT,
            model_id=model_id,
            db=self.db
        )
        
        # Parse JSON from vision response
        extracted_data = json.loads(result["analysis"])
        extracted_data["model_used"] = model_id
        extracted_data["extraction_method"] = "vision"
        
        return extracted_data
    
    async def _extract_with_hybrid(
        self,
        document: Dict[str, Any],
        request: DocumentExtractionRequest
    ) -> Dict[str, Any]:
        """Extract using hybrid (text + vision)"""
        logger.info("Extracting with hybrid mode")
        
        # Use tier_1 hybrid_extraction_service
        result = await self.hybrid_service.extract_structured_data(
            document_id=document["id"],
            schema=self._get_extraction_schema(),
            db=self.db
        )
        
        result["model_used"] = request.model_id or "gpt-4o"
        result["extraction_method"] = "hybrid"
        
        return result
    
    def _is_extraction_sufficient(self, data: Dict[str, Any]) -> bool:
        """Check if extraction has minimum required fields"""
        required_fields = ["project_name", "address", "storeys"]
        extracted_count = sum(1 for field in required_fields if data.get(field))
        return extracted_count >= 2  # At least 2/3 required fields
    
    def _count_extracted_fields(self, data: Dict[str, Any]) -> int:
        """Count non-null extracted fields"""
        field_names = [
            "project_name", "address", "project_status", "storeys", "gross_floor_area",
            "site_area", "zoning", "heritage_designation", "architect", "developer",
            "planning_consultant", "residential_units", "unit_types", "commercial_uses",
            "amenities", "parking_levels", "parking_spaces", "public_realm_features"
        ]
        return sum(1 for field in field_names if data.get(field) is not None)
    
    def _get_extraction_schema(self) -> Dict[str, Any]:
        """Get JSON schema for hybrid extraction"""
        return {
            "type": "object",
            "properties": {
                "project_name": {"type": ["string", "null"]},
                "address": {"type": ["string", "null"]},
                "project_status": {"type": ["string", "null"], "enum": ["approved", "pending", "rejected", "in_progress", "under_review", "unknown", None]},
                "storeys": {"type": ["integer", "null"]},
                "gross_floor_area": {"type": ["number", "null"]},
                "site_area": {"type": ["number", "null"]},
                "zoning": {"type": ["string", "null"]},
                "heritage_designation": {"type": ["string", "null"]},
                "architect": {"type": ["string", "null"]},
                "developer": {"type": ["string", "null"]},
                "planning_consultant": {"type": ["string", "null"]},
                "residential_units": {"type": ["integer", "null"]},
                "unit_types": {"type": ["array", "null"], "items": {"type": "string"}},
                "commercial_uses": {"type": ["array", "null"], "items": {"type": "string"}},
                "amenities": {"type": ["array", "null"], "items": {"type": "string"}},
                "parking_levels": {"type": ["integer", "null"]},
                "parking_spaces": {"type": ["integer", "null"]},
                "public_realm_features": {"type": ["array", "null"], "items": {"type": "string"}}
            },
            "required": []
        }
