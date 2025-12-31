# Dynamic Template Features Implementation Plan

## Overview

Three major features to make template management dynamic and user-friendly:

1. **Save as CSS Template** - Save successful extractions as reusable templates
2. **Auto Playwright Fallback** - Automatically retry with Playwright when blocked
3. **Smart Error Handling** - Guide users to alternatives when extraction fails

---

## Feature 1: "Save as CSS Template" Button

### User Experience Flow

```
User uses Smart Extraction
    ↓
Extraction succeeds
    ↓
Success message shows:
    ┌────────────────────────────────────┐
    │ ✓ Extraction Successful!          │
    │                                    │
    │ [💾 Save as CSS Template] ←  NEW  │
    └────────────────────────────────────┘
    ↓
User clicks button
    ↓
Modal appears:
    ┌────────────────────────────────────┐
    │ Save Template                      │
    │                                    │
    │ Name: [Drenting Cars______]       │
    │ Description: [Car listings___]     │
    │                                    │
    │ [Cancel]  [Save Template]          │
    └────────────────────────────────────┘
    ↓
Template saved
    ↓
Next time user visits CSS Selector mode:
    Dropdown now includes:
    - Screener.in Company Data
    - Drenting Cars  ← NEW
```

### Backend Changes

#### 1. New Database Table

```sql
CREATE TABLE saved_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    url_pattern VARCHAR(512),  -- e.g., "drenting.com/*"
    wait_for_selector VARCHAR(512),
    fields JSONB NOT NULL,     -- Array of ExtractionField objects
    created_by UUID,           -- User who created it
    created_at TIMESTAMP DEFAULT NOW(),
    last_used TIMESTAMP,
    use_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_saved_templates_name ON saved_templates(name);
CREATE INDEX idx_saved_templates_url_pattern ON saved_templates(url_pattern);
```

#### 2. New API Endpoints

```python
# backend/app/api/routes/template_extraction_routes.py

@router.post("/save-template")
async def save_smart_extraction_as_template(
    template_name: str,
    display_name: str,
    description: Optional[str],
    url_pattern: str,
    wait_for_selector: str,
    fields: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    """
    Save a Smart Extraction result as a reusable CSS template
    """
    # Validate template name is unique
    # Save to database
    # Return success with template_id
    pass


@router.get("/saved-templates")
async def list_saved_templates(db: Session = Depends(get_db)):
    """
    List all user-saved CSS templates (combined with presets)
    """
    # Get built-in presets
    presets = [screener_in, ...]

    # Get user-saved templates from database
    saved = db.query(SavedTemplate).filter(is_active=True).all()

    # Merge and return
    return {"templates": presets + saved}


@router.delete("/saved-templates/{template_id}")
async def delete_saved_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """Delete a user-saved template"""
    # Soft delete (set is_active = False)
    pass
```

#### 3. Dynamic Template Loading

```python
# backend/app/services/template_extraction_service.py

def get_template_by_name(template_name: str, db: Session) -> ExtractionTemplate:
    """
    Get template by name - checks both built-in and user-saved
    """
    # Check built-in presets first
    if template_name == "screener_in":
        return get_screener_in_template()
    elif template_name == "drenting":
        return get_drenting_template()

    # Check user-saved templates in database
    saved = db.query(SavedTemplate).filter(
        SavedTemplate.name == template_name,
        SavedTemplate.is_active == True
    ).first()

    if saved:
        # Convert DB record to ExtractionTemplate
        return ExtractionTemplate(
            name=saved.display_name,
            description=saved.description,
            wait_for_selector=saved.wait_for_selector,
            fields=[
                ExtractionField(**field_data)
                for field_data in saved.fields
            ]
        )

    raise HTTPException(404, f"Template '{template_name}' not found")
```

### Frontend Changes

#### 1. Save Template Button

