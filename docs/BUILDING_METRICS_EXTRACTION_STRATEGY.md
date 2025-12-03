# Building Metrics Extraction from Construction Documents
## Extract: Levels, Floor Areas, and Key Metrics Using Vision LLM

**Date**: 2025-12-02
**Status**: ✅ **READY TO IMPLEMENT**
**Target Metrics**:
- Levels (Above Ground)
- Levels (Below Ground)
- Gross Floor Area (GFA)
- External Area

---

## 🎯 Goal

**Extract structured building metrics** from construction tender documents automatically:

```json
{
  "project_name": "96-98 Tenby Street, Mt Gravatt East",
  "project_code": "110140",
  "metrics": {
    "levels_above_ground": 4,
    "levels_below_ground": 1,
    "gross_floor_area_m2": 2850.5,
    "external_area_m2": 450.0,
    "site_area_m2": 1200.0,
    "building_height_m": 15.6
  },
  "confidence": 0.95,
  "sources": [
    "A0000 - DRAWING SCHEDULE.pdf",
    "DA Approval - Decision Notice.pdf",
    "220127 Zhu Tenby ARCH TENDER.pdf"
  ]
}
```

---

## 📋 Where These Metrics Appear

### 1. **Architectural Drawings** (PRIMARY SOURCE)

#### Drawing Schedule / Cover Sheet
**File**: `A0000 - DRAWING SCHEDULE.pdf`, `A1000 - SITE PLAN.pdf`

**Typical Content**:
```
PROJECT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Site Area:                1,200 m²
Gross Floor Area:         2,850.5 m²
External Area:            450 m²
Building Height:          15.6m (RL 23.50 to RL 39.10)
Number of Levels:         5 (Ground + 4)
Basement Levels:          1 (Car park)
```

#### Floor Plans
**Files**: `A1101 - GROUND FLOOR.pdf`, `A1102 - LEVEL 1.pdf`, etc.

**Level Count**: Inferred from drawing numbers
```
A1101 - GROUND FLOOR
A1102 - LEVEL 1
A1103 - LEVEL 2
A1104 - LEVEL 3
A1105 - LEVEL 4
A1106 - ROOF PLAN
A1000 - BASEMENT 1 (Below Ground)
```

#### Elevation Drawings
**Files**: `A3000 - ELEVATION SHEET 1.pdf`

**Height Markers**:
```
RL 39.10 (Top of parapet)
RL 35.50 (Level 4 FFL)
RL 32.50 (Level 3 FFL)
RL 29.50 (Level 2 FFL)
RL 26.50 (Level 1 FFL)
RL 23.50 (Ground FFL)
RL 20.50 (Basement FFL)

Height: 15.6m (from Ground to Top)
Basement Depth: 3.0m (below ground)
```

---

### 2. **DA (Development Application) Approval** (SECONDARY SOURCE)

#### Decision Notice
**File**: `Decision Notice - Approved by Delegation.pdf`

**Typical Content**:
```
APPROVED DEVELOPMENT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Use: Multiple Dwelling (Apartments)
Site Area: 1,200 m²
Gross Floor Area (GFA): 2,850 m²
Number of Dwellings: 12
Building Height: 15.6m (5 storeys)
Car Parking Spaces: 24 (including 6 basement)
```

#### Approved Plans Summary
**File**: `Approved Plans.pdf`

**Contains**: Stamped architectural drawings with approval annotations

---

### 3. **Specifications Documents** (SUPPORTING SOURCE)

#### Architectural Specification
**File**: `220114 SC Tenby ARCH SPEC Rev Tender.pdf`

**Section 1.0 - Project Description**:
```
1.1 GENERAL
Building comprises:
- Ground floor: Retail + Residential lobby
- Levels 1-4: Residential apartments (3 per floor)
- Basement 1: Car parking and services

1.2 AREAS
- Total GFA: 2,850.5 m² (calculated per BCA)
- External areas: 450 m² (balconies, terraces)
- Car park area: 420 m²
```

---

## 🤖 Our Tech Stack for Metric Extraction

### Approach: Vision LLM + Structured Prompting

