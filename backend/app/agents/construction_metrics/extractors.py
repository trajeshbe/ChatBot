"""
Metric Extraction Functions for Construction Documents

Uses Vision LLM to extract building metrics from:
- Architectural drawings
- DA (Development Application) approvals
- Site photos
- Specifications
"""

import json
import logging
import re
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# Vision LLM Prompts for Metric Extraction
# ============================================================================

ARCHITECTURAL_DRAWING_PROMPT = """You are analyzing an architectural drawing to extract building metrics.

IMPORTANT: Many metrics are NOT explicitly labeled. You must CALCULATE them when necessary.

═══════════════════════════════════════════════════════════════════════
STEP 1: IDENTIFY SCALE BAR
═══════════════════════════════════════════════════════════════════════
Look for scale indicators:
- "1:50" means 1cm on drawing = 0.5m in reality
- "1:100" means 1cm on drawing = 1m in reality
- "1:200" means 1cm on drawing = 2m in reality

If found, record the scale ratio.

═══════════════════════════════════════════════════════════════════════
STEP 2: GROSS FLOOR AREA (GFA) EXTRACTION
═══════════════════════════════════════════════════════════════════════

METHOD 1: Look for Explicit GFA
- Search for: "Gross Floor Area", "GFA", "Total Floor Area"
- If found: Extract the value and mark as "explicit"

METHOD 2: Calculate if NOT Explicitly Stated
- Identify each floor level in the drawings:
  * Ground Floor
  * Level 1 (First Floor)
  * Level 2 (Second Floor)
  * ... etc.

- For EACH floor:
  a) If dimensions are labeled:
     - Length × Width = Floor Area

  b) If dimensions NOT labeled:
     - Use scale bar to measure
     - Estimate dimensions based on:
       * Grid lines (if present)
       * Typical room sizes (bedroom ~12-15m², living ~25-35m²)
       * Visible furniture scale

  c) For irregular shapes:
     - Break into rectangles
     - Sum individual areas

- Sum all floor areas:
  GFA = Ground + Level 1 + Level 2 + ... + Top Floor

═══════════════════════════════════════════════════════════════════════
STEP 3: EXTERNAL AREA CALCULATION
═══════════════════════════════════════════════════════════════════════

METHOD 1: Explicit Statement
- Look for: "External Area", "Terrace Area", "Balcony Area"

METHOD 2: Derivation
- If Site Area is known:
  External Area = Site Area - GFA

METHOD 3: Individual Measurement
- Identify balconies, terraces, outdoor areas
- Measure each individually
- Sum total external area

═══════════════════════════════════════════════════════════════════════
STEP 4: LEVELS COUNTING
═══════════════════════════════════════════════════════════════════════

Levels Above Ground:
- Count floors: Ground Floor = 1, Level 1 = 2, Level 2 = 3, etc.
- Do NOT count roof as a level
- Do NOT count mezzanines as full levels

Levels Below Ground:
- Count: Basement = 1, B1 = 1, B2 = 2, Car Park = 1

═══════════════════════════════════════════════════════════════════════
STEP 5: SITE AREA AND BUILDING HEIGHT
═══════════════════════════════════════════════════════════════════════

Site Area:
- Look for: "Site Area", "Land Area", "Lot Size"
- Check site plan drawings

Building Height:
- Look for: "Building Height", RL (Reduced Level) markers
- Calculate from floor-to-floor heights if shown
- Unit: meters (m)

═══════════════════════════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════════════════════════

Return ONLY a JSON object with this EXACT structure:

{
  "levels_above_ground": <integer or null>,
  "levels_below_ground": <integer or null>,
  "gross_floor_area_m2": <float or null>,
  "external_area_m2": <float or null>,
  "site_area_m2": <float or null>,
  "building_height_m": <float or null>,

  "calculation_method": "explicit" | "calculated_per_floor" | "estimated",
  "confidence": <float 0.0-1.0>,

  "floor_areas": [
    {"floor": "Ground", "area_m2": 850.5, "method": "measured"},
    {"floor": "Level 1", "area_m2": 850.5, "method": "measured"}
  ],

  "scale_used": "1:100" | null,
  "notes": "Brief explanation of calculations performed"
}

EXAMPLE OUTPUT (Calculated GFA):

{
  "levels_above_ground": 3,
  "levels_below_ground": 0,
  "gross_floor_area_m2": 2551.5,
  "external_area_m2": 120.0,
  "site_area_m2": null,
  "building_height_m": 10.5,

  "calculation_method": "calculated_per_floor",
  "confidence": 0.75,

  "floor_areas": [
    {"floor": "Ground", "area_m2": 850.5, "method": "dimensions_labeled"},
    {"floor": "Level 1", "area_m2": 850.5, "method": "same_as_ground"},
    {"floor": "Level 2", "area_m2": 850.5, "method": "same_as_ground"}
  ],

  "scale_used": "1:100",
  "notes": "GFA calculated by summing 3 identical floor plates. Scale 1:100 used for verification. External area measured from roof terrace."
}

EXAMPLE OUTPUT (Explicit GFA):

{
  "levels_above_ground": 4,
  "levels_below_ground": 1,
  "gross_floor_area_m2": 3200.0,
  "external_area_m2": 150.0,
  "site_area_m2": 1500.0,
  "building_height_m": 14.5,

  "calculation_method": "explicit",
  "confidence": 0.95,

  "floor_areas": [],

  "scale_used": null,
  "notes": "All metrics explicitly labeled in drawing title block."
}

═══════════════════════════════════════════════════════════════════════
CONFIDENCE GUIDELINES
═══════════════════════════════════════════════════════════════════════

Confidence Levels:
- 0.9-1.0: Explicitly labeled in drawing with clear values
- 0.7-0.9: Calculated from labeled dimensions
- 0.5-0.7: Calculated using scale bar measurements
- 0.3-0.5: Estimated based on typical sizes
- 0.0-0.3: Uncertain or incomplete data

Always err on the side of lower confidence if uncertain.
"""