```typescript
// frontend/src/components/SmartExtractor.tsx

const [showSaveModal, setShowSaveModal] = useState(false);
const [templateName, setTemplateName] = useState('');
const [templateDescription, setTemplateDescription] = useState('');

const handleSaveAsTemplate = async () => {
  try {
    const response = await axios.post('/api/v1/extract/save-template', {
      template_name: templateName.toLowerCase().replace(/\s+/g, '_'),
      display_name: templateName,
      description: templateDescription,
      url_pattern: extractUrlPattern(url),  // e.g., "drenting.com/*"
      wait_for_selector: generatedTemplate.fields[0].selector,
      fields: generatedTemplate.fields
    });

    alert('Template saved! Available in CSS Selector mode.');
    setShowSaveModal(false);
  } catch (error) {
    alert('Failed to save template: ' + error.message);
  }
};

// In the success UI:
{extractedData && extractedData.success && (
  <div className="success-message">
    ✓ Extraction Successful!
    <button onClick={() => setShowSaveModal(true)}>
      💾 Save as CSS Template
    </button>
  </div>
)}

// Save Modal
{showSaveModal && (
  <div className="modal">
    <h3>Save Template</h3>
    <input
      placeholder="Template Name"
      value={templateName}
      onChange={(e) => setTemplateName(e.target.value)}
    />
    <textarea
      placeholder="Description (optional)"
      value={templateDescription}
      onChange={(e) => setTemplateDescription(e.target.value)}
    />
    <button onClick={handleSaveAsTemplate}>Save Template</button>
    <button onClick={() => setShowSaveModal(false)}>Cancel</button>
  </div>
)}
```

#### 2. Dynamic Dropdown in CSS Selector Mode

```typescript
// frontend/src/components/TemplateExtractor.tsx

useEffect(() => {
  // Load both built-in and saved templates
  const loadTemplates = async () => {
    const response = await axios.get('/api/v1/extract/saved-templates');
    setAvailableTemplates(response.data.templates);
  };
  loadTemplates();
}, []);
```

---

## Feature 2: Auto Playwright Fallback

### Backend Implementation

```python
# backend/app/services/template_extraction_service.py

class TemplateExtractionService:
    async def extract_data(
        self,
        url: str,
        template: ExtractionTemplate,
        session_id: Optional[str] = None,
        use_playwright: bool = False
    ) -> Dict[str, Any]:
        """
        Extract data with automatic Playwright fallback
        """
        # Try with simple HTTP first (fast)
        if not use_playwright:
            try:
                return await self._extract_with_httpx(url, template)
            except HTTPStatusError as e:
                if e.response.status_code == 403:
                    logger.warning(f"403 Forbidden from {url}, falling back to Playwright")
                    # AUTOMATIC FALLBACK
                    use_playwright = True
                else:
                    raise

        # Use Playwright (slower but bypasses blocks)
        if use_playwright:
            return await self._extract_with_playwright(url, template, session_id)


    async def _extract_with_httpx(self, url, template):
        """Fast extraction using HTTPX"""
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()  # Raises 403 if blocked
            html = response.text
            return self._parse_html(html, template)


    async def _extract_with_playwright(self, url, template, session_id):
        """Robust extraction using Playwright (current implementation)"""
        # This is the existing Playwright code
        # Already handles JavaScript, bot detection, etc.
        ...
```

### Smart HTTP Client with Anti-Bot Headers

```python
# backend/app/services/scraper_service.py

class EnhancedScraperService:
    def __init__(self):
        self.httpx_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
        }

    async def scrape_with_fallback(self, url: str):
        """
        Try HTTPX first, fallback to Playwright if blocked
        """
        # Stage 1: Fast HTTPX attempt
        try:
            async with httpx.AsyncClient(headers=self.httpx_headers, timeout=10) as client:
                response = await client.get(url)
                response.raise_for_status()
                return {'html': response.text, 'method': 'httpx'}
        except httpx.HTTPStatusError as e:
            if e.response.status_code in [403, 429, 503]:
                logger.info(f"HTTPX blocked ({e.response.status_code}), trying Playwright...")
            else:
                raise

        # Stage 2: Playwright fallback
        return await self._scrape_with_playwright(url)
```

---

## Feature 3: Smart Error Handling & User Guidance

### Error Detection & Suggestions

