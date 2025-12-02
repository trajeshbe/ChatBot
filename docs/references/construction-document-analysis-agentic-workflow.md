# Agentic Workflow for Construction Document Analysis

## Use Case: Extracting Project Metrics from Complex Construction Documents

**Objective:** For each construction project, extract:
- Number of Floors Above Ground
- Number of Floors Below Ground  
- Gross Floor Area (GFA)
- External Area

**Data Source:** 29 Projects containing PDFs, images, architectural drawings, civil drawings, specifications, and reports

---

## High-Level Agentic Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              ORCHESTRATOR AGENT                                      │
│                    (Task Planning, Delegation, Aggregation)                         │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
            ┌────────────────────────────┼────────────────────────────┐
            ▼                            ▼                            ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   DISCOVERY AGENT   │    │   EXTRACTION AGENT  │    │  VALIDATION AGENT   │
│  (File Cataloging)  │    │  (Document Reading) │    │  (Cross-Reference)  │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
            │                            │                            │
            ▼                            ▼                            ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   FILE SYSTEM       │    │   VISION + PDF      │    │   RECONCILIATION    │
│   TOOLS             │    │   TOOLS             │    │   TOOLS             │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

---

## Phase 1: Task Understanding & Planning

### What the Orchestrator Agent Does First

When I (as Claude Code) receive this task, my first action is to **understand the scope and create an execution plan**.

```
┌─────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR THINKING                        │
├─────────────────────────────────────────────────────────────────┤
│ 1. Parse the user's requirements                                │
│    - Target metrics: floors above/below, GFA, external area     │
│    - Data location: ABC folder with 29 projects                 │
│    - Document types: PDFs, images, architectural drawings       │
│                                                                  │
│ 2. Identify key challenges                                       │
│    - Multi-modal: text PDFs + image-based drawings              │
│    - Information scattered across multiple document types        │
│    - Need to correlate data from different sources              │
│                                                                  │
│ 3. Create execution strategy                                     │
│    - Phase 1: Discover and catalog all files                    │
│    - Phase 2: Identify priority documents per project           │
│    - Phase 3: Extract data using appropriate tools              │
│    - Phase 4: Cross-validate and reconcile                      │
│    - Phase 5: Generate final report                             │
└─────────────────────────────────────────────────────────────────┘
```

### Initial Tool Calls

```python
# Step 1: List all projects and their structure
tool: bash
command: "find /data/ABC -type d -maxdepth 1 | head -50"

# Step 2: For each project, catalog file types
tool: bash  
command: "find /data/ABC/Project_1 -type f -name '*.pdf' -o -name '*.jpg' -o -name '*.png' | wc -l"

# Step 3: Identify document naming patterns
tool: bash
command: "ls -la /data/ABC/Project_1/ | grep -i 'arch\|civil\|struct\|floor\|site'"
```

---

## Phase 2: Document Priority Classification

### The Agent's Document Prioritization Logic

Based on the file list provided, here's how I would classify documents by their likelihood of containing target information:

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         DOCUMENT PRIORITY MATRIX                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  PRIORITY 1 - HIGH VALUE (Check First)                                              │
│  ════════════════════════════════════                                                │
│  • Architectural Floor Plans        → "_Architecturals Combined.pdf"                │
│  • Site Plans                       → "A1100 - SITE PLAN.pdf"                       │
│  • Floor Plan Documents             → "A1101 - PROPOSED FLOOR PLAN.pdf"             │
│  • Building Sections                → "A500_Building Sections.pdf"                  │
│  • DA Approval Documents            → "Decision Notice - Approved*.pdf"             │
│  • Project Summary/Scope            → "PPR Willawong*.pdf"                          │
│                                                                                      │
│  PRIORITY 2 - SUPPORTING (Cross-Reference)                                          │
│  ═════════════════════════════════════════                                           │
│  • Survey Plans                     → "_Survey Plan.pdf"                            │
│  • Civil Combined Drawings          → "_Civil Combined.pdf"                         │
│  • Structural Drawings              → "_Structural Combined.pdf"                    │
│  • Finishes Schedules               → "FINISHES SCHEDULE*.pdf"                      │
│  • Energy Reports                   → Contains GFA calculations                     │
│                                                                                      │
│  PRIORITY 3 - CONTEXTUAL (If needed)                                                │
│  ════════════════════════════════════                                                │
│  • Geotechnical Reports             → May mention basement depth                    │
│  • Hydraulic Drawings               → Floor-specific information                    │
│  • Electrical per-level drawings    → "E02 Ground Level", "E03 Level 1"            │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### File Selection Strategy Per Project

