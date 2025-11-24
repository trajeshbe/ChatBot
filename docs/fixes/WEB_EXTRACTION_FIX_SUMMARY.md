# Web Extraction Fix - Smart Extract Endpoint

## Issue Diagnosed

When testing the Smart Extract endpoint with books.toscrape.com URLs, the extraction was returning empty data:
```json
{
  "success": true,
  "data": [{}],  // Empty object!
  "row_count": 1
}
```

## Root Cause

The Ultra-Smart extractor's `_extract_from_page()` method was prioritizing trafilatura for text extraction, which was failing on certain websites like books.toscrape.com:

```
ERROR | trafilatura.core - empty HTML tree for URL None
ERROR | trafilatura.utils - parsed tree length: 0, wrong data type or not valid HTML
```

When trafilatura failed, it would fall back to Playwright's `inner_text()`, but by that time the extraction quality was already compromised.

## Fix Applied

**File**: `backend/app/services/webscraper/extractors/ultra_smart_extractor.py`
**Lines**: 1200-1236

**Changes**:
1. **Reversed extraction priority**: Now uses Playwright's `inner_text("body")` as the PRIMARY extraction method
2. **Trafilatura as fallback**: Only uses trafilatura if Playwright text is too short (< 100 chars)
3. **Added logging**: Better visibility into text extraction process

**Before** (lines 1207-1217):
```python
# Get page content
content = await page.content()

# Extract clean text using trafilatura if available
try:
    import trafilatura
    text_content = trafilatura.extract(content) or ""
except:
    # Fallback: use page text
    text_content = await page.inner_text("body")
```

**After** (lines 1208-1224):
```python
# Primary: Use Playwright's built-in text extraction (most reliable)
text_content = await page.inner_text("body")

# If Playwright extraction is empty or very short, try trafilatura as fallback
if len(text_content.strip()) < 100:
    logger.info("🔄 Playwright text too short, trying trafilatura fallback...")
    try:
        import trafilatura
        content = await page.content()
        trafilatura_text = trafilatura.extract(content)
        if trafilatura_text and len(trafilatura_text) > len(text_content):
            text_content = trafilatura_text
            logger.info(f"✅ Using trafilatura text ({len(text_content)} chars)")
    except Exception as e:
        logger.debug(f"Trafilatura extraction failed: {e}")

logger.info(f"📝 Extracted {len(text_content)} characters of text for LLM")
```

## Benefits

1. **More Reliable**: Playwright's `inner_text()` works reliably across all websites
2. **Better Quality**: Playwright provides cleaner, properly formatted text
3. **Smart Fallback**: Still uses trafilatura when beneficial (very short text)
4. **Better Debugging**: Logging shows exactly which method was used and how much text was extracted

## Testing Required

To verify the fix works:
1. Restart the backend completely (not just container restart)
2. Test with Sharp Objects URL: `https://books.toscrape.com/catalogue/sharp-objects_997/index.html`
3. Should now extract actual book title and price instead of empty data
4. Check logs for "📝 Extracted X characters of text for LLM" message

## Related Work

- ✅ PDF URL detection added to Ultra-Smart extractor
- ✅ Automatic PDF download and Docling processing
- ✅ Text extraction priority fixed
- ⏳ Need to verify in UI

