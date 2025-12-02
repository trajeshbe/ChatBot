# Hybrid OCR + Vision Model Extraction - Implementation Plan

**Date**: 2025-12-02
**Status**: 🔄 **IN PROGRESS** (Strategy Design)
**Priority**: P0 (Comprehensive Image Understanding)

---

## Overview

Comprehensive image and drawing extraction using **TWO complementary approaches**:

1. **OCR (Tesseract)** → Fast, accurate text extraction
2. **Vision Models (LLaMA 3.2 Vision 11B + alternatives)** → Context understanding, complex queries

**Combined Power**: Best of both worlds for technical drawings and embedded images.

---

## Why Hybrid Approach?

###  OCR Strengths (Tesseract)
✅ **Fast**: Processes pages in 1-2 seconds
✅ **Accurate**: 80-95% confidence for clean text
✅ **Text-Focused**: Extracts dimensions, labels, annotations
✅ **No GPU Required**: Runs on CPU

❌ **Limitations**:
- Cannot understand context or relationships
- Struggles with handwriting
- Cannot answer questions about the image
- No layout understanding

### Vision Model Strengths (LLaMA 3.2 Vision 11B)
✅ **Context Understanding**: "What type of drawing is this?"
✅ **Handwriting**: Can read handwritten notes
✅ **Complex Queries**: "How many floors above ground?"
✅ **Layout Understanding**: Understands spatial relationships
✅ **Visual Reasoning**: Can interpret diagrams

❌ **Limitations**:
- Slower (5-10 seconds per image)
- Requires GPU (11B model)
- Higher memory usage (~8GB)
- More expensive computation

---

## Hybrid Strategy: When to Use What

### Strategy 1: OCR FIRST (Default)
**Use For**: Quick text extraction from clean documents

```
Technical Drawing Upload
    ↓
1. OCR (Tesseract) - Extract all text (2 sec)
    ├─ Dimensions: "5000 sqm"
    ├─ Labels: "Gross Floor Area", "External Area"
    └─ Annotations: "Level +10.5m"
    ↓
2. Store extracted text → Embeddings → Searchable
```

**Result**: User can query "What is the Gross Floor Area?" → ✅ "5000 sqm"

---

### Strategy 2: VISION MODEL for Complex Queries
**Use For**: Questions requiring understanding or interpretation

```
User Query: "What type of building is shown in the drawing?"
    ↓
1. Identify relevant PDF page with drawing
2. Render page as image
3. Call LLaMA 3.2 Vision with custom prompt
    ↓
Vision Model analyzes image:
    ├─ Recognizes architectural drawing
    ├─ Identifies building components
    └─ Interprets context
    ↓
Response: "This is a multi-story residential building with
          commercial space on ground floor, 10 levels above
          ground and 2 basement levels."
```

**Result**: Deep understanding, not just text extraction

---

### Strategy 3: HYBRID (Both OCR + Vision)
**Use For**: Maximum accuracy and completeness

```
Critical Technical Document (Engineering Plans, CAD Drawings)
    ↓
1. OCR (Tesseract) - Extract text (2 sec)
    └─ Text: dimensions, labels, annotations
    ↓
2. Vision Model (LLaMA 3.2) - Understand context (8 sec)
    └─ Context: layout, relationships, visual elements
    ↓
3. Merge Both Results
    └─ Combined text stored with full context
```

**Result**: Complete extraction + understanding

---

## Vision Model Options (Memory-Efficient)

### Option 1: LLaMA 3.2 Vision 11B (Current)
- **Memory**: ~8GB GPU RAM
- **Speed**: 8-10 seconds per image
- **Quality**: Excellent
- **Best For**: Production use with GPU

### Option 2: LLaMA 3.2 Vision 3B (Smaller)
- **Memory**: ~4GB GPU RAM
- **Speed**: 4-5 seconds per image
- **Quality**: Very good
- **Best For**: Limited GPU memory

### Option 3: MiniCPM-V 2.6 (Ultra-Small)
- **Memory**: ~2GB GPU RAM
- **Speed**: 2-3 seconds per image
- **Quality**: Good
- **Best For**: CPU-only environments

### Option 4: GPT-4V / Claude 3 Opus (API)
- **Memory**: None (API call)
- **Speed**: 3-5 seconds per image (network latency)
- **Quality**: Excellent
- **Best For**: No local GPU, willing to pay API costs

### Option 5: CLIP (Embeddings Only)
- **Memory**: ~1GB
- **Speed**: <1 second per image
- **Quality**: N/A (embeddings, not text extraction)
- **Best For**: Visual similarity search

---

## Implementation Plan

### Phase 1: Enhance OCR Service ✅ DONE
- ✅ PDF OCR with Tesseract
- ✅ Image extraction from PDF, DOCX, PPTX, XLSX
- ✅ Preprocessing for technical drawings
- ✅ Confidence scoring

### Phase 2: Vision Model Integration 🔄 CURRENT
- 🔄 Create hybrid extraction service
- 🔄 Add vision model selection (11B / 3B / Mini)
- 🔄 Implement fallback chain (Vision → OCR)
- 🔄 Add custom prompt templates

