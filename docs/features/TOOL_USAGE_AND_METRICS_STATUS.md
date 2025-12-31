# Tool Usage Tracking & RAG Evaluation Metrics - Implementation Status

> **Last Updated**: 2025-11-23
> **Status**: Phase 1 & 2 COMPLETE ✅ | Phase 3 Ready to Start

---

## 📊 Executive Summary

All requested features have been implemented and are working:

### ✅ COMPLETED - RAG Evaluation Metrics Display
- **Issue Fixed**: Quality metrics now properly appear below each response
- **Root Cause**: EnhancedRAGAgent wasn't passing through `quality_metrics` from RAG service
- **Solution**: Modified `tool_registry.py` and `enhanced_rag_agent.py` to preserve quality_metrics
- **Verification**: Tested with live query - all 8 metrics now visible

### ✅ COMPLETED - Inline Tool Usage Tracking
- **Feature**: Shows which tools/steps were used and their execution order
- **Display**: Inline badge showing "🔧 N tools" with detailed expansion
- **Tracked Tools**: 15+ different pipeline steps with timing and details
- **Location**: `rag_service_enhanced.py` + `ChatInterfaceEnhanced.tsx`

### ✅ COMPLETED - Comprehensive Tool Usage Statistics System
- **Database**: `tool_usage_stats` table + materialized view for analytics
- **Service**: `tool_usage_tracker.py` with context manager pattern
- **API**: 4 endpoints for statistics, timeline, categories, top tools
- **Documentation**: Complete guide in `docs/features/TOOL_USAGE_TRACKING_GUIDE.md`

---

## 🎯 What's Working Right Now

### 1. RAG Evaluation Metrics (Below Each Response)

**What You See:**
```json
{
  "quality_metrics": {
    "faithfulness": 0.75,
    "answer_relevancy": 0.705,
    "context_relevancy": 0.694,
    "context_precision": 1.0,
    "rag_score": 0.775,
    "quality_level": "good",
    "classification_type": "ai_personal",
    "classification_confidence": 1.0
  }
}
```

**Includes:**
- Faithfulness score with claim-by-claim analysis
- Answer relevancy score
- Context relevancy with chunk breakdown
- Context precision with ranking analysis
- Overall RAG score (0-1)
- Quality level (poor/fair/good/excellent)
- Query classification type
- Classification confidence

**Files Modified:**
- `backend/app/agents/tool_registry.py` - Lines 539-553 (preserve quality_metrics)
- `backend/app/agents/enhanced_rag_agent.py` - Lines 629-649 (pass through quality_metrics)

### 2. Inline Tool Usage Display (Execution Order)

**What You See:**

**Inline Badge:**
```
🔧 15 tools  [hover for details]
```

**Expanded View:**
```
Tool Execution Order:
1. security_check @ 2ms - Query safety validation
2. query_preprocessing @ 15ms - Normalize and extract proper nouns
3. semantic_cache_check @ 23ms - Check Redis for cached results
4. query_reformulation @ 125ms - Generate query variations (acronyms + synonyms)
5. embedding_generation @ 456ms - Generate embeddings for 3 variation(s)
6. short_term_memory_search @ 512ms - Search session-specific documents (hybrid)
7. long_term_memory_search @ 834ms - Search all documents (hybrid + cascading fallback)
8. cross_encoder_reranking @ 1203ms - Rerank 25 candidates → top 5
9. llm_generation_with_context @ 2456ms - 5 chunks + 3 messages
10. quality_evaluation @ 2891ms - Calculate RAGAS metrics
... and 5 more
```

**Files Modified:**
- `backend/app/services/rag_service_enhanced.py` - Added `tools_used` tracking throughout query() method
- `frontend/src/components/ChatInterfaceEnhanced.tsx` - Added tool usage display in UI

### 3. Tool Usage Statistics Infrastructure

**Database Tables Created:**

1. **tool_usage_stats** - Records every tool invocation
   - tool_category (document_processing, web_scraping, rag_service, llm_service, mcp_tool)
   - tool_name (docling, playwright, gpt-4, cross_encoder_reranker, etc.)
   - operation (parse_pdf, scrape_url, rerank_chunks, generate_response)
   - Performance: latency_ms, success, error_message
   - Resources: tokens_used, cost_usd
   - Quality: quality_score, metadata

2. **tool_usage_summary** - Materialized view for fast analytics
   - Aggregated statistics by tool_category and tool_name
   - Metrics: total_invocations, success_rate, avg_latency, P95, cost, etc.

**API Endpoints Available:**

```bash
# Get aggregated tool usage statistics
GET /api/v1/tool-stats/summary?category=llm_service&days=7

# Get tool usage timeline (for charts)
GET /api/v1/tool-stats/timeline?days=30

# Get list of all tool categories
GET /api/v1/tool-stats/categories

# Get top N tools by metric
GET /api/v1/tool-stats/top-tools?limit=10&sort_by=invocations
```

