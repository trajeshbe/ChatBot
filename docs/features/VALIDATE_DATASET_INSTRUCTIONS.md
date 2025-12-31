# How to Validate Your Dataset (Make it Valid)

**Dataset**: story1
**ID**: `5884c0d1-2cf3-4183-ba33-8e74d1330398`
**Current Status**: `preprocessing_status: pending`, `is_valid: false`

---

## Why It Shows "Invalid"

Your dataset is **uploaded successfully** but needs **preprocessing/validation** to:
- Count samples
- Extract preview rows
- Validate format
- Create train/val split

This makes Overview/Samples/Quality tabs populate.

---

## How to Fix: Trigger Validation

### Option 1: Browser Console (Easiest)

1. **Open browser console** (F12)
2. **Paste and run**:

```javascript
const token = localStorage.getItem('access_token');
const datasetId = '5884c0d1-2cf3-4183-ba33-8e74d1330398';

fetch(`http://localhost:8000/api/v1/finetuning/datasets/${datasetId}/validate`, {
  method: 'POST',
  headers: { Authorization: `Bearer ${token}` }
})
.then(r => r.json())
.then(data => {
  console.log('✅ Validation result:', data);
  alert(`✅ Dataset validated!\n\nSamples: ${data.num_samples || 'processing...'}\nValid: ${data.is_valid}`);
})
.catch(err => {
  console.error('❌ Validation failed:', err);
  alert('❌ Validation failed. Check console for details.');
});
```

3. **Wait** for alert showing success
4. **Refresh** the Fine-Tuning Datasets page
5. **Check** dataset - should now show samples, overview, quality

---

### Option 2: Command Line

```bash
# 1. Get your token from browser console:
#    localStorage.getItem('access_token')

# 2. Run this command:
export TOKEN='paste_your_token_here'

curl -X POST \
  'http://localhost:8000/api/v1/finetuning/datasets/5884c0d1-2cf3-4183-ba33-8e74d1330398/validate' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' | python3 -m json.tool
```

---

## Expected Result

**Before validation**:
```
name: story1
preprocessing_status: pending
is_valid: false
num_samples: null
Overview: (blank)
Samples: (blank)
Quality: (blank)
```

**After validation**:
```
name: story1
preprocessing_status: completed
is_valid: true
num_samples: 100  (or however many rows in your CSV)
num_train_samples: 80  (80% split)
num_val_samples: 20   (20% split)
Overview: Shows sample counts, file info
Samples: Shows first 5 rows preview
Quality: Shows validation results
```

---

## Regarding "Global" Project

You mentioned the dataset should be in "global" project. Currently it's at:

```
technology/backend-development/default/admin/finetuning/datasets/story1/...
```

This path is based on:
- **Department**: Technology (from admin user)
- **Team**: Backend Development (from admin user)
- **Project**: Default (no project specified in upload)
- **User**: admin

**To use "Global" project**:
1. Find Global project ID:
   ```sql
   SELECT id FROM projects WHERE name = 'Global';
   -- Result: 997968df-c164-4697-90d5-3e7a01929dc2
   ```

2. When uploading dataset, add `project_id` parameter:
   - In UI: Select "Global" from project dropdown (if available)
   - Via API: Add `?project_id=997968df-c164-4697-90d5-3e7a01929dc2`

The path would then be:
```
technology/backend-development/global/admin/finetuning/datasets/...
```

**However**: For fine-tuning purposes, the path doesn't affect functionality. The dataset will work fine with "default" project.

---

## Quick Test

After validation, verify in database:

```bash
docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "
SELECT
  name,
  preprocessing_status,
  is_valid,
  num_samples,
  num_train_samples,
  num_val_samples
FROM finetuning_datasets
WHERE name = 'story1';"
```

Should show:
```
 name  | preprocessing_status | is_valid | num_samples | num_train_samples | num_val_samples
-------+----------------------+----------+-------------+-------------------+-----------------
 story1| completed            | t        | 100         | 80                | 20
```

---

## Use the Easiest Method

**Recommended**: Option 1 (Browser Console) - just copy-paste the JavaScript code and run it!

The validation will:
1. Download CSV from MinIO
2. Count rows → `num_samples`
3. Validate format (check for Question/Answer columns)
4. Extract first 5 rows → `sample_rows`
5. Create 80/20 train/val split
6. Update database: `preprocessing_status = 'completed'`, `is_valid = true`

Then your dataset will show as valid with all tabs populated!
