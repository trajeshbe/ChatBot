# RAG Evaluation & Agent Architecture - Quick Reference

## Key Files Overview

### Evaluation System

| File | Lines | Purpose | Key Classes |
|------|-------|---------|-------------|
| `backend/app/services/evaluation_service.py` | 1,056 | Main evaluation framework | `EvaluationService`, `EvaluationConfig`, `EvaluationMethod` |
| `backend/app/api/routes/evaluation.py` | 658 | REST API endpoints for evaluation | Routes for config, evaluation, feedback, analytics |
| `backend/app/services/quality_metrics.py` | 352 | Lightweight quality metrics | `QualityMetricsService` (faithfulness, relevancy, etc.) |
| `backend/app/services/query_classifier.py` | 136 | Query type classification | `QueryClassifier` (ai_personal, document_specific, general) |

### RAG Service & Agents

| File | Lines | Purpose | Key Classes |
|------|-------|---------|-------------|
| `backend/app/services/rag_service_enhanced.py` | 893 | Memory hierarchy RAG | `EnhancedRAGService` (short-term + long-term memory) |
| `backend/app/services/rag_service.py` | 265 | Basic RAG service | `RAGService` (fallback implementation) |
| `backend/app/agents/rag_agent.py` | 227 | LangGraph agent workflows | `RAGAgent`, Prefect flows |

### Supporting Services

| File | Lines | Purpose |
|------|-------|---------|
| `backend/app/services/document_service.py` | - | Document processing & search |
| `backend/app/services/embedding_service.py` | - | Text embedding generation |
| `backend/app/services/llm_service_enhanced.py` | - | Multi-model LLM support |
| `backend/app/services/audit_service.py` | - | Audit logging |

---

## Evaluation Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ API Request: POST /api/v1/evaluation/evaluate                   │
├─────────────────────────────────────────────────────────────────┤
│ 1. Load evaluation config (per-session)                          │
│ 2. Build evaluation task list (enabled methods)                  │
│ 3. Check cache (SHA256 of query+response+chunk_count)           │
│ 4. If cache miss:                                               │
│    ├─ If async_evaluation=True AND >1 task:                    │
│    │  └─ asyncio.gather() → PARALLEL EXECUTION                 │
│    └─ Else: Sequential for loop                                │
│ 5. Aggregate results (collect scores + errors)                 │
│ 6. Calculate overall score (weighted average)                  │
│ 7. Cache result (1-hour TTL)                                   │
│ 8. Store in evaluation_results table                           │
└─────────────────────────────────────────────────────────────────┘
```

### Evaluation Methods (13 Total)

**Frameworks** (Require external libraries):
- RAGAS - Comprehensive assessment
- DeepEval - Modern evaluation framework
- BERTScore - Semantic similarity metric

**LLM-Based**:
- LLM-as-Judge (GPT-4/Claude) - 5-point criteria

**Built-in Custom**:
- Citation Accuracy - Word overlap heuristic
- Toxicity Detection - Keyword pattern matching
- Bias Detection - Pattern-based detection
- Hallucination Detection - LLM-based analysis
- Answer Relevancy - Embedding similarity
- Context Precision - Ranking quality check
- Context Recall - Word overlap with ground truth
- Faithfulness - Answer grounding in context
- Semantic Similarity - Embedding cosine similarity

---

## RAG Query Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ API Request: POST /api/v1/query                                 │
├─────────────────────────────────────────────────────────────────┤
│ 1. Query Classification                                          │
│    └─ Is this AI-personal? Skip RAG if yes                     │
│ 2. Semantic Cache Check                                         │
│    └─ Similar cached query? Return cached result               │
│ 3. Generate Query Embedding                                     │
│    └─ embedding_service.get_embedding(query_text)              │
│ 4. Search Short-Term Memory (Session Documents)                │
│    └─ Hybrid search: 0.6*semantic + 0.4*keyword                │
│    └─ Cascading fallback thresholds                            │
│ 5. Search Long-Term Memory (All Documents)                     │
│    └─ Same hybrid search approach                              │
│ 6. Combine Results                                              │
│    └─ Short-term chunks prioritized                            │
│    └─ Deduplicated, limited to top_k                           │
│ 7. Get Conversation Context                                     │
│    └─ Last N messages from session                             │
│ 8. Generate LLM Response                                        │
│    └─ llm_service.generate_with_context(...)                  │
│ 9. EVALUATE QUALITY METRICS                                    │
│    └─ quality_metrics_service.evaluate_response()              │
│    └─ Fast, ~100-200ms, no external APIs                       │
│ 10. Save Conversation Message                                   │
│    └─ Store in conversation_messages table                     │
│ 11. Cache Result                                                │
│    └─ Save to query_cache (1-hour TTL)                         │
└─────────────────────────────────────────────────────────────────┘

Response includes:
  - answer: Generated response
  - sources: List of referenced documents
  - quality_metrics: {faithfulness, answer_relevancy, context_relevancy, 
                      context_precision, rag_score, quality_level}
```

