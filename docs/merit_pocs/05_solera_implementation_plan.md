# Solera POC - Implementation Plan

> **Customer:** Solera (Insurance & Auto Claims)
> **Use Case:** OCR + Part Code Extraction from Claims Photos
> **Priority:** Tier 2 (Medium - 65% code reuse, OCR + keyword search focus)
> **Estimated Effort:** 2-3 weeks
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
- **Photo OCR**: Extract text from insurance claim photos (damaged vehicles)
- **Part Code Detection**: Identify automotive part codes from damaged parts
- **VIN Extraction**: Extract Vehicle Identification Numbers (VIN) from photos
- **Damage Assessment**: Classify damage severity (minor, moderate, severe)
- **Claims Report Generation**: Auto-generate claims reports with extracted data

### 1.2 Document/Image Types
- **Claim Photos**: Damaged vehicles, parts close-ups
- **Insurance Forms**: PDF forms with handwritten or typed text
- **Invoices/Receipts**: Repair shop invoices with part codes
- **VIN Plates**: Photos of VIN plates on vehicles

### 1.3 Key Use Cases

**Use Case 1: Damaged Part Detection**
```
Input: Photo of damaged front bumper
Output:
- Part identified: "Front Bumper Cover"
- Possible part codes: ["BMW-51117140850", "OEM-equivalent"]
- Damage severity: "Moderate"
- Estimated cost: €450
```

**Use Case 2: VIN Extraction**
```
Input: Photo of VIN plate
Output:
- VIN: "WBA3B1C50EP123456"
- Make: BMW
- Model: 3-Series
- Year: 2014
```

**Use Case 3: Invoice Processing**
```
Input: Scanned repair shop invoice
Output:
- Part codes: ["BMW-51117140850", "BMW-63117240037"]
- Labor cost: €200
- Parts cost: €650
- Total: €850
```

### 1.4 Success Metrics
- OCR accuracy: >90% for clear photos
- VIN extraction: >95% accuracy
- Part code detection: >85% accuracy
- Damage classification: >80% accuracy
- Response time: <3 seconds per image

---

## 2. Technical Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SOLERA POC STACK                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           IMAGE UPLOAD (Claims Photos)                   │  │
│  │  - Damaged vehicle photos                                │  │
│  │  - VIN plate photos                                      │  │
│  │  - Insurance forms (PDF/image)                           │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           MULTI-OCR PIPELINE                             │  │
│  │                                                            │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │ Tesseract    │  │ PaddleOCR    │  │ EasyOCR      │   │  │
│  │  │ (fallback)   │  │ (primary)    │  │ (backup)     │   │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │  │
│  │         └──────────────────┴─────────────────┘           │  │
│  │                            │                               │  │
│  │                  ┌─────────▼──────────┐                   │  │
│  │                  │ OCR Result Fusion  │                   │  │
│  │                  │ (confidence-based) │                   │  │
│  │                  └─────────┬──────────┘                   │  │
│  └────────────────────────────┼───────────────────────────────┘  │
│                               │                                   │
│                               ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           TEXT PROCESSING ENGINE                         │  │
│  │                                                            │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌─────────────┐│  │
│  │  │ VIN Extractor  │  │ Part Code      │  │ Damage      ││  │
│  │  │ (regex)        │  │ Extractor      │  │ Classifier  ││  │
│  │  └────────┬───────┘  └────────┬───────┘  └─────┬───────┘│  │
│  │           │                   │                 │         │  │
│  └───────────┼───────────────────┼─────────────────┼─────────┘  │
│              │                   │                 │             │
│              ▼                   ▼                 ▼             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          ELASTICSEARCH SEARCH (Infrastructure)           │  │
│  │  - VIN database lookup                                   │  │
│  │  - Part code catalog search                              │  │
│  │  - Keyword-based filtering                               │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          LLM SYNTHESIS (GPT-4o-mini)                     │  │
│  │  - Damage assessment summary                             │  │
│  │  - Claims report generation                              │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          CLAIMS REPORT EXPORT                            │  │
│  │  - PDF report with extracted data                        │  │
│  │  - Excel damage catalog                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **OCR Primary** | PaddleOCR | Best for vehicle/part photos, multi-language |
| **OCR Backup** | Tesseract + EasyOCR (existing) | Fallback for low-quality images |
| **VIN Validation** | NHTSA API (external) | Validate VINs against official database |
| **Keyword Search** | Elasticsearch (infrastructure) | Part code exact match |
| **LLM** | GPT-4o-mini | Damage assessment + report generation |
| **Image Preprocessing** | OpenCV (existing) | Enhance image quality before OCR |
| **Backend** | FastAPI + Pydantic | Existing stack |
| **Storage** | MinIO + PostgreSQL | Existing infrastructure |

