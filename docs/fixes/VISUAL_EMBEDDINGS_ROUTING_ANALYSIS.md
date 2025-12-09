# Visual Embeddings & Routing Analysis for arch1.pdf

**Date**: 2025-12-07
**Issue**: Visual embeddings not being generated; query routing to visual analysis needs verification
**Status**: 🔴 **CRITICAL** - Visual embeddings system not functioning

---

## 🔍 Investigation Summary

### File Status: arch1.pdf

**Database Records**:
- ✅ File exists: `arch1.pdf`
- ✅ File type: `application/pdf`
- ✅ Processing status: `completed`
- ✅ Upload dates: 2 copies (2025-12-02, 2025-12-06)
- ✅ Text embeddings: Generated successfully

**Document Chunks Analysis**:
```sql
SELECT COUNT(*) as total_chunks, COUNT(visual_embedding) as with_visual
FROM document_chunks dc
JOIN documents d ON dc.document_id = d.id
WHERE d.filename = 'arch1.pdf';
```

**Result**:
```
total_chunks | with_visual
--------------+-------------
            2 |           0
```

❌ **CRITICAL FINDING**: Visual embeddings are **NOT** being generated for arch1.pdf!

---

## 🚨 Root Cause Analysis

### Issue 1: Visual Embedding Generation Failure

**Expected Behavior**:
When uploading a PDF with diagrams/images, the system should:
1. Extract images from PDF using Docling
2. Generate CLIP visual embeddings for images
3. Store both text and visual embeddings in database
4. Populate `visual_embedding` column in `document_chunks` table

**Actual Behavior**:
- Text processing works correctly
- Visual embedding column remains NULL
- Multi-channel processing not creating visual embeddings

**Affected Services**:
- `backend/app/services/document_service.py` - Document upload/processing
- `backend/app/services/multi_channel_processor.py` - Multi-channel embedding generation
- `backend/app/services/intelligent_embedding_service.py` - Embedding strategy selection

---

## 🔬 Query Classification & Routing Analysis

### Current System Capabilities

**Available Components**:
✅ LLaMA 3.2 Vision 11B model (confirmed in logs)
✅ Query classifier infrastructure exists
✅ Vision analysis routing code present
✅ Docling for PDF diagram extraction

**Missing/Not Working**:
❌ Visual embeddings not generated during upload
❌ CLIP embeddings not in database
❌ No visual context for vision model queries

### Expected Routing Flow for Visual Queries

**Query**: "Describe the architecture diagram in arch1.pdf"

**Step 1: Query Classification**
```
Input: "Describe the architecture diagram in arch1.pdf"
↓
Query Classifier (backend/app/services/query_classifier.py)
↓
Classification: VISUAL_QUERY
Confidence: 0.85
Keywords detected: ["diagram", "architecture", "describe"]
```

**Step 2: Embedding Strategy Selection**
```
Query Type: VISUAL_QUERY
↓
Intelligent Embedding Service
↓
Strategy: VISUAL
Use visual_embedding column for retrieval
```

**Step 3: Document Retrieval**
```
SELECT * FROM document_chunks
WHERE visual_embedding IS NOT NULL
ORDER BY visual_embedding <=> query_visual_embedding
LIMIT 5
↓
❌ PROBLEM: Returns 0 results (visual_embedding IS NULL for all chunks)
```

**Step 4: Fallback to Text Retrieval**
```
Fallback triggered: No visual embeddings found
↓
Use standard text embedding retrieval
↓
Return text chunks to LLM
```

**Step 5: LLM Selection & Response**
```
Model: llama3.2-vision:11b
Input: Text chunks (no visual context) + query
↓
LLM generates answer without seeing diagram images
↓
⚠️ Answer quality degraded (no visual analysis possible)
```

---

## 📊 Current Routing Configuration

### Query Classification Rules

Location: `backend/app/config/query_classification_rules.yaml`

**Visual Query Patterns**:
```yaml
visual_queries:
  keywords:
    - diagram
    - image
    - architecture
    - chart
    - graph
    - figure
    - illustration
  threshold: 0.7
  strategy: visual_analysis
  preferred_model: llama3.2-vision:11b
```

### Model Routing

**LLaMA 3.2 Vision** (confirmed available):
- Model: `llama3.2-vision:11b`
- Provider: Ollama
- Capabilities: Text + Image understanding
- Status: ✅ Running and accessible

---

## 🎯 Tool Selection Flow

### Document Processing Tools

**Upload Time**:
1. **Docling** - PDF parsing and image extraction
   - Status: ✅ Available
   - Used for: Extracting images from PDFs

2. **CLIP** - Visual embedding generation
   - Status: ⚠️ Not being called during upload
   - Should generate: 512-dimensional visual embeddings

3. **Sentence Transformers** - Text embedding generation
   - Status: ✅ Working correctly
   - Generates: 384-dimensional text embeddings

**Query Time**:
1. **Query Classifier** - Determines query type
   - Status: ✅ Infrastructure exists
   - Decision: Routes visual queries to vision model