### Phase 3: Document Processing Integration 🔜
- 🔜 Integrate OCR into document_service
- 🔜 Add vision model extraction for vector_graphics
- 🔜 Merge OCR + Vision results
- 🔜 Store combined text with attribution

### Phase 4: Query-Time Vision Analysis 🔜
- 🔜 Detect when user query needs visual understanding
- 🔜 Retrieve relevant images/pages
- 🔜 Call vision model with query as prompt
- 🔜 Return interpreted answer

---

## Proposed Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    HYBRID EXTRACTION PIPELINE                   │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Document Upload (PDF with Technical Drawings)                 │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  Multi-Analyzer Ensemble                                │   │
│  │  └─> Detects: vector_graphics (90% confidence)          │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  PARALLEL EXTRACTION                                     │   │
│  │                                                          │   │
│  │  ┌──────────────────┐       ┌──────────────────┐       │   │
│  │  │  OCR Path        │       │  Vision Path     │       │   │
│  │  │  (Tesseract)     │       │  (LLaMA 3.2)     │       │   │
│  │  │                  │       │                  │       │   │
│  │  │  1. Render PDF   │       │  1. Render PDF   │       │   │
│  │  │  2. Preprocess   │       │  2. Encode image │       │   │
│  │  │  3. OCR Extract  │       │  3. Call LLM     │       │   │
│  │  │  4. Text Output  │       │  4. Context      │       │   │
│  │  │                  │       │                  │       │   │
│  │  │  Result:         │       │  Result:         │       │   │
│  │  │  "Gross Floor    │       │  "This is a      │       │   │
│  │  │   Area: 5000sqm" │       │   floor plan..."  │       │   │
│  │  │                  │       │                  │       │   │
│  │  │  Speed: 2 sec    │       │  Speed: 8 sec    │       │   │
│  │  └──────────────────┘       └──────────────────┘       │   │
│  │           │                         │                   │   │
│  │           └─────────┬───────────────┘                   │   │
│  │                     ▼                                    │   │
│  │          ┌──────────────────────┐                       │   │
│  │          │  MERGE RESULTS       │                       │   │
│  │          │                      │                       │   │
│  │          │  Combined Text:      │                       │   │
│  │          │  - OCR text          │                       │   │
│  │          │  - Vision context    │                       │   │
│  │          │  - Attribution       │                       │   │
│  │          └──────────────────────┘                       │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  Embeddings + Storage                                   │   │
│  │  └─> Store in vector DB with full traceability         │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Proposed Service: HybridExtractionService

```python
class HybridExtractionService:
    """
    Hybrid OCR + Vision Model extraction service

    Uses both Tesseract OCR and vision-language models for
    comprehensive image and drawing understanding.
    """

    def __init__(self):
        self.ocr_service = ocr_service
        self.vision_service = vision_service

        # Vision model configuration
        self.vision_models = {
            "llama3.2-vision:11b": {"memory_gb": 8, "quality": "excellent"},
            "llama3.2-vision:3b": {"memory_gb": 4, "quality": "very_good"},
            "minicpm-v:latest": {"memory_gb": 2, "quality": "good"}
        }

        # Default strategy
        self.default_strategy = "ocr_first"  # or "vision_first", "both_parallel"

    async def extract_from_document(
        self,
        file_path: str,
        content_type: str,  # From multi-analyzer
        strategy: str = "auto",
        vision_model: str = "llama3.2-vision:11b"
    ) -> Dict[str, Any]:
        """
        Extract text and context from document using hybrid approach

        Args:
            file_path: Path to document
            content_type: Content type from multi-analyzer
            strategy: Extraction strategy (auto, ocr_only, vision_only, both)
            vision_model: Vision model to use

        Returns:
            {
                "ocr_text": str,
                "vision_context": str,
                "combined_text": str,
                "confidence": float,
                "methods_used": List[str]
            }
        """

        # Auto-select strategy based on content type
        if strategy == "auto":
            strategy = self._select_strategy(content_type)

        results = {}

        # OCR extraction
        if strategy in ["ocr_only", "ocr_first", "both"]:
            ocr_result = await self.ocr_service.extract_text(file_path)
            results["ocr"] = ocr_result

        # Vision model extraction
        if strategy in ["vision_only", "vision_first", "both"]:
            vision_result = await self.vision_service.process_image(
                image_path=file_path,
                prompt=self._get_vision_prompt(content_type)
            )
            results["vision"] = vision_result

        # Merge results
        return self._merge_results(results, strategy)

    def _select_strategy(self, content_type: str) -> str:
        """Select extraction strategy based on content type"""
        if content_type == "vector_graphics":
            return "both"  # Technical drawings need both
        elif content_type == "image_heavy":
            return "vision_first"  # Photos/diagrams benefit from vision
        elif content_type == "text_heavy":
            return "ocr_only"  # Standard text doesn't need vision
        else:
            return "ocr_first"  # Default to OCR

    def _get_vision_prompt(self, content_type: str) -> str:
        """Get appropriate prompt for vision model"""
        prompts = {
            "vector_graphics": (
                "This is a technical drawing or CAD plan. Please analyze it and provide:\n"
                "1. Type of drawing (floor plan, elevation, section, etc.)\n"
                "2. Key measurements and dimensions visible\n"
                "3. Important annotations or labels\n"
                "4. Any specifications or requirements noted\n"
                "5. Overall purpose or function described"
            ),
            "image_heavy": (
                "Analyze this image in detail. Describe:\n"
                "1. What you see in the image\n"
                "2. Any text visible (signs, labels, captions)\n"
                "3. Context and purpose\n"
                "4. Notable details or elements"
            )
        }
        return prompts.get(content_type, "Describe this image in detail.")

    def _merge_results(self, results: Dict, strategy: str) -> Dict[str, Any]:
        """Merge OCR and Vision results intelligently"""
        ocr_text = results.get("ocr", {}).get("text", "")
        vision_text = results.get("vision", {}).get("text", "")

        # Combine with clear attribution
        combined = ""

        if ocr_text:
            combined += "=== OCR EXTRACTED TEXT ===\n\n" + ocr_text + "\n\n"

        if vision_text:
            combined += "=== VISION MODEL ANALYSIS ===\n\n" + vision_text

        return {
            "ocr_text": ocr_text,
            "vision_context": vision_text,
            "combined_text": combined,
            "confidence": self._calculate_confidence(results),
            "methods_used": list(results.keys())
        }
```

