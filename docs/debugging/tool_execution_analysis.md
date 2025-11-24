# Tool Execution Analysis - Moneycontrol Query

## 🔍 What Happened

### Query Details
- **User Query**: "can you get me the headlines of https://www.moneycontrol.com/ today"
- **Endpoint Called**: `/api/v1/query`
- **Model Used**: `llama3.2:3b`
- **Execution Time**: 23,590 ms (~24 seconds)

---

## 📊 Execution Flow (Current Behavior)

### Step 1: Query Received
```
POST /api/v1/query
{
  "query": "can you get me the headlines of https://www.moneycontrol.com/ today",
  "model_id": "llama3.2:3b"
}
```

### Step 2: RAG Service Processing
```
app.services.rag_service_enhanced - Processing query
├── Searched document database for relevant chunks
├── No relevant context found (no moneycontrol.com docs in DB)
└── WARNING: "⚠️ No relevant context found for query"
```

### Step 3: LLM Response Generation
```
- LLM generated generic response
- No tool invocation occurred
- No web scraping happened
- Response: "I don't have direct access to external websites..."
```

### Step 4: Database Storage
```
- Stored query in messages table
- Stored audit log
- Cached query result (3600s TTL)
- Returned response with 0 sources
```

---

## ❌ Problems Identified

### 1. **No Tool Selection**
- The system did NOT detect that this query requires web scraping
- No tool selection logic was executed
- Query was treated as pure RAG document search

### 2. **No Multi-Tool Agent**
- The `/api/v1/query` endpoint currently only does document RAG
- It does NOT use the multi-tool agent system
- Tools like `smart_extraction` or `web_scraper` were not considered

### 3. **Missing Intent Detection**
- No classification of query type:
  - Document search? ❌
  - Web scraping? ❌
  - Multi-tool needed? ❌

---

## ✅ Expected Behavior (Multi-Tool Agent)

### What SHOULD Have Happened:

```
1. Query Classification
   ├── Detect URL in query: https://www.moneycontrol.com/
   ├── Detect intent: "get headlines" = web scraping task
   └── Classify as: WEB_SCRAPING_QUERY

2. Tool Selection
   ├── Query Tool Registry for available tools
   ├── Match intent to tools:
   │   ├── smart_extraction (BEST MATCH)
   │   ├── web_scraper (ALTERNATIVE)
   │   └── navigation_agent (IF MULTI-PAGE)
   └── Select: smart_extraction tool

3. Tool Execution
   ├── Invoke smart_extraction tool with:
   │   - url: "https://www.moneycontrol.com/"
   │   - instructions: "Extract headlines from the page"
   │   - llm_provider: "openai"
   ├── Tool executes web scraping
   └── Returns structured data (headlines)

4. Response Generation
   ├── Combine tool results
   ├── Format for user
   └── Include metadata:
       - tools_used: ["smart_extraction"]
       - tool_timing: {"smart_extraction": 2500ms}
       - execution_summary: {success: true}
```

---

## 🛠️ Current System Architecture

```
Frontend
   ↓
POST /api/v1/query
   ↓
rag_service_enhanced.query()
   ├── Generate embeddings
   ├── Search documents (PostgreSQL + pgvector)
   ├── Retrieve relevant chunks
   ├── Build context
   └── Generate LLM response
       ↓
   Return answer (NO TOOL CALLS)
```

---

## 🎯 Required Architecture (Multi-Tool Agent)

```
Frontend
   ↓
POST /api/v1/query
   ↓
multi_tool_agent.process_query()
   ├── 1. CLASSIFY QUERY
   │   ├── Check for URLs → web scraping
   │   ├── Check for document refs → RAG search
   │   └── Determine intent
   │
   ├── 2. SELECT TOOLS
   │   ├── Query tool_registry
   │   ├── Match tools to intent
   │   └── Rank by confidence
   │
   ├── 3. EXECUTE TOOLS (in parallel if possible)
   │   ├── smart_extraction.execute()
   │   ├── document_rag.execute() (if needed)
   │   └── Collect results
   │
   ├── 4. SYNTHESIZE RESULTS
   │   ├── Combine tool outputs
   │   ├── Resolve conflicts
   │   └── Generate final answer
   │
   └── 5. RETURN WITH METADATA
       ├── Answer
       ├── Sources
       └── Tool execution metadata:
           - tools_used: [...]
           - tool_timing: {...}
           - tool_execution_summary: {...}
```

