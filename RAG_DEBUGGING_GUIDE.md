# RAG Pipeline Debugging Guide

> **Purpose**: Step-by-step guide to debug RAG pipeline issues using the debug tools

---

## 🔍 Overview

This guide helps you diagnose and fix issues with the RAG (Retrieval-Augmented Generation) pipeline, including:

- Query classification problems (queries being treated as direct AI questions)
- Document retrieval issues (wrong documents being retrieved)
- Embedding generation problems
- Vector similarity search issues
- Chunking and threshold problems

---

## 🛠️ Debug Tools

### 1. `debug_rag_pipeline.py` - Main Debug Script

Comprehensive Python script that traces the entire RAG pipeline.

**Features:**
- Query classification analysis
- Embedding generation testing
- Document and chunk analysis
- Vector similarity search testing
- Full pipeline trace
- pgvector installation check

### 2. `debug-rag.sh` - Easy Wrapper Script

Simple bash wrapper for common debugging tasks.

**Quick Commands:**
```bash
./debug-rag.sh docs          # Analyze all documents
./debug-rag.sh chunks        # Analyze chunks
./debug-rag.sh pgvector      # Check pgvector
./debug-rag.sh query "text"  # Test a query
./debug-rag.sh full          # Run all checks
```

---

## 🚀 Quick Start - Debugging the TCS Issue

Based on your screenshot, the issue is that when asking "what is the revenue of TCS in Sep 2025?", the system is retrieving a Wikipedia article about Thoothukudi (a city) instead of TCS financial documents.

### Step 1: Check What Documents Exist

```bash
./debug-rag.sh docs
```

**What to look for:**
- Are there TCS-related documents in the database?
- Are they processed?
- Do they have embeddings?

**Expected Output:**
```
Document 1:
  Filename: TCS_Q2_2025_Results.pdf
  Type: pdf
  Processed: True
  Chunks: 45
  Chunks with Embeddings: 45
```

**If you see:**
- ❌ No TCS documents → Need to upload TCS financial documents
- ❌ `Processed: False` → Documents failed to process
- ❌ `Chunks: 0` → Chunking failed
- ❌ `Chunks with Embeddings: 0` → Embedding generation failed

### Step 2: Test the Problematic Query

```bash
./debug-rag.sh trace "what is the revenue of TCS in Sep 2025?"
```

**What this does:**
1. Analyzes query classification
2. Generates query embedding
3. Searches for similar chunks
4. Shows what the RAG service returns

**Look for these issues:**

#### Issue 1: Query Classification
```
Should Skip RAG: True
Query classified as NON-RETRIEVAL
```
**Problem:** System thinks this is a direct AI question
**Solution:** Modify query classification logic in `rag_service.py`

#### Issue 2: Low Similarity Scores
```
Result 1:
  Document: scraped_en.wikipedia.org_7e54833d.txt
  Similarity Score: 0.3214
  Quality: Fair match (>0.3)
```
**Problem:** Wrong document retrieved with low score
**Solution:**
- Upload correct TCS documents
- Adjust similarity threshold
- Check embedding quality

#### Issue 3: Wrong Documents Retrieved
```
Result 1:
  Document: Thoothukudi_Wikipedia.txt
  Similarity Score: 0.95
```
**Problem:** High score but wrong document
**Solution:** Check if "TCS" in Thoothukudi article is confusing the search

### Step 3: Analyze Document Chunks

```bash
./debug-rag.sh chunks
```

**What to look for:**
- Chunk sizes (should be 800 ± overlap)
- Are chunks meaningful or broken?
- Do chunks contain searchable content?

**Example Good Chunk:**
```
Chunk 1:
  Document: TCS_Financial_Report.pdf
  Length: 756
  Has Embedding: Yes
  Preview: "Tata Consultancy Services reported revenue of $7.2B..."
```

**Example Bad Chunk:**
```
Chunk 1:
  Document: TCS_Financial_Report.pdf
  Length: 45
  Has Embedding: No
  Preview: "Page 1..."
```

### Step 4: Check Embedding Quality

```bash
./debug-rag.sh embedding "TCS revenue September 2025"
```

**What to look for:**
```
Embedding dimension: 384
Embedding stats:
  Mean: 0.015234
  Std Dev: 0.089432
  Norm (L2): 1.0000
```

**Red flags:**
- Dimension not 384
- All zeros
- Very low norm (<0.5)
- Mean/std outside expected range

---

## 🔬 Detailed Debugging Scenarios

### Scenario 1: "TCS" Query Returns Thoothukudi Wikipedia