```python
def select_priority_documents(project_files: list) -> dict:
    """
    Agent's logic for selecting which documents to process first
    """
    priority_docs = {
        "floor_info": [],      # For floors above/below ground
        "area_info": [],       # For GFA and external area
        "validation": []       # For cross-referencing
    }
    
    # Pattern matching for floor information
    floor_patterns = [
        r"floor.plan",
        r"arch.*combined",
        r"building.section",
        r"elevation",
        r"site.plan"
    ]
    
    # Pattern matching for area information
    area_patterns = [
        r"floor.plan",
        r"site.plan",
        r"energy.report",
        r"da.approval",
        r"schedule"
    ]
    
    for file in project_files:
        filename_lower = file.lower()
        
        # Categorize by likely content
        if any(re.search(p, filename_lower) for p in floor_patterns):
            priority_docs["floor_info"].append(file)
            
        if any(re.search(p, filename_lower) for p in area_patterns):
            priority_docs["area_info"].append(file)
            
    return priority_docs
```

---

## Phase 3: Multi-Modal Document Processing

### The Extraction Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         DOCUMENT PROCESSING PIPELINE                                 │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────┐
                    │       DOCUMENT TYPE DETECTION        │
                    │   (Text PDF vs Image-based PDF)      │
                    └─────────────────────────────────────┘
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼                                         ▼
        ┌─────────────────────┐                   ┌─────────────────────┐
        │    TEXT-BASED PDF   │                   │   IMAGE-BASED PDF   │
        │   (Specifications,  │                   │   (Drawings, Plans) │
        │    Reports, DA)     │                   │                     │
        └─────────────────────┘                   └─────────────────────┘
                    │                                         │
                    ▼                                         ▼
        ┌─────────────────────┐                   ┌─────────────────────┐
        │   PyPDF2 / pdfplumber│                  │  PDF → Image Convert│
        │   Text Extraction    │                  │  (pdf2image)        │
        └─────────────────────┘                   └─────────────────────┘
                    │                                         │
                    ▼                                         ▼
        ┌─────────────────────┐                   ┌─────────────────────┐
        │   Regex + NLP       │                   │   Vision API        │
        │   Pattern Matching  │                   │   (Claude Vision)   │
        └─────────────────────┘                   └─────────────────────┘
                    │                                         │
                    └────────────────────┬────────────────────┘
                                         ▼
                    ┌─────────────────────────────────────┐
                    │      STRUCTURED DATA EXTRACTION      │
                    │   {floors_above, floors_below,       │
                    │    gfa, external_area, confidence}   │
                    └─────────────────────────────────────┘
```

### Tool Implementation for Different Document Types

#### For Text-Based PDFs (Specifications, Reports)

```python
# Agent executes this sequence:

# Step 1: Extract text from PDF
tool: bash
command: """
python3 << 'EOF'
import pdfplumber
import re
import json

def extract_metrics_from_text(pdf_path):
    results = {
        "floors_above": None,
        "floors_below": None,
        "gfa": None,
        "external_area": None,
        "sources": []
    }
    
    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text() or ""
            full_text += text + "\n"
            
            # Look for floor count patterns
            floor_patterns = [
                r"(\d+)\s*(?:storey|story|stories|levels?)\s*(?:above|over)\s*ground",
                r"(?:ground|G)\s*\+\s*(\d+)\s*(?:levels?|floors?)",
                r"(\d+)\s*(?:basement|underground)\s*levels?",
                r"floors?:\s*(\d+)\s*above.*?(\d+)\s*below",
            ]
            
            for pattern in floor_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    results["sources"].append({
                        "pattern": pattern,
                        "match": match.group(),
                        "page": page.page_number
                    })
            
            # Look for GFA patterns
            gfa_patterns = [
                r"gross\s*floor\s*area[:\s]*([0-9,]+\.?\d*)\s*(?:m²|sqm|m2)",
                r"GFA[:\s]*([0-9,]+\.?\d*)\s*(?:m²|sqm|m2)",
                r"total\s*floor\s*area[:\s]*([0-9,]+\.?\d*)\s*(?:m²|sqm|m2)",
            ]
            
            for pattern in gfa_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    results["gfa"] = float(match.group(1).replace(",", ""))
                    results["sources"].append({
                        "metric": "gfa",
                        "value": results["gfa"],
                        "page": page.page_number
                    })
    
    return results

result = extract_metrics_from_text("/data/project/DA_Approval.pdf")
print(json.dumps(result, indent=2))
EOF
"""
```

#### For Image-Based PDFs (Architectural Drawings)

```python
# Agent executes this sequence:

