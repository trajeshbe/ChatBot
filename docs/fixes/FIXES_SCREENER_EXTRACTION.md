# Screener.in Data Extraction Fixes

**Date:** 2025-11-17
**Issues Fixed:** Template extraction timeout and smart extraction LLM errors

## Problems Identified

### Error 1: Playwright Timeout (10000ms exceeded)
- **Root Cause:** Playwright's default navigation timeout was 10 seconds, which is too short for slow-loading sites like screener.in
- **Symptoms:** `Timeout 10000ms exceeded` error when attempting template-based extraction
- **Affected Files:**
  - `backend/app/services/template_extraction_service.py`
  - `backend/app/services/webscraper/core/scraper_engine.py`

### Error 2: LLM Service Failure in Smart Extraction
- **Root Cause:** LLM service errors not properly handled, causing complete failure of auto-template generation
- **Symptoms:** `Failed to analyze content structure` error in smart extraction
- **Affected Files:**
  - `backend/app/services/webscraper/templates/template_auto_generator.py`

## Solutions Implemented

### 1. Extended Playwright Timeouts

#### File: `backend/app/services/template_extraction_service.py`

**Changes:**
- Set default navigation timeout to 60 seconds (up from 10 seconds)
- Set default timeout for all operations to 60 seconds
- Increased page.goto timeout to 90 seconds for slow sites
- Added timeout configuration to browser context

**Code Changes:**
```python
# Create context with increased default timeout (60 seconds instead of 10)
context = await self.browser.new_context(
    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
)
# Set default navigation timeout to 60 seconds
context.set_default_navigation_timeout(60000)
context.set_default_timeout(60000)

# Navigate to URL with extended timeout for slow sites like screener.in
await page.goto(url, wait_until='networkidle', timeout=90000)
```

#### File: `backend/app/services/webscraper/core/scraper_engine.py`

**Changes:**
- Applied same timeout increases to Playwright fallback scraper
- Set 90-second default timeouts for context
- Increased page.goto timeout to 90 seconds

**Code Changes:**
```python
# Set increased default timeouts for slow sites like screener.in
context.set_default_navigation_timeout(90000)  # 90 seconds
context.set_default_timeout(90000)

# Navigate to page with extended timeout
await page.goto(url, wait_until='networkidle', timeout=90000)
```

### 2. Robust Error Handling for LLM Service

#### File: `backend/app/services/webscraper/templates/template_auto_generator.py`

**Changes:**
1. **Enhanced Content Validation:**
   - Added validation to ensure content exists before analysis
   - Better handling of empty/missing content
   - Truncated content to fit LLM context window (5000 chars)

2. **Comprehensive Error Handling:**
   - Added try-catch for LLM service method errors
   - Added AttributeError handling for missing methods
   - Better logging with exc_info for debugging

3. **Fallback Analysis System:**
   - Created `_get_fallback_analysis()` method
   - Generates basic templates without LLM when service fails
   - Uses HTML structure analysis to suggest fields
   - Provides degraded but functional extraction

**Fallback Analysis Features:**
- Detects tables and suggests table data extraction
- Adds content and title fields by default
- Detects lists and adds list extraction
- Returns confidence score (0.5 for fallback vs 0.85 for LLM)

**Code Changes:**
```python
try:
    # Validate that we have content to analyze
    text_content = page_content.get('text', '')
    html_content = page_content.get('html', '')

    if not text_content and not html_content:
        self.logger.error("No content available to analyze")
        return None

    # LLM call with comprehensive error handling
    # ...
except AttributeError as attr_error:
    self.logger.error(f"LLM service method error: {str(attr_error)}")
    return self._get_fallback_analysis(page_content, user_instructions)
except Exception as llm_error:
    self.logger.error(f"LLM service call failed: {str(llm_error)}", exc_info=True)
    return self._get_fallback_analysis(page_content, user_instructions)
```

## Testing the Fixes

### Prerequisites
1. Ensure Docker services are running:
   ```bash
   docker compose up -d
   ```

2. Check service status:
   ```bash
   docker compose ps
   ```

### Test Case 1: Template-Based Extraction (Screener.in Preset)

**API Endpoint:** `POST /api/v1/extract/preset/screener_in`

**Request:**
```json
{
  "url": "https://www.screener.in/company/BHARTIARTL/consolidated/",
  "preset": "screener_in",
  "session_id": "test-session-123"
}
```

**Expected Result:**
- ✅ No timeout errors
- ✅ Successfully extracts company data
- ✅ Returns financial metrics (Market Cap, P/E, ROE, etc.)

**cURL Command:**
```bash
curl -X POST "http://localhost:8000/api/v1/extract/preset/screener_in" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.screener.in/company/BHARTIARTL/consolidated/",
    "preset": "screener_in"
  }'
```

### Test Case 2: Smart Extraction (Auto-Template Generation)

**API Endpoint:** `POST /api/v1/extract/smart-extract`

**Request:**
```json
{
  "url": "https://www.screener.in/company/BHARTIARTL/consolidated/",
  "user_instructions": "Extract company financial data including market cap, P/E ratio, book value, and profitability ratios",
  "llm_provider": "openai",
  "output_format": "excel"
}
```

**Expected Result:**
- ✅ No LLM service errors
- ✅ Falls back to basic template if LLM unavailable
- ✅ Successfully generates and applies extraction template
- ✅ Returns extracted data

