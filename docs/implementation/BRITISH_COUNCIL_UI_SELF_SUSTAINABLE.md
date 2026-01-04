# British Council POC - UI-Based Self-Sustainable Solution

> **Date**: 2026-01-03
> **Purpose**: Eliminate backend scripts and enable fully self-sustainable course catalog management via UI

---

## Summary of Changes

The British Council POC is now **fully self-sustainable** - no backend scripts needed! All operations (course catalog upload, chunking, embedding, recommendations) can be done through the UI.

### Before ❌

**Backend Script Required**:
```bash
# Had to run this backend script to ingest courses
docker-compose exec backend python3 -m scripts.british_council.ingest_course_catalog
```

**Limitations**:
- ❌ Required backend access
- ❌ Manual script execution
- ❌ Not user-friendly
- ❌ Technical knowledge required
- ❌ Hard to update courses

### After ✅

**UI-Based Upload**:
- ✅ Upload files directly in British Council UI
- ✅ Automatic chunking and embedding
- ✅ Metadata tagging (company, usecase)
- ✅ No backend scripts needed
- ✅ Self-sustainable solution
- ✅ User-friendly drag-and-drop

---

## Architecture Changes

### 1. Backend Metadata Support

**File**: `/backend/app/main.py`

**Upload Endpoint Extended** (lines 348-363):
```python
@app.post("/api/v1/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    project_id: Optional[str] = Form(None),
    company: Optional[str] = Form(None),  # NEW: POC company identifier
    usecase: Optional[str] = Form(None),  # NEW: POC use case identifier
    db: AsyncSession = Depends(get_db)
):
    """Upload a file for processing and associate with session

    Optional POC metadata:
    - company: Company identifier for POC filtering (e.g., 'british_council')
    - usecase: Use case identifier (e.g., 'course_recommendation')
    """
```

**Metadata Passed to Services** (lines 536-558):
```python
# Build POC metadata (for filtering in tier2/tier3 modules)
poc_metadata = {}
if company:
    poc_metadata['company'] = company
    logger.info(f"🏢 POC Company: {company}")
if usecase:
    poc_metadata['usecase'] = usecase
    logger.info(f"🎯 POC Use Case: {usecase}")

document = await document_service.upload_file(
    file_data=file_data,
    filename=file.filename,
    file_type=file.content_type,
    source_type="upload",
    db=db,
    user_id=user_id,
    department=department_name,
    team=team_name,
    project_id=project_uuid,
    minio_path=minio_path,
    user_role=current_user.role if current_user else None,
    metadata=poc_metadata if poc_metadata else None  # Pass POC metadata
)
```

**File**: `/backend/app/tier_1/document_processing/document_service.py`

**Document Service Extended** (lines 152-186):
```python
async def upload_file(
    self,
    file_data: bytes,
    filename: str,
    file_type: str,
    source_type: str = "upload",
    source_url: Optional[str] = None,
    session_id: Optional[str] = None,
    db: AsyncSession = None,
    user_id: Optional[uuid.UUID] = None,
    department: Optional[str] = None,
    team: Optional[str] = None,
    project_id: Optional[uuid.UUID] = None,
    minio_path: Optional[str] = None,
    user_role: Optional[str] = None,
    metadata: Optional[dict] = None  # NEW: Custom metadata
) -> Document:
```

**Metadata Stored in Document** (line 228):
```python
document = Document(
    id=uuid.UUID(file_id),
    filename=filename,
    file_path=object_name,
    minio_path=minio_path,
    file_type=file_type,
    file_size=len(file_data),
    source_type=source_type,
    source_url=source_url,
    processing_status='pending',
    uploaded_by=user_id,
    department=department,
    team=team,
    user_role=user_role,
    project_id=project_id,
    meta_info=metadata if metadata else {}  # Store POC metadata (company, usecase)
)
```

**Process Document Extended** (lines 300-320):
```python
async def process_document(
    self,
    document_id: uuid.UUID,
    db: AsyncSession,
    user_id: Optional[uuid.UUID] = None,
    department: Optional[str] = None,
    team: Optional[str] = None,
    project_id: Optional[uuid.UUID] = None,
    metadata: Optional[dict] = None  # NEW: Propagate to chunks
) -> List[DocumentChunk]:
```

