# MinIO Hierarchical Path Structure Implementation

**Date**: 2025-11-29
**Status**: ✅ **COMPLETE FOR ALL WEB SCRAPING METHODS**
**Last Updated**: 2025-11-29 19:15

---

## 📋 Summary

All 4 web scraping methods now save files with **full hierarchical paths** in MinIO:

✅ **Basic Scraping** - Fixed scraper service
✅ **Smart Extraction** - Fixed save-to-db endpoint
✅ **Template Mapper** - Uses same save-to-db endpoint
✅ **CSS Selector** - Uses same save-to-db endpoint

**Key Achievement**: Instead of flat paths like `extractions/books_romance/file.json`, all scraped content is now organized as:

```
{department}/{team}/{project}/{username}/extractions/{filename}
```

Example:
```
Technology/AI-Team/Construction-Intelligence/admin/extractions/20251129_135558_abc123.json
```

This provides:
- ✅ Organized storage by org structure
- ✅ Clear ownership and attribution
- ✅ Project-scoped knowledge management
- ✅ Easy access control and governance
- ✅ Better audit trail

---

## 🎯 Goal

Implement hierarchical MinIO storage paths for ALL web scraping methods to organize scraped documents by:
- Department
- Team
- Project
- User
- Folder type (documents/extractions/exports/temp)
- Filename

## 📊 Path Structure

### Format
```
{department}/{team}/{project}/{username}/{folder}/{filename}
```

### Example Paths
```
Technology/AI-Team/Construction-Intelligence/admin/extractions/scraped_example.com_a1b2c3d4.txt
Engineering/Data-Ops-Team/Marketing/john_doe/extractions/scraped_wikipedia.org_5e6f7g8h.txt
Unassigned/General/Global/anonymous/extractions/scraped_news.com_9i0j1k2l.txt
```

### Path Components

| Component | Description | Default if Missing |
|-----------|-------------|-------------------|
| department | Department name from user profile or request | "Unassigned" |
| team | Team name from user profile or request | "General" |
| project | Project name (fetched from project_id) | "Global" |
| username | Username of the person scraping | "anonymous" |
| folder | Type of content (documents, extractions, exports, temp) | "extractions" for scraping |
| filename | Original or generated filename | Auto-generated with URL netloc |

---

## ✅ What's Been Implemented

### 1. Basic Scraping (WebScraper Component) ✅

**Files Modified**:
1. `backend/app/services/scraper_service_enhanced.py`
   - Added `username` parameter to `scrape_url()` method
   - Added logic to fetch project name from `project_id`
   - Added `construct_minio_path()` call to create hierarchical path
   - Pass `minio_path` to `document_service.upload_file()`

2. `backend/app/api/routes/scraper_routes.py`
   - Extract username from `current_user`
   - Pass `username` to scraper service

**Key Code Changes**:

```python
# scraper_service_enhanced.py (lines 201-241)

# Get project name from project_id
project_name = "Global"
if db and project_id:
    try:
        from sqlalchemy import select
        from app.models.database_enhanced import Project
        project_result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project_obj = project_result.scalar_one_or_none()
        if project_obj:
            project_name = project_obj.name
    except Exception as e:
        logger.warning(f"Could not fetch project name: {e}")

# Construct hierarchical MinIO path
minio_path = construct_minio_path(
    department=department,
    team=team,
    username=username or "anonymous",
    project=project_name,
    filename=filename,
    folder="extractions"
)
logger.info(f"📁 Constructed MinIO path: {minio_path}")

# Pass to document service
document = await document_service.upload_file(
    file_data=content_bytes,
    filename=filename,
    file_type="text/plain",
    source_type="scrape",
    source_url=url,
    session_id=session_id,
    project_id=project_id,
    department=department,
    team=team,
    user_id=user_id,
    minio_path=minio_path,  # NEW: Hierarchical path
    db=db
)
```