---

## 3. Reusable Components

### 3.1 From Core Platform (65% Reuse)

| Component | Source | Reuse % | Usage in Solera |
|-----------|--------|---------|----------------|
| **OCR Service** | `app/services/ocr_service.py` | 100% | OCR for claim photos |
| **OpenCV Service** | `app/services/opencv_measurement_service.py` | 80% | Image preprocessing |
| **Document Service** | `app/services/document_service.py` | 70% | Upload images to MinIO |
| **LLM Service** | `app/services/llm_service.py` | 100% | Damage assessment synthesis |

### 3.2 From Infrastructure

| Component | Source | Usage |
|-----------|--------|-------|
| **Elasticsearch Service** | `infrastructure/elasticsearch_service.py` | VIN + part code lookup |
| **Re-ranker Service** | `infrastructure/reranker_service.py` | Improve part code search precision |

### 3.3 From GT Motive

| Component | Source | Adaptation |
|-----------|--------|-----------|
| **Part Code Extractor** | `gt_motive/part_code_extractor.py` | Extract part codes from OCR text |
| **Excel Export** | Grant Thornton's excel exporter | Export claims data to Excel |

---

## 4. New Components

### 4.1 Multi-OCR Service (Enhanced)

**File:** `backend/app/services/solera/multi_ocr_service.py`

**Purpose:** Run multiple OCR engines and fuse results

```python
from app.services.ocr_service import OCRService
from typing import List, Dict, Any
import asyncio

class MultiOCRService:
    """Run multiple OCR engines in parallel and fuse results."""

    def __init__(self):
        self.ocr = OCRService()

    async def extract_text_multi_engine(
        self,
        image_path: str
    ) -> Dict[str, Any]:
        """
        Run Tesseract, PaddleOCR, and EasyOCR in parallel.

        Returns best result based on confidence scores.

        Returns:
            {
                "text": str,
                "confidence": float,
                "engine": str,  # tesseract, paddle, easyocr
                "all_results": List[dict]
            }
        """
        # Run all OCR engines in parallel
        tasks = [
            self._run_tesseract(image_path),
            self._run_paddleocr(image_path),
            self._run_easyocr(image_path)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = [
            r for r in results
            if not isinstance(r, Exception) and r.get("confidence", 0) > 0.5
        ]

        if not valid_results:
            return {
                "text": "",
                "confidence": 0.0,
                "engine": "none",
                "all_results": []
            }

        # Choose best result by confidence
        best_result = max(valid_results, key=lambda x: x["confidence"])

        return {
            "text": best_result["text"],
            "confidence": best_result["confidence"],
            "engine": best_result["engine"],
            "all_results": valid_results
        }

    async def _run_tesseract(self, image_path: str) -> Dict[str, Any]:
        """Run Tesseract OCR."""
        result = await self.ocr.extract_text(image_path, engine="tesseract")
        return {
            "text": result["text"],
            "confidence": result.get("confidence", 0.7),
            "engine": "tesseract"
        }

    async def _run_paddleocr(self, image_path: str) -> Dict[str, Any]:
        """Run PaddleOCR (best for vehicle photos)."""
        result = await self.ocr.extract_text(image_path, engine="paddle")
        return {
            "text": result["text"],
            "confidence": result.get("confidence", 0.8),
            "engine": "paddle"
        }

    async def _run_easyocr(self, image_path: str) -> Dict[str, Any]:
        """Run EasyOCR."""
        result = await self.ocr.extract_text(image_path, engine="easyocr")
        return {
            "text": result["text"],
            "confidence": result.get("confidence", 0.75),
            "engine": "easyocr"
        }
```

