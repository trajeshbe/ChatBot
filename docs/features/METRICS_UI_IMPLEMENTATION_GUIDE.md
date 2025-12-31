# UI-Controlled Metrics & Evaluation - Implementation Guide

## Overview

This guide shows how to add UI controls for enabling/disabling evaluation and performance metrics without requiring backend configuration changes.

## Implementation Status

✅ **Completed**:
1. SettingsPanel component created (`frontend/src/components/SettingsPanel.tsx`)

⚠️ **Remaining Tasks** (Quick Implementation Required):
2. PerformanceMetrics display component
3. Update ChatInterfaceEnhanced to integrate settings
4. Update backend to accept `enable_evaluation` parameter
5. Add lightweight performance metrics to backend response

---

## 1. Performance Metrics Component ✅

Create: `frontend/src/components/PerformanceMetrics.tsx`

```typescript
import React from 'react';
import { Clock, Zap, Database, Activity } from 'lucide-react';

interface PerformanceMetricsProps {
  metadata: {
    chunks_retrieved?: number;
    tool_usage?: {
      total_time_ms?: number;
      tool_timing?: Record<string, number>;
    };
    response_time_ms?: number;
    tokens_used?: number;
  };
}

const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({ metadata }) => {
  const responseTime = metadata.response_time_ms || metadata.tool_usage?.total_time_ms || 0;
  const chunksRetrieved = metadata.chunks_retrieved || 0;
  const tokensUsed = metadata.tokens_used || 0;

  return (
    <div className="mt-2 p-3 bg-gray-50 rounded-lg border border-gray-200">
      <div className="flex items-center gap-4 text-xs text-gray-600">
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          <span>{(responseTime / 1000).toFixed(2)}s</span>
        </div>
        <div className="flex items-center gap-1">
          <Database className="w-3 h-3" />
          <span>{chunksRetrieved} chunks</span>
        </div>
        {tokensUsed > 0 && (
          <div className="flex items-center gap-1">
            <Activity className="w-3 h-3" />
            <span>{tokensUsed.toLocaleString()} tokens</span>
          </div>
        )}
        {metadata.tool_usage?.tool_timing && Object.entries(metadata.tool_usage.tool_timing).map(([tool, time]) => (
          <div key={tool} className="flex items-center gap-1" title={`${tool} execution time`}>
            <Zap className="w-3 h-3" />
            <span className="text-[10px]">{tool}: {(time / 1000).toFixed(2)}s</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PerformanceMetrics;
```

---

## 2. Update ChatInterfaceEnhanced.tsx

Add at the top of the file (after imports):

```typescript
import SettingsPanel, { MetricsSettings } from './SettingsPanel';
import PerformanceMetrics from './PerformanceMetrics';
```

Add state for metrics settings:

```typescript
const [metricsSettings, setMetricsSettings] = useState<MetricsSettings>({
  enableEvaluation: false,
  showPerformanceMetrics: true,
});
```

Add SettingsPanel before the chat messages:

```typescript
{/* Add this before the messages map */}
<SettingsPanel onSettingsChange={setMetricsSettings} />
```

Update the sendMessage function to include evaluation flag:

```typescript
const sendMessage = async () => {
  // ... existing code ...

  const formData = new FormData();
  formData.append('query', input);
  formData.append('session_id', sessionId);
  formData.append('model_id', selectedModel);
  formData.append('enable_evaluation', metricsSettings.enableEvaluation.toString());  // ✅ ADD THIS
  // ... rest of existing code ...
};
```

Add performance metrics and evaluation metrics below each assistant message:

```typescript
{/* Inside the message mapping, after the answer */}
{message.role === 'assistant' && (
  <>
    {/* Existing sources display */}

    {/* Performance Metrics - show if enabled */}
    {metricsSettings.showPerformanceMetrics && message.metadata && (
      <PerformanceMetrics metadata={message.metadata} />
    )}

    {/* Evaluation Metrics - show if enabled and present */}
    {metricsSettings.enableEvaluation && message.quality_metrics && (
      <EvaluationMetrics metrics={message.quality_metrics} />
    )}
  </>
)}
```

---

## 3. Backend Changes

### A. Update `backend/app/main.py`

Add evaluation parameter to the query endpoint:

```python
@app.post("/api/v1/query")
async def query_endpoint(
    request: Request,
    query: str = Form(...),
    session_id: Optional[str] = Form(None),
    use_cache: bool = Form(True),
    model_id: Optional[str] = Form(None),
    conversation_history: Optional[str] = Form(None),
    top_k: Optional[int] = Form(None),
    similarity_threshold: Optional[float] = Form(None),
    min_similarity_threshold: Optional[float] = Form(None),
    no_relevant_docs_threshold: Optional[float] = Form(None),
    enable_evaluation: bool = Form(False),  # ✅ ADD THIS
    db: AsyncSession = Depends(get_db)
):
    # ... existing code ...

    user_preferences = {
        "top_k": top_k,
        "similarity_threshold": similarity_threshold,
        "min_similarity_threshold": min_similarity_threshold,
        "no_relevant_docs_threshold": no_relevant_docs_threshold,
        "enable_evaluation": enable_evaluation,  # ✅ ADD THIS
        # ... other preferences
    }

    result = await enhanced_rag_agent.run(
        query=query,
        session_id=session_id,
        user_preferences=user_preferences
    )

    # Add performance metrics to response
    if "metadata" in result:
        result["metadata"]["response_time_ms"] = (time.time() - start_time) * 1000  # ✅ ADD THIS
        result["metadata"]["tokens_used"] = result.get("tokens", 0)  # ✅ ADD THIS if available

    return result
```

### B. Update `backend/app/agents/enhanced_rag_agent.py`

Add evaluation logic:

```python
async def run(self, query, session_id, user_preferences):
    # ... existing code ...

    # Get RAG response
    rag_response = await rag_service.query(...)

    # Conditionally run evaluation if enabled
    quality_metrics = None
    if user_preferences.get("enable_evaluation", False):
        try:
            from app.services.evaluation_service import EvaluationService
            evaluation_service = EvaluationService()

            evaluation_result = await evaluation_service.evaluate_response(
                query=query,
                response=rag_response["answer"],
                context_chunks=rag_response.get("sources", []),
                db=user_preferences.get("db")
            )
            quality_metrics = evaluation_result
            logger.info(f"Evaluation metrics: {quality_metrics}")
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            # Continue without metrics on failure

    # Return with optional quality metrics
    return {
        "answer": rag_response["answer"],
        "sources": rag_response["sources"],
        "metadata": {
            ...rag_response.get("metadata", {}),
            "quality_metrics": quality_metrics  # ✅ ADD THIS (will be None if evaluation disabled)
        }
    }
```

### C. Optional: Add Lightweight Performance Tracking

If evaluation is disabled, still return lightweight performance metrics:

```python
# In rag_service.py or enhanced_rag_agent.py
import time

async def query(self, ...):
    start_time = time.time()

    # ... existing query logic ...

    # Always add performance metrics (lightweight)
    return {
        "answer": answer,
        "sources": sources,
        "metadata": {
            "chunks_retrieved": len(sources),
            "response_time_ms": (time.time() - start_time) * 1000,
            "tool_usage": {
                "total_time_ms": (time.time() - start_time) * 1000,
                # ... existing tool timing
            }
        }
    }
```

---

## 4. Testing

### A. Test Settings Persistence

```bash
# Settings should persist in localStorage
# 1. Open UI at http://localhost:3001
# 2. Toggle evaluation ON
# 3. Refresh page
# 4. Verify toggle is still ON
```

### B. Test Evaluation Disabled (Fast)

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=Tell me about King Aadhan" \
  -F "model_id=gpt-4" \
  -F "enable_evaluation=false" | jq '{
    has_quality_metrics: has("quality_metrics"),
    has_performance: (.metadata | has("response_time_ms")),
    response_time: .metadata.response_time_ms
  }'
```

**Expected**:
```json
{
  "has_quality_metrics": false,
  "has_performance": true,
  "response_time": 2500  // ~2.5s (fast, no evaluation)
}
```

### C. Test Evaluation Enabled (Slower)

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=Tell me about King Aadhan" \
  -F "model_id=gpt-4" \
  -F "enable_evaluation=true" | jq '{
    has_quality_metrics: has("quality_metrics"),
    quality_metrics: .quality_metrics,
    has_performance: (.metadata | has("response_time_ms")),
    response_time: .metadata.response_time_ms
  }'
```

**Expected**:
```json
{
  "has_quality_metrics": true,
  "quality_metrics": {
    "faithfulness": 0.92,
    "answer_relevancy": 0.88,
    "context_relevancy": 0.85
  },
  "has_performance": true,
  "response_time": 7200  // ~7.2s (slower, with evaluation)
}
```

---

## 5. Deployment

```bash
# Frontend
docker-compose build frontend
docker-compose restart frontend

# Backend
docker-compose build backend
docker-compose restart backend

# Verify services
docker-compose ps
```

---

## UI Features Summary

### Settings Panel Features:
1. **Collapsible panel** - Expands/collapses on click
2. **Enable RAG Evaluation Toggle** - Shows warning about latency
3. **Show Performance Metrics Toggle** - Always available, no performance impact
4. **Status Indicators** - Visual feedback for what's enabled
5. **Tooltips** - Explains what each option does
6. **LocalStorage persistence** - Settings survive page refresh

### Performance Metrics Display:
- Response time (seconds)
- Chunks retrieved
- Tokens used
- Tool execution times

### Evaluation Metrics Display (when enabled):
- Faithfulness score
- Answer relevancy score
- Context relevancy score
- Context precision score
- Overall quality score

---

## Cost/Performance Trade-offs

| Setting | Response Time | Cost per Query | Quality Insights |
|---------|---------------|----------------|------------------|
| **Evaluation OFF** | ~2-3s | $0.005-0.01 | None |
| **Evaluation ON** | ~5-8s | $0.02-0.03 | Detailed quality metrics |

**Recommendation**:
- **Development**: Enable evaluation to debug quality issues
- **Production**: Disable by default, enable per-query when needed
- **Analytics**: Enable for sample of queries (10%) to track quality trends

---

## Implementation Checklist

- [x] Create SettingsPanel.tsx
- [ ] Create PerformanceMetrics.tsx
- [ ] Update ChatInterfaceEnhanced.tsx to integrate settings
- [ ] Update backend/app/main.py to accept enable_evaluation
- [ ] Update backend/app/agents/enhanced_rag_agent.py to conditionally run evaluation
- [ ] Test with evaluation disabled (should be fast)
- [ ] Test with evaluation enabled (should show metrics)
- [ ] Deploy frontend and backend

---

## File Locations

```
frontend/src/components/
├── SettingsPanel.tsx (✅ Created)
├── PerformanceMetrics.tsx (❌ To Create)
└── ChatInterfaceEnhanced.tsx (❌ To Update)

backend/app/
├── main.py (❌ To Update)
└── agents/
    └── enhanced_rag_agent.py (❌ To Update)
```

---

## Summary

This implementation provides:
1. ✅ **User control** - Enable/disable metrics from UI
2. ✅ **No backend config required** - Settings passed per request
3. ✅ **Performance-conscious** - Evaluation only when needed
4. ✅ **Persistent** - Settings saved in localStorage
5. ✅ **Clear cost indicators** - Users warned about latency/cost trade-offs