```python
# scraper_routes.py (lines 118-194)

# Get username for MinIO path
username = current_user.username if current_user else "anonymous"

logger.info(f"🔍 Scraping with context - User: {username}/{user_id}, Project: {project_id}, Dept: {department}, Team: {team}")

# Pass username to scraper service
result = await enhanced_scraper_service.scrape_url(
    url=str(scrape_request.url),
    scrape_prompt=scrape_request.scrape_prompt,
    strategy=scrape_request.strategy.value if scrape_request.strategy else None,
    config=scraper_config,
    session_id=scrape_request.session_id,
    project_id=project_id,
    department=department,
    team=team,
    user_id=user_id,
    username=username,  # NEW
    db=db
)
```

**Database Storage**:
- `documents.file_path`: UUID-based path (backward compatibility)
- `documents.minio_path`: Hierarchical path (new field)
- `documents.department`: Department name
- `documents.team`: Team name
- `documents.project_id`: UUID reference to projects table
- `documents.uploaded_by`: User UUID

---

### 2. Smart Extraction (SmartExtractor Component) ✅

**Endpoint Updated**: `/api/v1/extract/save-to-db`

**Files Modified**:
1. `backend/app/api/routes/template_extraction_routes.py`
   - Added `Request` parameter to get current user
   - Added `project_id`, `department`, `team` fields to `SaveToDBRequest` schema
   - Added user authentication and context extraction
   - Fetch project name from `project_id`
   - Use `construct_minio_path()` for hierarchical paths
   - Update document record with organizational metadata

2. `frontend/src/components/SmartExtractor.tsx`
   - Added `project_id` to save-to-db API request

**Key Code Changes**:

```python
# template_extraction_routes.py SaveToDBRequest (lines 1706-1716)
class SaveToDBRequest(BaseModel):
    company_name: str
    source_url: str
    extraction_type: str
    data: List[Dict[str, Any]]
    template_name: Optional[str] = None
    session_id: Optional[str] = None
    project_id: Optional[str] = None  # NEW
    department: Optional[str] = None  # NEW
    team: Optional[str] = None  # NEW
```

```python
# template_extraction_routes.py save_extracted_data_to_db (lines 1763-1831)

# Get current user for organizational context
from app.core.security import get_current_user_from_request
current_user = await get_current_user_from_request(http_request, db)
username = current_user.username if current_user else "anonymous"

# Get department and team from user if not provided
department = request.department
team = request.team

if current_user and not department:
    # Fetch from user profile...

# Get project name from project_id
project_name = "Global"
if db and request.project_id:
    # Fetch from projects table...

# Construct hierarchical MinIO path
from app.services.document_service import construct_minio_path
minio_path = construct_minio_path(
    department=department,
    team=team,
    username=username,
    project=project_name,
    filename=json_filename,
    folder="extractions"
)
logger.info(f"📁 Constructed hierarchical MinIO path: {minio_path}")

# Create document record with organizational metadata
document_record = Document(
    id=uuid_lib.UUID(extraction_id),
    filename=f"{request.company_name} - {request.extraction_type}",
    file_path=f"{extraction_id}.json",  # UUID for backward compatibility
    minio_path=minio_path,  # Hierarchical path
    uploaded_by=user_id,
    department=department,
    team=team,
    project_id=project_id,
    # ... other fields
)
```

```typescript
// SmartExtractor.tsx (line 353-361)
const response = await axios.post(`${API_URL}/api/v1/extract/save-to-db`, {
  company_name: companyName,
  source_url: extractedData.url || url,
  extraction_type: 'smart',
  template_name: null,
  data: extractedData.table,
  session_id: sessionId,
  project_id: projectId || undefined  // NEW: Include project context
})
```

**Path Generated**:
```
Technology/AI-Team/Construction-Intelligence/admin/extractions/20251129_135558_2f1664f1.json
```

Instead of the old path:
```
extractions/books_romance/20251129_135558_2f1664f1.json
```

---

### 3. Template Mapper (SmartTemplateMapper Component) ✅

