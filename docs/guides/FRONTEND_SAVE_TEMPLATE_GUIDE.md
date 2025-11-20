# Frontend Save Template Button - Implementation Guide

## Overview

This guide provides the code changes needed to add the "Save as CSS Template" button to the frontend.

---

## Implementation Status

### ✅ Backend Complete:
- Auto-fallback to Playwright
- Better error messages
- Database migration
- Save Template API endpoints (/save-template, /saved-templates, /saved-templates/{id})

### 🔄 Frontend Remaining:
- Add Save Template button to TemplateExtractor.tsx
- Create modal for template name/description
- Connect to save-template API
- Refresh template dropdown after save

---

## Step 1: Add State Variables

Add these state variables to `frontend/src/components/TemplateExtractor.tsx`:

```typescript
// Add after existing useState declarations (around line 30-40)
const [showSaveModal, setShowSaveModal] = useState(false);
const [templateName, setTemplateName] = useState('');
const [templateDescription, setTemplateDescription] = useState('');
const [isSaving, setIsSaving] = useState(false);
```

---

## Step 2: Add Save Template Handler

Add this function (around line 100-150, after other handlers):

```typescript
const handleSaveAsTemplate = async () => {
  if (!templateName.trim()) {
    alert('Please enter a template name');
    return;
  }

  setIsSaving(true);
  try {
    // Convert template name to internal format (lowercase with underscores)
    const internalName = templateName.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '');

    // Get URL pattern from current URL
    const urlObj = new URL(url);
    const urlPattern = `${urlObj.hostname}/*`;

    // Prepare fields from current extraction
    const templateFields = extractedData.data[0] ? Object.keys(extractedData.data[0]).map(key => ({
      name: key,
      selector: '',  // User would need to define selectors - this is from successful extraction
      data_type: 'text',
      required: false
    })) : [];

    const response = await axios.post(`${API_URL}/api/v1/extract/save-template`, {
      template_name: internalName,
      display_name: templateName,
      description: templateDescription || `Extract data from ${urlObj.hostname}`,
      url_pattern: urlPattern,
      wait_for_selector: '.main',  // Default selector
      fields: templateFields
    });

    alert(`✅ Template "${templateName}" saved successfully! It's now available in the preset dropdown.`);
    setShowSaveModal(false);
    setTemplateName('');
    setTemplateDescription('');

    // Optionally reload presets
    // await loadPresets();

  } catch (error: any) {
    console.error('Error saving template:', error);
    alert(`Failed to save template: ${error.response?.data?.detail || error.message}`);
  } finally {
    setIsSaving(false);
  }
};
```

---

## Step 3: Add Save Button to Success UI

Find the success message display (search for `extractedData && extractedData.success`) and add the Save Template button:

```typescript
{extractedData && extractedData.success && (
  <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 mb-6">
    <div className="flex items-center justify-between">
      <div className="flex items-center space-x-2">
        <svg className="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
        <span className="text-green-700 dark:text-green-300 font-medium">
          ✓ Extraction Successful! Extracted {extractedData.row_count} row(s)
        </span>
      </div>

      {/* NEW: Save Template Button */}
      <button
        onClick={() => setShowSaveModal(true)}
        className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
        title="Save this extraction as a reusable CSS template"
      >
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
        </svg>
        <span>Save as CSS Template</span>
      </button>
    </div>
  </div>
)}
```

---

## Step 4: Add Save Template Modal

Add this modal component at the end of the return statement, before the closing `</div>`:

```typescript
{/* Save Template Modal */}
{showSaveModal && (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl p-6 w-full max-w-md">
      <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">
        Save as CSS Template
      </h3>

      <div className="space-y-4">
        {/* Template Name */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
            Template Name *
          </label>
          <input
            type="text"
            value={templateName}
            onChange={(e) => setTemplateName(e.target.value)}
            placeholder="e.g., Product Data Extraction"
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
          />
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            This name will appear in the preset dropdown
          </p>
        </div>

        {/* Template Description */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
            Description (optional)
          </label>
          <textarea
            value={templateDescription}
            onChange={(e) => setTemplateDescription(e.target.value)}
            placeholder="Brief description of what this template extracts..."
            rows={3}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
          />
        </div>

        {/* Info Note */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
          <p className="text-sm text-blue-700 dark:text-blue-300">
            💡 This will save the extraction structure as a reusable template. You can use it for similar pages in the future.
          </p>
        </div>
      </div>

      {/* Modal Actions */}
      <div className="flex space-x-3 mt-6">
        <button
          onClick={() => {
            setShowSaveModal(false);
            setTemplateName('');
            setTemplateDescription('');
          }}
          className="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
          disabled={isSaving}
        >
          Cancel
        </button>
        <button
          onClick={handleSaveAsTemplate}
          disabled={isSaving || !templateName.trim()}
          className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white rounded-lg transition-colors"
        >
          {isSaving ? 'Saving...' : 'Save Template'}
        </button>
      </div>
    </div>
  </div>
)}
```

---

## Step 5: Update Template Dropdown (Optional Enhancement)

To dynamically load templates from the database, update the `useEffect` that loads presets:

```typescript
useEffect(() => {
  // Load presets from API
  const loadPresets = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/v1/extract/saved-templates`);
      setAvailablePresets(response.data.templates);
    } catch (error) {
      console.error('Error loading presets:', error);
      // Fallback to hardcoded presets if API fails
    }
  };

  loadPresets();
}, []);
```

---

## Testing Steps

### 1. Test Save Template Flow:
```
1. Go to CSS Selector Based extraction
2. Enter URL: https://www.screener.in/company/RELIANCE/consolidated/
3. Select preset: "Screener.in Company Data"
4. Click "Extract Data"
5. After success, click "💾 Save as CSS Template"
6. Enter Name: "Test Template"
7. Enter Description: "Testing save functionality"
8. Click "Save Template"
9. Should see success message
10. Check database to verify template was saved
```

### 2. Verify Database:
```bash
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "SELECT name, display_name, description FROM saved_css_templates;"
```

### 3. Test Template Retrieval:
```bash
curl http://localhost:8000/api/v1/extract/saved-templates | jq '.templates[] | {name, display_name, source}'
```

Expected output:
```json
{
  "name": "screener_in",
  "display_name": "Screener.in Company Data",
  "source": "builtin"
}
{
  "name": "drenting",
  "display_name": "Drenting.com Car Listings",
  "source": "builtin"
}
{
  "name": "test_template",
  "display_name": "Test Template",
  "source": "user_saved"
}
```

---

## Error Handling

The modal handles these scenarios:
- ❌ Empty template name: Shows alert
- ❌ Duplicate template name: Backend returns 400 error
- ❌ API error: Shows error message in alert
- ✅ Success: Shows success message and closes modal

---

## Next Steps After Implementation

1. Restart frontend: `docker-compose restart frontend`
2. Test save template functionality
3. Test template dropdown shows saved templates
4. Test using a saved template for extraction
5. Test deleting a saved template (future feature)

---

## Complete Implementation Checklist

### Backend ✅
- [x] Auto-fallback to Playwright
- [x] Better error messages
- [x] Database migration
- [x] Save Template API endpoint
- [x] List Templates API endpoint
- [x] Delete Template API endpoint

### Frontend 🔄
- [ ] Add state variables
- [ ] Add save handler function
- [ ] Add Save Template button
- [ ] Add Save Template modal
- [ ] Update template dropdown loading
- [ ] Restart frontend
- [ ] Test end-to-end

---

## Quick Copy-Paste Summary

**File to modify**: `frontend/src/components/TemplateExtractor.tsx`

**Sections to add**:
1. State variables (4 lines)
2. Save handler function (40 lines)
3. Save button in success UI (15 lines)
4. Save modal component (60 lines)

**Total additions**: ~120 lines of code

---

**Status**: Ready for implementation
**Estimated Time**: 15-30 minutes
