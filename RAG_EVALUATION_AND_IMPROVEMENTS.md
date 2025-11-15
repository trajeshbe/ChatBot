# RAG System Evaluation and Improvement Plan

## Executive Summary
Based on the test conversation analyzing queries about a short story, the RAG system shows **critical failures** in answer faithfulness (0%) despite good document retrieval (Context Precision: 100%). This document outlines specific issues and actionable improvements.

---

## Current Performance Metrics

### Query: "who is aadhan?"
- **RAG Score**: 55% (Fair)
- **Answer Relevance**: 67%
- **Faithfulness**: 0% ⚠️ **CRITICAL**
- **Context Precision**: 100%
- **Context Relevance**: 76%
- **Sources Retrieved**: 5
- **Model**: Qwen 1.5B Q4 (CPU)

### Query: "who is Thamarai?"
- **RAG Score**: 71% (Good)
- **Model**: Qwen 1.5B Q4 (CPU)

### Query: "who is Amudhan?"
- **RAG Score**: 56% (Fair)
- **Answer Relevance**: 72%
- **Faithfulness**: 0% ⚠️ **CRITICAL**
- **Sources Retrieved**: 0 ⚠️ **No documents found**
- **Model**: Llama 3.2 3B Q4 (CPU)

### Query: "tell me about kandigai"
- **Model**: GPT-4 Turbo
- **Sources Retrieved**: 5
- **Performance**: Good answer quality

---

## Critical Issues

### 1. **Zero Faithfulness - Hallucination Problem**

**Issue**: Models are generating answers that contradict or misrepresent source documents.

**Evidence**:
```
Source snippet: "Aadhan's efforts bore fruit, and Kandigai began to thrive once
more under his benevolent rule..."

Model answer: "Aadhan is a character... It is not clear whether Aadhan has any
specific role or status within the narrative other than being a partner and
supporter of Thamarai."
```

**Root Causes**:
- Small model size (1.5B, 3B parameters) lacks reasoning capability
- Q4 quantization degrades model intelligence
- No prompt engineering to enforce faithfulness
- No citation requirements in system prompt

**Impact**: Users cannot trust the answers, defeating the purpose of RAG.

---

### 2. **Model Selection Issues**

**Current Models**:
- Qwen 1.5B Q4 (CPU)
- Llama 3.2 3B Q4 (CPU)
- GPT-4 Turbo (only used for one query)

**Problems**:
| Model | Parameters | Quantization | CPU/GPU | Faithfulness |
|-------|-----------|--------------|---------|--------------|
| Qwen 1.5B Q4 | 1.5B | Q4 (4-bit) | CPU | Poor |
| Llama 3.2 3B Q4 | 3B | Q4 | CPU | Poor |
| GPT-4 Turbo | ~1.7T | None | Cloud | Good |

**Analysis**:
- 1.5B-3B models are too small for reliable RAG
- Q4 quantization causes further degradation
- CPU inference limits model choice
- GPT-4 Turbo performs well but expensive

---

### 3. **Entity Detection Failures**

**Issue**: Query "who is Amudhan?" returns **0 documents** despite character being in the story.

**Possible Causes**:

#### A. Chunking Strategy Issues
```python
# Current settings (visible in UI)
Chunk Size: 800 characters
Overlap: 150 characters
```

**Problem**: Character name "Amudhan" might be:
- Split across chunk boundaries
- Mentioned only in chunk overlap regions
- In very small sections that don't meet relevance threshold

#### B. Embedding Issues
- Sentence transformer model may not capture proper nouns well
- 384-dimensional embeddings may be too small
- Embedding model not tuned for entity recognition

#### C. Spelling Variations
- Story might use: Amudhan, Amadhan, Amudham, etc.
- No fuzzy matching or normalization

---

### 4. **Inconsistent Search Settings**

**Observed Variations**:
| Query | Min Similarity | Relevance | Top K |
|-------|---------------|-----------|-------|
| "who is aadhan?" | 30% | 30% | 5 |
| "who is Amudhan?" | 85% | 85% | 5 |

