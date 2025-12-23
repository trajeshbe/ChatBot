# Governance & Audit - Model Visibility Fix

> **Fixed**: 2025-12-22
> **Issue**: Governance & Audit only showed `registered` models, hiding `approved` and `merge_failed` models
> **Impact**: Users couldn't retry failed deployments or see approved models

---

## ✅ Problems Fixed

### 1. **Limited Model Visibility**
**Before**: Only showed models with status `registered`
**After**: Shows ALL actionable models: `registered`, `approved`, `adapter_only`, `completed`, `merge_failed`

### 2. **No Retry After Failure**
**Before**: Models with `merge_failed` status disappeared from the list
**After**: Failed models stay visible with "Retry Workflow" button

### 3. **Confusing Section Title**
**Before**: "Pending Model Approvals" (implied only unapproved models)
**After**: "Models Ready for Deployment" (clearer intent)

---

## 🔧 What Was Changed

### File: `frontend/src/components/finetuning/GovernanceAudit.tsx`

#### Change 1: Fetch All Models (Lines 73-91)
```typescript
// Before:
const fetchPendingApprovals = async () => {
  const response = await fetch(
    'http://localhost:8000/api/v1/finetuning/models-public?status=registered',
    { headers: { 'Content-Type': 'application/json' } }
  );
  const data = await response.json();
  setPendingModels(data.models || []);
};

// After:
const fetchPendingApprovals = async () => {
  // Fetch all models (no status filter on API)
  const response = await fetch(
    'http://localhost:8000/api/v1/finetuning/models-public',
    { headers: { 'Content-Type': 'application/json' } }
  );
  const data = await response.json();

  // Filter client-side to show only actionable models
  const actionableModels = (data.models || []).filter((model: PendingModel) =>
    ['registered', 'approved', 'adapter_only', 'completed', 'merge_failed'].includes(model.status)
  );
  setPendingModels(actionableModels);
};
```

**Why**:
- Removes server-side filtering (`?status=registered`)
- Applies client-side filter for ALL actionable statuses
- Includes `merge_failed` so retry button appears

#### Change 2: Updated Section Title (Line 261)
```typescript
// Before:
<h3 className="text-lg font-semibold">Pending Model Approvals</h3>

// After:
<h3 className="text-lg font-semibold">Models Ready for Deployment</h3>
```

**Why**: More accurate description - not just pending approvals, but all deployable models

---

## 📊 Model Visibility by Status

### Now Visible in Governance & Audit:
| Status | Visible? | Button Shown | Action |
|--------|----------|--------------|--------|
| `registered` | ✅ Yes | "Merge & Deploy to Ollama" | Auto-approve → Merge → Deploy |
| `approved` | ✅ Yes (NEW!) | "Merge & Deploy to Ollama" | Merge → Deploy |
| `adapter_only` | ✅ Yes | "Merge & Deploy to Ollama" | Merge → Deploy |
| `completed` | ✅ Yes | "Merge & Deploy to Ollama" | Merge → Deploy |
| `merge_failed` | ✅ Yes (NEW!) | "Merge & Deploy to Ollama" (Retry) | Retry merge → Deploy |

### Not Visible (Already Deployed):
| Status | Visible? | Reason |
|--------|----------|--------|
| `merged` | ❌ No | Already merged, use Evaluation Hub to deploy |
| `deployed` | ❌ No | Already deployed, nothing to do |
| `training` | ❌ No | Still training, not ready |
| `failed` | ❌ No | Training failed, can't deploy |

---

## 🧪 Test Scenarios

### Scenario 1: Approved Model Now Appears
**Before**:
1. Model approved in Governance & Audit
2. Model disappeared from list
3. User confused: "Where did my model go?"

**After**:
1. Model approved
2. Model stays in list with status badge "Approved"
3. "Merge & Deploy to Ollama" button still visible
4. Can deploy immediately

### Scenario 2: Failed Merge Retry
**Before**:
1. Click "Merge & Deploy to Ollama"
2. Merge fails (e.g., GPU busy)
3. Model disappeared from list
4. No way to retry in UI

**After**:
1. Click "Merge & Deploy to Ollama"
2. Merge fails
3. Model stays in list with status "merge_failed"
4. Button changes to "Retry Workflow"
5. Can click to retry immediately

