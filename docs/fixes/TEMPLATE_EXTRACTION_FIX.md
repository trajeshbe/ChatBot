# Template-Based Extraction Fix

## Problem Summary

The template-based extraction module had a critical issue where:

1. **Excel Template Upload** worked (stored templates in `templates_store`)
2. **Template-based extraction jobs** failed because:
   - The workflow didn't load templates from `templates_store`
   - The workflow didn't use the LLM extractor for template columns
   - Data extraction always returned 0 records

## Root Cause

The LangGraph extraction workflow in `workflow_nodes.py` had two incomplete nodes:

### 1. `parse_template_node` (Line 28-66)
- **Problem**: Just a TODO placeholder, didn't actually load templates
- **Effect**: Templates were never loaded from `templates_store`
- **Result**: `state['has_template']` was True but `state['fields']` was empty

### 2. `extract_data_node` (Line 220-260)
- **Problem**: Didn't implement LLM-based extraction for templates
- **Effect**: Even with a template, no data was extracted
- **Result**: Always returned 0 records with 0% quality score

## Solution Implemented

### Fix 1: Template Loading (`parse_template_node`)

**Before:**
```python
# TODO: Load template from database/storage
state['has_template'] = True
logger.info("Template parsed successfully")
```

**After:**
```python
# Import templates_store from extraction_routes
from app.api.routes.extraction_routes import templates_store

# Load template from in-memory store
if state['template_id'] in templates_store:
    template = templates_store[state['template_id']]

    # Extract template information
    state['template_name'] = template.get('name', 'Unknown Template')
    state['fields'] = template.get('fields', [])
    state['llm_extraction_prompts'] = template.get('llm_extraction_prompts', {})
    state['css_selectors'] = template.get('css_selectors', {})
    state['xpath_selectors'] = template.get('xpath_selectors', {})
    state['validation_rules'] = template.get('validation_rules', {})
    state['has_template'] = True
    state['use_llm_extraction'] = len(state['llm_extraction_prompts']) > 0
```

### Fix 2: LLM-Based Extraction (`extract_data_node`)

**Before:**
```python
# TODO: Implement extractor factory
logger.info(f"Extracting {len(state['fields'])} fields from {len(state['raw_data'])} pages")
extracted_data = {field['name']: [] for field in state['fields']}
extracted_data['url'] = [item['url'] for item in state['raw_data'] if item['success']]
state['extracted_data'] = extracted_data
```

**After:**
```python
elif state.get('use_llm_extraction'):
    # Import LLM services
    from app.services.llm_service import llm_service
    from app.services.webscraper.extractors.llm_extractor import LLMExtractor

    # Initialize LLM service
    await llm_service.initialize()
    extractor = LLMExtractor(llm_service=llm_service)

    # Extract column names from fields
    template_columns = [field['name'] for field in state['fields']]

    # Process each scraped page
    all_records = []
    for scraped_item in state['raw_data']:
        if scraped_item.get('success'):
            # Use LLM to map scraped data to template columns
            mapping_result = await extractor.map_to_custom_template(
                scraped_data=scraped_item.get('content', ''),
                template_columns=template_columns,
                template_examples=None,
                llm_provider="openai"
            )

            if mapping_result:
                mapped_data = mapping_result.get('mapped_data', {})
                mapped_data['url'] = scraped_item.get('url')
                all_records.append(mapped_data)

    # Convert to column-based format for DataFrame
    extracted_data = {}
    for col in template_columns:
        extracted_data[col] = [record.get(col, '') for record in all_records]
    extracted_data['url'] = [record.get('url', '') for record in all_records]

    state['extracted_data'] = extracted_data
```

## How It Works Now

### Workflow Flow (Excel Template Upload → Extraction)

