# Unified Project Context Dropdown Implementation

**Date**: 2025-11-29
**Status**: Phase 2 Complete ✅ (UI Redesign + Authentication Fix)
**Remaining**: SmartTemplateMapper, TemplateExtractor, Backend Endpoints

---

## 🎯 Goal

Create a **single, unified Project Context dropdown** that appears at the top of the Web Scraping page and works across ALL scraping types:
- ✅ Basic Scraping
- ✅ Smart Extraction (AI-powered)
- ⏳ Template Mapper (needs update)
- ⏳ CSS Selector Based (needs update)

---

## ✅ What's Been Implemented

### 1. Unified Project Dropdown in UnifiedWebScraper ✅

**File**: `frontend/src/components/UnifiedWebScraper.tsx`

**Changes**:
- Added project state and fetching logic at the parent component level
- Created beautiful project dropdown above the tab navigation
- Dropdown loads all active projects from `/api/v1/projects`
- Shows "Global (No Project)" as default option
- Displays helpful message when a project is selected
- Passes `selectedProjectId` to ALL child scraping components

**Key Features**:
- Loads projects on mount
- Handles authentication token
- Silently fails if projects unavailable (optional feature)
- Clean UI with Folder icon and clear labeling
- Confirmation message: "✓ All scraped/extracted content will be organized under this project"

### 2. WebScraper Component Updated ✅

**File**: `frontend/src/components/WebScraper.tsx`

**Changes**:
- **Removed** its own project dropdown (now handled by parent)
- **Added** `projectId` prop to interface
- **Updated** scraping requests to include `project_id` in payload
- **Changed** endpoint to `/api/v1/scraper/scrape` (JSON instead of FormData)
- **Simplified** component - no longer manages projects internally

**Before**:
```typescript
export default function WebScraper({ sessionId }: WebScraperProps)
```

**After**:
```typescript
interface WebScraperProps {
  sessionId?: string
  projectId?: string  // NEW
}

export default function WebScraper({ sessionId, projectId }: WebScraperProps)
```

**API Request**:
```typescript
const requestData = {
  url: validUrls[i],
  scrape_prompt: scrapePrompt || undefined,
  session_id: sessionId || undefined,
  project_id: projectId || undefined  // Sent to backend
}
```

### 3. SmartExtractor Component Updated ✅

**File**: `frontend/src/components/SmartExtractor.tsx`

**Changes**:
- **Added** `projectId` prop to interface
- **Updated** both API calls to include `project_id`:
  - Auto-generate template: `/api/v1/extract/auto-generate`
  - Ultra-smart extraction: `/api/v1/extract/ultra-smart`

**API Requests Now Include**:
```typescript
{
  url,
  user_instructions: userInstructions,
  llm_provider: llmProvider,
  // ... other params
  project_id: projectId || undefined  // NEW
}
```

---

## ⏳ What Still Needs to Be Done

### 1. SmartTemplateMapper Component

**File**: `frontend/src/components/SmartTemplateMapper.tsx`

**Required Changes**:
- [ ] Add `projectId` prop to component interface
- [ ] Find API endpoint used for template mapping
- [ ] Add `project_id` to request payload

### 2. TemplateExtractor Component

**File**: `frontend/src/components/TemplateExtractor.tsx`

**Required Changes**:
- [ ] Add `projectId` prop to component interface (already passed from parent)
- [ ] Find API endpoint used for CSS selector extraction
- [ ] Add `project_id` to request payload

### 3. Backend Endpoints

All extraction endpoints need to accept `project_id` parameter and save documents with project context:

**Endpoints to Update**:
- [ ] `/api/v1/extract/auto-generate` - Add project_id parameter
- [ ] `/api/v1/extract/ultra-smart` - Add project_id parameter
- [ ] `/api/v1/extract/template-mapping` - Add project_id parameter (if exists)
- [ ] `/api/v1/extract/css-selector` - Add project_id parameter (if exists)