**Metadata Propagated to Chunks** (lines 606-625):
```python
# Merge custom metadata (company, usecase) with source_info
chunk_meta_info = chunk_data['source_info'].copy()
if metadata:
    chunk_meta_info.update(metadata)  # Add company, usecase, etc.

# Create DocumentChunk record
chunk_record = DocumentChunk(
    document_id=document_id,
    chunk_index=i,
    content=chunk_data['content'],
    embedding=chunk_data.get('embedding'),
    visual_embedding=chunk_data.get('visual_embedding'),
    table_embedding=chunk_data.get('table_embedding'),
    code_embedding=chunk_data.get('code_embedding'),
    numerical_embedding=chunk_data.get('numerical_embedding'),
    embedding_strategy=embedding_strategy,
    embedding_metadata=chunk_data['embedding_metadata'],
    meta_info=chunk_meta_info,  # Include POC metadata
    project_id=project_id,
    uploaded_by=user_id,
    department=department,
    team=team
)
```

### 2. Frontend FileUpload Component Extended

**File**: `/frontend/src/components/FileUpload.tsx`

**Metadata Prop Added** (line 36):
```typescript
interface FileUploadProps {
  currentUser?: {
    id: string
    username: string
    role: string
    department_id?: string
    team_id?: string
  }
  sessionId?: string
  projectId?: string
  onUploadComplete?: () => void
  hideProjectSelector?: boolean
  compact?: boolean
  metadata?: Record<string, string>  // NEW: Custom metadata (company, usecase for POCs)
}
```

**Metadata Appended to FormData** (lines 126-132):
```typescript
// ✅ Append custom metadata (company, usecase for POCs)
if (metadata) {
  Object.entries(metadata).forEach(([key, value]) => {
    formData.append(key, value)
    console.log(`🏷️ [FileUpload] Metadata: ${key}=${value}`)
  })
}
```

### 3. British Council UI Integration

**File**: `/frontend/src/components/BritishCouncilRecommender.tsx`

**FileUpload Imported** (line 5):
```typescript
import FileUpload from './FileUpload'
```

**Upload Section Added** (lines 144-161):
```typescript
{/* Course Catalog Upload Section */}
<div className="bg-white rounded-xl shadow-sm p-6 mb-6">
  <h2 className="text-xl font-semibold text-slate-800 mb-2">
    📚 Upload Course Catalog
  </h2>
  <p className="text-sm text-slate-600 mb-4">
    Upload course catalog files (JSON, CSV, TXT, PDF) to make them searchable for recommendations.
    Files will be automatically chunked and embedded into the vector database.
  </p>
  <FileUpload
    hideProjectSelector={true}
    compact={true}
    metadata={{
      company: 'british_council',
      usecase: 'course_recommendation'
    }}
  />
</div>
```

---

## Data Flow

### Upload → Storage → Embedding → Retrieval

```
User uploads file via UI
  ↓
FileUpload component appends metadata:
  - company: 'british_council'
  - usecase: 'course_recommendation'
  ↓
POST /api/v1/upload with FormData:
  - file: <binary>
  - company: 'british_council'
  - usecase: 'course_recommendation'
  ↓
main.py:upload_file() builds poc_metadata dict
  ↓
document_service.upload_file(metadata=poc_metadata)
  ↓
Document created in PostgreSQL:
  meta_info = {"company": "british_council", "usecase": "course_recommendation"}
  ↓
document_service.process_document(metadata=poc_metadata)
  ↓
Document chunked (Docling + Hybrid Extraction)
  ↓
Chunks created with embeddings:
  meta_info = {
    "source": "filename.json",
    "source_type": "upload",
    "company": "british_council",      ← POC metadata
    "usecase": "course_recommendation"  ← POC metadata
  }
  embedding = [0.123, 0.456, ...]  ← 384-dim vector
  ↓
Stored in PostgreSQL document_chunks table
  ↓
Searchable via vector search with metadata filtering:
  WHERE meta_info->>'company' = 'british_council'
    AND meta_info->>'usecase' = 'course_recommendation'
  ORDER BY embedding <=> query_embedding
```

---

## User Workflow

### 1. Upload Course Catalog