**Why Vision LLM is Perfect**:
1. ✅ Reads drawing annotations (text + layout)
2. ✅ Understands context (knows "GFA" = Gross Floor Area)
3. ✅ Counts floor levels from elevation drawings
4. ✅ Extracts numbers with units (m², m, storeys)
5. ✅ Cross-validates across multiple documents

---

## 🔧 Implementation Strategy

### Phase 1: Targeted Vision LLM Prompts

#### **Prompt Template for Metrics Extraction**

```python
BUILDING_METRICS_PROMPT = """
Analyze this construction document and extract the following building metrics:

REQUIRED METRICS:
1. Levels (Above Ground): Count of floors/storeys above ground level (exclude basement)
2. Levels (Below Ground): Count of basement levels (if any, otherwise 0)
3. Gross Floor Area (GFA): Total floor area in square meters (m²)
4. External Area: Balconies, terraces, external covered areas in square meters (m²)

OPTIONAL METRICS (if visible):
5. Site Area: Total land area in square meters (m²)
6. Building Height: Maximum height in meters (m)
7. Number of Units/Dwellings: If residential
8. Car Parking Spaces: Total parking count

INSTRUCTIONS:
- Look for drawing schedules, project details sections, elevation drawings
- Look for text like "GFA:", "Gross Floor Area:", "Site Area:", "Building Height:"
- Count floor levels from floor plan names (Ground, Level 1, Level 2, etc.)
- Count elevation markers (RL heights) to determine floors
- If metric not found, return "Not found" for that field
- Include confidence score (0-1) for each metric

RETURN FORMAT (JSON):
{
  "levels_above_ground": <number or "Not found">,
  "levels_below_ground": <number or "Not found">,
  "gross_floor_area_m2": <number or "Not found">,
  "external_area_m2": <number or "Not found">,
  "site_area_m2": <number or "Not found">,
  "building_height_m": <number or "Not found">,
  "number_of_units": <number or "Not found">,
  "car_parking_spaces": <number or "Not found">,
  "confidence": <0-1>,
  "source_location": "<where in document these were found>"
}

Document page image: [IMAGE_HERE]
"""
```

---

### Phase 2: Multi-Document Aggregation

#### **Strategy**: Query multiple documents and merge results

```python
async def extract_building_metrics(project_id: str, session_id: str) -> Dict:
    """
    Extract building metrics from project documents

    Process:
    1. Identify key documents (drawing schedule, DA approval, specs)
    2. Run Vision LLM extraction on each
    3. Aggregate results with confidence weighting
    4. Return best estimates with sources
    """

    # Step 1: Find relevant documents
    target_documents = await find_metric_documents(project_id)
    # Returns: [
    #   "A0000 - DRAWING SCHEDULE.pdf",
    #   "Decision Notice - Approved.pdf",
    #   "ARCH SPEC.pdf"
    # ]

    # Step 2: Extract from each document
    results = []
    for doc in target_documents:
        # Process with Vision LLM
        extraction = await vision_llm_extract_metrics(
            document_path=doc.file_path,
            prompt=BUILDING_METRICS_PROMPT
        )
        results.append({
            "source": doc.filename,
            "metrics": extraction,
            "confidence": extraction.get("confidence", 0.5)
        })

    # Step 3: Aggregate results (highest confidence wins)
    final_metrics = aggregate_metrics(results)

    return {
        "project_id": project_id,
        "metrics": final_metrics,
        "extraction_date": datetime.now().isoformat(),
        "sources": [r["source"] for r in results],
        "raw_extractions": results  # For debugging
    }
```

---

### Phase 3: Smart Document Identification

#### **Auto-detect which documents contain metrics**