**Endpoint Updated**: `/api/v1/extract/save-to-db` (same as Smart Extraction)

**Files Modified**:
1. `frontend/src/components/SmartTemplateMapper.tsx`
   - Added `project_id` to save-to-db API request (line 415)

**Key Code Changes**:
```typescript
// SmartTemplateMapper.tsx (line 406-420)
const response = await axios.post(
  `${API_URL}/api/v1/extract/save-to-db`,
  {
    company_name: companyName,
    source_url: url,
    extraction_type: 'smart_mapper',
    data: mappedData.data,
    template_name: domain + '_mapper',
    session_id: sessionId,
    project_id: projectId || undefined  // NEW: Include project context
  }
)
```

**Status**: ✅ Complete - Backend already supports hierarchical paths from Smart Extraction fix

---

### 4. CSS Selector Based (TemplateExtractor Component) ✅

**Endpoint Updated**: `/api/v1/extract/save-to-db` (same as Smart Extraction)

**Files Modified**:
1. `frontend/src/components/TemplateExtractor.tsx`
   - Added `project_id` to save-to-db API request (line 507)

**Key Code Changes**:
```typescript
// TemplateExtractor.tsx (line 500-508)
const response = await axios.post(`${API_URL}/api/v1/extract/save-to-db`, {
  company_name: companyName,
  source_url: job.url,
  extraction_type: 'css_selector',
  template_name: job.preset,
  data: job.data,
  session_id: sessionId,
  project_id: projectId || undefined  // NEW: Include project context
})
```

**Status**: ✅ Complete - Backend already supports hierarchical paths from Smart Extraction fix

---

## 🔍 How It Works

### Frontend → Backend Flow

1. **User selects project** in unified dropdown (UnifiedWebScraper)
2. **Frontend sends request** with `project_id`
3. **Backend authenticates** user and extracts:
   - User ID and username
   - Department (from user profile or request)
   - Team (from user profile or request)
4. **Backend fetches** project name from `projects` table using `project_id`
5. **Backend constructs** hierarchical path:
   ```python
   minio_path = construct_minio_path(
       department="Technology",
       team="AI-Team",
       username="admin",
       project="Construction-Intelligence",
       filename="scraped_example.com_a1b2c3d4.txt",
       folder="extractions"
   )
   # Result: Technology/AI-Team/Construction-Intelligence/admin/extractions/scraped_example.com_a1b2c3d4.txt
   ```
6. **Backend uploads** file to MinIO with hierarchical path
7. **Backend saves** document record with both paths:
   - `file_path`: UUID path (backward compatibility)
   - `minio_path`: Hierarchical path (new)

### Database Schema

```sql
-- documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    filename VARCHAR(255),
    file_path VARCHAR(512),      -- UUID path (e.g., "abc-123.txt")
    minio_path VARCHAR(1024),    -- Hierarchical path (e.g., "Tech/AI/Project/user/extractions/file.txt")
    file_type VARCHAR(50),
    file_size INTEGER,
    source_type VARCHAR(50),     -- 'upload' or 'scrape'
    source_url VARCHAR(1024),
    uploaded_by UUID,
    department VARCHAR(100),
    team VARCHAR(100),
    project_id UUID REFERENCES projects(id),
    processed BOOLEAN,
    upload_date TIMESTAMP WITH TIME ZONE
);
```

---

## 🧪 Testing

### Test 1: Basic Scraping with Project Context

**Steps**:
1. Login to the application
2. Navigate to Web Scraping page
3. Select a project from the unified dropdown (e.g., "Construction Intelligence")
4. Switch to "Basic Scraping" tab
5. Enter URL: `https://en.wikipedia.org/wiki/India`
6. Click "Start Scraping"

