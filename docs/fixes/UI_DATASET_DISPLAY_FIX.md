# UI Dataset Display Issue - Root Cause & Fix

**Date**: 2025-12-17
**Status**: 🟢 **ROOT CAUSE IDENTIFIED** - Schema mismatch between backend and frontend

---

## Problem

User reported: "it still shows in invalid in UI, not samples, no quality, no overview"

Despite backend database having correct validation data:
```sql
name: story7
is_valid: true
num_samples: 97
validation_errors: [helpful messages with warnings and suggestions]
sample_rows: [5 preview samples]
```

The UI displays:
- ❌ Invalid status
- ❌ No samples count
- ❌ No quality metrics
- ❌ No overview information

---

## Root Cause Analysis

### Issue 1: Missing Fields in Response Schema ⚠️

**File**: `/backend/app/schemas/finetuning_schemas.py` (Lines 514-531)

**Current Schema** (`DatasetDetailResponse`):
```python
class DatasetDetailResponse(BaseModel):
    """Detailed dataset response"""
    id: str
    name: str
    filename: str
    format_type: str
    training_objective: Optional[str] = None
    status: str                                  # ✅ preprocessing_status
    num_samples: Optional[int] = None            # ✅ Included
    file_size_bytes: Optional[int] = None
    validation_errors: Optional[List[str]] = None # ✅ Included
    meta_info: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    # ❌ MISSING: is_valid
    # ❌ MISSING: sample_rows
```

**Database Fields NOT Returned**:
1. `is_valid` - Boolean validation status (shows true/false for validity)
2. `sample_rows` - List of formatted preview samples (shows quality)

---

### Issue 2: API Endpoint Response Mapping

**File**: `/backend/app/api/routes/finetuning_routes.py` (Lines 373-388)

**Current Mapping** in `list_datasets` endpoint:
```python
DatasetDetailResponse(
    id=str(d.id),
    name=d.name,
    filename=d.filename,
    format_type=d.format_type or "",
    training_objective=None,  # Not stored in dataset model
    status=d.preprocessing_status or "pending",  # ✅ Maps correctly
    num_samples=d.num_samples,                   # ✅ Included
    file_size_bytes=d.file_size,
    validation_errors=d.validation_errors,       # ✅ Included
    meta_info={"minio_path": d.minio_path} if d.minio_path else {},
    created_at=d.uploaded_at,
    updated_at=d.uploaded_at
    # ❌ MISSING: is_valid=d.is_valid
    # ❌ MISSING: sample_rows=d.sample_rows
)
```

---

## Solution

### Step 1: Update Response Schema ✅

**File**: `/backend/app/schemas/finetuning_schemas.py`

**Add missing fields**:
```python
class DatasetDetailResponse(BaseModel):
    """Detailed dataset response"""
    id: str
    name: str
    filename: str
    format_type: str
    training_objective: Optional[str] = None
    status: str
    num_samples: Optional[int] = None
    file_size_bytes: Optional[int] = None
    validation_errors: Optional[List[str]] = None
    meta_info: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    # NEW FIELDS:
    is_valid: Optional[bool] = None              # ✅ Validation status
    sample_rows: Optional[List[str]] = None       # ✅ Quality preview

    class Config:
        orm_mode = True
        from_attributes = True
```

---

### Step 2: Update API Endpoint Response ✅

**File**: `/backend/app/api/routes/finetuning_routes.py`

**Update `list_datasets` endpoint** (Lines 373-390):
```python
DatasetDetailResponse(
    id=str(d.id),
    name=d.name,
    filename=d.filename,
    format_type=d.format_type or "",
    training_objective=None,
    status=d.preprocessing_status or "pending",
    num_samples=d.num_samples,
    file_size_bytes=d.file_size,
    validation_errors=d.validation_errors,
    meta_info={"minio_path": d.minio_path} if d.minio_path else {},
    created_at=d.uploaded_at,
    updated_at=d.uploaded_at,

    # NEW FIELDS:
    is_valid=d.is_valid,                        # ✅ Add validation status
    sample_rows=d.sample_rows                    # ✅ Add quality preview
)
```

**Update `get_dataset` endpoint** (Lines 417-430):
```python
DatasetDetailResponse(
    id=str(dataset.id),
    name=dataset.name,
    filename=dataset.filename,
    format_type=dataset.format_type or "",
    training_objective=None,
    status=dataset.preprocessing_status or "pending",
    num_samples=dataset.num_samples,
    file_size_bytes=dataset.file_size,
    validation_errors=dataset.validation_errors,
    meta_info={"minio_path": dataset.minio_path} if dataset.minio_path else {},
    created_at=dataset.uploaded_at,
    updated_at=dataset.uploaded_at,

    # NEW FIELDS:
    is_valid=dataset.is_valid,                  # ✅ Add validation status
    sample_rows=dataset.sample_rows              # ✅ Add quality preview
)
```

---

## Expected Result After Fix

