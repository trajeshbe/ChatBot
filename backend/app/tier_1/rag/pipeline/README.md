# Robust RAG Pipeline

A production-ready Retrieval-Augmented Generation (RAG) pipeline with advanced features including hybrid retrieval, LLM-based reranking, self-critique, and adaptive context window management.

## Features

### 🔍 **Hybrid Retrieval**
- Combines semantic (vector) and lexical (keyword) search
- Configurable α parameter to balance semantic vs lexical weights
- Memory hierarchy: session documents (short-term) → all documents (long-term)
- Cascading fallback strategy for maximum recall

### 🎯 **LLM-Based Reranking**
- Uses Ollama to rerank retrieved chunks for better relevance
- Batch processing for efficiency
- Optional feature (can be disabled for performance)

### 🧠 **Self-Critique & Refinement**
- Self-RAG style critique assesses answer groundedness and completeness
- Automatic refinement when critique identifies issues
- Improves answer quality while maintaining source fidelity

### 💾 **Semantic Caching**
- Redis-based semantic cache using VSS (Vector Similarity Search)
- Caches based on query similarity, not exact matches
- Configurable similarity threshold and TTL

### 📊 **Adaptive Context Windows**
- Automatically adjusts chunk count based on model's context window
- Large models (>100k tokens): Maximize context utilization
- Small models (<10k tokens): Use selective, high-quality chunks
- Supports OpenAI GPT, Anthropic Claude, Ollama models

### 🔭 **Observability**
- Structured logging with timing breakdowns
- Metrics collection (cache hit rate, refinement rate, latency)
- Error tracking and debugging support

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     RAG Pipeline Flow                       │
└─────────────────────────────────────────────────────────────┘

1. normalize_query          → Clean and normalize user input
2. embed_query              → Generate query embedding
3. semantic_cache_check     → Check Redis cache for similar queries
4. hybrid_retrieval         → Semantic + lexical search (with memory hierarchy)
5. rerank_candidates        → LLM-based reranking (optional)
6. generate_initial_answer  → Generate grounded answer
7. self_critique            → Evaluate answer quality (optional)
8. refine_or_finalize       → Refine if needed, otherwise finalize

Each stage can short-circuit (e.g., cache hit skips stages 4-8)
```

## Installation

The pipeline is already installed as part of the backend. Dependencies are included in `requirements.txt`:

```bash
# Core dependencies
sentence-transformers>=2.3.1
redis>=5.0.1
httpx>=0.27.0
openai>=1.40.0
anthropic>=0.39.0
```

## Configuration

Configuration is managed through `app/rag_pipeline/config.py`. You can override settings using environment variables with the `RAG_` prefix:

```bash
# Example .env configuration
RAG_EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
RAG_GENERATION_MODEL_NAME=gpt-4-turbo-preview
RAG_ENABLE_RERANKER=true
RAG_ENABLE_SELF_CRITIQUE=true
RAG_ENABLE_SEMANTIC_CACHE=true
RAG_RETRIEVAL_ALPHA=0.7  # 70% semantic, 30% lexical
```

### Key Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `EMBEDDING_MODEL_NAME` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `GENERATION_MODEL_NAME` | `gpt-4-turbo-preview` | Primary generation model |
| `ENABLE_RERANKER` | `True` | Enable LLM-based reranking |
| `ENABLE_SELF_CRITIQUE` | `True` | Enable self-critique |
| `ENABLE_SEMANTIC_CACHE` | `True` | Enable semantic caching |
| `RETRIEVAL_ALPHA` | `0.7` | Semantic vs lexical weight (0.0-1.0) |
| `RETRIEVAL_CANDIDATES` | `20` | Initial retrieval pool size |
| `RERANK_TOP_K` | `5` | Final chunks after reranking |
| `CONTEXT_CHUNKS` | `5` | Chunks for generation (medium models) |

## Usage

### Via REST API

```python
import requests

# Query the robust RAG pipeline
response = requests.post(
    "http://localhost:8000/api/v1/rag-pipeline/query",
    json={
        "query": "What is the project about?",
        "session_id": "session-123",
        "model_name": "gpt-4-turbo-preview",
        "use_cache": True
    }
)