```
1. Open British Council POC at http://localhost:3001
2. Navigate to "British Council Course Recommender" section
3. See "📚 Upload Course Catalog" section
4. Drag-and-drop or click to upload course files:
   - Supported formats: JSON, CSV, TXT, PDF, DOCX
   - Example: course_catalog_sample.json
5. File automatically uploads with metadata:
   - company='british_council'
   - usecase='course_recommendation'
6. Backend processes file:
   - Stores in MinIO (object storage)
   - Creates document record in PostgreSQL
   - Chunks document (intelligent chunking)
   - Generates embeddings (384-dim vectors)
   - Stores chunks with embeddings in PostgreSQL
7. Upload complete! Courses now searchable
```

### 2. Get Course Recommendations

```
1. In "Tell us about your learning goals" section
2. Enter your profile:
   Example: "I'm a software engineer looking to improve my business English.
            I have intermediate level English (B1) and prefer online courses
            on weekends. I want to advance my career in international companies."
3. Click "🎯 Get Recommendations"
4. System:
   a. Extracts structured profile using LLM (ProfileAnalyzerService)
   b. Searches vector DB with metadata filtering:
      - company='british_council'
      - usecase='course_recommendation'
   c. Hybrid scoring (60% semantic + 40% profile match)
   d. Returns top 10 recommendations
5. View personalized recommendations with match scores
```

---

## Testing the Solution

### Test 1: Upload Course Catalog via UI

```
1. Open http://localhost:3001
2. Navigate to British Council POC
3. Upload sample course file:
   - File: sample_data/tier3_customer_pocs/british_council/course_catalog_sample.json
4. Verify upload success:
   - Check UI shows "✅ Upload successful"
   - Check backend logs:
     docker-compose logs -f backend | grep "POC Company"
     # Should see: 🏢 POC Company: british_council
     # Should see: 🎯 POC Use Case: course_recommendation
5. Verify document in database:
   docker-compose exec postgres psql -U postgres -d ragchatbot -c "
     SELECT id, filename, meta_info
     FROM documents
     WHERE meta_info->>'company' = 'british_council'
   "
6. Verify chunks in database:
   docker-compose exec postgres psql -U postgres -d ragchatbot -c "
     SELECT chunk_index, meta_info, embedding IS NOT NULL as has_embedding
     FROM document_chunks
     WHERE meta_info->>'company' = 'british_council'
     LIMIT 5
   "
```

### Test 2: End-to-End Recommendation Flow

```
1. Upload course catalog (Test 1)
2. Enter user profile:
   "I'm a software engineer wanting to improve my business English"
3. Click "🎯 Get Recommendations"
4. Verify results:
   - Should return 5-10 course recommendations
   - Each course should have:
     - course_name
     - description
     - match_score (0.0-1.0)
     - semantic_score
     - profile_score
     - reasons array
5. Check backend logs for vector search:
   docker-compose logs -f backend | grep "direct_vector_search"
   # Should see: Company filter: british_council
   # Should see: Use case filter: course_recommendation
   # Should see: Found X candidates
```

### Test 3: Multiple File Uploads

```
1. Upload course_catalog_sample.json
2. Upload another course file (e.g., additional_courses.txt)
3. Upload PDF course brochure
4. All files tagged with:
   - company='british_council'
   - usecase='course_recommendation'
5. Verify all files searchable together:
   - Get recommendations should search across all uploaded files
   - Vector search filters by metadata (company + usecase)
```

---

## Benefits Summary

### For Users

1. **No Backend Access Needed**: Upload courses directly in UI
2. **Drag-and-Drop**: Easy file upload (JSON, CSV, TXT, PDF)
3. **Automatic Processing**: Chunking and embedding handled automatically
4. **Real-Time**: Courses available for recommendations immediately after upload
5. **Self-Sustainable**: No technical knowledge required
6. **Update Anytime**: Upload new course files to refresh catalog

### For Developers

1. **Reusable Pattern**: Same metadata approach for all POCs
2. **Centralized Upload**: Single endpoint handles all POC uploads
3. **Metadata Filtering**: Efficient vector search with metadata constraints
4. **No Script Maintenance**: Eliminated backend ingestion scripts
5. **Scalable**: Supports unlimited POCs with different metadata tags

### For System

1. **Metadata Propagation**: Document → Chunks (seamless)
2. **Vector Search Optimization**: Filter by metadata before vector comparison
3. **Storage Efficiency**: Single upload endpoint for all POCs
4. **Consistent UX**: Same upload experience across all POCs
5. **Database Integrity**: Metadata stored in JSONB, searchable with `->>` operator