# Step 1: Convert PDF pages to images
tool: bash
command: """
python3 << 'EOF'
from pdf2image import convert_from_path
import os

pdf_path = "/data/project/Architectural_Combined.pdf"
output_dir = "/workspace/extracted_images"
os.makedirs(output_dir, exist_ok=True)

# Convert first 5 pages (usually contains plans + elevations)
images = convert_from_path(pdf_path, first_page=1, last_page=5, dpi=200)

for i, image in enumerate(images):
    image.save(f"{output_dir}/page_{i+1}.png", "PNG")
    print(f"Saved page {i+1}")
EOF
"""

# Step 2: Use Claude Vision to analyze each drawing
tool: vision_analyze
image_path: "/workspace/extracted_images/page_1.png"
prompt: """
Analyze this architectural drawing and extract:
1. Number of floors/levels shown above ground
2. Number of basement/underground levels
3. Any gross floor area (GFA) annotations
4. External area or site coverage annotations

Look for:
- Level labels (Ground, L1, L2, B1, B2, etc.)
- Section drawings showing vertical extent
- Area schedules or tables
- Title block information

Provide structured output with confidence levels.
"""
```

### Vision Analysis Strategy for Complex Drawings

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    VISION ANALYSIS STRATEGY FOR DRAWINGS                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  STEP 1: DRAWING TYPE IDENTIFICATION                                                │
│  ════════════════════════════════════                                                │
│  • Floor Plan    → Count level labels, look for area annotations                    │
│  • Section       → Count visible floor plates, identify ground line                 │
│  • Elevation     → Count window rows, identify basement indicators                  │
│  • Site Plan     → Look for building footprint, site boundary annotations           │
│                                                                                      │
│  STEP 2: KEY ELEMENT DETECTION                                                       │
│  ═════════════════════════════                                                       │
│  • Level markers (G, L1, L2, B1, B2, etc.)                                          │
│  • Dimension chains with area callouts                                               │
│  • Title blocks with project summary                                                 │
│  • Area schedule tables                                                              │
│  • North arrows and scale bars (for area calculations)                              │
│                                                                                      │
│  STEP 3: EXTRACTION PROMPTS                                                          │
│  ═════════════════════════                                                           │
│                                                                                      │
│  For Floor Plans:                                                                    │
│  "This is an architectural floor plan. Identify:                                     │
│   - Which level this represents (Ground/L1/L2/B1 etc)                               │
│   - Any area annotations (look for numbers with m² or sqm)                          │
│   - Room schedules or area breakdowns"                                               │
│                                                                                      │
│  For Sections:                                                                       │
│  "This is a building section drawing. Count:                                         │
│   - Total floor plates visible                                                       │
│   - Floors above the ground line (usually marked with grade/GL)                     │
│   - Floors below the ground line (basements)                                        │
│   - Overall building height annotations"                                             │
│                                                                                      │
│  For Site Plans:                                                                     │
│  "This is a site plan. Extract:                                                      │
│   - Site area / lot size                                                             │
│   - Building footprint area                                                          │
│   - External works area (driveways, landscaping)                                    │
│   - Site coverage percentage if shown"                                               │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 4: The Agentic Loop in Action

### Complete Workflow for One Project

Let me walk through exactly what happens when processing **Project 1: Bottlebrush Ave Apartments**:

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ITERATION 1: DISCOVERY                                                              │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  THINK: "I need to understand what files are available for this project"            │
│                                                                                      │
│  ACT:                                                                                │
│  ┌────────────────────────────────────────────────────────────────────────────┐     │
│  │ tool: bash                                                                  │     │
│  │ command: "ls -la /data/110126_Bottlebrush_Ave/"                            │     │
│  └────────────────────────────────────────────────────────────────────────────┘     │
│                                                                                      │
│  OBSERVE:                                                                            │
│  ┌────────────────────────────────────────────────────────────────────────────┐     │
│  │ DA Approval/                                                                │     │
│  │ Drawings/                                                                   │     │
│  │ Finishes/                                                                   │     │
│  │ Reports/                                                                    │     │
│  │ _FIRE SPRINKLERS COMBINED R1.pdf                                           │     │
│  │ _Fire Services Combined.pdf                                                 │     │
│  └────────────────────────────────────────────────────────────────────────────┘     │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ITERATION 2: PRIORITY FILE IDENTIFICATION                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  THINK: "Based on my document priority matrix, I should look at:                    │
│          1. DA Approval folder (Decision Notice has project summary)                │
│          2. Drawings/_Architecturals Combined.pdf (floor plans + sections)          │
│          3. Drawings/_Survey Plan.pdf (site area)"                                  │
│                                                                                      │
│  ACT:                                                                                │
│  ┌────────────────────────────────────────────────────────────────────────────┐     │
│  │ tool: bash                                                                  │     │
│  │ command: "ls -la '/data/110126_Bottlebrush_Ave/DA Approval/'"              │     │
│  └────────────────────────────────────────────────────────────────────────────┘     │
│                                                                                      │
│  OBSERVE:                                                                            │
│  ┌────────────────────────────────────────────────────────────────────────────┐     │
│  │ 001 ECM_21694266_v4_Decision Notice - Approved by Delegation...pdf         │     │
│  │ 002 ECM_21694501_v2_Approved Plans - MCU21-0133 & OPW21-0220.pdf           │     │
│  │ 003 ECM_21696347_v1_MCU21-0133_IC N1677...pdf                              │     │
│  └────────────────────────────────────────────────────────────────────────────┘     │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ITERATION 3: DA DOCUMENT EXTRACTION (Text-based)                                   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  THINK: "DA Decision Notices often contain project summaries with floor counts     │
│          and GFA. Let me extract text and search for patterns."                     │
│                                                                                      │
│  ACT:                                                                                │
│  ┌────────────────────────────────────────────────────────────────────────────┐     │
│  │ tool: bash                                                                  │     │
│  │ command: """                                                                │     │
│  │ python3 -c "                                                                │     │
│  │ import pdfplumber                                                           │     │
│  │ with pdfplumber.open('DA Approval/001*.pdf') as pdf:                       │     │
│  │     for page in pdf.pages[:5]:                                              │     │
│  │         print(page.extract_text()[:2000])                                   │     │
│  │ "                                                                           │     │
│  │ """                                                                         │     │
│  └────────────────────────────────────────────────────────────────────────────┘     │
│                                                                                      │
│  OBSERVE:                                                                            │
│  ┌────────────────────────────────────────────────────────────────────────────┐     │
│  │ DECISION NOTICE                                                             │     │
│  │ Application: MCU21-0133                                                     │     │
│  │ Description: Multiple Dwelling (18 units) over 4 storeys                   │     │
│  │ Site Area: 1,215 m²                                                        │     │
│  │ Gross Floor Area: 2,847 m²                                                 │     │
│  │ ...                                                                         │     │
│  └────────────────────────────────────────────────────────────────────────────┘     │
│                                                                                      │
│  THINK: "Found key data! 4 storeys mentioned, GFA 2,847 m². But I need to          │
│          confirm floors above/below ground. Let me check architectural drawings."   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ITERATION 4: ARCHITECTURAL DRAWING ANALYSIS (Vision-based)                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  THINK: "The architectural drawings will show section views that clarify            │
│          which floors are above/below ground. I'll convert to images and analyze." │
│                                                                                      │
│  ACT:                                                                                │
│  ┌────────────────────────────────────────────────────────────────────────────┐     │
│  │ tool: bash                                                                  │     │
│  │ command: """                                                                │     │
│  │ python3 -c "                                                                │     │
│  │ from pdf2image import convert_from_path                                     │     │
│  │ images = convert_from_path('Drawings/_Architecturals Combined.pdf',        │     │
│  │                            first_page=1, last_page=10, dpi=150)            │     │
│  │ for i, img in enumerate(images):                                            │     │
│  │     img.save(f'/workspace/arch_page_{i+1}.png')                            │     │
│  │ "                                                                           │     │
│  │ """                                                                         │     │
│  └────────────────────────────────────────────────────────────────────────────┘     │
│                                                                                      │
│  ACT (continued):                                                                    │
│  ┌────────────────────────────────────────────────────────────────────────────┐     │
│  │ tool: vision_analyze                                                        │     │
│  │ image: "/workspace/arch_page_3.png"  (typically section drawing)           │     │
│  │ prompt: "This is an architectural section drawing. Please identify:         │     │
│  │   1. The ground level (usually marked GL, Ground, or G)                     │     │
│  │   2. How many floor levels are ABOVE ground                                 │     │
│  │   3. How many floor levels are BELOW ground (basement/parking)              │     │
│  │   4. Any level labels visible (L1, L2, B1, etc.)"                          │     │
│  └────────────────────────────────────────────────────────────────────────────┘     │
│                                                                                      │
│  OBSERVE:                                                                            │
│  ┌────────────────────────────────────────────────────────────────────────────┐     │
│  │ Vision Analysis Result:                                                     │     │
│  │ - Ground level marked as "GROUND FLOOR" at natural ground line             │     │
│  │ - Levels above ground: 4 (Ground, Level 1, Level 2, Level 3)               │     │
│  │ - Levels below ground: 1 (Basement - Car Park)                              │     │
│  │ - Total building height: ~12.5m above ground                                │     │
│  │ - Confidence: HIGH                                                          │     │
│  └────────────────────────────────────────────────────────────────────────────┘     │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ITERATION 5: CROSS-VALIDATION                                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  THINK: "I have data from DA (4 storeys, GFA 2,847m²) and from drawings            │
│          (4 above ground, 1 basement). Let me verify GFA and get external area     │
│          from the site plan or civil drawings."                                     │
│                                                                                      │
│  ACT:                                                                                │
│  ┌────────────────────────────────────────────────────────────────────────────┐     │
│  │ tool: vision_analyze                                                        │     │
│  │ image: "/workspace/survey_page_1.png"                                       │     │
│  │ prompt: "This is a survey/site plan. Please identify:                       │     │
│  │   1. Total site/lot area                                                    │     │
│  │   2. Building footprint area if shown                                       │     │
│  │   3. External areas (driveways, landscaping, setbacks)                      │     │
│  │   4. Any area schedule or summary table"                                    │     │
│  └────────────────────────────────────────────────────────────────────────────┘     │
│                                                                                      │
│  OBSERVE:                                                                            │
│  ┌────────────────────────────────────────────────────────────────────────────┐     │
│  │ Vision Analysis Result:                                                     │     │
│  │ - Site Area: 1,215 m² (matches DA document)                                 │     │
│  │ - Building Footprint: 580 m²                                                │     │
│  │ - External Areas:                                                           │     │
│  │   - Driveway/Access: 120 m²                                                 │     │
│  │   - Landscaping: 315 m²                                                     │     │
│  │   - Pool/Recreation: 85 m²                                                  │     │
│  │ - Total External: ~520 m²                                                   │     │
│  │ - Confidence: MEDIUM-HIGH                                                   │     │
│  └────────────────────────────────────────────────────────────────────────────┘     │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ITERATION 6: CONSOLIDATION & CONFIDENCE SCORING                                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  THINK: "I have collected data from multiple sources. Now I need to                 │
│          consolidate, check for conflicts, and assign confidence scores."           │
│                                                                                      │
│  FINAL OUTPUT FOR PROJECT 1:                                                         │
│  ┌────────────────────────────────────────────────────────────────────────────┐     │
│  │ {                                                                           │     │
│  │   "project_id": "110126",                                                   │     │
│  │   "project_name": "Bottlebrush Ave Apartments, Noosa Heads",               │     │
│  │   "metrics": {                                                              │     │
│  │     "floors_above_ground": 4,                                               │     │
│  │     "floors_below_ground": 1,                                               │     │
│  │     "gross_floor_area_m2": 2847,                                            │     │
│  │     "external_area_m2": 520                                                 │     │
│  │   },                                                                        │     │
│  │   "confidence": {                                                           │     │
│  │     "floors_above_ground": "HIGH",                                          │     │
│  │     "floors_below_ground": "HIGH",                                          │     │
│  │     "gross_floor_area_m2": "HIGH",                                          │     │
│  │     "external_area_m2": "MEDIUM"                                            │     │
│  │   },                                                                        │     │
│  │   "sources": [                                                              │     │
│  │     "DA Approval/001 Decision Notice.pdf (p.1)",                           │     │
│  │     "Drawings/_Architecturals Combined.pdf (p.3 - Section)",               │     │
│  │     "Drawings/_Survey Plan.pdf (p.1)"                                       │     │
│  │   ],                                                                        │     │
│  │   "notes": "External area calculated from site plan elements"              │     │
│  │ }                                                                           │     │
│  └────────────────────────────────────────────────────────────────────────────┘     │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 5: Scaling Across All 29 Projects

### Parallel Processing Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          ORCHESTRATION FOR 29 PROJECTS                               │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────┐
                    │         PROJECT QUEUE               │
                    │   [P1, P2, P3, ... P29]             │
                    └─────────────────────────────────────┘
                                         │
            ┌───────────────┬────────────┼────────────┬───────────────┐
            ▼               ▼            ▼            ▼               ▼
     ┌───────────┐   ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
     │  WORKER 1 │   │  WORKER 2 │ │  WORKER 3 │ │  WORKER 4 │ │  WORKER 5 │
     │  (P1, P6, │   │  (P2, P7, │ │  (P3, P8, │ │  (P4, P9, │ │  (P5, P10,│
     │   P11...)  │   │   P12...) │ │   P13...) │ │   P14...) │ │   P15...) │
     └───────────┘   └───────────┘ └───────────┘ └───────────┘ └───────────┘
            │               │            │            │               │
            └───────────────┴────────────┼────────────┴───────────────┘
                                         ▼
                    ┌─────────────────────────────────────┐
                    │         RESULTS AGGREGATOR          │
                    │   Collect, Validate, Report         │
                    └─────────────────────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────┐
                    │         FINAL OUTPUT                │
                    │   Excel/CSV + Confidence Report     │
                    └─────────────────────────────────────┘
```

