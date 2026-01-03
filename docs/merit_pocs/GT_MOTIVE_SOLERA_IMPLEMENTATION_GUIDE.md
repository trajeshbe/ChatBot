# GT Motive & Solera Full Implementation Guide

**Date:** 2026-01-02
**Estimated Effort:** GT Motive (4 weeks) + Solera (3 weeks) = 7 weeks total
**Priority:** P1 - Next implementations after British Council, CRU, Grant Thornton

---

## ⚠️ Implementation Scope Notice

This guide provides the implementation roadmap and code structure for:
- **GT Motive POC**: Multi-modal part code extraction (Vision + NLP)
- **Solera POC**: Multi-OCR claims processing with VIN extraction

**Full implementation requires:**
- 4 weeks for GT Motive (multi-modal, Claude Vision, part code patterns)
- 3 weeks for Solera (multi-OCR pipeline, VIN extraction, damage assessment)
- Dedicated development resources
- Testing and validation

This document provides:
1. Complete implementation roadmap
2. Code structure and patterns to follow
3. Service architectures
4. Integration points with existing infrastructure

---

## Table of Contents

### GT Motive Implementation
1. [GT Motive Overview](#gt-motive-overview)
2. [GT Motive Phase 1: Core Architecture](#gt-motive-phase-1)
3. [GT Motive Phase 2: Part Code Patterns](#gt-motive-phase-2)
4. [GT Motive Phase 3: Claude Vision](#gt-motive-phase-3)
5. [GT Motive Phase 4: Excel Export](#gt-motive-phase-4)

### Solera Implementation
6. [Solera Overview](#solera-overview)
7. [Solera Phase 1: Multi-OCR Pipeline](#solera-phase-1)
8. [Solera Phase 2: VIN Extraction](#solera-phase-2)
9. [Solera Phase 3: Damage Classification](#solera-phase-3)
10. [Solera Phase 4: Claims Reports](#solera-phase-4)

### Integration
11. [Frontend Integration](#frontend-integration)
12. [Testing Strategy](#testing-strategy)
13. [Deployment Checklist](#deployment-checklist)

---

## GT Motive Overview

**Customer:** GT Motive (Automotive Parts)
**Use Case:** Extract part codes from technical diagrams, catalogs, and manuals

### Key Features
- Multi-modal processing (text PDFs + technical diagram images)
- Claude 3.5 Sonnet Vision for diagram analysis
- Regex-based part code extraction for BMW, Mercedes, Audi, VW, Toyota, Ford
- Vehicle model mapping
- Excel export with part catalogs

### Technology Stack
- **Vision Model:** Claude 3.5 Sonnet Vision (for diagrams)
- **Text Extraction:** Docling (existing)
- **OCR:** Tesseract + PaddleOCR (existing)
- **Part Code Patterns:** Regex + LLM fallback
- **Vector DB:** ChromaDB (existing)
- **Keyword Search:** Elasticsearch (optional)
- **Export:** openpyxl (existing from Grant Thornton)

### Success Metrics
- Part code extraction accuracy: >95%
- Multi-modal processing: Text + image support
- Query response time: <5 seconds
- Excel export completeness: 100% of extracted codes

---

## GT Motive Phase 1: Core Architecture

### 1.1 Enhanced Service Structure

**File:** `backend/app/tier_3/customer_solutions/gt_motive_service_enhanced.py`

```python
"""GT Motive POC - Multi-Modal Part Code Extraction Service"""
import logging
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel
import base64

from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from app.services.vision_service import VisionService
from app.services.document_service import DocumentService
from app.utils.docling_analyzer import analyze_document_with_docling
from app.services.ocr_service import OCRService
from .gt_motive_schemas import *

logger = logging.getLogger(__name__)

class PartCode(BaseModel):
    """Extracted part code with metadata"""
    code: str
    description: str = ""
    price: Optional[float] = None
    vehicle_models: List[str] = []
    source_page: int
    confidence: float  # 0-1
    extraction_method: str  # "regex", "llm", "vision"

class GtMotiveServiceEnhanced:
    """Multi-modal automotive part code extraction service"""
    
    # Part code regex patterns for major brands
    PART_CODE_PATTERNS = {
        "bmw": r"\b[0-9]{11}\b",  # BMW: 11 digits (e.g., 51117140850)
        "mercedes": r"\b[A-Z][0-9]{3}[-\s]?[0-9]{3}[-\s]?[0-9]{2}[-\s]?[0-9]{2}\b",  # Mercedes: A123-456-78-90
        "audi": r"\b[0-9]{3}[-\s]?[0-9]{3}[-\s]?[0-9]{3}[-\s]?[A-Z]{1,2}\b",  # Audi: 123-456-789-A
        "vw": r"\b[0-9]{3}[-\s]?[0-9]{3}[-\s]?[0-9]{3}\b",  # VW: 123-456-789
        "toyota": r"\b[0-9]{5}[-\s]?[0-9]{5}\b",  # Toyota: 12345-67890
        "ford": r"\b[A-Z]{1,2}[0-9]{2}[-\s]?[0-9]{4,5}[-\s]?[A-Z]{0,2}\b",  # Ford: AB12-3456-CD
        "generic": r"\b[A-Z0-9]{8,15}\b"  # Generic alphanumeric
    }
    
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.llm_service = LLMService()
        self.vision_service = VisionService()
        self.document_service = DocumentService(db)
        self.ocr_service = OCRService()
    
    async def extract_part_codes(
        self,
        file_path: str,
        file_type: str,
        brand: str = "generic",
        use_vision: bool = True
    ) -> List[PartCode]:
        """
        Extract part codes from document using multi-modal approach.
        
        Args:
            file_path: Path to document (PDF or image)
            file_type: File type (pdf, jpg, png)
            brand: Vehicle brand for pattern matching
            use_vision: Whether to use Claude Vision for diagrams
            
        Returns:
            List of PartCode objects
        """
        logger.info(f"Extracting part codes from {file_path} (brand={brand}, vision={use_vision})")
        
        part_codes = []
        
        if file_type.lower() == "pdf":
            # Text + table extraction using Docling
            part_codes.extend(await self._extract_from_pdf(file_path, brand))
        
        if file_type.lower() in ["jpg", "jpeg", "png"] and use_vision:
            # Vision-based extraction for technical diagrams
            part_codes.extend(await self._extract_from_image_vision(file_path, brand))
        elif file_type.lower() in ["jpg", "jpeg", "png"]:
            # OCR fallback
            part_codes.extend(await self._extract_from_image_ocr(file_path, brand))
        
        # Deduplicate by code
        unique_codes = self._deduplicate_part_codes(part_codes)
        
        logger.info(f"Extracted {len(unique_codes)} unique part codes")
        return unique_codes
    
    async def _extract_from_pdf(self, file_path: str, brand: str) -> List[PartCode]:
        """Extract part codes from PDF using Docling + regex"""
        part_codes = []
        
        try:
            # Use Docling to extract text and tables
            doc_result = await analyze_document_with_docling(file_path)
            
            # Extract from text content
            for page_num, page_content in enumerate(doc_result.get("pages", []), start=1):
                text = page_content.get("text", "")
                codes = self._extract_codes_from_text(text, brand, page_num)
                part_codes.extend(codes)
            
            # Extract from tables
            for table in doc_result.get("tables", []):
                table_codes = await self._extract_codes_from_table(table, brand)
                part_codes.extend(table_codes)
        
        except Exception as e:
            logger.error(f"PDF extraction error: {e}", exc_info=True)
        
        return part_codes
    
    def _extract_codes_from_text(
        self,
        text: str,
        brand: str,
        page_no: int
    ) -> List[PartCode]:
        """Extract part codes from plain text using regex"""
        part_codes = []
        pattern = self.PART_CODE_PATTERNS.get(brand.lower(), self.PART_CODE_PATTERNS["generic"])
        
        matches = re.findall(pattern, text)
        unique_codes = list(set(matches))
        
        for code in unique_codes:
            # Try to extract description from surrounding text
            description = self._extract_description_near_code(text, code)
            
            part_codes.append(PartCode(
                code=code.strip(),
                description=description,
                source_page=page_no,
                confidence=0.9,  # High confidence for regex matches
                extraction_method="regex"
            ))
        
        return part_codes
    
    def _extract_description_near_code(self, text: str, code: str) -> str:
        """Extract description text near the part code"""
        try:
            # Find code position
            idx = text.find(code)
            if idx == -1:
                return ""
            
            # Extract 100 characters after code
            snippet = text[idx:idx+150]
            
            # Clean and return first sentence
            sentences = snippet.split('.')
            return sentences[0].replace(code, "").strip() if sentences else ""
        except:
            return ""
    
    async def _extract_codes_from_table(
        self,
        table: Dict[str, Any],
        brand: str
    ) -> List[PartCode]:
        """Extract part codes from table structure"""
        part_codes = []
        
        try:
            # Table format: [{ "Part Code": "...", "Description": "...", "Price": "..." }, ...]
            for row in table.get("rows", []):
                code = None
                description = ""
                price = None
                
                # Find part code column
                for key, value in row.items():
                    if "code" in key.lower() or "number" in key.lower():
                        code = str(value).strip()
                    elif "description" in key.lower() or "name" in key.lower():
                        description = str(value).strip()
                    elif "price" in key.lower() or "cost" in key.lower():
                        try:
                            price = float(str(value).replace("$", "").replace("€", "").strip())
                        except:
                            price = None
                
                if code:
                    part_codes.append(PartCode(
                        code=code,
                        description=description,
                        price=price,
                        source_page=table.get("page", 1),
                        confidence=0.95,  # Very high confidence for table data
                        extraction_method="table"
                    ))
        
        except Exception as e:
            logger.error(f"Table extraction error: {e}", exc_info=True)
        
        return part_codes
    
    async def _extract_from_image_vision(
        self,
        image_path: str,
        brand: str
    ) -> List[PartCode]:
        """Extract part codes from technical diagrams using Claude Vision"""
        part_codes = []
        
        try:
            # Read image as base64
            with open(image_path, "rb") as img_file:
                image_data = base64.b64encode(img_file.read()).decode("utf-8")
            
            # Claude Vision prompt for part code extraction
            prompt = f"""Analyze this automotive technical diagram and extract all visible part codes.
            
This is a {brand.upper()} parts diagram. Look for:
1. Callout numbers (1, 2, 3, ...) pointing to parts
2. Part codes in format: {self._get_example_format(brand)}
3. Part descriptions or names

Return a JSON array with format:
[
  {{"code": "part_code_here", "description": "part description", "callout": "callout number"}},
  ...
]

If you see a legend or table matching callouts to part codes, extract all mappings.
"""
            
            response = await self.vision_service.analyze_image(
                image_data=image_data,
                prompt=prompt,
                model="claude-3-5-sonnet-20241022"
            )
            
            # Parse Vision response and create PartCode objects
            import json
            try:
                vision_data = json.loads(response.get("text", "[]"))
                for item in vision_data:
                    part_codes.append(PartCode(
                        code=item.get("code", ""),
                        description=item.get("description", ""),
                        source_page=1,
                        confidence=0.85,  # Good confidence for vision
                        extraction_method="vision"
                    ))
            except json.JSONDecodeError:
                logger.warning("Could not parse Vision response as JSON")
        
        except Exception as e:
            logger.error(f"Vision extraction error: {e}", exc_info=True)
        
        return part_codes
    
    async def _extract_from_image_ocr(
        self,
        image_path: str,
        brand: str
    ) -> List[PartCode]:
        """Extract part codes from image using OCR (fallback)"""
        part_codes = []
        
        try:
            # Use OCR service
            ocr_result = await self.ocr_service.extract_text(image_path)
            text = ocr_result.get("text", "")
            
            # Apply regex extraction
            part_codes = self._extract_codes_from_text(text, brand, page_no=1)
            
            # Update extraction method
            for pc in part_codes:
                pc.extraction_method = "ocr"
                pc.confidence = 0.75  # Lower confidence for OCR
        
        except Exception as e:
            logger.error(f"OCR extraction error: {e}", exc_info=True)
        
        return part_codes
    
    def _get_example_format(self, brand: str) -> str:
        """Get example part code format for brand"""
        examples = {
            "bmw": "51117140850 (11 digits)",
            "mercedes": "A123-456-78-90",
            "audi": "123-456-789-A",
            "vw": "123-456-789",
            "toyota": "12345-67890",
            "ford": "AB12-3456-CD",
            "generic": "alphanumeric 8-15 characters"
        }
        return examples.get(brand.lower(), examples["generic"])
    
    def _deduplicate_part_codes(self, part_codes: List[PartCode]) -> List[PartCode]:
        """Deduplicate part codes, keeping highest confidence"""
        unique = {}
        for pc in part_codes:
            if pc.code not in unique or pc.confidence > unique[pc.code].confidence:
                unique[pc.code] = pc
        return list(unique.values())
    
    async def process_request(
        self,
        request: Gt_motiveRequest
    ) -> Gt_motiveResponse:
        """Main entry point for GT Motive POC"""
        try:
            # For now, use enhanced logic or fallback to basic
            if request.query:
                # Query-based extraction (future)
                insights = f"GT Motive POC ready for multi-modal part code extraction. Upload PDF catalogs or technical diagrams."
                return Gt_motiveResponse(
                    success=True,
                    session_id=request.session_id,
                    result={"query": request.query, "status": "ready"},
                    insights=insights,
                    recommendations=[
                        "Upload a parts catalog PDF for text-based extraction",
                        "Upload a technical diagram image for vision-based extraction",
                        "Specify vehicle brand (BMW, Mercedes, Audi, etc.) for better accuracy"
                    ]
                )
        
        except Exception as e:
            logger.error(f"GT Motive error: {e}", exc_info=True)
            raise
    
    async def get_status(self) -> StatusResponse:
        """Get enhanced POC status"""
        return StatusResponse(
            success=True,
            status="operational",
            description="Multi-modal automotive part code extraction (Vision + NLP)",
            tier_2_modules_used=[
                "document-intelligence (Docling)",
                "vision-service (Claude 3.5 Sonnet)",
                "ocr-service (Tesseract + PaddleOCR)",
                "intelligent-embeddings (BAAI/bge-large)"
            ],
            capabilities=[
                "Multi-modal processing (text PDFs + technical diagrams)",
                "Regex-based extraction for BMW, Mercedes, Audi, VW, Toyota, Ford",
                "Claude Vision for exploded diagrams",
                "Vehicle model mapping",
                "Excel export with part catalogs"
            ]
        )
```

### 1.2 Implementation Steps for Phase 1

**Week 1-2: Core Multi-Modal Extraction**

1. **Create enhanced service** (`gt_motive_service_enhanced.py`)
2. **Implement regex patterns** for all major brands
3. **Integrate Docling** for PDF text + table extraction
4. **Add OCR fallback** for scanned documents
5. **Test with sample catalogs**

**Deliverables:**
- Text-based part code extraction working
- Table extraction functional
- OCR fallback operational
- Unit tests for regex patterns

---

## GT Motive Phase 2: Part Code Patterns

### 2.1 Part Code Validation Service

**File:** `backend/app/services/gt_motive/part_code_validator.py`

```python
"""Part Code Validation and Catalog Lookup"""
import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class PartCodeValidator:
    """Validate extracted part codes against catalog database"""
    
    def __init__(self, db: Session):
        self.db = db
        # In production, load reference catalog from database
        self.catalog = self._load_catalog()
    
    def _load_catalog(self) -> Dict[str, Dict]:
        """Load part code catalog (mock for now)"""
        # TODO: Load from database table: part_codes_catalog
        return {}
    
    async def validate_codes(
        self,
        part_codes: List[str],
        brand: str = "generic"
    ) -> Dict[str, bool]:
        """
        Validate part codes against catalog.
        
        Returns:
            Dict mapping part_code -> is_valid
        """
        validation = {}
        for code in part_codes:
            validation[code] = self._is_valid_format(code, brand)
        return validation
    
    def _is_valid_format(self, code: str, brand: str) -> bool:
        """Check if code matches expected format for brand"""
        import re
        patterns = {
            "bmw": r"^\d{11}$",
            "mercedes": r"^[A-Z]\d{3}-?\d{3}-?\d{2}-?\d{2}$",
            "audi": r"^\d{3}-?\d{3}-?\d{3}-?[A-Z]{1,2}$",
            "generic": r"^[A-Z0-9]{8,15}$"
        }
        pattern = patterns.get(brand.lower(), patterns["generic"])
        return bool(re.match(pattern, code))
    
    async def enrich_codes(
        self,
        part_codes: List[str]
    ) -> Dict[str, Dict]:
        """
        Enrich part codes with catalog data (description, price, vehicle models).
        
        Returns:
            Dict mapping part_code -> {description, price, models, ...}
        """
        enriched = {}
        for code in part_codes:
            # TODO: Query database for part code details
            enriched[code] = {
                "valid": self._is_valid_format(code, "generic"),
                "description": "",
                "price": None,
                "models": []
            }
        return enriched
```

### 2.2 Vehicle Model Mapping

**File:** `backend/app/services/gt_motive/vehicle_mapper.py`

```python
"""Vehicle Model Mapping Service"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class VehicleMapper:
    """Map part codes to compatible vehicle models"""
    
    # Vehicle model database (mock)
    VEHICLE_MODELS = {
        "BMW": {
            "3-Series": {
                "F30": {"years": "2012-2019", "engine": ["320i", "328i", "335i"]},
                "G20": {"years": "2019-2024", "engine": ["320i", "330i", "M340i"]}
            },
            "5-Series": {
                "F10": {"years": "2010-2017"},
                "G30": {"years": "2017-2024"}
            }
        },
        "Mercedes": {
            "C-Class": {
                "W204": {"years": "2007-2014"},
                "W205": {"years": "2014-2021"}
            }
        }
    }
    
    async def map_part_to_vehicles(
        self,
        part_code: str,
        brand: str
    ) -> List[Dict]:
        """
        Map part code to compatible vehicle models.
        
        Returns:
            List of compatible models: [{"model": "3-Series F30", "years": "2012-2019"}, ...]
        """
        # TODO: Query database for actual compatibility
        # For now, return mock data based on brand
        vehicles = []
        
        if brand.upper() in self.VEHICLE_MODELS:
            for model, variants in self.VEHICLE_MODELS[brand.upper()].items():
                for variant, details in variants.items():
                    vehicles.append({
                        "brand": brand,
                        "model": f"{model} {variant}",
                        "years": details.get("years", "Unknown"),
                        "compatibility": "exact"  # or "compatible", "unknown"
                    })
        
        return vehicles
```

---

## GT Motive Phase 3: Claude Vision Integration

### 3.1 Vision-Based Diagram Extraction

**Already implemented in Phase 1:** See `_extract_from_image_vision()` method above.

**Key Enhancements:**

1. **Callout Detection**: Detect numbered callouts (1, 2, 3, ...) in exploded diagrams
2. **Legend Extraction**: Extract callout → part code mappings from diagram legends
3. **Position Mapping**: Map callout positions to diagram locations

**Example Vision Prompt:**
```
Analyze this automotive exploded diagram. Extract:
1. All numbered callouts (1, 2, 3, ...)
2. The legend/table mapping callouts to part codes
3. Part descriptions for each callout

Return JSON format:
[
  {"callout": "1", "code": "51117140850", "description": "Front Bumper Cover", "position": "top-left"},
  {"callout": "2", "code": "63117240037", "description": "LED Headlight Left", "position": "center"},
  ...
]
```

### 3.2 Testing Claude Vision

**Test Script:** `backend/test_gt_motive_vision.py`

```python
import asyncio
from app.tier_3.customer_solutions.gt_motive_service_enhanced import GtMotiveServiceEnhanced
from app.core.database import SessionLocal
from app.tier_1.infrastructure.config import get_settings

async def test_vision_extraction():
    db = SessionLocal()
    settings = get_settings()
    service = GtMotiveServiceEnhanced(db, settings)
    
    # Test with sample technical diagram
    image_path = "/path/to/bmw_exploded_diagram.jpg"
    brand = "bmw"
    
    part_codes = await service._extract_from_image_vision(image_path, brand)
    
    print(f"Extracted {len(part_codes)} part codes using Vision:")
    for pc in part_codes:
        print(f"  - Code: {pc.code}, Description: {pc.description}, Confidence: {pc.confidence}")

if __name__ == "__main__":
    asyncio.run(test_vision_extraction())
```

---

## GT Motive Phase 4: Excel Export & Vehicle Mapping

### 4.1 Excel Export Service

**File:** `backend/app/services/gt_motive/excel_exporter.py`

Reuse from Grant Thornton with modifications:

```python
"""GT Motive Excel Export Service"""
import logging
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from typing import List
from ..gt_motive_service_enhanced import PartCode

logger = logging.getLogger(__name__)

class GtMotiveExcelExporter:
    """Export part codes to formatted Excel file"""
    
    async def export_part_codes(
        self,
        part_codes: List[PartCode],
        output_path: str,
        brand: str = "Generic"
    ):
        """Export extracted part codes to Excel"""
        wb = Workbook()
        ws = wb.active
        ws.title = f"{brand} Parts Catalog"
        
        # Header row
        headers = ["Part Code", "Description", "Price", "Vehicle Models", "Source Page", "Confidence", "Method"]
        ws.append(headers)
        
        # Style headers
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")
        
        # Data rows
        for pc in part_codes:
            ws.append([
                pc.code,
                pc.description,
                pc.price if pc.price else "",
                ", ".join(pc.vehicle_models),
                pc.source_page,
                f"{pc.confidence:.2%}",
                pc.extraction_method
            ])
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[column_letter].width = min(max_length + 2, 50)
        
        # Save
        wb.save(output_path)
        logger.info(f"Exported {len(part_codes)} part codes to {output_path}")
```

---

## Solera Overview

**Customer:** Solera (Insurance & Auto Claims)
**Use Case:** OCR + Part Code Extraction from Claims Photos

### Key Features
- Multi-OCR pipeline (PaddleOCR primary + Tesseract + EasyOCR backups)
- VIN extraction with NHTSA API validation
- Damage classification (minor, moderate, severe, total loss)
- Claims report generation (PDF)

### Technology Stack
- **Primary OCR:** PaddleOCR (best for vehicle photos)
- **Backup OCR 1:** Tesseract (existing)
- **Backup OCR 2:** EasyOCR (easy to integrate)
- **VIN Decoder:** NHTSA API (free government API)
- **Damage Classification:** GPT-4o-mini with vision
- **Report Generation:** ReportLab (PDF) or jinja2 templates

### Success Metrics
- OCR accuracy: >90% for clear photos
- VIN extraction: >95% accuracy
- Part code detection: >85% accuracy
- Response time: <3 seconds per image

---

## Solera Phase 1: Multi-OCR Pipeline

### 1.1 Multi-OCR Service

**File:** `backend/app/services/solera/multi_ocr_service.py`

```python
"""Multi-OCR Pipeline Service for Solera POC"""
import logging
from typing import Dict, Any, List, Optional
import asyncio

logger = logging.getLogger(__name__)

class MultiOCRService:
    """Multi-OCR pipeline with fallback strategy"""
    
    def __init__(self):
        self.ocr_engines = []
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize OCR engines in priority order"""
        # Priority 1: PaddleOCR (best for vehicle photos)
        try:
            from paddleocr import PaddleOCR
            self.paddle_ocr = PaddleOCR(use_angle_cls=True, lang='en')
            self.ocr_engines.append(("paddleocr", self._paddle_extract))
            logger.info("PaddleOCR initialized successfully")
        except ImportError:
            logger.warning("PaddleOCR not available - install with: pip install paddleocr")
        
        # Priority 2: Tesseract (existing)
        try:
            import pytesseract
            self.tesseract = pytesseract
            self.ocr_engines.append(("tesseract", self._tesseract_extract))
            logger.info("Tesseract initialized successfully")
        except ImportError:
            logger.warning("Tesseract not available")
        
        # Priority 3: EasyOCR (good backup)
        try:
            import easyocr
            self.easy_ocr = easyocr.Reader(['en'])
            self.ocr_engines.append(("easyocr", self._easyocr_extract))
            logger.info("EasyOCR initialized successfully")
        except ImportError:
            logger.warning("EasyOCR not available - install with: pip install easyocr")
    
    async def extract_text(
        self,
        image_path: str,
        fallback: bool = True
    ) -> Dict[str, Any]:
        """
        Extract text from image using multi-OCR pipeline.
        
        Args:
            image_path: Path to image file
            fallback: If True, try backup engines if primary fails
            
        Returns:
            {
                "text": "extracted text",
                "confidence": 0.85,
                "engine": "paddleocr",
                "success": True
            }
        """
        results = []
        
        for engine_name, engine_func in self.ocr_engines:
            try:
                logger.info(f"Trying OCR engine: {engine_name}")
                result = await engine_func(image_path)
                results.append({
                    "engine": engine_name,
                    "text": result.get("text", ""),
                    "confidence": result.get("confidence", 0.0),
                    "success": True
                })
                
                # If confidence is good, return immediately
                if result.get("confidence", 0) > 0.7:
                    logger.info(f"OCR successful with {engine_name} (confidence={result['confidence']:.2f})")
                    return results[0]
                
                if not fallback:
                    break
            
            except Exception as e:
                logger.warning(f"OCR engine {engine_name} failed: {e}")
                results.append({
                    "engine": engine_name,
                    "text": "",
                    "confidence": 0.0,
                    "success": False,
                    "error": str(e)
                })
        
        # Return best result if all tried
        if results:
            best_result = max(results, key=lambda x: x.get("confidence", 0))
            return best_result
        
        return {"text": "", "confidence": 0.0, "engine": "none", "success": False}
    
    async def _paddle_extract(self, image_path: str) -> Dict[str, Any]:
        """Extract text using PaddleOCR"""
        result = self.paddle_ocr.ocr(image_path, cls=True)
        
        # Combine all detected text
        text_blocks = []
        confidence_scores = []
        
        for line in result[0] or []:
            if len(line) >= 2:
                text_blocks.append(line[1][0])
                confidence_scores.append(line[1][1])
        
        combined_text = "\n".join(text_blocks)
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return {
            "text": combined_text,
            "confidence": avg_confidence
        }
    
    async def _tesseract_extract(self, image_path: str) -> Dict[str, Any]:
        """Extract text using Tesseract"""
        from PIL import Image
        import pytesseract
        
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        
        # Tesseract doesn't provide confidence easily, use heuristic
        confidence = 0.6 if len(text) > 10 else 0.3
        
        return {
            "text": text,
            "confidence": confidence
        }
    
    async def _easyocr_extract(self, image_path: str) -> Dict[str, Any]:
        """Extract text using EasyOCR"""
        result = self.easy_ocr.readtext(image_path)
        
        # Combine all detected text
        text_blocks = []
        confidence_scores = []
        
        for detection in result:
            text_blocks.append(detection[1])
            confidence_scores.append(detection[2])
        
        combined_text = "\n".join(text_blocks)
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return {
            "text": combined_text,
            "confidence": avg_confidence
        }
```

### 1.2 Dependencies for Multi-OCR

Add to `backend/requirements.txt`:

```
# Multi-OCR Pipeline (Solera POC)
paddleocr>=2.7.0
easyocr>=1.7.0
pytesseract>=0.3.10
Pillow>=10.0.0
```

---

## Solera Phase 2: VIN Extraction

### 2.1 VIN Extraction Service

**File:** `backend/app/services/solera/vin_extractor.py`

```python
"""VIN Extraction and Validation Service"""
import logging
import re
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

class VINExtractor:
    """Extract and validate Vehicle Identification Numbers (VIN)"""
    
    # VIN pattern: 17 characters (letters + numbers, no I, O, Q)
    VIN_PATTERN = r"\b[A-HJ-NPR-Z0-9]{17}\b"
    
    def __init__(self):
        self.nhtsa_api_base = "https://vpic.nhtsa.dot.gov/api/vehicles"
    
    async def extract_vin_from_text(self, text: str) -> Optional[str]:
        """Extract VIN from OCR text"""
        matches = re.findall(self.VIN_PATTERN, text.upper())
        return matches[0] if matches else None
    
    async def validate_vin(self, vin: str) -> Dict[str, Any]:
        """
        Validate VIN using NHTSA API.
        
        Returns:
            {
                "valid": True/False,
                "make": "BMW",
                "model": "3-Series",
                "year": 2014,
                "details": {...}
            }
        """
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.nhtsa_api_base}/DecodeVin/{vin}?format=json"
                response = await client.get(url)
                data = response.json()
                
                if "Results" in data:
                    results = data["Results"]
                    
                    # Extract key fields
                    make = self._get_field(results, "Make")
                    model = self._get_field(results, "Model")
                    year = self._get_field(results, "ModelYear")
                    
                    return {
                        "valid": make is not None,
                        "vin": vin,
                        "make": make,
                        "model": model,
                        "year": year,
                        "details": results
                    }
        
        except Exception as e:
            logger.error(f"VIN validation error: {e}", exc_info=True)
        
        return {"valid": False, "vin": vin, "error": "Validation failed"}
    
    def _get_field(self, results: list, variable_name: str) -> Optional[str]:
        """Extract field from NHTSA results"""
        for item in results:
            if item.get("Variable") == variable_name:
                return item.get("Value")
        return None
```

---

## Solera Phase 3: Damage Classification

### 3.1 Damage Classifier Service

**File:** `backend/app/services/solera/damage_classifier.py`

```python
"""Damage Classification Service using Vision + LLM"""
import logging
from typing import Dict, Any
import base64

logger = logging.getLogger(__name__)

class DamageClassifier:
    """Classify vehicle damage severity from photos"""
    
    DAMAGE_LEVELS = {
        "minor": "Minor scratches, dents - repairable without major parts",
        "moderate": "Moderate damage - requires part replacement",
        "severe": "Severe damage - structural components affected",
        "total_loss": "Total loss - repair cost exceeds vehicle value"
    }
    
    def __init__(self, vision_service, llm_service):
        self.vision_service = vision_service
        self.llm_service = llm_service
    
    async def classify_damage(
        self,
        image_path: str
    ) -> Dict[str, Any]:
        """
        Classify vehicle damage from photo.
        
        Returns:
            {
                "severity": "moderate",
                "affected_parts": ["front_bumper", "headlight"],
                "estimated_cost": 1200,
                "details": "..."
            }
        """
        try:
            # Read image as base64
            with open(image_path, "rb") as img_file:
                image_data = base64.b64encode(img_file.read()).decode("utf-8")
            
            # Vision prompt for damage assessment
            prompt = """Analyze this vehicle damage photo and provide:

1. Damage severity: minor / moderate / severe / total_loss
2. Affected parts (list all visible damaged parts)
3. Estimated repair cost in USD
4. Brief assessment (2-3 sentences)

Return JSON format:
{
  "severity": "moderate",
  "affected_parts": ["front_bumper", "hood", "left_headlight"],
  "estimated_cost": 2500,
  "assessment": "Moderate front-end collision damage. Bumper cover needs replacement..."
}
"""
            
            response = await self.vision_service.analyze_image(
                image_data=image_data,
                prompt=prompt,
                model="gpt-4o"  # GPT-4o has vision capabilities
            )
            
            # Parse response
            import json
            result = json.loads(response.get("text", "{}"))
            
            return result
        
        except Exception as e:
            logger.error(f"Damage classification error: {e}", exc_info=True)
            return {
                "severity": "unknown",
                "affected_parts": [],
                "estimated_cost": 0,
                "error": str(e)
            }
```

---

## Solera Phase 4: Claims Report Generation

### 4.1 Claims Report Generator

**File:** `backend/app/services/solera/claims_report_generator.py`

```python
"""Claims Report PDF Generator"""
import logging
from datetime import datetime
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

logger = logging.getLogger(__name__)

class ClaimsReportGenerator:
    """Generate PDF claims reports"""
    
    async def generate_report(
        self,
        claim_data: Dict[str, Any],
        output_path: str
    ):
        """
        Generate claims report PDF.
        
        Args:
            claim_data: {
                "claim_id": "CLM-2024-001",
                "vin": "WBA3B1C50EP123456",
                "vehicle": {"make": "BMW", "model": "3-Series", "year": 2014},
                "damage": {"severity": "moderate", "parts": [...], "cost": 2500},
                "ocr_text": "extracted text",
                "images": ["path/to/photo1.jpg", ...]
            }
            output_path: Path to save PDF
        """
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#003366'),
            spaceAfter=30,
        )
        story.append(Paragraph("Insurance Claims Report", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Claim Info
        story.append(Paragraph(f"<b>Claim ID:</b> {claim_data.get('claim_id', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Vehicle Info
        vehicle = claim_data.get('vehicle', {})
        story.append(Paragraph("<b>Vehicle Information</b>", styles['Heading2']))
        vehicle_data = [
            ["VIN", claim_data.get('vin', 'Not detected')],
            ["Make", vehicle.get('make', 'Unknown')],
            ["Model", vehicle.get('model', 'Unknown')],
            ["Year", vehicle.get('year', 'Unknown')]
        ]
        vehicle_table = Table(vehicle_data, colWidths=[2*inch, 4*inch])
        vehicle_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(vehicle_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Damage Assessment
        damage = claim_data.get('damage', {})
        story.append(Paragraph("<b>Damage Assessment</b>", styles['Heading2']))
        story.append(Paragraph(f"<b>Severity:</b> {damage.get('severity', 'Unknown').upper()}", styles['Normal']))
        story.append(Paragraph(f"<b>Estimated Cost:</b> ${damage.get('estimated_cost', 0):,.2f}", styles['Normal']))
        
        affected_parts = damage.get('affected_parts', [])
        if affected_parts:
            story.append(Paragraph("<b>Affected Parts:</b>", styles['Normal']))
            for part in affected_parts:
                story.append(Paragraph(f"  • {part}", styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Add damage photos
        images = claim_data.get('images', [])
        if images:
            story.append(Paragraph("<b>Damage Photos</b>", styles['Heading2']))
            for img_path in images[:3]:  # Max 3 images
                try:
                    story.append(Image(img_path, width=4*inch, height=3*inch))
                    story.append(Spacer(1, 0.2*inch))
                except:
                    pass
        
        # Build PDF
        doc.build(story)
        logger.info(f"Claims report generated: {output_path}")
```

### 4.2 Add ReportLab Dependency

Add to `backend/requirements.txt`:

```
# Claims Report Generation (Solera POC)
reportlab>=4.0.0
```

---

## Frontend Integration

### Update Frontend Components

**File:** `frontend/src/pages/GTMotivePOC.tsx`

```typescript
import React, { useState } from 'react';
import axios from 'axios';

export default function GTMotivePOC() {
  const [file, setFile] = useState<File | null>(null);
  const [brand, setBrand] = useState('generic');
  const [useVision, setUseVision] = useState(true);
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('brand', brand);
    formData.append('use_vision', useVision.toString());

    try {
      const response = await axios.post(
        'http://localhost:8000/api/v1/gt-motive/extract',
        formData
      );
      setResults(response.data);
    } catch (error) {
      console.error('GT Motive extraction error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">GT Motive POC - Part Code Extraction</h1>
      
      <div className="mb-4">
        <label className="block mb-2">Vehicle Brand:</label>
        <select
          value={brand}
          onChange={(e) => setBrand(e.target.value)}
          className="border p-2 rounded"
        >
          <option value="generic">Generic</option>
          <option value="bmw">BMW</option>
          <option value="mercedes">Mercedes-Benz</option>
          <option value="audi">Audi</option>
          <option value="vw">Volkswagen</option>
          <option value="toyota">Toyota</option>
          <option value="ford">Ford</option>
        </select>
      </div>
      
      <div className="mb-4">
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={useVision}
            onChange={(e) => setUseVision(e.target.checked)}
            className="mr-2"
          />
          Use Claude Vision for diagrams
        </label>
      </div>
      
      <div className="mb-4">
        <input
          type="file"
          accept=".pdf,.jpg,.jpeg,.png"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="border p-2"
        />
      </div>
      
      <button
        onClick={handleUpload}
        disabled={!file || loading}
        className="bg-blue-500 text-white px-4 py-2 rounded disabled:bg-gray-400"
      >
        {loading ? 'Extracting...' : 'Extract Part Codes'}
      </button>
      
      {results && (
        <div className="mt-6">
          <h2 className="text-xl font-bold mb-2">Extracted Part Codes:</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full border">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border p-2">Code</th>
                  <th className="border p-2">Description</th>
                  <th className="border p-2">Method</th>
                  <th className="border p-2">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {results.part_codes?.map((pc: any, idx: number) => (
                  <tr key={idx}>
                    <td className="border p-2 font-mono">{pc.code}</td>
                    <td className="border p-2">{pc.description}</td>
                    <td className="border p-2">{pc.extraction_method}</td>
                    <td className="border p-2">{(pc.confidence * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## Testing Strategy

### Unit Tests

**File:** `backend/tests/test_gt_motive_enhanced.py`

```python
import pytest
from app.tier_3.customer_solutions.gt_motive_service_enhanced import GtMotiveServiceEnhanced, PartCode

def test_part_code_regex_bmw():
    """Test BMW part code extraction"""
    service = GtMotiveServiceEnhanced(None, None)
    text = "Front bumper part 51117140850 costs $450"
    
    codes = service._extract_codes_from_text(text, "bmw", 1)
    
    assert len(codes) == 1
    assert codes[0].code == "51117140850"
    assert codes[0].extraction_method == "regex"
    assert codes[0].confidence == 0.9

def test_part_code_regex_mercedes():
    """Test Mercedes part code extraction"""
    service = GtMotiveServiceEnhanced(None, None)
    text = "Headlight A123-456-78-90"
    
    codes = service._extract_codes_from_text(text, "mercedes", 1)
    
    assert len(codes) == 1
    assert "A123" in codes[0].code

def test_deduplication():
    """Test part code deduplication"""
    service = GtMotiveServiceEnhanced(None, None)
    
    part_codes = [
        PartCode(code="12345", description="Part A", source_page=1, confidence=0.8, extraction_method="regex"),
        PartCode(code="12345", description="Part A", source_page=1, confidence=0.9, extraction_method="table"),
        PartCode(code="67890", description="Part B", source_page=2, confidence=0.7, extraction_method="ocr")
    ]
    
    unique = service._deduplicate_part_codes(part_codes)
    
    assert len(unique) == 2
    # Should keep higher confidence "12345"
    for pc in unique:
        if pc.code == "12345":
            assert pc.confidence == 0.9
```

---

## Deployment Checklist

### Prerequisites

1. **Claude API Key** (for Vision)
2. **OpenAI API Key** (for LLM fallback)
3. **Docker** (for containers)
4. **MinIO** (for file storage)
5. **PostgreSQL** (for metadata)

### Dependencies Installation

```bash
# Backend dependencies
cd backend
pip install -r requirements.txt

# Additional for Solera
pip install paddleocr easyocr reportlab

# Frontend
cd ../frontend
npm install
```

### Environment Variables

Add to `.env`:

```
# GT Motive
CLAUDE_API_KEY=sk-ant-xxx
GT_MOTIVE_USE_VISION=true

# Solera
NHTSA_API_BASE=https://vpic.nhtsa.dot.gov/api/vehicles
SOLERA_ENABLE_MULTI_OCR=true
```

### Restart Services

```bash
docker-compose down
docker-compose up -d --build
```

---

## Implementation Timeline

| Week | GT Motive Tasks | Solera Tasks |
|------|----------------|--------------|
| **Week 1** | Regex patterns + Docling integration | Multi-OCR pipeline setup |
| **Week 2** | OCR fallback + table extraction | VIN extraction + NHTSA API |
| **Week 3** | Claude Vision integration | Damage classification |
| **Week 4** | Excel export + vehicle mapping | Claims report generation |
| **Week 5** | - | Frontend UI + testing |
| **Week 6** | Testing + refinements | Testing + refinements |
| **Week 7** | Deployment + documentation | Deployment + documentation |

---

## Next Steps

### For GT Motive

1. **Immediate** (Week 1-2):
   - Implement regex-based extraction
   - Test with sample BMW/Mercedes catalogs
   - Integrate Docling for PDF processing

2. **Short-term** (Week 3-4):
   - Add Claude Vision for diagrams
   - Implement Excel export
   - Build vehicle mapping database

3. **Production** (Week 5+):
   - Performance optimization
   - Extensive testing
   - Production deployment

### For Solera

1. **Immediate** (Week 1-2):
   - Setup multi-OCR pipeline
   - Test PaddleOCR vs Tesseract
   - Implement VIN extraction

2. **Short-term** (Week 3-4):
   - Add damage classification
   - Build claims report generator
   - Integrate with existing claims workflow

3. **Production** (Week 5+):
   - Accuracy validation
   - Integration testing
   - Production deployment

---

## Success Criteria

### GT Motive
- ✅ Part code extraction accuracy >95%
- ✅ Multi-modal support (PDF + images)
- ✅ Claude Vision working for diagrams
- ✅ Excel export functional
- ✅ Response time <5 seconds

### Solera
- ✅ OCR accuracy >90%
- ✅ VIN extraction >95%
- ✅ Multi-OCR fallback working
- ✅ Damage classification functional
- ✅ PDF reports generated
- ✅ Response time <3 seconds per image

---

**Generated:** 2026-01-02
**Status:** Implementation Guide Ready
**Next Action:** Begin Phase 1 implementations for GT Motive and Solera

**Related Documents:**
- `docs/merit_pocs/04_gt_motive_implementation_plan.md`
- `docs/merit_pocs/05_solera_implementation_plan.md`
- `TIER3_IMPLEMENTATION_COMPLETE_SUMMARY.md`