---

## 📝 Missing Components

### 1. Query Classifier
**File**: `backend/app/services/query_classifier.py`
**Status**: ❌ Not integrated with `/api/v1/query` endpoint

**Needed**:
- URL detection
- Intent classification
- Query type determination

### 2. Multi-Tool Orchestrator
**File**: `backend/app/agents/multi_tool_agent.py` or `enhanced_rag_agent.py`
**Status**: ⚠️ Enhanced RAG agent exists but NOT called from `/api/v1/query`

**Needed**:
- Tool selection logic
- Parallel tool execution
- Result synthesis

### 3. Tool Registry Integration
**File**: `backend/app/agents/tool_registry.py`
**Status**: ✅ Exists (Phase 1-5 work)
**Integration**: ❌ Not called from query endpoint

**Needed**:
- Connect query endpoint to tool registry
- Enable tool discovery and selection

### 4. Endpoint Routing
**Current**: `/api/v1/query` → `rag_service_enhanced.query()`
**Needed**: `/api/v1/query` → `multi_tool_agent.process_query()`

---

## 🔧 Immediate Fix Needed

### Option 1: Modify `/api/v1/query` Endpoint
```python
# backend/app/api/routes/rag_pipeline_routes.py

@router.post("/api/v1/query")
async def query_rag(request: QueryRequest, db: Session = Depends(get_db)):
    # CURRENT: Direct RAG
    # result = rag_service.query(request.query, ...)
    
    # NEEDED: Multi-tool agent
    from app.agents.multi_tool_agent import multi_tool_agent
    result = await multi_tool_agent.process_query(
        query=request.query,
        session_id=request.session_id,
        model_id=request.model_id
    )
    return result
```

### Option 2: Create New Endpoint
```python
# Keep /api/v1/query for RAG only
# Add /api/v1/agent/query for multi-tool

@router.post("/api/v1/agent/query")
async def agent_query(request: QueryRequest, db: Session = Depends(get_db)):
    from app.agents.multi_tool_agent import multi_tool_agent
    result = await multi_tool_agent.process_query(...)
    return result
```

---

## 📈 Phases Completed vs Needed

| Phase | Component | Status | Note |
|-------|-----------|--------|------|
| 1 | Tool Registry | ✅ Complete | Exists with 7 tools |
| 2 | Tool Implementations | ✅ Complete | smart_extraction, web_scraper, etc. |
| 3 | Query Classifier | ⚠️ Exists | Not integrated |
| 4 | LLM-based Selection | ⚠️ Partial | Not used by query endpoint |
| 5 | Enhanced RAG Agent | ⚠️ Exists | Not called from endpoint |
| 6 | API Integration | ✅ Complete | Tool Discovery & MCP APIs |
| **7** | **Query Endpoint Integration** | ❌ **MISSING** | **NOT YET DONE** |

---

## 🎯 Solution: Phase 7 Implementation

**Goal**: Integrate multi-tool agent with `/api/v1/query` endpoint

**Tasks**:
1. Modify query endpoint to call multi-tool agent
2. Add query classification at entry point
3. Enable tool selection and execution
4. Return enhanced metadata with tool usage

**Expected Result**:
- User queries with URLs automatically trigger web scraping
- Document queries trigger RAG search
- Multi-intent queries use multiple tools
- All tool executions tracked in metadata

---

## 🧪 Test Case

**Input**:
```json
{
  "query": "can you get me the headlines of https://www.moneycontrol.com/ today",
  "model_id": "gpt-4"
}
```

**Expected Output** (after Phase 7):
```json
{
  "answer": "Here are today's headlines from MoneyControl:\n1. Market hits record high...\n2. Rupee weakens against dollar...\n...",
  "sources": [
    {
      "url": "https://www.moneycontrol.com/",
      "type": "web_scrape",
      "extraction_method": "smart_extraction"
    }
  ],
  "metadata": {
    "tool_usage": {
      "tools_used": ["smart_extraction"],
      "tool_timing": {
        "smart_extraction": 2456.78
      },
      "tool_execution_summary": {
        "smart_extraction": {
          "success": true,
          "execution_time_ms": 2456.78,
          "error": null
        }
      },
      "tool_selection_method": "llm_based",
      "selection_confidence": 0.95,
      "intent_detected": "web_scraping",
      "multi_tool_used": false
    }
  }
}
```

---

**End of Analysis**
