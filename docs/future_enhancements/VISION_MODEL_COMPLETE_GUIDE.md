# Vision Model Complete Implementation Guide

**Last Updated**: 2025-11-25
**Status**: ✅ Vision Model Registered | ⚠️ Workflow Needs Documentation

---

## 📋 Summary

The vision model (`llama3.2-vision:11b`) is **fully integrated** but requires specific workflow for image analysis. This guide explains current status, limitations, and best practices.

---

## ✅ What's Working

### 1. Vision Model Registered
- **Model**: llama3.2-vision:11b (7.8 GB)
- **Location**: Model registry (`model_registry.py`)
- **UI Access**: Appears in model dropdown with 🔍 icon
- **GPU**: Enabled via Ollama
- **Capabilities**: Text + Image analysis (multimodal)

### 2. Vision Tool Available
- **Tool ID**: `vision_analysis`
- **Location**: Tool registry (`tool_registry.py` lines 270-301, 1001-1085)
- **Purpose**: LLM can call this tool for image analysis
- **Features**:
  - Image file support (PNG, JPG)
  - PDF support (needs pdf2image)
  - Specific questions ("How many floors?")
  - General analysis mode

### 3. Tool Registry Integration
```python
# 8 tools available for LLM function calling:
- document_rag: Search uploaded documents
- smart_extraction: Web scraping with AI
- web_scraper: Basic Playwright scraping
- template_extraction: Template-based extraction
- docling_pdf: Advanced PDF text extraction
- ocr: Tesseract OCR for images
- vision_analysis: 🆕 Vision model for construction drawings
- navigation_agent: Multi-page web navigation
```

---

## ⚠️ Current Limitations

### 1. Image Upload Pipeline Gap
**Problem**: Images uploaded to chat are NOT automatically analyzed with vision model.

**What Happens**:
- Image stored in MinIO/filesystem
- Document record created
- **BUT**: No vision analysis triggered
- **Result**: User queries about image content search text embeddings (wrong!)

### 2. Query Detection Issue
**Problem**: Asking "what's in Screenshot.png?" searches for text about the filename instead of analyzing the image.

**Example from User Test**:
```
User: "can you explain what is in Screenshot 2025-11-11 174558.png"

Wrong Behavior:
- LLM searches documents for text matching "Screenshot 2025-11-11 174558.png"
- Finds RAG docs mentioning similar terms
- Returns incorrect answer about RAG systems

Correct Behavior Should Be:
- Detect query references an image file
- Find image in session documents
- Call vision_analysis tool with image path
- Return actual image content description
```

### 3. PDF Conversion Missing
**Problem**: `pdf2image` library not installed in container.

**Impact**: Vision tool can't convert PDF pages to images automatically.

**Workaround**: Convert PDFs externally or add pdf2image to requirements.txt

### 4. Embeddings Don't Work for Images
**Problem**: Vector embeddings only work for text, not image pixels.

**Impact**: Can't search images by visual similarity, only by filename or metadata.

---

## 🎯 How to Use Vision Model RIGHT NOW

### Method 1: Upload + Manual Model Selection ✅ WORKS

```
1. Upload Image/PDF to chat
2. Select "LLaMA 3.2 Vision 11B 🔍" from model dropdown
3. Ask: "What's in this image?" or "How many floors?"
4. Vision model analyzes and responds
```

**Pros**: Simple, works immediately
**Cons**: Manual model selection required

### Method 2: Direct API Call ✅ WORKS

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze /tmp/construction_drawing.png and count floors",
    "model": "llama3.2-vision:11b",
    "session_id": "test-session"
  }'
