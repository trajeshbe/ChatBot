# Hybrid Extraction Testing Guide

**Date**: 2025-12-02
**Status**: ✅ **READY TO TEST**
**Priority**: P0 (Core Feature)

---

## Quick Test

### 1. Upload Technical Drawing PDF

Upload any technical drawing PDF (CAD plans, floor plans, engineering drawings) via the UI at http://localhost:3001

**Test Files**:
- WA200-CONTROL-PLAN-Rev.K.pdf
- WA206-EQUIPMENT-ORDERING-PLAN-Rev.E.pdf
- Any architectural/engineering drawing PDF

### 2. Monitor Processing

**Terminal 1** - Watch hybrid extraction:
```bash
docker-compose logs backend -f | grep -E "(Running hybrid|Hybrid extraction|Methods used|Confidence|OCR|Vision)" --color=always
```

**Expected Output**:
```
🔍 Running hybrid OCR+Vision extraction for vector_graphics document...
   Running OCR extraction...
   Running Vision model analysis with llama3.2-vision:11b...
✅ Hybrid extraction complete:
   Methods used: ['ocr', 'vision']
   Confidence: 87%
   Original text: 5000 chars
   Added text: 12000 chars
   Total text: 17000 chars
```

**Terminal 2** - Watch full processing:
```bash
docker-compose logs backend -f | grep -E "(Processing document|Content type:|Multi-analyzer|Voting result)" --color=always
```

**Expected Output**:
```
📄 Processing document: WA206-EQUIPMENT-ORDERING-PLAN-Rev.E.pdf
   Running multi-analyzer ensemble...
   ├─ PyMuPDF Analyzer: vector_graphics (confidence: 85%)
   ├─ PIL Visual Analyzer: vector_graphics (confidence: 92%)
   ├─ PDF Structure Analyzer: vector_graphics (confidence: 95%)
   └─ Docling Analyzer: image_heavy (confidence: 75%)

✅ Voting result: vector_graphics (3/4 votes, 90% confidence)
   Content type: vector_graphics
```

### 3. Query the Document

After upload completes (30-60 seconds), ask:

**Architectural Questions**:
- "What is the Gross Floor Area?"
- "What is the External Area?"
- "How many levels are above ground?"
- "How many levels are below ground?"
- "What is the building height?"

**Technical Questions**:
- "List all room names and their areas"
- "What are the key dimensions?"
- "What equipment is shown in this drawing?"
- "Summarize the technical specifications"

### 4. Verify Results

The answer should include:
- ✅ Information extracted from graphical annotations
- ✅ Dimensions and measurements
- ✅ Room labels and names
- ✅ Technical specifications
- ✅ Source attribution with document name

---

## What's Being Tested

### Feature 1: Multi-Analyzer Ensemble
**File**: `backend/app/services/document_service.py`
**Lines**: 344-390

**What It Does**:
- Runs 4 analyzers in parallel (PyMuPDF, Docling, PIL Visual, PDF Structure)
- Each analyzer votes on content type
- Consolidates results with confidence scoring

**Success Criteria**:
- ✅ Detects `vector_graphics` or `image_heavy` for technical drawings
- ✅ Confidence ≥ 70%
- ✅ At least 2/4 analyzers agree

**Log Messages**:
```
📊 Multi-analyzer voting results:
   - PyMuPDF Analyzer: vector_graphics (85%)
   - PIL Visual Analyzer: vector_graphics (92%)
   - PDF Structure Analyzer: vector_graphics (95%)
   - Docling Analyzer: image_heavy (75%)

✅ Consolidated result: vector_graphics (90% confidence)
```

### Feature 2: Hybrid OCR + Vision Extraction
**File**: `backend/app/services/hybrid_extraction_service.py`
**Lines**: 1-700+

**What It Does**:
- **OCR Path** (via `ocr_service.py`):
  - Renders PDF at 300 DPI
  - Preprocesses with bilateral filtering + adaptive thresholding
  - Extracts text with Tesseract (PSM 11 sparse text mode)

- **Vision Path** (via LLaMA 3.2 Vision 11B):
  - Analyzes drawing context and layout
  - Extracts handwritten annotations
  - Understands visual relationships
  - Answers complex spatial questions

- **Merging**:
  - Combines OCR text (fast, accurate) with Vision context (understanding)
  - Adds to Docling text for comprehensive coverage

**Success Criteria**:
- ✅ Both OCR and Vision methods execute
- ✅ Combined text length > original text
- ✅ Confidence ≥ 70%
- ✅ Extracts text from graphical annotations

