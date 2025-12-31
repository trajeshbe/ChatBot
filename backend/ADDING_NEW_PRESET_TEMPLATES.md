# How to Add New Preset Templates for CSS Selector-Based Extraction

This guide shows you how to add preset templates for new websites.

## Quick Overview

1. **Inspect the website** to find CSS selectors
2. **Add template function** to `template_extraction_service.py`
3. **Register the template** in the presets list
4. **Restart backend** and test

---

## Step 1: Inspect the Target Website

Use the inspection script to find the right CSS selectors:

```bash
# Edit inspect_new_website.py with your target URL
docker-compose exec backend python inspect_new_website.py
```

### Example: Inspecting a product page

```python
url = "https://example.com/product/12345"

selectors_to_check = [
    "h1.product-title",        # Product name
    "span.price",              # Price
    "div.description",         # Description
    ".stock-status",           # Stock info
    "#reviews-count",          # Reviews
]
```

**Look for:**
- Unique IDs: `#product-info`, `#price-section`
- Stable classes: `.product-name`, `.price-value`
- Structural selectors: `div.details > span.price`
- Avoid: Dynamic classes with hashes, randomly generated IDs

---

## Step 2: Add Template Function

Add a new function in `backend/app/services/template_extraction_service.py`:

```python
def get_example_product_template() -> ExtractionTemplate:
    """Template for extracting product data from Example.com"""
    return ExtractionTemplate(
        name="Example Product Data",
        description="Extract product details from Example.com product pages",

        # Wait for this element to ensure page is loaded
        wait_for_selector="h1.product-title",

        fields=[
            ExtractionField(
                name="Product Name",
                selector="h1.product-title",
                required=True  # Extraction fails if this is missing
            ),
            ExtractionField(
                name="Price",
                selector="span.price",
                data_type="text"  # Keep as text to preserve currency symbols
            ),
            ExtractionField(
                name="Description",
                selector="div.description",
                data_type="text"
            ),
            ExtractionField(
                name="Stock Status",
                selector=".stock-status",
                data_type="text"
            ),
            ExtractionField(
                name="Rating",
                selector=".rating-value",
                data_type="text"
            ),
            ExtractionField(
                name="Reviews Count",
                selector="#reviews-count",
                data_type="text"
            ),
            ExtractionField(
                name="Category",
                selector=".breadcrumb li:last-child",
                data_type="text"
            ),
            ExtractionField(
                name="SKU",
                selector="span.sku",
                data_type="text"
            ),
            # Add source info
            ExtractionField(
                name="Source / Notes",
                selector=None,  # No selector = use default value
                default_value="Scraped from Example.com using CSS selectors"
            ),
        ]
    )
```

---

## Step 3: Register the Template

Find the `PRESET_TEMPLATES` dictionary in `template_extraction_service.py` and add your template:

```python
# Around line 630-650 in template_extraction_service.py
PRESET_TEMPLATES = {
    "screener_in": {
        "name": "screener_in",
        "display_name": "Screener.in Company Data",
        "description": "Extract financial metrics from Screener.in",
        "fields": ["Company Name", "Market Cap", "Stock P/E", "ROE", "ROCE"],
        "template_func": get_screener_in_template
    },

    # ADD YOUR NEW TEMPLATE HERE
    "example_product": {
        "name": "example_product",
        "display_name": "Example.com Products",
        "description": "Extract product data from Example.com",
        "fields": ["Product Name", "Price", "Description", "Stock Status", "Rating"],
        "template_func": get_example_product_template
    },
}
```

---

## Step 4: Restart and Test

```bash
# Rebuild backend
docker-compose build backend

# Restart backend
docker-compose restart backend

# Test the new template
docker-compose exec backend python -c "
from app.services.template_extraction_service import PRESET_TEMPLATES
print('Available templates:', list(PRESET_TEMPLATES.keys()))
"
```

### Test extraction:

```bash
curl -X POST http://localhost:8000/api/v1/extract/preset/example_product \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/product/12345",
    "session_id": "test"
  }' | jq
```

---

## CSS Selector Cheat Sheet

### Basic Selectors
```css
h1                    /* All h1 elements */
.classname            /* Elements with class="classname" */
#id                   /* Element with id="id" */
div.product           /* Div with class="product" */
```

### Combinators
```css
div > span            /* Direct child: span inside div */
div span              /* Descendant: span anywhere inside div */
li:nth-child(1)       /* First li element */
li:nth-child(3)       /* Third li element */
li:last-child         /* Last li element */
```

### Attribute Selectors
```css
[data-price]          /* Elements with data-price attribute */
a[href*="product"]    /* Links containing "product" in href */
input[type="text"]    /* Text inputs */
```

### Advanced
```css
li:has-text('Price')               /* Li containing "Price" text */
div.card:has(> span.price)        /* Div.card that has a span.price child */
ul.stats > li:nth-child(2) span   /* Complex nested selector */
```

---