```python
# backend/app/api/routes/template_extraction_routes.py

class ExtractionError(Exception):
    def __init__(self, message: str, error_type: str, suggestions: List[str]):
        self.message = message
        self.error_type = error_type
        self.suggestions = suggestions


@router.post("/extract")
async def extract_with_smart_errors(...):
    try:
        result = await template_service.extract_data(url, template)
        return result
    except HTTPStatusError as e:
        if e.response.status_code == 403:
            raise ExtractionError(
                message="Website is blocking automated access",
                error_type="BOT_BLOCKED",
                suggestions=[
                    "Try using Smart Extraction (AI-powered, works around blocks)",
                    "The site may require login or have anti-scraping protection",
                    "Consider using a different URL from the same site"
                ]
            )
        elif e.response.status_code == 404:
            raise ExtractionError(
                message="Page not found",
                error_type="NOT_FOUND",
                suggestions=[
                    "Check if the URL is correct",
                    "The page may have moved or been deleted",
                    "Try the website's homepage first"
                ]
            )
    except TimeoutError:
        raise ExtractionError(
            message="Page took too long to load",
            error_type="TIMEOUT",
            suggestions=[
                "Try again - the site may be slow",
                "Check your internet connection",
                "Try a different page from the same site"
            ]
        )
```

### Frontend Error Handling with Suggestions

```typescript
// frontend/src/components/TemplateExtractor.tsx

interface ExtractionError {
  message: string;
  error_type: string;
  suggestions: string[];
}

const handleExtraction = async () => {
  try {
    const result = await axios.post('/api/v1/extract', {...});
    setExtractedData(result.data);
  } catch (error) {
    if (error.response?.data?.error_type === 'BOT_BLOCKED') {
      // Show smart error with suggestions
      setError({
        title: '🚫 Website Blocking Detected',
        message: error.response.data.message,
        suggestions: error.response.data.suggestions,
        alternativeActions: [
          {
            label: 'Try Smart Extraction Instead',
            action: () => {
              // Navigate to Smart Extraction tab
              // Pre-fill the URL
              window.location.hash = '#smart-extraction';
            }
          },
          {
            label: 'Use Template Mapper',
            action: () => {
              window.location.hash = '#template-mapper';
            }
          }
        ]
      });
    }
  }
};

// Error Display Component
{error && (
  <div className="error-panel">
    <h3>{error.title}</h3>
    <p>{error.message}</p>

    <div className="suggestions">
      <h4>💡 Suggestions:</h4>
      <ul>
        {error.suggestions.map((suggestion, i) => (
          <li key={i}>{suggestion}</li>
        ))}
      </ul>
    </div>

    <div className="alternative-actions">
      <h4>Try These Instead:</h4>
      {error.alternativeActions.map((action, i) => (
        <button key={i} onClick={action.action}>
          {action.label}
        </button>
      ))}
    </div>
  </div>
)}
```

---

## Implementation Priority

### Phase 1: Auto Playwright Fallback (Quick Win)
**Time**: 2-3 hours
**Impact**: High
**Files to modify**:
- `backend/app/services/template_extraction_service.py`
- Add fallback logic to existing extraction methods

### Phase 2: Smart Error Handling
**Time**: 3-4 hours
**Impact**: Medium-High
**Files to modify**:
- `backend/app/api/routes/template_extraction_routes.py`
- `frontend/src/components/TemplateExtractor.tsx`
- `frontend/src/components/SmartExtractor.tsx`

### Phase 3: Save as CSS Template
**Time**: 6-8 hours
**Impact**: High (long-term)
**Files to create**:
- Database migration for `saved_templates` table
- New API endpoints for save/list/delete
- Modal component for saving templates
- Dynamic template loader

---

## Testing Plan

### Test Auto Fallback
```python
# Test with drenting.com (blocks HTTPX)
url = "https://www.drenting.com/"
result = await service.extract_data(url, template)
# Should automatically use Playwright
assert result['method'] == 'playwright'
```

### Test Save Template
```bash
curl -X POST http://localhost:8000/api/v1/extract/save-template \
  -d '{
    "template_name": "my_custom_template",
    "display_name": "My Custom Template",
    "url_pattern": "example.com/*",
    "fields": [...]
  }'
```

### Test Error Suggestions
```bash
# Try blocked site
curl -X POST http://localhost:8000/api/v1/extract/preset/screener_in \
  -d '{"url": "https://blocked-site.com"}'

# Should return suggestions to try Smart Extraction
```

---

## Summary

These features make the extraction system:
- **Smarter**: Auto-fallback when blocked
- **More User-Friendly**: Clear error messages with suggestions
- **Dynamic**: Users can save successful extractions as templates
- **Self-Service**: No developer needed to add new site templates

Want me to implement any of these features? I recommend starting with **Auto Playwright Fallback** since it's a quick win and solves the drenting.com issue immediately!