### 4.2 VIN Extractor Service

**File:** `backend/app/services/solera/vin_extractor.py`

**Purpose:** Extract and validate VINs

```python
import re
from typing import Dict, Any, Optional
import httpx

class VINExtractor:
    """Extract and validate Vehicle Identification Numbers (VIN)."""

    VIN_PATTERN = r"\b[A-HJ-NPR-Z0-9]{17}\b"  # Standard 17-character VIN

    def __init__(self):
        self.nhtsa_api_url = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/"

    async def extract_vin(self, text: str) -> Optional[str]:
        """
        Extract VIN from OCR text using regex.

        VIN format: 17 alphanumeric characters (no I, O, Q to avoid confusion)

        Args:
            text: OCR text

        Returns:
            VIN string or None
        """
        matches = re.findall(self.VIN_PATTERN, text)

        if not matches:
            return None

        # Return first match (most likely to be VIN)
        return matches[0]

    async def validate_vin(self, vin: str) -> Dict[str, Any]:
        """
        Validate VIN using NHTSA API.

        Returns vehicle details if valid.

        Returns:
            {
                "valid": bool,
                "make": str,
                "model": str,
                "year": int,
                "body_type": str,
                "engine": str
            }
        """
        if len(vin) != 17:
            return {"valid": False, "error": "Invalid VIN length"}

        # Call NHTSA API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.nhtsa_api_url}{vin}?format=json",
                timeout=5.0
            )

        if response.status_code != 200:
            return {"valid": False, "error": "NHTSA API error"}

        data = response.json()
        results = data.get("Results", [])

        # Parse results
        vehicle_info = {}
        for item in results:
            variable = item.get("Variable", "")
            value = item.get("Value", "")

            if variable == "Make":
                vehicle_info["make"] = value
            elif variable == "Model":
                vehicle_info["model"] = value
            elif variable == "Model Year":
                vehicle_info["year"] = int(value) if value else None
            elif variable == "Body Class":
                vehicle_info["body_type"] = value
            elif variable == "Engine Number of Cylinders":
                vehicle_info["engine"] = value

        if not vehicle_info.get("make"):
            return {"valid": False, "error": "VIN not found in database"}

        return {
            "valid": True,
            **vehicle_info
        }
```

### 4.3 Damage Classifier Service

**File:** `backend/app/services/solera/damage_classifier.py`

**Purpose:** Classify damage severity using LLM

```python
from typing import Dict, Any
from enum import Enum
import json

class DamageSeverity(str, Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    TOTAL_LOSS = "total_loss"

class DamageClassifier:
    """Classify vehicle damage severity using LLM."""

    def __init__(self, llm_service):
        self.llm = llm_service

    async def classify_damage(
        self,
        ocr_text: str,
        image_description: str = ""
    ) -> Dict[str, Any]:
        """
        Classify damage severity from OCR text and image description.

        Args:
            ocr_text: Text extracted from claim photo
            image_description: Optional description from vision model

        Returns:
            {
                "severity": DamageSeverity,
                "damaged_parts": List[str],
                "estimated_cost": float,
                "repair_required": bool,
                "explanation": str
            }
        """
        prompt = f"""You are an auto insurance damage assessor.

Analyze this claim and classify the damage severity.

OCR Text: {ocr_text}
Image Description: {image_description}

Classify into:
- MINOR: Cosmetic damage, no structural damage (€0-€500)
- MODERATE: Significant damage, parts replacement needed (€500-€2000)
- SEVERE: Major damage, structural damage (€2000-€10000)
- TOTAL_LOSS: Vehicle not economically repairable (>€10000)

Return JSON:
{{
  "severity": "minor|moderate|severe|total_loss",
  "damaged_parts": ["part1", "part2", ...],
  "estimated_cost": 1234.56,
  "repair_required": true,
  "explanation": "Brief explanation of assessment"
}}"""

        response = await self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"}
        )

        result = json.loads(response["content"])

        return {
            "severity": DamageSeverity(result.get("severity", "moderate")),
            "damaged_parts": result.get("damaged_parts", []),
            "estimated_cost": result.get("estimated_cost", 0.0),
            "repair_required": result.get("repair_required", True),
            "explanation": result.get("explanation", "")
        }
```

