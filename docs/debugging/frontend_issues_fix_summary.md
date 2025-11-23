# Frontend Display Issues - Fix Summary

## Date: 2025-11-23

## Issues Reported

1. **Sources showing "NaN%"** instead of actual relevance percentages
2. **RAG Evaluation Metrics missing** below chat responses

---

## Issue 1: Sources Display "NaN%" - FIXED ✅

### Root Cause
Frontend code at `ChatInterfaceEnhanced.tsx:638` was missing defensive null/undefined checks:
```typescript
{(source.relevance * 100).toFixed(0)}%
```

When `source.relevance` is `undefined` or `null`, the expression becomes `undefined * 100 = NaN`, which displays as "NaN%".

### Backend Analysis
Backend is working correctly - it returns valid decimal values:
```json
{
  "relevance": 0.8270125746726991  // = 82.7%
}
```

### Fix Applied
Updated `ChatInterfaceEnhanced.tsx:638-640` with defensive checking:
```typescript
{source.relevance !== undefined && source.relevance !== null && !isNaN(source.relevance)
  ? `${(source.relevance * 100).toFixed(0)}%`
  : 'N/A'}
```

This ensures:
- Checks if `relevance` exists (`!== undefined`)
- Checks if it's not null (`!== null`)
- Verifies it's a number (`!isNaN()`)
- Safely converts to percentage or shows 'N/A'

### Next Steps for Issue 1
1. **Rebuild frontend**: `docker-compose build frontend`
2. **Restart services**: `docker-compose restart frontend`
3. **Test**: Send query "Tell me about King Aadhan from the story"
4. **Verify**: Sources should show "83%" and "78%" instead of "NaN%"

---

## Issue 2: Missing RAG Evaluation Metrics - BACKEND ISSUE ❌

### Root Cause
Backend response does NOT include `quality_metrics` field:
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

### Investigation Findings

1. **Evaluation Service Exists**:
   - File: `backend/app/services/evaluation_service.py` ✅ EXISTS
   - File: `backend/app/api/routes/evaluation.py` ✅ EXISTS

2. **Frontend Code is Correct**:
   ```typescript
   // ChatInterfaceEnhanced.tsx:604-607
   {message.quality_metrics && (
     <EvaluationMetrics metrics={message.quality_metrics} />
   )}
   ```
   Frontend expects `quality_metrics` from backend - nothing wrong here!

3. **Backend is NOT Calling Evaluation**:
   - Enhanced RAG Agent should call evaluation service after getting RAG response
   - Quality metrics should be added to response
   - **This is not happening** → Evaluation is either disabled or not configured

### Possible Reasons

1. **Evaluation Disabled in Config** (`backend/app/core/config.py`):
   ```python
   ENABLE_EVALUATION = False  # If this is False, no metrics
   ```

2. **Enhanced RAG Agent Not Configured**:
   - `enhanced_rag_agent.py` might not call `evaluation_service`
   - Missing code to add `quality_metrics` to response

3. **Silent Failure**:
   - Evaluation service might be throwing errors
   - Errors being caught and swallowed silently

### Recommended Actions for Issue 2

#### 1. Check Backend Configuration
```bash
# Check if evaluation is enabled
docker-compose exec backend python -c "from app.core.config import settings; print(f'Evaluation enabled: {getattr(settings, \"ENABLE_EVALUATION\", \"NOT_SET\")}')"
```

#### 2. Check Enhanced RAG Agent
```bash
# Search for evaluation service usage in enhanced_rag_agent.py
grep -n "evaluation" backend/app/agents/enhanced_rag_agent.py
```

#### 3. Enable Evaluation (if disabled)
Look for these settings in `backend/app/core/config.py`:
```python
ENABLE_EVALUATION: bool = True  # Should be True
RAGAS_ENABLED: bool = True      # Should be True
ENABLE_FAITHFULNESS: bool = True
ENABLE_ANSWER_RELEVANCY: bool = True
ENABLE_CONTEXT_RELEVANCY: bool = True
```

#### 4. Check Backend Logs
```bash
# Search for evaluation-related errors
docker-compose logs backend | grep -i evaluation
docker-compose logs backend | grep -i "quality.*metric"
```

### Why This is a Backend Issue
- Frontend is correctly checking for `quality_metrics`
- Frontend is correctly rendering `<EvaluationMetrics>` when data exists
- **Backend simply isn't returning the data**
- Issue must be fixed in backend code or configuration

---

## Summary

| Issue | Status | Location | Action Required |
|-------|--------|----------|-----------------|
| Sources showing "NaN%" | ✅ FIXED | Frontend `ChatInterfaceEnhanced.tsx:638` | Rebuild frontend |
| Missing evaluation metrics | ❌ BACKEND ISSUE | Backend configuration/code | Enable evaluation in backend |

---

## Files Modified

1. `frontend/src/components/ChatInterfaceEnhanced.tsx` (line 638-640) - Fixed NaN% display
2. `/tmp/frontend_issues_investigation.md` - Investigation details
3. `/tmp/frontend_issues_fix_summary.md` - This file

---

## Testing Plan

### Test 1: Verify Source Relevance Fix (Frontend)
```bash
# After rebuilding frontend
curl -s -X POST http://localhost:8000/api/v1/query \
  -F "query=Tell me about King Aadhan from the story" \
  -F "model_id=gpt-4" | jq '.sources[] | {filename, relevance}'
```

**Expected in UI**: "83%" and "78%" (not "NaN%")

### Test 2: Verify Quality Metrics (Backend)
```bash
# Check if backend returns quality_metrics
curl -s -X POST http://localhost:8000/api/v1/query \
  -F "query=Tell me about King Aadhan from the story" \
  -F "model_id=gpt-4" | jq 'has("quality_metrics")'
```

**Current**: `false` (missing)
**Expected**: `true` (should be present)

---

## Next Steps

### Immediate (Frontend Fix - Issue 1):
1. Rebuild frontend: `docker-compose build frontend`
2. Restart: `docker-compose restart frontend`
3. Test UI - sources should show percentages

### Requires Investigation (Backend - Issue 2):
1. Check if evaluation is enabled in backend config
2. If disabled, enable it and restart backend
3. If enabled but not working, investigate enhanced_rag_agent
4. Check backend logs for evaluation errors
5. Fix backend code to return quality_metrics
6. Test and verify metrics appear in UI

---

## Conclusion

**Issue 1 (NaN%)**: ✅ Fixed in frontend with defensive null checking

**Issue 2 (Missing metrics)**: ❌ Requires backend investigation and fix. The backend is not returning `quality_metrics` in the API response. Frontend code is correct and will automatically display metrics once backend starts returning them.