DA_APPROVAL_PROMPT = """You are analyzing a Development Application (DA) approval document to extract building metrics.

This is typically a PDF document from a council or planning authority approving a development.

Look for approved development details including:

1. **Approved Levels**: Number of floors/storeys approved
2. **Gross Floor Area**: Total approved floor area
3. **External Areas**: Balconies, terraces, outdoor areas
4. **Site Area**: Property/site area
5. **Building Height**: Maximum approved height

**IMPORTANT INSTRUCTIONS**:
- Focus on the "Approved Development" or "Decision Notice" section
- Look for tables with "Proposed Development Details"
- Extract ONLY approved values (not proposed or refused values)
- If a metric is not mentioned, return null

Return ONLY a JSON object with this exact structure:
{
  "levels_above_ground": <integer or null>,
  "levels_below_ground": <integer or null>,
  "gross_floor_area_m2": <float or null>,
  "external_area_m2": <float or null>,
  "site_area_m2": <float or null>,
  "building_height_m": <float or null>,
  "confidence": <float 0.0-1.0>,
  "notes": "<brief explanation>"
}
"""

SITE_PHOTO_PROMPT = """You are analyzing a construction site photo.

Extract any visible building information:

1. **Visible Levels**: Count of floors you can see in the photo
2. **Building Height**: Estimated height if visible with reference objects
3. **Site Context**: Any visible site area or context

**IMPORTANT**:
- This is visual estimation only, confidence will be lower
- Count only clearly visible complete floors
- If uncertain, return null

Return ONLY a JSON object:
{
  "levels_above_ground": <integer or null>,
  "levels_below_ground": <integer or null>,
  "gross_floor_area_m2": null,
  "external_area_m2": null,
  "site_area_m2": null,
  "building_height_m": <float or null>,
  "confidence": <float 0.0-1.0>,
  "notes": "<what you observed>"
}
"""