### 4.4 Claims Report Generator

**File:** `backend/app/services/solera/claims_report_generator.py`

**Purpose:** Generate PDF claims reports

```python
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from typing import Dict, Any, List
from datetime import datetime

class ClaimsReportGenerator:
    """Generate PDF claims reports."""

    def generate_report(
        self,
        claim_data: Dict[str, Any],
        output_path: str
    ):
        """
        Generate claims report PDF.

        Args:
            claim_data:
                {
                    "claim_id": str,
                    "vin": str,
                    "vehicle": {"make": str, "model": str, "year": int},
                    "damage": {"severity": str, "parts": List[str], "cost": float},
                    "parts_extracted": List[dict],
                    "ocr_confidence": float
                }
            output_path: Path to save PDF
        """
        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter

        # Title
        c.setFont("Helvetica-Bold", 20)
        c.drawString(1*inch, height - 1*inch, "Auto Insurance Claim Report")

        # Claim ID
        c.setFont("Helvetica", 12)
        c.drawString(1*inch, height - 1.5*inch, f"Claim ID: {claim_data['claim_id']}")
        c.drawString(1*inch, height - 1.7*inch, f"Date: {datetime.now().strftime('%Y-%m-%d')}")

        # Vehicle Information
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1*inch, height - 2.2*inch, "Vehicle Information")

        c.setFont("Helvetica", 12)
        vehicle = claim_data["vehicle"]
        c.drawString(1*inch, height - 2.5*inch, f"VIN: {claim_data['vin']}")
        c.drawString(1*inch, height - 2.7*inch, f"Make: {vehicle['make']}")
        c.drawString(1*inch, height - 2.9*inch, f"Model: {vehicle['model']}")
        c.drawString(1*inch, height - 3.1*inch, f"Year: {vehicle['year']}")

        # Damage Assessment
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1*inch, height - 3.6*inch, "Damage Assessment")

        c.setFont("Helvetica", 12)
        damage = claim_data["damage"]
        c.drawString(1*inch, height - 3.9*inch, f"Severity: {damage['severity'].upper()}")
        c.drawString(1*inch, height - 4.1*inch, f"Estimated Cost: €{damage['cost']:.2f}")

        # Damaged Parts
        c.drawString(1*inch, height - 4.4*inch, "Damaged Parts:")
        y_pos = height - 4.6*inch
        for part in damage["parts"]:
            c.drawString(1.2*inch, y_pos, f"• {part}")
            y_pos -= 0.2*inch

        # Footer
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(1*inch, 0.5*inch, f"OCR Confidence: {claim_data['ocr_confidence']:.1%}")

        c.save()
```

---

## 5. Data Flow

### 5.1 Claim Photo Processing

```
PHOTO UPLOAD (damaged vehicle)
  ↓
IMAGE PREPROCESSING (OpenCV)
  ├─ Resize, enhance contrast
  └─ Denoise, sharpen
  ↓
MULTI-OCR EXTRACTION
  ├─ PaddleOCR (primary)
  ├─ Tesseract (backup)
  └─ EasyOCR (backup)
  ↓
OCR RESULT FUSION
  └─ Choose best result by confidence
  ↓
TEXT ANALYSIS (PARALLEL)
  ├─ VIN Extraction + Validation (NHTSA API)
  ├─ Part Code Extraction (regex + GT Motive)
  └─ Damage Classification (LLM)
  ↓
ELASTICSEARCH LOOKUP
  ├─ VIN → Vehicle details
  └─ Part codes → Catalog prices
  ↓
CLAIMS REPORT GENERATION
  └─ PDF with all extracted data
```