```

**Pros**: Programmatic access
**Cons**: Need to know image path

### Method 3: Tool Registry (For LLM Function Calling) ⚠️ PARTIAL

The `vision_analysis` tool exists but agent doesn't auto-detect image queries yet.

**Current State**: Tool registered, can be called if LLM explicitly chooses it
**Missing**: Agent logic to detect image-related queries

---

## 🔧 Recommended Fixes

### Priority 1: Hybrid Image Upload Pipeline

**Goal**: When image uploaded, immediately run vision analysis and embed the text description.

**Implementation**:

```python
# In document_service.py upload handler
if file_type in ['png', 'jpg', 'jpeg', 'pdf']:
    # 1. Store original file
    file_path = save_to_minio(file)

    # 2. Run vision analysis
    from app.services.vision_service import get_vision_service
    vision_service = await get_vision_service()

    if file_type == 'pdf':
        # Convert first page to image (needs pdf2image)
        image_path = convert_pdf_to_image(file_path)
    else:
        image_path = file_path

    # 3. Get vision description
    vision_result = await vision_service.process_image(
        image_path,
        prompt="Describe this image in detail, including any text, objects, and spatial information."
    )

    # 4. Store vision-generated text as searchable chunks
    await create_document_chunks(
        content=vision_result['text'],
        metadata={
            'type': 'vision_analysis',
            'source_image': filename,
            'model': 'llama3.2-vision:11b'
        }
    )

    # 5. Now RAG search can find image content via text embeddings!
```

**Benefits**:
- ✅ Images become searchable
- ✅ RAG queries work naturally
- ✅ No special query detection needed
- ✅ Text embeddings work on vision-extracted content

### Priority 2: Agent Image Query Detection

**Goal**: Enhanced RAG agent detects image-related queries and calls vision tool.

**Detection Patterns**:
```python
IMAGE_QUERY_PATTERNS = [
    r'what.*in.*\.(png|jpg|jpeg|pdf)',
    r'analyze.*\.(png|jpg|jpeg|pdf)',
    r'describe.*image',
    r'what.*screenshot',
    r'how many (floors|stories|levels)',
    r'floor plan',
    r'construction drawing',
    r'architectural diagram'
]

def is_image_query(query: str) -> bool:
    query_lower = query.lower()
    for pattern in IMAGE_QUERY_PATTERNS:
        if re.search(pattern, query_lower):
            return True
    return False

# In enhanced_rag_agent.py
if is_image_query(query):
    # Find image in session documents
    image_doc = find_image_document(session_id, query)

    if image_doc:
        # Call vision tool directly
        result = await tool_registry.execute_tool(
            'vision_analysis',
            {'image_path': image_doc.file_path, 'question': query}
        )
        return result
```

### Priority 3: Add pdf2image + poppler

**Goal**: Enable automatic PDF → PNG conversion.

**Implementation**:

```dockerfile
# In backend/Dockerfile
RUN apt-get update && apt-get install -y poppler-utils

# In backend/requirements.txt
pdf2image==1.16.3
```

Then restart container to apply changes.

---

## 📊 Best Practices for Construction Drawings

### Workflow for Australian Development Authority Use Case

#### Scenario: Upload construction drawing PDF, extract floors and GFA

**Step-by-Step**:

```
1. UPLOAD PHASE:
   User uploads: "A 1101 [C].pdf"
   ↓
   System detects: PDF file
   ↓
   Convert to PNG: page 1 extracted
   ↓
   Vision analysis runs:
     - Detects: Architectural floor plan
     - Extracts text: Building name, drawing number
     - Counts: 2 floors visible
     - Identifies: GFA markers (if present)
   ↓
   Store both:
     - Original PDF (MinIO)
     - Vision analysis text (database with embeddings)

2. QUERY PHASE:
   User asks: "How many floors are in Galleon Gardens?"
   ↓
   RAG search finds: Vision analysis text mentioning "2 floors"
   ↓
   Agent returns:
     "Based on architectural drawing A 1101 [C].pdf,
      the building has 2 floors."
   ↓
   Sources show: Document name + vision analysis timestamp
```

**Benefits**:
- Natural language queries work
- No special commands needed
- Source attribution included
- Works with text embeddings

### Structured Data Extraction

For systematic extraction (all drawings in batch):

```python
# Process multiple construction drawings
drawings = [
    "A 1101 [C].pdf",
    "A 1102 [C].pdf",
    "A 1103 [C].pdf"
]

