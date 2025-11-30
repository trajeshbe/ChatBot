# Project-Based Chat Sessions - Fixes Required

## Issue Summary
After implementing project-based chat sessions, testing revealed several issues that need to be addressed:

### 1. Backend: project_id Not Persisting to Database ⚠️ CRITICAL
**Problem**: Documents and sessions are not storing project_id despite being passed from frontend
**Evidence**: Database shows project_id as NULL even when passed in upload request
**Impact**: Document isolation not working - all documents visible across all projects

**Root Cause Investigation Needed**:
- Check if Form parameter is being read correctly
- Verify UUID conversion isn't failing silently
- Add logging to trace the full flow

**Files to Check**:
- `/backend/app/main.py` (upload endpoint, lines 333-492)
- `/backend/app/services/document_service.py` (upload_file method)

### 2. Frontend: Document List Not Filtered by Project
**Problem**: When viewing a project, all 90 documents are shown instead of only project documents
**Expected**: Only documents belonging to the selected project should be visible
**Impact**: Users see documents from other projects, breaking isolation

**Fix Required**:
- Update document list API to accept project_id filter
- Update ProjectDetail component to pass project_id when fetching documents
- Filter session documents to only show those in the current project

**Files to Modify**:
- `/frontend/src/components/ProjectDetail.tsx`
- `/backend/app/main.py` (documents endpoint)

### 3. Frontend: Navigation Confusion - Duplicate "New Chat" Buttons
**Problem**: Two different "New chat" buttons with different behaviors:
  - Center button: Takes to home page chat (no project context)
  - Top right button: Should start chat within project context

**Expected**: Single, consistent behavior - clicking "New chat in [Project]" should:
  1. Stay within the project context
  2. Show embedded chat interface
  3. Associate session with project
  4. Only show project documents

**Fix Required**:
- Remove or hide the center "New chat" button when in project view
- Ensure top-right button triggers `isInChatMode` correctly
- Verify project context is maintained throughout chat session

**Files to Modify**:
- `/frontend/src/components/ProjectDetail.tsx`

### 4. Frontend: Missing Project Selector in Chat Tab
**Problem**: Users can't switch between projects while in the main Chat tab
**Expected**: Dropdown to select project, which filters documents and scopes queries

**Fix Required**:
- Add project selector dropdown to ChatInterface
- Load user's accessible projects
- Update document list and RAG queries based on selected project
- Save selected project to localStorage for persistence

**Files to Modify**:
- `/frontend/src/components/ChatInterfaceEnhanced.tsx`

### 5. Backend/Frontend: Rename "Default" to "Global" Project
**Problem**: "Default" project name is unclear
**Expected**: "Global" indicates documents accessible across all projects

**Fix Required**:
- Update database: Rename project where name='Default' to 'Global'
- Update any hardcoded references in code
- Update UI labels

**Files to Modify**:
- Database migration script
- Any code with hardcoded "Default" references

## Implementation Plan

### Phase 1: Critical Backend Fix (PRIORITY 1)
1. Debug project_id persistence
2. Add comprehensive logging
3. Fix UUID conversion if needed
4. Verify database constraints

### Phase 2: Document Filtering (PRIORITY 2)
1. Add project_id filter to documents API
2. Update ProjectDetail to pass project_id
3. Filter uploaded files list by project

### Phase 3: Navigation & UX (PRIORITY 3)
1. Fix "New chat" button behavior
2. Add project selector to Chat tab
3. Improve navigation flow

### Phase 4: Cosmetic (PRIORITY 4)
1. Rename Default → Global
2. Update UI labels
3. Add helpful tooltips

## Success Criteria
- ✅ Documents with project_id correctly saved to database
- ✅ Project detail shows only its own documents (not all 90)
- ✅ Queries within project only search project documents
- ✅ Clear, single navigation pattern for starting chats
- ✅ Project selector available in main Chat tab
- ✅ "Global" project for non-project documents

## Testing Checklist
- [ ] Upload document to Project A, verify project_id in database
- [ ] Upload document to Project B, verify project_id in database
- [ ] View Project A, confirm only Project A documents shown
- [ ] Query in Project A, confirm only Project A sources returned
- [ ] Query in Project B, confirm only Project B sources returned
- [ ] Switch projects in Chat tab, confirm document list updates
- [ ] Upload to Global project, confirm visible across all contexts