---

## 6. API Endpoints

### 6.1 Upload Claim Photo

```http
POST /api/v1/solera/claims/upload
Content-Type: multipart/form-data

{
  "photo": <claim_photo.jpg>,
  "claim_id": "CLM-2024-001"
}

Response:
{
  "claim_id": "CLM-2024-001",
  "status": "processing"
}
```

### 6.2 Extract Claim Data

```http
POST /api/v1/solera/claims/{claim_id}/extract

Response:
{
  "claim_id": "CLM-2024-001",
  "vin": "WBA3B1C50EP123456",
  "vehicle": {
    "make": "BMW",
    "model": "3-Series",
    "year": 2014
  },
  "damage": {
    "severity": "moderate",
    "damaged_parts": ["Front Bumper Cover", "Headlight Left"],
    "estimated_cost": 1200.00,
    "explanation": "Moderate front-end damage requiring parts replacement"
  },
  "parts_extracted": [
    {
      "code": "BMW-51117140850",
      "description": "Front Bumper Cover",
      "price": 450.00
    }
  ],
  "ocr_confidence": 0.87
}
```

### 6.3 Download Claims Report

```http
GET /api/v1/solera/claims/{claim_id}/report

Response: PDF file
```

---

## 7. Database Schema

```sql
-- Solera insurance claims
CREATE TABLE solera_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id TEXT UNIQUE NOT NULL,
    vin TEXT,
    vehicle_make TEXT,
    vehicle_model TEXT,
    vehicle_year INT,
    damage_severity TEXT,
    estimated_cost DECIMAL(10,2),
    image_path TEXT,
    ocr_confidence FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Extracted parts from claims
CREATE TABLE solera_claim_parts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID REFERENCES solera_claims(id),
    part_code TEXT,
    description TEXT,
    price DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_claims_vin ON solera_claims(vin);
CREATE INDEX idx_claims_date ON solera_claims(created_at);
```

---

## 8. Frontend UI

**File:** `frontend/src/components/SoleraClaimsUpload.tsx`

```typescript
export const SoleraClaimsUpload: React.FC = () => {
  const [claimId, setClaimId] = useState('');
  const [result, setResult] = useState<ClaimResult | null>(null);

  return (
    <div>
      <input
        type="text"
        placeholder="Claim ID (e.g., CLM-2024-001)"
        value={claimId}
        onChange={(e) => setClaimId(e.target.value)}
      />

      <ImageUpload
        accept=".jpg,.png"
        onUpload={(file) => handleClaimUpload(file, claimId)}
      />

      {result && (
        <ClaimResultDisplay
          vin={result.vin}
          vehicle={result.vehicle}
          damage={result.damage}
          parts={result.parts_extracted}
        />
      )}
    </div>
  );
};
```

---

## 9. Testing Strategy

```python
# tests/services/solera/test_vin_extractor.py
async def test_vin_extraction():
    extractor = VINExtractor()

    text = "Vehicle VIN: WBA3B1C50EP123456"
    vin = await extractor.extract_vin(text)

    assert vin == "WBA3B1C50EP123456"
```

---

## 10. Deployment

### 10.1 Environment Variables

```bash
# Solera Configuration
SOLERA_ENABLE_PADDLEOCR=true
SOLERA_NHTSA_API_KEY=your-api-key
```

---

## 11. Timeline

### Week 1: OCR Enhancement (Jan 2-8, 2026)
- Multi-OCR service
- Image preprocessing

### Week 2: Extraction Logic (Jan 9-15, 2026)
- VIN extractor
- Part code extractor
- Damage classifier

### Week 3: Testing & Polish (Jan 16-22, 2026)
- Claims report generator
- Frontend UI
- Testing + deployment

**Total: 3 weeks**

---

**Status:** Ready for implementation
**Dependencies:** Infrastructure (Elasticsearch), OCR Service, GT Motive part extractor
**Reuse:** 65% from core platform