---

## Use Cases with Hybrid Approach

### Use Case 1: Extract Gross Floor Area

**OCR Approach** (Fast):
```
User: "What is the Gross Floor Area?"
System:
1. Searches OCR-extracted text
2. Finds: "Gross Floor Area: 5,000 sqm"
3. Returns answer in 0.1 seconds
```

**Vision Approach** (Understanding):
```
User: "Describe the building shown in the floor plan"
System:
1. Retrieves floor plan page
2. Calls LLaMA 3.2 Vision
3. Returns: "Multi-story residential building with commercial
            ground floor, 10 residential floors, 2 basement
            levels for parking. Total GFA approximately 5,000 sqm."
4. Takes 8 seconds but provides rich context
```

---

## Memory & Performance Considerations

### Vision Model Sizes

| Model | Memory | Speed | Quality | Recommendation |
|-------|--------|-------|---------|----------------|
| LLaMA 3.2 11B | 8GB GPU | 8-10s | Excellent | Production with GPU |
| LLaMA 3.2 3B | 4GB GPU | 4-5s | Very Good | Limited GPU memory |
| MiniCPM-V 2.6 | 2GB GPU | 2-3s | Good | CPU-only systems |
| GPT-4V (API) | 0 (Cloud) | 3-5s | Excellent | No local GPU |
| CLIP | 1GB | <1s | N/A (embeddings) | Similarity only |

### Processing Time Estimates

**Single Page Technical Drawing**:
- OCR only: 2 seconds
- Vision only: 8 seconds
- Both parallel: 8 seconds (run concurrently)
- Both sequential: 10 seconds

**50-Page Technical Document Set**:
- OCR only: 100 seconds (~2 min)
- Vision only: 400 seconds (~7 min)
- Hybrid (critical pages only): 150 seconds (~2.5 min)

---

## Next Steps

### Immediate (This Session)
1. ✅ Enhanced OCR service with comprehensive image extraction
2. 🔄 Create HybridExtractionService
3. 🔄 Add vision model selection
4. 🔄 Integrate into document processing

### Short Term (Next Session)
1. Test with WA200 PDF technical drawings
2. Benchmark OCR vs Vision vs Hybrid
3. Optimize vision prompts for technical drawings
4. Add query-time vision analysis

### Medium Term (Future)
1. Implement CLIP for visual similarity search
2. Add smaller vision models (3B, MiniCPM-V)
3. Create UI for vision model selection
4. Add cost/performance analytics

---

## Success Criteria

| Criterion | Target | How to Measure |
|-----------|--------|----------------|
| **OCR Accuracy** | >85% | Test with known drawings |
| **Vision Understanding** | >90% correct answers | Test with complex queries |
| **Processing Speed** | <10s per page | Benchmark tests |
| **Memory Usage** | <10GB total | Monitor during processing |
| **User Satisfaction** | Answers complex queries | Can extract GFA, levels, etc. |

---

## Conclusion

**Hybrid Approach = Best of Both Worlds**:
- ✅ OCR for fast, accurate text extraction
- ✅ Vision models for deep understanding
- ✅ Flexible strategy selection based on content type
- ✅ Multiple vision model options for different hardware

**Result**: Comprehensive extraction from technical drawings with both speed and intelligence.

---

**Date**: 2025-12-02
**Status**: 🔄 **DESIGNING HYBRID SERVICE**
**Next**: Implement HybridExtractionService

---

**End of Hybrid Strategy Document**
