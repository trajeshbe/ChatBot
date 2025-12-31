# ORM/Database Schema Alignment Fix

**Date**: 2025-11-30
**Status**: ✅ Complete
**Type**: Critical Bug Fix

---

## Problem

The ORM models in `/backend/app/models/database.py` were **out of sync** with the actual database schema created by migrations in `/backend/migrations/000_base_schema.sql`.

This caused multiple 500 Internal Server Errors when trying to:
- Load projects
- Load documents
- View project details
- Access departments

---

## Root Cause

### Mismatch Between ORM and Database

| ORM Model (database.py) | Database Schema (000_base_schema.sql) | Status |
|-------------------------|--------------------------------------|---------|
| `meta_info` (JSON) | `metadata` (JSONB) | ❌ MISMATCH |
| `upload_date` (DateTime) | `created_at` (TIMESTAMP) | ❌ MISMATCH |
| `processed` (Boolean) | `processing_status` (VARCHAR) | ❌ MISMATCH |
| `processing_error` (Text) | `error_message` (TEXT) | ❌ MISMATCH |
| (missing) | `updated_at` (TIMESTAMP) | ❌ MISSING |

### Specific Errors Encountered

1. **Error**: `column documents.meta_info does not exist`
   - **Cause**: Database has `metadata` column, ORM tried to query `meta_info`

2. **Error**: `Attribute name 'metadata' is reserved when using the Declarative API`
   - **Cause**: Tried to use `metadata` directly as column name, but SQLAlchemy reserves this attribute

3. **Error**: `column documents.upload_date does not exist`
   - **Cause**: Database has `created_at`, ORM tried to query `upload_date`

---

## Solution Applied

### File Modified
`/backend/app/models/database.py` - Document class (lines 19-25)

### Changes Made

#### BEFORE (Mismatched Schema)
```python
class Document(Base):
    __tablename__ = "documents"

    # ... other columns ...
    source_type = Column(String(50), nullable=False)
    source_url = Column(String(1024), nullable=True)
    meta_info = Column(JSON, nullable=True)          # ❌ Column doesn't exist
    upload_date = Column(DateTime(timezone=True))    # ❌ Column doesn't exist
    processed = Column(Boolean, default=False)        # ❌ Column doesn't exist
    processing_error = Column(Text, nullable=True)    # ❌ Column doesn't exist
```

#### AFTER (Aligned Schema)
```python
class Document(Base):
    __tablename__ = "documents"

    # ... other columns ...
    source_type = Column(String(50), nullable=False)
    source_url = Column(String(1024), nullable=True)
    processing_status = Column(String(50), default='pending', nullable=True)  # ✅ Matches DB
    error_message = Column(Text, nullable=True)                                # ✅ Matches DB
    meta_info = Column('metadata', JSON, nullable=True)  # ✅ Maps to DB column, avoids reserved name
    created_at = Column(DateTime(timezone=True), server_default=func.now())    # ✅ Matches DB
    updated_at = Column(DateTime(timezone=True), server_default=func.now())    # ✅ Matches DB
```

### Key Technical Details

#### 1. SQLAlchemy Column Name Mapping
The critical fix for `metadata` was using SQLAlchemy's column name mapping:

```python
meta_info = Column('metadata', JSON, nullable=True)
```

**How it works:**
- Python code references `document.meta_info`
- SQLAlchemy generates SQL query using database column `metadata`
- Avoids SQLAlchemy's reserved `metadata` attribute

#### 2. Alignment with Base Migration

All changes were made to match `000_base_schema.sql`:

```sql
-- From migration 000_base_schema.sql (line 9-21)
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_type VARCHAR(100),
    file_size BIGINT,
    source_type VARCHAR(50) NOT NULL,
    source_url TEXT,
    processing_status VARCHAR(50) DEFAULT 'pending',  -- ✅ Now matches ORM
    error_message TEXT,                                -- ✅ Now matches ORM
    metadata JSONB,                                    -- ✅ Now mapped correctly
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,  -- ✅ Now matches ORM
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP   -- ✅ Now matches ORM
);
```

---

## Testing & Verification

### Backend Health Check
```bash
curl http://localhost:8000/health
# Response:
{
  "status": "healthy",
  "app": "Enterprise RAG Chatbot",
  "version": "1.0.0"
}
```