---

## Comparison: Before vs After

| Aspect | Before (Backend Scripts) | After (UI Upload) |
|--------|-------------------------|-------------------|
| **Upload Method** | ❌ Backend script | ✅ UI drag-and-drop |
| **User Access** | ❌ Requires backend SSH | ✅ Browser only |
| **Technical Skills** | ❌ Python, Docker, CLI | ✅ None (point-and-click) |
| **File Formats** | ❌ JSON only (hardcoded) | ✅ JSON, CSV, TXT, PDF, DOCX |
| **Metadata Tagging** | ❌ Hardcoded in script | ✅ Automatic (UI passes metadata) |
| **Update Process** | ❌ Re-run script | ✅ Upload new file |
| **Self-Sustainable** | ❌ No | ✅ Yes |
| **Chunking** | ❌ Manual (script) | ✅ Automatic (Docling + Hybrid) |
| **Embedding** | ❌ Manual (script) | ✅ Automatic (Multi-Analyzer) |
| **Searchability** | ❌ After script run | ✅ Immediate after upload |

---

## POC Metadata Structure

### Document Level

**Table**: `documents`
**Column**: `meta_info` (JSONB)

```json
{
  "company": "british_council",
  "usecase": "course_recommendation"
}
```

### Chunk Level

**Table**: `document_chunks`
**Column**: `meta_info` (JSONB)

```json
{
  "source": "course_catalog_sample.json",
  "source_type": "upload",
  "company": "british_council",
  "usecase": "course_recommendation"
}
```

### Vector Search with Metadata Filtering

**File**: `backend/app/services/british_council/course_recommender.py` (lines 150-180)

```python
stmt = (
    select(
        DocumentChunk,
        (1 - DocumentChunk.embedding.op('<=>', return_type=Float)(
            literal_column(f"'{embedding_str}'::vector")
        )).label('similarity')
    )
    .join(Document, DocumentChunk.document_id == Document.id)
    .where(
        and_(
            DocumentChunk.embedding.isnot(None),
            # Metadata filtering using ->> operator for JSONB text extraction
            text("documents.meta_info->>'company' = :company").bindparams(company='british_council'),
            text("documents.meta_info->>'usecase' = :usecase").bindparams(usecase='course_recommendation')
        )
    )
    .order_by(desc('similarity'))
    .limit(top_k)
)
```

**Why `->>` operator?**
- `->>` extracts text value without quotes
- Avoids JSONB value quote mismatch: `"british_council"` vs `'british_council'`
- Ensures proper string comparison in WHERE clause

---

## Extending to Other POCs

### Template for New POC

1. **Add FileUpload to POC Component**:
```typescript
// In your POC component (e.g., CRUMiningIntelligence.tsx)
import FileUpload from './FileUpload'

// Add upload section
<FileUpload
  hideProjectSelector={true}
  compact={true}
  metadata={{
    company: 'cru',
    usecase: 'mining_intelligence'
  }}
/>
```

2. **Update Vector Search in Service**:
```python
# In your POC service (e.g., cru_query_service.py)
.where(
    and_(
        DocumentChunk.embedding.isnot(None),
        text("documents.meta_info->>'company' = :company").bindparams(company='cru'),
        text("documents.meta_info->>'usecase' = :usecase").bindparams(usecase='mining_intelligence')
    )
)
```

3. **No Backend Changes Needed**:
- Upload endpoint already supports metadata
- Document service already propagates metadata
- Just pass different metadata values from UI

---

## File Format Examples

### JSON Course Catalog

```json
[
  {
    "course_id": "BC-001",
    "course_name": "Business English Mastery",
    "description": "Advanced business communication skills",
    "level": "intermediate",
    "format": "online",
    "duration": "8 weeks",
    "topics": ["business writing", "presentations", "negotiations"]
  }
]
```

### CSV Course Catalog

```csv
course_id,course_name,description,level,format,duration
BC-001,Business English Mastery,Advanced business communication,intermediate,online,8 weeks
BC-002,IELTS Preparation,Prepare for IELTS exam,advanced,hybrid,12 weeks
```

### TXT Course Catalog