**Issues**:
- 85% threshold is too strict (no results for Amudhan)
- No clear strategy for when to adjust thresholds
- Hybrid search weights not visible

---

### 5. **Answer Quality Issues**

**Qwen 1.5B Answer** (for "who is Thamarai?"):
```
"Thamarai is a female character from the short story... The information
provided does not specify her exact background or personal details beyond
describing her as someone who has 'kindness and compassion'..."
```

**Problems**:
- Unnecessarily verbose meta-commentary
- States limitations instead of providing available information
- Fails to synthesize information from multiple chunks
- Doesn't mention key facts (her relationship with Aadhan, her role)

**GPT-4 Answer** (for "tell me about kandigai"):
```
"Kandigai is described as a land that experienced a period of thriving under
the benevolent rule of Aadhan... [concise, accurate synthesis with citations]"
```

**Success Factors**:
- Concise and direct
- Synthesizes information across chunks
- Provides proper citations [Source 1], [Source 2], etc.
- No unnecessary meta-commentary

---

## Improvement Recommendations

### **Priority 1: Model Upgrade (Immediate Impact)**

#### Option A: Better Local Models
```yaml
Recommended Models (in priority order):
  1. Llama 3.1 8B Instruct (or 70B if GPU available)
  2. Mistral 7B Instruct v0.3
  3. Qwen2.5 7B Instruct
  4. Phi-3 Medium (14B)

Minimum Requirements:
  - 7B+ parameters (do not use <7B for RAG)
  - Full precision or Q8 quantization (avoid Q4)
  - Instruct/Chat fine-tuned variant
```

#### Option B: Cloud API Models
```yaml
Recommended (Cost vs Quality):
  1. GPT-4 Turbo - Best quality, higher cost
  2. GPT-3.5 Turbo - Good balance, lower cost
  3. Claude 3.5 Sonnet - Excellent reasoning
  4. Claude 3 Haiku - Fast and cheap
  5. Gemini 1.5 Flash - Good quality, competitive pricing
```

**Implementation**:
```python
# backend/app/services/llm_service.py
# Add tiered model selection

RAG_MODEL_TIERS = {
    "premium": "gpt-4-turbo",
    "standard": "gpt-3.5-turbo",
    "local_best": "ollama/llama3.1:8b",
    "local_fast": "ollama/llama3.1:8b-q8_0"
}

# Fallback chain
DEFAULT_MODEL_CHAIN = [
    "gpt-3.5-turbo",  # Try cloud first
    "ollama/llama3.1:8b",  # Fallback to local
]
```

---

### **Priority 2: Improve Faithfulness with Prompt Engineering**

**Current Issue**: No explicit faithfulness constraints in prompts.

**Solution**: Implement strict RAG prompt with citations requirement.

**Implementation**:

```python
# backend/app/services/rag_service.py

RAG_SYSTEM_PROMPT = """You are a helpful assistant that answers questions based ONLY on the provided context documents.

CRITICAL RULES:
1. ONLY use information explicitly stated in the context documents
2. If the context doesn't contain the answer, say "I don't have enough information to answer that question based on the provided documents."
3. Cite sources using [Source N] notation for every fact
4. DO NOT add information from your general knowledge
5. DO NOT make assumptions or inferences beyond what's explicitly stated
6. If documents contradict each other, mention both perspectives and cite each

FORMAT:
- Be concise and direct
- Start with the direct answer
- Provide supporting details with citations
- Do not add meta-commentary about limitations unless truly necessary
"""

RAG_USER_PROMPT_TEMPLATE = """Context Documents:
{context}

Question: {question}

Answer based ONLY on the context above, with [Source N] citations:"""
```

**Add faithfulness validation**:

```python
def validate_faithfulness(answer: str, context_chunks: List[str]) -> dict:
    """
    Use a second LLM call to validate if answer is faithful to context.
    """
    validation_prompt = f"""
    Context: {context_chunks}

    Answer: {answer}

    Question: Is the answer faithful to the context? Does it only include facts stated in the context?
    Respond with JSON:
    {{
        "is_faithful": true/false,
        "violations": ["list of unfaithful statements"],
        "score": 0-100
    }}
    """

    # Make validation call
    # If faithfulness < 80%, regenerate or flag for review
```

---

### **Priority 3: Fix Entity Detection**

#### Solution 3A: Improved Chunking Strategy

**Current**:
```python
chunk_size = 800
overlap = 150
```

**Recommended**:
```python
# Use semantic chunking instead of fixed-size
from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,  # Increase size
    chunk_overlap=200,  # Increase overlap (20%)
    separators=["\n\n", "\n", ". ", " ", ""],
    length_function=len,
)

# OR use LangChain's SentenceTextSplitter for better entity preservation
```

**Alternative - Sliding Window with Guaranteed Entity Capture**:
```python
def chunk_with_entity_preservation(text: str, entities: List[str]):
    """
    Ensure each entity mention gets its own chunk + context.
    """
    chunks = []
    for entity in entities:
        # Find all mentions of entity
        mentions = find_entity_mentions(text, entity)
        for mention_idx in mentions:
            # Extract chunk around entity (±500 chars)
            chunk = extract_context_window(text, mention_idx, window=500)
            chunks.append(chunk)

    # Also add regular chunks
    regular_chunks = standard_chunking(text)
    return chunks + regular_chunks
```

#### Solution 3B: Add Named Entity Recognition

**Pre-process documents to extract and index entities**:

```python
# backend/app/services/entity_service.py
import spacy

class EntityService:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

    def extract_entities(self, text: str) -> List[Dict]:
        """Extract named entities and their context."""
        doc = self.nlp(text)
        entities = []

        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE", "LOC"]:
                entities.append({
                    "text": ent.text,
                    "type": ent.label_,
                    "context": get_sentence_context(text, ent.start_char, ent.end_char)
                })

        return entities

    def create_entity_index(self, document_id: str, entities: List[Dict]):
        """Store entities in separate table for direct lookup."""
        for entity in entities:
            db.add(DocumentEntity(
                document_id=document_id,
                entity_text=entity["text"],
                entity_type=entity["type"],
                context=entity["context"]
            ))
```

**Database Schema Addition**:
```sql
CREATE TABLE document_entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    entity_text VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,  -- PERSON, ORG, GPE, LOC
    context TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_entities_text ON document_entities(entity_text);
CREATE INDEX idx_entities_type ON document_entities(entity_type);
```

**Modified RAG Pipeline**:
```python
async def query_with_entity_detection(query: str, session_id: str):
    # Step 1: Check if query is asking about an entity
    entities_in_query = extract_entities(query)

    if entities_in_query:
        # Direct entity lookup first
        entity_results = db.query(DocumentEntity).filter(
            DocumentEntity.entity_text.ilike(f"%{entities_in_query[0]['text']}%")
        ).all()

        if entity_results:
            # Found entity, use its context as guaranteed chunks
            guaranteed_chunks = [e.context for e in entity_results]
        else:
            guaranteed_chunks = []
    else:
        guaranteed_chunks = []

    # Step 2: Regular vector search
    vector_results = vector_search(query, top_k=5)

    # Step 3: Combine results
    all_chunks = guaranteed_chunks + vector_results

    # Step 4: Generate answer
    return generate_answer(query, all_chunks)
```

#### Solution 3C: Fuzzy Matching for Name Variations

```python
from rapidfuzz import fuzz, process

def fuzzy_entity_search(query_entity: str, threshold: int = 80):
    """
    Find entities similar to query entity.
    """
    all_entities = db.query(DocumentEntity.entity_text).distinct().all()
    all_entities = [e[0] for e in all_entities]

    matches = process.extract(
        query_entity,
        all_entities,
        scorer=fuzz.ratio,
        limit=5
    )

    # Return matches above threshold
    return [m[0] for m in matches if m[1] >= threshold]

# Usage
if "Amudhan" not in entity_index:
    similar = fuzzy_entity_search("Amudhan", threshold=80)
    # Might find: "Amudham", "Amadhan", etc.
```

