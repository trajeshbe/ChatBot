# Project-Based Scraping Implementation

**Date**: 2025-11-29
**Status**: Phase 1-3 Complete (Database, Backend, Frontend) ✅
**Remaining**: Phase 4 (RAG Integration), Phase 5 (Testing)

---

## 🎯 Goals

1. ✅ **Database Schema**: Add project/user/dept/team columns to scraping tables (COMPLETE)
2. ✅ **Backend API**: Accept and pass project context through scraping endpoints (COMPLETE)
3. ✅ **Service Layer**: Update scraper service to handle organizational context (COMPLETE)
4. ✅ **UI Integration**: Add project dropdown to web scraping interface (COMPLETE)
5. 🔄 **RAG Integration**: Retrieve project-scoped scraped documents in chat queries (TODO)
6. 🔄 **End-to-End Testing**: Verify complete flow works as expected (TODO)

---

## ✅ Phase 1: Database Schema (COMPLETE)

### Migration Created: `012_add_project_based_scraping.sql`

#### Columns Added to `web_scrape_jobs`:
- `project_id` UUID → Links to `modules` table (projects)
- `scraped_by` UUID → Links to `users` table
- `department` VARCHAR(255) → Department name
- `team` VARCHAR(255) → Team name

#### Columns Added to `documents` (if missing):
- `project_id` UUID → Links to `modules` table
- `uploaded_by` UUID → Links to `users` table
- `department` VARCHAR(255) → Department name
- `team` VARCHAR(255) → Team name

#### Indexes Created:
```sql
-- web_scrape_jobs indexes
idx_web_scrape_jobs_project_id
idx_web_scrape_jobs_scraped_by
idx_web_scrape_jobs_department
idx_web_scrape_jobs_team
idx_web_scrape_jobs_project_status (composite)

-- documents indexes
idx_documents_project_id
idx_documents_department
idx_documents_team
idx_documents_uploaded_by
idx_documents_project_source (composite)
```

### Migration Applied
✅ Successfully applied to database
✅ Backend restarted to clear session state
✅ Web scraping error resolved

---

## ✅ Phase 2: Backend Service Layer (COMPLETE)

### Updated Scraper Service

**File**: `backend/app/services/scraper_service_enhanced.py`

#### Changes Made:

1. **Updated `scrape_url()` function signature** (Lines 70-82):
   - Added `project_id: Optional[str] = None`
   - Added `department: Optional[str] = None`
   - Added `team: Optional[str] = None`
   - Added `user_id: Optional[str] = None`

2. **Updated WebScrapeJob creation** (Lines 145-153):
   - Populates `project_id`, `scraped_by`, `department`, `team` fields

3. **Updated document creation** (Lines 200-212):
   - Passes organizational context to `document_service.upload_file()`
   - Ensures documents are saved with project/dept/team metadata

4. **Updated `scrape_multiple_urls()` function** (Lines 295-355):
   - Added same organizational parameters
   - Passes context to each individual `scrape_url()` call

---

## ✅ Phase 3: Backend API Endpoints (COMPLETE)

### Updated API Routes

**File**: `backend/app/api/routes/scraper_routes.py`

#### Changes Made:

1. **Added imports** (Lines 8, 13):
   - `Request` from FastAPI
   - `get_current_user_from_request` from security module

2. **Updated `/scrape` endpoint** (Lines 49-204):
   - Added `http_request: Request` parameter to access headers
   - Extracts current user from auth token (optional)
   - Gets `project_id`, `department`, `team` from request body
   - Falls back to user's department/team if not provided in request
   - Logs scraping context for debugging
   - Passes all organizational parameters to service

3. **Updated `/scrape/bulk` endpoint** (Lines 207-405):
   - Same pattern as single scrape endpoint
   - Extracts user and organizational context
   - Passes to service for all URLs

