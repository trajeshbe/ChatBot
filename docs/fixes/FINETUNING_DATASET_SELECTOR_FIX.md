# Fine-Tuning Dataset Selector Fix

**Date**: 2025-12-17
**Issue**: Dataset dropdown in Training Jobs is not selectable
**Root Cause**: Missing authentication headers in API calls
**Status**: ⚠️ BUG IDENTIFIED - FIX NEEDED

---

## Problem

When creating a new training job in the Fine-Tuning UI, the **Dataset** dropdown appears but shows no options (or shows "Select Dataset" but nothing else).

### User Report:
> "in the Fine-tuning Jobs -> Training jobs -> Dataset -> isn't selectable .. shouldn't it be a file picker which points to the uploaded dataset from minio?"

### What The User Expects: ✅
- Dropdown showing all uploaded datasets (test, test2, test3, test4, test5)
- Ability to select a dataset for training
- Display: "test4 (pending samples)" etc.

### What Actually Happens: ❌
- Dropdown appears empty or only shows "Select Dataset"
- No datasets loaded from backend
- Cannot select any dataset

---

## Root Cause Analysis

### API Call (Frontend - JobManager.tsx:116-126):
```typescript
const loadDatasets = async () => {
  try {
    const response = await fetch(`${API_BASE}/api/v1/finetuning/datasets`)  // ❌ NO AUTH HEADERS
    if (response.ok) {
      const data = await response.json()
      setDatasets(data.datasets || [])
    }
  } catch (error) {
    console.error('Error loading datasets:', error)
  }
}
```

### Backend Response:
```json
HTTP/1.1 401 Unauthorized
{
  "detail": "Not authenticated"
}
```

### Backend Logs:
```
2025-12-17 05:58:42 - AUDIT_EVENT: {
  "method": "GET",
  "path": "/api/v1/finetuning/datasets",
  "status_code": 401,  // ❌ UNAUTHORIZED
  "user_id": null,     // ❌ NO USER
  "error": null
}
```

### Database Check:
```sql
SELECT id, name, filename, minio_path FROM finetuning_datasets ORDER BY uploaded_at DESC LIMIT 5;
```

**Result**: ✅ 5 datasets exist in database (test, test2, test3, test4, test5)

**Conclusion**: The data exists, but the frontend can't access it due to missing authentication.

---

## Comparison with Working Components

### ❌ JobManager.tsx (BROKEN - No Auth):
```typescript
// Line 105 - Load jobs
const response = await fetch(`${API_BASE}/api/v1/finetuning/jobs`)

// Line 118 - Load datasets
const response = await fetch(`${API_BASE}/api/v1/finetuning/datasets`)

// Line 179 - Get recommendations
const recommendResponse = await fetch(...)

// Line 202 - Create job
const response = await fetch(`${API_BASE}/api/v1/finetuning/jobs`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },  // ❌ Missing Authorization
  body: JSON.stringify(payload)
})
```

### ✅ ChatHistory.tsx (WORKING - With Auth):
```typescript
const token = localStorage.getItem('token')

const response = await fetch(url, {
  headers: {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,  // ✅ HAS AUTH
  }
})
```

### ✅ AgentTaskMonitor.tsx (WORKING - With Auth):
```typescript
const token = localStorage.getItem('token')
const headers = token ? { Authorization: `Bearer ${token}` } : {}

const response = await fetch(url, { headers })
```

---

## The Fix

### Step 1: Add Token Retrieval at Component Level

Add near the top of `loadDatasets()` and all other API functions:

```typescript
const loadDatasets = async () => {
  try {
    // ✅ ADD THIS
    const token = localStorage.getItem('token')

    const response = await fetch(`${API_BASE}/api/v1/finetuning/datasets`, {
      // ✅ ADD THIS
      headers: token ? {
        Authorization: `Bearer ${token}`
      } : {}
    })

    if (response.ok) {
      const data = await response.json()
      setDatasets(data.datasets || [])
    }
  } catch (error) {
    console.error('Error loading datasets:', error)
  }
}
```

### Step 2: Fix ALL Fetch Calls

Update **all 6 fetch calls** in `JobManager.tsx`:

#### 1. `loadJobs()` (Line 105):
```typescript
const loadJobs = async () => {
  setLoading(true)
  try {
    const token = localStorage.getItem('token')  // ✅ ADD
    const response = await fetch(`${API_BASE}/api/v1/finetuning/jobs`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}  // ✅ ADD
    })
    if (response.ok) {
      const data = await response.json()
      setJobs(data.jobs || [])
    }
  } catch (error) {
    console.error('Error loading jobs:', error)
  }
  setLoading(false)
}
```

#### 2. `loadDatasets()` (Line 118):
```typescript
const loadDatasets = async () => {
  try {
    const token = localStorage.getItem('token')  // ✅ ADD
    const response = await fetch(`${API_BASE}/api/v1/finetuning/datasets`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}  // ✅ ADD
    })
    if (response.ok) {
      const data = await response.json()
      setDatasets(data.datasets || [])
    }
  } catch (error) {
    console.error('Error loading datasets:', error)
  }
}
```

#### 3. `createJob()` - Recommendation Call (Line 179):
```typescript
// Inside createJob(), around line 179
const token = localStorage.getItem('token')  // ✅ ADD

if (hyperparamMode === 'recommended') {
  const dataset = datasets.find(d => d.id === formData.dataset_id)
  const datasetSize = dataset?.sample_count || 1000

  const recommendResponse = await fetch(
    `${API_BASE}/api/v1/finetuning/recommend-hyperparameters`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {})  // ✅ ADD
      },
      body: JSON.stringify({
        dataset_size: datasetSize,
        model: formData.base_model,
        method: formData.finetuning_method
      })
    }
  )
  // ...
}
```