### API Response (GET `/api/v1/finetuning/datasets`):
```json
{
  "datasets": [
    {
      "id": "...",
      "name": "story7",
      "filename": "story7.csv",
      "format_type": "qa",
      "status": "completed",
      "is_valid": true,                          // ✅ NOW INCLUDED
      "num_samples": 97,                         // ✅ NOW INCLUDED
      "file_size_bytes": 5432,
      "validation_errors": [                     // ✅ NOW INCLUDED
        "⚠️  Dataset is small (97 samples)",
        "✅ Auto-detected column mapping: {'question_col': 'Question', 'answer_col': 'Answer'}",
        "💡 50-100+ samples recommended for better model performance."
      ],
      "sample_rows": [                           // ✅ NOW INCLUDED
        "### Question:\nWhat festival is celebrated annually on June 23rd?\n\n### Answer:\nSão João",
        "### Question:\nWhat is another name for the Feast of St. John?\n\n### Answer:\nSão João",
        "...(3 more samples)"
      ],
      "meta_info": {"minio_path": "..."},
      "created_at": "2025-12-17T...",
      "updated_at": "2025-12-17T..."
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

---

## UI Display After Fix

With these fields returned, the frontend should now display:

### Dataset Card:
```
📄 story7
✅ Valid - 97 samples
📊 Status: completed

⚠️  Warnings/Suggestions:
  • Dataset is small (97 samples)
  • Auto-detected column mapping: Question → question_col, Answer → answer_col
  • 50-100+ samples recommended for better model performance

📝 Sample Preview:
  1. What festival is celebrated annually on June 23rd? → São João
  2. What is another name for the Feast of St. John? → São João
  ...
```

---

## Files to Modify

### 1. `/backend/app/schemas/finetuning_schemas.py`
- Add `is_valid: Optional[bool] = None` field (Line ~527)
- Add `sample_rows: Optional[List[str]] = None` field (Line ~528)

### 2. `/backend/app/api/routes/finetuning_routes.py`
- Update `list_datasets` endpoint response (Lines 373-390)
- Update `get_dataset` endpoint response (Lines 417-430)

---

## Testing Plan

### 1. Verify Schema Update:
```bash
# Check OpenAPI docs
curl http://localhost:8000/api/docs
# Look for DatasetDetailResponse schema - should include is_valid and sample_rows
```

### 2. Verify API Response:
```bash
# Get token from browser console
TOKEN=$(localStorage.getItem('access_token'))

# List datasets
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/finetuning/datasets | jq .

# Should show is_valid and sample_rows for story7
```

### 3. Verify UI Display:
- Open Fine-Tuning page
- Check that story7 shows:
  - ✅ Valid status (green checkmark)
  - 97 samples count
  - Warning messages displayed
  - Sample preview shown

---

## Related Enhancement Request

**User Question**: "in the base model in finetuning, can we have qwen 1.5B model?"

**Answer**: ✅ **Already Available!**

The Qwen 1.5B model is already included in the base models catalog:

**File**: `/backend/app/api/routes/finetuning_routes.py` (Lines 1373-1398)

```python
{
    "id": "qwen-2.5-1.5b",
    "name": "Qwen2.5-1.5B-Instruct",
    "family": "Qwen",
    "size": "1.5B",
    "contextLength": 32768,
    "license": "Apache 2.0",
    "compatibility": {
        "fullFineTune": True,   # ✅ Small enough for full FT
        "lora": True,
        "qlora": True
    },
    "vramRequirements": {
        "fullFT": 8,   # ✅ Very light on VRAM
        "lora": 4,     # ✅ Extremely light
        "qlora": 2     # ✅ Minimal VRAM usage
    },
    "trainingCost": {
        "fullFT": 0.3,  # $/hour
        "lora": 0.15,
        "qlora": 0.1    # Most economical
    },
    "recommended": True,
    "tags": ["fast", "lightweight", "multilingual", "instruct"]
}
```

**Endpoint**: `GET /api/v1/finetuning/base-models`

The model is:
- ✅ Fully supported for fine-tuning
- ✅ Marked as recommended
- ✅ Compatible with full fine-tune, LoRA, and QLoRA
- ✅ Extremely lightweight (2-8GB VRAM depending on method)
- ✅ Most economical option ($0.10/hr with QLoRA)

---

## Summary

**Problem**: UI not displaying validation results despite backend having correct data

**Root Cause**: Response schema missing `is_valid` and `sample_rows` fields

**Fix**: Add two fields to schema and update API endpoints to return them

**Impact**:
- ✅ Users will see validation status (valid/invalid)
- ✅ Users will see sample count
- ✅ Users will see quality warnings and suggestions
- ✅ Users will see sample preview
- ✅ Qwen 1.5B model is already available (no changes needed)

**Next Steps**:
1. Modify schema to add missing fields
2. Update API endpoints to return new fields
3. Restart backend
4. Test API response
5. Verify UI display

---

**End of Analysis**