**Symptoms:**
- Query: "what is the revenue of TCS?"
- Retrieved: Wikipedia article about Thoothukudi city
- Similarity: High (0.95+)

**Root Cause:**
The Thoothukudi Wikipedia article likely contains "TCS" in a different context (e.g., "TCS iON building" or similar), causing semantic confusion.

**Debugging Steps:**

1. **Check what's in the Thoothukudi document:**
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT content FROM document_chunks
   WHERE document_id IN (
     SELECT id FROM documents
     WHERE filename LIKE '%Thoothukudi%'
   )
   AND content ILIKE '%TCS%'
   LIMIT 5;"
```

2. **Check if TCS financial docs exist:**
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT filename, processed FROM documents
   WHERE filename ILIKE '%TCS%'
   OR filename ILIKE '%Tata%'
   OR filename ILIKE '%financial%';"
```

3. **Compare embeddings:**
```bash
# Test both queries
./debug-rag.sh embedding "TCS revenue"
./debug-rag.sh embedding "Thoothukudi city"
```

**Solutions:**

**A. If TCS financial docs don't exist:**
- Upload TCS earnings reports, financial statements
- Upload from official TCS investor relations site

**B. If both documents exist:**
- Check document ranking in search results
- May need to boost exact keyword matches
- Consider implementing document metadata filtering

**C. Implement keyword boosting:**
```python
# In rag_service.py
if "revenue" in query.lower() and "TCS" in query.upper():
    # Boost documents with financial keywords
    filters.append("filename ILIKE '%financial%' OR filename ILIKE '%earnings%'")
```

### Scenario 2: Query Classification Skipping Retrieval

**Symptoms:**
- Query should search documents but doesn't
- Response is generic AI answer
- No sources shown

**Debugging:**
```bash
./debug-rag.sh trace "tell me about yourself"
```

**Look for:**
```
Should Skip RAG: True
Query classified as NON-RETRIEVAL
```

**Root Cause:**
Query matches a pattern in the "skip RAG" logic.

**Check the code:**
```bash
docker-compose exec backend grep -n "should_skip_rag" /app/app/services/rag_service.py -A 20
```

**Common patterns that skip RAG:**
- "who are you"
- "what are you"
- "tell me about yourself"
- "how do you work"

**Solution:**
Modify `rag_service.py` to be more precise:
```python
async def should_skip_rag(self, query: str) -> bool:
    """Determine if query should skip RAG and use direct AI response"""
    query_lower = query.lower().strip()

    # Only skip very specific meta questions about the AI itself
    direct_patterns = [
        "who are you",
        "what are you",
        "what can you do",
        "how do you work",
        "explain yourself"
    ]

    # Exact match only, don't be too aggressive
    for pattern in direct_patterns:
        if query_lower == pattern:  # Exact match
            return True

    return False
```

### Scenario 3: No Documents Found

**Symptoms:**
```
Total Documents: 0
No documents found in database!
```

**Solutions:**

1. **Upload documents via UI:**
   - Go to http://localhost:3001
   - Use file upload
   - Wait for processing

2. **Upload via API:**
```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@TCS_Q2_2025.pdf" \
  -F "session_id=test123"
```

3. **Check processing errors:**
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT filename, processing_error FROM documents
   WHERE processed = false;"
```

### Scenario 4: Documents Have No Embeddings

**Symptoms:**
```
Chunks: 45
Chunks with Embeddings: 0
⚠ Document has chunks but NO embeddings!
```

**Root Cause:**
- Embedding service failed
- Model download failed
- Out of memory

**Debugging:**

1. **Check embedding service:**
```bash
docker-compose logs backend | grep -i "embedding"
```

2. **Test embedding manually:**
```bash
./debug-rag.sh embedding "test"
```

3. **Check embedding model:**
```bash
docker-compose exec backend python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
embedding = model.encode('test')
print(f'Dimension: {len(embedding)}')
print(f'First 5 values: {embedding[:5]}')
"
```

**Solutions:**

1. **Regenerate embeddings:**
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "UPDATE documents SET processed = false WHERE id = 'YOUR_DOC_ID';"

# Restart backend to reprocess
docker-compose restart backend
```

2. **Check memory:**
```bash
docker stats backend
```

If OOM, increase memory in docker-compose.yml:
```yaml
backend:
  deploy:
    resources:
      limits:
        memory: 4G
```

### Scenario 5: Low Similarity Scores

**Symptoms:**
```
Result 1:
  Similarity Score: 0.1234
  Quality: Poor match (<0.3)
```

**Root Cause:**
- Query and document embeddings are semantically distant
- Embedding model not suitable for domain
- Documents don't contain relevant info

