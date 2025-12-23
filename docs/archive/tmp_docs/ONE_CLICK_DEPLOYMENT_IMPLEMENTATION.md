# One-Click Deployment Implementation Plan

**Date**: 2025-12-23
**Goal**: Enable one-button click from Governance UI → Deployed model in Chat dropdown

---

## Current State Analysis

### ✅ What's Already Working:

1. **MergeAndDeployButton Component** (`frontend/src/components/finetuning/MergeAndDeployButton.tsx`):
   - Already has one-click workflow implementation
   - Shows real-time progress (approval → merge → deploy)
   - Calls proper backend endpoints
   - Beautiful UI with progress indicators

2. **Backend Deployment Endpoint** (`/api/v1/finetuning/models-public/{id}/deploy`):
   - Already implements full pipeline orchestration
   - Already fixed for f16 GGUF conversion  
   - Working end-to-end (verified with choles-qa-ft model)

3. **GovernanceAudit Component**:
   - Already imports MergeAndDeployButton
   - Shows list of models ready for deployment

### ⚠️ Current Gaps:

1. **UI Integration**: GovernanceAudit doesn't render MergeAndDeployButton for each model
2. **Real-time Chat UI Sync**: After deployment, model doesn't auto-appear in Chat dropdown
3. **Database Status Updates**: Need to update `finetuned_models.status` to 'deployed' after successful Ollama deployment

---

## Implementation Plan

### Phase 1: Update GovernanceAudit UI ✅

**File**: `frontend/src/components/finetuning/GovernanceAudit.tsx`

**Changes**:
1. Replace separate "Approve" and "Reject" buttons with **MergeAndDeployButton**
2. Add conditional rendering based on model status
3. Add refresh callback to reload models after deployment

**Code Location**: Lines 272-340 (current approval/rejection UI)

**New UI Flow**:
```
For each model in pendingModels:
  - Show model card with metrics and lineage
  - Show MergeAndDeployButton (compact mode)
  - Button handles: Approve → Merge → GGUF → Deploy → Ollama
  - On completion: Refresh model list + notify user
```

---

### Phase 2: Backend Enhancement for Chat UI Sync ✅

**File**: `backend/app/services/ollama_deployment_service.py`

**Current Status**: Already has complete deployment logic
**Enhancement Needed**: Update database status to 'deployed' after successful Ollama deployment

**Code Addition** (after line 245 - successful Ollama deployment):
```python
# Update model status to 'deployed' in database
from sqlalchemy.orm import Session
from app.models.database_enhanced import FinetunedModel

async def _update_model_status_deployed(model_id: str, ollama_name: str, db: Session):
    """Update model status to deployed after successful Ollama deployment"""
    model = db.query(FinetunedModel).filter(FinetunedModel.id == model_id).first()
    if model:
        model.status = 'deployed'
        model.ollama_model_name = ollama_name
        model.deployment_timestamp = datetime.utcnow()
        db.commit()
        logger.info(f"✅ Updated model {model_id} status to 'deployed'")
```

---

### Phase 3: Chat UI Auto-Refresh ✅

**Approach Options**:

**Option A: WebSocket Real-time Updates** (Best UX, more complex)
- Backend emits WebSocket event on successful deployment
- Chat UI listens for model deployment events
- Auto-refreshes model dropdown

**Option B: Polling** (Simpler, good enough)
- Chat UI polls `/api/v1/ollama/models` every 10 seconds
- Auto-detects new models
- Shows toast notification

**Option C: Manual Refresh Button** (Simplest, current state)
- User clicks refresh button in Chat UI
- Already implemented

**Recommendation**: Start with **Option C** (already works), add **Option B** as enhancement

---

## Implementation Steps (Priority Order)

### Step 1: Update GovernanceAudit.tsx (HIGH PRIORITY) ✅

Replace current approval UI (lines 293-340) with:

```typescript
{/* Quick Deployment - One-Click Workflow */}
<div className="mt-4">
  <MergeAndDeployButton
    model={model}
    compact={true}
    onComplete={async () => {
      // Refresh model list
      await fetchPendingApprovals();
      await fetchAuditLogs();
      // Show success notification
      alert(`Model ${model.name} deployed successfully! Go to Chat UI and refresh the model dropdown.`);
    }}
    onError={(error) => {
      console.error('Deployment error:', error);
      alert(`Deployment failed: ${error}`);
    }}
  />
</div>

{/* Legacy: Keep Approve/Reject for edge cases */}
<details className="mt-2">
  <summary className="text-sm text-gray-600 cursor-pointer">Advanced: Manual Approval</summary>
  <div className="mt-2 space-y-2">
    {/* Existing approval/rejection UI */}
  </div>
</details>
```

