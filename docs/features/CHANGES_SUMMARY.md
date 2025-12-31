# Changes Summary: Template vs Smart Extractor Improvements

**Date**: 2025-11-17
**Branch**: `claude/enterprise-rag-chatbot-stack-011CV55YJHaUYhTQVqsEU4iK`
**Issue**: User validation of Smart Extractor prompt usage and Template Extractor diagnostics

---

## Overview

This update addresses two user concerns:
1. **Verification that Smart Extractor uses user's "What data do you want to extract?" prompt in LLM calls**
2. **Diagnosis of why Template Extractor might fail with screener.in URL while Smart Extractor succeeds**

---

## Changes Made

### 1. Smart Extractor - Enhanced Logging for User Prompt Usage

**File**: `backend/app/services/webscraper/templates/template_auto_generator.py`

**Changes**:

#### Added logging when user instructions are received (lines 309-314)
```python
if user_instructions:
    instructions_section = f"\n\nUser's Extraction Requirements:\n{user_instructions}\n"
    # Log that user instructions are being used
    self.logger.info(f"✓ User instructions will be sent to LLM for analysis: {user_instructions[:150]}{'...' if len(user_instructions) > 150 else ''}")
else:
    self.logger.info("No user instructions provided - using automatic field detection")
```

#### Added logging before LLM call (lines 340-341)
```python
if user_instructions:
    self.logger.info(f"LLM will analyze page with user guidance: '{user_instructions[:100]}{'...' if len(user_instructions) > 100 else ''}'")
```

#### Added metadata flag in generated template (lines 114, 128)
```python
user_instructions_used = user_instructions is not None and len(user_instructions) > 0

metadata={
    'source_url': url,
    'auto_generated': True,
    'user_instructions': user_instructions,
    'user_instructions_used': user_instructions_used,  # NEW: Explicit flag
    ...
}
```

#### Added logging in fallback mode (lines 559-560)
```python
if user_instructions:
    self.logger.info(f"User instructions noted (will influence content field): {user_instructions[:100]}{'...' if len(user_instructions) > 100 else ''}")
```

**Impact**:
- Users can now verify in logs that their prompts are being used
- Template metadata includes `user_instructions_used` flag
- Clear visibility into whether LLM or fallback mode was used
- Better transparency in prompt processing

---

### 2. Template Extractor - Enhanced Error Reporting and Diagnostics

**File**: `backend/app/services/template_extraction_service.py`

**Changes**:

#### Modified `_extract_fields` to return field errors (lines 164-203)
```python
async def _extract_fields(
    self,
    page: Page,
    soup: BeautifulSoup,
    fields: List[ExtractionField]
) -> tuple[Dict[str, Any], Dict[str, str]]:  # Now returns tuple with errors
    """
    Extract all fields from a page

    Returns:
        tuple: (extracted_data, field_errors)
            - extracted_data: Dict of field_name -> extracted_value
            - field_errors: Dict of field_name -> error_message for failed fields
    """
    extracted = {}
    field_errors = {}  # NEW: Track errors per field

    for field in fields:
        try:
            value = await self._extract_single_field(page, soup, field)
            extracted[field.name] = value

            # Track if we got a None or default value (potential extraction failure)
            if value is None and field.required:
                field_errors[field.name] = f"Required field returned None (selector: {field.selector or field.xpath or 'N/A'})"
                logger.warning(f"⚠ Field '{field.name}' extraction returned None. Selector: {field.selector}")
            elif value == field.default_value and field.default_value is not None:
                logger.info(f"Field '{field.name}' used default value: {field.default_value}")

        except Exception as e:
            error_msg = f"Error extracting field: {str(e)}"
            field_errors[field.name] = error_msg
            logger.error(f"✗ Error extracting field '{field.name}': {e}")

    return extracted, field_errors
```

#### Updated caller to use field errors (lines 122-133)
```python
# Extract each field
extracted_row, field_errors = await self._extract_fields(page, soup, template.fields)
all_data.append(extracted_row)

# Log field extraction results
successful_fields = len([v for v in extracted_row.values() if v is not None])
total_fields = len(template.fields)
logger.info(f"Extracted {successful_fields}/{total_fields} fields successfully")

if field_errors:
    logger.warning(f"Field extraction issues: {len(field_errors)} fields had errors")
    for field_name, error in field_errors.items():
        logger.warning(f"  - {field_name}: {error}")
```