**cURL Command:**
```bash
curl -X POST "http://localhost:8000/api/v1/extract/smart-extract" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.screener.in/company/BHARTIARTL/consolidated/",
    "user_instructions": "Extract company financial metrics",
    "llm_provider": "openai",
    "output_format": "excel"
  }'
```

### Test Case 3: Auto-Generate Template Only

**API Endpoint:** `POST /api/v1/extract/auto-generate`

**Request:**
```json
{
  "url": "https://www.screener.in/company/BHARTIARTL/consolidated/",
  "user_instructions": "Extract financial metrics for stock analysis",
  "llm_provider": "openai",
  "max_fields": 15
}
```

**Expected Result:**
- ✅ No content analysis errors
- ✅ Returns generated template with fields
- ✅ Uses fallback if LLM unavailable (confidence: 0.5)
- ✅ Provides extraction strategies for each field

## Verification Steps

### 1. Check Backend Logs
```bash
# Follow backend logs
docker compose logs -f rag-backend

# Look for these success indicators:
# ✅ "Page loaded: https://www.screener.in/..."
# ✅ "Successfully fetched ... bytes using Playwright"
# ✅ "Successfully parsed X fields from LLM" OR "Using fallback analysis"
# ✅ "Extracted X rows of data"
```

### 2. Verify No Timeout Errors
```bash
# Search for timeout errors (should be empty)
docker compose logs rag-backend 2>&1 | grep -i "timeout"
```

### 3. Check LLM Fallback
```bash
# Look for fallback usage (this is OK if LLM unavailable)
docker compose logs rag-backend 2>&1 | grep -i "fallback"
```

## Configuration Requirements

### Required Environment Variables

Add to `.env` file:

```bash
# OpenAI API Key (for LLM-based extraction)
OPENAI_API_KEY=sk-your-api-key-here

# Or use Ollama for local LLM (no API key needed)
# Make sure Ollama service is running: docker compose up -d ollama
```

### Service Dependencies

Ensure these services are running:
```bash
docker compose up -d postgres redis minio rag-backend
```

For LLM-based smart extraction:
```bash
# Option 1: Use OpenAI (requires API key)
# Set OPENAI_API_KEY in .env

# Option 2: Use local Ollama (no API key)
docker compose up -d ollama

# Pull a model in Ollama
docker compose exec ollama ollama pull mistral
```

## Performance Notes

### Timeout Values
- **Default Playwright timeout:** 10 seconds (too short for many sites)
- **New default timeout:** 60 seconds (context-level)
- **Navigation timeout:** 90 seconds (for page.goto)
- **Selector wait timeout:** 60 seconds (unchanged)

### Expected Load Times
- **Screener.in:** 15-30 seconds (depends on network)
- **Simple static sites:** 2-5 seconds
- **JavaScript-heavy sites:** 10-20 seconds

### Fallback Behavior
When LLM is unavailable, the system will:
1. Log warning about LLM failure
2. Automatically use fallback analysis
3. Generate basic template from HTML structure
4. Continue with extraction using fallback template
5. Return results with `"fallback": true` in metadata

## Troubleshooting

### Issue: Still getting timeout errors

**Solution:**
1. Check network connectivity to screener.in
2. Verify Playwright is properly installed:
   ```bash
   docker compose exec rag-backend playwright install chromium
   ```
3. Increase timeout further if needed (edit the files and set to 120000 = 2 minutes)

### Issue: LLM service not working

**Solution:**
1. Check OpenAI API key is set in `.env`
2. Verify Ollama is running: `docker compose ps ollama`
3. Check backend can reach LLM services:
   ```bash
   docker compose exec rag-backend curl http://ollama:11434/api/tags
   ```
4. Review logs for detailed error messages

### Issue: Empty extraction results

**Solution:**
1. Check if site changed structure (update selectors)
2. Verify page content is loading:
   ```bash
   curl "https://www.screener.in/company/BHARTIARTL/consolidated/" -A "Mozilla/5.0"
   ```
3. Try smart extraction instead of preset template
4. Check backend logs for extraction field errors

## Files Modified

1. **backend/app/services/template_extraction_service.py**
   - Lines 90-105: Added context timeout configuration

2. **backend/app/services/webscraper/core/scraper_engine.py**
   - Lines 238-246: Added Playwright timeout configuration

3. **backend/app/services/webscraper/templates/template_auto_generator.py**
   - Lines 249-377: Enhanced error handling in `_analyze_content_structure`
   - Lines 521-599: Added `_get_fallback_analysis` method

## Next Steps

1. **Monitor Production:** Watch for timeout patterns in production logs
2. **Optimize Timeouts:** May need site-specific timeout configurations
3. **Enhance Fallback:** Improve fallback template quality with better HTML analysis
4. **Add Caching:** Cache generated templates to avoid repeated LLM calls
5. **Site-Specific Templates:** Create more preset templates for common financial sites

## Support

If issues persist:
1. Check `docker compose logs rag-backend` for detailed errors
2. Verify all environment variables are set correctly
3. Ensure Playwright chromium is installed
4. Test with a simpler site first to isolate the issue
5. Review the extraction template selectors for accuracy

---

**Author:** Claude
**Version:** 1.0
**Last Updated:** 2025-11-17