## Example: Real-World Template (Amazon-style)

```python
def get_amazon_style_template() -> ExtractionTemplate:
    """Template for Amazon-style product pages"""
    return ExtractionTemplate(
        name="Amazon-Style Products",
        description="Extract product data from Amazon-like pages",
        wait_for_selector="#productTitle",
        fields=[
            ExtractionField(
                name="Product Title",
                selector="#productTitle",
                required=True
            ),
            ExtractionField(
                name="Price",
                selector=".a-price .a-offscreen",
                data_type="text"
            ),
            ExtractionField(
                name="Rating",
                selector="#acrPopover .a-icon-alt",
                data_type="text"
            ),
            ExtractionField(
                name="Review Count",
                selector="#acrCustomerReviewText",
                data_type="text"
            ),
            ExtractionField(
                name="Availability",
                selector="#availability span",
                data_type="text"
            ),
            ExtractionField(
                name="Brand",
                selector="#bylineInfo",
                data_type="text"
            ),
            ExtractionField(
                name="Product Description",
                selector="#feature-bullets",
                data_type="text"
            ),
        ]
    )
```

---

## Testing Tips

### 1. Test with Multiple URLs
```bash
# Test with different products from same site
python test_extraction.py --url https://example.com/product/1
python test_extraction.py --url https://example.com/product/2
python test_extraction.py --url https://example.com/product/3
```

### 2. Handle Missing Fields
- Use `required=False` for optional fields
- Use `default_value` for fallback values
- Test with pages that might be missing some data

### 3. Verify Data Types
```python
data_type="text"       # Default, preserves all formatting
data_type="number"     # Extracts numeric values (use with caution)
data_type="percentage" # For percentage values
```

### 4. Check Extraction Rate
Aim for 80%+ extraction success rate:
```python
fields_extracted = sum(1 for v in data.values() if v)
total_fields = len(data)
success_rate = (fields_extracted / total_fields) * 100
print(f"Success rate: {success_rate:.1f}%")
```

---

## Common Issues & Solutions

### Issue: Timeout waiting for selector
**Solution:** Check if the `wait_for_selector` exists on the page
```python
# Use a selector that appears early and reliably
wait_for_selector="h1"  # Usually safe
```

### Issue: Extracting wrong data
**Solution:** Be more specific with selectors
```python
# Too broad
selector="span"  # Might match many elements

# Better
selector="div.price > span.value"  # More specific
```

### Issue: Dynamic content not loading
**Solution:** Wait for network idle or specific element
```python
wait_for_selector="div.loaded-content"  # Element that appears after JS loads
```

### Issue: Getting HTML instead of text
**Solution:** Target specific text nodes or use `.number` class
```python
# Bad: Gets entire HTML block
selector="div.price"

# Good: Gets just the number
selector="div.price span.number"
```

---

## File Locations Reference

```
backend/
├── app/
│   └── services/
│       └── template_extraction_service.py  # Add templates here
├── inspect_new_website.py                  # Use this to find selectors
└── test_fixed_template.py                  # Test template (copy & modify)
```

---

## Complete Workflow Example

### 1. Inspect Moneycontrol.com stock page
```bash
# Edit inspect_new_website.py
url = "https://www.moneycontrol.com/india/stockpricequote/..."

# Run inspection
docker-compose exec backend python inspect_new_website.py
```

### 2. Create template function
```python
def get_moneycontrol_template() -> ExtractionTemplate:
    return ExtractionTemplate(
        name="Moneycontrol Stock Data",
        description="Extract stock data from Moneycontrol",
        wait_for_selector="#nselprice",
        fields=[
            ExtractionField(name="Company", selector="h1.pcstname", required=True),
            ExtractionField(name="Price", selector="#nselprice", data_type="text"),
            ExtractionField(name="Change", selector=".nseprcchange", data_type="text"),
            # ... more fields
        ]
    )
```

### 3. Register it
```python
PRESET_TEMPLATES = {
    "moneycontrol": {
        "name": "moneycontrol",
        "display_name": "Moneycontrol Stocks",
        "description": "Extract stock data from Moneycontrol",
        "fields": ["Company", "Price", "Change", "Volume"],
        "template_func": get_moneycontrol_template
    },
}
```

### 4. Test it
```bash
# Rebuild
docker-compose build backend
docker-compose restart backend

# Test
curl -X POST http://localhost:8000/api/v1/extract/preset/moneycontrol \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.moneycontrol.com/...", "session_id": "test"}' \
  | jq
```

### 5. Use in UI
The new template will automatically appear in the dropdown at http://localhost:3001 in the "CSS Selector Based" extraction mode!

---

## Need Help?

- Check `backend/inspect_screener.py` for a working inspection example
- Check `get_screener_in_template()` for a working template example
- Run `docker-compose logs backend` to see errors
- Test selectors in browser DevTools first (F12 → Console → `document.querySelector("selector")`)

---

**Happy Scraping!** 🎉
