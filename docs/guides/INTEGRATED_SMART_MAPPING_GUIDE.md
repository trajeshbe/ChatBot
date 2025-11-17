# Integrated Smart Template Mapping Guide

## Overview

Smart Template Mapping is now **fully integrated** into both extraction workflows:

1. **New Standalone Endpoint**: `/api/v1/extract/smart-map-to-template`
2. **Enhanced Template Extraction**: `/api/v1/extract/custom` with `use_smart_mapping` flag

This guide shows you how to use both approaches to solve the null value problem and get accurate data extraction.

---

## 🆕 Approach 1: Smart Map Endpoint (Recommended for Quick Extraction)

### When to Use
- You have custom template columns from Excel
- You want quick extraction without defining selectors
- You're experiencing null values with traditional extraction

### API Endpoint
```
POST /api/v1/extract/smart-map-to-template
```

### Request Format

```json
{
  "url": "https://www.screener.in/company/RELIANCE/",
  "template_columns": [
    "Company Name",
    "Market Cap",
    "Current Price",
    "Stock P/E",
    "Revenue Growth"
  ],
  "template_examples": {
    "Market Cap": "1,234 Cr",
    "Stock P/E": "25.3"
  },
  "llm_provider": "openai",
  "output_format": "json",
  "session_id": "optional-session-id"
}
```

### Response Format

```json
{
  "success": true,
  "url": "https://www.screener.in/company/RELIANCE/",
  "template_name": "Smart Template Mapping",
  "data": [
    {
      "Company Name": "Reliance Industries Ltd.",
      "Market Cap": "17,88,392 Cr",
      "Current Price": "2,645",
      "Stock P/E": "25.3",
      "Revenue Growth": "— (requires additional research)"
    }
  ],
  "row_count": 1,
  "extracted_at": "2025-11-17T12:00:00Z",
  "session_id": "optional-session-id",
  "error": null
}
```

### Python Example

```python
import httpx
import asyncio

async def smart_map_extraction():
    request_data = {
        "url": "https://www.screener.in/company/RELIANCE/",
        "template_columns": [
            "Company Name",
            "Market Cap",
            "Current Price",
            "Stock P/E",
            "Book Value",
            "Dividend Yield",
            "ROCE",
            "ROE",
            "Revenue Growth"
        ],
        "template_examples": {
            "Market Cap": "1,234 Cr",
            "Stock P/E": "25.3"
        },
        "llm_provider": "openai",
        "output_format": "json"
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "http://localhost:8000/api/v1/extract/smart-map-to-template",
            json=request_data
        )

        if response.status_code == 200:
            result = response.json()
            data = result['data'][0]

            print("Extracted Data:")
            for col, value in data.items():
                status = "✓" if value != "— (requires additional research)" else "✗"
                print(f"{status} {col}: {value}")
        else:
            print(f"Error: {response.text}")

asyncio.run(smart_map_extraction())
```

### cURL Example

```bash
curl -X POST "http://localhost:8000/api/v1/extract/smart-map-to-template" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.screener.in/company/RELIANCE/",
    "template_columns": [
      "Company Name",
      "Market Cap",
      "Current Price",
      "Stock P/E"
    ],
    "llm_provider": "openai"
  }'
```

---

## 🔧 Approach 2: Enhanced Template Extraction (Recommended for Existing Templates)

### When to Use
- You already have template definitions with fields
- You want to switch from selector-based to smart mapping
- You're experiencing null values with existing templates

### API Endpoint
```
POST /api/v1/extract/custom
```

### Key Change: `use_smart_mapping` Flag

Add `"use_smart_mapping": true` to your existing template request to enable AI-based mapping.

### Request Format (Smart Mapping Enabled)

```json
{
  "name": "Financial Data Extractor",
  "description": "Extract financial metrics",
  "url": "https://www.screener.in/company/RELIANCE/",
  "use_smart_mapping": true,
  "fields": [
    {"name": "Company Name"},
    {"name": "Market Cap"},
    {"name": "Current Price"},
    {"name": "Stock P/E"},
    {"name": "Revenue Growth"}
  ]
}
```

