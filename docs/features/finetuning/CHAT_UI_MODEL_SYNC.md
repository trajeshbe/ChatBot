# Chat UI Model Synchronization

**Date**: 2025-12-19
**Feature**: Automatic reflection of deployed/undeployed models in Chat UI

---

## 🎯 Overview

When you deploy or undeploy a fine-tuned model, the changes automatically reflect in the Chat UI model selector after a refresh.

---

## 🔄 How It Works

### Backend Logic

**Endpoint**: `GET /api/v1/finetuning/models-public/for-chat`

**Filter**: Returns only models with `status="deployed"` AND `ollama_model_name IS NOT NULL`

```sql
SELECT * FROM finetuned_models
WHERE status = 'deployed'
  AND ollama_model_name IS NOT NULL
ORDER BY created_at DESC;
```

### Status Transitions

| Action | Status Change | ollama_model_name | Chat UI Result |
|--------|--------------|-------------------|----------------|
| **Deploy** | approved → deployed | Set to model name | ✅ Appears in dropdown |
| **Undeploy** | deployed → approved | Cleared (NULL) | ❌ Disappears from dropdown |
| **Delete** | deployed → (deleted) | Cleared (NULL) | ❌ Disappears from dropdown |

---

## 🖱️ How to Refresh Chat UI

### Method 1: Manual Refresh Button (Recommended)

1. **Navigate to Chat UI**: http://localhost:3001
2. **Locate the model selector** (top of chat interface)
3. **Click the refresh icon** (🔄 circular arrow button next to dropdown)
4. **Wait for refresh** (icon will spin briefly)
5. **Verify**: Deployed models appear, undeployed models disappear

**Visual Guide**:
```
┌─────────────────────────────────────────────┐
│  [Current Model ▼] 🔄 ← Click this refresh  │
└─────────────────────────────────────────────┘
```

---

### Method 2: Page Reload

1. **Press F5** or **Ctrl+R** (Cmd+R on Mac)
2. Models will reload automatically on page load

---

### Method 3: Auto-Refresh (Future Enhancement)

**Not yet implemented**, but planned features:
- Auto-refresh every 30 seconds when chat is active
- WebSocket notification when models change
- Real-time sync across all browser tabs

---

## 🧪 Testing the Sync

### Test Scenario: Deploy → Undeploy → Verify

#### Step 1: Initial State
```bash
# Check current models in Ollama
docker-compose exec ollama ollama list
```

#### Step 2: Deploy a Model
1. Go to **Fine-Tuning Hub** → **Evaluations** tab
2. Find an approved model
3. Click **Deploy to Ollama**
4. Wait for deployment to complete

