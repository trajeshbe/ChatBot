# Issue Analysis and Fixes

## Summary of Issues

| # | Issue | Status | Root Cause |
|---|-------|--------|------------|
| 1 | Ollama LLM not working | ✅ Fixable | Missing jq dependency, script bug, possible Ollama config |
| 2 | Wikipedia 403 Forbidden | ✅ Fixable | Need enhanced scraper with Playwright |
| 3 | Excel template extraction | ⚠️ Partial | Routes exist but not registered in main.py |
| 4 | Retry options missing | ⚠️ Needs Implementation | UI exists, backend needs retry logic |
| 5 | Job monitor shows nothing | ✅ Fixable | Routes not registered in main.py |

---

## Issue 1: Ollama LLM Not Working

### Root Causes:
1. **Missing `jq` dependency** in validation script
2. **Bug in validate-services.sh line 87**: Incorrect variable expansion causing "integer expression expected"
3. **Ollama might not be properly configured** in settings

### Files Involved:
- `/home/user/ChatBot/scripts/maintenance/validate-services.sh` (lines 87-88, 102)
- `/home/user/ChatBot/backend/app/services/llm_service_enhanced.py` (has Ollama support)
- `/home/user/ChatBot/backend/app/core/config.py` (Ollama settings)

### Diagnosis:
```bash
# The error occurs here (line 87-88):
ollama_models=$(docker exec rag-ollama ollama list 2>/dev/null | grep -c "instruct" || echo "0")
if [ "$ollama_models" -ge 2 ]; then
    # Line 87 tries to compare, but if docker fails, it gets "0 0"
```

The problem is the command might return "0 0" instead of "0", causing the integer comparison to fail.

### Fixes:

#### Fix 1: Update validate-services.sh
```bash
# Line 87-88 - Fix integer comparison
ollama_models=$(docker exec rag-ollama ollama list 2>/dev/null | grep -c "instruct" 2>/dev/null || echo "0")
# Ensure it's a valid integer
ollama_models=${ollama_models##*[^0-9]*}  # Strip non-numeric characters
[ -z "$ollama_models" ] && ollama_models=0
if [ "$ollama_models" -ge 2 ]; then
```

#### Fix 2: Handle missing jq gracefully
```bash
# Line 102-103 - Handle missing jq
if command -v jq &> /dev/null; then
    echo "$models_response" | jq -r '.[] | "  • \(.name) (\(.provider))"'
    model_count=$(echo "$models_response" | jq '. | length')
else
    echo "  (install jq to see model list: apt-get install jq)"
    model_count=$(echo "$models_response" | grep -o '"name"' | wc -l)
fi
```

#### Fix 3: Check Ollama configuration
Need to verify in `.env` or `backend/app/core/config.py`:
```python
OLLAMA_ENDPOINT = "http://localhost:11434"  # or http://ollama:11434 in Docker
```

---

## Issue 2: Wikipedia 403 Forbidden

### Root Cause:
The basic `scraper_service.py` uses simple httpx with a basic User-Agent, which Wikipedia blocks.

### Current Situation:
- ✅ Enhanced scraper with Playwright EXISTS (`scraper_service_enhanced.py`, `scraper_engine.py`)
- ✅ Enhanced routes EXIST (`/api/v1/scraper/scrape/bulk`)
- ✅ Enhanced routes ARE REGISTERED in main.py (lines 593-597)
- ❌ Frontend might be calling wrong endpoint OR enhanced scraper not working

### Files Involved:
- `/home/user/ChatBot/backend/app/services/scraper_service_enhanced.py`
- `/home/user/ChatBot/backend/app/services/webscraper/core/scraper_engine.py`
- `/home/user/ChatBot/backend/app/api/routes/scraper_enhanced.py`

### Diagnosis:
The frontend `WebScraperEnhanced.tsx` is correctly calling `/api/v1/scraper/scrape/bulk`, but the enhanced scraper might be failing to use Playwright for Wikipedia.

### Fixes:

#### Fix 1: Ensure Playwright strategy is used for Wikipedia
The enhanced scraper should detect Wikipedia and use Playwright:

```python
# In scraper_engine.py or scraper_strategies.py
PLAYWRIGHT_REQUIRED_DOMAINS = [
    'wikipedia.org',
    'wikimedia.org',
    # Add other domains that need JS rendering
]

def should_use_playwright(url: str) -> bool:
    from urllib.parse import urlparse
    domain = urlparse(url).netloc
    return any(req_domain in domain for req_domain in PLAYWRIGHT_REQUIRED_DOMAINS)
```

#### Fix 2: Verify Playwright is installed
```bash
cd backend
pip show playwright  # Check if installed
playwright install chromium  # Install browser
```

#### Fix 3: Add retry with different strategies
The scraper should try multiple strategies when one fails:
1. Try trafilatura (fast)
2. If 403, try Playwright (bypasses bot detection)
3. If still fails, try with different User-Agent rotation