#### Enhanced selector logging in `_extract_single_field` (lines 233-249)
```python
# Try CSS selector first (Playwright)
if field.selector:
    try:
        element = await page.query_selector(field.selector)
        if element:
            ...
            logger.debug(f"✓ Playwright selector succeeded for '{field.name}': {field.selector}")
        else:
            logger.debug(f"✗ Playwright selector found no element for '{field.name}': {field.selector}")
    except Exception as e:
        logger.debug(f"✗ Playwright selector failed for '{field.name}': {e}")

# Fallback to BeautifulSoup
if value is None and field.selector:
    element = soup.select_one(field.selector)
    if element:
        ...
        logger.debug(f"✓ BeautifulSoup selector succeeded for '{field.name}': {field.selector}")
    else:
        logger.debug(f"✗ BeautifulSoup selector found no element for '{field.name}': {field.selector}")
```

**Impact**:
- Failed field extractions are now explicitly tracked
- Logs show success/failure rate for each extraction attempt
- Each selector attempt is logged with clear success (✓) or failure (✗) indicators
- Errors include which selector failed, making debugging much easier
- Field errors dictionary can be used in API responses (future enhancement)

---

### 3. Documentation - Comprehensive Analysis

**File**: `docs/debugging/TEMPLATE_VS_SMART_EXTRACTOR_ANALYSIS.md`

**Content**:
- Complete code flow analysis for both extractors
- Evidence that Smart Extractor DOES use user prompts
- Diagnosis of why Template Extractor might fail
- Comparison of both approaches
- Root cause analysis
- Testing recommendations
- Future improvement suggestions

**Impact**:
- Comprehensive reference for understanding both extraction methods
- Clear evidence addressing user's concerns
- Actionable debugging steps
- Foundation for future improvements

---

### 4. Diagnostic Script

**File**: `scripts/debugging/diagnose-template-vs-smart-extraction.py`

**Purpose**: Automated diagnostic tool to compare both extractors

**Features**:
- Tests Template Extractor with screener.in URL
- Tests Smart Extractor with same URL
- Validates CSS selectors on actual page
- Shows webpage content and structure
- Provides side-by-side comparison
- Identifies which selectors work/fail

**Usage**:
```bash
# Run inside backend container
docker-compose exec backend python /app/scripts/debugging/diagnose-template-vs-smart-extraction.py
```

**Impact**:
- Quick diagnosis of extraction issues
- Validates selectors against real pages
- Identifies selector mismatches
- Can be used for any website

---

## Verification Steps

### 1. Verify Smart Extractor Uses User Prompt

**Test**:
```bash
curl -X POST http://localhost:8000/api/v1/extract/smart-extract \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.screener.in/company/BHARTIARTL/consolidated/",
    "user_instructions": "Extract financial metrics: market cap, P/E ratio, ROE, ROCE",
    "llm_provider": "ollama"
  }'
```

**Expected Logs**:
```
INFO - ✓ User instructions will be sent to LLM for analysis: Extract financial metrics: market cap, P/E ratio, ROE, ROCE
INFO - Calling LLM service with provider: ollama
INFO - LLM will analyze page with user guidance: 'Extract financial metrics: market cap, P/E ratio, ROE, ROCE'
```

**Expected Response Metadata**:
```json
{
  "template": {
    "metadata": {
      "user_instructions": "Extract financial metrics: market cap, P/E ratio, ROE, ROCE",
      "user_instructions_used": true,
      "generated_by": "LLM",
      ...
    }
  }
}
```

### 2. Verify Template Extractor Error Reporting

**Test**:
```bash
curl -X POST http://localhost:8000/api/v1/extract/preset/screener_in \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.screener.in/company/BHARTIARTL/consolidated/"
  }'
```

**Expected Logs** (if selectors fail):
```
INFO - Extracting data from page 1
INFO - Extracted 3/10 fields successfully
WARNING - Field extraction issues: 7 fields had errors
WARNING -   - Market Cap: Required field returned None (selector: #top-ratios > li:nth-child(1) > span.number)
WARNING -   - Current Price: Required field returned None (selector: #top-ratios > li:nth-child(2) > span.number)
...
```

**Expected Logs** (if selectors succeed):
```
INFO - Extracting data from page 1
INFO - Extracted 10/10 fields successfully
```

