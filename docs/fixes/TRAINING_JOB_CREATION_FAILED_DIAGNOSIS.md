# Training Job Creation Failed - Diagnosis & Fix

**Date**: 2025-12-17
**Issue**: Training job creation failed - no request reached backend
**Status**: 🔍 **INVESTIGATING**

---

## Problem

User tried to create a training job and it failed. Backend logs show **NO POST request** to create the job, which means the error is happening on the **frontend** before the request is sent.

---

## Root Cause Analysis

### Backend Logs Show:
- ✅ GET requests to list jobs - working
- ✅ GET requests to list datasets - working
- ✅ GET requests to get stats - working
- ❌ **NO POST request to create job** - this is the problem!

### This Indicates:
The issue is happening **before** the request reaches the backend. Possible causes:

1. **Missing Required Fields** - Form validation blocking submission
2. **No Dataset Selected** - Dataset dropdown empty or not selected
3. **Empty Job Name** - Job name field not filled
4. **Browser Console Error** - JavaScript error preventing form submission
5. **Hyperparameter Request Failing** - If using "recommended" mode, the prereq request might be failing

---

## Available Valid Datasets

Database shows there's **1 valid dataset** available:

```
id: 3b5aebf0-8dcf-423c-aad4-65a8f3dba3b6
name: story8
is_valid: true
status: completed
```

So datasets ARE available to select.

---

## Troubleshooting Steps

### Step 1: Check Browser Console for Errors

1. **Open Browser Developer Console**:
   - Press `F12` or `Right-click → Inspect`
   - Go to **Console** tab

2. **Look for Errors**:
   - Red error messages
   - Failed network requests
   - JavaScript exceptions

3. **Common Errors to Look For**:
   ```
   ❌ "Cannot read property '...' of undefined"
   ❌ "Failed to fetch"
   ❌ "TypeError: ..."
   ❌ "Network request failed"
   ```

4. **Take Screenshot** and share the error message

---

### Step 2: Verify Form Fields Are Filled

The JobManager form requires these fields:

#### Required Fields:
1. **Job Name** (`formData.name`) - Must not be empty
2. **Dataset** (`formData.dataset_id`) - Must select a dataset
3. **Base Model** - Default: `Qwen/Qwen2.5-7B-Instruct`
4. **Fine-tuning Method** - Default: `peft`
5. **Training Objective** - Default: `instruction`
6. **Quantization** - Default: `4bit`

#### Check These:
```
✅ Is the "Job Name" field filled in?
✅ Is a dataset selected from the dropdown?
✅ Is "story8" showing in the dataset dropdown?
✅ Is the base model selected?
```

---

### Step 3: Check Network Tab

1. **Open Network Tab** in DevTools (F12)
2. **Try creating the job again**
3. **Look for requests**:
   - Should see: `POST /api/v1/finetuning/jobs`
   - If using "Recommended" mode, should see: `POST /api/v1/finetuning/hyperparameters/recommend`

4. **Check Request Status**:
   - ✅ **200** = Success
   - ❌ **400** = Bad request (missing/invalid data)
   - ❌ **401** = Unauthorized (token expired)
   - ❌ **404** = Endpoint not found
   - ❌ **500** = Server error

5. **If No Request Appears**:
   - Form validation is blocking it
   - JavaScript error is preventing submission
   - Check Console tab for errors

---

### Step 4: Verify Hyperparameter Mode

The form has 3 hyperparameter modes:

1. **Manual** - You provide all hyperparameters
2. **Recommended** (Default) - Backend suggests hyperparameters
3. **Auto-Tune** - Backend runs Optuna

If using **"Recommended" mode** (default), the form makes this request FIRST:
```
POST /api/v1/finetuning/hyperparameters/recommend
```

If this fails, the job creation won't proceed.

**Check**:
- Network tab for this request
- Any errors in response
- Try switching to **"Manual"** mode to bypass this step

---

### Step 5: Check Authentication Token

The request requires a valid authentication token.