4. **Key Features**:
   - **Optional Authentication**: Works with or without auth token
   - **Smart Defaults**: Uses user's dept/team if not explicitly provided
   - **Logging**: Comprehensive logging of scraping context
   - **Backward Compatible**: Existing scraping without projects still works

### Updated Request Schemas

**File**: `backend/app/schemas/scraper_schemas.py`

#### Changes Made (Lines 143-154):

```python
session_id: Optional[str] = Field(default=None, description="Session ID to associate document with")
project_id: Optional[str] = Field(default=None, description="Project/Module ID for organization")
department: Optional[str] = Field(default=None, description="Department name for organization")
team: Optional[str] = Field(default=None, description="Team name for organization")
```

---

## ✅ Phase 4: Frontend UI (COMPLETE)

### Updated WebScraper Component

**File**: `frontend/src/components/WebScraper.tsx`

#### Changes Made:

1. **Added Project interface** (Lines 5-10):
```typescript
interface Project {
  id: string
  name: string
  description?: string
  status?: string
}
```

2. **Added state variables** (Lines 78-80):
```typescript
const [selectedProjectId, setSelectedProjectId] = useState<string>('')
const [projects, setProjects] = useState<Project[]>([])
const [loadingProjects, setLoadingProjects] = useState(false)
```

3. **Added useEffect to fetch projects** (Lines 107-126):
   - Fetches projects from `/api/v1/projects` endpoint
   - Handles authentication token
   - Silently fails if projects unavailable (optional feature)

4. **Updated scraping request** (Lines 162-172):
   - Sends JSON instead of FormData
   - Includes `project_id` in request body
   - Changed endpoint to `/api/v1/scraper/scrape`

5. **Added Project Selection UI** (Lines 230-268):
   - Folder icon with clear heading
   - Dropdown with all active projects
   - "Global (No Project)" option for backward compatibility
   - Loading state while fetching projects
   - Helpful message when project selected

**UI Features**:
- Clean, consistent design matching existing UI
- Optional selection (defaults to "Global")
- Shows project description in dropdown
- Visual feedback when project selected
- Responsive and accessible

---

## 🔄 Phase 5: MinIO Path Structure (NOT IMPLEMENTED YET)

**Note**: The current implementation saves scraped documents to the database with project/dept/team metadata, but MinIO path structure has NOT been updated yet. This is still using the simple path structure.

**What Still Needs to be Done**:
- Update `document_service.py` to use hierarchical MinIO paths for scraped content
- Format: `/department/{dept}/team/{team}/project/{project}/users/{user}/scraped/{domain}/{filename}`
- This will be addressed in a future update

### Current MinIO Structure for File Uploads

```
/department/{dept}/team/{team}/project/{project}/users/{user}/{filename}
```

**Example**:
```
/department/Engineering/team/AI-Team/project/Construction-Intelligence/users/john-doe/document.pdf
```

### Required Changes for Scraped Content

#### 1. Update Scraper Service

**File**: `backend/app/services/scraper_service_enhanced.py`

**Current behavior**:
- Saves to MinIO with simple path: `scraped-content/{job_id}/{filename}`

**Required behavior**:
- Accept `project_id`, `user_id`, `department`, `team` parameters
- Build hierarchical path: `department/{dept}/team/{team}/project/{project}/users/{user}/scraped/{domain}/{filename}`

**Code Changes Needed**:

