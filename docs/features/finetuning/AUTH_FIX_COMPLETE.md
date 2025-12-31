# Authentication Fix - Merge & Deploy Button

> **Fixed**: 2025-12-22
> **Issue**: "Deployment failed: Not authenticated"
> **Root Cause**: MergeAndDeployButton missing Bearer token in API calls

---

## ✅ Problem Solved

The "Merge & Deploy to Ollama" button was failing with **"Not authenticated"** error because it wasn't including the authentication token in API requests.

---

## 🔧 What Was Fixed

Updated `MergeAndDeployButton.tsx` to include `Authorization: Bearer {token}` header in **all 4 API calls**:

### 1. Approval Step
```typescript
const token = localStorage.getItem('access_token');
const headers: Record<string, string> = {
  'Content-Type': 'application/json',
};
if (token) {
  headers['Authorization'] = `Bearer ${token}`;
}

const response = await fetch(
  `${API_BASE}/api/v1/finetuning/models-public/${model.id}/approve`,
  {
    method: 'POST',
    headers,
    body: JSON.stringify({
      notes: 'Auto-approved for merge and deployment'
    })
  }
);
```

### 2. Merge Step
```typescript
const token = localStorage.getItem('access_token');
const headers: Record<string, string> = {
  'Content-Type': 'application/json',
};
if (token) {
  headers['Authorization'] = `Bearer ${token}`;
}

const response = await fetch(
  `${API_BASE}/api/v1/finetuning/models/${model.id}/merge`,
  {
    method: 'POST',
    headers,
    body: JSON.stringify({
      base_model_name: model.base_model,
      force_cpu: false
    })
  }
);
```

### 3. Merge Status Polling
```typescript
const token = localStorage.getItem('access_token');
const headers: Record<string, string> = {};
if (token) {
  headers['Authorization'] = `Bearer ${token}`;
}

const response = await fetch(
  `${API_BASE}/api/v1/finetuning/models/${model.id}/merge-status`,
  { headers }
);
```

### 4. Deploy Step
```typescript
const token = localStorage.getItem('access_token');
const headers: Record<string, string> = {
  'Content-Type': 'application/json',
};
if (token) {
  headers['Authorization'] = `Bearer ${token}`;
}

const response = await fetch(
  `${API_BASE}/api/v1/finetuning/models-public/${model.id}/deploy`,
  {
    method: 'POST',
    headers,
    body: JSON.stringify({
      deployment_target: 'ollama',
      deployment_config: {
        model_name: ollamaModelName,
        temperature: 0.7,
        top_p: 0.9,
        top_k: 40
      }
    })
  }
);
```

---

## 🧪 How to Test

### Prerequisites:
1. **Login first**: http://localhost:3001/login
2. **Verify token exists**:
   - Open browser console (F12)
   - Run: `localStorage.getItem('access_token')`
   - Should return a JWT token string

### Test Steps:

1. **Navigate to the button**:
   - Option A: Admin → Fine-Tuning Hub → **Governance & Audit** → Pending Approvals
   - Option B: Admin → Fine-Tuning Hub → **Evaluation Hub** → Model Table

2. **Find a model with status `registered`**:
   ```sql
   SELECT name, status FROM finetuned_models
   WHERE status = 'registered'
   ORDER BY created_at DESC LIMIT 1;
   ```

3. **Click "Merge & Deploy to Ollama"**:
   - Button should show: "🔄 Processing... 10%"
   - No "Not authenticated" error

4. **Watch progress**:
   - ✓ Step 1: Approving... (20%)
   - ✓ Step 2: Merging... (20-75%, 5-15 min)
   - ✓ Step 3: Deploying... (75-100%)

5. **Success message**:
   - "✅ Successfully Deployed!"
   - Model appears in Chat UI dropdown

---

## 🔍 Troubleshooting

### Still Getting "Not authenticated"?

**Check 1: Are you logged in?**
```javascript
// Open browser console (F12)
localStorage.getItem('access_token')
// Should return a long JWT token string
```

If `null`, you're not logged in:
1. Go to http://localhost:3001/login
2. Login with admin credentials
3. Return to Fine-Tuning Hub
4. Try again

**Check 2: Is token expired?**
JWT tokens expire after a certain time. If you've been logged in for a long time:
1. Logout
2. Login again
3. Try the workflow

**Check 3: Backend logs**
```bash
docker-compose logs backend --tail 50 | grep -E "(401|authentication|Unauthorized)"
```

Look for specific error messages.

---

## 📊 Before vs After

### Before Fix:
```
User clicks "Merge & Deploy to Ollama"
  ↓
API call: POST /api/v1/finetuning/models-public/{id}/approve
Headers: { 'Content-Type': 'application/json' }  ❌ NO AUTH
  ↓
Backend returns: 401 Unauthorized
  ↓
Error: "Deployment failed: Not authenticated"
```

### After Fix:
```
User clicks "Merge & Deploy to Ollama"
  ↓
Get token: localStorage.getItem('access_token')
  ↓
API call: POST /api/v1/finetuning/models-public/{id}/approve
Headers: {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'  ✅ AUTH INCLUDED
}
  ↓
Backend returns: 200 OK
  ↓
Success! Continue to merge step
```

---

## 🚀 Ready to Use

The authentication issue is now fixed. You can use the "Merge & Deploy to Ollama" button in:

1. **Governance & Audit** tab → Pending Model Approvals section
2. **Evaluation Hub** tab → Model table Actions column

Just make sure you're **logged in** before clicking the button!

---

## 📝 Files Modified

- `frontend/src/components/finetuning/MergeAndDeployButton.tsx`
  - Lines 109-115: Added auth to approval step
  - Lines 158-164: Added auth to merge step
  - Lines 207-211: Added auth to merge status polling
  - Lines 276-282: Added auth to deploy step

---

## ✅ Verification Checklist

Before testing, ensure:
- [x] Frontend restarted: `docker-compose restart frontend`
- [x] Frontend compiled: Check logs for "✓ Compiled /admin"
- [x] Browser refreshed: `Ctrl+Shift+R`
- [ ] **User is logged in**: Check `localStorage.getItem('access_token')`
- [ ] Model exists with status `registered`

---

**Status**: ✅ **FIXED** - Ready for testing

---

**End of Document**
