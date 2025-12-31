# RAG Pipeline Debug Tools

Complete debugging toolkit for diagnosing and fixing RAG pipeline issues.

## 📁 Files Created

### 1. **debug_rag_pipeline.py**
Location: `backend/debug_rag_pipeline.py`

Comprehensive Python script that traces the entire RAG pipeline:
- Query classification analysis
- Embedding generation testing
- Document and chunk analysis
- Vector similarity search testing
- Full pipeline trace
- pgvector installation check

### 2. **debug-rag.sh**
Location: `./debug-rag.sh`

Easy-to-use wrapper script for common debugging tasks.

### 3. **RAG_DEBUGGING_GUIDE.md**
Location: `./RAG_DEBUGGING_GUIDE.md`

Complete 600+ line guide covering:
- Step-by-step debugging workflows
- Common issues and solutions
- Detailed scenario walkthroughs
- Code fixes and examples
- Troubleshooting tips

### 4. **DEBUG_QUICK_REFERENCE.md**
Location: `./DEBUG_QUICK_REFERENCE.md`

Quick reference card with:
- Most common commands
- Quick fixes
- Output interpretation
- Red flags and green flags

## 🚀 Quick Start

### For the TCS Issue

**Step 1: Check documents**
```bash
./debug-rag.sh docs
```

**Step 2: Trace the problematic query**
```bash
./debug-rag.sh trace "what is the revenue of TCS in Sep 2025?"
```

**Step 3: Analyze the output**
Look for:
- ❌ Wrong documents retrieved (Thoothukudi instead of TCS)
- ❌ Query classification incorrect
- ❌ Low similarity scores
- ❌ Missing embeddings

**Step 4: Apply fixes**
See `RAG_DEBUGGING_GUIDE.md` sections:
- Fix 1: Update Query Classification
- Fix 2: Add Keyword Boosting
- Fix 4: Implement Document Filtering

## 📖 Usage Examples

### Test a Query
```bash
./debug-rag.sh query "what is the revenue of TCS?"
```

### Full Pipeline Trace
```bash
./debug-rag.sh trace "your question here"
./debug-rag.sh trace "your question" session-id-123
```

### Analyze Documents
```bash
./debug-rag.sh docs
./debug-rag.sh chunks
```

### System Checks
```bash
./debug-rag.sh pgvector
./debug-rag.sh full  # All checks
```

### Test Embeddings
```bash
./debug-rag.sh embedding "test text"
```

## 🔍 What the Debug Script Shows

### Query Classification
```
Should Skip RAG: False
✓ Query classified as RETRIEVAL
```

### Embedding Generation
```
✓ Embedding generated in 0.123s
Embedding dimension: 384
Norm (L2): 1.000000
```

### Vector Search Results
```
Result 1:
  Document: TCS_Financial_Report.pdf
  Similarity Score: 0.8734
  Quality: Excellent match (>0.7)
```

### Issues Detected
```
⚠ Document has chunks but NO embeddings!
✗ Query matches direct pattern: "tell me about yourself"
⚠ Low similarity scores - all results <0.3
```

## 🎯 Common Issues Debugged

1. **Wrong documents retrieved**
   - Shows which documents match
   - Shows similarity scores
   - Identifies keyword confusion

2. **Query classification problems**
   - Shows if query skips RAG incorrectly
   - Shows matched patterns
   - Identifies classification logic issues

3. **Embedding issues**
   - Detects missing embeddings
   - Shows embedding statistics
   - Validates embedding model

4. **Threshold problems**
   - Shows actual similarity scores
   - Compares to thresholds
   - Recommends adjustments

## 📊 Output Interpretation

### Similarity Scores
- **0.9-1.0**: Nearly identical (excellent)
- **0.7-0.9**: Highly relevant (excellent)
- **0.5-0.7**: Relevant (good)
- **0.3-0.5**: Somewhat relevant (fair)
- **0.0-0.3**: Not relevant (poor)

### Query Classification
- ✓ **Should Skip RAG: False** for factual questions
- ✗ **Should Skip RAG: True** for factual questions (BAD)

### Document Status
- ✓ **Processed: True, Has Embeddings: Yes**
- ✗ **Processed: False** or **Has Embeddings: No**

## 🔧 Integration with Existing Tools

Works alongside:
- `diagnose-backend.sh`
- `diagnose-documents.sh`
- `check-documents.sh`
- `validate-services.sh`

But provides much deeper RAG-specific analysis.

## 📚 Documentation

- **RAG_DEBUGGING_GUIDE.md**: Comprehensive guide (600+ lines)
- **DEBUG_QUICK_REFERENCE.md**: Quick commands and fixes
- **This file**: Overview and quick start

## 🆘 Troubleshooting

### Script won't run
```bash
chmod +x debug-rag.sh
docker-compose restart backend
```

### Import errors
```bash
docker-compose exec backend pip install numpy sentence-transformers
```

### Permission denied
```bash
chmod +x debug-rag.sh
```

## ✅ Expected Workflow

1. Run full diagnostic: `./debug-rag.sh full`
2. Test problematic query: `./debug-rag.sh trace "query"`
3. Identify root cause from output
4. Apply fix from RAG_DEBUGGING_GUIDE.md
5. Verify: `./debug-rag.sh trace "query"` again

## 🎓 Learning Resources

1. Start with **DEBUG_QUICK_REFERENCE.md** for commands
2. Read **RAG_DEBUGGING_GUIDE.md** for understanding
3. Use **debug-rag.sh** for actual debugging
4. Check output against interpretation guide

## 💡 Pro Tips

- Always run `./debug-rag.sh docs` first
- Use `--full-trace` for maximum detail
- Compare embeddings of similar queries
- Check logs: `docker-compose logs -f backend`
- Enable DEBUG logging for more info

---

## Example: Debugging TCS Revenue Query

```bash
# 1. Check system status
./debug-rag.sh full

# 2. Trace the query
./debug-rag.sh trace "what is the revenue of TCS in Sep 2025?"

# 3. Check if TCS docs exist
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT filename FROM documents WHERE filename ILIKE '%TCS%';"

# 4. Check why Thoothukudi matches
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT content FROM document_chunks
   WHERE content ILIKE '%TCS%'
   AND document_id IN (SELECT id FROM documents WHERE filename LIKE '%Thoothukudi%')
   LIMIT 3;"

# 5. Apply fixes from RAG_DEBUGGING_GUIDE.md

# 6. Verify fix
./debug-rag.sh trace "what is the revenue of TCS in Sep 2025?"
```

---

**Created:** 2025-11-15
**Purpose:** Comprehensive RAG pipeline debugging toolkit
**Status:** Ready to use ✅