**Pattern to Follow** (from scraper_routes.py):
```python
@router.post("/extract/auto-generate")
async def auto_generate(
    request: AutoGenerateRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db)
):
    # Get current user
    current_user = await get_current_user_from_request(http_request, db)
    user_id = str(current_user.id) if current_user else None

    # Extract project context from request
    project_id = request.project_id
    department = request.department
    team = request.team

    # If user authenticated but no dept/team, get from user profile
    if current_user and not department:
        # ... fetch from Department/Team tables

    # Pass to service layer
    result = await extraction_service.auto_generate(
        url=request.url,
        project_id=project_id,
        department=department,
        team=team,
        user_id=user_id,
        db=db
    )
```

---

## 📊 Current Status

### ✅ Completed

1. **Unified Project Dropdown** ✅
   - Clean UI above tabs
   - Loads all active projects
   - Shows helpful feedback

2. **WebScraper (Basic Scraping)** ✅
   - Accepts projectId prop
   - Sends project_id to backend
   - Backend already supports this

3. **SmartExtractor (AI Extraction)** ✅
   - Accepts projectId prop
   - Sends project_id to backend API calls
   - Backend needs update to accept it

### 🔄 In Progress / Remaining

4. **SmartTemplateMapper** ⏳
   - Prop already passed from parent
   - Needs to send project_id to backend

5. **TemplateExtractor** ⏳
   - Prop already passed from parent
   - Needs to send project_id to backend

6. **Backend Extraction Endpoints** ⏳
   - Need to accept project_id parameter
   - Need to save documents with project context
   - Need to populate web_scrape_jobs or similar tracking table

---

## 🧪 Testing

### What You Can Test Right Now

**Test 1: Basic Scraping** ✅ READY
1. Go to Web Scraping tab
2. Select a project from unified dropdown
3. Switch to "Basic Scraping" tab
4. Enter URL: `https://en.wikipedia.org/wiki/Tuticorin_Airport`
5. Click "Start Scraping"

**Expected**:
- ✅ Project dropdown visible at top
- ✅ Scraping completes successfully
- ✅ Database has project_id populated

**Test 2: Smart Extraction** 🔄 PARTIAL
1. Select a project from unified dropdown
2. Switch to "Smart Extraction" tab
3. Enter URL and instructions
4. Click extract

**Expected**:
- ✅ Project dropdown visible (same as Basic)
- ✅ Request includes project_id
- ⚠️ Backend might not accept it yet (needs endpoint update)

**Test 3: Template Mapper** ⏳ NOT READY
- Component receives projectId prop
- But doesn't send it to backend yet

**Test 4: CSS Selector** ⏳ NOT READY
- Component receives projectId prop
- But doesn't send it to backend yet

---

## 🎨 UI/UX Features

### Unified Dropdown Appearance

```
┌─────────────────────────────────────────────────────┐
│  📁 Project Context (Optional)                      │
│                                                      │
│  Assign scraped/extracted content to a specific     │
│  project for organized knowledge management          │
│                                                      │
│  ┌────────────────────────────────────────────┐   │
│  │ Global (No Project)                ▼       │   │
│  └────────────────────────────────────────────┘   │
│                                                      │
│  ✓ All scraped/extracted content will be organized  │
│    under this project                                │
└─────────────────────────────────────────────────────┘
```

### Position

The dropdown appears:
- **Above** the tab navigation
- **Below** the page header ("Web Scraping & Data Extraction")
- **Applies to all tabs** - selection persists when switching between scraping methods

---

## 📝 Files Modified

### Frontend ✅
1. `frontend/src/components/UnifiedWebScraper.tsx` - Added unified dropdown
2. `frontend/src/components/WebScraper.tsx` - Removed own dropdown, uses prop
3. `frontend/src/components/SmartExtractor.tsx` - Added projectId prop and API integration

### Backend (Previous Work) ✅
1. `backend/app/api/routes/scraper_routes.py` - Already accepts project_id
2. `backend/app/services/scraper_service_enhanced.py` - Already handles project context
3. `backend/app/schemas/scraper_schemas.py` - Already has project_id field

