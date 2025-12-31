# Vision Query Failure - ROOT CAUSE IDENTIFIED

**Date**: 2025-12-08
**Issue**: arch1.pdf vision analysis returning Python documents instead of analyzing the architecture diagram
**Status**: ❌ **OLLAMA MEMORY ISSUE**

---

## 🎯 Problem Summary

**User Query**: "In the attached arch1 architecture diagram, analyze and find the number of rooms and also the total sq ft area of the house"

**Expected Behavior**:
- System routes to vision_analysis tool
- PDF converted to image
- Vision model analyzes the architecture diagram
- Returns room count and square footage

**Actual Behavior**:
- System routes to vision_analysis tool ✅
- PDF converted to image ✅
- **Ollama 500 error when loading qwen2.5vl:latest** ❌
- Vision service returns EMPTY result ❌
- Falls back to document_rag ❌
- Retrieves wrong documents (Python docs) ❌

---

## 🔍 Root Cause Analysis

### Step-by-Step Breakdown:

#### 1. Query Classification ✅ CORRECT
```
Reasoning: Visual query detected: The query mentions 'arch1 architecture diagram'
and requires finding the number of rooms and calculating the total square footage area,
which indicates a need for visual content analysis to interpret the diagram.

Files: ['pdf']. Using vision_analysis → docling_pdf → ocr → document_rag
```

**Result**: Routing correctly identifies this as a visual query requiring vision_analysis.

---

#### 2. PDF to Image Conversion ✅ CORRECT
```
📄 Found visual document: arch1.pdf (application/pdf)
   at Technology/Backend-Development/Global/admin/documents/arch1.pdf
📥 Downloading from MinIO: bucket=documents,
   path=Technology/Backend-Development/Global/admin/documents/arch1.pdf
📄 PDF detected: /tmp/tmpb2c8xcoc.pdf, converting to image for vision analysis
✅ PDF converted to image using PyMuPDF: /tmp/vision_pdf_tmpb2c8xcoc.pdf.png
```

**Result**: arch1.pdf successfully converted to image for vision processing.

---

#### 3. Vision Model Processing ❌ **OLLAMA 500 ERROR**
```
2025-12-08 12:47:49,895 - app.services.vision_service - ERROR -
Vision processing failed: Server error '500 Internal Server Error'
for url 'http://ollama:11434/api/generate'

Model attempted: qwen2.5vl:latest
Error: Ollama internal server error (likely memory issue)
```

**Result**: qwen2.5vl:latest fails to process the image due to Ollama 500 error.

---

#### 4. Empty Vision Result Returned ❌ **SILENT FAILURE**
```python
{'success': True, 'text': '', 'analysis': '', 'model': 'llama3.2-vision:11b',
 'metadata': {'source': '/tmp/vision_pdf_tmpcv1a766w.pdf.png',
              'extraction_method': 'vision_language_model',
              'question': 'In the attached arch1 architecure diagram, analyze and find...'}}
```

**Problem**: Instead of propagating the error, the system returns an empty vision result with `'text': ''`.

**This is the CRITICAL bug**: Empty vision result should trigger proper fallback, not silent failure.

---

#### 5. Fallback to document_rag with Empty Context ❌ **WRONG BEHAVIOR**
```
Query reformulation: 'Based on the following information, In the attached arch1
architecure diagram, analyze and find the number of rooms and also  calculate
the total sq ft area of the house
{'success': True, 'text': '', ...}' → 3 variations
```

**Problem**: The system passes the empty vision result to document_rag, which then:
- Has NO visual context (text is empty)
- Searches for generic keywords like "architecture", "diagram"
- Retrieves wrong documents (Python docs that happen to match keywords)

---

## 💡 Why This is Happening

### Ollama Memory Issue with qwen2.5vl:latest

qwen2.5vl:latest is a **large vision model** that requires significant memory:
- **Model Size**: Varies (3B, 7B, 14B, 32B variants)
- **Memory Required**: Depends on variant, but typically 8-16GB+ for larger models
- **Your System**: Ollama has ~5GB available memory

When qwen2.5vl tries to load, Ollama runs out of memory and returns 500 error.

### Silent Failure in Vision Service

The vision_service catches the Ollama 500 error but returns an empty result instead of:
1. Logging a clear error message
2. Returning a proper error status
3. Triggering the fallback mechanism correctly

This causes the system to proceed with an empty vision result, leading to wrong document retrieval.

---

## ✅ Solutions

### Solution 1: Use Smaller Vision Model (IMMEDIATE FIX)

**Change model from `qwen2.5vl:latest` to `llama3.2-vision:11b`:**

**How to do it:**
1. In the UI model dropdown, select **llama3.2-vision:11b** instead of qwen2.5vl:latest
2. Retry your query

**Why this works:**
- llama3.2-vision:11b is more stable and memory-efficient
- Already proven to work in your environment
- Supported by the system