### Database Schema Verification
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "\d documents"
```

**Confirmed columns:**
- ✅ `metadata` (jsonb)
- ✅ `created_at` (timestamp with time zone)
- ✅ `updated_at` (timestamp with time zone)
- ✅ `processing_status` (varchar)
- ✅ `error_message` (text)

### ORM Query Test
Backend no longer throws errors when querying documents table:
- ✅ GET /api/v1/documents
- ✅ GET /api/v1/projects/{id}
- ✅ GET /api/v1/departments

---

## Impact

### Fixed Endpoints
1. **GET /api/v1/projects** - Now loads successfully
2. **GET /api/v1/departments** - Now loads successfully
3. **GET /api/v1/documents?project_id={id}** - Now loads successfully
4. **GET /api/v1/sessions/{id}/documents** - Now loads successfully

### User-Facing Fixes
- ✅ "New Project" modal loads departments dropdown
- ✅ "View All Projects" page loads projects list
- ✅ Project detail pages load files and documents
- ✅ No more 500 Internal Server Error responses

---

## Lessons Learned

### 1. Always Align ORM with Migrations
**Problem**: ORM models were written independently of migration SQL
**Solution**: ORM models should **always match** the schema created by migrations

### 2. SQLAlchemy Reserved Attributes
**Problem**: `metadata` is reserved in SQLAlchemy Declarative API
**Solution**: Use column name mapping: `Column('actual_db_column_name', Type)`

**Reserved SQLAlchemy Attributes:**
- `metadata` - Table metadata
- `__table__` - Table reference
- `__mapper__` - Mapper reference

### 3. Database Schema as Source of Truth
**Best Practice**: Migration files should be the **authoritative source** for schema, not ORM models

**Correct Workflow:**
1. Write migration SQL first
2. Apply migration to database
3. Write ORM model to **match** database schema
4. Verify ORM model matches actual columns

### 4. Testing ORM Alignment
**Recommended Tests:**
```python
def test_document_model_matches_database(db_session):
    """Verify ORM columns match actual database columns"""
    from app.models.database import Document
    from sqlalchemy import inspect

    inspector = inspect(db_session.bind)
    db_columns = {col['name'] for col in inspector.get_columns('documents')}
    orm_columns = {col.name for col in Document.__table__.columns}

    assert db_columns == orm_columns, f"Mismatch: {db_columns ^ orm_columns}"
```

---

## Related Issues

### Historical Context
This mismatch likely occurred because:
1. Original migrations created schema with `metadata`, `created_at`, `processing_status`
2. ORM model was later written/modified using different naming conventions
3. No automated tests verified ORM/DB alignment
4. Code worked initially because no queries used the mismatched columns
5. Recent features (Projects, Departments) started querying Document model
6. Queries began failing with "column does not exist" errors

### Similar Issues to Watch For
Check these models for potential mismatches:
- ✅ `DocumentChunk` - Verified aligned
- ⚠️ `Project` - Recently added foreign keys, verify alignment
- ⚠️ `User` - Uses database_enhanced.py, check alignment
- ⚠️ `ChatSession` - Uses database_enhanced.py, check alignment

---

## Recommendations

### Immediate Actions
1. ✅ **DONE**: Fixed Document model alignment
2. ✅ **DONE**: Restarted backend with corrected models
3. ✅ **DONE**: Verified backend health and endpoints

### Future Prevention
1. **Add ORM/DB Alignment Tests**: Write pytest tests that compare ORM columns to actual DB schema
2. **Update CI/CD**: Add migration validation step that checks ORM matches resulting schema
3. **Documentation**: Document column naming conventions (metadata vs meta_info)
4. **Code Review**: Require DB schema review when modifying ORM models

### Migration Best Practices
```python
# GOOD: Migration creates schema, ORM matches it
# 1. Write migration
"""
CREATE TABLE documents (
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE
);
"""

# 2. Write matching ORM
class Document(Base):
    meta_info = Column('metadata', JSON)  # Maps to metadata column
    created_at = Column(DateTime(timezone=True))
```

---

## Commit Message

```
fix: align Document ORM model with database schema

- Map meta_info attribute to 'metadata' column (reserved in SQLAlchemy)
- Change upload_date -> created_at to match migration 000_base_schema.sql
- Change processed -> processing_status to match migration
- Change processing_error -> error_message to match migration
- Add missing updated_at column

Fixes:
- "Failed to load projects" error
- "Failed to load departments" error
- 500 errors on /api/v1/documents endpoints
- Column does not exist errors in backend logs

Related: MVP-0.2, migration 000_base_schema.sql
```

---

**Status**: ✅ Complete
**Backend**: Healthy and running
**Frontend**: Ready to test - refresh browser to load projects and departments
