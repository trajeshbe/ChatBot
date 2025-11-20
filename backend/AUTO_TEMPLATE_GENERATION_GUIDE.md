# Auto-Generate CSS Selector Templates from Smart Extraction

This guide shows you how to automatically create reusable CSS selector templates from successful Smart Extraction results.

## Overview

**Problem:** You use Smart Extraction on a website and it works great, but you want to reuse the same template later for speed.

**Solution:** Convert the Smart Extraction template to a CSS selector preset that loads instantly!

---

## Method 1: Using Smart Extraction Results

### Step 1: Test with Smart Extraction First

1. Go to **Smart Extraction** mode
2. Enter URL: `https://example.com/product/123`
3. Instructions: `"Extract product name, price, description, stock status"`
4. Click **Auto-Generate Template**
5. Click **Extract Data**

### Step 2: Inspect the Generated Template

The Smart Extraction creates a template behind the scenes. You can see it in the API response or logs.

### Step 3: Convert to CSS Preset

Once you know it works, create a permanent preset:

```python
# In backend/app/services/template_extraction_service.py

def get_example_product_template() -> ExtractionTemplate:
    """
    Template auto-generated from Smart Extraction
    Original URL: https://example.com/product/123
    Generated: 2025-11-19
    """
    return ExtractionTemplate(
        name="Example.com Products",
        description="Extract product data from Example.com (auto-generated)",
        wait_for_selector="h1.product-title",
        fields=[
            # Copy field definitions from Smart Extraction results
            ExtractionField(
                name="Product Name",
                selector="h1.product-title",
                required=True
            ),
            ExtractionField(
                name="Price",
                selector=".price-value",
                data_type="text"
            ),
            # ... etc
        ]
    )

# Register it
PRESET_TEMPLATES["example_products"] = {
    "name": "example_products",
    "display_name": "Example.com Products",
    "description": "Auto-generated from Smart Extraction",
    "fields": ["Product Name", "Price", "Description", "Stock"],
    "template_func": get_example_product_template
}
```

---

## Method 2: Automatic Template Discovery (Feature Idea)

### API Endpoint: `/api/v1/extract/discover`

This would be a new endpoint that:

1. Takes a URL
2. Automatically inspects it
3. Suggests common patterns (product, article, listing, etc.)
4. Returns a ready-to-use template

```bash
# Example API call
curl -X POST http://localhost:8000/api/v1/extract/discover \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/product/123",
    "template_type": "auto"
  }' | jq

# Response:
{
  "success": true,
  "detected_type": "ecommerce_product",
  "confidence": 0.92,
  "suggested_fields": [
    {"name": "Product Name", "selector": "h1.product-title"},
    {"name": "Price", "selector": ".price"},
    {"name": "Description", "selector": ".product-description"}
  ],
  "template_name": "auto_example_com_products",
  "can_save_as_preset": true
}
```

### Workflow:

```
User enters URL
    ↓
App discovers template automatically
    ↓
Shows preview: "Found 8 fields"
    ↓
User reviews and confirms
    ↓
Template saved and added to dropdown!
```

---

## Method 3: Hybrid Approach (Best of Both Worlds)

### Smart Extraction + Template Learning

1. **First Time (Slow but Smart):**
   - Use Smart Extraction with LLM
   - AI figures out what to extract
   - Takes 15-30 seconds

2. **App Learns:**
   - App saves the successful selectors
   - Creates a cached template
   - Stores in database

3. **Next Time (Fast):**
   - App recognizes the domain
   - Offers: "Use saved template for example.com?"
   - Extraction takes 2-3 seconds

### Implementation Idea:

```python
# New table: learned_templates
CREATE TABLE learned_templates (
    id UUID PRIMARY KEY,
    domain VARCHAR(255),              -- "example.com"
    template_name VARCHAR(255),        -- "Example Products"
    url_pattern VARCHAR(512),          -- "example.com/product/*"
    fields JSONB,                      -- Saved field definitions
    success_count INTEGER DEFAULT 0,   -- How many times it worked
    created_at TIMESTAMP,
    last_used TIMESTAMP
);

# When user extracts from a URL:
1. Check if domain has learned template
2. If yes: "Use fast template or Smart Extraction?"
3. If no: Use Smart Extraction and save results
```

---

## Method 4: Browser DevTools Inspector

### Manual Discovery Using Browser Tools