### Batch Processing Code

```python
# Orchestrator code for processing all projects

import asyncio
from dataclasses import dataclass
from typing import List, Dict, Optional
import json

@dataclass
class ProjectMetrics:
    project_id: str
    project_name: str
    floors_above_ground: Optional[int]
    floors_below_ground: Optional[int]
    gross_floor_area_m2: Optional[float]
    external_area_m2: Optional[float]
    confidence_scores: Dict[str, str]
    sources: List[str]
    processing_notes: List[str]

class ConstructionDocumentAgent:
    def __init__(self, anthropic_client, sandbox):
        self.client = anthropic_client
        self.sandbox = sandbox
        self.results = []
        
    async def process_all_projects(self, base_path: str) -> List[ProjectMetrics]:
        """Process all projects in the base path"""
        
        # Step 1: Discover all projects
        projects = await self._discover_projects(base_path)
        
        # Step 2: Process each project through the agentic loop
        for project in projects:
            print(f"Processing: {project['name']}")
            
            try:
                metrics = await self._process_single_project(project)
                self.results.append(metrics)
            except Exception as e:
                self.results.append(ProjectMetrics(
                    project_id=project['id'],
                    project_name=project['name'],
                    floors_above_ground=None,
                    floors_below_ground=None,
                    gross_floor_area_m2=None,
                    external_area_m2=None,
                    confidence_scores={},
                    sources=[],
                    processing_notes=[f"ERROR: {str(e)}"]
                ))
        
        return self.results
    
    async def _process_single_project(self, project: dict) -> ProjectMetrics:
        """Run the agentic loop for a single project"""
        
        context = {
            "project": project,
            "extracted_data": {},
            "sources_checked": [],
            "iteration": 0
        }
        
        # Priority document selection
        priority_docs = await self._identify_priority_documents(project)
        
        # Process each priority document
        for doc_category, doc_list in priority_docs.items():
            for doc_path in doc_list[:3]:  # Limit to top 3 per category
                
                # Determine document type
                doc_type = await self._classify_document(doc_path)
                
                if doc_type == "text_pdf":
                    data = await self._extract_from_text_pdf(doc_path)
                elif doc_type == "image_pdf":
                    data = await self._extract_from_image_pdf(doc_path)
                elif doc_type == "image":
                    data = await self._extract_from_image(doc_path)
                else:
                    continue
                
                # Merge extracted data
                context["extracted_data"] = self._merge_data(
                    context["extracted_data"], 
                    data
                )
                context["sources_checked"].append(doc_path)
        
        # Validate and consolidate
        return self._consolidate_metrics(context)
    
    async def _extract_from_image_pdf(self, pdf_path: str) -> dict:
        """Use vision capabilities to extract from drawings"""
        
        # Convert PDF pages to images
        await self.sandbox.execute_bash(f"""
            python3 -c "
            from pdf2image import convert_from_path
            images = convert_from_path('{pdf_path}', dpi=150)
            for i, img in enumerate(images[:5]):
                img.save(f'/workspace/temp_page_{i}.png')
            "
        """)
        
        extracted = {}
        
        # Analyze each page with vision
        for i in range(5):
            image_path = f"/workspace/temp_page_{i}.png"
            
            # Send to Claude Vision
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": self._load_image_base64(image_path)
                            }
                        },
                        {
                            "type": "text",
                            "text": """Analyze this construction drawing and extract:
                            
1. FLOOR COUNT:
   - Number of levels above ground (look for: Ground, G, L1, L2, Level 1, etc.)
   - Number of basement levels (look for: B1, B2, Basement, Lower Ground, etc.)

2. AREAS (if visible):
   - Gross Floor Area (GFA) - look for area schedules or annotations
   - Site/External areas

3. DRAWING TYPE:
   - Is this a floor plan, section, elevation, or site plan?

Return as JSON: {
    "drawing_type": "...",
    "floors_above": null or number,
    "floors_below": null or number,
    "gfa": null or number,
    "external_area": null or number,
    "confidence": "HIGH/MEDIUM/LOW",
    "notes": "..."
}"""
                        }
                    ]
                }]
            )
            
            # Parse response
            try:
                data = json.loads(response.content[0].text)
                extracted = self._merge_data(extracted, data)
            except:
                pass
        
        return extracted
```

