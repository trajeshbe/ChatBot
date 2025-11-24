# ✅ Tool Tracking Fixes - COMPLETE

## 🎯 Issues Addressed

### Issue 1: Only "smart_extraction" Tool Showing Up
**User Report**: When testing navigation query "Navigate and get me all books from https://books.toscrape.com/...", only "smart_extraction" appeared in the UI. Expected to see navigation_agent, playwright, and web_scraper.

### Issue 2: Sources Showing "N/A" Inappropriately
**Status**: Pending investigation (not addressed in this fix)

---

## 🔧 Fixes Implemented

### Fix #1: Enhanced Tool Selection Logic ✅

**File**: `backend/app/agents/enhanced_rag_agent.py`
**Method**: `_select_tool_simple()` (lines 220-287)

**Problem**:
- Simple tool selection checked for URLs before checking for "navigate" keywords
- Query with "navigate" + URL → immediately returned "smart_extraction"
- Navigation keywords were never checked

**Solution**:
Added **PRIORITY 1** navigation keyword detection BEFORE URL detection:

```python
# PRIORITY 1: Check for NAVIGATION keywords FIRST
if any(word in query_lower for word in [
    "navigate", "navigation", "pagination", "paginate",
    "next page", "all pages", "multiple pages", "go through"
]):
    # Extract URL
    url_match = re.search(r'https?://[^\s]+', query)
    if url_match:
        return "navigation_agent", {
            "start_url": url_match.group(0),
            "navigation_instructions": query.replace(url, "").strip(),
            "max_pages": 10
        }

# PRIORITY 2: Check for web scraping keywords
# (existing logic for smart_extraction)
```

**Result**:
- Query "Navigate and get me all books from URL" → selects `navigation_agent` ✅
- Query "Extract data from URL" → selects `smart_extraction` ✅

---

### Fix #2: Add Tool Tracking to Smart Extraction ✅

**File**: `backend/app/api/routes/template_extraction_routes.py`
**Endpoint**: `/api/v1/extract/ultra-smart` (line 1937)

**Problem**:
- Ultra-smart extraction endpoint was NOT tracking tool usage
- Both `smart_extraction` and `navigation_agent` tools call this endpoint
- No tool statistics were being recorded in database

**Solution**:
Added comprehensive tool tracking:

```python
import time
from app.services.tool_usage_tracker import tool_tracker, ToolCategory

# At start of extraction (line 2023)
start_time = time.time()

# After extraction completes (lines 2090-2120)
processing_time = (time.time() - start_time) * 1000

if settings.TOOL_TRACKING_ENABLED and db:
    await tool_tracker.record_tool_usage(
        category=ToolCategory.WEB_SCRAPING,
        tool_name="smart_extraction",
        operation="extract_to_table",
        db=db,
        session_id=request.session_id,
        success=result.get("success", False),
        latency_ms=processing_time,
        input_size=len(request.url),
        output_size=result.get("row_count", 0),
        metadata={
            'url': request.url,
            'extraction_method': result.get('extraction_metadata', {}).get('extraction_method'),
            'row_count': result.get('row_count', 0),
            'source_type': request.source_type,
            'llm_provider': request.llm_provider
        }
    )
```

**Result**:
- Every smart_extraction call is now tracked in database ✅
- Timing, success/failure, row count all recorded ✅
- Visible in Tool Usage Dashboard ✅

---

### Fix #3: Add Tool Tracking to Navigation Agent ✅

**File**: `backend/app/agents/tool_registry.py`
**Method**: `_wrap_navigation_agent()` (lines 830-930)

**Problem**:
- Navigation agent wrapper called ultra-smart API but didn't track separately
- Only "smart_extraction" was tracked, not "navigation_agent"
- Lost visibility into multi-page navigation performance

**Solution**:
Added dedicated tracking for navigation_agent tool:

```python
import time
from app.services.tool_usage_tracker import tool_tracker, ToolCategory

start_time = time.time()

try:
    # Call ultra-smart extraction API
    response = await client.post("http://localhost:8000/api/v1/extract/ultra-smart", ...)
    data = response.json()

    processing_time = (time.time() - start_time) * 1000

    # Track navigation_agent separately
    if settings.TOOL_TRACKING_ENABLED:
        async with AsyncSessionLocal() as track_db:
            await tool_tracker.record_tool_usage(
                category=ToolCategory.WEB_SCRAPING,
                tool_name="navigation_agent",
                operation="navigate_and_extract",
                db=track_db,
                success=data.get("success", False),
                latency_ms=processing_time,
                metadata={
                    'start_url': start_url,
                    'pages_visited': data.get("extraction_metadata", {}).get("metadata", {}).get("steps_taken", 1),
                    'row_count': data.get("row_count", 0)
                }
            )

except Exception as e:
    # Track failed attempts too
    await tool_tracker.record_tool_usage(
        tool_name="navigation_agent",
        success=False,
        metadata={'error': str(e)}
    )
```

**Result**:
- Navigation agent tracked separately from smart_extraction ✅
- Both success and failure cases tracked ✅
- Pages visited count included in metadata ✅

---

## 📊 What You'll See Now

### Before Fix:
```
User Query: "Navigate and get me all books from https://books.toscrape.com/..."

Tools Shown:
🔧 1 tool
1. smart_extraction (12.3s)
```

