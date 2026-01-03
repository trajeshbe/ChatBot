# GT Motive POC - Implementation Plan

> **Customer:** GT Motive (Automotive Parts)
> **Use Case:** Multi-Modal Part Code Extraction (Vision + NLP)
> **Priority:** Tier 2 (Medium - 60% code reuse, vision model required)
> **Estimated Effort:** 3-4 weeks
> **Created:** 2026-01-02

---

## Table of Contents
1. [Business Requirements](#1-business-requirements)
2. [Technical Architecture](#2-technical-architecture)
3. [Reusable Components](#3-reusable-components)
4. [New Components](#4-new-components)
5. [Data Flow](#5-data-flow)
6. [API Endpoints](#6-api-endpoints)
7. [Database Schema](#7-database-schema)
8. [Frontend UI](#8-frontend-ui)
9. [Testing Strategy](#9-testing-strategy)
10. [Deployment](#10-deployment)
11. [Timeline](#11-timeline)

---

## 1. Business Requirements

### 1.1 Core Functionality
- **Part Code Extraction**: Extract automotive part codes from PDFs, images, diagrams
- **Multi-Modal Processing**: Handle text, tables, technical drawings, exploded diagrams
- **Part Code Validation**: Verify extracted codes against catalog
- **Relationship Mapping**: Link part codes to vehicle models (e.g., "BMW 3-series 2020")
- **Export to Excel**: Generate structured catalogs with part codes + descriptions

### 1.2 Document Types
- **Parts Catalogs**: Text-based catalogs with part numbers, descriptions, prices
- **Technical Diagrams**: Exploded views with callout numbers
- **Service Manuals**: Repair procedures with part references
- **Images**: Photos of parts with visible labels/codes

### 1.3 Key Use Cases

**Use Case 1: Text-Based Extraction**
```
Input: PDF parts catalog with table
+-----------------+----------------------------------+--------+
| Part Code       | Description                      | Price  |
+-----------------+----------------------------------+--------+
| BMW-51117140850 | Front Bumper Cover (F30)         | €450   |
| BMW-63117240037 | LED Headlight Left (G20)         | €1200  |
+-----------------+----------------------------------+--------+

Output: Structured Excel with validated codes
```

**Use Case 2: Diagram Extraction**
```
Input: Exploded diagram image with callouts (1, 2, 3, ..., 45)
Output: Part codes extracted from callout table + mapped to diagram positions
```

**Use Case 3: Query-Based Extraction**
```
Query: "Find all BMW 3-series front suspension part codes"
Output: Filtered list with codes + descriptions
```

### 1.4 Success Metrics
- Part code extraction accuracy: >95%
- Multi-modal processing: Text + image support
- Query response time: <5 seconds
- Excel export completeness: 100% of extracted codes
- Catalog validation: 90% of codes verified against reference data

---

## 2. Technical Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GT MOTIVE POC STACK                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   DOCUMENT UPLOAD                        │  │
│  │  - PDF (parts catalog, service manual)                   │  │
│  │  - Image (technical diagram, photo)                      │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          MULTI-MODAL PROCESSING                          │  │
│  │                                                            │  │
│  │  ┌─────────────────┐         ┌──────────────────┐        │  │
│  │  │ TEXT PIPELINE   │         │ VISION PIPELINE  │        │  │
│  │  │                 │         │                  │        │  │
│  │  │ - Docling       │         │ - Claude Vision  │        │  │
│  │  │ - Table OCR     │         │ - Diagram OCR    │        │  │
│  │  │ - Regex         │         │ - Callout Map    │        │  │
│  │  └────────┬────────┘         └────────┬─────────┘        │  │
│  │           │                           │                    │  │
│  │           └────────────┬──────────────┘                    │  │
│  │                        │                                    │  │
│  └────────────────────────┼───────────────────────────────────┘  │
│                           │                                       │
│                           ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          PART CODE EXTRACTION ENGINE                     │  │
│  │  - Regex patterns for part codes                         │  │
│  │  - LLM-based extraction for unstructured text            │  │
│  │  - Validation against catalog database                   │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          HYBRID SEARCH (Infrastructure)                  │  │
│  │  - ChromaDB: Semantic search for part descriptions       │  │
│  │  - Elasticsearch: Keyword search for part codes          │  │
│  │  - Re-ranker: Improve precision                          │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          VEHICLE MODEL MAPPING                           │  │
│  │  - Map part codes to vehicle models                      │  │
│  │  - Link to year, trim, engine type                       │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          EXCEL EXPORT                                    │  │
│  │  - Structured catalog with part codes                    │  │
│  │  - Vehicle compatibility matrix                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Text Extraction** | Docling (existing) | PDF + table extraction |
| **Vision Model** | Claude 3.5 Sonnet Vision | Technical diagram understanding |
| **OCR** | Tesseract + PaddleOCR (existing) | Backup OCR for images |
| **Embeddings** | BAAI/bge-large-en-v1.5 | Semantic search for descriptions |
| **Vector DB** | ChromaDB (existing) | Part description search |
| **Keyword DB** | Elasticsearch (infrastructure) | Part code exact match |
| **Re-ranker** | BAAI/bge-reranker-large (infrastructure) | Precision boost |
| **LLM** | GPT-4o-mini | Unstructured text extraction |
| **Backend** | FastAPI + Pydantic | Existing stack |
| **Storage** | MinIO + PostgreSQL | Existing infrastructure |

---

## 3. Reusable Components

### 3.1 From Core Platform (60% Reuse)

| Component | Source | Reuse % | Usage in GT Motive |
|-----------|--------|---------|-------------------|
| **Document Service** | `app/services/document_service.py` | 80% | Upload PDFs + images to MinIO |
| **Docling Analyzer** | `app/utils/docling_analyzer.py` | 100% | Extract text + tables from PDFs |
| **Vision Service** | `app/services/vision_service.py` | 100% | Analyze technical diagrams |
| **OCR Service** | `app/services/ocr_service.py` | 100% | OCR for scanned catalogs |
| **Embedding Service** | `app/services/embedding_service.py` | 100% | Embed part descriptions |
| **Vector Store** | `app/rag_pipeline/retrieval.py` | 90% | Semantic search |

### 3.2 From Infrastructure (NEW)

| Component | Source | Usage |
|-----------|--------|-------|
| **Elasticsearch Service** | `infrastructure/elasticsearch_service.py` | Part code keyword search |
| **Multi-Pipeline Router** | `infrastructure/multi_pipeline_router.py` | Route queries (semantic vs keyword) |
| **Re-ranker Service** | `infrastructure/reranker_service.py` | Improve part code search precision |
| **Rank Fusion Service** | `infrastructure/rank_fusion_service.py` | Combine ChromaDB + Elasticsearch results |

### 3.3 From Grant Thornton

| Component | Source | Adaptation |
|-----------|--------|-----------|
| **Excel Export** | `grant_thornton/excel_exporter.py` | Export part codes to Excel |
| **Formula Normalization** | `grant_thornton/config.py` | Clean part code formats |

---

## 4. New Components

### 4.1 Part Code Extractor Service

**File:** `backend/app/services/gt_motive/part_code_extractor.py`

**Purpose:** Extract part codes using regex + LLM

```python
import re
from typing import List, Dict, Any
from pydantic import BaseModel

class PartCode(BaseModel):
    """Extracted part code with metadata."""
    code: str
    description: str
    price: float | None = None
    vehicle_models: List[str] = []
    source_page: int
    confidence: float  # 0-1

class PartCodeExtractor:
    """Extract automotive part codes from text and tables."""

    # Common part code patterns
    PATTERNS = {
        "bmw": r"\b[0-9]{11}\b",  # BMW: 11 digits
        "mercedes": r"\b[A-Z][0-9]{3}[-\s]?[0-9]{3}[-\s]?[0-9]{2}[-\s]?[0-9]{2}\b",
        "audi": r"\b[0-9]{3}[-\s]?[0-9]{3}[-\s]?[0-9]{3}[-\s]?[A-Z]{1,2}\b",
        "generic": r"\b[A-Z0-9]{8,15}\b"  # Generic alphanumeric
    }

    def __init__(self, llm_service):
        self.llm = llm_service

    async def extract_from_text(
        self,
        text: str,
        brand: str = "generic",
        page_no: int = 1
    ) -> List[PartCode]:
        """
        Extract part codes from plain text using regex.

        Args:
            text: Text content
            brand: Vehicle brand (bmw, mercedes, audi, generic)
            page_no: Source page number

        Returns:
            List of PartCode objects
        """
        pattern = self.PATTERNS.get(brand.lower(), self.PATTERNS["generic"])
        matches = re.findall(pattern, text)

        # Deduplicate
        unique_codes = list(set(matches))

        # Use LLM to extract descriptions
        part_codes = []
        for code in unique_codes:
            # Find context around code
            context = self._extract_context(text, code)

            # LLM extraction for description
            description = await self._extract_description(code, context)

            part_codes.append(PartCode(
                code=code,
                description=description,
                source_page=page_no,
                confidence=0.9  # High confidence for regex match
            ))

        return part_codes

    async def extract_from_table(
        self,
        table_data: List[List[str]],
        page_no: int = 1
    ) -> List[PartCode]:
        """
        Extract part codes from table structure.

        Expected table format:
        [
            ["Part Code", "Description", "Price"],
            ["BMW-51117140850", "Front Bumper Cover", "€450"],
            ...
        ]
        """
        if not table_data or len(table_data) < 2:
            return []

        headers = [h.lower() for h in table_data[0]]

        # Find column indexes
        code_idx = self._find_column(headers, ["part code", "code", "part number", "part no"])
        desc_idx = self._find_column(headers, ["description", "desc", "name"])
        price_idx = self._find_column(headers, ["price", "cost", "€", "$"])

        part_codes = []
        for row in table_data[1:]:
            if len(row) <= code_idx:
                continue

            code = row[code_idx].strip()
            description = row[desc_idx].strip() if desc_idx < len(row) else ""
            price_str = row[price_idx].strip() if price_idx < len(row) else ""

            # Parse price
            price = None
            if price_str:
                price_match = re.search(r"[\d,]+\.?\d*", price_str)
                if price_match:
                    price = float(price_match.group().replace(",", ""))

            part_codes.append(PartCode(
                code=code,
                description=description,
                price=price,
                source_page=page_no,
                confidence=0.95  # Very high for table extraction
            ))

        return part_codes

    async def extract_from_diagram(
        self,
        vision_response: Dict[str, Any],
        page_no: int = 1
    ) -> List[PartCode]:
        """
        Extract part codes from technical diagram via vision model.

        Vision model identifies callout numbers and matches to part table.

        Args:
            vision_response: Response from Claude Vision with:
                - callout_mapping: {callout_number: part_code}
                - descriptions: {part_code: description}

        Returns:
            List of PartCode objects
        """
        callout_mapping = vision_response.get("callout_mapping", {})
        descriptions = vision_response.get("descriptions", {})

        part_codes = []
        for callout, code in callout_mapping.items():
            part_codes.append(PartCode(
                code=code,
                description=descriptions.get(code, ""),
                source_page=page_no,
                confidence=0.75  # Lower confidence for vision extraction
            ))

        return part_codes

    def _extract_context(self, text: str, code: str, window: int = 100) -> str:
        """Extract text context around part code."""
        idx = text.find(code)
        if idx == -1:
            return ""

        start = max(0, idx - window)
        end = min(len(text), idx + len(code) + window)
        return text[start:end]

    async def _extract_description(self, code: str, context: str) -> str:
        """Use LLM to extract description from context."""
        if not context:
            return ""

        prompt = f"""Extract the part description for this part code from the context.

Part Code: {code}
Context: {context}

Return ONLY the description (1-2 sentences max), or "Unknown" if not found."""

        response = await self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )

        return response["content"].strip()

    def _find_column(self, headers: List[str], candidates: List[str]) -> int:
        """Find column index by matching header candidates."""
        for idx, header in enumerate(headers):
            for candidate in candidates:
                if candidate in header:
                    return idx
        return 0  # Default to first column
```

### 4.2 Vehicle Model Mapper Service

**File:** `backend/app/services/gt_motive/vehicle_model_mapper.py`

**Purpose:** Map part codes to vehicle models

```python
from typing import List, Dict, Any
from pydantic import BaseModel

class VehicleCompatibility(BaseModel):
    """Vehicle compatibility for a part."""
    part_code: str
    make: str  # BMW, Mercedes, Audi
    model: str  # 3-series, C-Class, A4
    year_from: int
    year_to: int
    engine: str | None = None  # "2.0L Turbo"
    trim: str | None = None  # "Sport", "Luxury"

class VehicleModelMapper:
    """Map part codes to compatible vehicle models."""

    def __init__(self, llm_service):
        self.llm = llm_service

    async def map_part_to_vehicles(
        self,
        part_code: str,
        description: str,
        context: str = ""
    ) -> List[VehicleCompatibility]:
        """
        Extract vehicle compatibility from part description/context.

        Example description: "Front Bumper Cover for BMW 3-Series (F30) 2012-2018"

        Returns:
            List of VehicleCompatibility objects
        """
        prompt = f"""Extract vehicle compatibility information for this automotive part.

Part Code: {part_code}
Description: {description}
Additional Context: {context}

Extract:
- Make (BMW, Mercedes, Audi, etc.)
- Model (3-Series, C-Class, A4, etc.)
- Year range (from - to)
- Engine type (optional)
- Trim level (optional)

Return JSON array:
[
  {{
    "make": "BMW",
    "model": "3-Series",
    "year_from": 2012,
    "year_to": 2018,
    "engine": "2.0L Turbo",
    "trim": "Sport"
  }},
  ...
]

If no vehicle information found, return empty array []."""

        response = await self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"}
        )

        import json
        vehicles_data = json.loads(response["content"])

        if not isinstance(vehicles_data, list):
            vehicles_data = vehicles_data.get("vehicles", [])

        # Convert to VehicleCompatibility objects
        compatibilities = []
        for vehicle in vehicles_data:
            compatibilities.append(VehicleCompatibility(
                part_code=part_code,
                make=vehicle.get("make", "Unknown"),
                model=vehicle.get("model", "Unknown"),
                year_from=vehicle.get("year_from", 0),
                year_to=vehicle.get("year_to", 9999),
                engine=vehicle.get("engine"),
                trim=vehicle.get("trim")
            ))

        return compatibilities
```

### 4.3 Diagram Analyzer Service

**File:** `backend/app/services/gt_motive/diagram_analyzer.py`

**Purpose:** Analyze technical diagrams using Claude Vision

```python
from app.services.vision_service import VisionService
from typing import Dict, Any
import json

class DiagramAnalyzer:
    """Analyze technical diagrams with callout numbers using vision models."""

    def __init__(self):
        self.vision = VisionService()

    async def analyze_exploded_diagram(
        self,
        image_path: str
    ) -> Dict[str, Any]:
        """
        Analyze exploded diagram and extract callout-to-part-code mapping.

        Expected diagram format:
        - Numbered callouts (1, 2, 3, ..., 45)
        - Legend/table with callout number → part code mapping

        Returns:
            {
                "callout_mapping": {
                    "1": "BMW-51117140850",
                    "2": "BMW-63117240037",
                    ...
                },
                "descriptions": {
                    "BMW-51117140850": "Front Bumper Cover",
                    ...
                }
            }
        """
        prompt = """You are analyzing an automotive technical diagram (exploded view).

Extract:
1. Callout numbers visible in the diagram (e.g., 1, 2, 3, ..., 45)
2. Part code mapping from the legend/table (callout number → part code)
3. Part descriptions

Return JSON:
{
  "callout_mapping": {
    "1": "part_code_here",
    "2": "another_part_code",
    ...
  },
  "descriptions": {
    "part_code_here": "description here",
    ...
  }
}

If no legend/table found, return empty mappings."""

        response = await self.vision.analyze_image(
            image_path=image_path,
            prompt=prompt
        )

        # Parse JSON response
        try:
            result = json.loads(response["content"])
        except json.JSONDecodeError:
            result = {
                "callout_mapping": {},
                "descriptions": {}
            }

        return result
```

---

## 5. Data Flow

### 5.1 Text-Based Catalog Processing

```
PDF UPLOAD
  ↓
DOCLING EXTRACTION
  ├─ Text content
  └─ Tables (part codes, descriptions, prices)
  ↓
PART CODE EXTRACTION
  ├─ Regex matching (brand-specific patterns)
  └─ LLM description extraction
  ↓
VEHICLE MODEL MAPPING
  └─ Extract vehicle compatibility from descriptions
  ↓
DUAL INDEXING
  ├─ Elasticsearch: Part codes (keyword search)
  └─ ChromaDB: Descriptions (semantic search)
  ↓
EXCEL EXPORT
  └─ Structured catalog with all extracted data
```

### 5.2 Diagram Processing

```
IMAGE UPLOAD (exploded diagram)
  ↓
VISION MODEL ANALYSIS
  ├─ Claude Vision identifies callouts (1, 2, 3, ...)
  ├─ Extracts legend/table (callout → part code)
  └─ Part descriptions
  ↓
PART CODE EXTRACTION
  └─ Map callouts to part codes
  ↓
DATABASE STORAGE
  └─ Store with diagram reference
```

### 5.3 Query Flow (Hybrid Search)

```
USER QUERY: "Find BMW 3-series front bumper part codes"
  ↓
QUERY CLASSIFICATION (Infrastructure)
  └─ HYBRID (has specific terms "BMW 3-series" + semantic "front bumper")
  ↓
PARALLEL RETRIEVAL
  ├─ Elasticsearch: Keyword match "BMW 3-series"
  └─ ChromaDB: Semantic search "front bumper"
  ↓
RANK FUSION (RRF)
  └─ Combine results
  ↓
RE-RANKING (BAAI)
  └─ Top 10 most relevant part codes
  ↓
RESPONSE
  └─ Part codes + descriptions + vehicle compatibility
```

---

## 6. API Endpoints

### 6.1 Upload Part Catalog

```http
POST /api/v1/gt-motive/catalogs/upload
Content-Type: multipart/form-data

{
  "file": <catalog.pdf>,
  "brand": "bmw",
  "catalog_type": "parts_catalog"  # or "service_manual", "diagram"
}

Response:
{
  "catalog_id": "uuid-here",
  "status": "processing",
  "estimated_parts": 0
}
```

### 6.2 Extract Part Codes

```http
POST /api/v1/gt-motive/catalogs/{catalog_id}/extract

Response:
{
  "catalog_id": "uuid-here",
  "total_parts": 245,
  "parts": [
    {
      "code": "BMW-51117140850",
      "description": "Front Bumper Cover (F30)",
      "price": 450.00,
      "vehicles": [
        {
          "make": "BMW",
          "model": "3-Series",
          "year_from": 2012,
          "year_to": 2018
        }
      ],
      "confidence": 0.95
    },
    ...
  ]
}
```

### 6.3 Query Part Codes

```http
POST /api/v1/gt-motive/parts/query
Content-Type: application/json

{
  "query": "BMW 3-series front suspension",
  "filters": {
    "make": "BMW",
    "model": "3-Series"
  },
  "top_k": 10
}

Response:
{
  "parts": [
    {
      "code": "BMW-31126796929",
      "description": "Front Suspension Control Arm",
      "price": 280.00,
      "match_score": 0.92
    },
    ...
  ],
  "pipeline_used": "hybrid"
}
```

### 6.4 Download Excel Catalog

```http
GET /api/v1/gt-motive/catalogs/{catalog_id}/download

Response: Excel file
- Sheet 1: Part Codes (code, description, price)
- Sheet 2: Vehicle Compatibility (code, make, model, year)
- Sheet 3: Summary (total parts, brands, models)
```

---

## 7. Database Schema

```sql
-- GT Motive part catalogs
CREATE TABLE gt_motive_catalogs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    catalog_name TEXT NOT NULL,
    brand TEXT,  -- bmw, mercedes, audi
    catalog_type TEXT,  -- parts_catalog, service_manual, diagram
    file_path TEXT,  -- MinIO path
    total_parts INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Extracted part codes
CREATE TABLE gt_motive_parts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    catalog_id UUID REFERENCES gt_motive_catalogs(id),
    part_code TEXT NOT NULL,
    description TEXT,
    price DECIMAL(10,2),
    source_page INT,
    confidence FLOAT,
    indexed_in_chromadb BOOLEAN DEFAULT FALSE,
    indexed_in_elasticsearch BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Vehicle compatibility
CREATE TABLE gt_motive_vehicle_compatibility (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    part_id UUID REFERENCES gt_motive_parts(id),
    make TEXT,
    model TEXT,
    year_from INT,
    year_to INT,
    engine TEXT,
    trim TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_parts_code ON gt_motive_parts(part_code);
CREATE INDEX idx_parts_catalog ON gt_motive_parts(catalog_id);
CREATE INDEX idx_compat_part ON gt_motive_vehicle_compatibility(part_id);
CREATE INDEX idx_compat_vehicle ON gt_motive_vehicle_compatibility(make, model);
```

---

## 8. Frontend UI

### 8.1 Catalog Upload Component

**File:** `frontend/src/components/GTMotiveCatalogUpload.tsx`

```typescript
export const GTMotiveCatalogUpload: React.FC = () => {
  const [brand, setBrand] = useState<'bmw' | 'mercedes' | 'audi' | 'generic'>('bmw');
  const [catalogType, setCatalogType] = useState<'parts_catalog' | 'diagram'>('parts_catalog');

  return (
    <div className="space-y-4">
      <select value={brand} onChange={(e) => setBrand(e.target.value)}>
        <option value="bmw">BMW</option>
        <option value="mercedes">Mercedes-Benz</option>
        <option value="audi">Audi</option>
        <option value="generic">Generic</option>
      </select>

      <select value={catalogType} onChange={(e) => setCatalogType(e.target.value)}>
        <option value="parts_catalog">Parts Catalog (PDF)</option>
        <option value="diagram">Technical Diagram (Image)</option>
      </select>

      <FileUpload
        accept=".pdf,.jpg,.png"
        onUpload={(file) => handleUpload(file, brand, catalogType)}
      />
    </div>
  );
};
```

### 8.2 Part Browser

**File:** `frontend/src/components/GTMotivePartBrowser.tsx`

```typescript
export const PartBrowser: React.FC = () => {
  const [parts, setParts] = useState<Part[]>([]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {parts.map((part) => (
        <PartCard
          key={part.code}
          code={part.code}
          description={part.description}
          price={part.price}
          vehicles={part.vehicles}
          confidence={part.confidence}
        />
      ))}
    </div>
  );
};
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

```python
# tests/services/gt_motive/test_part_code_extractor.py
async def test_extract_bmw_codes():
    extractor = PartCodeExtractor(llm_service)

    text = "Front Bumper Cover 51117140850 fits BMW 3-Series"
    codes = await extractor.extract_from_text(text, brand="bmw")

    assert len(codes) == 1
    assert codes[0].code == "51117140850"
```

### 9.2 Integration Tests

```python
# tests/integration/gt_motive/test_catalog_extraction.py
async def test_full_catalog_extraction(client):
    # Upload catalog
    response = client.post("/api/v1/gt-motive/catalogs/upload", files={...})
    catalog_id = response.json()["catalog_id"]

    # Extract parts
    response = client.post(f"/api/v1/gt-motive/catalogs/{catalog_id}/extract")
    parts = response.json()["parts"]

    assert len(parts) > 0
    assert all(p["confidence"] > 0.5 for p in parts)
```

---

## 10. Deployment

### 10.1 Environment Variables

```bash
# GT Motive Configuration
GT_MOTIVE_ENABLE_VISION=true
GT_MOTIVE_VISION_MODEL=claude-3-5-sonnet
GT_MOTIVE_ENABLE_HYBRID_SEARCH=true
```

### 10.2 MinIO Paths

```
merit/automotive/gt-motive/
├── bmw/
│   ├── catalogs/
│   └── diagrams/
├── mercedes/
├── audi/
└── generic/
```

---

## 11. Timeline

### Week 1-2: Core Extraction (Jan 2-15, 2026)
- Part code extractor (regex + LLM)
- Table extraction integration
- Vehicle model mapper

### Week 3: Multi-Modal (Jan 16-22, 2026)
- Diagram analyzer with Claude Vision
- Image upload support
- Hybrid search integration

### Week 4: Testing & Polish (Jan 23-29, 2026)
- Unit + integration tests
- Excel export
- Frontend UI
- Documentation

**Total: 4 weeks**

---

## 12. Success Criteria

- [ ] Extract part codes from PDF catalogs (>95% accuracy)
- [ ] Extract part codes from diagrams using vision model (>75% accuracy)
- [ ] Map part codes to vehicle models (>90% for text-based)
- [ ] Hybrid search (ChromaDB + Elasticsearch) working
- [ ] Excel export with complete catalog
- [ ] Response time <5 seconds

---

**Status:** Ready for implementation
**Dependencies:** Infrastructure (Elasticsearch, Re-ranker), Claude Vision API
**Reuse:** 60% from core platform + infrastructure