### Request Format (Traditional Selectors)

```json
{
  "name": "Financial Data Extractor",
  "description": "Extract financial metrics",
  "url": "https://www.screener.in/company/RELIANCE/",
  "use_smart_mapping": false,
  "fields": [
    {
      "name": "Company Name",
      "selector": "h1.h2",
      "data_type": "text"
    },
    {
      "name": "Market Cap",
      "selector": "#top-ratios > li:nth-child(1) > span.number",
      "data_type": "text"
    }
  ]
}
```

### Python Example (Switching to Smart Mapping)

```python
import httpx
import asyncio

async def enhanced_template_extraction():
    # Your existing template definition
    request_data = {
        "name": "Financial Data Extractor",
        "description": "Extract financial metrics using smart mapping",
        "url": "https://www.screener.in/company/RELIANCE/",

        # NEW: Just add this flag!
        "use_smart_mapping": True,

        # Fields - no selectors needed when using smart mapping
        "fields": [
            {"name": "Company Name"},
            {"name": "Market Cap"},
            {"name": "Current Price"},
            {"name": "Stock P/E"},
            {"name": "Book Value"},
            {"name": "Dividend Yield"},
            {"name": "ROCE"},
            {"name": "ROE"}
        ]
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "http://localhost:8000/api/v1/extract/custom",
            json=request_data
        )

        if response.status_code == 200:
            result = response.json()
            print(f"Success! Extracted {result['row_count']} row(s)")

            data = result['data'][0]
            successful = sum(1 for v in data.values() if v != "— (requires additional research)")
            total = len(data)

            print(f"Fields extracted: {successful}/{total}")
        else:
            print(f"Error: {response.text}")

asyncio.run(enhanced_template_extraction())
```

---

## 📊 Comparison: Smart Mapping vs Selectors

### Smart Mapping

| Feature | Value |
|---------|-------|
| **Selector Writing** | ❌ Not needed |
| **Null Values** | ✅ Never (marks as "requires research") |
| **Adapts to Changes** | ✅ Yes |
| **Speed** | 🟡 Moderate (LLM call) |
| **Cost** | 💰 LLM API costs |
| **Setup Time** | ⚡ Very fast |
| **Maintenance** | 🔧 Minimal |

### Selector-Based

| Feature | Value |
|---------|-------|
| **Selector Writing** | ✅ Required |
| **Null Values** | ❌ Common if selectors fail |
| **Adapts to Changes** | ❌ Breaks with page changes |
| **Speed** | ⚡ Very fast |
| **Cost** | 💰 Free |
| **Setup Time** | 🕒 Slower (write selectors) |
| **Maintenance** | 🔧 High (update selectors) |

---

## 🎯 Migration Guide

### Migrating Existing Templates to Smart Mapping

**Step 1:** Identify templates with null value problems

```python
# Old template returning nulls
{
  "name": "Product Extractor",
  "fields": [
    {"name": "Product Name", "selector": ".product-title"},
    {"name": "Price", "selector": ".price"}
  ]
}
```

**Step 2:** Add `use_smart_mapping: true`

```python
# New template with smart mapping
{
  "name": "Product Extractor",
  "use_smart_mapping": true,  # ← Add this!
  "fields": [
    {"name": "Product Name"},  # ← Remove selectors
    {"name": "Price"}
  ]
}
```

**Step 3:** Test and compare results

```python
# Run both versions and compare
old_result = extract_with_selectors(url, template)
new_result = extract_with_smart_mapping(url, template)

print("Old approach fields with values:", count_non_null(old_result))
print("New approach fields with values:", count_non_null(new_result))
```

---

## 🚀 Use Cases

### Use Case 1: Financial Data Extraction

**Problem:** Extracting company financials from screener.in, getting null values