```python
async def find_metric_documents(project_id: str) -> List[Document]:
    """
    Identify documents likely to contain building metrics

    Priority order:
    1. Drawing schedule (A0000, A1000, cover sheet)
    2. DA approval / Decision notice
    3. Architectural specification
    4. Floor plans (to count levels)
    5. Elevation drawings (to measure height)
    """

    # Query database for project documents
    all_docs = await get_project_documents(project_id)

    priority_docs = []

    # Priority 1: Drawing schedules
    drawing_schedules = [
        doc for doc in all_docs
        if any(keyword in doc.filename.lower() for keyword in [
            "drawing schedule",
            "cover sheet",
            "a0000",
            "a1000",
            "site plan"
        ])
    ]
    priority_docs.extend(drawing_schedules)

    # Priority 2: DA approvals
    da_approvals = [
        doc for doc in all_docs
        if any(keyword in doc.filename.lower() for keyword in [
            "decision notice",
            "da approval",
            "approved plans",
            "development approval"
        ])
    ]
    priority_docs.extend(da_approvals)

    # Priority 3: Specifications
    specs = [
        doc for doc in all_docs
        if any(keyword in doc.filename.lower() for keyword in [
            "specification",
            "arch spec",
            "scope of works"
        ])
    ]
    priority_docs.extend(specs)

    # Priority 4: Floor plans (for level counting)
    floor_plans = [
        doc for doc in all_docs
        if any(keyword in doc.filename.lower() for keyword in [
            "floor plan",
            "level 1", "level 2", "level 3",
            "ground floor",
            "basement"
        ])
    ]
    # Take first 3-5 floor plans (representative sample)
    priority_docs.extend(floor_plans[:5])

    return priority_docs
```

---

### Phase 4: Confidence-Based Aggregation

#### **Merge extractions from multiple sources**

```python
def aggregate_metrics(extractions: List[Dict]) -> Dict:
    """
    Aggregate metrics from multiple documents

    Strategy:
    - For each metric, take the value with highest confidence
    - If multiple sources agree, boost confidence
    - Mark metrics with low confidence or conflicts
    """

    metrics = {}

    metric_fields = [
        "levels_above_ground",
        "levels_below_ground",
        "gross_floor_area_m2",
        "external_area_m2",
        "site_area_m2",
        "building_height_m"
    ]

    for field in metric_fields:
        # Collect all values for this metric
        values = []
        for extraction in extractions:
            value = extraction["metrics"].get(field)
            if value and value != "Not found":
                values.append({
                    "value": value,
                    "confidence": extraction["confidence"],
                    "source": extraction["source"]
                })

        if not values:
            metrics[field] = {
                "value": None,
                "confidence": 0.0,
                "status": "not_found",
                "sources": []
            }
            continue

        # Sort by confidence (highest first)
        values.sort(key=lambda x: x["confidence"], reverse=True)

        # Check for agreement (multiple sources with same value)
        best_value = values[0]["value"]
        agreeing_sources = [
            v for v in values
            if abs(v["value"] - best_value) < 0.01 * best_value  # Within 1%
        ]

        # Boost confidence if multiple sources agree
        if len(agreeing_sources) > 1:
            final_confidence = min(0.99, values[0]["confidence"] * 1.2)
            status = "confirmed"
        else:
            final_confidence = values[0]["confidence"]
            status = "single_source"

        metrics[field] = {
            "value": best_value,
            "confidence": final_confidence,
            "status": status,
            "sources": [v["source"] for v in agreeing_sources]
        }

        # Detect conflicts (different values with high confidence)
        if len(values) > 1:
            diff_values = [
                v for v in values[1:]
                if abs(v["value"] - best_value) > 0.05 * best_value  # >5% difference
            ]
            if diff_values and diff_values[0]["confidence"] > 0.7:
                metrics[field]["status"] = "conflict"
                metrics[field]["alternative_values"] = [
                    {"value": v["value"], "source": v["source"]}
                    for v in diff_values
                ]

    return metrics
```

---

## 📊 Example Output

### Input: 110140 - Tenby Street Project

**Documents Analyzed**:
1. `220127 Zhu Tenby ARCH TENDER.pdf`
2. `Decision Notice - Approved.pdf`
3. `220114 SC Tenby ARCH SPEC.pdf`

### Output JSON:

```json
{
  "project_id": "110140",
  "project_name": "96-98 Tenby Street, Mt Gravatt East",
  "extraction_date": "2025-12-02T19:45:00Z",
  "metrics": {
    "levels_above_ground": {
      "value": 4,
      "confidence": 0.95,
      "status": "confirmed",
      "sources": [
        "220127 Zhu Tenby ARCH TENDER.pdf",
        "Decision Notice - Approved.pdf"
      ]
    },
    "levels_below_ground": {
      "value": 1,
      "confidence": 0.92,
      "status": "confirmed",
      "sources": [
        "220127 Zhu Tenby ARCH TENDER.pdf"
      ]
    },
    "gross_floor_area_m2": {
      "value": 2850.5,
      "confidence": 0.98,
      "status": "confirmed",
      "sources": [
        "220127 Zhu Tenby ARCH TENDER.pdf",
        "Decision Notice - Approved.pdf",
        "220114 SC Tenby ARCH SPEC.pdf"
      ],
      "note": "All three sources agree"
    },
    "external_area_m2": {
      "value": 450.0,
      "confidence": 0.85,
      "status": "single_source",
      "sources": [
        "220114 SC Tenby ARCH SPEC.pdf"
      ]
    },
    "site_area_m2": {
      "value": 1200.0,
      "confidence": 0.95,
      "status": "confirmed",
      "sources": [
        "Decision Notice - Approved.pdf"
      ]
    },
    "building_height_m": {
      "value": 15.6,
      "confidence": 0.90,
      "status": "confirmed",
      "sources": [
        "220127 Zhu Tenby ARCH TENDER.pdf"
      ]
    }
  },
  "raw_extractions": [
    {
      "source": "220127 Zhu Tenby ARCH TENDER.pdf",
      "confidence": 0.95,
      "metrics": {
        "levels_above_ground": 4,
        "levels_below_ground": 1,
        "gross_floor_area_m2": 2850.5,
        "building_height_m": 15.6,
        "source_location": "Drawing schedule on page 1"
      }
    },
    {
      "source": "Decision Notice - Approved.pdf",
      "confidence": 0.92,
      "metrics": {
        "levels_above_ground": 4,
        "gross_floor_area_m2": 2850.0,
        "site_area_m2": 1200.0,
        "source_location": "Approved Development Details section"
      }
    },
    {
      "source": "220114 SC Tenby ARCH SPEC.pdf",
      "confidence": 0.85,
      "metrics": {
        "gross_floor_area_m2": 2850.5,
        "external_area_m2": 450.0,
        "source_location": "Section 1.2 - Areas"
      }
    }
  ]
}
```

---

## 🔧 API Implementation

### Endpoint 1: Extract Metrics from Single Document

```python
POST /api/v1/projects/{project_id}/extract-metrics/document

Body:
{
  "document_id": "uuid-of-drawing-schedule",
  "metrics_requested": [
    "levels_above_ground",
    "levels_below_ground",
    "gross_floor_area_m2",
    "external_area_m2"
  ]
}

Response:
{
  "document_id": "uuid",
  "filename": "A0000 - DRAWING SCHEDULE.pdf",
  "metrics": {
    "levels_above_ground": 4,
    "levels_below_ground": 1,
    "gross_floor_area_m2": 2850.5,
    "external_area_m2": 450.0
  },
  "confidence": 0.95,
  "processing_time_ms": 2340
}
```

### Endpoint 2: Extract Metrics from Entire Project

```python
POST /api/v1/projects/{project_id}/extract-metrics/project

Body:
{
  "project_id": "110140",
  "auto_detect_sources": true,
  "metrics_requested": [
    "levels_above_ground",
    "levels_below_ground",
    "gross_floor_area_m2",
    "external_area_m2",
    "site_area_m2",
    "building_height_m"
  ]
}

Response: (as shown in example above)
```

### Endpoint 3: Batch Extraction (All Projects)

```python
POST /api/v1/projects/extract-metrics/batch

Body:
{
  "project_ids": ["110140", "110126", "110150"],
  "metrics_requested": ["levels_above_ground", "gross_floor_area_m2"]
}

Response:
{
  "projects": [
    {
      "project_id": "110140",
      "metrics": { ... }
    },
    {
      "project_id": "110126",
      "metrics": { ... }
    }
  ],
  "summary": {
    "total_projects": 3,
    "successful": 3,
    "failed": 0,
    "total_processing_time_ms": 8340
  }
}
```

---

## 🎯 Frontend UI Integration

### Dashboard View

