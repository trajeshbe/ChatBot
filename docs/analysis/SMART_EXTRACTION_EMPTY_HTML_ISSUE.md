# Smart Extraction - Empty HTML Issue

## Problem Summary

Smart Extraction is completing but returning 0 extracted values. Root cause: HTML content is coming through as None/empty.

## Evidence from Logs

```
07:11:24.252 | ERROR   | trafilatura.core - empty HTML tree for URL None
07:11:26.659 | WARNING | app.services.webscraper.extractors.llm_extractor - ⚠ LLM extraction returned 0 non-empty values out of 2 fields
```

URLs tested:
- `https://books.toscrape.com` - 0 values extracted
- `https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html` - 0 values extracted

## Root Cause Analysis

### Missing Logs
- No "Using scraper service to fetch" logs
- No "Fetching URL" logs from scraper_service
- No "Smart extraction from:" logs from endpoint

This suggests:
1. Either `self.scraper_service` is None in TemplateAutoGenerator
2. OR scraper_service.scrape_url() is failing silently and returning None
3. OR the httpx fallback path is being used but failing

### Code Flow

**Smart Extract Endpoint** (`template_extraction_routes.py:703`)
```python
@router.post("/smart-extract")
async def smart_extract_without_template(request: SmartExtractRequest):
    auto_gen = TemplateAutoGenerator(
        llm_service=llm_service,
        scraper_service=scraper_service  # ← Is this None?
    )

    template = await auto_gen.generate_template_from_user_instructions(
        url=request.url,
        user_instructions=request.user_instructions,
        llm_provider=request.llm_provider  # ← Gets passed correctly
    )
```

**Template Auto Generator** (`template_auto_generator.py:189`)
```python
async def generate_template_from_user_instructions(
    self,
    url: str,
    user_instructions: str,
    llm_provider: str = "ollama",  # ← DEFAULT STILL OLLAMA!
    include_smart_mapping: bool = True
):
    return await self.analyze_webpage_and_generate_template(
        url=url,
        user_instructions=user_instructions,
        llm_provider=llm_provider
    )
```

**Webpage Fetch** (`template_auto_generator.py:219`)
```python
async def _fetch_webpage_content(self, url: str):
    try:
        if self.scraper_service:
            self.logger.info(f"Using scraper service to fetch: {url}")  # ← NOT APPEARING IN LOGS
            result = await self.scraper_service.scrape_url(url)  # ← db=None, should return dict

            if not result:
                # Fallback to Playwright
                result = await self._fetch_with_playwright(url)
        else:
            # Fallback to httpx  # ← LIKELY THIS PATH
            self.logger.info(f"Using fallback httpx client to fetch: {url}")
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url, follow_redirects=True)
                ...
```

## Issues Identified

### Issue 1: LLM Provider Default Still Ollama
**File:** `backend/app/services/webscraper/templates/template_auto_generator.py:193`
**Current:** `llm_provider: str = "ollama"`
**Should be:** `llm_provider: str = "openai"`

### Issue 2: scraper_service May Be None
The logs show NO "Using scraper service" message, suggesting `self.scraper_service` is None and code is taking the httpx fallback path.

**Possible causes:**
- scraper_service import failing
- scraper_service not initialized properly
- Circular import issue

### Issue 3: httpx Fallback May Be Failing
If httpx fallback is being used, it may be:
- Failing silently without proper error logging
- Returning empty content
- Not handling bot protection (403/Cloudflare)

## Immediate Fixes Needed

1. ✅ **Change LLM default from Ollama to OpenAI** (line 193)
2. ⚠️ **Add debug logging** to understand which code path is executing
3. ⚠️ **Test scraper_service directly** to verify it works
4. ⚠️ **Enhance error handling** in _fetch_webpage_content

## Testing Plan

1. Add extensive debug logging
2. Test Wikipedia (known working site)
3. Test books.toscrape.com
4. Check if CSS Selector mode works (for comparison)
5. Verify OpenAI is being used vs Ollama

## Status

- **Backend:** Healthy and running
- **Default LLM:** Changed from Ollama → OpenAI in one location (line 97)
- **Still needs fix:** Line 193 default
- **Needs investigation:** Why scraper_service appears to be None
