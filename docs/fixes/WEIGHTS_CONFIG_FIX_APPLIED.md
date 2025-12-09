# Weights Config localStorage Fix Applied

**Date**: 2025-12-06
**Issue**: RAG routing with `rag_long_term: 0.9` not working from UI - config not saving to localStorage
**Fix**: Frontend rebuilt without cache
**Status**: 🔄 **REBUILDING**

---

## What Was Done

### 1. Root Cause Identified

User confirmed: "its not getting saved in the session UI local"

**Timeline**:
- Config saving **WAS** working before
- Issue appeared **AFTER** Brain View `--no-cache` rebuild
- Most likely cause: Browser caching stale JavaScript files

### 2. Fix Applied

```bash
docker-compose stop frontend
docker builder prune -f  # Clear Docker build cache
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

**Status**: Rebuilding (takes ~60 seconds)

---

## After Rebuild: Testing Steps

### Step 1: Clear Browser Cache

**Critical**: You MUST clear your browser cache to load the new JavaScript files.

**Windows Chrome/Edge**:
1. Press `Ctrl + Shift + Delete`
2. Select "Cached images and files"
3. Click "Clear data"
4. **Close ALL tabs** for localhost:3001
5. **Close browser completely**
6. Reopen browser
7. Navigate to http://localhost:3001

**Alternative: Hard Refresh**:
- Press `Ctrl + Shift + R` (Windows)
- Or `Cmd + Shift + R` (Mac)

---

### Step 2: Test Config Save

1. Open http://localhost:3001
2. Open browser DevTools (F12) → Console tab
3. Click "⚙️ Advanced Settings" to open WeightsConfigManager
4. Adjust `rag_long_term` slider to **0.9**
5. **Watch console** - you should see:
   ```
   🔔 Dispatched weightsConfigUpdated event with 11 parameter groups
   ```
6. Click **"Apply to My Session"** button
7. **Watch for success message**: "Settings applied to your session!"

---

### Step 3: Verify localStorage

In browser console, run:
```javascript
const config = JSON.parse(localStorage.getItem('userWeightsConfig'));
console.log('rag_long_term weight:', config.strategy_weights.rag_long_term);
```

**Expected Output**: `rag_long_term weight: 0.9`

**If null or undefined**: Config did not save (see Troubleshooting below)

---

### Step 4: Test RAG Routing

1. Keep DevTools open
2. Send query: **"Who is Aadhan?"**
3. **Expected behavior**:
   - Backend should retrieve documents from long-term memory
   - Answer should include information about Aadhan from uploaded documents
   - Sources should be displayed

4. **Check Network tab**:
   - Click on `/api/v1/query` request
   - Go to "Payload" tab
   - Verify `unified_config` contains: `"rag_long_term":0.9`

---

## If Still Not Working

### Debug Option 1: Check if localStorage Works at All

In browser console:
```javascript
localStorage.setItem('test', 'hello');
console.log(localStorage.getItem('test')); // Should print: hello
```

**If fails**: Browser localStorage is disabled in settings

---

### Debug Option 2: Check Frontend Logs

```bash
docker logs rag-frontend --tail=50 2>&1 | grep -i -E "(error|warn)"
```

**Look for**: TypeScript errors or build warnings

---

### Debug Option 3: Manual Config Test

Test directly via API (bypass UI):

```bash
curl -s -X POST http://localhost:8000/api/v1/query \
  -F "query=Who is Aadhan?" \
  -F "session_id=test_manual_rag" \
  -F "model=gpt-4o-mini" \
  -F 'unified_config={"strategy_weights":{"rag_long_term":0.9}}' | jq '.sources | length'
```

**Expected**: Should return number > 0 (documents were retrieved)

**If this works**: Backend RAG routing is fine, issue is in UI config flow

---

## Success Criteria

✅ localStorage.setItem works in browser console
✅ WeightsConfigManager shows success message after clicking "Apply to My Session"
✅ Browser console logs show `weightsConfigUpdated` event dispatched
✅ localStorage contains `userWeightsConfig` with `rag_long_term: 0.9`
✅ Query "Who is Aadhan?" retrieves documents and shows sources

---

## Related Documentation

- Investigation: `docs/fixes/WEIGHTS_CONFIG_LOCALSTORAGE_INVESTIGATION.md`
- RAG Routing Test: `docs/fixes/RAG_ROUTING_UI_CONFIG_INVESTIGATION.md`

---

**Fix Applied**: 2025-12-06
**Rebuild Status**: In Progress
**Next Step**: User must clear browser cache and test