---

### **Priority 4: Hybrid Search Optimization**

**Current Issue**: Not clear how hybrid search is weighted.

**Recommendation**: Implement configurable hybrid search with explicit weights.

```python
# backend/app/services/rag_service.py

from typing import Literal

class HybridSearchConfig:
    def __init__(
        self,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        vector_top_k: int = 10,
        keyword_top_k: int = 10,
        final_top_k: int = 5,
        rerank: bool = True
    ):
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        self.vector_top_k = vector_top_k
        self.keyword_top_k = keyword_top_k
        self.final_top_k = final_top_k
        self.rerank = rerank

async def hybrid_search(
    query: str,
    config: HybridSearchConfig,
    session_id: Optional[str] = None
) -> List[Dict]:
    """
    Perform hybrid search combining vector similarity and keyword matching.
    """
    # Vector search using embeddings
    vector_results = await vector_search(
        query,
        top_k=config.vector_top_k,
        session_id=session_id
    )

    # Keyword search using PostgreSQL full-text search
    keyword_results = await keyword_search(
        query,
        top_k=config.keyword_top_k,
        session_id=session_id
    )

    # Reciprocal Rank Fusion (RRF) for combining results
    combined = reciprocal_rank_fusion(
        vector_results=vector_results,
        keyword_results=keyword_results,
        vector_weight=config.vector_weight,
        keyword_weight=config.keyword_weight
    )

    # Optional: Rerank with cross-encoder
    if config.rerank:
        combined = rerank_results(query, combined)

    return combined[:config.final_top_k]

def reciprocal_rank_fusion(
    vector_results: List[Dict],
    keyword_results: List[Dict],
    vector_weight: float,
    keyword_weight: float,
    k: int = 60
) -> List[Dict]:
    """
    RRF algorithm: score = Σ(weight / (k + rank))
    """
    scores = defaultdict(float)
    chunk_data = {}

    for rank, result in enumerate(vector_results, 1):
        chunk_id = result["chunk_id"]
        scores[chunk_id] += vector_weight / (k + rank)
        chunk_data[chunk_id] = result

    for rank, result in enumerate(keyword_results, 1):
        chunk_id = result["chunk_id"]
        scores[chunk_id] += keyword_weight / (k + rank)
        if chunk_id not in chunk_data:
            chunk_data[chunk_id] = result

    # Sort by combined score
    sorted_chunks = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return [chunk_data[chunk_id] for chunk_id, _ in sorted_chunks]
```

**Add PostgreSQL Full-Text Search**:

```sql
-- Add tsvector column to document_chunks
ALTER TABLE document_chunks
ADD COLUMN content_tsv tsvector;

-- Create index
CREATE INDEX idx_chunks_tsv ON document_chunks USING gin(content_tsv);

-- Update tsvector on insert/update
CREATE TRIGGER tsvector_update BEFORE INSERT OR UPDATE ON document_chunks
FOR EACH ROW EXECUTE FUNCTION
tsvector_update_trigger(content_tsv, 'pg_catalog.english', content);

-- Update existing rows
UPDATE document_chunks SET content_tsv = to_tsvector('english', content);
```

```python
async def keyword_search(query: str, top_k: int = 10, session_id: Optional[str] = None):
    """
    Full-text search using PostgreSQL.
    """
    tsquery = " & ".join(query.split())  # Basic query parsing

    sql = """
    SELECT
        dc.id,
        dc.content,
        dc.document_id,
        d.filename,
        ts_rank(dc.content_tsv, to_tsquery('english', :query)) as rank
    FROM document_chunks dc
    JOIN documents d ON dc.document_id = d.id
    WHERE dc.content_tsv @@ to_tsquery('english', :query)
    """

    if session_id:
        sql += " AND EXISTS (SELECT 1 FROM session_documents sd WHERE sd.document_id = dc.document_id AND sd.session_id = :session_id)"

    sql += " ORDER BY rank DESC LIMIT :top_k"

    results = db.execute(text(sql), {"query": tsquery, "top_k": top_k, "session_id": session_id})
    return [dict(row) for row in results]
```