**Verify Token**:
```javascript
// Open browser console and run:
localStorage.getItem('access_token')
```

**Expected**: Long string (JWT token)
**If null/undefined**: You're not logged in

**Fix**:
1. Refresh the page
2. Log in again
3. Try creating the job

---

## Likely Issues & Solutions

### Issue 1: Job Name Field Empty ⚠️

**Symptom**: Form doesn't submit, no error shown
**Cause**: Job name is required but not filled
**Fix**: Enter a job name in the "Job Name" field

```
Job Name: [story8-qwen-1.5b-test] ← Fill this in!
```

---

### Issue 2: No Dataset Selected ⚠️

**Symptom**: Form doesn't submit, or shows "dataset required" error
**Cause**: Dataset dropdown not selected
**Fix**: Select "story8" from the dataset dropdown

```
Dataset: [Select dataset ▼] ← Click and select "story8"
```

---

### Issue 3: Datasets Not Loading ⚠️

**Symptom**: Dataset dropdown is empty
**Cause**: Datasets API request failed
**Fix**:
1. Check browser console for errors
2. Verify token is valid
3. Check backend logs: `docker-compose logs backend | grep datasets`
4. Manually reload datasets by refreshing the page

---

### Issue 4: Hyperparameter Recommendation Failing ⚠️

**Symptom**: Form submits but nothing happens
**Cause**: Recommended hyperparameters request failing
**Fix**:
1. Switch hyperparameter mode to **"Manual"**
2. Or check Network tab for failed hyperparameter request
3. Check backend logs for hyperparameter endpoint errors

---

### Issue 5: Browser Cache Issue ⚠️

**Symptom**: Old UI version, missing Qwen 1.5B model
**Cause**: Browser cache hasn't refreshed
**Fix**:
1. Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
2. Or: `Ctrl+F5`
3. Or: Clear browser cache for `localhost:3001`

---

## Testing Guide

### Manual Test - Create Job via API

To verify the backend is working, try creating a job directly via curl:

```bash
# Get token from database
TOKEN=$(docker-compose exec -T postgres psql -U postgres -d ragchatbot -c "
  SELECT cs.access_token
  FROM chat_sessions cs
  JOIN users u ON cs.user_id = u.id
  WHERE u.username = 'admin'
  AND cs.is_active = true
  ORDER BY cs.last_activity DESC
  LIMIT 1;" -t | tr -d ' \n')

# Create test job
curl -X POST http://localhost:8000/api/v1/finetuning/jobs \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-job-story8",
    "dataset_id": "3b5aebf0-8dcf-423c-aad4-65a8f3dba3b6",
    "base_model": "Qwen/Qwen2.5-1.5B-Instruct",
    "finetuning_method": "peft",
    "training_objective": "instruction",
    "quantization": "4bit",
    "hyperparameters": {
      "learning_rate": 0.0002,
      "num_epochs": 3,
      "batch_size": 4,
      "gradient_accumulation_steps": 4,
      "warmup_steps": 100,
      "lora_r": 16,
      "lora_alpha": 32,
      "lora_dropout": 0.05
    }
  }'
```

**Expected Result**: Success message with job ID

**If This Works**: Backend is fine, issue is in the UI
**If This Fails**: Backend error - check logs

---

## Next Steps

1. ✅ **Check browser console** for JavaScript errors
2. ✅ **Verify all required fields** are filled in the form
3. ✅ **Check Network tab** to see if request is made
4. ✅ **Try Manual hyperparameter mode** to bypass recommendation
5. ✅ **Share error screenshots** if you see any errors

---

## Request for User

**Please provide**:
1. **Screenshot of browser console** (F12 → Console tab)
2. **Screenshot of the job creation form** showing what you filled in
3. **Screenshot of Network tab** (F12 → Network tab) when you click "Create Job"
4. **Any error message** you saw in an alert or on the page

This will help me identify the exact issue!

---

**Status**: ⏳ Waiting for user diagnostic information

---

**End of Diagnosis**