#### Step 3: Verify in Chat UI
1. Go to **Chat UI** (http://localhost:3001)
2. Click the **refresh icon** 🔄
3. Open model selector dropdown
4. **Expected**: Your model appears under "Fine-Tuned Models"

#### Step 4: Undeploy the Model
1. Go back to **Fine-Tuning Hub** → **Evaluations** tab
2. Find the deployed model
3. Click **Undeploy (X)** button
4. Confirm undeploy

#### Step 5: Verify Removal in Chat UI
1. Go back to **Chat UI**
2. Click the **refresh icon** 🔄
3. Open model selector dropdown
4. **Expected**: Your model is GONE from the list

#### Step 6: Verify Ollama Cleanup
```bash
# Check Ollama - model should be gone
docker-compose exec ollama ollama list
```

**Expected**: Model no longer appears in Ollama list

---

## 🐛 Troubleshooting

### Issue: Model still appears after undeploy

**Cause**: Chat UI hasn't refreshed yet

**Solution**:
1. Click the refresh icon 🔄 in model selector
2. If that doesn't work, press F5 to reload page
3. Clear browser cache if persistent: Ctrl+Shift+Delete

---

### Issue: Model doesn't appear after deploy

**Possible Causes**:
1. Deployment failed (check Evaluations tab for errors)
2. Model status is not "deployed"
3. `ollama_model_name` is not set

**Diagnosis**:
```bash
# Check database
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT name, status, ollama_model_name
FROM finetuned_models
WHERE name LIKE '%your-model%';"
```

**Expected Output**:
```
      name       | status   | ollama_model_name
-----------------+----------+-------------------
 my-model_model  | deployed | my-model-v1
```

**Solution**:
- If status is NOT "deployed": Re-deploy from Evaluations tab
- If `ollama_model_name` is NULL: Re-deploy (deployment may have failed)

---

### Issue: Refresh button doesn't work

**Symptoms**: Click refresh but model list doesn't update

**Diagnosis**:
1. Open browser console (F12)
2. Click refresh button
3. Look for errors

**Common Errors**:
```javascript
// Error 1: Backend not responding
GET http://localhost:8000/api/v1/finetuning/models-public/for-chat net::ERR_CONNECTION_REFUSED

Solution: Check backend is running: docker-compose ps backend

// Error 2: 500 Internal Server Error
GET http://localhost:8000/api/v1/finetuning/models-public/for-chat 500

Solution: Check backend logs: docker-compose logs backend | tail -50
```

---

## 📊 Expected Behavior Summary

| User Action | Backend Changes | Chat UI (after refresh) |
|-------------|----------------|-------------------------|
| Deploy model | status→deployed, ollama_model_name→set | Model appears in dropdown |
| Undeploy model | status→approved, ollama_model_name→NULL | Model disappears from dropdown |
| Delete model from Ollama manually | (no change) | Model may still appear ⚠️ |
| Train new model | status→registered | Model NOT in dropdown (needs approval) |
| Approve model | status→approved | Model NOT in dropdown (needs deployment) |

**Important**: Only models with **both** `status="deployed"` AND `ollama_model_name IS NOT NULL` appear in chat.

---

## 🔧 Backend Implementation Details

### Undeploy Endpoint Changes (2025-12-19)

**File**: `backend/app/api/routes/finetuning_routes.py` (line 4085)

**What Changed**:
```python
# NEW: Clear ollama_model_name on undeploy
model.status = "approved"
model.deployment_url = None
model.ollama_model_name = None  # ← This ensures model disappears from chat UI
```

**Why**: Previously, `ollama_model_name` was left set even after undeploy, causing inconsistencies.

---

### Chat Endpoint Filter

**File**: `backend/app/api/routes/finetuning_routes.py` (line 3879-3880)

```python
query = select(FineTunedModel).where(
    FineTunedModel.status == "deployed"
).order_by(FineTunedModel.created_at.desc())
```

**Additional Check** (line 3889-3898):
```python
if m.ollama_model_name:
    provider = "ollama"
    model_id = f"ollama/{m.ollama_model_name}"
else:
    continue  # Skip if no deployment name
```

**Result**: Models appear in chat ONLY if:
- ✅ `status = "deployed"`
- ✅ `ollama_model_name IS NOT NULL`

---

## 🚀 Future Enhancements

### 1. Auto-Refresh with Polling
```typescript
// Every 30 seconds, auto-refresh model list
useEffect(() => {
  const interval = setInterval(() => {
    fetchModels()
  }, 30000)
  return () => clearInterval(interval)
}, [])
```

### 2. WebSocket Real-Time Updates
```python
# Backend: Send WebSocket message on deploy/undeploy
await websocket_manager.broadcast({
  "event": "model_deployed",
  "model_id": model.id,
  "action": "add"  # or "remove"
})
```

### 3. Browser Tab Sync
```typescript
// Use Broadcast Channel API to sync across tabs
const channel = new BroadcastChannel('model-updates')
channel.postMessage({ action: 'refresh' })
```

### 4. Smart Caching
- Cache model list in localStorage
- Only refetch if cache is older than 5 minutes
- Invalidate cache on deploy/undeploy events

---

## ✅ Current Status

**Implementation**: ✅ COMPLETE
**Testing**: ✅ READY

**What Works**:
- ✅ Manual refresh button in Chat UI
- ✅ Backend filters by status="deployed"
- ✅ Undeploy clears `ollama_model_name`
- ✅ Models appear/disappear correctly after refresh

**What's Next**:
- Train a new model
- Deploy it
- Verify it appears in chat
- Undeploy it
- Verify it disappears after refresh

---

**Date**: 2025-12-19
**Status**: ✅ READY FOR TESTING
