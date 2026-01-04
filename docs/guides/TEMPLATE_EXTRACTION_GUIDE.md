# Template Extraction & Web Scraping Guide

> **Last Updated**: 2025-11-16
> **Features**: Template-based data extraction, Excel export, Session management, Collapsible errors

---

## Overview

This guide covers the new features added to the Enterprise RAG Chatbot:

1. **Template-based Data Extraction**: Extract structured data from websites using predefined or custom templates
2. **Excel Export**: Export extracted data to formatted Excel files
3. **Session Management**: Maintain scraping history across page navigation
4. **Collapsible Error Messages**: Improved UX with collapsible error displays
5. **Docling Integration**: Multi-format document processing (PDF, HTML, DOCX, PPTX)

---

## Installation & Setup

### 1. Install New Dependencies

Update the backend with new Python packages:

```bash
cd backend
pip install -r requirements.txt
```

**New dependencies added:**
- `docling==2.0.0` - Advanced document parsing
- `python-dateutil==2.8.2` - Flexible date parsing
- Already have: `pandas`, `xlsxwriter`, `playwright`

### 2. Install Playwright Browsers

```bash
playwright install --with-deps chromium
```

### 3. Rebuild Docker Containers (if using Docker)

```bash
# Stop existing containers
docker-compose down

# Rebuild with new dependencies
docker-compose build --no-cache backend frontend

# Start services
docker-compose up -d

# Install Playwright in backend container
docker-compose exec backend playwright install --with-deps chromium
```

---

## API Endpoints

### Template Extraction Endpoints

#### 1. Extract with Preset Template

```http
POST /api/v1/extract/preset/{preset_name}
Content-Type: application/json

{
  "url": "https://www.screener.in/company/BHARTIARTL/consolidated/",
  "session_id": "session-123" // Optional
}
```

**Available Presets:**
- `screener_in` - Extract financial data from Screener.in company pages

**Response:**
```json
{
  "success": true,
  "url": "https://www.screener.in/company/BHARTIARTL/consolidated/",
  "template_name": "Screener.in Company Data",
  "data": [
    {
      "Company Name": "Bharti Airtel",
      "Market Cap": 9250000,
      "Current Price": 1542.50,
      "Stock P/E": 35.2,
      "Book Value": 185.3,
      "Dividend Yield": 0.52,
      "ROCE": 12.5,
      "ROE": 18.3,
      "Face Value": 5,
      "Market Position": "Leading telecom operator in India",
      "Source / Notes": "Scraped from Screener.in"
    }
  ],
  "row_count": 1,
  "extracted_at": "2025-11-16T12:00:00Z",
  "session_id": "session-123"
}
```

#### 2. Extract with Custom Template

```http
POST /api/v1/extract/custom
Content-Type: application/json

{
  "name": "My Custom Template",
  "description": "Extract product data",
  "url": "https://example.com/products",
  "fields": [
    {
      "name": "Product Name",
      "selector": "h1.product-title",
      "required": true
    },
    {
      "name": "Price",
      "selector": "span.price",
      "data_type": "number"
    },
    {
      "name": "Rating",
      "selector": "div.rating",
      "regex": "\\d+\\.\\d+",
      "data_type": "number"
    }
  ],
  "wait_for_selector": "div.product-container",
  "max_pages": 1,
  "session_id": "session-123"
}
```

**Field Configuration:**
- `name` (required): Field name
- `selector`: CSS selector
- `xpath`: XPath expression (alternative to selector)
- `regex`: Regular expression to extract from text
- `attribute`: HTML attribute to extract (e.g., 'href', 'src')
- `data_type`: `text`, `number`, `percentage`, `date`, `integer`
- `required`: Boolean
- `default_value`: Default if not found

#### 3. Export to Excel

```http
POST /api/v1/extract/to-excel
Content-Type: application/json

[
  {
    "Company Name": "Bharti Airtel",
    "Market Cap": 9250000,
    "Current Price": 1542.50
  }
]
```

**Response:** Excel file download

#### 4. List Available Presets

```http
GET /api/v1/extract/presets
```

---

## Frontend Usage