```python
# In ScraperServiceEnhanced class

async def save_to_minio(
    self,
    content: str,
    url: str,
    job_id: str,
    project_id: Optional[str] = None,
    user_id: Optional[str] = None,
    department: Optional[str] = None,
    team: Optional[str] = None
) -> str:
    """
    Save scraped content to MinIO with organizational path structure

    Path structure:
    - With project: /department/{dept}/team/{team}/project/{project}/users/{user}/scraped/{domain}/{filename}
    - Without project: /department/{dept}/team/{team}/users/{user}/scraped/{domain}/{filename}
    - Fallback: /scraped-content/{job_id}/{filename}
    """
    from urllib.parse import urlparse

    domain = urlparse(url).netloc.replace('www.', '')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{domain}_{timestamp}.html"

    # Build hierarchical path
    if project_id and user_id and department and team:
        # Full organizational path
        path_parts = [
            'department', department,
            'team', team,
            'project', project_id,
            'users', user_id,
            'scraped', domain,
            filename
        ]
        object_name = '/'.join(path_parts)
    elif user_id and department and team:
        # Without project
        path_parts = [
            'department', department,
            'team', team,
            'users', user_id,
            'scraped', domain,
            filename
        ]
        object_name = '/'.join(path_parts)
    else:
        # Fallback to simple path
        object_name = f"scraped-content/{job_id}/{filename}"

    # Save to MinIO
    self.minio_client.put_object(
        bucket_name=self.bucket_name,
        object_name=object_name,
        data=io.BytesIO(content.encode('utf-8')),
        length=len(content.encode('utf-8')),
        content_type='text/html'
    )

    return object_name
```

#### 2. Update Scraping Endpoints

**File**: `backend/app/api/routes/scraper_routes.py` or `scraper_enhanced.py`

**Update POST endpoints to accept**:
```python
class ScrapeRequest(BaseModel):
    urls: List[str]
    scrape_prompt: Optional[str] = None
    project_id: Optional[str] = None  # Add this
    department: Optional[str] = None  # Add this
    team: Optional[str] = None        # Add this
    # ... other fields
```

**Pass to service**:
```python
@router.post("/api/v1/scrape")
async def scrape_urls(
    request: ScrapeRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get user info
    user_id = current_user.get('user_id')

    # Get project info if provided
    project_id = request.project_id
    department = request.department
    team = request.team

    # If project_id is provided, get dept/team from project
    if project_id and not (department and team):
        project = db.query(Module).filter(Module.id == project_id).first()
        if project:
            # Extract dept/team from project metadata or user assignment
            # This logic depends on your Module schema
            pass

    # Create scraping job with organizational context
    job = WebScrapeJob(
        url=url,
        project_id=project_id,
        scraped_by=user_id,
        department=department,
        team=team,
        status='processing'
    )
    db.add(job)
    db.commit()

    # Pass context to scraper service
    await scraper_service.scrape_url(
        url=url,
        job_id=job.id,
        project_id=project_id,
        user_id=user_id,
        department=department,
        team=team
    )
```

#### 3. Update Document Creation

**File**: `backend/app/services/scraper_service_enhanced.py`

When creating the `documents` record after scraping, populate organizational fields:

```python
# After successful scrape
document = Document(
    filename=filename,
    file_path=minio_path,
    file_type='html',
    file_size=len(content),
    source_type='scrape',
    source_url=url,
    project_id=project_id,      # Add this
    uploaded_by=user_id,         # Add this
    department=department,       # Add this
    team=team,                   # Add this
    processing_status='pending'
)
```

---

## 🔄 Phase 3: RAG Integration (TODO)

### Goal
When user queries in a project context, RAG should:
1. Retrieve documents uploaded to that project
2. Retrieve documents scraped in that project context
3. Prioritize project-scoped content over global content

### Required Changes

#### 1. Update RAG Service Query

**File**: `backend/app/services/rag_service.py` or `rag_service_enhanced.py`

**Current behavior**:
- Queries all document chunks
- Filters by session (short-term memory)
- Falls back to all documents (long-term memory)

**Required behavior**:
- Add project filtering layer
- Query hierarchy:
  1. **Project + Session**: Documents in current project + current session
  2. **Project-wide**: All documents in current project
  3. **Global**: All documents (if no project context)

**Code Changes**:

```python
async def retrieve_relevant_chunks(
    self,
    query: str,
    session_id: Optional[str] = None,
    project_id: Optional[str] = None,  # Add this parameter
    top_k: int = 5
) -> List[dict]:
    """
    Retrieve relevant document chunks with project filtering

    Query hierarchy:
    1. If project_id: Filter by project first, then by session if provided
    2. If session_id only: Filter by session
    3. Otherwise: Query all documents
    """

    # Generate query embedding
    query_embedding = self.embedding_service.generate_embedding(query)

    # Build query with project filtering
    query = db.query(DocumentChunk).join(Document)

    if project_id:
        # Filter by project
        query = query.filter(Document.project_id == project_id)

        if session_id:
            # Within project, prioritize session documents
            query = query.filter(
                or_(
                    Document.session_id == session_id,
                    Document.session_id.is_(None)  # Include project-wide docs
                )
            )

        # Order by: session docs first, then by similarity
        query = query.order_by(
            Document.session_id.desc().nullslast(),
            DocumentChunk.embedding.cosine_distance(query_embedding)
        )
    elif session_id:
        # Filter by session only
        query = query.filter(Document.session_id == session_id)
        query = query.order_by(
            DocumentChunk.embedding.cosine_distance(query_embedding)
        )
    else:
        # Global search
        query = query.order_by(
            DocumentChunk.embedding.cosine_distance(query_embedding)
        )

    # Execute query
    chunks = query.limit(top_k).all()

    return [
        {
            'content': chunk.content,
            'document_id': chunk.document_id,
            'filename': chunk.document.filename,
            'source_url': chunk.document.source_url,
            'project_id': chunk.document.project_id,
            'score': calculate_similarity(query_embedding, chunk.embedding)
        }
        for chunk in chunks
    ]
```

#### 2. Update Chat Query Endpoint

**File**: `backend/app/api/routes/rag_pipeline_routes.py` or similar

**Accept `project_id` parameter**:

```python
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    project_id: Optional[str] = None  # Add this
    top_k: int = 5
    model: Optional[str] = None

@router.post("/api/v1/query")
async def query_documents(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Retrieve chunks with project context
    chunks = await rag_service.retrieve_relevant_chunks(
        query=request.query,
        session_id=request.session_id,
        project_id=request.project_id,  # Pass project context
        top_k=request.top_k
    )

    # Generate answer with retrieved chunks
    answer = await llm_service.generate_answer(
        query=request.query,
        context_chunks=chunks
    )

    return {
        'answer': answer,
        'sources': chunks,
        'project_scoped': bool(request.project_id)
    }
```

---

## 🔄 Phase 4: UI Integration (TODO)

### Update Frontend Components

#### 1. WebScraper Component

**File**: `frontend/src/components/UnifiedWebScraper.tsx` or `WebScraperEnhanced.tsx`

**Add project selector**:

```typescript
const UnifiedWebScraper: React.FC = () => {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const [projects, setProjects] = useState<Project[]>([])

  // Load projects
  useEffect(() => {
    fetchProjects().then(setProjects)
  }, [])

  const handleScrape = async () => {
    const response = await fetch('/api/v1/scrape', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        urls: urls,
        project_id: selectedProjectId,  // Include project context
        // department and team will be derived from project on backend
      })
    })
    // Handle response...
  }

  return (
    <div>
      {/* Project Selector */}
      <div className="mb-4">
        <label>Scrape to Project (Optional)</label>
        <select value={selectedProjectId || ''} onChange={(e) => setSelectedProjectId(e.target.value || null)}>
          <option value="">Global (No Project)</option>
          {projects.map(project => (
            <option key={project.id} value={project.id}>{project.name}</option>
          ))}
        </select>
      </div>

      {/* URL inputs, etc. */}
    </div>
  )
}
```

#### 2. ChatInterface Component

**File**: `frontend/src/components/ChatInterfaceEnhanced.tsx`

**Already has `projectId` prop** - just ensure it's passed to query API:

```typescript
const sendQuery = async () => {
  const response = await fetch('/api/v1/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: userMessage,
      session_id: sessionId,
      project_id: projectId,  // Already available!
      top_k: 5
    })
  })
  // Handle response...
}
```