---

## LangGraph Agent Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ Agent State Machine                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐                                               │
│  │analyze_query│ ← Keyword matching for intent                 │
│  └──────┬───────┘   (upload/scrape/query)                       │
│         │                                                        │
│         ↓                                                        │
│  ┌──────────────────────┐                                       │
│  │retrieve_documents    │ ← Semantic search                     │
│  └──────┬───────────────┘   top_k=5, threshold=0.7             │
│         │                                                        │
│         ↓                                                        │
│  ┌──────────────────────┐                                       │
│  │generate_answer       │ ← RAG response generation             │
│  └──────┬───────────────┘                                       │
│         │                                                        │
│         ↓                                                        │
│  ┌──────────────────────┐                                       │
│  │validate_answer       │ ← Checks: len>10 chars, no errors     │
│  └──────┬───────────────┘                                       │
│         │                                                        │
│    ┌────┴────────────────────┐                                  │
│    │                         │                                  │
│  regenerate           complete                                  │
│    │                         │                                  │
│    └──→ generate_answer      → END                              │
│         (loop-back)                                             │
└─────────────────────────────────────────────────────────────────┘

Status: Implemented but NOT integrated in main REST API flow
         Used for demo/testing, not for production queries
```

---

## Database Tables

### Evaluation Tables

**evaluation_config**
```
id, session_id, 
enable_ragas, enable_llm_as_judge, enable_deepeval,
enable_semantic_similarity, enable_bertscore,
enable_citation_accuracy, enable_toxicity, 
enable_bias_detection, enable_hallucination,
enable_answer_relevancy, enable_context_precision, 
enable_context_recall, enable_faithfulness,
llm_judge_model, async_evaluation, use_cache, 
batch_size, min_score_threshold, cache_ttl_seconds,
auto_evaluate, evaluation_sampling_rate,
created_at, updated_at
```

**evaluation_result**
```
id, session_id, query, response, 
scores (JSONB: {method: {scores: {...}}}),
overall_score, evaluation_time_ms, 
enabled_methods (JSONB: [method names]),
errors (JSONB: [{method, error}]),
metadata (JSONB: {query, num_contexts, evaluation_time_ms, ...}),
created_at
```

**evaluation_cache**
```
id, cache_key (SHA256), 
result (JSONB), ttl_seconds, 
created_at, last_accessed
```

**human_feedback**
```
id, session_id, message_id, evaluation_id,
rating (1-5), thumbs_up (bool), feedback_text,
accuracy_rating, helpfulness_rating, clarity_rating,
has_hallucination, has_bias, has_toxicity, is_irrelevant,
feedback_type, created_at
```

### RAG Tables

**chat_sessions**
```
id, session_id, user_id, title,
created_at, last_activity, is_active
```

**session_documents** (Short-term memory)
```
id, session_id, document_id, priority, added_at
```

**conversation_messages**
```
id, session_id, role, content, 
model_id, model_name, total_tokens, latency_ms,
sources (JSONB), created_at
```

---

## API Endpoints

### Evaluation Endpoints

```
POST   /api/v1/evaluation/config
GET    /api/v1/evaluation/config/{session_id}
POST   /api/v1/evaluation/evaluate
GET    /api/v1/evaluation/results
GET    /api/v1/evaluation/analytics
POST   /api/v1/evaluation/feedback
GET    /api/v1/evaluation/feedback
GET    /api/v1/evaluation/methods
```

### RAG Query Endpoints

```
POST   /api/v1/query              ← Main endpoint (uses quality metrics)
POST   /api/v1/upload             ← Attach to session
GET    /api/v1/documents          ← List by session
POST   /api/v1/scrape             ← Web scraping
```

---

## Configuration & Toggles

### Evaluation Config (Per-Session)

```python
enabled_methods: List[EvaluationMethod] = [
    EvaluationMethod.CITATION_ACCURACY,
    EvaluationMethod.TOXICITY,
    EvaluationMethod.BIAS_DETECTION,
    EvaluationMethod.HALLUCINATION,
    EvaluationMethod.ANSWER_RELEVANCY,
    EvaluationMethod.FAITHFULNESS
]
async_evaluation: bool = True      # Parallel vs Sequential
use_cache: bool = True             # Cache results
auto_evaluate: bool = False        # Auto-run after every query
evaluation_sampling_rate: float = 1.0  # Evaluate X% of queries
```

### RAG Query Config (Per-Request Override)

```python
top_k: Optional[int] = None                    # Default: settings.TOP_K_RESULTS
similarity_threshold: Optional[float] = None   # Default: settings.SIMILARITY_THRESHOLD
min_similarity_threshold: Optional[float] = None
no_relevant_docs_threshold: Optional[float] = None
```

---

## Performance Metrics

### Query Latency Breakdown
- Embedding generation: 100-200ms
- Database search: 50-100ms
- LLM response: 3-10 seconds
- Quality metrics: 100-200ms
- Message persistence: 50-100ms
- **Total**: 3.5-10.5 seconds

### Evaluation Time
- Sequential (default): Sum of all method times
  - Example: RAGAS(5s) + Judge(10s) = 15s
- Parallel (async_evaluation=True): Max of all method times
  - Example: RAGAS(5s) + Judge(10s) = 10s
  - Improvement: ~33% faster

### Cache Impact
- Cache hit: ~10-50ms
- Cache miss: Full evaluation time
- TTL: 1 hour

---

## Key Architectural Decisions

### ✅ What Works Well

1. **Dual-Layer Evaluation**
   - Light: Quality metrics (always, inline, 100-200ms)
   - Heavy: Full evaluation (optional, manual, 5-30s)

2. **Memory Hierarchy**
   - Session-first prioritization
   - Automatic document-session association
   - Hybrid search with semantic + keyword

3. **Configuration Flexibility**
   - Per-session evaluation config
   - Per-request RAG parameter overrides
   - Enable/disable individual metrics

4. **Graceful Degradation**
   - Optional external libraries (RAGAS, DeepEval, BERTScore)
   - Fallback to basic RAG if enhanced unavailable
   - Missing embeddings handling

### ⚠️ Current Limitations

1. **Agent Not Integrated**
   - RAGAgent exists but not used in REST API
   - Enhanced RAG service provides better functionality
   - Agent could be used for custom workflows (not currently)

2. **Evaluation Not in Query Path**
   - Only quality metrics included in response
   - Full evaluation requires separate API call
   - Reasoning: Avoid adding latency to user-facing queries

3. **Prefect Flows Sequential**
   - Could run document processing in parallel
   - Currently processes documents/URLs sequentially

---

## References

- Full analysis: `/home/user/ChatBot/RAG_EVALUATION_ARCHITECTURE.md`
- Enhanced RAG service: `/home/user/ChatBot/backend/app/services/rag_service_enhanced.py`
- Evaluation service: `/home/user/ChatBot/backend/app/services/evaluation_service.py`
- Quality metrics: `/home/user/ChatBot/backend/app/services/quality_metrics.py`
- Agent: `/home/user/ChatBot/backend/app/agents/rag_agent.py`