```
Course: Business English Mastery
Level: Intermediate
Format: Online
Description: Develop advanced business communication skills including
             writing, presentations, and negotiations.

Course: IELTS Preparation
Level: Advanced
Format: Hybrid
Description: Comprehensive IELTS exam preparation with practice tests.
```

All formats supported! Backend automatically:
1. Extracts text (Docling + Hybrid Extraction)
2. Chunks intelligently
3. Generates embeddings
4. Stores with metadata

---

## Troubleshooting

### Issue 1: Upload Fails

**Symptoms**: File upload shows error

**Check**:
```bash
# Check backend logs
docker-compose logs -f backend | grep "upload"

# Common errors:
# - "MinIO connection failed" → Check MinIO is running
# - "Embedding service unavailable" → Check embedding service
```

**Solution**:
```bash
# Restart services
docker-compose restart backend minio
```

### Issue 2: No Recommendations Returned

**Symptoms**: Upload succeeds but recommendations return 0 results

**Check**:
```bash
# Verify chunks with metadata in database
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
  SELECT COUNT(*) as chunk_count,
         COUNT(embedding) as embedding_count
  FROM document_chunks dc
  JOIN documents d ON dc.document_id = d.id
  WHERE d.meta_info->>'company' = 'british_council'
    AND d.meta_info->>'usecase' = 'course_recommendation'
"
```

**Solution**:
- If chunk_count = 0: File didn't process. Check backend logs
- If embedding_count = 0: Embeddings failed. Check embedding service logs
- If both > 0: Check vector search query in course_recommender.py

### Issue 3: Metadata Not Stored

**Symptoms**: Chunks created but no metadata

**Check**:
```bash
# Check document metadata
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
  SELECT filename, meta_info
  FROM documents
  WHERE meta_info IS NOT NULL
  ORDER BY created_at DESC
  LIMIT 5
"
```

**Solution**:
- Verify FileUpload passes metadata prop
- Check browser console for metadata logging: `🏷️ [FileUpload] Metadata: company=british_council`
- Check backend logs for metadata reception: `🏢 POC Company: british_council`

---

## Performance Considerations

### Vector Search Optimization

**Index**: Ensure pgvector IVFFlat index exists
```sql
CREATE INDEX IF NOT EXISTS idx_chunks_embedding
ON document_chunks
USING ivfflat (embedding vector_cosine_ops);
```

**Query Plan**: Check if index is used
```sql
EXPLAIN ANALYZE
SELECT ...
FROM document_chunks dc
JOIN documents d ON dc.document_id = d.id
WHERE d.meta_info->>'company' = 'british_council'
  AND dc.embedding <=> '[...]'::vector
ORDER BY embedding <=> '[...]'::vector
LIMIT 10;
```

**Expected**: Index Scan using idx_chunks_embedding

### Metadata Filtering First

**Efficient**:
```python
.where(
    and_(
        text("documents.meta_info->>'company' = :company"),  # Filter first
        DocumentChunk.embedding.isnot(None),
        DocumentChunk.embedding.op('<=>')(query_embedding) < 0.3  # Then vector compare
    )
)
```

**Inefficient**:
```python
.where(
    DocumentChunk.embedding.op('<=>')(query_embedding) < 0.3  # Vector compare ALL chunks
)
# Then filter by metadata in Python → SLOW
```

---

## Next Steps

1. ✅ **COMPLETED**: Backend metadata support (company, usecase)
2. ✅ **COMPLETED**: Frontend FileUpload component extended
3. ✅ **COMPLETED**: British Council UI integration
4. ✅ **COMPLETED**: Restart containers
5. **TODO**: User testing (upload → recommend flow)
6. **TODO**: Extend to other POCs (CRU, GT Motive, Solera)
7. **TODO**: Add file type validation UI (optional)
8. **TODO**: Add progress indicators for chunking/embedding (optional)

---

## Related Documentation

- `MODEL_SELECTOR_INTEGRATION_IN_POC_CONFIG.md` - ModelSelector in Module Configuration
- `BRITISH_COUNCIL_MODULE_CONFIG_INTEGRATION.md` - Module config architecture
- `BRITISH_COUNCIL_RAG_ANALYSIS.md` - Direct vector search implementation
- `POC_IMPLEMENTATION_COMPLETE.md` - All POC implementations

---

**End of Document**