### 1. Data Extraction Tab

Navigate to the new **"Data Extraction"** tab in the sidebar:

```
http://localhost:3001
```

**Features:**
- Select preset template (Screener.in, etc.)
- Enter URL to extract
- View extraction history
- Export to Excel with one click

### 2. Web Scraping Tab

The **"Web Scraping"** tab now includes:

**Session Management:**
- History persists across page navigation
- Stored in `sessionStorage` per session
- Each job has unique ID and timestamp

**Collapsible Errors:**
- Errors are collapsed by default
- Click to expand and see full error details
- Better UX for long error messages

### 3. Hydration Error Fix

Fixed Next.js hydration mismatch errors:
- No more "Text content does not match" errors
- localStorage access deferred to `useEffect`
- Prevents server/client render mismatch

---

## Usage Examples

### Example 1: Extract Screener.in Financial Data

```bash
curl -X POST http://localhost:8000/api/v1/extract/preset/screener_in \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.screener.in/company/BHARTIARTL/consolidated/",
    "session_id": "my-session-123"
  }'
```

### Example 2: Export to Excel

```python
import requests

# Extract data
response = requests.post(
    'http://localhost:8000/api/v1/extract/preset/screener_in',
    json={
        'url': 'https://www.screener.in/company/BHARTIARTL/consolidated/'
    }
)

data = response.json()['data']

# Export to Excel
excel_response = requests.post(
    'http://localhost:8000/api/v1/extract/to-excel',
    json=data,
    params={'filename': 'bharti_airtel_data.xlsx'}
)

with open('bharti_airtel_data.xlsx', 'wb') as f:
    f.write(excel_response.content)
```

### Example 3: Custom Template

```python
template = {
    "name": "E-commerce Product Extraction",
    "description": "Extract product details",
    "url": "https://example.com/product/123",
    "fields": [
        {
            "name": "Product Name",
            "selector": "h1.product-title",
            "required": True
        },
        {
            "name": "Price",
            "selector": "span.price",
            "data_type": "number"
        },
        {
            "name": "Stock Status",
            "selector": "div.stock",
            "default_value": "Unknown"
        },
        {
            "name": "Image URL",
            "selector": "img.product-image",
            "attribute": "src"
        },
        {
            "name": "Rating",
            "selector": "div.rating",
            "regex": r"(\d+\.\d+) out of 5",
            "data_type": "number"
        }
    ],
    "wait_for_selector": "div.product-container",
    "max_pages": 1
}

response = requests.post(
    'http://localhost:8000/api/v1/extract/custom',
    json=template
)
```

---

## Testing Checklist

### Backend Tests

```bash
cd backend

# Test template extraction endpoint
python -c "
import asyncio
import sys
sys.path.append('.')
from app.services.template_extraction_service import template_extraction_service, get_screener_in_template

async def test():
    await template_extraction_service.initialize()
    template = get_screener_in_template()
    result = await template_extraction_service.extract_data(
        'https://www.screener.in/company/BHARTIARTL/consolidated/',
        template
    )
    print(f'Success: {result[\"success\"]}')
    print(f'Rows extracted: {result[\"row_count\"]}')
    if result['success']:
        print(result['data'][0])
    await template_extraction_service.close()

asyncio.run(test())
"
```

### Frontend Tests

1. **Hydration Error Check:**
   - Open browser console
   - Navigate to http://localhost:3001
   - Should see NO hydration errors

2. **Session Management:**
   - Go to "Web Scraping" tab
   - Add a URL and scrape
   - Switch to "Chat" tab and back
   - Scraping history should persist

3. **Collapsible Errors:**
   - Intentionally cause an error (invalid URL)
   - Error should be collapsed by default
   - Click to expand and see full error

4. **Template Extraction:**
   - Go to "Data Extraction" tab
   - Enter: `https://www.screener.in/company/BHARTIARTL/consolidated/`
   - Click "Extract Data"
   - Should see extracted financial data
   - Click "Export Excel"
   - Excel file should download

---

## Architecture

### Template Extraction Service