**Log Messages**:
```
🔍 Running hybrid OCR+Vision extraction for vector_graphics document...
   Strategy: auto (selected: both_parallel)
   Vision model: llama3.2-vision:11b

📝 OCR Extraction Results:
   - Pages processed: 42
   - Text extracted: 8,542 chars
   - Average confidence: 89%
   - Processing time: 12.3s

👁️ Vision Model Results:
   - Images analyzed: 42
   - Context extracted: 3,458 chars
   - Key findings: 127
   - Processing time: 24.7s

✅ Hybrid extraction complete:
   Methods used: ['ocr', 'vision']
   Confidence: 87%
   Original text: 5,000 chars
   Added text: 12,000 chars (OCR: 8,542 + Vision: 3,458)
   Total text: 17,000 chars
```

### Feature 3: Enhanced OCR Service
**File**: `backend/app/services/ocr_service.py`
**Lines**: 298-600

**What It Does**:
- **PDF OCR**: PyMuPDF rendering at 300 DPI → Tesseract
- **Preprocessing**: Bilateral filtering, adaptive thresholding, morphological operations
- **Image Extraction**: Embedded images from PDF, DOCX, PPTX, XLSX
- **Batch Processing**: Async processing of multiple pages/images

**Success Criteria**:
- ✅ Extracts text from rendered PDF pages
- ✅ Preprocesses images for better OCR quality
- ✅ Handles technical drawings with high contrast lines
- ✅ Confidence ≥ 60% (technical drawings are challenging)

**Log Messages**:
```
📄 Running PDF OCR extraction...
   Pages to process: 42
   Resolution: 300 DPI
   OCR mode: Tesseract PSM 11 (sparse text)

📊 OCR Results by Page:
   Page 1: 287 chars (confidence: 91%)
   Page 2: 193 chars (confidence: 87%)
   ...
   Page 42: 156 chars (confidence: 84%)

✅ PDF OCR complete:
   Total text: 8,542 chars
   Average confidence: 89%
   Processing time: 12.3s
```

### Feature 4: Smart Query Waiting
**File**: `backend/app/main.py`
**Lines**: 640-694

**What It Does**:
- When user queries immediately after upload
- Automatically polls every 2 seconds for up to 30 seconds
- Waits for document processing to complete
- Returns friendly message if timeout

**Success Criteria**:
- ✅ Query doesn't fail if document still processing
- ✅ Returns answer when ready (< 30s typical)
- ✅ Returns timeout message if needed (> 30s)
- ✅ No user action required

**Log Messages**:
```
⏳ Checking if session documents are ready for query...

⏳ Waiting for 1 document(s) to finish processing:
   ['WA206-EQUIPMENT-ORDERING-PLAN-Rev.E.pdf']
   Elapsed: 2s / 30s

⏳ Waiting for 1 document(s) to finish processing...
   Elapsed: 4s / 30s

✅ All session documents are ready!
   Executing query...
```

---

## Test Scenarios

### Scenario 1: Small Technical Drawing (Fast)
**File**: 5-page floor plan PDF
**Expected Time**: 15-20 seconds
**Expected Behavior**:
1. Upload → Returns immediately
2. Multi-analyzer detects vector_graphics (3/4 votes)
3. Hybrid extraction runs (OCR + Vision)
4. Processing completes in ~15s
5. Query immediately → Waits 0-5s → Returns answer

### Scenario 2: Large Technical Drawing (Normal)
**File**: 40-page equipment plan PDF (like WA206)
**Expected Time**: 45-60 seconds
**Expected Behavior**:
1. Upload → Returns immediately
2. Multi-analyzer detects vector_graphics (90% confidence)
3. Hybrid extraction runs (OCR + Vision parallel)
4. Processing takes ~50s
5. Query after 20s → Waits 30s → Returns answer
6. Query after 60s → Returns immediately

### Scenario 3: Very Large Technical Drawing (Slow)
**File**: 200+ page technical specification PDF
**Expected Time**: 2-3 minutes
**Expected Behavior**:
1. Upload → Returns immediately
2. Multi-analyzer detects vector_graphics
3. Hybrid extraction runs
4. Processing takes ~120s
5. Query after 10s → Waits 30s → Timeout message
6. Query after 150s → Returns answer immediately

**Timeout Message**:
```
⏳ Your document(s) are still being processed: WA206-EQUIPMENT-ORDERING-PLAN-Rev.E.pdf.
This usually takes 1-2 minutes for large documents with technical drawings.
Please try your query again in a moment.
```

---

## Monitoring Commands

### Real-time Monitoring

**Terminal 1** - Hybrid extraction:
```bash
docker-compose logs backend -f | grep -E "(Running hybrid|Hybrid extraction|Methods used|Confidence|OCR|Vision)" --color=always
```

**Terminal 2** - Multi-analyzer:
```bash
docker-compose logs backend -f | grep -E "(Multi-analyzer|Voting result|Content type:)" --color=always
```