**Solution:** Use smart mapping endpoint

```python
template_columns = [
    "Company Name",
    "Market Cap",
    "Current Price",
    "Stock P/E",
    "Book Value",
    "Dividend Yield",
    "ROCE",
    "ROE",
    "Face Value"
]

result = await smart_map_extraction(
    url="https://www.screener.in/company/RELIANCE/",
    template_columns=template_columns
)
```

**Result:**
- ✅ All available fields extracted
- ✅ Missing fields clearly marked
- ✅ No null values

### Use Case 2: Multi-Company Extraction

**Problem:** Extracting data from 100+ company pages with slight variations

**Solution:** Use smart mapping for flexibility

```python
companies = [
    "https://www.screener.in/company/RELIANCE/",
    "https://www.screener.in/company/TCS/",
    "https://www.screener.in/company/INFY/",
    # ... 100+ more
]

template_columns = ["Company Name", "Market Cap", "Stock P/E", "ROE"]

all_data = []
for url in companies:
    result = await smart_map_extraction(url, template_columns)
    all_data.append(result['data'][0])

# Export to Excel
df = pd.DataFrame(all_data)
df.to_excel('companies.xlsx', index=False)
```

**Benefits:**
- Handles variations across company pages
- No need to update selectors for each variation
- Robust to page structure changes

### Use Case 3: One-Time Data Extraction

**Problem:** Need to extract data once from a website you don't control

**Solution:** Use smart map endpoint for quick extraction

```python
# No template setup needed!
result = await smart_map_extraction(
    url="https://example.com/data-page",
    template_columns=[
        "Title",
        "Author",
        "Date",
        "Content",
        "Tags"
    ]
)
```

**Benefits:**
- Zero setup time
- No selector maintenance
- Get results immediately

---

## 🔍 Debugging & Troubleshooting

### Issue 1: All Fields Return "— (requires additional research)"

**Diagnosis:**
```python
# Check if data was scraped
scrape_result = await scraper_service.scrape_url(url)
print(f"Scraped data length: {len(scrape_result['html'])}")
print(f"First 500 chars: {scrape_result['html'][:500]}")
```

**Solutions:**
1. URL may be blocking automated access
2. Scraped content may be empty
3. Column names may not match data labels

**Fix:**
```python
# Be more specific with column names
template_columns = [
    "Current Market Capitalization",  # Instead of "Market Cap"
    "Latest Stock Price",              # Instead of "Price"
]

# Provide examples
template_examples = {
    "Current Market Capitalization": "1,234 Cr"
}
```

### Issue 2: LLM Service Not Available

**Error:**
```
LLM service not initialized
```

**Solution:**
```bash
# Check .env file
cat .env | grep OPENAI_API_KEY

# Should have:
OPENAI_API_KEY=sk-...

# Restart backend
docker-compose restart backend
```

### Issue 3: Slow Performance

**Problem:** Smart mapping takes 30+ seconds

**Solutions:**

```python
# 1. Use faster LLM provider
"llm_provider": "openai"  # Faster than ollama

# 2. Reduce template columns
template_columns = template_columns[:10]  # Limit to 10 fields

# 3. Pre-clean scraped data
from bs4 import BeautifulSoup
soup = BeautifulSoup(scraped_html, 'html.parser')
cleaned_data = soup.get_text()
```

---

## 📈 Performance Tips

### Tip 1: Batch Processing

For multiple URLs, process in batches:

```python
import asyncio

async def batch_smart_mapping(urls, template_columns, batch_size=5):
    results = []

    for i in range(0, len(urls), batch_size):
        batch = urls[i:i+batch_size]

        tasks = [
            smart_map_extraction(url, template_columns)
            for url in batch
        ]

        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)

    return results
```

### Tip 2: Cache Scraped Data

Avoid re-scraping when testing:

```python
# Cache scraped data
cached_scrapes = {}

async def cached_smart_mapping(url, template_columns):
    if url not in cached_scrapes:
        scrape_result = await scraper_service.scrape_url(url)
        cached_scrapes[url] = scrape_result['html']

    return await smart_map_extraction(
        scraped_data=cached_scrapes[url],
        template_columns=template_columns
    )
```

### Tip 3: Use OpenAI for Production

OpenAI is faster and more accurate than Ollama:

```python
# Production: Use OpenAI
"llm_provider": "openai"

# Development/Testing: Use Ollama (free)
"llm_provider": "ollama"
```

---

## 🧪 Testing

Run the integration tests:

```bash
cd backend
python test_integrated_smart_mapping.py
```

Expected output:
```
TEST 1: NEW /smart-map-to-template ENDPOINT
================================================================================
Sending request to http://localhost:8000/api/v1/extract/smart-map-to-template

Response status: 200

✓ SUCCESS!
Extracted Data:
  ✓ Company Name              : Reliance Industries Ltd.
  ✓ Market Cap                : 17,88,392 Cr
  ✓ Current Price             : 2,645
  ✓ Stock P/E                 : 25.3
  ✗ Revenue Growth            : — (requires additional research)
```

---

## 📚 API Reference

### Smart Map Endpoint

```
POST /api/v1/extract/smart-map-to-template
```

**Request Body:**
- `url` (string, required): URL to scrape
- `template_columns` (array, required): Column headers from template
- `template_examples` (object, optional): Example values for guidance
- `llm_provider` (string, optional): "openai", "anthropic", or "ollama"
- `output_format` (string, optional): "excel", "csv", or "json"
- `session_id` (string, optional): Session identifier

**Response:**
- `success` (boolean): Whether extraction succeeded
- `url` (string): Scraped URL
- `template_name` (string): Template name
- `data` (array): Extracted data rows
- `row_count` (integer): Number of rows
- `extracted_at` (string): ISO timestamp
- `session_id` (string): Session identifier
- `error` (string): Error message if failed

### Enhanced Custom Endpoint

```
POST /api/v1/extract/custom
```

**New Parameter:**
- `use_smart_mapping` (boolean, optional, default: false): Enable smart mapping

When `use_smart_mapping=true`:
- Selectors in fields are ignored
- LLM maps scraped data to field names
- Never returns null (marks as "requires research")

---

## 🎓 Best Practices

### 1. Choose the Right Approach

| Scenario | Recommended Approach |
|----------|---------------------|
| Quick one-time extraction | Smart Map Endpoint |
| Existing templates with nulls | Enhanced Custom (smart mapping) |
| Stable pages, high volume | Enhanced Custom (selectors) |
| Changing page structures | Smart Map Endpoint |

### 2. Optimize Column Names

```python
# ❌ Bad
template_columns = ["MC", "P", "PE"]

# ✅ Good
template_columns = [
    "Market Capitalization",
    "Current Stock Price",
    "Price to Earnings Ratio"
]
```

### 3. Provide Examples When Possible

```python
template_examples = {
    "Market Capitalization": "1,234 Cr",
    "Price to Earnings Ratio": "25.3"
}
```

### 4. Handle Missing Fields

```python
result = await smart_map_extraction(url, columns)
data = result['data'][0]

# Filter out fields requiring research
complete_data = {
    k: v for k, v in data.items()
    if v != "— (requires additional research)"
}

# Or highlight them
for col, value in data.items():
    if value == "— (requires additional research)":
        print(f"⚠️  {col} needs manual research")
```

---

## 🔗 Related Documentation

- [Smart Template Mapping Guide](./SMART_TEMPLATE_MAPPING_GUIDE.md) - Core concepts
- [API Documentation](http://localhost:8000/api/docs) - Interactive API docs
- [Template Extraction Guide](./TEMPLATE_EXTRACTION_GUIDE.md) - Selector-based approach

---

**Last Updated:** 2025-11-17
**Version:** 1.0
**Status:** Production Ready
