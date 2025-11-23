# State-of-the-Art Retrieval System Roadmap

**Date**: 2025-11-23
**Status**: 🟢 Architecture Fixed - Ready for Advanced Improvements

---

## ✅ Current State (What's Working)

### ✅ Implemented & Working
1. **Hybrid Search (80/20 Semantic/Keyword)** - Implemented in `document_service.py`
2. **SQL Injection Prevention** - Keywords sanitized, parameterized queries
3. **Configurable Weights** - Can be overridden per request via API
4. **Memory Hierarchy** - Short-term (session) + Long-term (global) retrieval
5. **Cascading Fallback** - Automatic threshold lowering if no results
6. **Quality-Based Routing** - NEW! RAG first, classification only if quality low
7. **Conversation Context** - Multi-turn coherence

### ⚠️ Partially Implemented
- **Eval Metrics** - Calculated but UI display needs restoration
- **Semantic Weight in UI** - Backend supports it, but **UI config not yet exposed**

### ❌ Not Yet Implemented (Priority Improvements)
- Cross-encoder reranking
- Dynamic chunking by document type
- Versioned cache keys
- Guardrails (prompt injection filters, URL allowlists)

---

## 🚀 State-of-the-Art Retrieval Roadmap

### Phase 1: Production Hardening (Priority: HIGH)

#### 1.1 UI Configuration for Semantic Weights ✅ **TODO**

**Current State**: Backend accepts `semantic_weight` and `keyword_weight` parameters, but UI doesn't expose them.

**Implementation**:
```typescript
// frontend/src/components/RAGSettings.tsx
<div className="setting-group">
  <label>Semantic Weight (0.0 - 1.0)</label>
  <input
    type="range"
    min="0"
    max="1"
    step="0.05"
    value={semanticWeight}
    onChange={(e) => setSemanticWeight(parseFloat(e.target.value))}
  />
  <span>{semanticWeight.toFixed(2)}</span>
</div>

<div className="setting-group">
  <label>Keyword Weight</label>
  <span>{(1 - semanticWeight).toFixed(2)} (auto-calculated)</span>
</div>
```

**API Integration**:
```typescript
const response = await axios.post('/api/v1/query', {
  query: queryText,
  semantic_weight: semanticWeight,  // From UI slider
  keyword_weight: 1 - semanticWeight,
  // ... other params
});
```

#### 1.2 Restore Eval Metrics Display ✅ **TODO**

**File**: `frontend/src/components/ChatInterface.tsx`

**Add Below Chat Response**:
```typescript
{message.quality_metrics && (
  <div className="eval-metrics">
    <div className="metric">
      <span className="label">Quality:</span>
      <span className={`value ${getQualityClass(message.quality_metrics.rag_score)}`}>
        {message.quality_metrics.quality_level}
        ({message.quality_metrics.rag_score?.toFixed(2) || 'N/A'})
      </span>
    </div>
    <div className="metric">
      <span className="label">Sources:</span>
      <span className="value">{message.num_sources}</span>
    </div>
    <div className="metric">
      <span className="label">Latency:</span>
      <span className="value">{message.latency_ms?.toFixed(0)}ms</span>
    </div>
  </div>
)}
```

#### 1.3 Versioned Cache Keys 🔧 **CRITICAL**

**Problem**: Changing embedding models invalidates cache but doesn't clear it.

**Current** (`rag_service.py`):
```python
cache_key = f"query:{hash(query_text)}"
```

**Fixed**:
```python
from app.core.config import settings

cache_key = f"query:{settings.EMBEDDING_MODEL}:v{settings.EMBEDDING_DIMENSION}:{hash(query_text)}"

# Add cache version to settings
CACHE_VERSION: str = "v1"  # Increment on major changes
cache_key = f"{settings.CACHE_VERSION}:query:{settings.EMBEDDING_MODEL}:{hash(query_text)}"
```

---

### Phase 2: Advanced Retrieval (ChatGPT/Claude Level)

#### 2.1 Cross-Encoder Reranking 🎯 **HIGH IMPACT**

**Why**: Initial vector search is fast but noisy. Reranking refines top results.

**Implementation**:
```python
# backend/app/services/reranker_service.py
from sentence_transformers import CrossEncoder

class RerankerService:
    def __init__(self):
        # Load cross-encoder model (more expensive but more accurate)
        self.model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

    async def rerank(
        self,
        query: str,
        chunks: List[Dict],
        top_k: int = 5
    ) -> List[Dict]:
        """
        Rerank chunks using cross-encoder for higher precision.
        """
        if not chunks:
            return []

        # Create query-document pairs
        pairs = [(query, chunk['content']) for chunk in chunks]

        # Score all pairs
        scores = self.model.predict(pairs)

        # Combine scores with chunks
        for chunk, score in zip(chunks, scores):
            chunk['rerank_score'] = float(score)

        # Sort by rerank score and return top_k
        reranked = sorted(chunks, key=lambda x: x['rerank_score'], reverse=True)
        return reranked[:top_k]

reranker_service = RerankerService()
```