### Scenario 3: See All Actionable Models
**Before**: Only saw 1-2 `registered` models
**After**: See ALL models that can be deployed (5-10 models typically)

---

## 📈 Impact

### User Experience:
- ✅ **No more disappearing models** after approval
- ✅ **Retry button visible** after failures
- ✅ **See full pipeline** of deployable models
- ✅ **Clearer section title** explains what's shown

### Technical:
- ✅ Client-side filtering instead of server-side
- ✅ Includes all actionable statuses
- ✅ Same backend API (no backend changes needed)
- ✅ Works with existing MergeAndDeployButton logic

---

## 🔄 Complete Workflow Visibility

### Models at Each Stage:

```
Training Complete
    ↓
[registered] ← Visible in Governance & Audit ✅
    ↓ (click "Merge & Deploy")
[approved] ← Visible in Governance & Audit ✅ (NEW!)
    ↓ (auto-merges)
[merging] ← Not shown (temporary state)
    ↓
[merged] ← Not shown (use Evaluation Hub)
    ↓ (auto-deploys)
[deployed] ← Not shown (already done)
```

### Retry Flow:
```
[approved]
    ↓ (click "Merge & Deploy")
[merging]
    ↓ (fails)
[merge_failed] ← Visible in Governance & Audit ✅ (NEW!)
    ↓ (click "Retry Workflow")
[merging]
    ↓ (succeeds)
[merged]
```

---

## 🎯 How to Use

### View All Deployable Models:
1. Go to: http://localhost:3001/admin
2. Click: **Fine-Tuning Hub** → **Governance & Audit**
3. Scroll to: **"Models Ready for Deployment"** section
4. You should now see ALL models that can be deployed:
   - Registered (needs approval + merge + deploy)
   - Approved (needs merge + deploy)
   - Merge Failed (retry button)
   - etc.

### Retry Failed Deployment:
1. Find your model with status badge showing "Merge Failed"
2. Look for red error message showing what went wrong
3. Click: **"Merge & Deploy to Ollama"** (button text says "Retry Workflow")
4. System retries: Approve (if needed) → Merge → Deploy
5. Watch progress bar: 0% → 100%

### Check Model Status:
Each model card shows:
- **Model name** and version
- **Status badge** (color-coded):
  - Blue: Registered
  - Purple: Approved
  - Yellow: Merging
  - Red: Failed
  - Green: Merged/Deployed
- **Base model** used
- **Evaluation metrics** (if available)
- **Action buttons** ("Merge & Deploy" or "Retry")

---

## 🔍 Verification

### Check Model Count:
```sql
-- Count models that should be visible
SELECT status, COUNT(*)
FROM finetuned_models
WHERE status IN ('registered', 'approved', 'adapter_only', 'completed', 'merge_failed')
GROUP BY status;
```

Should match the count shown in orange badge in UI.

### Check Specific Model:
```sql
-- Check your model's status
SELECT name, status, created_at
FROM finetuned_models
WHERE name LIKE '%training38%' OR name LIKE '%training39%'
ORDER BY created_at DESC;
```

If status is in the allowed list, it should appear in UI.

---

## 📝 Related Changes

This fix works with:
1. **Auth Fix**: Bearer token in API calls
2. **Merge Status Fix**: Backend allows `approved` status
3. **MergeAndDeployButton**: Handles retry after error

All three fixes together provide:
- ✅ Full visibility of deployable models
- ✅ Retry capability after failures
- ✅ Authenticated API calls
- ✅ Proper status validation

---

## ✅ Summary

**Before**: Governance & Audit was a "one-shot" view - models disappeared after approval or failure

**After**: Governance & Audit is a "persistent deployment hub" - models stay visible through the entire deployment lifecycle until deployed

**Key Benefit**: Users can now:
- See all models ready for deployment
- Retry failed deployments
- Track deployment progress
- No confusion about "where did my model go?"

---

**Status**: ✅ **FIXED** - All actionable models now visible with retry capability

**Try it**: Refresh http://localhost:3001/admin → Fine-Tuning Hub → Governance & Audit

You should now see training38 and training39 models (both `approved` status)!

---

**End of Document**
