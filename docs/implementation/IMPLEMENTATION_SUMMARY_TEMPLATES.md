# Template Management Implementation Summary

## Current Status

### ✅ What's Working Now

1. **CSS Selector Extraction (Template-Based)**
   - Screener.in preset: ✅ Working (100% extraction rate)
   - Drenting.com preset: ✅ Added to dropdown
   - Uses Playwright (bypasses bot blocks)

2. **Smart Extraction (AI-Powered)**
   - Works on any website
   - Uses LLM to discover fields
   - ❌ Gets blocked on drenting.com (uses simple HTTP)

### 📋 What We Need To Implement

Based on your requests:

1. **"Save Template" Button in UI** - Create templates from successful extractions
2. **Auto-fallback to Playwright** - Retry with Playwright when HTTP is blocked
3. **Better Error Messages** - Guide users to alternatives

---

## How To Add Templates Currently (Manual Method)

###Step 1: Find CSS Selectors
```bash
docker-compose exec backend python inspect_new_website.py
# Edit the URL in the file first
```

### Step 2: Add Template Function
Edit `backend/app/services/template_extraction_service.py`:
```python
def get_your_site_template() -> ExtractionTemplate:
    return ExtractionTemplate(
        name="Your Site Name",
        description="What it extracts",
        wait_for_selector=".main-content",  # Element to wait for
        fields=[
            ExtractionField(name="Title", selector="h1", required=True),
            ExtractionField(name="Price", selector=".price", data_type="text"),
            # ... more fields
        ]
    )
```

### Step 3: Register in Dropdown
Edit `backend/app/api/routes/template_extraction_routes.py`:
```python
presets = [
    {
        "name": "your_site",
        "display_name": "Your Site Name",
        "description": "Extracts data from your site",
        "fields": ["Title", "Price", ...]
    },
    # ... existing presets
]
```

### Step 4: Restart
```bash
docker-compose restart backend
```

Template now appears in dropdown! ✅

---

## How Templates SHOULD Work (With New Features)

### User-Friendly Flow

```
User goes to any extraction mode
    ↓
Tries to extract from a site
    ↓
TWO SCENARIOS:

┌─────────────────────────────────────────────────────────────┐
│ SCENARIO A: Extraction Succeeds                            │
├─────────────────────────────────────────────────────────────┤
│ ✓ Success! Data extracted                                  │
│                                                             │
│ [💾 Save as CSS Template] ← NEW BUTTON                     │
│                                                             │
│ User clicks → Modal opens:                                 │
│   Name: [My Template_____]                                 │
│   Description: [____________]                              │
│   [Save]                                                    │
│                                                             │
│ Template saved to database                                 │
│ Appears in CSS Selector dropdown automatically!            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ SCENARIO B: Extraction Fails (Bot Blocked)                 │
├─────────────────────────────────────────────────────────────┤
│ ❌ Website blocking detected (403 Error)                    │
│                                                             │
│ AUTOMATIC RETRY:                                           │
│   ⏳ Retrying with Playwright...                           │
│                                                             │
│ IF SUCCEEDS:                                               │
│   ✓ Success! (Used advanced browser method)               │
│   [💾 Save as CSS Template]                                │
│                                                             │
│ IF STILL FAILS:                                            │
│   ❌ Unable to access website                              │
│                                                             │
│   💡 Try these instead:                                    │
│   • [Switch to Smart Extraction] ← Button                 │
│   • [Switch to Template Mapper] ← Button                  │
│   • Site may require login                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Technical Implementation Plan

### Feature 1: Auto-Fallback to Playwright

**Problem**: drenting.com blocks simple HTTP requests (403 error)

**Solution**: Automatically retry with Playwright

```python
# backend/app/services/scraper_service.py

async def scrape_with_fallback(url: str):
    # Stage 1: Try fast HTTP first
    try:
        result = await scrape_with_httpx(url)
        return {'html': result, 'method': 'httpx', 'fast': True}
    except HTTPStatusError as e:
        if e.status_code == 403:
            logger.info("HTTP blocked (403), retrying with Playwright...")
        else:
            raise

    # Stage 2: Fallback to Playwright (slower but works)
    result = await scrape_with_playwright(url)
    return {'html': result, 'method': 'playwright', 'fast': False}