**Terminal 3** - Processing progress:
```bash
docker-compose logs backend -f | grep -E "(Processing document|chunks generated|Embedding|Complete)" --color=always
```

**Terminal 4** - Query waiting:
```bash
docker-compose logs backend -f | grep -E "(⏳|✅ All session|⚠️ Query timeout)" --color=always
```

### Post-Upload Analysis

**Check document in database**:
```bash
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "
  SELECT filename, file_type, processing_status,
         (SELECT COUNT(*) FROM document_chunks WHERE document_id = documents.id) as chunk_count
  FROM documents
  ORDER BY created_at DESC
  LIMIT 5;
"
```

**Check embeddings**:
```bash
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "
  SELECT
    d.filename,
    COUNT(DISTINCT dc.id) as total_chunks,
    COUNT(dc.embedding) as text_embeddings,
    COUNT(dc.visual_embedding) as visual_embeddings,
    COUNT(dc.table_embedding) as table_embeddings
  FROM documents d
  LEFT JOIN document_chunks dc ON d.id = dc.document_id
  WHERE d.filename LIKE '%WA%'
  GROUP BY d.filename;
"
```

---

## Troubleshooting

### Issue 1: Hybrid Extraction Not Running

**Symptom**: No "Running hybrid" log message

**Check**:
```bash
docker-compose logs backend | grep "Content type:"
```

**Possible Causes**:
- Document not detected as vector_graphics or image_heavy
- File type check failed
- Hybrid extraction service import error

**Solutions**:
1. Verify multi-analyzer detected correct content type
2. Check file_type in database:
   ```bash
   docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "
     SELECT filename, file_type FROM documents ORDER BY created_at DESC LIMIT 5;
   "
   ```
3. Verify file_type contains 'pdf' (e.g., "application/pdf")
4. Check for import errors in logs

### Issue 2: Vision Model Timeout

**Symptom**: "Vision model timeout after 60s"

**Check**:
```bash
docker-compose exec ollama ollama list
curl http://localhost:11434/api/tags
```

**Possible Causes**:
- LLaMA Vision model not loaded
- Ollama service down
- Out of memory

**Solutions**:
1. Pull vision model:
   ```bash
   docker-compose exec ollama ollama pull llama3.2-vision:11b
   ```
2. Restart Ollama:
   ```bash
   docker-compose restart ollama
   ```
3. Use smaller model (3B instead of 11B)
4. Check memory usage: `docker stats`

### Issue 3: OCR Not Extracting Text

**Symptom**: OCR completes but adds 0 chars

**Check**:
```bash
docker-compose logs backend | grep "OCR.*complete"
```

**Possible Causes**:
- Tesseract not installed in container
- Image preprocessing too aggressive
- PDF pages blank/corrupted

**Solutions**:
1. Verify Tesseract installed:
   ```bash
   docker-compose exec backend which tesseract
   docker-compose exec backend tesseract --version
   ```
2. Check OCR confidence scores in logs
3. Adjust preprocessing parameters in `ocr_service.py`

### Issue 4: Query Returns Empty Results

**Symptom**: Query succeeds but no relevant chunks found

**Check**:
```bash
# Check if chunks were created
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "
  SELECT COUNT(*) FROM document_chunks WHERE document_id = (
    SELECT id FROM documents ORDER BY created_at DESC LIMIT 1
  );
"

# Check if embeddings exist
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "
  SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL;
"
```

**Possible Causes**:
- Chunking failed
- Embeddings not generated
- Query embedding mismatch

**Solutions**:
1. Verify chunks were created
2. Check embedding generation logs
3. Test with simple query: "What is this document about?"

---

## Success Checklist

After testing, verify:

**Multi-Analyzer Ensemble**:
- ✅ Detects vector_graphics for technical drawings
- ✅ Runs 4 analyzers in parallel
- ✅ Consolidates with voting (≥70% confidence)
- ✅ Logs show all analyzer results

**Hybrid Extraction**:
- ✅ Triggers automatically for vector_graphics/image_heavy
- ✅ Runs both OCR and Vision extraction
- ✅ Merges results successfully
- ✅ Adds substantial text (≥2x original for technical drawings)
- ✅ Confidence ≥70%

**Enhanced OCR**:
- ✅ Renders PDF at 300 DPI
- ✅ Preprocesses images correctly
- ✅ Extracts text from graphical annotations
- ✅ Confidence ≥60%

**Vision Model**:
- ✅ Analyzes images with LLaMA Vision
- ✅ Extracts context and understanding
- ✅ Completes within 60s
- ✅ Returns meaningful content