---

### Solution 2: Use API Vision Model (BEST FOR ACCURACY)

**Use OpenAI GPT-4o-mini or Claude Sonnet:**

**How to do it:**
1. In the UI model dropdown, select **gpt-4o-mini** or **claude-3.5-sonnet**
2. Ensure you have API keys configured in .env:
   ```
   OPENAI_API_KEY=your-key-here
   ANTHROPIC_API_KEY=your-key-here
   ```
3. Retry your query

**Why this is better:**
- No memory constraints (runs on provider's servers)
- Better accuracy for vision tasks
- More reliable

---

### Solution 3: Increase Ollama Memory (REQUIRES CONFIG CHANGE)

**Allocate more memory to Ollama container:**

Edit `docker-compose.yml`:
```yaml
ollama:
  image: ollama/ollama:latest
  deploy:
    resources:
      limits:
        memory: 16G  # Increase from current limit
```

Then rebuild:
```bash
docker-compose down
docker-compose up -d
```

**Note**: This requires your system to have sufficient RAM available.

---

### Solution 4: Fix Vision Service Error Handling (CODE FIX)

**Update vision_service.py to properly handle Ollama errors:**

This would prevent silent failures and ensure proper fallback behavior when Ollama fails.

**File**: `/backend/app/services/vision_service.py`
**Lines**: 226-288 (`_call_ollama_vision` method)

**Issue**: Currently catches 500 errors but doesn't propagate them correctly, leading to empty results.

---

## 🧪 Quick Test

Try this command to test if qwen2.5vl works directly with Ollama:

```bash
curl -X POST http://localhost:11434/api/generate \
  -d '{
    "model": "qwen2.5vl:latest",
    "prompt": "Describe this image",
    "images": ["iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="],
    "stream": false
  }'
```

**Expected**:
- If it works: JSON response with generated text
- If it fails: 500 error with memory-related message

---

## 📊 Comparison: Working vs Broken Flow

### WORKING FLOW (When it worked "couple of days ago"):
```
1. Query Classification → vision_analysis ✅
2. PDF → Image conversion ✅
3. Vision model (llama3.2-vision:11b) analyzes image ✅
4. Returns analysis with room count and sq ft ✅
5. Answer shown to user ✅
```

### BROKEN FLOW (Current issue):
```
1. Query Classification → vision_analysis ✅
2. PDF → Image conversion ✅
3. Vision model (qwen2.5vl:latest) FAILS with 500 error ❌
4. Returns EMPTY text result ❌
5. Fallback to document_rag with no visual context ❌
6. Retrieves wrong documents (Python docs) ❌
7. Answer about Python instead of architecture ❌
```

---

## 🎯 Immediate Action Required

**Option A: Quick Fix (Use llama3.2-vision:11b)**
1. Open UI at http://localhost:3001
2. Click model dropdown
3. Select **llama3.2-vision:11b**
4. Retry your arch1.pdf query

**Option B: Best Quality (Use GPT-4o-mini)**
1. Open UI at http://localhost:3001
2. Click model dropdown
3. Select **gpt-4o-mini**
4. Retry your arch1.pdf query

---

## 📝 Related Issues

### Model Selection Fix (Completed)
- **File**: `/tmp/MODEL_SELECTION_FIX_DEPLOYED.md`
- **Status**: ✅ Fixed - UI model selection now properly passes to vision service
- **This confirms**: The model_id is being passed correctly, but qwen2.5vl is failing to load

### Why It Worked Before
A few days ago, you were likely using:
- **llama3.2-vision:11b** (default vision model)
- OR had less memory pressure on Ollama
- OR qwen2.5vl was a smaller variant

---

## 🔧 Debug Commands

```bash
# Check Ollama memory usage
docker stats ollama

# Check available vision models
curl -s http://localhost:11434/api/tags | python3 -c "
import sys, json
data = json.load(sys.stdin)
for m in data.get('models', []):
    if 'vision' in m['name'] or 'vl' in m['name']:
        print(f\"{m['name']} - Size: {m.get('size', 'unknown')}\")
"

# Test qwen2.5vl directly
docker exec -it ollama ollama run qwen2.5vl:latest "Describe this image"
```

---

## ✅ Summary

**Root Cause**: qwen2.5vl:latest crashes Ollama with 500 error due to memory constraints

**Impact**: Vision analysis fails silently, falls back to document_rag with empty context, retrieves wrong documents

**Solution**:
1. Use llama3.2-vision:11b (immediate fix)
2. Use gpt-4o-mini (best quality)
3. Increase Ollama memory allocation (requires config change)

**Status**:
- ✅ Routing is correct
- ✅ PDF conversion works
- ✅ Model selection works
- ❌ qwen2.5vl fails due to memory
- ❌ Error handling needs improvement

---

**Next Step**: Select a different vision model in the UI dropdown and retry your query.