result = response.json()
print(result["answer"])
print(result["citations"])
print(f"Latency: {result['latency_ms']}ms")
print(f"Cache hit: {result['cache_hit']}")
```

### Programmatic Usage

```python
from app.rag_pipeline import rag_answer
from app.core.database import get_db

async def example():
    async for db in get_db():
        answer, citations, state = await rag_answer(
            user_query="What is the project about?",
            db=db,
            session_id="session-123",
            model_name="gpt-4-turbo-preview"
        )

        print(f"Answer: {answer}")
        print(f"Citations: {len(citations)}")
        print(f"Cache hit: {state.cache_hit}")
        print(f"Refined: {state.refined}")
        print(f"Timings: {state.timings_ms}")
```

## API Endpoints

### `POST /api/v1/rag-pipeline/query`

Query the robust RAG pipeline.

**Request:**
```json
{
  "query": "What is the project about?",
  "session_id": "session-123",
  "tenant_id": "tenant-456",
  "user_id": "user-789",
  "model_name": "gpt-4-turbo-preview",
  "use_cache": true
}
```

**Response:**
```json
{
  "answer": "The project is...",
  "citations": [
    {
      "source_number": 1,
      "filename": "README.md",
      "source_url": null,
      "excerpt": "This is an Enterprise RAG..."
    }
  ],
  "model_used": "gpt-4-turbo-preview",
  "tokens_used": 1234,
  "latency_ms": 567.89,
  "cache_hit": false,
  "refined": false,
  "rerank_used": true,
  "num_candidates": 20,
  "num_chunks_used": 5,
  "timings_ms": {
    "embed_query": 45.2,
    "hybrid_retrieval": 123.4,
    "rerank": 234.5,
    "generate_initial_answer": 164.8
  },
  "critique_passed": true
}
```

### `GET /api/v1/rag-pipeline/metrics`

Get pipeline performance metrics.

**Response:**
```json
{
  "total_requests": 100,
  "cache_hits": 25,
  "cache_misses": 75,
  "cache_hit_rate": 0.25,
  "refinements": 10,
  "refinement_rate": 0.10,
  "errors": 2,
  "error_rate": 0.02,
  "avg_latency_ms": 456.78
}
```

### `GET /api/v1/rag-pipeline/health`

Health check for the pipeline.

## Module Overview

### `config.py`
Pipeline configuration with support for multiple models and adaptive strategies.

### `embeddings.py`
Embedding generation with Redis caching.

**Key Functions:**
- `embed_query(query: str) -> List[float]`
- `embed_documents(texts: List[str]) -> List[List[float]]`

### `retrieval.py`
Hybrid retrieval with memory hierarchy.

**Key Functions:**
- `retrieve_hybrid(query, query_embedding, top_k, alpha, db, session_id, tenant_id) -> List[Dict]`

### `reranker.py`
LLM-based reranking using Ollama.

**Key Functions:**
- `rerank_with_ollama(query, candidates, model_name, top_k) -> List[Dict]`

### `semantic_cache.py`
Semantic caching with Redis VSS.

**Key Functions:**
- `get_cached_answer(embedding, tenant_id, similarity_threshold) -> Optional[CachedAnswer]`
- `store_answer(embedding, tenant_id, normalized_query, answer, citations, ttl_seconds)`

### `llm.py`
Multi-provider LLM client with generation, critique, and refinement.

**Key Functions:**
- `generate_grounded_answer(query, chunks, model_name, temperature, max_tokens) -> Tuple[str, List[Dict]]`
- `critique_answer(query, chunks, answer, model_name) -> Dict`
- `refine_answer_with_critique(query, chunks, initial_answer, critique, model_name) -> Tuple[str, Optional[List[Dict]]]`

### `observability.py`
Timing, logging, and metrics collection.

**Key Functions:**
- `@timed(operation_name)` - Decorator for timing functions
- `log_rag_request(...)` - Structured logging
- `get_metrics_collector()` - Access metrics

### `pipeline.py`
Main orchestrator that coordinates all stages.

**Key Function:**
- `rag_answer(user_query, db, session_id, tenant_id, user_id, model_name, extra_meta) -> Tuple[str, List[Dict], RagState]`

## Testing

### Manual Testing

```bash
# Start the backend
cd backend
uvicorn app.main:app --reload