**Smart Query Waiting**:
- ✅ Polls automatically (2s intervals)
- ✅ Returns answer when ready
- ✅ Timeout message after 30s if needed
- ✅ No errors when querying during processing

**Query Results**:
- ✅ Returns relevant information from technical drawings
- ✅ Includes text from graphical annotations
- ✅ Provides source attribution
- ✅ Answers architectural/technical questions accurately

---

## Example Test Log

Here's what a successful test looks like:

```bash
# Upload WA206-EQUIPMENT-ORDERING-PLAN-Rev.E.pdf
📄 Processing document: WA206-EQUIPMENT-ORDERING-PLAN-Rev.E.pdf (42 pages)

# Multi-analyzer ensemble
🔄 Running multi-analyzer ensemble...
   ├─ PyMuPDF Analyzer: vector_graphics (85%) [12.3s]
   ├─ PIL Visual Analyzer: vector_graphics (92%) [8.7s]
   ├─ PDF Structure Analyzer: vector_graphics (95%) [5.2s]
   └─ Docling Analyzer: image_heavy (75%) [18.9s]

📊 Voting results:
   - vector_graphics: 3 votes (75%)
   - image_heavy: 1 vote (25%)

✅ Consolidated result: vector_graphics (90% confidence)

# Hybrid extraction triggered
🔍 Running hybrid OCR+Vision extraction for vector_graphics document...
   Strategy: auto → selected: both_parallel
   Vision model: llama3.2-vision:11b

# OCR extraction
📝 Running OCR extraction...
   Pages: 42
   Resolution: 300 DPI
   Mode: Tesseract PSM 11
   ✅ OCR complete: 8,542 chars (89% confidence) [12.3s]

# Vision extraction (parallel)
👁️ Running Vision model analysis...
   Model: llama3.2-vision:11b
   Images: 42
   ✅ Vision complete: 3,458 chars [24.7s]

# Merging results
✅ Hybrid extraction complete:
   Methods used: ['ocr', 'vision']
   Confidence: 87%
   Original text: 5,000 chars (Docling)
   Added text: 12,000 chars (OCR: 8,542 + Vision: 3,458)
   Total text: 17,000 chars

# Chunking and embedding
🔄 Chunking document...
   Chunk size: 512 chars
   Overlap: 128 chars
   Strategy: semantic_chunking
   ✅ Generated 89 chunks

🔄 Generating embeddings...
   Strategy: vision (multi-modal)
   Model: all-MiniLM-L6-v2 (384d)
   ✅ Embeddings complete: 89 chunks [3.2s]

✅ Document processing complete! [Total: 52.8s]

# Query immediately after upload
POST /api/v1/query
   Query: "What is the Gross Floor Area?"
   Session: abc-123

⏳ Checking if session documents are ready...
⏳ Waiting for 1 document(s) to finish processing...
   Elapsed: 2s / 30s
⏳ Waiting for 1 document(s) to finish processing...
   Elapsed: 4s / 30s

✅ All session documents are ready!

# RAG query execution
🔍 RAG Query:
   Short-term memory: 1 document (WA206)
   Top-k: 5
   Similarity threshold: 0.7

📊 Retrieved chunks:
   1. WA206 - Page 3 - Chunk 12 (score: 0.94)
      "GROSS FLOOR AREA: 12,450 sqm"
   2. WA206 - Page 1 - Chunk 3 (score: 0.89)
      "Building specifications: GFA calculation includes..."
   3. WA206 - Page 5 - Chunk 23 (score: 0.87)
      "Total area breakdown: Gross 12,450 sqm, Net 10,200 sqm"

✅ Query complete:
   Answer: "The Gross Floor Area is 12,450 sqm according to the WA206 equipment ordering plan."
   Sources: 3 chunks from WA206-EQUIPMENT-ORDERING-PLAN-Rev.E.pdf
   Model: gpt-4
   Tokens: 287
   Latency: 2.3s
```

---

## Next Steps

After successful testing:

1. **Document Results**:
   - Create test report with screenshots
   - Note any issues or improvements needed
   - Document query accuracy for different drawing types

2. **Optimize Performance**:
   - Tune OCR preprocessing parameters
   - Adjust vision model prompts for better extraction
   - Optimize parallel processing

3. **Expand Testing**:
   - Test with more drawing types (elevation, section, detail)
   - Test with different file formats (DOCX with embedded images)
   - Test with non-technical documents (should NOT trigger hybrid)

4. **Monitor Production**:
   - Track hybrid extraction usage
   - Monitor vision model latency and memory
   - Collect user feedback on answer quality

---

**Date**: 2025-12-02
**Feature**: Complete and ready to test
**Status**: ✅ **UPLOAD A TECHNICAL DRAWING PDF TO BEGIN TESTING**

---

**End of Testing Guide**