### Backend (Still Needed) ⏳
1. `backend/app/api/routes/extraction_routes.py` - Needs project_id support
2. `backend/app/services/template_extraction_service.py` - Needs update
3. `backend/app/schemas/extraction_schemas.py` - Add project_id fields

---

## 🎯 Next Steps

### Immediate (Can Test Now)
1. **Test Basic Scraping** with project selection
2. **Test Smart Extraction** with project selection (frontend sends it, backend might ignore)

### Short-term (Next Session)
1. **Update SmartTemplateMapper** to send project_id
2. **Update TemplateExtractor** to send project_id
3. **Update backend extraction endpoints** to accept and use project_id
4. **Test all 4 scraping methods** end-to-end

### Long-term (Future)
1. **RAG Integration** - Filter documents by project_id in queries
2. **MinIO Paths** - Hierarchical storage structure
3. **Analytics** - Project-level scraping stats

---

**Summary**: The unified project dropdown is working and appears for all scraping types. Basic Scraping is fully functional with project context. Smart Extraction sends project_id but backend needs update. Template Mapper and CSS Selector need frontend + backend updates.

**Status**: ✅ Phase 2 Complete (Authentication Fix + UI Redesign)
**Next**: Update remaining components and backend endpoints

**Created**: 2025-11-29 15:00
**Last Updated**: 2025-11-29 17:45

---

## 🎨 Phase 2 Updates (2025-11-29 17:45)

### Authentication Fix ✅

**Issue**: Project dropdown was not populating - returning 403 Forbidden error

**Root Cause**: UnifiedWebScraper was using `localStorage.getItem('token')` instead of `localStorage.getItem('access_token')`

**Fix Applied**:
```typescript
// Before
const token = localStorage.getItem('token')

// After
const token = localStorage.getItem('access_token')
```

**Result**: Project dropdown now successfully loads projects from `/api/v1/projects` endpoint

### UI Redesign ✅

**Issue**: User reported that the web scraping page and tabs looked "wide and messy"

**Changes Made**:

1. **Compact Layout**
   - Changed max-width from `max-w-7xl` to `max-w-6xl`
   - Added horizontal padding: `px-4`
   - Reduced header size from `text-3xl` to `text-2xl`

2. **Modern Project Dropdown**
   - Horizontal layout instead of vertical
   - Gradient background: `bg-gradient-to-r from-white to-gray-50`
   - Compact padding: `p-4` instead of `p-6`
   - Smaller font sizes: `text-sm` and `text-xs`
   - Dropdown positioned on the right side
   - Max-width constraint: `max-w-xs`

3. **Pill-Style Tabs**
   - Replaced border-bottom tabs with modern pill design
   - Enclosed in rounded container: `rounded-xl p-1 gap-1`
   - Active tab has white background and shadow
   - Compact size: `text-sm` and `w-4 h-4` icons
   - Tooltip on hover (title attribute) instead of visible descriptions

4. **Compact Info Footer**
   - Two-column grid layout on medium screens
   - Gradient background: `from-blue-50 to-indigo-50`
   - Smaller text: `text-xs`
   - Colorful icons for each method
   - Concise descriptions

**Visual Improvements**:
- More white space and breathing room
- Better visual hierarchy
- Cleaner, more modern aesthetic
- Responsive design that doesn't look wide
- Improved color palette with gradients
- Better dark mode support

**Before/After Comparison**:

| Aspect | Before | After |
|--------|--------|-------|
| Header Size | 3xl | 2xl |
| Max Width | 7xl | 6xl |
| Project Dropdown | Vertical, large | Horizontal, compact |
| Tabs | Border-bottom style | Pill-style in container |
| Info Footer | Single column | Two-column grid |
| Text Sizes | Mixed large/medium | Consistent small |
| Design Style | Wide, spacious | Compact, modern |