---

## Phase 6: Output Generation

### Final Report Structure

```python
# Generate final output

def generate_output(results: List[ProjectMetrics]) -> None:
    """Generate Excel report with all extracted metrics"""
    
    import pandas as pd
    
    # Create DataFrame
    data = []
    for r in results:
        data.append({
            "Project ID": r.project_id,
            "Project Name": r.project_name,
            "Floors Above Ground": r.floors_above_ground,
            "Floors Below Ground": r.floors_below_ground,
            "Gross Floor Area (m²)": r.gross_floor_area_m2,
            "External Area (m²)": r.external_area_m2,
            "Confidence - Floors Above": r.confidence_scores.get("floors_above", "N/A"),
            "Confidence - Floors Below": r.confidence_scores.get("floors_below", "N/A"),
            "Confidence - GFA": r.confidence_scores.get("gfa", "N/A"),
            "Confidence - External": r.confidence_scores.get("external_area", "N/A"),
            "Sources": "; ".join(r.sources),
            "Notes": "; ".join(r.processing_notes)
        })
    
    df = pd.DataFrame(data)
    
    # Save to Excel with formatting
    with pd.ExcelWriter('/output/project_metrics.xlsx', engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Metrics', index=False)
        
        # Add summary sheet
        summary = df.describe()
        summary.to_excel(writer, sheet_name='Summary')
    
    # Also save as JSON for API consumption
    with open('/output/project_metrics.json', 'w') as f:
        json.dump([asdict(r) for r in results], f, indent=2)
    
    print(f"Processed {len(results)} projects")
    print(f"Success rate: {sum(1 for r in results if r.gross_floor_area_m2) / len(results) * 100:.1f}%")
```