```
┌─────────────────────────────────────────────────┐
│         Template Extraction Service             │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────┐  ┌──────────────┐            │
│  │  Playwright  │  │ BeautifulSoup│            │
│  │   Browser    │  │  HTML Parser │            │
│  └──────────────┘  └──────────────┘            │
│                                                 │
│  ┌──────────────┐  ┌──────────────┐            │
│  │ Field        │  │ Data Type    │            │
│  │ Extraction   │  │ Conversion   │            │
│  └──────────────┘  └──────────────┘            │
│                                                 │
│  ┌──────────────┐  ┌──────────────┐            │
│  │ Excel        │  │ Template     │            │
│  │ Export       │  │ Management   │            │
│  └──────────────┘  └──────────────┘            │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Data Flow

```
User Input (URL + Template)
    ↓
Template Extraction Service
    ↓
Playwright Browser Launch
    ↓
Navigate to URL
    ↓
Wait for Selector (if specified)
    ↓
Extract Fields (CSS/XPath/Regex)
    ↓
Data Type Conversion
    ↓
Return Structured Data
    ↓
Export to Excel (optional)
```

---

## Troubleshooting

### Issue: Playwright Browser Not Found

**Error:**
```
playwright._impl._api_types.Error: Executable doesn't exist
```

**Solution:**
```bash
playwright install --with-deps chromium
```

### Issue: Hydration Error Persists

**Error:**
```
Error: Text content does not match server-rendered HTML
```

**Check:**
1. Ensure you're using the latest `ChatInterfaceEnhanced.tsx`
2. Clear browser cache and localStorage
3. Restart dev server

### Issue: Excel Export Fails

**Error:**
```
Module 'xlsxwriter' not found
```

**Solution:**
```bash
pip install xlsxwriter pandas
```

### Issue: Template Extraction Returns Empty Data

**Possible Causes:**
1. Incorrect CSS selectors
2. Website uses JavaScript to load content (use `wait_for_selector`)
3. Website blocks scrapers (check robots.txt)

**Debug:**
```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Security Considerations

### Robots.txt Compliance

The template extraction service should respect `robots.txt`:

```python
# Check robots.txt before scraping
from urllib.robotparser import RobotFileParser

rp = RobotFileParser()
rp.set_url("https://example.com/robots.txt")
rp.read()

if rp.can_fetch("*", "https://example.com/page"):
    # Proceed with scraping
    pass
```

### Rate Limiting

Implement rate limiting to avoid overwhelming target servers:

```python
import time

# Add delay between requests
time.sleep(1)  # 1 second delay
```

### User Agent

Always use a descriptive user agent:

```python
user_agent = 'MyBot/1.0 (+https://mysite.com/bot-info)'
```

---

## Performance Optimization

### 1. Caching

Cache extracted data to avoid repeated scraping:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def extract_cached(url: str):
    # ... extraction logic
    pass
```

### 2. Parallel Extraction

Extract from multiple URLs in parallel:

```python
import asyncio

urls = [...]
tasks = [extract_data(url, template) for url in urls]
results = await asyncio.gather(*tasks)
```

### 3. Headless Mode

Use headless browser for better performance:

```python
browser = await playwright.chromium.launch(headless=True)
```

---

## Future Enhancements

1. **More Preset Templates:**
   - LinkedIn profile extraction
   - Google search results
   - E-commerce product catalogs
   - Job board listings

2. **Scheduled Extraction:**
   - Set up recurring extraction jobs
   - Monitor for changes
   - Send notifications

3. **Data Validation:**
   - Validate extracted data against schemas
   - Flag anomalies
   - Retry on validation failure

4. **Advanced Export Formats:**
   - CSV
   - JSON
   - XML
   - Parquet (for analytics)

5. **Template Builder UI:**
   - Visual template builder
   - Point-and-click field selection
   - Live preview

---

## Support

For issues or questions:
1. Check `backend/app/services/template_extraction_service.py` for service implementation
2. Check `backend/app/api/routes/template_extraction_routes.py` for API routes
3. Check `frontend/src/components/TemplateExtractor.tsx` for frontend component
4. Review logs: `docker-compose logs -f backend`

---

**End of Template Extraction Guide**