#### 4. `createJob()` - Submit Job (Line 202):
```typescript
const token = localStorage.getItem('token')  // ✅ ENSURE THIS IS AT TOP OF FUNCTION

const response = await fetch(`${API_BASE}/api/v1/finetuning/jobs`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {})  // ✅ ADD
  },
  body: JSON.stringify(payload)
})
```

#### 5. `submitJob()` (Line 229):
```typescript
const submitJob = async (jobId: string) => {
  try {
    const token = localStorage.getItem('token')  // ✅ ADD
    const response = await fetch(`${API_BASE}/api/v1/finetuning/jobs/${jobId}/submit`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {}  // ✅ ADD
    })
    if (response.ok) {
      alert('Job submitted successfully!')
      loadJobs()
    }
  } catch (error) {
    console.error('Error submitting job:', error)
  }
}
```

#### 6. `cancelJob()` (Line 251):
```typescript
const cancelJob = async (jobId: string) => {
  try {
    const token = localStorage.getItem('token')  // ✅ ADD
    const response = await fetch(`${API_BASE}/api/v1/finetuning/jobs/${jobId}/cancel`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {}  // ✅ ADD
    })
    if (response.ok) {
      alert('Job cancelled successfully!')
      loadJobs()
    }
  } catch (error) {
    console.error('Error cancelling job:', error)
  }
}
```

---

## Expected Result After Fix

### Before (Current State):
- Dataset dropdown: **Empty** or only "Select Dataset"
- Browser console: `401 Unauthorized` errors
- No datasets loaded

### After (With Fix):
- Dataset dropdown shows: **5 options**
  ```
  Select Dataset
  test (pending samples)
  test2 (pending samples)
  test3 (pending samples)
  test4 (pending samples)
  test5 (pending samples)
  ```
- All jobs load correctly
- Can create training jobs
- Authentication works properly

---

## Testing the Fix

### 1. Check Browser Console (Before Fix):
```
GET http://localhost:8000/api/v1/finetuning/datasets 401 (Unauthorized)
```

### 2. Check Browser Console (After Fix):
```
GET http://localhost:8000/api/v1/finetuning/datasets 200 (OK)
Response: {
  "datasets": [
    {
      "id": "d172415e-193f-46f6-9bcc-8d049ca92b79",
      "name": "test5",
      "filename": "simple_extended_story_question_answers_for_rag.csv",
      "num_samples": null,
      "preprocessing_status": "pending",
      ...
    },
    ...
  ]
}
```

### 3. Check Dataset Dropdown:
- Navigate to: **Fine-Tuning** → **Training Jobs** → **Create New Job**
- Dataset dropdown should show all 5 datasets
- Selecting a dataset should populate `formData.dataset_id`

### 4. Verify in Backend Logs:
```bash
docker-compose logs backend | grep "/api/v1/finetuning/datasets" | tail -5
```

Expected (After Fix):
```
2025-12-17 06:XX:XX - AUDIT_EVENT: {
  "method": "GET",
  "path": "/api/v1/finetuning/datasets",
  "status_code": 200,  // ✅ SUCCESS
  "user_id": "424488c8-a3d0-4bd6-ac00-7be806eac672",  // ✅ HAS USER
  "username": "admin"  // ✅ AUTHENTICATED
}
```

---

## Files to Modify

1. **Primary File**:
   - `/frontend/src/components/finetuning/JobManager.tsx` (Lines 105, 118, 179, 202, 229, 251)

2. **Related Files** (May have same issue):
   - `/frontend/src/components/finetuning/DatasetManager.tsx`
   - `/frontend/src/components/finetuning/ModelManager.tsx`
   - `/frontend/src/components/finetuning/GPUMonitor.tsx`

---

## Additional Improvements (Optional)

### 1. Show Dataset File Path in Dropdown:
```typescript
<option key={dataset.id} value={dataset.id}>
  {dataset.name} ({dataset.num_samples || 'pending'} samples) - {dataset.filename}
</option>
```

### 2. Add Visual Indicator for New Unified Paths:
```typescript
<option key={dataset.id} value={dataset.id}>
  {dataset.name}
  {dataset.minio_path.startsWith('technology/') ? ' ✅' : ' ⚠️ old path'}
  ({dataset.num_samples || 'pending'} samples)
</option>
```

### 3. Filter by Project (Future Enhancement):
If datasets are project-scoped, filter to show only datasets for the selected project:
```typescript
const filteredDatasets = datasets.filter(d =>
  !selectedProjectId || d.project_id === selectedProjectId
)
```

---

## Summary

**Issue**: Dataset selector not working
**Root Cause**: Missing `Authorization: Bearer {token}` headers in API calls
**Impact**: All fine-tuning operations fail to authenticate
**Fix**: Add authentication headers to all 6 fetch calls in `JobManager.tsx`
**Testing**: Verify dropdown shows 5 datasets after fix

**Priority**: HIGH (blocks fine-tuning functionality)
**Complexity**: LOW (simple 1-line fix per API call)
**Risk**: VERY LOW (just adding missing auth headers)

---

**Status**: ⚠️ FIX DOCUMENTED - READY TO IMPLEMENT
**Date**: 2025-12-17
**Next**: Apply auth header fixes to JobManager.tsx
