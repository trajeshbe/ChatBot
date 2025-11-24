# CSS Selector Template Fix - 2025-11-19

## ✅ ISSUE FIXED - CSS Selector Templates Now Properly Filtered

### Summary
Fixed CSS Selector extraction to only show and use templates with valid CSS selectors, preventing errors when trying to use Smart Extraction templates (which don't have CSS selectors) in CSS Selector mode.

**Root Cause**: Templates created via Smart Extraction don't have CSS selectors (they use AI), but were appearing in the CSS Selector dropdown and causing "Preset template 'X' not found" errors.

**Solution**: 
1. Backend now validates templates have CSS selectors before using them
2. Backend adds `has_css_selectors` flag to template API responses
3. Frontend filters dropdown to only show templates with CSS selectors
4. Backend provides helpful error message when invalid template is used

**Status**: ✅ COMPLETED AND TESTED

---

## Problem Analysis

### Database Investigation
```sql
-- Templates in database:
SELECT name, display_name FROM saved_css_templates WHERE is_active = TRUE;

-- Results showed:
drenting_cars  | Has CSS selectors (.card h3, .card span)
my_test_site   | Has CSS selectors (h1.title, p.desc)
sampleecom     | NO CSS selectors (selector: "")  ← Created via Smart Extraction
book1          | NO CSS selectors (selector: "")  ← Created via Smart Extraction
bookstore      | NO CSS selectors (selector: "")  ← Created via Smart Extraction
```

### Root Causes
1. **Backend**: `/preset/{preset_name}` endpoint only handled hardcoded presets (screener_in, drenting)
   - User-saved templates were not loadable at all
   - Returned "Preset template 'X' not found" for all user-saved templates

2. **Frontend**: Showed ALL templates in dropdown
   - Including templates without CSS selectors (created via Smart Extraction)
   - No way to distinguish CSS Selector templates from Smart Extraction templates

---

## Files Modified

### Backend: `/backend/app/api/routes/template_extraction_routes.py`

#### 1. Updated `/preset/{preset_name}` endpoint (lines 336-393)
**Before**: Only handled hardcoded presets (screener_in, drenting)
```python
if preset_name == "screener_in":
    template = get_screener_in_template()
else:
    raise HTTPException(status_code=404, detail=f"Preset template '{preset_name}' not found")
```

**After**: Loads user-saved templates from database + validates CSS selectors
```python
if preset_name == "screener_in":
    template = get_screener_in_template()
elif preset_name == "drenting":
    template = get_drenting_template()
else:
    # Try to load from database (user-saved templates)
    query = text("""
        SELECT name, display_name, url_pattern, wait_for_selector, fields
        FROM saved_css_templates
        WHERE name = :template_name AND is_active = TRUE
    """)
    
    result = await db.execute(query, {"template_name": preset_name})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail=f"Preset template '{preset_name}' not found")
    
    # Validate that template has at least one non-empty CSS selector
    fields_data = row[4]  # fields column (JSONB)
    has_valid_selector = any(
        field.get("selector") and field.get("selector").strip()
        for field in fields_data
    )
    
    if not has_valid_selector:
        raise HTTPException(
            status_code=422,
            detail=f"Template '{preset_name}' has no CSS selectors defined. This template was created via Smart Extraction and cannot be used with CSS Selector mode. Please use Smart Extraction or Template Mapper instead."
        )
    
    # Convert database template to ExtractionTemplate format
    from app.services.template_extraction_service import ExtractionTemplate, FieldDefinition
    
    template_fields = []
    for field_data in fields_data:
        field_def = FieldDefinition(
            name=field_data["name"],
            selector=field_data.get("selector", ""),
            data_type=field_data.get("data_type", "text"),
            required=field_data.get("required", False),
            regex=field_data.get("regex"),
            xpath=field_data.get("xpath"),
            attribute=field_data.get("attribute"),
            default_value=field_data.get("default_value")
        )
        template_fields.append(field_def)
    
    template = ExtractionTemplate(
        name=row[0],
        display_name=row[1],
        url_pattern=row[2],
        wait_for_selector=row[3],
        fields=template_fields
    )
```

#### 2. Updated `/saved-templates` endpoint (lines 1290-1343)
Added `has_css_selectors` flag to both builtin and user-saved templates:

**Builtin templates** (lines 1290-1309):
```python
builtin_presets = [
    {
        "name": "screener_in",
        "display_name": "Screener.in Company Data",
        "description": "Extract financial metrics from Screener.in company pages",
        "fields": [...],
        "source": "builtin",
        "is_active": True,
        "has_css_selectors": True  # ← ADDED
    },
    {
        "name": "drenting",
        "display_name": "Drenting.com Car Listings",
        "description": "Extract car rental/leasing offers from Drenting.com",
        "fields": [...],
        "source": "builtin",
        "is_active": True,
        "has_css_selectors": True  # ← ADDED
    }
]
```

**User-saved templates** (lines 1321-1344):
```python
saved_templates = []
for row in rows:
    fields_json = row[5]  # fields column
    field_names = [f["name"] for f in fields_json]
    
    # Check if template has at least one non-empty CSS selector
    has_css_selectors = any(
        f.get("selector") and f.get("selector").strip()
        for f in fields_json
    )
    
    saved_templates.append({
        "id": str(row[0]),
        "name": row[1],
        "display_name": row[2],
        "description": row[3],
        "url_pattern": row[4],
        "fields": field_names,
        "use_count": row[6],
        "created_at": row[7].isoformat(),
        "source": "user_saved",
        "is_active": row[8],
        "has_css_selectors": has_css_selectors  # ← ADDED
    })
```

### Frontend: `/frontend/src/components/TemplateExtractor.tsx`

#### Updated template loading (lines 141-165)
Added filtering to only show templates with CSS selectors:

**Before**: Showed all templates
```typescript
useEffect(() => {
  const loadPresets = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/v1/extract/saved-templates`)
      setAvailablePresets(response.data.templates || [])
    } catch (error) {
      console.error('Error loading presets:', error)
    }
  }
  loadPresets()
}, [])
```

**After**: Filters to only show templates with CSS selectors
```typescript
useEffect(() => {
  const loadPresets = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/v1/extract/saved-templates`)
      const allTemplates = response.data.templates || []
      
      // Filter to only show templates with CSS selectors (for CSS Selector extraction mode)
      const cssTemplates = allTemplates.filter((t: any) =>
        t.has_css_selectors !== false  // Keep builtin templates and user templates with selectors
      )
      
      setAvailablePresets(cssTemplates)
      
      // Log filtered templates for debugging
      const filteredOut = allTemplates.length - cssTemplates.length
      if (filteredOut > 0) {
        console.log(`Filtered out ${filteredOut} templates without CSS selectors (created via Smart Extraction)`)
      }
    } catch (error) {
      console.error('Error loading presets:', error)
    }
  }
  loadPresets()
}, [])
```

---

## Test Results

### ✅ Backend API Tests

**1. List all templates with CSS selector flag**:
```bash
curl -s http://localhost:8000/api/v1/extract/saved-templates | jq '.templates[] | {name: .name, has_css_selectors: .has_css_selectors}'
```

**Result**:
```json
✅ With CSS Selectors (usable in CSS Selector mode):
{"name": "screener_in", "has_css_selectors": true}
{"name": "drenting", "has_css_selectors": true}
{"name": "my_test_site", "has_css_selectors": true}
{"name": "drenting_cars", "has_css_selectors": true}

❌ Without CSS Selectors (created via Smart Extraction):
{"name": "book1", "has_css_selectors": false}
{"name": "bookstore", "has_css_selectors": false}
{"name": "book", "has_css_selectors": false}
{"name": "tcs", "has_css_selectors": false}
{"name": "sampleecom", "has_css_selectors": false}
```

**2. Test template WITH CSS selectors (drenting_cars)**:
```bash
curl -X POST http://localhost:8000/api/v1/extract/preset/drenting_cars \
  -H "Content-Type: application/json" \
  -d '{"url": "https://drenting.com/", "session_id": "test"}'
```

**Result**: ✅ Template loads successfully (no "template not found" error)

**3. Test template WITHOUT CSS selectors (sampleecom)**:
```bash
curl -X POST http://localhost:8000/api/v1/extract/preset/sampleecom \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/", "session_id": "test"}'
```

**Result**: ✅ Returns helpful error:
```json
{
  "detail": "Template 'sampleecom' has no CSS selectors defined. This template was created via Smart Extraction and cannot be used with CSS Selector mode. Please use Smart Extraction or Template Mapper instead."
}
```

### ✅ Frontend Tests

**Before Fix**:
- CSS Selector dropdown showed ALL 9 templates
- Clicking templates without CSS selectors → "Preset template 'X' not found" error

**After Fix**:
- CSS Selector dropdown shows only 4 templates WITH CSS selectors:
  - ✅ screener_in (builtin)
  - ✅ drenting (builtin)
  - ✅ my_test_site (user-saved)
  - ✅ drenting_cars (user-saved)
- Templates without CSS selectors are hidden from dropdown
- Browser console shows: "Filtered out 5 templates without CSS selectors (created via Smart Extraction)"

---

## Technical Details

### How Template Types Work

#### CSS Selector Templates
- **Created via**: CSS Selector tab or manually defined
- **Extraction method**: Playwright/HTTP + CSS selectors (e.g., `.card h3`)
- **Requirements**: Must have at least one non-empty CSS selector
- **Usage**: Fast, reliable for structured pages with consistent HTML
- **Examples**: screener_in, drenting, my_test_site, drenting_cars

#### Smart Extraction Templates
- **Created via**: Smart Extraction tab (AI-powered)
- **Extraction method**: AI analyzes page content and extracts data
- **Requirements**: No CSS selectors needed
- **Usage**: Flexible, works on any page structure
- **Examples**: bookstore, sampleecom, book1, tcs, book
- **Limitation**: Cannot be used in CSS Selector mode

### Template Compatibility Matrix

| Template Name | Has CSS Selectors | Usable in CSS Selector Mode | Created Via |
|--------------|-------------------|----------------------------|-------------|
| screener_in | ✅ Yes | ✅ Yes | Builtin |
| drenting | ✅ Yes | ✅ Yes | Builtin |
| my_test_site | ✅ Yes | ✅ Yes | CSS Selector tab |
| drenting_cars | ✅ Yes | ✅ Yes | CSS Selector tab |
| book1 | ❌ No | ❌ No | Smart Extraction |
| bookstore | ❌ No | ❌ No | Smart Extraction |
| book | ❌ No | ❌ No | Smart Extraction |
| tcs | ❌ No | ❌ No | Smart Extraction |
| sampleecom | ❌ No | ❌ No | Smart Extraction |

---

## User Experience

### Before Fix
1. User creates template via Smart Extraction (no CSS selectors)
2. Template appears in CSS Selector dropdown
3. User selects template → Error: "Preset template 'X' not found"
4. Confusing experience

### After Fix
1. User creates template via Smart Extraction (no CSS selectors)
2. Template does NOT appear in CSS Selector dropdown (automatically filtered out)
3. Template still available in Smart Extraction mode for reuse
4. If someone tries to use it via API directly, they get helpful error message explaining why

---

## Next Steps (Optional)

1. **Add template type indicator**: Show badge/icon in dropdown indicating template source (builtin/user-saved)
2. **Cross-tab template usage**: Allow Smart Extraction templates to be loaded in Smart Extraction tab
3. **Template conversion**: Add tool to convert Smart Extraction templates to CSS Selector templates by generating selectors
4. **Template management**: Add UI to view/edit/delete all templates regardless of type

---

## Files Changed Summary

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `template_extraction_routes.py` | 336-393 | Load user-saved templates from DB + validate CSS selectors |
| `template_extraction_routes.py` | 1290-1343 | Add `has_css_selectors` flag to template responses |
| `TemplateExtractor.tsx` | 141-165 | Filter dropdown to only show templates with CSS selectors |

---

**Date**: 2025-11-19
**Status**: ✅ PRODUCTION READY
**Tested**: Backend API + Frontend UI + Database
**Result**: CSS Selector mode now only shows and uses compatible templates

---

## Related Documentation

- Templates created via **Smart Extraction** should be used in Smart Extraction mode
- Templates created via **CSS Selector** or with proper selectors can be used in CSS Selector mode
- All templates remain in database and can be reused in their appropriate extraction mode