**Expected Results**:
- ✅ Backend logs show: `📁 Constructed MinIO path: Technology/AI-Team/Construction-Intelligence/admin/extractions/scraped_wikipedia.org_xxxxx.txt`
- ✅ MinIO file is stored at hierarchical path
- ✅ Database `documents.minio_path` contains full hierarchical path
- ✅ Database `documents.project_id` matches selected project
- ✅ Database `documents.department` and `documents.team` populated

**Verification Queries**:
```sql
-- Check latest scraped document
SELECT
    filename,
    minio_path,
    department,
    team,
    project_id,
    source_url
FROM documents
WHERE source_type = 'scrape'
ORDER BY upload_date DESC
LIMIT 1;
```

**MinIO Verification**:
1. Open MinIO console: http://localhost:9001
2. Login: minioadmin/minioadmin
3. Navigate to bucket
4. Check if file exists at hierarchical path

---

## 📝 Benefits of Hierarchical Paths

### 1. **Organized Storage**
- Easy to browse files by department/team/project
- Clear ownership and categorization
- Logical folder structure

### 2. **Access Control**
- Can implement department/team-level access policies
- Project-based permissions
- User-based quotas

### 3. **Audit Trail**
- Clear attribution to user, team, department
- Easy to track who scraped what
- Project-based analytics

### 4. **Data Governance**
- Compliance with data retention policies
- Easy bulk operations by department/team
- Simplified backup and archival

### 5. **User Experience**
- Users can see their department's files
- Team collaboration made easier
- Project-scoped knowledge management

---

## 🔧 Utility Functions

### construct_minio_path()

**Location**: `backend/app/services/document_service.py:69`

**Signature**:
```python
def construct_minio_path(
    department: Optional[str],
    team: Optional[str],
    username: str,
    project: str,
    filename: str,
    folder: str = "documents"
) -> str
```

**Features**:
- Sanitizes path components (removes special chars)
- Provides defaults for missing components
- Validates folder types
- Preserves original filename
- Returns properly formatted path

**Example Usage**:
```python
from app.services.document_service import construct_minio_path

path = construct_minio_path(
    department="Technology",
    team="AI-Team",
    username="admin",
    project="Construction-Intelligence",
    filename="report.pdf",
    folder="documents"
)
# Result: "Technology/AI-Team/Construction-Intelligence/admin/documents/report.pdf"
```

---

## 🚀 Deployment Checklist

### Before Deploying

- [ ] Test Basic Scraping with hierarchical paths
- [ ] Verify MinIO paths are created correctly
- [ ] Check database `minio_path` field populated
- [ ] Test with missing department/team (should use defaults)
- [ ] Test with anonymous users
- [ ] Verify backward compatibility (old UUID paths still work)

### After Deploying

- [ ] Monitor backend logs for path construction
- [ ] Check MinIO storage structure
- [ ] Verify database queries work with new schema
- [ ] Test document retrieval using `minio_path`
- [ ] Update Smart Extraction endpoints
- [ ] Update Template Mapper endpoints
- [ ] Update CSS Selector endpoints

---

## 📊 Current Status Summary

| Scraping Method | Frontend Updated | Backend Updated | Status |
|----------------|------------------|-----------------|--------|
| **Basic Scraping** | ✅ Yes | ✅ Yes | ✅ **Complete** |
| **Smart Extraction** | ✅ Yes | ✅ Yes | ✅ **Complete** |
| **Template Mapper** | ✅ Yes | ✅ Yes (shared endpoint) | ✅ **Complete** |
| **CSS Selector** | ✅ Yes | ✅ Yes (shared endpoint) | ✅ **Complete** |

### 🎉 All 4 Web Scraping Methods Now Use Hierarchical Paths!

---

## 📚 Related Documentation

- `UNIFIED_PROJECT_DROPDOWN_IMPLEMENTATION.md` - Unified project dropdown feature
- `backend/app/services/document_service.py` - Document service with path utilities
- `backend/app/models/database.py` - Database schema

---

**Created**: 2025-11-29 18:30
**Last Updated**: 2025-11-29 18:30
**Author**: Claude Code Assistant