```
1. User uploads Excel file with column headers
   └─> POST /api/v1/extraction/templates/upload-excel
       ├─> Reads Excel columns: ["Product Name", "Price", "Rating"]
       ├─> Creates LLM prompts for each column
       └─> Stores in templates_store with template_id

2. User creates extraction job with template_id
   └─> POST /api/v1/extraction/jobs
       └─> {
             "urls": ["https://example.com/product"],
             "template_id": "abc-123",
             "output_format": "excel"
           }

3. LangGraph Workflow Executes
   ├─> parse_template_node
   │   ├─> Loads template from templates_store
   │   ├─> Sets state['fields'] = ["Product Name", "Price", "Rating"]
   │   ├─> Sets state['llm_extraction_prompts'] = {...}
   │   └─> Sets state['use_llm_extraction'] = True
   │
   ├─> scrape_sources_node
   │   └─> Scrapes webpage content using Playwright
   │
   ├─> extract_data_node
   │   ├─> Detects state['use_llm_extraction'] = True
   │   ├─> Initializes LLMExtractor
   │   ├─> For each scraped page:
   │   │   ├─> Calls extractor.map_to_custom_template()
   │   │   ├─> LLM intelligently maps data to columns
   │   │   └─> Returns: {
   │   │         "Product Name": "iPhone 15",
   │   │         "Price": "$999",
   │   │         "Rating": "4.5/5",
   │   │         "url": "https://example.com/product"
   │   │       }
   │   └─> Converts to DataFrame format
   │
   ├─> consolidate_node → transform_node → clean_node → deduplicate_node → validate_node
   │   └─> Quality score calculated based on data completeness
   │
   ├─> generate_output_node
   │   └─> Generates Excel file with extracted data
   │
   └─> deliver_node
       └─> Makes file available for download
```

## Testing the Fix

### 1. Upload an Excel Template

```bash
curl -X POST "http://localhost:8000/api/v1/extraction/templates/upload-excel" \
  -F "file=@my_template.xlsx" \
  -F "template_name=Product Template"

# Response:
{
  "template_id": "abc-123-def-456",
  "name": "Excel Template: my_template.xlsx",
  "fields_count": 5,
  "created_at": "2025-11-17T..."
}
```

### 2. Create Extraction Job

```bash
curl -X POST "http://localhost:8000/api/v1/extraction/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://www.screener.in/company/RELIANCE/"],
    "template_id": "abc-123-def-456",
    "output_format": "excel",
    "delivery_method": "download"
  }'

# Response:
{
  "job_id": "job-789",
  "status": "pending",
  "urls_count": 1,
  ...
}
```

### 3. Check Job Status

```bash
curl "http://localhost:8000/api/v1/extraction/jobs/job-789"

# Response:
{
  "job_id": "job-789",
  "status": "completed",
  "records_extracted": 1,
  "quality_score": 85.5,
  "download_url": "/api/v1/extraction/jobs/job-789/download",
  ...
}
```

### 4. Download Result

```bash
curl -O "http://localhost:8000/api/v1/extraction/jobs/job-789/download"
```

## Key Benefits

1. **✅ No More 0 Records**: Template-based extraction now properly extracts data
2. **✅ LLM Intelligence**: AI intelligently maps scraped data to your Excel columns
3. **✅ Quality Scores**: Proper quality metrics based on data completeness
4. **✅ Clear Missing Fields**: Missing data marked as "— (requires additional research)"
5. **✅ Multiple URLs**: Can extract from multiple pages and consolidate into one Excel

## Files Modified

1. **`backend/app/services/webscraper/workflows/workflow_nodes.py`**
   - Fixed `parse_template_node` to load templates from `templates_store`
   - Fixed `extract_data_node` to use LLM extractor for template columns

## Prerequisites

**Important**: Make sure your `.env` file has a valid OpenAI API key for LLM-based extraction:

```env
OPENAI_API_KEY=sk-your-api-key-here
```

## Remaining Issues

### Preset Templates (screener_in)

The preset templates still use selector-based extraction which may be fragile. The fix applied here only affects **uploaded Excel templates** that use LLM extraction.

**Preset template flow:**
- Uses `/api/v1/extract/preset/screener_in` endpoint
- Uses CSS selectors defined in `get_screener_in_template()`
- Uses `template_extraction_service.py` (different from workflow)
- **Not affected by this fix**

**Recommendation**: Convert preset templates to use the LLM-based workflow instead of selector-based extraction.

## Next Steps

1. **Test the fix** with a simple Excel template
2. **Check backend logs** for any errors during extraction
3. **Verify OpenAI API key** is configured in `.env`
4. **Monitor quality scores** to ensure good extraction results

## Debugging Tips

If extraction still fails:

1. **Check backend logs:**
   ```bash
   docker-compose logs -f backend | grep -E "(template|extraction|LLM)"
   ```

2. **Verify template upload:**
   ```bash
   curl "http://localhost:8000/api/v1/extraction/templates"
   ```

3. **Check LLM service:**
   ```bash
   curl "http://localhost:8000/health"
   ```

4. **Test with Smart Extraction first** (doesn't require templates):
   ```bash
   curl -X POST "http://localhost:8000/api/v1/extract/smart-extract" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://www.screener.in/company/RELIANCE/",
       "user_instructions": "Extract company name, market cap, and stock price",
       "llm_provider": "openai"
     }'
   ```

---

**Status**: ✅ Fix completed and ready for testing
**Date**: 2025-11-17
