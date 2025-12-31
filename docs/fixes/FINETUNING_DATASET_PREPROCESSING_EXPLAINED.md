# Fine-Tuning Dataset Preprocessing - Explained

**Date**: 2025-12-17 06:50 UTC
**Question**: Why are test5 (and all datasets) showing as "invalid" with blank overview, samples, and quality?

---

## The Answer

### ✅ Your Datasets Are UPLOADED Successfully
All 5 datasets (test, test2, test3, test4, test5) are uploaded to MinIO and stored in the database.

### ⏳ But They Haven't Been PREPROCESSED Yet
They're stuck in `preprocessing_status: "pending"` - which means they haven't been validated, analyzed, or prepared for training.

---

## What Each Field Means

### Dataset Status Fields (From Database):

| Field | Current Value | What It Means |
|-------|---------------|---------------|
| **preprocessing_status** | `pending` | Dataset uploaded but not validated/analyzed yet |
| **is_valid** | `false` | Dataset hasn't been validated (no quality checks run) |
| **num_samples** | `null` | Number of training examples hasn't been counted |
| **num_train_samples** | `null` | Training split size not calculated |
| **num_val_samples** | `null` | Validation split size not calculated |
| **format_type** | `qa` | Format detected as Question-Answer pairs ✅ |
| **sample_rows** | `null` | Sample rows not extracted for preview |
| **validation_errors** | `null` | No validation errors recorded (because not validated yet) |
| **columns** | `null` | Column structure not analyzed |

---

## What Should Happen After Upload

### Step 1: Upload ✅ DONE
```
User uploads CSV file → Stored in MinIO → Database record created
Status: preprocessing_status = "pending"
```

### Step 2: Preprocessing ❌ NOT DONE YET
```
System should:
1. Download file from MinIO
2. Parse CSV and count rows → num_samples
3. Analyze column structure → columns
4. Extract sample rows for preview → sample_rows
5. Validate data quality:
   - Check for missing values
   - Verify format matches type (qa, instruction, etc.)
   - Check encoding and special characters
6. Split into train/val sets → num_train_samples, num_val_samples
7. Update: preprocessing_status = "completed", is_valid = true/false
```

### Step 3: Ready for Training ❌ BLOCKED
```
Once preprocessing_status = "completed" AND is_valid = true:
- Dataset appears as "valid" in UI
- Overview shows: "X samples, Y train, Z validation"
- Samples tab shows: Preview of actual data rows
- Quality tab shows: Validation results, column analysis
- Can be used in training jobs
```

---

## Why Preprocessing Didn't Run Automatically

Looking at the code (`finetuning_routes.py:201`):

```python
dataset = FineTuningDataset(
    ...
    preprocessing_status="pending"  # ← Set to pending, but NO background task triggered
)
```

**Issue**: The upload endpoint creates the dataset record but **doesn't trigger preprocessing**.

**Expected Behavior**: Should either:
1. Trigger preprocessing as background task after upload
2. Provide manual "Validate Dataset" button in UI
3. Auto-preprocess when dataset is first accessed

---

## Current Workaround: Manual API Call

There IS an endpoint to validate/preprocess a dataset:

```
POST /api/v1/finetuning/datasets/{dataset_id}/validate
```

This endpoint (`finetuning_routes.py:240-275`):
```python
@router.post("/datasets/{dataset_id}/validate", response_model=DatasetValidationResponse)
async def validate_dataset(dataset_id: str, ...):
    validation_result = await service.validate_dataset(dataset.id)
    return DatasetValidationResponse(...)
```

---

## How to Fix This Now

### Option 1: Manual API Call (Immediate)

For each dataset, call the validate endpoint:

```bash
# Get test5 dataset ID
DATASET_ID="d172415e-193f-46f6-9bcc-8d049ca92b79"
TOKEN=$(cat ~/.local/share/token.txt)  # Or from localStorage

# Trigger validation/preprocessing
curl -X POST \
  "http://localhost:8000/api/v1/finetuning/datasets/${DATASET_ID}/validate" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json"
```

**Do this for all 5 datasets**.

### Option 2: Add UI Button (Better UX)

Add a "Validate" or "Process" button in the Dataset Manager UI that calls the validate endpoint.

### Option 3: Auto-preprocess on Upload (Best)

Modify the upload endpoint to trigger preprocessing as a background task:

```python
# In finetuning_routes.py after line 202
from fastapi import BackgroundTasks

@router.post("/datasets/upload", ...)
async def upload_dataset(
    background_tasks: BackgroundTasks,  # Add this
    ...
):
    # ... existing code ...
    db.add(dataset)
    await db.commit()

    # NEW: Trigger preprocessing in background
    background_tasks.add_task(
        service.validate_dataset,
        dataset.id
    )

    return DatasetUploadResponse(...)
```

---

## What Preprocessing Actually Does

Based on the service code, `service.validate_dataset()` should:

### 1. Download File from MinIO
```python
# Downloads CSV from MinIO using dataset.minio_path
file_content = await minio_client.get_object(dataset.minio_path)
```

### 2. Parse and Count Rows
```python
import pandas as pd
df = pd.read_csv(file_content)
num_samples = len(df)  # Total rows
```

### 3. Validate Format
For `format_type='qa'` (Question-Answer):
```python
# Check required columns
required_cols = ['Question', 'Answer']
if not all(col in df.columns for col in required_cols):
    validation_errors = {"error": "Missing required columns"}
    is_valid = False
```

### 4. Extract Samples
```python
# Get first 5 rows for preview
sample_rows = df.head(5).to_dict('records')
```

### 5. Create Train/Val Split
```python
from sklearn.model_selection import train_test_split
train_df, val_df = train_test_split(df, test_size=0.2)
num_train_samples = len(train_df)  # 80% of data
num_val_samples = len(val_df)      # 20% of data
```

### 6. Update Database
```python
dataset.num_samples = num_samples
dataset.num_train_samples = num_train_samples
dataset.num_val_samples = num_val_samples
dataset.sample_rows = sample_rows
dataset.columns = list(df.columns)
dataset.is_valid = True
dataset.preprocessing_status = "completed"
await db.commit()
```

---

## Expected UI After Preprocessing

### Before (Current State):
```
Dataset: test5
Status: ⏳ pending
Valid: ❌ No
Samples: (blank)
Overview: (blank)
Quality: (blank)
```

### After Preprocessing:
```
Dataset: test5
Status: ✅ completed
Valid: ✅ Yes
Samples: 100 total (80 train, 20 validation)

Overview Tab:
- Total Samples: 100
- Training Samples: 80
- Validation Samples: 20
- Format: Question-Answer (qa)
- Columns: Question, Answer
- File Size: 15.2 KB
- Uploaded: 2025-12-17 05:30 UTC

Samples Tab:
+--------------------------------------------------+--------------------------------------------------+
| Question                                          | Answer                                           |
+--------------------------------------------------+--------------------------------------------------+
| What festival is celebrated annually on June 23rd| São João                                         |
| and 24th in Portugal?                            |                                                  |
+--------------------------------------------------+--------------------------------------------------+
| What is another name for the Feast of St. John?  | São João                                         |
+--------------------------------------------------+--------------------------------------------------+
(showing 5 of 100 samples)

Quality Tab:
✅ All required columns present
✅ No missing values
✅ All rows have valid Question-Answer pairs
✅ Character encoding: UTF-8
⚠️ Recommended minimum: 1000 samples (you have 100)
```

---

## Immediate Action Plan

### For YOU (User):

**Wait for frontend rebuild to complete** (still in progress), then:

1. **Navigate to**: Fine-Tuning → Datasets
2. **For each dataset** (test, test2, test3, test4, test5):
   - Click on dataset name
   - Look for "Validate" or "Process" button
   - Click it to trigger preprocessing

**OR** use the API call workaround above.

### For ME (If we're implementing auto-preprocessing):

1. Modify `finetuning_routes.py` upload endpoint
2. Add `BackgroundTasks` to trigger validation after upload
3. Re-upload datasets (or trigger validation on existing ones)

---

## Summary

**Question**: Why are datasets "invalid" with blank info?

**Answer**:
- ✅ Datasets uploaded successfully
- ❌ Preprocessing never ran (stuck in "pending" status)
- ⏳ Need to trigger validation/preprocessing manually
- 📋 After preprocessing: will show samples, quality, train/val split

**What preprocessing does**:
1. Counts rows → `num_samples`
2. Analyzes columns → `columns`
3. Extracts sample data → `sample_rows`
4. Validates format → `is_valid`, `validation_errors`
5. Creates train/val split → `num_train_samples`, `num_val_samples`
6. Updates status → `preprocessing_status = "completed"`

**What you'll see after**:
- Overview: "100 samples (80 train, 20 val)"
- Samples: Preview of first 5 rows
- Quality: Validation results and recommendations
- Status: "completed" instead of "pending"

---

**Next**: Let me check if the validate endpoint is exposed in the UI, and if not, I'll show you how to call it via API or add a UI button.