results = []
for drawing in drawings:
    vision_result = await vision_service.process_image(
        drawing,
        prompt="""
        Extract the following from this construction drawing:
        1. Building name
        2. Number of floors
        3. Gross Floor Area (GFA) if visible
        4. Drawing number
        5. Any special features or notes

        Provide as structured data.
        """
    )

    # Parse vision model response into structured format
    parsed = parse_vision_response(vision_result['text'])
    results.append({
        'filename': drawing,
        'floors': parsed.get('floors'),
        'gfa': parsed.get('gfa'),
        'features': parsed.get('features')
    })

# Export to Excel/CSV for approval process
df = pd.DataFrame(results)
df.to_excel('construction_analysis.xlsx')
```

---

## 🧪 Testing Vision Capabilities

### Test 1: Simple Image Analysis

```python
from app.services.vision_service import get_vision_service

vision_service = await get_vision_service()

result = await vision_service.describe_image(
    '/path/to/construction_drawing.png',
    question="How many floors are shown in this building?"
)

print(result)  # "The architectural drawing shows a 2-story building..."
```

### Test 2: Floor Count Extraction

```python
result = await vision_service.process_image(
    '/path/to/floor_plan.pdf',
    prompt="Count the number of floors in this building and explain your reasoning."
)

# Result includes confidence level and reasoning
```

### Test 3: GFA Extraction

```python
result = await vision_service.describe_image(
    '/path/to/architectural_diagram.png',
    question="What is the Gross Floor Area (GFA) indicated in this diagram?"
)

# Vision model looks for GFA labels, dimension annotations, etc.
```

---

## ⚡ Performance Notes

### Vision Model Characteristics

- **Model Size**: 7.8 GB
- **GPU Required**: Yes (available via Ollama)
- **First Query**: 120-180 seconds (model loading)
- **Subsequent Queries**: 30-60 seconds (depends on image complexity)
- **Timeout**: 120 seconds (may need increase for complex drawings)

### Optimization Tips

1. **Pre-load Model**: Hit vision endpoint on startup to load model into GPU memory
2. **Batch Processing**: Process multiple similar images together
3. **Cache Results**: Store vision analysis text to avoid re-analyzing
4. **Increase Timeout**: For complex architectural drawings, use 180-240s timeout

---

## 🚀 Future Enhancements

### Phase 1: Basic Integration (✅ COMPLETE)
- ✅ Vision model in registry
- ✅ Vision tool registered
- ✅ Manual selection works

### Phase 2: Automatic Workflow (⚠️ IN PROGRESS)
- ⚠️ Auto-detect image queries
- ⚠️ Vision analysis on upload
- ⚠️ Embed vision-generated text

### Phase 3: Advanced Features (🔜 FUTURE)
- 🔜 Multi-page PDF processing
- 🔜 Comparison analysis (compare 2 drawings)
- 🔜 OCR + Vision hybrid (better text extraction)
- 🔜 Spatial reasoning (room layout understanding)
- 🔜 Symbol recognition (architectural symbols)

---

## 📚 Related Documentation

- **Vision Service**: `backend/app/services/vision_service.py`
- **Tool Registry**: `backend/app/agents/tool_registry.py` (lines 270-301, 1001-1085)
- **Model Registry**: `backend/app/models/model_registry.py` (lines 302-316)
- **Fixes Applied**: `FIXES_APPLIED_2025-11-25.md` (Fix #13, #14)

---

## 🆘 Troubleshooting

### Issue: "Model timeout after 120s"
**Solution**: Increase timeout in `vision_service.py`:
```python
self.timeout = 240.0  # Increase from 120s
```

### Issue: "pdf2image not found"
**Solution**: Add to requirements.txt and rebuild:
```bash
echo "pdf2image==1.16.3" >> backend/requirements.txt
docker-compose build backend
```

### Issue: "Image uploaded but query returns wrong answer"
**Solution**: Use Method 1 (manual model selection) OR implement Priority 1 fix (hybrid pipeline)

### Issue: "Vision analysis takes too long"
**Solution**:
1. Check GPU is being used: `docker-compose logs ollama | grep CUDA`
2. Pre-load model on startup
3. Use smaller images (resize to max 2000px)

---

**End of Guide**