**Response Example:**
```json
{
  "summary": {
    "total_tools": 12,
    "total_invocations": 1547,
    "total_successful": 1498,
    "total_failed": 49,
    "total_tokens_used": 245678,
    "total_cost_usd": 12.34,
    "date_range": {
      "start": "2025-11-16T00:00:00Z",
      "end": "2025-11-23T00:00:00Z",
      "days": 7
    }
  },
  "by_category": {
    "llm_service": [{
      "tool_name": "gpt-4",
      "total_invocations": 456,
      "successful_invocations": 450,
      "avg_latency_ms": 1234.56,
      "total_cost_usd": 8.90
    }],
    "rag_service": [{
      "tool_name": "cross_encoder_reranker",
      "total_invocations": 456,
      "successful_invocations": 456,
      "avg_latency_ms": 234.56,
      "p95_latency_ms": 450.00,
      "success_rate_pct": 100.00
    }]
  }
}
```

**Files Created:**
- `backend/migrations/005_add_tool_usage_tracking.sql` - Database schema
- `backend/app/services/tool_usage_tracker.py` - Tracking service
- `backend/app/api/routes/tool_stats_routes.py` - API endpoints
- `docs/features/TOOL_USAGE_TRACKING_GUIDE.md` - Complete documentation

---

## 🎨 What's Next - Frontend Dashboard (Phase 3)

### Recommended Implementation

Create a new **Tool Usage Dashboard** tab in the Evaluation Dashboard to visualize:

#### 1. Overview Cards
```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Total Tools    │  │ Total Calls     │  │  Success Rate   │
│      23         │  │    12,456       │  │     98.5%       │
└─────────────────┘  └─────────────────┘  └─────────────────┘

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Total Cost     │  │  Avg Latency    │  │  Total Tokens   │
│    $45.67       │  │    834ms        │  │    456,789      │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

#### 2. Tool Category Breakdown (Pie Chart)
```
        Document Processing (15%)
        Web Scraping (10%)
        RAG Services (40%)
        LLM Services (30%)
        Embedding (5%)
```

#### 3. Top Tools by Invocations (Bar Chart)
```
gpt-4                    ████████████████████ 1,234
cross_encoder_reranker   ███████████████ 987
playwright               ██████████ 567
docling                  ████████ 456
ollama/mistral           ███████ 345
```

#### 4. Performance Metrics Table
```
┌─────────────────────┬──────────┬─────────┬──────────┬──────────┐
│ Tool                │ Calls    │ Success │ Avg (ms) │ P95 (ms) │
├─────────────────────┼──────────┼─────────┼──────────┼──────────┤
│ gpt-4               │ 1,234    │ 99.2%   │ 1,234    │ 2,456    │
│ cross_encoder       │ 987      │ 100%    │ 234      │ 450      │
│ playwright          │ 567      │ 95.3%   │ 3,456    │ 8,900    │
│ docling             │ 456      │ 98.7%   │ 2,345    │ 5,678    │
└─────────────────────┴──────────┴─────────┴──────────┴──────────┘
```

#### 5. Cost Breakdown (if applicable)
```
GPT-4:          $35.67 (78%)
Claude:         $8.90  (19%)
Anthropic:      $1.10  (3%)
```

#### 6. Usage Timeline (Line Chart)
```
Tool Invocations Over Time
 ^
 │     ╱╲
 │    ╱  ╲     ╱╲
 │   ╱    ╲   ╱  ╲
 │  ╱      ╲ ╱    ╲
 │ ╱        ╲      ╲
 └──────────────────────>
   Mon  Tue  Wed  Thu  Fri
```

### Frontend Component Structure

```typescript
// New component: ToolUsageDashboard.tsx
export const ToolUsageDashboard: React.FC = () => {
  const [stats, setStats] = useState<ToolStats | null>(null);
  const [timeline, setTimeline] = useState<TimelineData[]>([]);
  const [days, setDays] = useState(7);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  useEffect(() => {
    // Fetch stats from /api/v1/tool-stats/summary
    // Fetch timeline from /api/v1/tool-stats/timeline
  }, [days, selectedCategory]);

  return (
    <div className="space-y-6">
      <OverviewCards stats={stats} />
      <CategoryBreakdown data={stats?.by_category} />
      <TopToolsChart data={stats?.all_tools} />
      <PerformanceMetricsTable data={stats?.all_tools} />
      <CostBreakdown data={stats?.all_tools} />
      <UsageTimeline data={timeline} />
    </div>
  );
};
```

### Chart Libraries to Use

**Recommended**: Recharts (already used in the project)
```bash
npm install recharts
```

**Alternative**: Chart.js or Victory

---

## 🔧 Optional - Service Instrumentation (Phase 4)

If you want to track ACTUAL service calls (not just inline RAG tracking), here's how to instrument each service:

### Example: LLM Service

```python
# In backend/app/services/llm_service.py

from app.services.tool_usage_tracker import tool_tracker, ToolCategory

async def generate(self, prompt, ...):
    # Wrap with tool tracker
    async with tool_tracker.track_tool_usage(
        category=ToolCategory.LLM_SERVICE,
        tool_name=model_name,  # "gpt-4", "ollama/mistral", etc.
        operation="generate_response",
        db=db,
        session_id=session_id,
        input_size=len(prompt)
    ) as tracker:
        # Existing code
        result = await self._call_openai(...)

        # Track metrics
        tracker.set_output_size(len(result["content"]))
        tracker.set_tokens_used(result.get("tokens", 0))
        tracker.set_cost(self._calculate_cost(result["tokens"], model_name))

        return result