```

### Feature 2: Save Template Button

**Database**:
```sql
CREATE TABLE saved_templates (
    id UUID PRIMARY KEY,
    name VARCHAR(255) UNIQUE,
    display_name VARCHAR(255),
    description TEXT,
    url_pattern VARCHAR(512),
    fields JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Backend API**:
```python
@router.post("/save-template")
async def save_template(request: SaveTemplateRequest):
    # Validate unique name
    # Save to database
    # Return template_id
    pass

@router.get("/templates")  # Replaces /presets
async def list_all_templates():
    # Get built-in presets
    presets = [screener_in, drenting, ...]

    # Get user-saved from database
    saved = db.query(SavedTemplate).all()

    # Merge and return
    return presets + saved
```

**Frontend**:
```typescript
// Add to SmartExtractor.tsx, TemplateExtractor.tsx, SmartTemplateMapper.tsx

{extractionSuccess && (
  <div className="success-panel">
    ✓ Extraction successful!
    <button onClick={handleSaveTemplate}>
      💾 Save as CSS Template
    </button>
  </div>
)}

const handleSaveTemplate = () => {
  setShowSaveModal(true);
};

// Modal component
{showSaveModal && (
  <SaveTemplateModal
    url={url}
    fields={extractedFields}
    onSave={async (name, desc) => {
      await axios.post('/api/v1/extract/save-template', {...});
      alert('Template saved!');
    }}
    onCancel={() => setShowSaveModal(false)}
  />
)}
```

### Feature 3: Smart Error Messages

```python
# backend/app/api/routes/template_extraction_routes.py

except HTTPStatusError as e:
    if e.status_code == 403:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Website blocking detected",
                "message": "The website is blocking automated access",
                "suggestions": [
                    "Automatically retrying with advanced browser method...",
                    "Try Smart Extraction (AI-powered)",
                    "Try Template Mapper with custom columns"
                ],
                "retry_method": "playwright",  # Frontend can auto-retry
                "alternative_modes": ["smart", "mapper"]
            }
        )
```

```typescript
// frontend error handling

catch (error) {
  if (error.response?.status === 403) {
    const { suggestions, alternative_modes } = error.response.data;

    setError({
      title: "Website Blocking Detected",
      message: error.response.data.message,
      suggestions: suggestions,
      actions: [
        {
          label: "Try Smart Extraction",
          onClick: () => switchToMode('smart')
        },
        {
          label: "Try Template Mapper",
          onClick: () => switchToMode('mapper')
        }
      ]
    });
  }
}
```

---

## Implementation Timeline

### Quick Wins (Today)

1. **Auto Playwright Fallback** - 1-2 hours
   - Modify `scraper_service.py`
   - Add fallback logic
   - Test with drenting.com

2. **Better Error Messages** - 1 hour
   - Update error responses
   - Add suggestions array
   - Frontend error display

### Medium-Term (This Week)

3. **Save Template Button** - 4-6 hours
   - Database migration
   - Backend API endpoints
   - Frontend modal component
   - Dynamic template loading

### Testing Plan

```bash
# Test Auto Fallback
curl http://localhost:8000/api/v1/smart-extract \
  -d '{"url": "https://www.drenting.com/"}'
# Should automatically use Playwright

# Test drenting.com with CSS template
curl http://localhost:8000/api/v1/extract/preset/drenting \
  -d '{"url": "https://www.drenting.com/"}'
# Should work now!

# Test Save Template
# 1. Use Smart Extraction successfully
# 2. Click "Save Template" button
# 3. Enter name and description
# 4. Check dropdown in CSS Selector mode
# 5. Template should appear!
```

---

## Summary

**Current State**:
- CSS Selector mode: Works great (Screener.in 100%)
- Drenting added but needs testing
- Smart Extraction blocked by drenting.com

**After Implementation**:
- ✅ Auto-fallback handles bot blocking
- ✅ Users can save successful extractions as templates
- ✅ Clear error messages guide users
- ✅ No developer needed to add templates

**Want me to implement these features now?** I recommend:
1. Start with auto-fallback (solves drenting.com immediately)
2. Then add better error messages
3. Finally, "Save Template" button (bigger feature)

Let me know and I'll get started! 🚀