---

## 📊 Implementation Summary

### What's Done ✅

1. **Database Schema**:
   - ✅ Added `project_id`, `scraped_by`, `department`, `team` to `web_scrape_jobs`
   - ✅ Ensured `documents` table has same organizational columns
   - ✅ Created indexes for efficient querying
   - ✅ Applied migration to database
   - ✅ Restarted backend

2. **Immediate Error Fix**:
   - ✅ Resolved "column 'project_id' does not exist" error
   - ✅ Web scraping should now work without database errors

### What's Remaining 🔄

#### Priority 1: MinIO Path Structure
- [ ] Update `scraper_service_enhanced.py` to build hierarchical paths
- [ ] Update scraping endpoints to accept `project_id`, `department`, `team`
- [ ] Populate `documents` table with organizational fields when creating documents

#### Priority 2: RAG Integration
- [ ] Update `rag_service.py` to filter by `project_id`
- [ ] Implement 3-tier query hierarchy (project+session → project → global)
- [ ] Update chat query endpoint to accept and pass `project_id`

#### Priority 3: UI Enhancement
- [ ] Add project selector to WebScraper component
- [ ] Show project context indicator when scraping to a project
- [ ] Display project-scoped sources differently in chat responses

---

## 🧪 Testing Plan

### Test 1: Basic Scraping (After Phase 1)
**Status**: Ready to test now

**Steps**:
1. Go to Web Scraping page
2. Enter URL: `https://en.wikipedia.org/wiki/Tuticorin_Airport`
3. Click scrape

**Expected**:
- ✅ No database error
- ✅ Scraping completes successfully
- ⚠️ Project context not yet saved (Phase 2 needed)

### Test 2: Project-Based Scraping (After Phase 2)
**Status**: Not ready yet

**Steps**:
1. Go to Web Scraping page
2. Select project: "Construction Intelligence"
3. Enter URL and scrape

**Expected**:
- ✅ Scrapes successfully
- ✅ Saves to MinIO with path: `/department/Engineering/team/AI-Team/project/Construction-Intelligence/users/john-doe/scraped/en.wikipedia.org/Tuticorin_Airport_20251129.html`
- ✅ Document record has `project_id`, `department`, `team`, `uploaded_by` populated

### Test 3: Project-Scoped RAG Query (After Phase 3)
**Status**: Not ready yet

**Steps**:
1. Scrape document to "Construction Intelligence" project
2. Open "Construction Intelligence" project
3. Go to Chats tab, open a chat
4. Ask: "What is Tuticorin Airport?"

**Expected**:
- ✅ RAG retrieves the scraped document (project-scoped)
- ✅ Answer includes information from the scraped page
- ✅ Sources show the Wikipedia page
- ✅ If same question asked in global chat, might not retrieve it (if project filtering works)

---

## 🎯 Next Steps

### Immediate (You can test now):
1. **Test web scraping** with the Wikipedia URL
2. Verify no more database errors
3. Check if scraping completes successfully

### Short-term (I need to implement):
1. **Implement MinIO path structure** (Phase 2)
   - Update scraper service
   - Update endpoints to accept project context
   - Update document creation

2. **Implement RAG filtering** (Phase 3)
   - Add project filtering to RAG queries
   - Update chat endpoint

3. **Update UI** (Phase 4)
   - Add project selector to scraper
   - Ensure chat passes project context

---

## 📝 Files to Modify

### Backend:
1. `backend/app/services/scraper_service_enhanced.py` - MinIO path structure
2. `backend/app/api/routes/scraper_enhanced.py` - Accept project parameters
3. `backend/app/services/rag_service.py` - Project-based filtering
4. `backend/app/api/routes/rag_pipeline_routes.py` - Pass project to RAG