---

### **Priority 5: Add Cross-Encoder Reranking**

**Problem**: Initial retrieval may have false positives in top K results.

**Solution**: Use a cross-encoder model to rerank results based on query-chunk relevance.

```python
# backend/app/services/reranker_service.py
from sentence_transformers import CrossEncoder

class RerankerService:
    def __init__(self):
        # Load cross-encoder model (smaller and faster than bi-encoder)
        self.model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

    def rerank(
        self,
        query: str,
        chunks: List[Dict],
        top_k: int = 5
    ) -> List[Dict]:
        """
        Rerank chunks using cross-encoder.
        """
        if not chunks:
            return []

        # Create query-chunk pairs
        pairs = [[query, chunk["content"]] for chunk in chunks]

        # Get relevance scores
        scores = self.model.predict(pairs)

        # Add scores to chunks
        for chunk, score in zip(chunks, scores):
            chunk["rerank_score"] = float(score)

        # Sort by rerank score
        reranked = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)

        return reranked[:top_k]
```

**Integration**:
```python
async def query_with_reranking(query: str, session_id: str, top_k: int = 5):
    # Step 1: Hybrid search (get 2x results)
    initial_results = await hybrid_search(query, session_id, top_k=top_k * 2)

    # Step 2: Rerank
    reranker = RerankerService()
    final_results = reranker.rerank(query, initial_results, top_k=top_k)

    return final_results
```

---

### **Priority 6: Evaluation Framework**

**Implement automated evaluation to catch regressions**:

```python
# backend/tests/test_rag_evaluation.py
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    faithfulness,
    context_precision,
    context_recall,
)

class RAGEvaluator:
    def __init__(self):
        self.metrics = [
            answer_relevancy,
            faithfulness,
            context_precision,
            context_recall,
        ]

    async def evaluate_query(
        self,
        query: str,
        ground_truth: str,
        session_id: str
    ) -> Dict[str, float]:
        """
        Evaluate a single query.
        """
        # Get RAG response
        response = await rag_service.query(query, session_id)

        # Prepare data for RAGAS
        data = {
            "question": [query],
            "answer": [response["answer"]],
            "contexts": [[chunk["content"] for chunk in response["sources"]]],
            "ground_truth": [ground_truth]
        }

        # Evaluate
        result = evaluate(Dataset.from_dict(data), metrics=self.metrics)

        return result

    async def evaluate_test_set(self, test_set_path: str) -> pd.DataFrame:
        """
        Evaluate entire test set.
        """
        test_cases = load_test_cases(test_set_path)
        results = []

        for case in test_cases:
            result = await self.evaluate_query(
                case["query"],
                case["ground_truth"],
                case["session_id"]
            )
            results.append(result)

        return pd.DataFrame(results)
```

**Create test dataset**:

```json
// tests/data/rag_test_cases.json
[
  {
    "query": "Who is Aadhan?",
    "ground_truth": "Aadhan is the ruler of Kandigai who brought prosperity to the land through benevolent rule. He is in a relationship with Thamarai.",
    "session_id": "test_session_1",
    "expected_sources": ["Short Story.txt"],
    "min_faithfulness": 0.8,
    "min_relevancy": 0.8
  },
  {
    "query": "Who is Amudhan?",
    "ground_truth": "[Actual ground truth from story]",
    "session_id": "test_session_1",
    "expected_sources": ["Short Story.txt"],
    "min_faithfulness": 0.8,
    "min_relevancy": 0.8
  }
]
```

**CI/CD Integration**:

```yaml
# .github/workflows/rag_evaluation.yml
name: RAG Evaluation

on:
  pull_request:
    paths:
      - 'backend/app/services/rag_service.py'
      - 'backend/app/services/embedding_service.py'

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Run RAG Evaluation
        run: |
          python -m pytest backend/tests/test_rag_evaluation.py -v

      - name: Upload Results
        uses: actions/upload-artifact@v2
        with:
          name: rag-evaluation-results
          path: evaluation_results.csv

      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v5
        with:
          script: |
            // Post evaluation metrics as comment on PR
```

---

### **Priority 7: Monitoring and Logging**

**Add comprehensive logging for debugging**:

```python
# backend/app/services/rag_service.py
import structlog

logger = structlog.get_logger()

async def query(query: str, session_id: str, model: str, top_k: int = 5):
    query_id = str(uuid.uuid4())

    logger.info(
        "rag_query_start",
        query_id=query_id,
        query=query,
        session_id=session_id,
        model=model,
        top_k=top_k
    )

    try:
        # Embedding
        start_time = time.time()
        query_embedding = await embedding_service.embed(query)
        embedding_time = time.time() - start_time

        logger.info(
            "rag_embedding_complete",
            query_id=query_id,
            embedding_time_ms=embedding_time * 1000
        )

        # Search
        start_time = time.time()
        chunks = await hybrid_search(query_embedding, session_id, top_k)
        search_time = time.time() - start_time

        logger.info(
            "rag_search_complete",
            query_id=query_id,
            search_time_ms=search_time * 1000,
            chunks_found=len(chunks),
            chunks=[{
                "chunk_id": c["id"],
                "document": c["filename"],
                "score": c["score"]
            } for c in chunks]
        )

        # Generation
        start_time = time.time()
        answer = await llm_service.generate(query, chunks, model)
        generation_time = time.time() - start_time

        logger.info(
            "rag_generation_complete",
            query_id=query_id,
            generation_time_ms=generation_time * 1000,
            model=model,
            tokens_used=answer.get("tokens"),
            answer_preview=answer["text"][:100]
        )

        # Calculate faithfulness
        faithfulness_score = await validate_faithfulness(answer["text"], chunks)

        logger.info(
            "rag_query_complete",
            query_id=query_id,
            total_time_ms=(embedding_time + search_time + generation_time) * 1000,
            faithfulness=faithfulness_score
        )

        if faithfulness_score < 0.7:
            logger.warning(
                "rag_low_faithfulness",
                query_id=query_id,
                faithfulness=faithfulness_score,
                answer=answer["text"],
                chunks=[c["content"] for c in chunks]
            )

        return {
            "query_id": query_id,
            "answer": answer["text"],
            "sources": chunks,
            "metrics": {
                "embedding_time_ms": embedding_time * 1000,
                "search_time_ms": search_time * 1000,
                "generation_time_ms": generation_time * 1000,
                "total_time_ms": (embedding_time + search_time + generation_time) * 1000,
                "faithfulness": faithfulness_score,
                "chunks_retrieved": len(chunks)
            }
        }

    except Exception as e:
        logger.error(
            "rag_query_error",
            query_id=query_id,
            error=str(e),
            traceback=traceback.format_exc()
        )
        raise
```

---

## Implementation Roadmap

### Phase 1: Quick Wins (1-2 days)
1. ✅ **Upgrade to better model** - Switch to GPT-3.5-Turbo or Llama 3.1 8B
2. ✅ **Add faithfulness prompt** - Implement strict RAG prompt with citation requirements
3. ✅ **Increase chunk overlap** - Change to 200-250 characters
4. ✅ **Add structured logging** - Implement query ID tracking and metrics

### Phase 2: Core Improvements (1 week)
1. ✅ **Named Entity Recognition** - Extract and index entities separately
2. ✅ **Hybrid search** - Implement vector + keyword search with RRF
3. ✅ **Cross-encoder reranking** - Add reranking layer
4. ✅ **Faithfulness validation** - Two-stage generation with validation

### Phase 3: Advanced Features (2-3 weeks)
1. ✅ **Automated evaluation** - RAGAS integration and test suite
2. ✅ **Query classification** - Different strategies for entity vs. topic queries
3. ✅ **Answer caching** - Redis caching with semantic similarity
4. ✅ **A/B testing framework** - Compare different RAG configurations