**Integration** in `rag_service_enhanced.py`:
```python
# After hybrid search (line ~145)
long_term_chunks = await document_service.search_similar_chunks(...)

# NEW: Rerank before combining
if long_term_chunks and len(long_term_chunks) > 3:
    logger.info(f"🔄 Reranking {len(long_term_chunks)} chunks...")
    long_term_chunks = await reranker_service.rerank(
        query=query_text,
        chunks=long_term_chunks,
        top_k=_top_k
    )
    logger.info(f"✅ Reranked to {len(long_term_chunks)} high-precision chunks")
```

**Expected Improvement**: +15-25% answer accuracy

#### 2.2 Dynamic Chunking by Document Type 📄

**Current**: Fixed 800-char chunks for all documents

**Problem**: FAQs need shorter chunks, narratives need longer chunks

**Implementation**:
```python
# backend/app/services/chunking_service.py
from enum import Enum

class DocType(Enum):
    FAQ = "faq"
    NARRATIVE = "narrative"
    TECHNICAL = "technical"
    UI_TEXT = "ui_text"
    CODE = "code"

CHUNKING_CONFIG = {
    DocType.FAQ: {
        "chunk_size": 400,
        "chunk_overlap": 50,
        "separators": ["\n\nQ:", "\n\nA:", "\n\n", "\n"]
    },
    DocType.NARRATIVE: {
        "chunk_size": 1200,
        "chunk_overlap": 200,
        "separators": ["\n\n", "\n", ". ", "! ", "? "]
    },
    DocType.TECHNICAL: {
        "chunk_size": 800,
        "chunk_overlap": 150,
        "separators": ["\n\n## ", "\n\n### ", "\n\n", "\n"]
    },
    DocType.UI_TEXT: {
        "chunk_size": 300,
        "chunk_overlap": 50,
        "separators": ["\n", ". "]
    },
    DocType.CODE: {
        "chunk_size": 1000,
        "chunk_overlap": 100,
        "separators": ["\nclass ", "\ndef ", "\n\n", "\n"]
    }
}

def detect_doc_type(content: str, filename: str) -> DocType:
    """Auto-detect document type from content and filename."""
    # FAQ detection
    if content.count("Q:") > 3 or content.count("A:") > 3:
        return DocType.FAQ

    # Code detection
    if filename.endswith(('.py', '.js', '.ts', '.java', '.cpp')):
        return DocType.CODE

    # Technical documentation
    if content.count("##") > 5 or content.count("###") > 5:
        return DocType.TECHNICAL

    # Short UI text
    if len(content) < 1000 and "\n" not in content:
        return DocType.UI_TEXT

    # Default to narrative
    return DocType.NARRATIVE

def chunk_document(content: str, filename: str) -> List[str]:
    """Chunk document based on auto-detected type."""
    doc_type = detect_doc_type(content, filename)
    config = CHUNKING_CONFIG[doc_type]

    # Store doc_type and chunking_version in metadata
    metadata = {
        "doc_type": doc_type.value,
        "chunking_version": "v2",  # Increment on config changes
        "chunk_config": config
    }

    # Chunk with appropriate settings
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config["chunk_size"],
        chunk_overlap=config["chunk_overlap"],
        separators=config["separators"]
    )

    return splitter.split_text(content), metadata
```

**Expected Improvement**: +10-20% retrieval precision

#### 2.3 Query Reformulation & Expansion 🔄

**Why**: User queries are often ambiguous or incomplete.

**Implementation**:
```python
# backend/app/services/query_reformulation.py
class QueryReformulator:
    async def reformulate(self, query: str) -> Dict[str, List[str]]:
        """
        Generate multiple query variations for better recall.
        """
        # 1. Synonym expansion
        synonyms = await self._expand_synonyms(query)

        # 2. LLM-based reformulation
        reformulated = await llm_service.generate(
            prompt=f"Reformulate this question in 3 different ways:\n{query}",
            max_tokens=150
        )

        # 3. Question decomposition
        sub_queries = await self._decompose_question(query)

        return {
            "original": [query],
            "synonyms": synonyms,
            "reformulated": reformulated,
            "sub_queries": sub_queries
        }

    async def multi_query_search(
        self,
        query_variants: Dict[str, List[str]],
        top_k: int = 5
    ) -> List[Dict]:
        """
        Search with all query variants and deduplicate results.
        """
        all_chunks = []

        for variant_type, queries in query_variants.items():
            for q in queries:
                embedding = await embedding_service.get_embedding(q)
                chunks = await document_service.search_similar_chunks(
                    query_embedding=embedding,
                    top_k=top_k // len(queries)  # Split quota
                )
                all_chunks.extend(chunks)

        # Deduplicate and re-score
        return self._deduplicate_and_rerank(all_chunks, top_k)
```

