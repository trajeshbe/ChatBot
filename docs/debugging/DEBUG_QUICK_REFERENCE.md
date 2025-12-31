# RAG Debug Quick Reference Card

## 🚀 Quick Commands

```bash
# Check system status
./debug-rag.sh docs              # List all documents
./debug-rag.sh chunks            # Analyze chunks
./debug-rag.sh pgvector          # Check pgvector
./debug-rag.sh full              # Run all diagnostics

# Test specific queries
./debug-rag.sh query "your question"
./debug-rag.sh trace "your question"  # Full trace
./debug-rag.sh trace "your question" session123  # With session

# Test embeddings
./debug-rag.sh embedding "test text"
```

## 🔍 For the TCS Issue

### Step 1: Check Documents
```bash
./debug-rag.sh docs
```
**Look for:**
- ✓ TCS financial documents exist
- ✓ Processed = True
- ✓ Has embeddings

### Step 2: Trace the Query
```bash
./debug-rag.sh trace "what is the revenue of TCS in Sep 2025?"
```
**Look for:**
- ✗ Should Skip RAG: True (BAD - should be False)
- ✗ Wrong document retrieved (Thoothukudi instead of TCS)
- ✗ Low similarity scores (<0.5)

### Step 3: Check Database Directly
```bash
# Check TCS documents
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT filename, processed FROM documents WHERE filename ILIKE '%TCS%';"

# Check why Thoothukudi matches
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT content FROM document_chunks
   WHERE document_id IN (SELECT id FROM documents WHERE filename LIKE '%Thoothukudi%')
   AND content ILIKE '%TCS%'
   LIMIT 3;"
```

## 🎯 Common Issues & Fixes

### Issue: No Documents
```bash
# Upload via curl
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@TCS_Report.pdf"
```

### Issue: Query Classified Wrong
**File:** `backend/app/services/rag_service.py`
```python
async def should_skip_rag(self, query: str) -> bool:
    # Be more conservative - only skip obvious meta questions
    meta_questions = {"who are you", "what are you"}
    return query.lower().strip() in meta_questions
```

### Issue: Wrong Documents Retrieved
**Add keyword boosting:**
```python
# In rag_service.py search function
if "TCS" in query.upper() and "revenue" in query.lower():
    sql += " AND content ILIKE '%TCS%' AND content ILIKE '%revenue%'"
```

### Issue: Low Similarity
**Lower threshold:**
```python
# In rag_service.py
SIMILARITY_THRESHOLD = 0.3  # Was 0.5
```

## 📊 Interpreting Results

### Good Query Classification
```
Should Skip RAG: False
✓ Query classified as RETRIEVAL - will search documents
```

### Bad Query Classification
```
Should Skip RAG: True
⚠ Query classified as NON-RETRIEVAL
```

### Good Search Results
```
Result 1:
  Document: TCS_Financial_Report.pdf
  Similarity Score: 0.8734
  Quality: Excellent match (>0.7)
```

### Bad Search Results
```
Result 1:
  Document: Thoothukudi_Wikipedia.txt
  Similarity Score: 0.3214
  Quality: Fair match (>0.3)
```

## 🔧 Emergency Fixes

### Regenerate All Embeddings
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "UPDATE document_chunks SET embedding = NULL;"

docker-compose restart backend
```

### Clear and Restart
```bash
docker-compose down -v
docker-compose up -d
./setup-database.sh
```

### View Logs
```bash
docker-compose logs -f backend | grep -i "rag\|embedding"
```

## 📈 Expected Flow

1. **Query Input:** "what is the revenue of TCS?"
2. **Classification:** Should Skip RAG = False
3. **Embedding:** Generate 384-dim vector
4. **Search:** Find top 5 similar chunks
5. **Filter:** Similarity > 0.5
6. **Rank:** TCS docs should rank higher than Thoothukudi
7. **Return:** Answer with TCS sources

## ⚠️ Red Flags

- ❌ Should Skip RAG = True for factual questions
- ❌ No TCS documents in results
- ❌ Thoothukudi ranking higher than TCS docs
- ❌ All similarity scores < 0.3
- ❌ Chunks with no embeddings
- ❌ Documents not processed

## ✅ Green Flags

- ✓ Should Skip RAG = False for factual questions
- ✓ TCS documents retrieved first
- ✓ Similarity scores > 0.7
- ✓ All chunks have embeddings
- ✓ Correct sources in response

---

**Quick Tip:** Run `./debug-rag.sh full` first to get complete picture!
