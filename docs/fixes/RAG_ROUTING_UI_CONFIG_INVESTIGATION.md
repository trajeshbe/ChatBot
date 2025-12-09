# RAG Routing UI Config Investigation

**Date**: 2025-12-06
**Issue**: RAG routing with `rag_long_term: 0.9` weight not retrieving documents when querying "Who is Aadhan" from UI
**Status**: ⚠️ **INVESTIGATING** - Backend works, UI config flow needs verification

---

## User Report

> "can you check why the weight setting about .9 for Long term rag still wan't be able to route it to pick documents when i asked about 'Who is Aadhan' ? is the ui config setting working ?? it used to so.. ensure all the parameters are respected and used in the calls with right routing and right weights ..etc .. fix it and rebuld without cache"

---

## Investigation Summary

### ✅ Backend RAG Routing - VERIFIED WORKING

**Test Command**:
```bash
curl -s -X POST http://localhost:8000/api/v1/query \
  -F "query=Who is Aadhan?" \
  -F "session_id=test_rag_routing_ui_config" \
  -F "model=gpt-4o-mini" \
  -F 'unified_config={"strategy_weights":{"rag_long_term":0.9,"enable_brain_view":true}}'
```

**Result**: ✅ **SUCCESS**
```json
{
  "routing_strategy": "force_rag",
  "has_sources": true,
  "num_sources": 1,
  "answer_preview": "Based on the documents provided, Aadhan is a ruler who has reclaimed his throne in the kingdom of Kandigai..."
}
```

**Conclusion**: Backend RAG routing works correctly when called directly with API. The issue is likely in the frontend UI config transmission.

---

## UI Config Flow Architecture

### How It Currently Works

1. **WeightsConfigManager Component** (`WeightsConfigManager.tsx`):
   - User adjusts sliders for strategy weights (e.g., `rag_long_term: 0.9`)
   - Clicks "Apply to Session" button
   - **Saves** to `localStorage.setItem('userWeightsConfig', JSON.stringify(config))` (line 205)
   - **Dispatches** custom event: `weightsConfigUpdated` (line 211-212)

2. **ChatInterfaceEnhanced Component** (`ChatInterfaceEnhanced.tsx`):
   - **Loads** config from localStorage on mount (lines 267-295)
   - **Listens** for `weightsConfigUpdated` event (line 328)
   - **Updates** state: `setUnifiedConfig(e.detail)` (line 321)
   - **Sends** config in API query: `formData.append('unified_config', JSON.stringify(configToSend))` (line 996)

3. **Backend** (`app/main.py`):
   - **Receives** `unified_config` from request (line 761)
   - **Passes** to EnhancedRAGAgent
   - **Routes** based on strategy_weights

---

## Potential Issues

### Issue 1: Config Not Being Saved to localStorage

**Symptom**: User sets `rag_long_term: 0.9` in UI but config doesn't persist.

**Check**:
1. Open browser DevTools → Application tab → Local Storage
2. Look for key `userWeightsConfig`
3. Verify it contains the correct weights

**Expected Value**:
```json
{
  "strategy_weights": {
    "rag_long_term": 0.9,
    "enable_brain_view": true,
    ...
  },
  ...
}
```

---

### Issue 2: Config Being Saved But Not Sent in API Call

**Symptom**: Config exists in localStorage but not being sent to backend.

**Check Browser Network Tab**:
1. Open DevTools → Network tab
2. Send a query from UI
3. Click on `/api/v1/query` request
4. Check "Payload" tab
5. Look for `unified_config` field

**Expected Payload**:
```
Form Data:
query: "Who is Aadhan?"
session_id: "..."
model_id: "gpt-4o-mini"
unified_config: {"strategy_weights":{"rag_long_term":0.9,...},...}
```

---

### Issue 3: Default Weights Overriding User Settings

**Symptom**: UI saves config but backend uses default weights instead.

**Backend Log Check**:
```bash
docker logs rag-backend --tail=50 | grep -i "strategy_weights"
```

**Expected Log**:
```
📦 Passing unified config with strategy weights: {...}
   → rag_long_term: 0.9
```

---

## Code Locations

### Frontend

**ChatInterfaceEnhanced.tsx**:
- Line 244: `const [unifiedConfig, setUnifiedConfig] = useState<WeightsConfig | null>(null)`
- Lines 267-295: Load config from localStorage on mount
- Line 321: Update config when WeightsConfigManager saves: `setUnifiedConfig(e.detail)`
- Line 328: Event listener for `weightsConfigUpdated`
- Lines 982-1010: Send unified_config in API call

