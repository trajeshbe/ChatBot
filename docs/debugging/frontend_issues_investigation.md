# Frontend Issues Investigation Report

## Date: 2025-11-23

## Summary

Investigation into two frontend display issues reported by user:
1. Sources showing "NaN%" instead of actual percentage values (e.g., "82.7%")
2. RAG evaluation metrics missing below chat responses

## Investigation Findings

### Issue 1: Sources Displaying "NaN%"

**Current Code** (`ChatInterfaceEnhanced.tsx:638`):
```typescript
<span className="text-[10px] text-slate-500">
  {(source.relevance * 100).toFixed(0)}%
</span>
```

**Backend Response** (verified from `/tmp/aadhan_king_test.json`):
```json
"sources": [
  {
    "filename": "Short Story3.txt",
    "relevance": 0.8270125746726991,  // Valid decimal number
    ...
  },
  {
    "filename": "scraped_en.wikipedia.org_f4f8354f.txt",
    "relevance": 0.7778417958115468,  // Valid decimal number
    ...
  }
]
```

**Root Cause**:
- Backend returns valid decimal values (0.827, 0.778)
- Frontend code should work correctly: `(0.827 * 100).toFixed(0)` = "83%"
- "NaN%" indicates `source.relevance` is `undefined` or `null` when rendering
- Possible causes:
  1. Type mismatch between backend response and frontend interface
  2. Data transformation issue during state update
  3. Missing null/undefined check causing `undefined * 100 = NaN`

**Recommended Fix**:
Add defensive null checking and type validation:
```typescript
<span className="text-[10px] text-slate-500">
  {source.relevance !== undefined && source.relevance !== null && !isNaN(source.relevance)
    ? `${(source.relevance * 100).toFixed(0)}%`
    : 'N/A'}
</span>
```

### Issue 2: Missing RAG Evaluation Metrics

**Current Code** (`ChatInterfaceEnhanced.tsx:604-607`):
```typescript
{/* Evaluation Metrics */}
{message.quality_metrics && (
  <EvaluationMetrics metrics={message.quality_metrics} />
)}
```

**Backend Response** (from test):
```json
{
  "answer": "...",
  "sources": [...],
  "metadata": {
    "chunks_retrieved": 2,
    "cache_hit": false,
    "synthesis_method": "rag_service",
    "tool_usage": {...}
  }
}
```

**Root Cause**:
- Backend response does NOT include `quality_metrics` field
- The Enhanced RAG Agent (`backend/app/agents/enhanced_rag_agent.py`) is not calling the evaluation service
- Frontend code is correct - it expects `quality_metrics` from backend
- **This is a BACKEND issue**, not a frontend issue

**Where Evaluation Should Happen**:
1. User sends query → `main.py` → `enhanced_rag_agent.run()`
2. Enhanced RAG Agent should call evaluation service after getting RAG response
3. Evaluation service should return quality metrics
4. Enhanced RAG Agent should include `quality_metrics` in response

**Verification Needed**:
Check if:
1. `backend/app/services/evaluation_service.py` exists and is functional
2. Enhanced RAG Agent is configured to call evaluation
3. Evaluation is enabled in settings

## Recommended Actions

### Immediate Fix (Frontend - NaN% issue):
1. Update `ChatInterfaceEnhanced.tsx` line 638 with defensive null checking
2. Rebuild frontend: `docker-compose build frontend --no-cache`
3. Test with "Tell me about King Aadhan from the story" query

### Investigation Required (Backend - quality_metrics):
1. Check if `backend/app/services/evaluation_service.py` exists
2. Check `enhanced_rag_agent.py` to see if it calls evaluation
3. Check backend config for evaluation settings (might be disabled)
4. Enable evaluation in backend if disabled
5. Test to verify quality_metrics are returned

## Test Cases

### Test 1: Verify Source Relevance Display
```bash
curl -s -X POST http://localhost:8000/api/v1/query \
  -F "query=Tell me about King Aadhan from the story" \
  -F "model_id=gpt-4" \
  -F "top_k=5" \
  -F "similarity_threshold=0.70" | jq '.sources[] | {filename, relevance}'
```

**Expected**: Sources should show "83%" and "78%" in frontend (not "NaN%")

### Test 2: Verify Quality Metrics
```bash
curl -s -X POST http://localhost:8000/api/v1/query \
  -F "query=Tell me about King Aadhan from the story" \
  -F "model_id=gpt-4" | jq 'has("quality_metrics")'
```

**Current**: Returns `false` (quality_metrics missing)
**Expected**: Returns `true` (quality_metrics should be present)

## Conclusion

**Issue 1 (NaN%)**: Frontend defensive coding needed - add null checks

**Issue 2 (Missing metrics)**: Backend issue - evaluation service not being called. Requires backend investigation and configuration.