### Frontend:
1. `frontend/src/components/UnifiedWebScraper.tsx` - Add project selector
2. `frontend/src/components/ChatInterfaceEnhanced.tsx` - Pass projectId to queries

### Database:
1. ✅ `backend/migrations/012_add_project_based_scraping.sql` - Applied

---

## 📊 Implementation Summary

### ✅ Completed (Ready for Testing)

1. **Database Schema** ✅
   - `web_scrape_jobs` table has `project_id`, `scraped_by`, `department`, `team`
   - `documents` table has same organizational columns
   - Indexes created for efficient querying
   - Migration applied successfully

2. **Backend Service Layer** ✅
   - `scraper_service_enhanced.py` accepts project context
   - WebScrapeJob records include organizational info
   - Documents created with project/dept/team metadata
   - Bulk scraping support included

3. **Backend API Endpoints** ✅
   - `/api/v1/scraper/scrape` accepts `project_id`, `department`, `team`
   - `/api/v1/scraper/scrape/bulk` supports project context
   - Optional authentication - works with or without token
   - Smart defaults from user profile
   - Request schemas updated

4. **Frontend UI** ✅
   - WebScraper component has project dropdown
   - Loads projects from `/api/v1/projects`
   - Clean, optional UI - defaults to "Global"
   - Shows loading state and selection feedback
   - Sends project_id in scraping requests

### 🔄 Not Yet Implemented

1. **MinIO Path Hierarchy** ⏳
   - Scraped documents currently use simple paths
   - Need to implement: `/department/{dept}/team/{team}/project/{project}/users/{user}/scraped/{domain}/{filename}`
   - Database has the metadata, just need to update file storage logic

2. **RAG Project Filtering** ⏳
   - RAG service needs to filter documents by `project_id`
   - Implement 3-tier hierarchy: project+session → project → global
   - Update chat endpoints to pass `project_id` to RAG queries

### 🧪 What You Can Test Right Now

**Test 1: Basic Project-Based Scraping**
1. Go to Web Scraping tab
2. Select a project from dropdown (e.g., "Construction Intelligence")
3. Enter URL: `https://en.wikipedia.org/wiki/Tuticorin_Airport`
4. Click "Start Scraping"

**Expected Results**:
- ✅ Scraping completes successfully
- ✅ No database errors
- ✅ `web_scrape_jobs` record has `project_id` populated
- ✅ `documents` record has `project_id`, `department`, `team` populated
- ⚠️ MinIO path will still be simple (not hierarchical) - this is known
- ⚠️ RAG queries won't filter by project yet - this is next

**Test 2: Verify Database Records**
```sql
-- Check scrape job
SELECT id, url, project_id, scraped_by, department, team, status
FROM web_scrape_jobs
ORDER BY created_at DESC
LIMIT 5;

-- Check document
SELECT id, filename, project_id, department, team, source_type
FROM documents
WHERE source_type = 'scrape'
ORDER BY upload_date DESC
LIMIT 5;
```

### 🎯 Next Steps

**Priority 1: Test Current Implementation**
- Verify scraping works with project selection
- Check database records are populated correctly
- Confirm no errors or regressions

**Priority 2: RAG Integration** (Next Session)
- Update `rag_service.py` to filter by `project_id`
- Implement project-scoped retrieval
- Update chat endpoints

**Priority 3: MinIO Paths** (Optional Enhancement)
- Update `document_service.py` for hierarchical paths
- Align with file upload structure
- Test backwards compatibility

---

**Status Summary**:
- ✅ **Phase 1-4 Complete**: Database, Backend API, Service Layer, Frontend UI
- 🔄 **Phase 5 Pending**: MinIO hierarchical paths
- 🔄 **Phase 6 Pending**: RAG project filtering
- 🧪 **Ready to Test**: Basic project-based scraping workflow

**Created**: 2025-11-29 09:00
**Last Updated**: 2025-11-29 14:30
**Session**: Project-Based Scraping Implementation - Part 1