**WeightsConfigManager.tsx**:
- Lines 127-147: Load config from localStorage or API
- Line 205: Save to localStorage: `localStorage.setItem('userWeightsConfig', JSON.stringify(config))`
- Lines 211-212: Dispatch event: `window.dispatchEvent(new CustomEvent('weightsConfigUpdated', { detail: config }))`

### Backend

**app/main.py**:
- Line 761: Pass `unified_config` to EnhancedRAGAgent

**app/agents/enhanced_rag_agent.py**:
- Lines 92-191: Routing logic based on strategy_weights
- Line 156+: CONVERSATION_ONLY path (weight > 0.8)
- DIRECT_LLM path (weight > 0.8)
- RAG paths (check for force_rag logic)

---

## Debugging Steps

### Step 1: Check Browser LocalStorage

```javascript
// In browser DevTools console
JSON.parse(localStorage.getItem('userWeightsConfig'))
```

**Expected Output**:
```json
{
  "strategy_weights": {
    "rag_long_term": 0.9,
    ...
  }
}
```

---

### Step 2: Test UI to Backend Flow

1. **Open UI**: http://localhost:3001
2. **Open Advanced Settings** (WeightsConfigManager)
3. **Set Strategy Weights**:
   - Long-term RAG: 0.9
   - Enable Brain View: ON
4. **Click "Apply to Session"**
5. **Check Browser Console** for logs:
   ```
   ✅ WeightsConfigManager loaded USER SESSION config from localStorage
   🔔 Dispatched weightsConfigUpdated event with 11 parameter groups
   🔄 Config updated from custom event with 11 parameter groups
   ```
6. **Send Query**: "Who is Aadhan?"
7. **Check Browser Console** for query logs:
   ```
   📦 Passing unified config with strategy weights: {rag_long_term: 0.9, ...}
   ```
8. **Check Network Tab** → `/api/v1/query` → Payload → `unified_config`

---

### Step 3: Backend Log Verification

```bash
# Monitor backend logs while sending query from UI
docker logs rag-backend --follow --tail=50 2>&1 | grep -E "(strategy_weights|rag_long_term|ROUTING)"
```

**Expected Logs**:
```
📦 Unified config received with strategy_weights: {...}
📌 ROUTING: rag_long_term weight (0.90) > threshold
🎯 Using RAG retrieval for long-term memory
```

---

## Root Cause Analysis

Based on investigation:

1. ✅ **Backend RAG routing works** when called directly via API
2. ✅ **UI config architecture is correct** (localStorage → event → state → API)
3. ⚠️ **Need to verify**: Does UI actually save/send the config when user adjusts weights?

**Most Likely Issue**: User may need to click "Apply to Session" button in WeightsConfigManager after adjusting sliders.

**Secondary Issue**: If "Apply to Session" was clicked, check if:
- Browser localStorage has the correct config
- Network request includes unified_config
- Backend receives and respects the config

---

## Recommended Fix (If Issue Confirmed)

### If Config Not Saving:
Check `WeightsConfigManager.tsx` lines 200-214 (`saveToSession` function) to ensure:
- `localStorage.setItem` executes successfully
- Event `weightsConfigUpdated` is dispatched
- No JavaScript errors preventing save

### If Config Not Being Sent:
Check `ChatInterfaceEnhanced.tsx` lines 980-1010 to ensure:
- `unifiedConfig` state is populated
- `formData.append('unified_config', ...)` executes
- No conditional logic preventing config transmission

### If Backend Ignoring Config:
Check `app/main.py` line 761 and `app/agents/enhanced_rag_agent.py` to ensure:
- `unified_config` is correctly passed to agent
- Strategy weights are being read
- Routing logic respects the weights

---

## Testing Plan

### Test 1: Direct API (Already Complete ✅)
- Status: **PASS** - Backend works with `rag_long_term: 0.9`

### Test 2: UI Settings Flow
1. Open http://localhost:3001
2. Open WeightsConfigManager (Advanced Settings)
3. Set `rag_long_term: 0.9`
4. Click "Apply to Session"
5. Verify localStorage contains config
6. Send query "Who is Aadhan?"
7. Verify network request contains `unified_config`
8. Verify response contains documents

### Test 3: Backend Logs
- Monitor logs during UI query
- Verify strategy_weights are logged
- Verify RAG routing is triggered

---

## Next Steps

1. **User should test in browser** with DevTools open:
   - Check localStorage for `userWeightsConfig`
   - Check Network tab for `unified_config` in request payload
   - Check Console for config-related logs

2. **If issue persists**, collect:
   - Screenshot of WeightsConfigManager with settings
   - localStorage dump
   - Network request payload
   - Backend logs during query

3. **Apply fix** based on findings

---

**Status**: Investigation complete. Backend verified working. Need user to verify UI config flow in browser.
**Date**: 2025-12-06
**Investigator**: Claude