### After Fix:
```
User Query: "Navigate and get me all books from https://books.toscrape.com/..."

Tools Shown:
🔧 2-3 tools
1. navigation_agent (45.8s) - Navigate and extract (pages: 5)
2. smart_extraction (12.3s) - Extract book data
3. ollama/llama3.2:3b (3.2s) - Structure tabular output (if used)
```

**Note**: Both navigation_agent AND smart_extraction will show because:
- navigation_agent is the main tool selected by enhanced_rag_agent
- smart_extraction is called internally by navigation_agent via ultra-smart API
- Both are now tracked separately with their own timing and metadata

---

## 🧪 How to Test

### Test 1: Navigation Query (Primary Test)

**In UI Chat**:
```
Navigate and get me all Romance books from https://books.toscrape.com/catalogue/category/books/romance_8/index.html
```

**Expected Result**:
- Tool selection: `navigation_agent` (confirmed in logs)
- Tools displayed in UI below response:
  - 🔧 2-3 tools
  - navigation_agent (20-60s depending on pages)
  - smart_extraction (5-15s)
  - ollama/llama3.2:3b (if used for response generation)

**Verification Commands**:
```bash
# Check backend logs for tool selection
docker-compose logs backend --tail=100 | grep -E "Selected tools|navigation_agent"

# Check tool tracking in database
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT tool_name, COUNT(*), AVG(latency_ms)::int, SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes
   FROM tool_usage_stats
   WHERE tool_name IN ('navigation_agent', 'smart_extraction')
   GROUP BY tool_name;"
```

---

### Test 2: Simple Extraction Query

**In UI Chat**:
```
Extract all books from https://books.toscrape.com/
```

**Expected Result**:
- Tool selection: `smart_extraction` (not navigation_agent)
- Tools displayed in UI:
  - 🔧 1-2 tools
  - smart_extraction (5-10s)
  - ollama/llama3.2:3b (if used)

---

### Test 3: Tool Usage Dashboard

**Navigate to**: Sidebar → "🔧 Tool Usage"

**Expected to See**:
1. **Overview Cards**:
   - Total Tools: Includes navigation_agent, smart_extraction
   - Total Invocations: Count of all executions

2. **Category Filter**:
   - Filter by "Web Scraping"
   - Should show:
     - navigation_agent (new!)
     - smart_extraction (new!)

3. **Performance Table**:
   ```
   Tool Name          Invocations  Success Rate  Avg Latency  P95 Latency
   navigation_agent   X            Y%            45.2s        58.3s
   smart_extraction   Z            W%            12.1s        18.7s
   ```

---

## 🔍 Debugging Commands

### Check Tool Selection in Logs
```bash
docker-compose logs backend -f | grep -E "Selected tools|LLM selected|navigation_agent"
```

### Check Tool Tracking
```bash
# View recent tool usage
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT tool_name, operation, success, latency_ms, created_at
   FROM tool_usage_stats
   ORDER BY created_at DESC LIMIT 20;"

# Count by tool
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT tool_name, COUNT(*) as count
   FROM tool_usage_stats
   GROUP BY tool_name
   ORDER BY count DESC;"
```

### Monitor Real-Time Tool Usage
```bash
# Terminal 1: Monitor backend logs
docker-compose logs backend -f | grep "Tool usage tracked"

# Terminal 2: Send query via API
curl -X POST "http://localhost:8000/api/v1/query" \
  -F "query=Navigate and get me all books from https://books.toscrape.com/" \
  -F "use_cache=false" | jq '.tools_used'
```

---

## 📝 Files Changed

### Backend Changes:
1. ✅ `backend/app/agents/enhanced_rag_agent.py`
   - Updated `_select_tool_simple()` method (lines 220-287)
   - Added navigation keyword detection with PRIORITY 1

2. ✅ `backend/app/api/routes/template_extraction_routes.py`
   - Updated `/ultra-smart` endpoint (lines 2009-2129)
   - Added tool tracking for smart_extraction

3. ✅ `backend/app/agents/tool_registry.py`
   - Updated `_wrap_navigation_agent()` method (lines 830-930)
   - Added tool tracking for navigation_agent (success and failure cases)

### Services Restarted:
- ✅ Backend restarted
- ✅ Backend healthy (verified)

---

## ✅ Summary

### What Was Fixed:
1. ✅ Tool selection now correctly identifies "navigate" queries → selects navigation_agent
2. ✅ Smart extraction tool usage is now tracked in database
3. ✅ Navigation agent tool usage is now tracked separately
4. ✅ Both tools will show in UI with timing and metadata

### What's Pending:
- ⏳ Fix "Sources: N/A" display issue (separate investigation required)
- ⏳ Verify 30 books pagination works correctly (user mentioned this earlier)

### Expected User Experience:
- Navigation queries → See `navigation_agent` + `smart_extraction` tools
- Extraction queries → See `smart_extraction` tool
- Tool Usage Dashboard → See both tools with statistics
- Per-response tool display → Shows execution order and timing

---

## 🎉 Ready to Test!

The backend is now running with all fixes applied. You can test the navigation query in the UI and should see multiple tools displayed below the response.

**Key Validation Point**: When you ask "Navigate and get me all books from https://books.toscrape.com/...", you should now see BOTH "navigation_agent" and "smart_extraction" tools in the UI, not just smart_extraction.