SPECIFICATION_PROMPT = """You are analyzing a construction specification document.

Look for building metrics mentioned in the text:

1. **Building description**: Number of levels/floors mentioned
2. **Areas**: Any mentioned floor areas, site areas, external areas
3. **Heights**: Building height specifications

Return ONLY a JSON object:
{
  "levels_above_ground": <integer or null>,
  "levels_below_ground": <integer or null>,
  "gross_floor_area_m2": <float or null>,
  "external_area_m2": <float or null>,
  "site_area_m2": <float or null>,
  "building_height_m": <float or null>,
  "confidence": <float 0.0-1.0>,
  "notes": "<relevant excerpts>"
}
"""


# ============================================================================
# Helper Functions
# ============================================================================

def extract_json_from_llm_response(response: str) -> Dict[str, Any]:
    """
    Extract JSON object from LLM response that may contain markdown or text.

    Args:
        response: Raw LLM response text

    Returns:
        Parsed JSON dict, or default structure if parsing fails
    """
    if not response:
        return _get_default_metrics()

    # Try to find JSON in markdown code blocks
    json_match = re.search(r'```json\s*\n(.*?)\n```', response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        # Try to find JSON by braces
        brace_match = re.search(r'\{.*\}', response, re.DOTALL)
        if brace_match:
            json_str = brace_match.group(0).strip()
        else:
            logger.warning("Could not find JSON in LLM response")
            return _get_default_metrics()

    # Parse JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from LLM response: {e}")
        logger.debug(f"Response was: {json_str[:500]}")
        return _get_default_metrics()


def _get_default_metrics() -> Dict[str, Any]:
    """Return default metrics structure with all null values"""
    return {
        "levels_above_ground": None,
        "levels_below_ground": None,
        "gross_floor_area_m2": None,
        "external_area_m2": None,
        "site_area_m2": None,
        "building_height_m": None,
        "calculation_method": "unknown",
        "confidence": 0.0,
        "floor_areas": [],
        "scale_used": None,
        "notes": "No metrics extracted"
    }


def classify_document_type(filename: str, content_type: str) -> str:
    """
    Classify document type based on filename and content type.

    Args:
        filename: Document filename
        content_type: Content type from multi_analyzer ('image_heavy', 'scanned', etc.)

    Returns:
        Document type: 'architectural_drawing', 'da_approval', 'site_photo', 'specification', 'unknown'
    """
    filename_lower = filename.lower()

    # Architectural drawings
    if any(pattern in filename_lower for pattern in [
        'arch', 'drawing', 'plan', 'elevation', 'section',
        'a0000', 'a1', 'a2', 'a3',  # Common drawing prefixes
        'floor plan', 'site plan'
    ]):
        return 'architectural_drawing'

    # DA/Development approvals
    if any(pattern in filename_lower for pattern in [
        'da approval', 'decision notice', 'development approval',
        'council approval', 'planning approval', 'building approval'
    ]):
        return 'da_approval'

    # Site photos
    if any(pattern in filename_lower for pattern in [
        '.jpg', '.jpeg', '.png', 'photo', 'site photo',
        'img_', 'dsc_'  # Common camera prefixes
    ]) and content_type == 'image_heavy':
        return 'site_photo'

    # Specifications
    if any(pattern in filename_lower for pattern in [
        'spec', 'specification', 'scope of work', 'scope of works',
        'ff&e', 'fixtures', 'schedule'
    ]):
        return 'specification'

    return 'unknown'


def get_prompt_for_document_type(document_type: str) -> str:
    """
    Get the appropriate Vision LLM prompt for a document type.

    Args:
        document_type: Document type classification

    Returns:
        Prompt string for Vision LLM
    """
    prompt_map = {
        'architectural_drawing': ARCHITECTURAL_DRAWING_PROMPT,
        'da_approval': DA_APPROVAL_PROMPT,
        'site_photo': SITE_PHOTO_PROMPT,
        'specification': SPECIFICATION_PROMPT
    }

    return prompt_map.get(document_type, ARCHITECTURAL_DRAWING_PROMPT)


# ============================================================================
# Main Extraction Function
# ============================================================================

async def extract_metrics_from_document(
    file_path: str,
    document_type: str,
    llm_service,
    vision_service,
    model_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract building metrics from a single document using Vision LLM.

    Args:
        file_path: Path to document file
        document_type: Type of document ('architectural_drawing', 'da_approval', etc.)
        llm_service: LLM service instance
        vision_service: Vision service instance
        model_id: LLM model to use (default: llama3.2-vision:11b)

    Returns:
        Dict with extracted metrics:
        {
            "file_path": str,
            "filename": str,
            "document_type": str,
            "metrics": {...},
            "confidence": float,
            "extraction_method": str,
            "raw_response": str
        }
    """
    filename = Path(file_path).name
    logger.info(f"Extracting metrics from {filename} (type: {document_type})")

    try:
        # Get appropriate prompt
        prompt = get_prompt_for_document_type(document_type)

        # Use vision service to analyze document with HybridExtractionService
        if hasattr(vision_service, 'extract_from_document'):
            # Call HybridExtractionService.extract_from_document
            # Use "both_parallel" to leverage ALL extraction methods:
            # - OCR: Extract text from PDFs (good for specifications)
            # - Docling: Advanced document structure understanding
            # - Table extraction: Get numerical data from tables
            # - Vision LLM: Visual understanding of drawings
            # 🆕 CRITICAL FIX: Enable fallback for memory constraints (agent task)
            extraction_result = await vision_service.extract_from_document(
                file_path=file_path,
                content_type="construction_document",  # Content type for strategy selection
                strategy="both_parallel",  # Use ALL extraction methods in parallel for best results
                vision_model=model_id or "llama3.2-vision:11b",
                custom_prompt=prompt,  # Pass our construction metrics prompt
                allow_fallback=True  # 🆕 Enable fallback to smaller model if needed (agent task)
            )

            # Extract the combined text (includes OCR + Docling + Vision analysis)
            # combined_text has the most comprehensive information
            response = extraction_result.get("combined_text", "")
            if not response:
                # Fallback to vision_context if combined_text is empty
                response = extraction_result.get("vision_context", "")
            logger.debug(f"Hybrid extraction response for {filename}: {response[:200]}...")
        else:
            # Fallback: use LLM service with file content
            logger.warning("Vision service doesn't have extract_from_document method, using fallback")
            response = "Vision analysis not available"

        # Parse response
        metrics = extract_json_from_llm_response(response)

        return {
            "file_path": file_path,
            "filename": filename,
            "document_type": document_type,
            "metrics": metrics,
            "confidence": metrics.get("confidence", 0.0),
            "extraction_method": "vision_llm",
            "raw_response": response
        }

    except Exception as e:
        logger.error(f"Error extracting metrics from {filename}: {e}")
        return {
            "file_path": file_path,
            "filename": filename,
            "document_type": document_type,
            "metrics": _get_default_metrics(),
            "confidence": 0.0,
            "extraction_method": "error",
            "raw_response": str(e)
        }


async def batch_extract_metrics(
    files_with_types: List[tuple],  # [(file_path, document_type), ...]
    llm_service,
    vision_service,
    model_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Extract metrics from multiple documents in batch.

    Args:
        files_with_types: List of (file_path, document_type) tuples
        llm_service: LLM service instance
        vision_service: Vision service instance
        model_id: LLM model to use

    Returns:
        List of extraction results
    """
    import asyncio

    tasks = [
        extract_metrics_from_document(
            file_path=file_path,
            document_type=doc_type,
            llm_service=llm_service,
            vision_service=vision_service,
            model_id=model_id
        )
        for file_path, doc_type in files_with_types
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out exceptions
    valid_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Batch extraction error for {files_with_types[i][0]}: {result}")
            # Add error result
            valid_results.append({
                "file_path": files_with_types[i][0],
                "filename": Path(files_with_types[i][0]).name,
                "document_type": files_with_types[i][1],
                "metrics": _get_default_metrics(),
                "confidence": 0.0,
                "extraction_method": "error",
                "raw_response": str(result)
            })
        else:
            valid_results.append(result)

    return valid_results
