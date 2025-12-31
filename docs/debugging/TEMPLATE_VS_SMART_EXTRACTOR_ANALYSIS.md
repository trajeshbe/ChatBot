# Template Extractor vs Smart Extractor Analysis

**Date**: 2025-11-17
**Issue**: Template Extractor failing with screener.in URL while Smart Extractor succeeds
**Reporter**: User validation request

---

## Summary of Findings

### 1. Smart Extractor - User Prompt Usage ✅ VERIFIED

**Concern**: User was unsure if the "What data do you want to extract?" prompt is being used in the Smart Extractor's LLM call.

**Finding**: ✅ **YES, the user prompt IS being used correctly**

**Evidence from Code**:

#### File: `backend/app/services/webscraper/templates/template_auto_generator.py`

**Lines 308-322** - User instructions are explicitly included in the LLM analysis prompt:

```python
# Build analysis prompt
instructions_section = ""
if user_instructions:
    instructions_section = f"\n\nUser's Extraction Requirements:\n{user_instructions}\n"

analysis_prompt = f"""Analyze this webpage content and suggest the best fields to extract:

Webpage Text Preview:
{text_preview}

HTML Structure Info:
- Tables: {page_content.get('structure', {}).get('tables', 0)}
- Lists: {page_content.get('structure', {}).get('lists', 0)}
- Common CSS classes: {', '.join(page_content.get('structure', {}).get('common_classes', [])[:10])}

{instructions_section}  # ← USER INSTRUCTIONS INSERTED HERE

Maximum fields to suggest: {max_fields}

Analyze the content and return the JSON object with suggested fields."""
```

**Lines 329-333** - The prompt with user instructions is sent to LLM:

```python
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": analysis_prompt}  # ← Contains user instructions
]
```

**Lines 348-353** - LLM service is called with the messages:

```python
llm_result = await self.llm_service.generate(
    prompt=analysis_prompt,
    messages=messages,
    max_tokens=2000,
    temperature=0.2
)
```

**Call Flow**:
1. User submits request to `/api/v1/extract/smart-extract` with `user_instructions`
2. Endpoint calls `auto_gen.generate_template_from_user_instructions(user_instructions=user_instructions)`
3. This calls `analyze_webpage_and_generate_template(user_instructions=user_instructions)`
4. Lines 309-322: User instructions are added to the analysis prompt
5. Lines 348-353: Complete prompt (including user instructions) is sent to LLM
6. LLM analyzes the page based on user's requirements

**Recommendation**: Add debug logging to make this more transparent to users.

---

### 2. Template Extractor - Why It Might Fail ⚠️ INVESTIGATION NEEDED

**Issue**: Template Extractor not extracting data from screener.in URL despite Smart Extractor succeeding.

**Root Cause Hypothesis**: The issue is NOT with the URL itself, but with the **CSS selectors** or **extraction logic** in the Template Extractor.

#### Current Template Definition

From `backend/app/services/template_extraction_service.py` lines 339-401:

```python
def get_screener_in_template() -> ExtractionTemplate:
    """Template for extracting company data from Screener.in"""
    return ExtractionTemplate(
        name="Screener.in Company Data",
        description="Extract financial metrics from Screener.in company pages",
        wait_for_selector="#company-ratios",  # ← Key wait condition
        fields=[
            ExtractionField(
                name="Company Name",
                selector="h1.h2",
                required=True
            ),
            ExtractionField(
                name="Market Cap",
                selector="#top-ratios > li:nth-child(1) > span.number",
                data_type="number"
            ),
            # ... more fields with specific CSS selectors
        ]
    )
```

#### Potential Issues

1. **Wait Selector Might Not Exist**
   - Line 344: `wait_for_selector="#company-ratios"`
   - If this element doesn't exist or takes too long to load, extraction fails before trying field selectors
   - The template waits up to 60 seconds (line 109 in service), which should be enough

2. **CSS Selectors Might Be Outdated**
   - Screener.in might have changed their HTML structure
   - Selectors like `#top-ratios > li:nth-child(1) > span.number` are very specific and fragile
   - If the page structure changed, ALL selectors would fail

3. **Silent Failures in Field Extraction**
   - Lines 174-182: When a field extraction fails, it logs a warning but continues
   - If `required=True`, field gets `None`
   - If `required=False`, field gets `default_value`
   - **This means extraction might "succeed" but return empty/null values**