```

### Example: Document Service

```python
# In backend/app/services/document_service.py

async def process_document(self, file_path, db):
    async with tool_tracker.track_tool_usage(
        category=ToolCategory.DOCUMENT_PROCESSING,
        tool_name="docling",
        operation="parse_pdf",
        db=db,
        input_size=file_size
    ) as tracker:
        result = await docling.parse_pdf(file_path)

        tracker.set_output_size(len(result["text"]))
        tracker.set_quality_score(result.get("confidence", 0.0))

        return result
```

### Example: Embedding Service

```python
# In backend/app/services/embedding_service.py

async def generate_embedding(self, text, db):
    async with tool_tracker.track_tool_usage(
        category=ToolCategory.EMBEDDING,
        tool_name=self.model_name,  # "all-MiniLM-L6-v2"
        operation="generate_embedding",
        db=db,
        input_size=len(text)
    ) as tracker:
        embedding = self.model.encode(text)

        tracker.set_output_size(len(embedding))

        return embedding
```

---

## 📝 Testing the Implementation

### 1. Test RAG Evaluation Metrics

```bash
# Test that quality_metrics appears in response
curl -s -X POST "http://localhost:8000/api/v1/query" \
  -F "query=Who is Aadhan?" \
  -F "use_cache=false" | jq '.quality_metrics'

# Expected output:
{
  "faithfulness": 0.75,
  "answer_relevancy": 0.705,
  "context_relevancy": 0.694,
  "context_precision": 1.0,
  "rag_score": 0.775,
  "quality_level": "good"
}
```

### 2. Test Inline Tool Usage

```bash
# Query and check tools_used field
curl -s -X POST "http://localhost:8000/api/v1/query" \
  -F "query=Who is Aadhan?" \
  -F "use_cache=false" | jq '.metadata.tools_used[] | {tool, timestamp_ms, details}'
```

### 3. Test Tool Stats API

```bash
# Get tool statistics
curl -s "http://localhost:8000/api/v1/tool-stats/summary?days=7" | jq '.summary'

# Get tool categories
curl -s "http://localhost:8000/api/v1/tool-stats/categories" | jq '.categories[].name'

# Get top tools
curl -s "http://localhost:8000/api/v1/tool-stats/top-tools?limit=5" | jq '.top_tools[].tool_name'
```

---

## 🎯 Consolidation Summary (Per User Request)

**User Feedback**: "don't duplicate, we already have few RAG services and can be confusing.. consolidate it"

**How We Addressed This**:

1. ✅ **No New RAG Services Created** - We fixed the existing `enhanced_rag_service.py`
2. ✅ **Single Tool Tracking Service** - One `tool_usage_tracker.py` for ALL tools
3. ✅ **Reused Existing Services** - Modified existing components instead of creating duplicates
4. ✅ **Consolidated API** - Single `/api/v1/tool-stats/*` namespace for all tool statistics
5. ✅ **Clear Separation of Concerns**:
   - `rag_service_enhanced.py` - Core RAG logic + inline tracking
   - `tool_usage_tracker.py` - Centralized statistics collection
   - `tool_stats_routes.py` - Single API for all analytics

**Result**: Clean, consolidated architecture with NO duplication

---

## 📋 Next Steps (Your Choice)

### Option 1: Add Frontend Dashboard (Recommended)
- Create `ToolUsageDashboard.tsx` component
- Add charts for visualization
- Integrate with Evaluation Dashboard

### Option 2: Instrument Additional Services (Optional)
- Add tracking to LLM service
- Add tracking to document processing
- Add tracking to embedding service
- Add tracking to web scraping tools

### Option 3: Both
- Do Phase 3 (frontend) first for immediate visibility
- Then add Phase 4 (instrumentation) incrementally

---

## 🔍 Files Changed Summary

### Phase 1: RAG Evaluation Metrics Fix
1. `backend/app/agents/tool_registry.py` - Pass through quality_metrics
2. `backend/app/agents/enhanced_rag_agent.py` - Include quality_metrics in response

### Phase 2: Tool Usage Infrastructure
1. `backend/migrations/005_add_tool_usage_tracking.sql` - Database schema
2. `backend/app/services/tool_usage_tracker.py` - Tracking service
3. `backend/app/api/routes/tool_stats_routes.py` - API endpoints
4. `backend/app/main.py` - Register tool stats router
5. `docs/features/TOOL_USAGE_TRACKING_GUIDE.md` - Documentation

### Phase 2B: Inline Tool Usage Display
1. `backend/app/services/rag_service_enhanced.py` - Add tools_used tracking
2. `frontend/src/components/ChatInterfaceEnhanced.tsx` - Display tool usage

---

**Status**: ✅ All requested features are WORKING and TESTED

**Next**: Choose Option 1, 2, or 3 above to continue