**Expected Improvement**: +20-30% recall

#### 2.4 Contextual Compression 📝

**Why**: Retrieve large chunks, extract only relevant sentences.

**Implementation**:
```python
# backend/app/services/contextual_compressor.py
from transformers import pipeline

class ContextualCompressor:
    def __init__(self):
        self.qa_model = pipeline(
            "question-answering",
            model="deepset/roberta-base-squad2"
        )

    async def compress(
        self,
        query: str,
        chunks: List[Dict],
        max_compressed_length: int = 200
    ) -> List[Dict]:
        """
        Extract only relevant sentences from each chunk.
        """
        compressed_chunks = []

        for chunk in chunks:
            # Extract most relevant sentences
            result = self.qa_model(
                question=query,
                context=chunk['content']
            )

            # Get context around answer
            answer_start = result['start']
            answer_end = result['end']

            # Expand to full sentences
            expanded = self._expand_to_sentences(
                chunk['content'],
                answer_start,
                answer_end,
                max_length=max_compressed_length
            )

            compressed_chunks.append({
                **chunk,
                'original_content': chunk['content'],
                'content': expanded,
                'compression_ratio': len(expanded) / len(chunk['content'])
            })

        return compressed_chunks
```

**Expected Improvement**: -30% token usage, +10% answer quality

#### 2.5 Multi-Vector Retrieval (Late Interaction) 🔬

**State-of-the-Art**: ColBERT-style late interaction

**Why**: Instead of single vector per chunk, use multiple vectors for better precision.

**Implementation** (Advanced):
```python
# Requires model upgrade to ColBERT
from colbert import Indexer, Searcher

class MultiVectorRetriever:
    def __init__(self):
        self.indexer = Indexer(checkpoint="colbert-ir/colbertv2.0")

    async def index_document(self, chunks: List[str]):
        """Index document with multiple vectors per chunk."""
        self.indexer.index(chunks, name="multi_vector_index")

    async def search(self, query: str, top_k: int = 5):
        """Late interaction search."""
        searcher = Searcher(index="multi_vector_index")
        results = searcher.search(query, k=top_k)
        return results
```

**Expected Improvement**: +30-40% precision (but higher latency)

---

### Phase 3: Guardrails & Safety 🛡️

#### 3.1 Prompt Injection Detection 🚨

**Implementation**:
```python
# backend/app/services/guardrails/prompt_injection_filter.py
import re

INJECTION_PATTERNS = [
    r"ignore (previous|all|above) instructions",
    r"disregard (previous|all|above) (instructions|rules)",
    r"forget (everything|all|previous)",
    r"system:.*?admin",
    r"<\s*script\s*>",
    r"eval\s*\(",
    r"exec\s*\(",
]

class PromptInjectionFilter:
    def detect(self, query: str) -> Dict:
        """Detect potential prompt injection attempts."""
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return {
                    "is_injection": True,
                    "pattern": pattern,
                    "severity": "high"
                }

        return {"is_injection": False}

    def sanitize(self, query: str) -> str:
        """Remove potentially malicious patterns."""
        sanitized = query
        for pattern in INJECTION_PATTERNS:
            sanitized = re.sub(pattern, "[FILTERED]", sanitized, flags=re.IGNORECASE)
        return sanitized
```

#### 3.2 URL Allowlist for Scraping 🔒

**Implementation**:
```python
# backend/app/services/guardrails/url_validator.py
from urllib.parse import urlparse

ALLOWED_DOMAINS = [
    "wikipedia.org",
    "github.com",
    "stackoverflow.com",
    # Add trusted domains
]

BLOCKED_DOMAINS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    # Internal/private IPs
]

def validate_url(url: str) -> Dict:
    """Validate URL before scraping."""
    parsed = urlparse(url)

    # Check blocked
    if any(blocked in parsed.netloc for blocked in BLOCKED_DOMAINS):
        return {
            "allowed": False,
            "reason": "Blocked domain"
        }

    # Check allowlist (if strict mode)
    if STRICT_MODE and not any(allowed in parsed.netloc for allowed in ALLOWED_DOMAINS):
        return {
            "allowed": False,
            "reason": "Not in allowlist"
        }

    return {"allowed": True}
```