```
┌─────────────────────────────────────────────────────────────┐
│ PROJECT: 110140 - 96-98 Tenby Street, Mt Gravatt East      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  BUILDING METRICS                      📊 Auto-Extracted    │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  📐 LEVELS                                                   │
│  ├─ Above Ground:    4 storeys          ✓ 95% confidence   │
│  └─ Below Ground:    1 basement         ✓ 92% confidence   │
│                                                              │
│  📏 AREAS                                                    │
│  ├─ Gross Floor Area:    2,850.5 m²    ✓ 98% confidence   │
│  ├─ External Area:       450.0 m²      ✓ 85% confidence   │
│  ├─ Site Area:           1,200.0 m²    ✓ 95% confidence   │
│  └─ Building Height:     15.6 m         ✓ 90% confidence   │
│                                                              │
│  📄 SOURCES (3)                                             │
│  ├─ ✓ 220127 Zhu Tenby ARCH TENDER.pdf                     │
│  ├─ ✓ Decision Notice - Approved.pdf                       │
│  └─ ✓ 220114 SC Tenby ARCH SPEC.pdf                        │
│                                                              │
│  [View Details] [Re-extract] [Export CSV]                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Accuracy & Validation

### Expected Accuracy

| Metric | Accuracy | Notes |
|--------|----------|-------|
| **Levels Above Ground** | 95-98% | Easy to count from drawings |
| **Levels Below Ground** | 90-95% | Sometimes ambiguous (mezzanine?) |
| **Gross Floor Area** | 90-95% | Usually explicit in documents |
| **External Area** | 80-90% | Sometimes not documented |
| **Site Area** | 95-98% | Always in DA approval |
| **Building Height** | 85-95% | May need calculation from RLs |

### Validation Strategies

1. **Cross-Document Validation**: Compare values across multiple sources
2. **Sanity Checks**: Flag unrealistic values (e.g., 100-storey residential)
3. **Calculation Validation**: GFA should be ≈ levels × floor plate area
4. **User Review**: Mark low-confidence extractions for manual review

---

## 🚀 Implementation Timeline

### Phase 1: Core Extraction (4 hours)
- [x] CLIP embeddings working ✅
- [ ] Create metrics extraction prompt template (30 mins)
- [ ] Implement single-document extraction (1 hour)
- [ ] Test on 3-5 sample documents (1 hour)
- [ ] Validate extraction accuracy (30 mins)
- [ ] Implement confidence scoring (1 hour)

### Phase 2: Multi-Document Aggregation (3 hours)
- [ ] Implement smart document identification (1 hour)
- [ ] Build confidence-based aggregation (1 hour)
- [ ] Add conflict detection (30 mins)
- [ ] Test on full projects (30 mins)

### Phase 3: API & UI (3 hours)
- [ ] Create API endpoints (1 hour)
- [ ] Build frontend dashboard component (1.5 hours)
- [ ] Add export functionality (CSV, JSON) (30 mins)

**Total: 10 hours** from start to production-ready

---

## 💡 Key Benefits

### 1. **Automated Data Entry**
- ✅ No manual reading of 687 files per project
- ✅ Consistent extraction across all projects
- ✅ Immediate availability after document upload

### 2. **Confidence Scoring**
- ✅ Know which metrics are reliable
- ✅ Flag conflicts for manual review
- ✅ Track source documents for audit trail

### 3. **Batch Processing**
- ✅ Extract metrics from 29 projects in one API call
- ✅ Generate comparison reports
- ✅ Identify outliers (unusually tall/large buildings)

### 4. **Integration Ready**
- ✅ JSON output → Easy to integrate with estimating tools
- ✅ CSV export → Excel/Google Sheets
- ✅ API endpoints → External systems (ERPs, CRMs)

---

## 📝 Summary

### What We Have
✅ Vision LLM (llama3.2-vision:11b) - Reads and understands drawings
✅ Hybrid OCR - Extracts text from scanned documents
✅ CLIP embeddings - Finds relevant documents visually
✅ Text semantic search - Locates metric information

### What's Needed
🚧 Structured prompts for metric extraction (30 mins)
🚧 Multi-document aggregation logic (2 hours)
🚧 API endpoints (1 hour)
🚧 Frontend dashboard (1.5 hours)

### Expected Result
🎯 **Automated extraction** of building metrics from construction documents
🎯 **95%+ accuracy** on standard metrics (levels, GFA, site area)
🎯 **10x faster** than manual data entry
🎯 **Audit trail** with source documents and confidence scores

---

**Ready to implement? Start with Phase 1 (core extraction) and test on Tenby Street project!**

---

**END OF DOCUMENT**