### Phase 4: Production Hardening (Ongoing)
1. ✅ **Monitoring dashboards** - Grafana dashboards for RAG metrics
2. ✅ **Alert system** - Alert on low faithfulness scores
3. ✅ **Continuous evaluation** - Regular testing on production data
4. ✅ **User feedback loop** - Collect user ratings and use for improvement

---

## Expected Improvements

### Baseline (Current)
- Faithfulness: 0-56%
- Answer Relevance: 67-72%
- Entity Detection: 0/3 entities found
- Model: Qwen 1.5B Q4

### After Phase 1 (Quick Wins)
- Faithfulness: 70-80%
- Answer Relevance: 80-85%
- Entity Detection: 2/3 entities found
- Model: GPT-3.5-Turbo or Llama 3.1 8B

### After Phase 2 (Core Improvements)
- Faithfulness: 85-92%
- Answer Relevance: 88-93%
- Entity Detection: 3/3 entities found
- Context Precision: 95%+

### After Phase 3 (Advanced Features)
- Faithfulness: 90-95%
- Answer Relevance: 92-96%
- Entity Detection: 100% (with fuzzy matching)
- Query Latency: <2 seconds (with caching)

---

## Configuration Template

```yaml
# config/rag_config.yaml

rag:
  # Model Selection
  models:
    primary: "gpt-3.5-turbo"
    fallback: "ollama/llama3.1:8b"
    embedding: "sentence-transformers/all-MiniLM-L6-v2"
    reranker: "cross-encoder/ms-marco-MiniLM-L-6-v2"

  # Chunking
  chunking:
    strategy: "recursive"  # recursive | semantic | sentence
    chunk_size: 1000
    chunk_overlap: 200
    separators: ["\n\n", "\n", ". ", " "]

  # Search
  search:
    type: "hybrid"  # vector | keyword | hybrid
    vector_weight: 0.7
    keyword_weight: 0.3
    top_k: 10
    min_similarity: 0.3
    rerank: true
    rerank_top_k: 5

  # Entity Detection
  entities:
    enabled: true
    types: ["PERSON", "ORG", "GPE", "LOC"]
    fuzzy_matching: true
    fuzzy_threshold: 80

  # Generation
  generation:
    temperature: 0.1
    max_tokens: 500
    require_citations: true
    validate_faithfulness: true
    min_faithfulness: 0.7

  # Memory Hierarchy
  memory:
    strategy: "hierarchical"  # session_only | global_only | hierarchical
    session_weight: 0.8
    global_weight: 0.2

  # Caching
  cache:
    enabled: true
    ttl: 3600
    similarity_threshold: 0.95

  # Monitoring
  monitoring:
    log_level: "INFO"
    track_metrics: true
    alert_on_low_faithfulness: true
    faithfulness_threshold: 0.7
```

---

## Testing Checklist

Before deploying improvements:

- [ ] All existing tests pass
- [ ] New tests added for entity detection
- [ ] Faithfulness score >80% on test set
- [ ] No regression in retrieval quality
- [ ] Latency <3 seconds for 95th percentile
- [ ] Memory usage acceptable
- [ ] Cost per query documented
- [ ] Monitoring dashboards created
- [ ] Documentation updated
- [ ] User acceptance testing complete

---

## References

1. **RAGAS Framework**: https://github.com/explodinggradients/ragas
2. **Hybrid Search Best Practices**: https://www.pinecone.io/learn/hybrid-search/
3. **Cross-Encoder Reranking**: https://www.sbert.net/examples/applications/cross-encoder/README.html
4. **LangChain RAG**: https://python.langchain.com/docs/use_cases/question_answering/
5. **Named Entity Recognition with spaCy**: https://spacy.io/usage/linguistic-features#named-entities

---

**Document Version**: 1.0
**Last Updated**: 2025-11-15
**Author**: RAG System Analysis
**Next Review**: After Phase 1 implementation