1. **Open the target page in browser**
2. **Right-click → Inspect** (F12)
3. **Console tab:**

```javascript
// Find all headings
document.querySelectorAll('h1, h2, h3')

// Find elements with prices
document.querySelectorAll('[class*="price"]')

// Find all links
document.querySelectorAll('a[href*="product"]')

// Test a specific selector
document.querySelector('.product-title').textContent

// Get all elements with data attributes
document.querySelectorAll('[data-product-id]')
```

4. **Copy selectors that work**
5. **Add to template** as shown in Method 1

---

## Comparison: When to Use Each Method

| Method | Speed | Flexibility | Best For |
|--------|-------|------------|----------|
| **CSS Selector Preset** | ⚡ Fast (2-3s) | ❌ Fixed fields | Regular scraping, known sites |
| **Smart Extraction** | 🐌 Slow (15-30s) | ✅ Any website | New sites, exploratory |
| **Template Mapper** | 🐌 Slow (15-30s) | ✅ Custom columns | When you have Excel template |
| **Auto-Discovery** | ⚡ Fast (5-10s) | ✅ Auto-learns | Hybrid approach |

---

## Proposed Feature: "Save This Template" Button

### UI Flow:

```
Smart Extraction succeeds
    ↓
Show success message with:
    ↓
[✓ Data Extracted Successfully]
    ↓
[💾 Save as Preset Template] ← NEW BUTTON
    ↓
User clicks button
    ↓
Prompt: "Template name: _______"
    ↓
Template saved to database
    ↓
Next time: Appears in CSS Selector dropdown!
```

### API Endpoint:

```python
@router.post("/api/v1/extract/save-template")
async def save_smart_template(
    template_name: str,
    url_pattern: str,
    fields: List[ExtractionField],
    db: Session = Depends(get_db)
):
    """
    Save a Smart Extraction template as a reusable preset
    """
    # Save to database
    # Add to PRESET_TEMPLATES dynamically
    # Return success
```

---

## Current Workflow vs. Proposed Workflow

### ❌ Current (Manual):

1. Smart Extraction on URL A → Success
2. Smart Extraction on URL B (same site) → Slow again
3. Smart Extraction on URL C (same site) → Still slow
4. Manually create CSS template in code
5. Rebuild backend
6. Now fast, but takes developer time

### ✅ Proposed (Automatic):

1. Smart Extraction on URL A → Success → Click "Save Template"
2. Extract from URL B (same site) → **Auto-suggests saved template** → Fast!
3. Extract from URL C (same site) → Uses saved template → Fast!
4. Template automatically available in dropdown
5. No developer intervention needed

---

## Implementation Checklist

If you want this feature, here's what needs to be added:

### Backend:
- [ ] Database table for `learned_templates`
- [ ] API endpoint: `POST /api/v1/extract/save-template`
- [ ] API endpoint: `GET /api/v1/extract/learned-templates`
- [ ] Logic to suggest templates by domain
- [ ] Dynamic template loading from database

### Frontend:
- [ ] "Save as Template" button in Smart Extraction results
- [ ] Modal to name the template
- [ ] UI to show "Suggested template for this domain?"
- [ ] Dropdown to switch between saved templates

### Nice-to-Have:
- [ ] Template versioning (v1, v2, etc.)
- [ ] Template sharing between users
- [ ] Template marketplace/community templates
- [ ] Auto-update templates if selectors change

---

## Quick Win: Export Smart Extraction Config

**Available NOW without code changes:**

After Smart Extraction succeeds:

1. Check browser Network tab (F12 → Network)
2. Find the API call to `/extract/smart` or similar
3. Look at the response
4. Copy the field definitions
5. Manually create a preset using the guide

This gives you the best of both worlds:
- Use Smart Extraction to **discover** selectors
- Convert to CSS preset for **speed**

---

## Summary

**You already have auto-discovery via Smart Extraction!**

**To make it faster for repeat use:**
- Option 1: Manually convert successful Smart Extraction → CSS Preset
- Option 2: Request the "Save Template" feature (moderate dev work)
- Option 3: Use Smart Extraction every time (slow but always works)

**Best approach for now:**
1. Use Smart Extraction to test new sites
2. If you'll scrape the site regularly, convert to CSS preset
3. For one-off extractions, stick with Smart Extraction

---

Would you like me to implement the "Save Template" feature? It would make this workflow automatic! 🚀