---

### Step 2: Add Database Status Update (MEDIUM PRIORITY) ✅

**File**: `backend/app/services/ollama_deployment_service.py`

Add database update after successful deployment (line ~245):

```python
# After successful Ollama deployment
if ollama_result and "ollama_model_name" in ollama_result:
    # Update model status in database
    try:
        from app.core.database import get_db
        from app.models.database_enhanced import FinetunedModel
        from datetime import datetime
        
        # Get DB session
        db = next(get_db())
        
        # Update model
        model = db.query(FinetunedModel).filter(FinetunedModel.id == model_id).first()
        if model:
            model.status = 'deployed'
            model.ollama_model_name = ollama_result["ollama_model_name"]
            model.deployment_timestamp = datetime.utcnow()
            db.commit()
            logger.info(f"✅ Model {model_id} status updated to 'deployed'")
    except Exception as e:
        logger.warning(f"Failed to update model status: {e}")
        # Don't fail deployment if status update fails
```

---

### Step 3: Chat UI Polling (OPTIONAL ENHANCEMENT) ⏸️

**File**: `frontend/src/components/ChatInterfaceEnhanced.tsx` or `frontend/src/components/ModelSelector.tsx`

Add polling logic:

```typescript
useEffect(() => {
  // Poll for new models every 30 seconds when chat is active
  const interval = setInterval(async () => {
    const response = await fetch(`${API_BASE}/api/v1/ollama/models`);
    if (response.ok) {
      const data = await response.json();
      const newModels = data.models.filter(m => !availableModels.includes(m.name));
      
      if (newModels.length > 0) {
        // New model detected!
        setAvailableModels(data.models.map(m => m.name));
        // Show toast notification
        toast.success(`New fine-tuned model available: ${newModels[0].name}`);
      }
    }
  }, 30000); // 30 seconds

  return () => clearInterval(interval);
}, []);
```

---

## Testing Checklist

### Test 1: End-to-End Deployment ✅

1. Navigate to Governance & Audit tab
2. Find approved model (status: 'registered', 'approved', or 'adapter_only')
3. Click "Quick Deploy" button
4. Verify progress indicators:
   - ✅ Step 1: Approve Model (if needed)
   - ⏳ Step 2: Merge LoRA Adapter (5-15 min)
   - ⏳ Step 3: Deploy to Ollama
5. Wait for completion (expect 10-20 minutes total)
6. Verify success message
7. Go to Chat UI
8. Click refresh button
9. Verify model appears in dropdown

### Test 2: Database Verification ✅

```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT id, name, status, ollama_model_name, deployment_timestamp 
   FROM finetuned_models 
   WHERE status = 'deployed';"
```

Expected: Status = 'deployed', ollama_model_name populated

### Test 3: Ollama Verification ✅

```bash
docker-compose exec ollama ollama list
```

Expected: Model appears in list

### Test 4: Inference Test ✅

```bash
docker-compose exec ollama ollama run <model-name> "Test query"
```

Expected: Model responds

---

## File Summary

### Files to Modify:

1. **frontend/src/components/finetuning/GovernanceAudit.tsx**
   - Lines 272-340: Replace approval UI with MergeAndDeployButton
   - Add onComplete callback to refresh

2. **backend/app/services/ollama_deployment_service.py**
   - Line ~245: Add database status update after successful deployment

### Files Already Complete:

1. **frontend/src/components/finetuning/MergeAndDeployButton.tsx** ✅
   - Already has complete one-click workflow
   - No changes needed

2. **backend/app/api/routes/finetuning_routes.py** ✅
   - Deploy endpoint already working
   - GGUF conversion fix already applied

---

## Success Criteria

✅ User can click ONE button in Governance UI
✅ Button shows real-time progress for all steps
✅ Model is merged, converted to GGUF, and deployed to Ollama
✅ Database status updates to 'deployed'
✅ Model appears in Chat UI dropdown (after manual refresh)
✅ Model responds to inference queries

---

## Estimated Time

- **Step 1** (GovernanceAudit UI): 15 minutes
- **Step 2** (Database update): 10 minutes
- **Step 3** (Chat UI polling - optional): 20 minutes
- **Testing**: 30 minutes (including merge/deploy wait time)

**Total**: ~1-2 hours (including test deployment)

---

## Next Actions

1. ✅ Modify GovernanceAudit.tsx to render MergeAndDeployButton
2. ✅ Add database status update in ollama_deployment_service.py
3. ✅ Test with existing approved model
4. ⏸️ (Optional) Add Chat UI polling

---

**Status**: Ready for implementation
**Priority**: HIGH - This completes the fine-tuning user workflow