**Debugging:**

1. **Check actual document content:**
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT SUBSTRING(content, 1, 500) FROM document_chunks
   WHERE document_id IN (
     SELECT id FROM documents WHERE filename LIKE '%TCS%'
   )
   LIMIT 5;"
```

2. **Test different query phrasings:**
```bash
./debug-rag.sh trace "TCS Q2 2025 revenue"
./debug-rag.sh trace "Tata Consultancy Services quarterly earnings"
./debug-rag.sh trace "TCS financial results September 2025"
```

3. **Compare embeddings:**
```python
# In Python
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')

query_emb = model.encode("TCS revenue")
doc_emb = model.encode("Tata Consultancy Services reported revenue of $7.2B")

similarity = np.dot(query_emb, doc_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(doc_emb))
print(f"Similarity: {similarity}")
```

**Solutions:**

1. **Adjust similarity threshold:**
In `rag_service.py`:
```python
# Lower threshold if getting no results
similarity_threshold = 0.3  # Was 0.5
```

2. **Use hybrid search (keyword + vector):**
```python
# Combine vector search with keyword search
sql = """
SELECT ... FROM document_chunks
WHERE
  (embedding <=> :query_embedding) < 0.7
  AND (
    content ILIKE '%TCS%'
    OR content ILIKE '%Tata Consultancy%'
  )
ORDER BY embedding <=> :query_embedding
"""
```

3. **Consider different embedding model:**
```python
# For financial/business domain
model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
```

---

## 📊 Understanding Output

### Query Classification Output

```
========================================
    QUERY CLASSIFICATION ANALYSIS
========================================

Query: "what is the revenue of TCS?"
Should Skip RAG: False
✓ Query classified as RETRIEVAL - will search documents
```

**Good:** Should Skip RAG = False for factual questions
**Bad:** Should Skip RAG = True for factual questions

### Embedding Output

```
========================================
      QUERY EMBEDDING ANALYSIS
========================================

Generating embedding for query: "what is the revenue of TCS?"
✓ Embedding generated in 0.123s
Embedding dimension: 384
Embedding type: ndarray
Embedding stats:
  Mean: 0.015234
  Std Dev: 0.089432
  Min: -0.456789
  Max: 0.567890
  Norm (L2): 1.000000
```

**Good indicators:**
- ✓ Dimension: 384
- ✓ Norm close to 1.0
- ✓ Mean near 0
- ✓ Std Dev 0.05-0.15

**Bad indicators:**
- ✗ All zeros
- ✗ Norm < 0.5
- ✗ Very high/low mean

### Vector Search Output

```
========================================
    VECTOR SIMILARITY SEARCH
========================================

Result 1:
  Document: TCS_Q2_2025_Results.pdf
  Chunk Index: 12
  Similarity Score: 0.8734
  Quality: Excellent match (>0.7)
  Content: "TCS reported consolidated revenue of ₹62,613 crore..."
```

**Similarity Score Guide:**
- **0.9 - 1.0**: Nearly identical (excellent)
- **0.7 - 0.9**: Highly relevant (excellent)
- **0.5 - 0.7**: Relevant (good)
- **0.3 - 0.5**: Somewhat relevant (fair)
- **0.0 - 0.3**: Not relevant (poor)

---

## 🔧 Common Fixes

### Fix 1: Update Query Classification

**File:** `backend/app/services/rag_service.py`

```python
async def should_skip_rag(self, query: str) -> bool:
    """Determine if query should skip RAG"""
    query_lower = query.lower().strip()

    # Only exact matches for meta questions
    meta_questions = {
        "who are you",
        "what are you",
        "what can you do",
        "tell me about yourself"
    }

    # Exact match only
    if query_lower in meta_questions:
        return True

    # Don't skip for questions with specific keywords
    factual_keywords = ["revenue", "profit", "earnings", "financial", "results", "quarter"]
    if any(keyword in query_lower for keyword in factual_keywords):
        return False

    return False
```

### Fix 2: Add Keyword Boosting

```python
async def search_documents(self, query: str, top_k: int = 5):
    """Search with keyword boosting"""

    # Generate embedding
    query_embedding = await self.embedding_service.generate_embedding(query)

    # Extract important keywords
    keywords = self.extract_keywords(query)

    # Build search with keyword filter
    keyword_filter = ""
    if keywords:
        conditions = [f"content ILIKE '%{kw}%'" for kw in keywords]
        keyword_filter = f"AND ({' OR '.join(conditions)})"

    sql = f"""
        SELECT ...
        FROM document_chunks c
        WHERE c.embedding IS NOT NULL
        {keyword_filter}
        ORDER BY c.embedding <=> :query_embedding
        LIMIT :top_k
    """

    return results