### Sample Output

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              EXTRACTION RESULTS                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Project: 110126 - Bottlebrush Ave Apartments                                       │
│  ═══════════════════════════════════════════                                         │
│  Floors Above Ground:  4          (Confidence: HIGH)                                │
│  Floors Below Ground:  1          (Confidence: HIGH)                                │
│  Gross Floor Area:     2,847 m²   (Confidence: HIGH)                                │
│  External Area:        520 m²     (Confidence: MEDIUM)                              │
│                                                                                      │
│  Sources:                                                                            │
│  - DA Approval/Decision Notice.pdf                                                  │
│  - Drawings/_Architecturals Combined.pdf (Section p.3)                              │
│  - Drawings/_Survey Plan.pdf                                                        │
│                                                                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Project: 110140 - 96-98 Tenby Street, Mt Gravatt East                              │
│  ════════════════════════════════════════════════════                                │
│  Floors Above Ground:  5          (Confidence: HIGH)                                │
│  Floors Below Ground:  0          (Confidence: HIGH)                                │
│  Gross Floor Area:     3,215 m²   (Confidence: HIGH)                                │
│  External Area:        380 m²     (Confidence: MEDIUM)                              │
│                                                                                      │
│  Sources:                                                                            │
│  - 100. Architecture/220127 Zhu Tenby ARCH TENDER.pdf                               │
│  - 155. Building Approval/Building Approval (Certifier) v1.pdf                      │
│  - 145. Survey/*.pdf                                                                │
│                                                                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ... (27 more projects)                                                              │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘

SUMMARY STATISTICS:
═══════════════════
Total Projects Processed:     29
Successful Extractions:       26 (89.7%)
Partial Extractions:          2  (6.9%)
Failed Extractions:           1  (3.4%)

Average Confidence Scores:
- Floors Above Ground:  92% HIGH, 8% MEDIUM
- Floors Below Ground:  85% HIGH, 12% MEDIUM, 3% LOW
- Gross Floor Area:     78% HIGH, 19% MEDIUM, 3% LOW
- External Area:        45% HIGH, 48% MEDIUM, 7% LOW
```

---

## Key Takeaways: The Agentic Approach

### Why This Works

1. **Iterative Refinement**: The agent doesn't try to extract everything at once. It discovers, prioritizes, extracts, and validates in cycles.

2. **Multi-Modal Processing**: Combines text extraction (for specs/reports) with vision analysis (for drawings) based on document type.

3. **Source Triangulation**: Cross-references multiple documents to validate findings and assign confidence scores.

4. **Graceful Degradation**: If primary sources fail, falls back to secondary sources. Always produces output, even if partial.

5. **Structured Output**: Returns consistent JSON/Excel format regardless of input document variations.

### Critical Success Factors

| Factor | Implementation |
|--------|----------------|
| **Document Prioritization** | Know which files to check first based on naming patterns |
| **Vision Prompt Engineering** | Specific prompts for floor plans vs sections vs site plans |
| **Confidence Scoring** | Track source reliability and cross-validation |
| **Error Handling** | Graceful fallbacks when documents are missing or unreadable |
| **Parallel Processing** | Process multiple projects simultaneously |

---

## Tools Required

| Tool | Purpose |
|------|---------|
| `bash` | File discovery, PDF conversion, text extraction |
| `file_read` | Read extracted text, configuration files |
| `file_write` | Save intermediate results, final outputs |
| `vision_analyze` | Analyze architectural drawings, site plans |
| `pdf_extract` | Convert PDF to text or images |

This workflow demonstrates how an agentic system can handle complex, multi-modal document analysis at scale—exactly the kind of task that benefits from autonomous iteration and tool use.
