# RAG Evaluation Metrics Enablement Guide

## Date: 2025-11-23

## Status Summary

| Issue | Status | Action Required |
|-------|--------|-----------------|
| Frontend NaN% sources display | ✅ **FIXED** | Frontend rebuilt and restarted |
| Backend evaluation metrics missing | ⚠️ **REQUIRES CONFIGURATION** | Enable evaluation in backend config |

---

## Issue: Missing RAG Evaluation Metrics

### Current State

The backend **does NOT return** `quality_metrics` in the query response:

```json
{
  "answer": "...",
  "sources": [...],
  "metadata": {
    "chunks_retrieved": 2,
    "tool_usage": {...}
    // ❌ NO quality_metrics field
  }
}
```

**Frontend code is correct** - it expects and will display metrics if they exist:
```typescript
// ChatInterfaceEnhanced.tsx:604-607
{message.quality_metrics && (
  <EvaluationMetrics metrics={message.quality_metrics} />
)}
```

### Root Cause

**Evaluation is NOT enabled** in the backend configuration:

1. **Missing Config Settings**: `backend/app/core/config.py` does NOT have:
   - `ENABLE_EVALUATION`
   - `RAGAS_ENABLED`
   - `ENABLE_FAITHFULNESS`
   - `ENABLE_ANSWER_RELEVANCY`
   - `ENABLE_CONTEXT_RELEVANCY`

2. **Evaluation Service Exists**: `backend/app/services/evaluation_service.py` ✅ EXISTS and is functional

3. **Agent Not Calling Evaluation**: Enhanced RAG Agent is not configured to call the evaluation service

---

## Solution: Enable Evaluation Metrics

### Step 1: Add Evaluation Settings to Config

**File**: `backend/app/core/config.py`

Add these settings to the `Settings` class:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # ===== EVALUATION SETTINGS =====
    # Enable/disable evaluation
    ENABLE_EVALUATION: bool = True  # Master toggle
    RAGAS_ENABLED: bool = True      # Enable RAGAS metrics

    # Individual metric toggles
    ENABLE_FAITHFULNESS: bool = True           # Check if answer is grounded in context
    ENABLE_ANSWER_RELEVANCY: bool = True       # Check if answer addresses the query
    ENABLE_CONTEXT_RELEVANCY: bool = True      # Check if retrieved context is relevant
    ENABLE_CONTEXT_PRECISION: bool = True      # Check precision of context retrieval
    ENABLE_CITATION_ACCURACY: bool = True      # Check citation accuracy

    # Evaluation performance
    EVALUATION_ASYNC: bool = True              # Run evaluation asynchronously
    EVALUATION_BATCH_SIZE: int = 10            # Batch size for evaluation
    EVALUATION_CACHE_TTL: int = 3600           # Cache results for 1 hour
    EVALUATION_MIN_SCORE: float = 0.7          # Minimum acceptable score

    # LLM for evaluation (LLM-as-a-Judge)
    EVALUATION_LLM_MODEL: str = "gpt-4-turbo-preview"  # Model for evaluation

    # ... rest of existing settings ...
```

### Step 2: Update Enhanced RAG Agent to Call Evaluation

**File**: `backend/app/agents/enhanced_rag_agent.py`

Add evaluation call after RAG response:

```python
from app.services.evaluation_service import EvaluationService
from app.core.config import settings

# Initialize evaluation service
evaluation_service = EvaluationService()

# In the enhanced_rag_agent.run() method, after getting RAG response:
async def run(self, query, session_id, user_preferences):
    # ... existing code to get rag_response ...

    # Add evaluation if enabled
    quality_metrics = None
    if settings.ENABLE_EVALUATION:
        try:
            evaluation_result = await evaluation_service.evaluate_response(
                query=query,
                response=rag_response["answer"],
                context_chunks=rag_response.get("sources", []),
                db=state["user_preferences"].get("db")
            )
            quality_metrics = evaluation_result
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            # Continue without metrics on failure

    # Add quality_metrics to response
    return {
        "answer": rag_response["answer"],
        "sources": rag_response["sources"],
        "metadata": {
            ...rag_response["metadata"],
            "quality_metrics": quality_metrics  # ✅ ADD THIS
        }
    }
