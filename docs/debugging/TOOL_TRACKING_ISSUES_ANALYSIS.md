# 🔍 Tool Tracking Issues - Root Cause Analysis

## Issue: Only "smart_extraction" Tool Showing Up

### What The User Reported:
- User tested navigation query: "Navigate and get me all books from https://books.toscrape.com/..."
- Expected to see: `navigation_agent`, `playwright`, `web_scraper`, `smart_extraction`
- Actually saw: Only `smart_extraction`

---

## Root Cause #1: Tool Selection Logic

**File**: `backend/app/agents/enhanced_rag_agent.py`
**Method**: `_select_tool_simple()` (lines 220-280)

### The Problem:
- OpenAI quota exceeded (429 error) → LLM-based tool selection FAILED
- System fell back to simple keyword-based selection
- Simple selection logic:
  ```python
  # Check for web scraping keywords (line 242)
  if any(word in query_lower for word in ["scrape", "extract from", "get data from", ...]):
      # Check if URL exists (line 247)
      if "http" in query or ".com" in query:
          return "smart_extraction", {params}  # ← RETURNS HERE!
  ```

### Why "Navigate" Wasn't Detected:
- Query: "Navigate and get me all books from https://..."
- Simple selection checks for URL first (line 247)
- Finds "https://books.toscrape.com" → immediately returns "smart_extraction"
- NEVER checks if query contains "navigate" keyword
- "navigation_agent" tool requires "navigate" keyword detection (but it's not implemented)

### The Fix Needed:
Add "navigate" keyword detection BEFORE the URL check:
```python
# Check for navigation keywords FIRST
if any(word in query_lower for word in ["navigate", "pagination", "next page", "all pages"]):
    # Extract URL
    url_match = re.search(r'https?://[^\s]+', query)
    if url_match:
        return "navigation_agent", {
            "start_url": url_match.group(0),
            "navigation_instructions": query,
            "max_pages": 10
        }
```

---

## Root Cause #2: Tool Tracking Not Implemented

**File**: `backend/app/api/routes/template_extraction_routes.py`
**Endpoint**: `/api/v1/extract/ultra-smart` (line 1937)

### The Problem:
- Tool registry wrappers (`_wrap_smart_extraction`, `_wrap_navigation_agent`) call the ultra-smart API
- But the ultra-smart endpoint DOES NOT track tool usage
- The ultra_extractor.extract_to_table() calls:
  - Playwright (web scraping)
  - Navigation agent (pagination logic)
  - LLM extraction
  - But NONE of these are recorded in tool_usage_stats database

### Currently Tracked Tools:
✅ Document RAG (rag_service_enhanced.py) - returns tools_used array
✅ Document Processing (document_service.py) - tracks Docling, pypdf2, python_docx, etc.
✅ Embedding (embedding_service.py) - tracks all-MiniLM-L6-v2
✅ LLM Service (llm_service.py) - tracks OpenAI, Anthropic, Ollama models

### NOT Tracked (Missing):
❌ Smart Extraction (ultra-smart endpoint)
❌ Navigation Agent (ultra-smart endpoint)
❌ Playwright (used by scraper_service)
❌ Web Scraper (scraper_service)
❌ OCR (if used)
❌ Template Extraction

### The Fix Needed:
Add tool tracking to the ultra-smart endpoint:
```python
import time
from app.services.tool_usage_tracker import tool_tracker, ToolCategory
from app.core.config import settings

# In ultra_smart_extract() endpoint (line 2009):
start_time = time.time()

# ... existing extraction logic ...
result = await ultra_extractor.extract_to_table(...)

processing_time = (time.time() - start_time) * 1000

# Track the extraction
if settings.TOOL_TRACKING_ENABLED:
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
            'row_count': result.get('row_count', 0)
        }
    )
```

---

## Summary of Fixes Needed:

### Priority 1: Tool Selection
**File**: `backend/app/agents/enhanced_rag_agent.py`
- Update `_select_tool_simple()` to detect "navigate" keyword BEFORE URL check
- Ensure navigation_agent tool is selected for navigation queries

### Priority 2: Tool Tracking
**Files**:
1. `backend/app/api/routes/template_extraction_routes.py`
   - Add tracking to `/ultra-smart` endpoint (line 2009)
   - Add tracking to `/ultra-smart-navigation` endpoint (line 2172)

2. `backend/app/services/scraper_service.py`
   - Add tracking to `scrape_url()` method

3. `backend/app/services/webscraper/agents/navigation_agent.py`
   - Add tracking to navigation actions

### Priority 3: Fix "Sources: N/A" Display
**File**: TBD - need to investigate where "N/A" is shown inappropriately

---

## Expected Result After Fixes:

When user asks: "Navigate and get me all books from https://books.toscrape.com/..."

**Tool Selection**: `navigation_agent` (instead of just smart_extraction)

**Tools Tracked**:
1. `navigation_agent` (10-30s) - Navigate through pages
2. `playwright` (5-10s per page) - Browser automation
3. `smart_extraction` (2-5s per page) - AI extraction
4. `ollama/llama3.2:3b` (1-3s) - LLM for data structuring

**Tools Shown in UI**:
```
🔧 4 tools

Expanded:
1. navigation_agent (23.5s) - Paginate through 5 pages
2. playwright (45.2s) - Browser automation (5 pages)
3. smart_extraction (12.3s) - Extract book data
4. ollama/llama3.2:3b (8.1s) - Structure tabular output
```

---

## Implementation Order:
1. ✅ Fix tool selection logic (navigation keyword detection)
2. ✅ Add tracking to ultra-smart endpoint
3. ✅ Add tracking to scraper_service
4. ✅ Add tracking to navigation_agent
5. ⏳ Fix "Sources: N/A" display issue (separate investigation)
6. ✅ Restart backend
7. ✅ Test with navigation query