4. **Data Type Conversion Issues**
   - Lines 235-236: Data type conversion is applied to extracted values
   - Lines 244-276: The `_convert_data_type` method might throw exceptions
   - If conversion fails, the value might be lost or become a string

#### Extraction Flow Analysis

```
Template Extractor Flow:
1. Navigate to URL (90s timeout) ✓
2. Wait for #company-ratios (60s timeout) ← POTENTIAL FAILURE POINT
3. Get page HTML and create BeautifulSoup
4. For each field:
   a. Try Playwright query_selector
   b. If fails, try BeautifulSoup select_one
   c. If fails, try XPath (if provided)
   d. Apply regex (if provided)
   e. Convert data type
   f. Return value or default_value
5. Return extracted data

Smart Extractor Flow:
1. Fetch page content (no specific wait conditions)
2. Analyze HTML structure with LLM
3. Generate field definitions based on actual page content
4. Use intelligent extraction strategies
5. Fallback to rule-based analysis if LLM unavailable
```

**Key Difference**: Smart Extractor analyzes the ACTUAL page content and adapts to it, while Template Extractor uses HARDCODED selectors that might be outdated.

---

## Diagnostic Recommendations

### For Template Extractor

1. **Add Detailed Logging**
   - Log each selector attempt and result
   - Log the HTML structure around failed selectors
   - Log wait conditions and timeouts

2. **Verify Selectors Against Current Page**
   - Inspect https://www.screener.in/company/BHARTIARTL/consolidated/ with browser DevTools
   - Check if `#company-ratios` exists
   - Check if `#top-ratios > li:nth-child(1) > span.number` exists
   - Verify the structure matches the template

3. **Add Fallback Selectors**
   - Instead of single CSS selector, provide array of alternatives
   - Example: `["#top-ratios > li:nth-child(1) > span.number", ".ratio:nth-child(1) .number", "li:contains('Market Cap') span.number"]`

4. **Improve Error Reporting**
   - Currently, failed field extraction just logs a warning
   - Should report which selectors failed and why
   - Should include screenshot or HTML snippet for debugging

### For Smart Extractor

1. **Add User Prompt Visibility**
   - Log when user instructions are included
   - Show in API response that instructions were used
   - Include in metadata: `"user_instructions_used": true`

2. **Add Confidence Metrics**
   - Show how well the generated template matches user instructions
   - Indicate if fallback rule-based analysis was used
   - Show which LLM provider was used

---

## Code Issues Found

### Issue 1: Error Handling Masks Failures

**Location**: `template_extraction_service.py` lines 174-182

```python
for field in fields:
    try:
        value = await self._extract_single_field(page, soup, field)
        extracted[field.name] = value
    except Exception as e:
        logger.warning(f"Error extracting field {field.name}: {e}")
        if field.required:
            extracted[field.name] = None  # ← Silent failure
        else:
            extracted[field.name] = field.default_value  # ← Hides error
```

**Problem**:
- Exceptions are caught and logged as warnings, not errors
- Extraction continues even if critical fields fail
- Response shows `success: true` even with null values

**Impact**:
- Users think extraction worked when it actually failed
- No indication that selectors are broken
- Difficult to debug why data is empty

**Recommendation**:
- Track failed fields separately
- Include `failed_fields` in response
- Set `success: false` if required fields fail
- Include detailed error messages per field

### Issue 2: No Selector Validation

**Location**: `template_extraction_service.py` lines 186-242

**Problem**:
- No validation that selectors work before extraction
- No fallback to alternative extraction methods
- Relies solely on CSS selectors without testing

**Recommendation**:
- Add selector validation step
- Provide multiple selector strategies per field
- Auto-fallback to alternative selectors

### Issue 3: Smart Extractor Success Not Documented

**Location**: `template_auto_generator.py` line 309-322

**Problem**:
- User instructions are used but not logged prominently
- No indication in logs that LLM received the instructions
- Users can't verify their prompt was used

**Recommendation**:
- Add INFO log: "Using user instructions in LLM analysis: {user_instructions}"
- Include in response metadata: `"user_instructions_received": user_instructions`
- Show in generated template description

---

## Recommended Fixes

### Fix 1: Add Logging to Show User Prompt Usage

**File**: `backend/app/services/webscraper/templates/template_auto_generator.py`

**Line 309**, add after `if user_instructions:`:

```python
if user_instructions:
    instructions_section = f"\n\nUser's Extraction Requirements:\n{user_instructions}\n"
    # ADD THIS:
    self.logger.info(f"✓ User instructions will be sent to LLM: {user_instructions[:100]}...")
else:
    # ADD THIS:
    self.logger.info("No user instructions provided - using automatic analysis")
```