#### 3.3 Tool/Command Whitelist ✅

**Implementation**:
```python
# backend/app/agents/tool_whitelist.py
ALLOWED_TOOLS = {
    "document_rag",
    "web_search",
    "calculator",
    "date_time",
    # Add safe tools only
}

BLOCKED_TOOLS = {
    "shell_execute",
    "file_delete",
    "database_drop",
    # Dangerous tools
}

def validate_tool(tool_name: str) -> bool:
    """Check if tool is allowed."""
    if tool_name in BLOCKED_TOOLS:
        return False
    if tool_name not in ALLOWED_TOOLS:
        return False
    return True
```

---

## 📊 Implementation Priority Matrix

| Feature | Impact | Complexity | Priority | Timeline |
|---------|--------|------------|----------|----------|
| UI Semantic Weight Config | Medium | Low | **P0** | 1 day |
| Restore Eval Metrics UI | High | Low | **P0** | 1 day |
| Versioned Cache Keys | Medium | Low | **P0** | 2 days |
| Cross-Encoder Reranker | **Very High** | Medium | **P1** | 3-5 days |
| Prompt Injection Filter | High | Low | **P1** | 2 days |
| URL/Tool Whitelists | High | Low | **P1** | 1 day |
| Dynamic Chunking | High | Medium | **P2** | 5-7 days |
| Query Reformulation | High | Medium | **P2** | 5-7 days |
| Contextual Compression | Medium | Medium | **P3** | 7-10 days |
| Multi-Vector (ColBERT) | **Very High** | **Very High** | **P3** | 14-21 days |

---

## 🎯 Quick Wins (This Week)

1. ✅ **Add Semantic Weight to UI** - 1 day
2. ✅ **Restore Eval Metrics Display** - 1 day
3. ✅ **Versioned Cache Keys** - 2 days
4. ✅ **Prompt Injection Filter** - 2 days
5. ✅ **URL Whitelist** - 1 day

**Total**: 5 high-impact improvements in ~1 week

---

## 🚀 Next Sprint (2-4 Weeks)

1. **Cross-Encoder Reranker** - Biggest accuracy boost
2. **Dynamic Chunking** - Better recall per document type
3. **Query Reformulation** - Handle ambiguous queries

---

## 💡 State-of-the-Art Inspiration

### ChatGPT Retrieval Strategies
1. **Multi-stage retrieval**: Coarse → Fine → Rerank
2. **Query understanding**: Decompose complex questions
3. **Citation quality**: Exact quotes with confidence scores
4. **Conversational coherence**: Reference resolution across turns

### Claude's Approach
1. **Contextual compression**: Extract only relevant sentences
2. **Source quality scoring**: Rank sources by relevance
3. **Uncertainty handling**: Explicit "I don't know" when low confidence
4. **Long-context optimization**: Process 100K+ tokens efficiently

### Perplexity's Innovation
1. **Real-time web search** + vector search hybrid
2. **Source diversity**: Ensure varied perspectives
3. **Follow-up question suggestions**: Based on context
4. **Streaming citations**: Show sources as they're found

---

## ✅ Current Implementation Status

### Backend
- ✅ Hybrid search (80/20 weights)
- ✅ Parameterized SQL (injection-safe)
- ✅ Quality-based routing
- ✅ Configurable weights via API
- ❌ UI exposure for weights (TODO)
- ❌ Cross-encoder reranking (TODO)
- ❌ Dynamic chunking (TODO)
- ❌ Versioned cache (TODO)
- ❌ Guardrails (TODO)

### Frontend
- ✅ Eval metrics calculated
- ❌ Eval metrics display (TODO - was working before)
- ❌ Semantic weight slider (TODO)
- ❌ Quality indicators (TODO)

---

**Recommendation**: Focus on **P0 and P1** items first (UI config, eval metrics, cache versioning, reranker, guardrails). These provide 80% of the value with 20% of the effort.

Then move to **P2** (dynamic chunking, query reformulation) for advanced capabilities.

**P3** (multi-vector/ColBERT) is cutting-edge but requires significant infrastructure changes - save for later optimization.

---

**Next Actions**:
1. ✅ Test current architecture - **DONE! 2 sources returned**
2. Add semantic weight to UI config
3. Restore eval metrics display
4. Implement cross-encoder reranker
5. Add prompt injection filter