```

### Step 3: Install Evaluation Dependencies (if needed)

Check if RAGAS is installed in `backend/requirements.txt`:

```bash
# Check if ragas is in requirements
grep -i ragas backend/requirements.txt
```

If not found, add:
```txt
ragas>=0.1.0
```

Then rebuild backend:
```bash
docker-compose build backend
docker-compose restart backend
```

---

## What Evaluation Metrics Provide

Once enabled, the backend will return quality metrics like:

```json
{
  "answer": "...",
  "sources": [...],
  "metadata": {
    "chunks_retrieved": 2,
    "quality_metrics": {
      "faithfulness": 0.92,           // Answer grounded in retrieved context
      "answer_relevancy": 0.88,       // Answer addresses the query
      "context_relevancy": 0.85,      // Retrieved context is relevant
      "context_precision": 0.91,      // Precision of retrieval
      "citation_accuracy": 0.94,      // Citations are accurate
      "overall_score": 0.90           // Combined quality score
    }
  }
}
```

The frontend will automatically display these metrics below the chat response.

---

## Performance Considerations

**⚠️ Important**: Enabling evaluation adds:
- **Latency**: +2-5 seconds per query (for evaluation LLM calls)
- **Cost**: Additional LLM API calls for each metric
- **Tokens**: ~500-1000 tokens per evaluation

**Recommendations**:
1. **Development**: Enable all metrics for debugging
2. **Production**: Enable only critical metrics (faithfulness, answer_relevancy)
3. **Async Evaluation**: Set `EVALUATION_ASYNC: true` to avoid blocking user response
4. **Caching**: Enable `EVALUATION_CACHE_TTL` to cache results

---

## Testing

After enabling evaluation:

### Test 1: Verify Config
```bash
docker-compose exec backend python -c "from app.core.config import settings; print(f'Evaluation enabled: {settings.ENABLE_EVALUATION}')"
```

**Expected**: `Evaluation enabled: True`

### Test 2: Query with Evaluation
```bash
curl -s -X POST http://localhost:8000/api/v1/query \
  -F "query=Tell me about King Aadhan from the story" \
  -F "model_id=gpt-4" | jq 'has("quality_metrics")'
```

**Expected**: `true` (quality_metrics present)

### Test 3: Check Metrics Content
```bash
curl -s -X POST http://localhost:8000/api/v1/query \
  -F "query=Tell me about King Aadhan from the story" \
  -F "model_id=gpt-4" | jq '.quality_metrics'
```

**Expected**: JSON object with metric scores

---

## Alternative: Simplified Evaluation

If full RAGAS evaluation is too heavy, you can implement lightweight evaluation:

```python
# Simplified evaluation without RAGAS
def simple_evaluation(query, answer, sources):
    return {
        "source_count": len(sources),
        "answer_length": len(answer),
        "has_sources": len(sources) > 0,
        "avg_relevance": sum(s.get("relevance", 0) for s in sources) / len(sources) if sources else 0
    }
```

This provides basic metrics without additional LLM calls.

---

## Summary

**Frontend**: ✅ Fixed and deployed

**Backend Evaluation**: Requires:
1. Add evaluation settings to `config.py`
2. Update Enhanced RAG Agent to call `evaluation_service`
3. Optional: Install RAGAS if not present
4. Rebuild and restart backend

**Decision Required**: Do you want to enable full evaluation metrics?
- **Yes**: Follow steps above (adds latency/cost but provides quality insights)
- **No**: Use simplified metrics or skip evaluation (faster but no quality visibility)

---

## Files to Modify

1. `backend/app/core/config.py` - Add evaluation settings
2. `backend/app/agents/enhanced_rag_agent.py` - Call evaluation service
3. `backend/requirements.txt` - Add ragas dependency (if needed)

---

## Related Documentation

- Evaluation Service: `backend/app/services/evaluation_service.py`
- Evaluation API: `backend/app/api/routes/evaluation.py`
- Frontend Component: `frontend/src/components/EvaluationMetrics.tsx`
- Investigation Report: `docs/debugging/frontend_issues_fix_summary.md`