---

## Issue 3: Excel Template Extraction

### Root Cause:
Extraction routes exist but are **NOT registered** in main.py

### Current Situation:
- ✅ Frontend UI is complete (`WebScraperEnhanced.tsx` - Template tab)
- ✅ Backend routes exist (`extraction_routes.py`)
- ❌ Routes NOT registered in main.py
- ❌ Workflow implementation may be incomplete

### Files Involved:
- `/home/user/ChatBot/backend/app/api/routes/extraction_routes.py`
- `/home/user/ChatBot/backend/app/main.py` (needs router registration)
- `/home/user/ChatBot/backend/app/services/webscraper/workflows.py`

### Fixes:

#### Fix 1: Register extraction routes in main.py
Add after line 597 in `main.py`:

```python
# Extraction Workflow API
try:
    from app.api.routes import extraction_routes
    app.include_router(extraction_routes.router)
    logger.info("✓ Extraction Workflow API router registered (Phase 3 LangGraph)")
except ImportError as e:
    logger.warning(f"⚠ Extraction routes not available: {e}")
```

#### Fix 2: Implement template-based extraction
The current extraction workflow needs to:
1. Accept Excel template with column definitions
2. Use LLM to map scraped data to columns
3. Generate output in requested format (Excel, CSV, JSON, etc.)

This is a more complex feature that requires:
- Template schema parsing (read Excel columns)
- LLM-based field extraction
- Data validation and quality scoring

---

## Issue 4: Retry Options for Failed Extractions

### Root Cause:
UI elements exist but backend doesn't implement retry logic

### Current Situation:
- ✅ Frontend shows errors in JobMonitorTab
- ❌ No retry button or retry mechanism
- ❌ Backend doesn't store retry state

### Fixes:

#### Fix 1: Add retry endpoint to extraction_routes.py
```python
@router.post("/jobs/{job_id}/retry", response_model=ExtractionJobResponse)
async def retry_extraction_job(
    job_id: str,
    retry_config: Optional[Dict[str, Any]] = None
):
    """Retry a failed extraction job with optional config changes"""
    # Implementation needed
```

#### Fix 2: Add retry UI in JobMonitorTab
In `WebScraperEnhanced.tsx`, add retry button for failed jobs:
```typescript
{selectedJob.status === 'failed' && (
  <button
    onClick={() => handleRetry(selectedJob.job_id)}
    className="px-6 py-3 bg-yellow-600 text-white rounded-lg"
  >
    <RefreshCw className="w-5 h-5" />
    Retry with Different Settings
  </button>
)}
```

---

## Issue 5: Job Monitor Shows Nothing

### Root Cause:
Same as Issue #3 - extraction routes not registered

### Fixes:
Same fix as Issue #3 - register extraction routes in main.py

---

## Priority Fix Order

### Immediate Fixes (Can do right now):

1. **Fix validate-services.sh** (5 minutes)
   - Fix line 87-88 integer comparison
   - Add jq fallback

2. **Register extraction routes** (2 minutes)
   - Add router registration in main.py

3. **Check Ollama configuration** (5 minutes)
   - Verify OLLAMA_ENDPOINT in config
   - Test Ollama connectivity

### Medium Priority (Require testing):

4. **Fix Wikipedia scraping** (15 minutes)
   - Ensure Playwright strategy is used
   - Add domain-based strategy selection
   - Test with Wikipedia URL

5. **Add retry mechanism** (30 minutes)
   - Backend retry endpoint
   - Frontend retry UI
   - State management

### Long-term (Complex features):

6. **Excel template extraction** (2-4 hours)
   - Template parsing
   - LLM-based field mapping
   - Output generation
   - Quality validation

---

## Testing Checklist

After fixes:

- [ ] Run validate-services.sh - should detect Ollama models
- [ ] Test chat with Ollama model from frontend
- [ ] Test scraping https://en.wikipedia.org/wiki/Ooty - should succeed
- [ ] Create extraction job from Template tab - should appear in Job Monitor
- [ ] View job in Job Monitor - should show progress
- [ ] Download completed job results - should get Excel file

---

## Environment Verification Commands

```bash
# 1. Check if jq is installed
which jq || echo "jq not installed"

# 2. Check Ollama container
docker ps | grep ollama

# 3. Check Ollama models
docker exec rag-ollama ollama list

# 4. Check Ollama API
curl http://localhost:11434/api/tags

# 5. Check if Playwright is installed
docker exec rag-backend python -c "import playwright; print('✓ Playwright installed')"

# 6. Check backend logs for errors
docker compose logs backend | grep -i "error\|warning" | tail -20

# 7. Test extraction endpoint
curl http://localhost:8000/api/v1/extraction/jobs
```

---

## Next Steps

1. Apply immediate fixes
2. Test each fix individually
3. Verify with user
4. Implement medium priority fixes
5. Plan long-term features

Would you like me to start implementing these fixes?