```

### Fix 3: Adjust Similarity Thresholds

```python
# In rag_service.py
class RAGService:
    # Configurable thresholds
    SIMILARITY_THRESHOLD = 0.3  # Minimum to consider
    EXCELLENT_THRESHOLD = 0.7   # High quality match
    GOOD_THRESHOLD = 0.5        # Decent match
```

### Fix 4: Implement Document Filtering

```python
async def query_with_rag(self, request: QueryRequest):
    """Query with document type filtering"""

    # Detect query type
    if self.is_financial_query(request.query):
        # Only search financial documents
        document_filter = """
            AND d.filename ILIKE ANY(ARRAY['%financial%', '%earnings%', '%results%', '%report%'])
        """
    else:
        document_filter = ""

    # Search with filter
    results = await self.search_documents(
        query=request.query,
        document_filter=document_filter
    )
```

---

## 🎯 Recommended Debugging Workflow

For the TCS issue specifically:

### Phase 1: Identify the Problem
```bash
# 1. Check what documents exist
./debug-rag.sh docs

# 2. Run full trace
./debug-rag.sh trace "what is the revenue of TCS in Sep 2025?"

# 3. Check chunks
./debug-rag.sh chunks
```

### Phase 2: Analyze Root Cause
```bash
# Check if TCS documents exist
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT filename FROM documents WHERE filename ILIKE '%TCS%' OR filename ILIKE '%Tata%';"

# Check why Thoothukudi is matching
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT content FROM document_chunks
   WHERE document_id IN (SELECT id FROM documents WHERE filename LIKE '%Thoothukudi%')
   AND content ILIKE '%TCS%';"
```

### Phase 3: Implement Fix

**If no TCS documents:**
1. Upload TCS financial reports
2. Wait for processing
3. Verify with `./debug-rag.sh docs`

**If wrong documents retrieved:**
1. Implement keyword boosting (Fix 2)
2. Add document type filtering (Fix 4)
3. Adjust similarity thresholds (Fix 3)

**If query classification wrong:**
1. Update `should_skip_rag()` (Fix 1)
2. Add factual question detection

### Phase 4: Verify Fix
```bash
# Test the query again
./debug-rag.sh trace "what is the revenue of TCS in Sep 2025?"

# Should now show:
# - Correct documents retrieved
# - High similarity scores
# - Relevant content
```

---

## 📝 Logging and Monitoring

### Enable Debug Logging

**In docker-compose.yml:**
```yaml
backend:
  environment:
    - LOG_LEVEL=DEBUG
```

**Or in .env:**
```
LOG_LEVEL=DEBUG
```

### Watch Logs in Real-Time
```bash
# All backend logs
docker-compose logs -f backend

# Just RAG-related
docker-compose logs -f backend | grep -i "rag\|embedding\|similarity"

# Just errors
docker-compose logs -f backend | grep -i "error\|exception"
```

### Check Query History
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT
     m.content as query,
     m.sources,
     m.model_used,
     m.created_at
   FROM messages m
   WHERE m.role = 'user'
   ORDER BY m.created_at DESC
   LIMIT 10;"
```

---

## 🆘 Troubleshooting

### Script Won't Run

```bash
# Make executable
chmod +x debug-rag.sh

# Install dependencies
docker-compose exec backend pip install numpy sentence-transformers
```

### Import Errors
```bash
# Check Python path
docker-compose exec backend python -c "import sys; print('\n'.join(sys.path))"

# Reinstall dependencies
docker-compose exec backend pip install -r /app/requirements.txt
```

### Database Connection Errors
```bash
# Check database is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres pg_isready

# Check DATABASE_URL
docker-compose exec backend env | grep DATABASE_URL
```

---

## 📚 Additional Resources

- **CLAUDE.md**: Full project documentation
- **MEMORY_HIERARCHY_GUIDE.md**: RAG architecture details
- **STATUS.md**: Current project status
- **backend/app/services/rag_service.py**: RAG service implementation
- **backend/app/services/embedding_service.py**: Embedding generation

---

## ✅ Success Checklist

After debugging, verify:

- [ ] `./debug-rag.sh docs` shows TCS documents
- [ ] All documents have `Processed: True`
- [ ] All chunks have embeddings
- [ ] `./debug-rag.sh pgvector` passes
- [ ] Test query returns correct documents
- [ ] Similarity scores > 0.5 for relevant docs
- [ ] Query classification is correct
- [ ] Sources shown in UI match expected documents

---

**End of RAG Debugging Guide**
