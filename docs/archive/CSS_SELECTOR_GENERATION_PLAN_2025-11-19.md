# CSS Selector Generation for Smart Extraction Templates

## Overview
Enable Smart Extraction to automatically generate CSS selectors when extracting data from web pages, so saved templates can be reused in CSS Selector mode for faster extraction.

## Problem
Currently, Smart Extraction saves templates with empty CSS selectors, making them unusable in CSS Selector mode.

## Solution Architecture

### 1. Backend Changes

#### A. Response Model Update
**File**: `/backend/app/api/routes/template_extraction_routes.py`
**Status**: ✅ COMPLETED

Added `suggested_selectors` field to `UltraSmartExtractResponse`:
```python
suggested_selectors: Optional[Dict[str, str]] = Field(
    default=None,
    description="AI-generated CSS selectors for each field (field_name -> CSS selector)"
)
```

#### B. CSS Selector Generation Method
**File**: `/backend/app/services/webscraper/extractors/ultra_smart_extractor.py`
**Status**: 🔄 IN PROGRESS

Add new method `_generate_css_selectors_for_fields()`:
```python
async def _generate_css_selectors_for_fields(
    self,
    html_content: str,
    extracted_table: List[Dict[str, Any]],
    model_id: str = "gpt-4-turbo"
) -> Dict[str, str]:
    """
    Generate CSS selectors for each field in the extracted table
    
    Uses LLM to analyze HTML and suggest reliable CSS selectors for each field.
    
    Args:
        html_content: Raw HTML from the page
        extracted_table: Extracted data table
        model_id: LLM model to use
        
    Returns:
        Dict mapping field names to CSS selectors
        Example: {"title": "h3 a", "price": ".price_color"}
    """
```

**Implementation Strategy**:
1. Get first row of extracted data as example
2. Simplify HTML (remove scripts/styles, keep only structure)
3. Use LLM to match each field value to HTML elements
4. Generate reliable CSS selectors for each match
5. Return selector map

#### C. Integration into extract_to_table()
**File**: `/backend/app/services/webscraper/extractors/ultra_smart_extractor.py`
**Line**: After line 937 (before return statement)

Add CSS selector generation only for URL sources:
```python
# Step 3.5: Generate CSS selectors (only for URL sources)
suggested_selectors = None
if (source_type == "url" or raw_result.get("source_type_detected") == "url") and table:
    # Extract HTML from raw_result metadata
    html_content = raw_result.get("metadata", {}).get("html_content")
    
    if html_content:
        logger.info("🔍 Generating CSS selectors for template creation...")
        try:
            suggested_selectors = await self._generate_css_selectors_for_fields(
                html_content=html_content,
                extracted_table=table,
                model_id="gpt-4-turbo"
            )
            logger.info(f"✅ Generated {len(suggested_selectors)} CSS selectors")
        except Exception as e:
            logger.warning(f"⚠️  Failed to generate CSS selectors: {e}")

# Then add to return value:
return {
    "success": True,
    "table": table,
    "columns": columns,
    "row_count": len(table),
    "extraction_metadata": {...},
    "suggested_selectors": suggested_selectors  # NEW
}
```

### 2. Frontend Changes

#### Update SmartExtractor.tsx
**File**: `/frontend/src/components/SmartExtractor.tsx`
**Line**: 290 (template field creation)

Change from hardcoded empty selectors to using suggested selectors from backend:

**Before**:
```typescript
const templateFields = Object.keys(extractedData.table[0]).map(key => ({
  name: key,
  selector: '',  // ❌ Empty selector
  data_type: 'text',
  required: false
}))
```

**After**:
```typescript
const templateFields = Object.keys(extractedData.table[0]).map(key => ({
  name: key,
  selector: extractedData.suggested_selectors?.[key] || '',  // ✅ Use AI-generated selector
  data_type: 'text',
  required: false
}))
```

## Workflow

### Before (Current):
1. User: "Extract books from https://books.toscrape.com/"
2. Smart Extraction extracts data using AI
3. User saves template
4. Template saved with EMPTY CSS selectors
5. ❌ Template can't be used in CSS Selector mode

### After (New):
1. User: "Extract books from https://books.toscrape.com/"
2. Smart Extraction extracts data using AI
3. Backend generates CSS selectors: {"title": "h3 a", "price": ".price_color"}
4. User saves template
5. Template saved with VALID CSS selectors
6. ✅ Template can be reused in CSS Selector mode for fast extraction

## Benefits

1. **Faster Re-extraction**: Templates with CSS selectors are ~10x faster than AI extraction
2. **Cost Savings**: No LLM API calls needed when using CSS Selector mode
3. **Reliability**: CSS selectors provide deterministic extraction
4. **Learning Workflow**: Smart Extract learns → CSS Selector reuses
5. **Best of Both Worlds**: AI intelligence for discovery + CSS speed for reuse

## Implementation Status

- [x] Add `suggested_selectors` field to response model
- [x] Update ultra-smart endpoint to include selectors
- [ ] Implement `_generate_css_selectors_for_fields()` method
- [ ] Integrate into `extract_to_table()` workflow
- [ ] Update frontend to use suggested selectors
- [ ] Test end-to-end with books.toscrape.com example
- [ ] Document feature in user guides

## Next Steps

1. Implement CSS selector generation method with LLM
2. Ensure HTML content is preserved in extraction metadata
3. Test with multiple websites
4. Handle edge cases (dynamic content, shadow DOM, etc.)

