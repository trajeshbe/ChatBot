# Smart Extraction Guide

> **Feature Status**: ✨ NEW - Intelligent template auto-generation and LLM-guided data mapping
> **Last Updated**: 2025-11-16

---

## Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Architecture](#architecture)
4. [Usage Guide](#usage-guide)
5. [API Reference](#api-reference)
6. [Examples](#examples)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The **Smart Extraction** feature revolutionizes web scraping by eliminating the need for predefined templates. Instead of manually creating templates with CSS selectors and XPath expressions, you simply describe what data you want to extract in natural language, and AI handles the rest.

### What Problems Does This Solve?

1. **No Template Needed**: Extract data without creating Excel templates or defining complex selectors
2. **Intelligent Column Discovery**: AI analyzes webpage content and suggests optimal fields to extract
3. **Dynamic Mapping**: LLM intelligently maps scraped data to appropriate columns
4. **Natural Language Interface**: Guide the extraction process with plain English instructions
5. **Adaptive Extraction**: Works with websites you've never seen before

### How It Works

```
┌─────────────────┐
│ User provides:  │
│ - URL           │
│ - Instructions  │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ AI analyzes:    │
│ - Page content  │
│ - Structure     │
│ - Data patterns │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ AI generates:   │
│ - Field names   │
│ - Data types    │
│ - Extractors    │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Data extracted  │
│ and formatted   │
└─────────────────┘
```

---

## Key Features

### 1. Auto-Generate Templates

**What it does**: Analyzes a webpage and automatically creates an extraction template

**Use case**: When you need to extract data but don't know the page structure

**Endpoint**: `POST /api/v1/extract/auto-generate`

**Benefits**:
- No manual template creation
- AI suggests optimal fields
- Identifies data patterns automatically
- Provides confidence scores

### 2. Smart Extraction

**What it does**: Extracts data using only a URL and natural language instructions

**Use case**: Quick, one-off data extraction tasks

**Endpoint**: `POST /api/v1/extract/smart-extract`

**Benefits**:
- Immediate results (no template creation step)
- Natural language interface
- Multiple output formats (Excel, CSV, JSON)
- Session-based data tracking

### 3. LLM-Guided Mapping

**What it does**: Uses LLM to intelligently map extracted data to columns

**Use case**: Complex extractions with ambiguous data structures

**Features**:
- **Multi-provider support**: OpenAI, Anthropic, Ollama (local)
- **Extraction strategies**: CSS, XPath, Regex, or LLM-based
- **Type conversion**: Automatic data type detection and conversion
- **Validation**: Built-in data validation rules

---

## Architecture

### Backend Components

#### 1. Template Auto-Generator Service
**File**: `backend/app/services/webscraper/templates/template_auto_generator.py`

**Key Methods**:
- `analyze_webpage_and_generate_template()`: Main auto-generation method
- `generate_template_from_user_instructions()`: Natural language interface
- `refine_template_with_user_feedback()`: Iterative refinement

**Workflow**:
```python
# Step 1: Fetch webpage content
page_content = await _fetch_webpage_content(url)

# Step 2: Analyze with LLM
analysis_result = await _analyze_content_structure(
    page_content,
    user_instructions,
    llm_provider
)

# Step 3: Generate field definitions
fields = await _generate_field_definitions(
    analysis_result,
    page_content,
    llm_provider
)

# Step 4: Create template
template = ExtractionTemplate(
    name=template_name,
    fields=fields,
    schema_definition=schema
)
```

#### 2. LLM Extractor
**File**: `backend/app/services/webscraper/extractors/llm_extractor.py`

**Features**:
- Single field extraction
- Multi-field extraction (batch)
- Structured data extraction
- Confidence scoring

**Example Usage**:
```python
# Extract single field
result = await llm_extractor.extract(
    content=page_html,
    prompt="Extract the product price",
    field_name="price",
    field_type="float",
    llm_provider="ollama"
)

# Extract multiple fields
results = await llm_extractor.extract_multiple_fields(
    content=page_html,
    field_definitions=[
        {"name": "product_name", "prompt": "Extract product name", "type": "string"},
        {"name": "price", "prompt": "Extract price", "type": "float"},
        {"name": "rating", "prompt": "Extract rating", "type": "float"}
    ]
)
```

### Frontend Components

#### 1. SmartExtractor Component
**File**: `frontend/src/components/SmartExtractor.tsx`

**Features**:
- Natural language instruction input
- Example prompt suggestions
- Real-time extraction status
- Template preview (auto-generated fields)
- Data preview with export

#### 2. DataExtractionHub Component
**File**: `frontend/src/components/DataExtractionHub.tsx`

**Features**:
- Tab interface: Smart vs Template-based extraction
- Feature comparison displays
- Mode-specific instructions

---

## Usage Guide

### Option 1: Smart Extraction (Recommended for Quick Tasks)

#### Via UI

1. **Navigate to Data Extraction**
   - Click "Data Extraction" in the sidebar
   - Select "Smart Extraction" tab

2. **Enter URL**
   ```
   URL: https://example.com/products
   ```

3. **Provide Instructions**
   ```
   Extract product information: name, price, description, and availability
   ```

4. **Configure Settings**
   - AI Provider: Ollama (local), OpenAI, or Anthropic
   - Output Format: Excel, CSV, or JSON
   - Max Fields: 15 (recommended)

5. **Click "Smart Extract"**
   - AI analyzes the page
   - Template is auto-generated
   - Data is extracted
   - Results displayed with preview

6. **Download Results**
   - Click "Download" for Excel/CSV/JSON export

#### Via API

```bash
curl -X POST "http://localhost:8000/api/v1/extract/smart-extract" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/products",
    "user_instructions": "Extract product names, prices, and ratings",
    "llm_provider": "ollama",
    "output_format": "excel"
  }'
```

**Response**:
```json
{
  "success": true,
  "url": "https://example.com/products",
  "template_name": "auto_generated_example.com",
  "data": [
    {
      "product_name": "Laptop",
      "price": 999.99,
      "rating": 4.5
    }
  ],
  "row_count": 1,
  "extracted_at": "2025-11-16T10:30:00Z"
}
```

### Option 2: Auto-Generate Template (For Reusable Templates)

#### Via UI

1. **Navigate to Data Extraction** > **Smart Extraction**

2. **Expand Advanced Options**

3. **Click "Generate Template Only"**
   - Reviews auto-generated fields
   - See extraction strategies
   - Check confidence scores

4. **Review Template**
   - Field names and types
   - Extraction strategies (CSS, XPath, LLM)
   - Validation rules

5. **Use Template**
   - Save for reuse
   - Refine with feedback
   - Apply to similar pages

#### Via API

```bash
curl -X POST "http://localhost:8000/api/v1/extract/auto-generate" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/products",
    "user_instructions": "Extract product details",
    "llm_provider": "ollama",
    "max_fields": 10
  }'
```

**Response**:
```json
{
  "success": true,
  "template": {
    "name": "auto_generated_example.com",
    "description": "Auto-generated template for https://example.com/products",
    "template_type": "product_data",
    "fields_count": 5
  },
  "fields": [
    {
      "name": "product_name",
      "display_name": "Product Name",
      "description": "The name of the product",
      "type": "string",
      "required": true,
      "extraction_strategy": "llm",
      "extraction_hint": "Extract the product name"
    },
    {
      "name": "price",
      "display_name": "Price",
      "description": "Product price",
      "type": "float",
      "required": true,
      "extraction_strategy": "css",
      "extraction_hint": ".price"
    }
  ],
  "confidence": 0.85
}
```

---

## API Reference

### Auto-Generate Template

**Endpoint**: `POST /api/v1/extract/auto-generate`

**Request Body**:
```typescript
{
  url: string                    // Required: URL to analyze
  user_instructions?: string     // Optional: What data to extract
  template_name?: string         // Optional: Custom template name
  llm_provider?: string          // Default: "ollama"
  max_fields?: number            // Default: 15, Range: 1-30
  session_id?: string            // Optional: Session ID
}
```

**Response**:
```typescript
{
  success: boolean
  template?: {
    name: string
    description: string
    template_type: string
    fields_count: number
    metadata: object
  }
  fields?: Array<{
    name: string
    display_name: string
    description: string
    type: "string" | "integer" | "float" | "boolean" | "date"
    required: boolean
    extraction_strategy: "css" | "xpath" | "regex" | "llm"
    extraction_hint: string
  }>
  template_type?: string
  confidence?: number            // 0.0 - 1.0
  message?: string
  error?: string
}
```

### Smart Extract

**Endpoint**: `POST /api/v1/extract/smart-extract`

**Request Body**:
```typescript
{
  url: string                    // Required: URL to scrape
  user_instructions: string      // Required: Extraction instructions
  llm_provider?: string          // Default: "ollama"
  output_format?: string         // Default: "excel"
  session_id?: string            // Optional: Session ID
}
```

**Response**:
```typescript
{
  success: boolean
  url: string
  template_name: string
  data: Array<Record<string, any>>
  row_count: number
  extracted_at: string
  session_id?: string
  error?: string
}
```

---

## Examples

### Example 1: E-commerce Product Scraping

**Scenario**: Extract laptop listings from an e-commerce site

**Instructions**:
```
Extract laptop specifications: model name, processor, RAM, storage, price, and customer rating
```

**API Call**:
```bash
curl -X POST "http://localhost:8000/api/v1/extract/smart-extract" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example-shop.com/laptops",
    "user_instructions": "Extract laptop specifications: model name, processor, RAM, storage, price, and customer rating",
    "llm_provider": "ollama",
    "output_format": "excel"
  }'
```

**Expected Fields**:
- `model_name` (string)
- `processor` (string)
- `ram` (string)
- `storage` (string)
- `price` (float)
- `customer_rating` (float)

### Example 2: Financial Data Extraction

**Scenario**: Extract company financials from a stock screener

**Instructions**:
```
Get company financial metrics: revenue, profit margin, market cap, P/E ratio, and 52-week high/low
```

**API Call**:
```bash
curl -X POST "http://localhost:8000/api/v1/extract/auto-generate" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://finance-site.com/stocks/AAPL",
    "user_instructions": "Get company financial metrics: revenue, profit margin, market cap, P/E ratio, and 52-week high/low",
    "max_fields": 8
  }'
```

**Expected Fields**:
- `revenue` (float)
- `profit_margin` (float)
- `market_cap` (float)
- `pe_ratio` (float)
- `week_52_high` (float)
- `week_52_low` (float)

### Example 3: Job Listings

**Scenario**: Scrape job postings

**Instructions**:
```
Extract job listings: job title, company, location, salary range, experience required, and application deadline
```

**API Call**:
```bash
curl -X POST "http://localhost:8000/api/v1/extract/smart-extract" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://job-board.com/software-engineer",
    "user_instructions": "Extract job listings: job title, company, location, salary range, experience required, and application deadline",
    "output_format": "csv"
  }'
```

### Example 4: Real Estate Listings

**Scenario**: Extract property listings

**Instructions**:
```
Pull real estate data: address, price, bedrooms, bathrooms, square footage, year built, and property type
```

---

## Best Practices

### 1. Writing Effective Instructions

**Good Instructions**:
- ✅ "Extract product names, prices, and customer ratings"
- ✅ "Get company financial metrics: revenue, profit margin, and market cap"
- ✅ "Pull article metadata: title, author, publish date, and category"

**Poor Instructions**:
- ❌ "Get everything"
- ❌ "Extract data"
- ❌ "Scrape this page"

**Tips**:
- Be specific about what fields you want
- Use clear, descriptive field names
- Mention data types if important (e.g., "price in USD")
- List fields in order of priority

### 2. Choosing LLM Provider

| Provider | Best For | Pros | Cons |
|----------|----------|------|------|
| **Ollama** | Local, privacy-sensitive | Free, private, no API limits | Slower, less accurate |
| **OpenAI** | High accuracy needed | Fast, very accurate | Costs money, requires API key |
| **Anthropic** | Complex extractions | Best reasoning, context window | Costs money, requires API key |

### 3. Optimizing Field Count

- **1-5 fields**: Quick, accurate extractions
- **6-15 fields**: Balanced (recommended)
- **16-30 fields**: Comprehensive but slower

### 4. Output Format Selection

- **Excel (.xlsx)**: Best for business users, supports formatting
- **CSV (.csv)**: Best for data pipelines, universal compatibility
- **JSON (.json)**: Best for developers, nested data structures

### 5. Handling Errors

**Common Issues**:

1. **"Failed to auto-generate template"**
   - Solution: Provide more specific instructions
   - Check that the URL is accessible
   - Try a different LLM provider

2. **"No data extracted"**
   - Solution: Verify the page has the requested data
   - Check if page requires authentication
   - Inspect the page source manually

3. **"Low confidence score"**
   - Solution: Be more specific in instructions
   - Use template extraction for known sites
   - Manually review and refine the template

---

## Troubleshooting

### Issue: Template generation fails

**Symptoms**: Auto-generate returns error

**Possible Causes**:
1. LLM service not running (Ollama)
2. Invalid URL or page not accessible
3. Page requires authentication
4. Page content is too large

**Solutions**:
```bash
# Check Ollama status
docker-compose logs ollama

# Test URL accessibility
curl -I https://example.com

# Restart services
docker-compose restart backend ollama
```

### Issue: Extracted data is incorrect

**Symptoms**: Fields contain wrong data or null values

**Possible Causes**:
1. Ambiguous instructions
2. Page structure doesn't match expectations
3. Dynamic content not loaded

**Solutions**:
1. Be more specific in instructions
2. Use "Generate Template Only" to review fields
3. Try different LLM provider
4. Use template-based extraction for complex sites

### Issue: Slow extraction

**Symptoms**: Smart extraction takes > 30 seconds

**Possible Causes**:
1. Using remote LLM (OpenAI/Anthropic)
2. Large page with many elements
3. Too many fields requested

**Solutions**:
1. Use Ollama for faster (local) processing
2. Reduce max_fields
3. Be more specific to avoid analyzing entire page

---

## Advanced Topics

### Combining Smart and Template Extraction

You can use smart extraction to generate a template, then refine it for reuse:

1. **Generate template** with `/auto-generate`
2. **Review and save** the template JSON
3. **Refine** the template (adjust selectors, types)
4. **Upload** as custom template
5. **Reuse** for similar pages

### Custom LLM Prompts

Advanced users can customize the extraction prompts:

```python
# In template_auto_generator.py
custom_system_prompt = """You are a data extraction expert specializing in e-commerce sites.
Focus on product attributes and pricing information."""

template = await auto_gen.analyze_webpage_and_generate_template(
    url=url,
    user_instructions=instructions,
    llm_provider="ollama"
)
```

### Batch Processing

For multiple URLs with similar structure:

```python
urls = [
    "https://example.com/product/1",
    "https://example.com/product/2",
    "https://example.com/product/3"
]

# Generate template from first URL
template = await auto_gen.analyze_webpage_and_generate_template(
    url=urls[0],
    user_instructions=instructions
)

# Use template for all URLs
for url in urls:
    result = await extract_with_template(url, template)
```

---

## Integration Examples

### Python SDK

```python
import requests

def smart_extract(url: str, instructions: str):
    response = requests.post(
        "http://localhost:8000/api/v1/extract/smart-extract",
        json={
            "url": url,
            "user_instructions": instructions,
            "output_format": "json"
        }
    )
    return response.json()

# Usage
data = smart_extract(
    url="https://example.com/products",
    instructions="Extract product names and prices"
)

print(f"Extracted {data['row_count']} products")
for item in data['data']:
    print(f"{item['product_name']}: ${item['price']}")
```

### JavaScript/TypeScript

```typescript
async function smartExtract(url: string, instructions: string) {
  const response = await fetch(
    'http://localhost:8000/api/v1/extract/smart-extract',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url,
        user_instructions: instructions,
        output_format: 'json'
      })
    }
  )

  return await response.json()
}

// Usage
const data = await smartExtract(
  'https://example.com/products',
  'Extract product names and prices'
)
```

---

## FAQ

**Q: Do I need to provide CSS selectors or XPath?**
A: No! That's the point of smart extraction. Just describe what you want in plain English.

**Q: Which LLM provider should I use?**
A: Start with Ollama (free, local). Use OpenAI or Anthropic for higher accuracy on complex sites.

**Q: Can I refine the auto-generated template?**
A: Yes! Use the `/refine-template` endpoint with feedback like "Add a field for product ratings".

**Q: How accurate is the extraction?**
A: Depends on LLM provider and page complexity. Typical confidence scores: 0.75-0.95

**Q: Can I use this for authenticated pages?**
A: Not yet. Authentication support is planned for future releases.

**Q: What's the difference between auto-generate and smart-extract?**
A: `auto-generate` creates a template for review/reuse. `smart-extract` generates and immediately extracts in one step.

---

## Related Documentation

- [Template Extraction Guide](./TEMPLATE_EXTRACTION_GUIDE.md) - Traditional template-based extraction
- [Web Scraper Guide](./docs/guides/QUICKSTART.md#web-scraping) - General web scraping features
- [LLM Service Documentation](./backend/app/services/llm_service.py) - LLM provider configuration
- [GraphQL API](./docs/guides/GRAPHQL_EXAMPLES.md) - GraphQL queries for extraction

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/your-repo/issues
- Documentation: [CLAUDE.md](./CLAUDE.md)
- Email: support@example.com

---

**Last Updated**: 2025-11-16
**Version**: 1.0.0
**Status**: ✨ Production Ready