# Test the pipeline
curl -X POST http://localhost:8000/api/v1/rag-pipeline/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the project about?",
    "session_id": "test-session",
    "model_name": "gpt-4-turbo-preview"
  }'
```

### Unit Testing

Create tests in `backend/tests/test_rag_pipeline.py`:

```python
import pytest
from app.rag_pipeline import rag_answer
from app.core.database import get_db

@pytest.mark.asyncio
async def test_rag_pipeline_basic():
    """Test basic RAG pipeline functionality"""
    async for db in get_db():
        answer, citations, state = await rag_answer(
            user_query="test query",
            db=db
        )

        assert answer is not None
        assert isinstance(citations, list)
        assert state.query_embedding is not None
        break
```

## Performance Considerations

### Latency Breakdown

Typical latency for a query (with no cache hit):

- **embed_query**: 30-50ms
- **hybrid_retrieval**: 100-200ms (depends on DB size)
- **rerank**: 200-500ms (optional, can be disabled)
- **generate_initial_answer**: 500-2000ms (depends on model)
- **self_critique**: 300-800ms (optional, only if enabled)

**Total**: ~1.2-3.5s without cache

With cache hit: **<50ms**

### Optimization Tips

1. **Enable Semantic Caching**: Reduces latency by 95% for similar queries
2. **Disable Reranking**: Saves 200-500ms if not needed
3. **Disable Self-Critique**: Saves 300-800ms if answer quality is acceptable
4. **Adjust `RETRIEVAL_ALPHA`**: Lower values (more lexical) are faster but may reduce quality
5. **Use Smaller Models**: Ollama models are faster but may produce lower quality answers

## Troubleshooting

### No results returned

**Issue**: Query returns "I couldn't find relevant information..."

**Solutions**:
1. Check if documents have been processed and have embeddings
2. Lower `MIN_SIMILARITY_THRESHOLD` in config
3. Enable cascading fallback (default: enabled)
4. Check query text - very short queries may not work well

### High latency

**Issue**: Queries take too long (>5s)

**Solutions**:
1. Enable semantic caching
2. Disable reranking (`ENABLE_RERANKER=false`)
3. Disable self-critique (`ENABLE_SELF_CRITIQUE=false`)
4. Use faster models (e.g., GPT-3.5 instead of GPT-4)
5. Reduce `RETRIEVAL_CANDIDATES` and `CONTEXT_CHUNKS`

### Memory errors with large models

**Issue**: Out of memory when using Claude/GPT-4 with many chunks

**Solutions**:
1. The pipeline automatically adjusts chunk count based on model
2. Manually set `CONTEXT_CHUNKS` to a lower value
3. Use `SMALL_MODEL_CHUNK_LIMIT` for models with <10k context

### Ollama reranking fails

**Issue**: Reranking step fails or times out

**Solutions**:
1. Check if Ollama is running: `curl http://localhost:11434/api/tags`
2. Pull the rerank model: `docker-compose exec ollama ollama pull mistral`
3. Disable reranking as fallback: `ENABLE_RERANKER=false`

## Contributing

When contributing to the RAG pipeline:

1. **Follow the stage pattern**: Each stage should be a separate async function
2. **Use the `@timed` decorator**: For observability
3. **Handle errors gracefully**: Don't fail the entire pipeline on optional features
4. **Update tests**: Add tests for new features
5. **Document configuration**: Add new config parameters to this README

## License

This pipeline is part of the Enterprise RAG Chatbot project.

## References

- [RAG Survey Paper](https://arxiv.org/abs/2312.10997)
- [Self-RAG](https://arxiv.org/abs/2310.11511)
- [Hybrid Search Best Practices](https://www.pinecone.io/learn/hybrid-search/)
- [LangChain RAG](https://python.langchain.com/docs/use_cases/question_answering/)