---

## Key Improvements

### Smart Extractor ✅
1. ✅ Clear logging shows user prompt is being used
2. ✅ Metadata flag `user_instructions_used` in response
3. ✅ Logging at multiple stages (receipt, LLM call, fallback)
4. ✅ Better visibility into LLM vs fallback mode

### Template Extractor ✅
1. ✅ Field-level error tracking
2. ✅ Success/failure rate reporting
3. ✅ Detailed selector diagnostics (debug level)
4. ✅ Clear indicators for which selectors work
5. ✅ Better error messages for debugging

### Documentation ✅
1. ✅ Comprehensive analysis document
2. ✅ Code flow verification
3. ✅ Testing recommendations
4. ✅ Future improvement roadmap

### Tools ✅
1. ✅ Diagnostic script for comparing extractors
2. ✅ Automated selector validation
3. ✅ Side-by-side comparison capability

---

## Answering User's Questions

### Question 1: "Is the Smart Extractor using the user's prompt?"

**Answer**: ✅ **YES, absolutely**

**Evidence**:
1. **Code Analysis**: Lines 309-322 in `template_auto_generator.py` explicitly add user instructions to the LLM prompt
2. **Call Flow**: User instructions flow through: API → generate_template_from_user_instructions → analyze_webpage_and_generate_template → LLM prompt
3. **Now Logged**: With this update, you'll see clear log messages confirming prompt usage
4. **Metadata**: Response includes `user_instructions_used: true` flag

### Question 2: "Why does Template Extractor fail with screener.in but Smart Extractor succeeds?"

**Answer**: The issue is **NOT with the URL**, but with the **extraction method**:

**Template Extractor**:
- Uses **hardcoded CSS selectors** from template
- Selectors might be outdated if page structure changed
- Fails silently if selectors don't match
- No adaptation to actual page content

**Smart Extractor**:
- **Analyzes actual page content** dynamically
- Adapts to current page structure
- Uses LLM to intelligently find data
- Has fallback to rule-based extraction

**Likely Root Cause**:
- Screener.in page structure may have changed
- CSS selectors like `#top-ratios > li:nth-child(1) > span.number` no longer match
- Template needs updating with current selectors
- Or use Smart Extractor which adapts automatically

**Diagnostic Steps**:
1. Run diagnostic script to test selectors
2. Inspect current page structure with browser DevTools
3. Update template with correct selectors
4. Or switch to Smart Extractor for dynamic sites

---

## Next Steps

1. **Monitor Logs**: Check that new logging provides useful information
2. **Test Both Extractors**: Compare results on various websites
3. **Update Templates**: If Template Extractor fails, update selectors or use Smart Extractor
4. **Gather Feedback**: Determine if additional logging/diagnostics needed
5. **Consider Enhancements**:
   - Add `failed_fields` to API response
   - Implement selector validation before extraction
   - Add automatic fallback from Template to Smart Extractor
   - Create UI indicators showing prompt usage

---

## Files Changed

1. ✅ `backend/app/services/webscraper/templates/template_auto_generator.py`
   - Added user prompt usage logging
   - Added metadata flags
   - Enhanced transparency

2. ✅ `backend/app/services/template_extraction_service.py`
   - Added field error tracking
   - Enhanced selector logging
   - Improved error reporting

3. ✅ `docs/debugging/TEMPLATE_VS_SMART_EXTRACTOR_ANALYSIS.md`
   - Comprehensive analysis document
   - Evidence and recommendations
   - Testing procedures

4. ✅ `scripts/debugging/diagnose-template-vs-smart-extraction.py`
   - Diagnostic tool for comparing extractors
   - Selector validation
   - Side-by-side comparison

5. ✅ `CHANGES_SUMMARY.md` (this file)
   - Complete change documentation
   - Verification procedures
   - User question answers

---

## Conclusion

This update provides:
1. ✅ **Clear verification** that Smart Extractor uses user prompts
2. ✅ **Better diagnostics** for Template Extractor failures
3. ✅ **Comprehensive documentation** of both systems
4. ✅ **Diagnostic tools** for troubleshooting
5. ✅ **Enhanced logging** for transparency

Both user concerns have been addressed with code improvements, documentation, and diagnostic capabilities.

---

**Status**: Ready for Testing and Deployment
**Review**: Recommended before merging to main
**Testing**: Use verification steps above
