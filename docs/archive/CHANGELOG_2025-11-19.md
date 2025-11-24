# Changelog - 2025-11-19

## Extraction System: Dynamic Model Selection & Brotli Compression Fix

### Summary
Fixed two critical issues preventing web extraction from working correctly:
1. Implemented dynamic model selection (like chat) using EnhancedLLMService
2. Fixed brotli compression bug in HTTP client

**Status**: ✅ ULTRA-SMART ENDPOINT COMPLETED AND TESTED | ⚠️ SMART-EXTRACT ENDPOINT IN PROGRESS

---

## Files Modified

### Backend API Routes
1. **`/backend/app/api/routes/template_extraction_routes.py`**
   - **Line 576**: Added `model_id` field to `SmartExtractRequest` schema
   - Lines 108, 128-130: Switched to EnhancedLLMService (ultra-smart endpoint)
   - Lines 136-137: Use request parameters instead of hardcoded values
   - Line 1557: Added `model_id` field to `UltraSmartExtractRequest` schema
   - Lines 775, 783-784, 798-800: Updated ultra-smart endpoint

### Extraction Services
2. **`/backend/app/services/webscraper/extractors/llm_extractor.py`**
   - Lines 435-436: Added `model_id` parameter to `map_to_custom_template()`
   - Line 456: Updated docstring with model_id description
   - Line 584: Pass `model_id` to `generate()` call

3. **`/backend/app/services/webscraper/extractors/ultra_smart_extractor.py`**
   - Lines 112-114: Extract `model_id` from kwargs
   - Lines 155-159: Updated `_extract_from_url()` signature
   - Lines 239-247: Updated `_extract_from_document()` signature
   - Lines 410-423: Updated `_extract_from_text()` signature
   - Lines 436-442: Updated `_llm_extract_fields()` signature
   - Lines 699-730: Updated `_extract_with_intelligent_fallback()` signature
   - All routing calls updated to pass `model_id` parameter

4. **`/backend/app/services/scraper_service.py`**
   - Line 26: Removed `br` from Accept-Encoding header
   - Changed from: `'Accept-Encoding': 'gzip, deflate, br'`
   - Changed to: `'Accept-Encoding': 'gzip, deflate'`

---

## Test Results

### ✅ Ultra-Smart Endpoint (/api/v1/extract/ultra-smart)

**Test 1 - HTTP Method (books.toscrape.com)**:
```json
{
  "Book Title": "Sharp Objects",
  "Price (excl. tax)": "£47.82",
  "Price (incl. tax)": "£47.82"
}
```

**Test 2 - Playwright Method (cloudflare.com)**:
```json
{
  "MainHeading": "Connect, protect, and build everywhere | Cloudflare",
  "KeyFeatures": [...],
  "Benefits": [...]
}
```

**Test 3 - User's URL (a-light-in-the-attic)**:
```json
{
  "Book Title": "A Light in the Attic",
  "Price": "£51.77"
}
```

### ⚠️ Smart-Extract Endpoint (/api/v1/extract/smart-extract) - UI Endpoint

**Status**: `model_id` error fixed, but extraction returns empty data

**Before Fix**:
```
ERROR: 'SmartExtractRequest' object has no attribute 'model_id'
```

**After Fix**:
```json
{
  "success": true,
  "data": {},  ← Empty data
  "row_count": 1
}
```

---

## Investigation: Smart-Extract vs Ultra-Smart

### Discovery

Both endpoints use **identical extraction logic**:

```python
# Line 775-801 in template_extraction_routes.py
# BOTH smart-extract AND ultra-smart use this EXACT code:
ultra_extractor = UltraSmartExtractor(llm_service, scraper_service, None)
result = await ultra_extractor.extract_from_any_source(
    source_type="url",
    source=request.url,
    user_instructions=request.user_instructions,
    llm_provider=request.llm_provider,
    model_id=request.model_id
)
```

### Why Smart-Extract Returns Empty Data

**Lines 812-815** show the issue:
```python
extracted_table = result.get("table", [])
if not extracted_table:
    logger.warning("⚠️ No data extracted")
    extracted_table = [{}]  # ← Returns empty dict when extraction fails
```

**Backend logs confirm**: "⚠️ No data extracted"

### Possible Causes

1. **Frontend not sending required parameters** - UI may not send `user_instructions` correctly
2. **Different request format** - Smart-extract may expect different parameter structure
3. **Extraction actually failing** - UltraSmartExtractor returns empty table `[]`

### Next Steps

1. ✅ **Fixed**: Added `model_id` field to `SmartExtractRequest` schema
2. ⏳ **In Progress**: Investigate why extraction returns empty data
3. ⏳ **TODO**: Check frontend SmartExtractor.tsx to see what parameters it sends
4. ⏳ **TODO**: Compare backend logs for successful ultra-smart vs failed smart-extract

---

## Technical Details

### Issue 1: Hardcoded Models → Dynamic Selection ✅

- **Root Cause**: `model_id` parameter not passed through entire extraction chain
- **Fix**: Updated all methods to accept and pass `model_id` parameter
- **Result**: Extraction uses requested model (gpt-4-turbo, claude-3-opus, etc.)

### Issue 2: Brotli Compression Not Decompressed ✅

- **Root Cause**: httpx only auto-decompresses gzip/deflate, NOT brotli
- **Fix**: Removed `br` from Accept-Encoding header
- **Result**: Server sends gzip → httpx decompresses → clean HTML

### Issue 3: Smart-Extract Returns Empty Data ⏳

- **Root Cause**: Under investigation
- **Status**: model_id error fixed, but extraction still fails
- **Next**: Check frontend request parameters and compare logs

---

## Validation

- [x] Dynamic model selection working (ultra-smart)
- [x] HTTP method tested and working (ultra-smart)
- [x] Playwright method tested and working (ultra-smart)
- [x] No more "---" empty responses (ultra-smart)
- [x] Added `model_id` to SmartExtractRequest schema
- [x] Smart-extract endpoint no longer crashes with model_id error
- [ ] Smart-extract extraction returning actual data (IN PROGRESS)

---

**Date**: 2025-11-19
**Status**: Ultra-Smart Endpoint ✅ | Smart-Extract Endpoint ⏳
**Tested By**: Claude Code