2. **Intelligent Embedding Service** - Selects embedding strategy
   - Status: ⚠️ Falls back to text when visual embeddings missing
   - Should use: Visual embeddings for diagram queries

3. **Vision Model** - Processes visual queries
   - Status: ✅ Model available but receives no visual context
   - Model: llama3.2-vision:11b

---

## 🔧 Diagnostic Steps Performed

### 1. Database Inspection
```bash
# Checked arch1.pdf existence
✅ File found in documents table

# Checked visual embeddings
❌ No visual embeddings in document_chunks

# Checked embedding dimensions
✅ Text embeddings: 384 dimensions
❌ Visual embeddings: NULL
```

### 2. Log Analysis
```bash
# Searched for visual embedding generation
docker logs rag-backend --tail=1000 | grep -i "visual"
# Result: No visual embedding generation logs found

# Searched for CLIP usage
docker logs rag-backend --tail=1000 | grep -i "CLIP"
# Result: No CLIP embedding logs found

# Searched for multi-channel processing
docker logs rag-backend --tail=1000 | grep -i "Multi-channel"
# Result: No multi-channel processing logs found
```

### 3. Query Test
```bash
# Sent test query about architecture diagram
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=Describe the architecture diagram in arch1.pdf" \
  -F "model=llama3.2-vision:11b"

# Expected: Visual embeddings retrieval + vision model analysis
# Actual: Text embeddings retrieval + vision model (degraded quality)
```

---

## 💡 Recommendations

### Immediate Actions

**1. Enable Visual Embedding Generation**

Check and fix the multi-channel processor:

```python
# backend/app/services/multi_channel_processor.py
# Ensure process_with_visual_embeddings() is being called during upload
```

**2. Re-upload arch1.pdf**

Once visual embeddings are enabled:
```bash
# Delete old arch1.pdf entries
DELETE FROM documents WHERE filename = 'arch1.pdf';

# Re-upload through UI with visual processing enabled
# This will generate both text and visual embeddings
```

**3. Verify Visual Embedding Pipeline**

```sql
# After re-upload, check:
SELECT COUNT(*) FROM document_chunks
WHERE visual_embedding IS NOT NULL;
# Should return > 0
```

### Configuration Review Needed

**Files to Check**:
1. `backend/app/services/document_service.py`
   - Line: Document upload handler
   - Check: Is multi_channel_processor being called?

2. `backend/app/services/multi_channel_processor.py`
   - Line: Visual embedding generation
   - Check: Is CLIP model being initialized and used?

3. `backend/app/config/query_classification_rules.yaml`
   - Line: Visual query patterns
   - Check: Are patterns matching correctly?

---

## 🧪 Testing Plan

### Test 1: Visual Embedding Generation
```bash
# Upload a PDF with diagrams
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@arch1.pdf" \
  -F "session_id=visual_test"

# Verify visual embeddings created
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c \
  "SELECT COUNT(*) FROM document_chunks WHERE visual_embedding IS NOT NULL;"
```

### Test 2: Query Classification
```bash
# Send visual query
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=Show me the architecture diagram" \
  -F "session_id=visual_test" \
  -F "model=llama3.2-vision:11b"

# Check logs for classification
docker logs rag-backend | grep "Query Classification"
# Expected: Classification: VISUAL_QUERY, Confidence: >0.7
```

### Test 3: Visual Embedding Retrieval
```bash
# Query with visual intent
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=Explain the components in the diagram" \
  -F "session_id=visual_test"

# Check logs for retrieval strategy
docker logs rag-backend | grep "Embedding Strategy"
# Expected: Strategy: visual_embedding
```

### Test 4: Vision Model Usage
```bash
# Complex visual query
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=Count the layers in the architecture diagram" \
  -F "model=llama3.2-vision:11b"

# Check logs for model routing
docker logs rag-backend | grep "Model:"
# Expected: Using LLaMA 3.2 Vision 11B with visual context
```

---

## 📋 Summary

### What's Working
- ✅ Text embedding generation
- ✅ PDF text extraction
- ✅ Document upload and storage
- ✅ LLaMA 3.2 Vision model availability
- ✅ Query classification infrastructure

### What's NOT Working
- ❌ Visual embedding generation during upload
- ❌ CLIP embeddings creation
- ❌ Multi-channel document processing
- ❌ Visual context for vision model queries

### Impact
- **Severity**: 🔴 HIGH
- **User Impact**: Vision queries cannot access diagram visual context
- **Degraded Experience**: Vision model operates on text-only descriptions
- **Missing Capability**: Full visual RAG pipeline not functional

### Next Steps
1. **Investigate** why visual embeddings aren't being generated
2. **Fix** the multi-channel processor or document service
3. **Re-upload** arch1.pdf to generate visual embeddings
4. **Test** full visual RAG pipeline end-to-end
5. **Verify** query routing to visual analysis is working

---

**Investigation Date**: 2025-12-07
**Investigated By**: Claude Code Assistant
**Files Analyzed**:
- Documents table
- Document_chunks table
- Backend logs (last 1000 lines)
- Query classification configuration

**Status**: Analysis complete, fix required for visual embedding generation