### Fix 2: Improve Template Extractor Error Reporting

**File**: `backend/app/services/template_extraction_service.py`

**Lines 138-148**, modify the response:

```python
return {
    'success': True,
    'url': url,
    'template_name': template.name,
    'data': all_data,
    'row_count': len(all_data),
    'extracted_at': datetime.utcnow().isoformat(),
    'session_id': session_id,
    # ADD THESE:
    'failed_fields': failed_fields_list,  # Track which fields had issues
    'selector_warnings': selector_warnings,  # Show which selectors didn't match
    'extraction_quality': quality_score  # Percentage of fields successfully extracted
}
```

### Fix 3: Add Selector Diagnostics

**File**: `backend/app/services/template_extraction_service.py`

Add new method to validate selectors before extraction:

```python
async def validate_selectors(
    self,
    page: Page,
    template: ExtractionTemplate
) -> Dict[str, bool]:
    """
    Validate that template selectors work on the current page
    Returns dict of {field_name: selector_found}
    """
    validation_results = {}

    for field in template.fields:
        if field.selector:
            element = await page.query_selector(field.selector)
            validation_results[field.name] = element is not None

            if not element:
                logger.warning(
                    f"Selector validation failed for '{field.name}': "
                    f"selector '{field.selector}' not found on page"
                )

    return validation_results
```

Call this after page load but before extraction.

---

## Testing Plan

### Test 1: Verify User Prompt in Smart Extractor

```bash
curl -X POST http://localhost:8000/api/v1/extract/smart-extract \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.screener.in/company/BHARTIARTL/consolidated/",
    "user_instructions": "Extract financial metrics: market cap, P/E ratio, ROE, ROCE",
    "llm_provider": "ollama"
  }'
```

**Expected in logs**:
```
INFO - ✓ User instructions will be sent to LLM: Extract financial metrics: market cap, P/E ratio, ROE, ROCE
```

### Test 2: Compare Template vs Smart Extractor

**Template Extractor**:
```bash
curl -X POST http://localhost:8000/api/v1/extract/preset/screener_in \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.screener.in/company/BHARTIARTL/consolidated/"
  }'
```

**Smart Extractor**:
```bash
curl -X POST http://localhost:8000/api/v1/extract/smart-extract \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.screener.in/company/BHARTIARTL/consolidated/",
    "user_instructions": "Extract company name, market cap, current price, P/E ratio, book value, dividend yield, ROCE, ROE, face value"
  }'
```

**Compare**:
- Which one returns actual data?
- Which fields are populated?
- Are there errors in logs?

### Test 3: Inspect Actual Page Structure

Open browser to `https://www.screener.in/company/BHARTIARTL/consolidated/` and verify:

1. Does `#company-ratios` element exist?
2. Does `#top-ratios` element exist?
3. What is the actual structure of the ratio elements?
4. Do the CSS selectors in the template match current structure?

---

## Conclusion

### Smart Extractor User Prompt ✅

**Status**: Working correctly
**Evidence**: Code analysis shows user instructions are properly included in LLM prompt
**Action**: Add logging to make this more transparent

### Template Extractor Issues ⚠️

**Status**: Likely selector mismatch
**Evidence**: Hardcoded selectors might not match current page structure
**Root Cause**: Template selectors are fragile and page structure may have changed

**Why Smart Extractor Works**:
- Analyzes actual page content dynamically
- Adapts to current page structure
- Uses LLM to intelligently find data
- Has fallback to rule-based extraction

**Why Template Extractor Might Fail**:
- Uses hardcoded CSS selectors
- No dynamic adaptation
- Silent failures when selectors don't match
- No fallback strategies

**Recommendations**:
1. Inspect current screener.in page structure
2. Update template selectors to match current HTML
3. Add selector validation before extraction
4. Improve error reporting for failed field extraction
5. Add fallback selector strategies
6. Consider using Smart Extractor as default for dynamic sites

---

## Next Steps

1. ✅ Document that Smart Extractor DOES use user prompts
2. 🔨 Add logging to make user prompt usage visible
3. 🔍 Inspect current screener.in page with browser DevTools
4. 🔧 Update template selectors if page structure changed
5. 📊 Add selector validation and better error reporting
6. 🧪 Create comprehensive test suite comparing both extractors

---

**Document Status**: Analysis Complete
**Prepared By**: Claude AI Assistant
**Review Date**: 2025-11-17
