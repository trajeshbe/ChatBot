# Weights Config localStorage Save Issue Investigation

**Date**: 2025-12-06
**Issue**: RAG routing with `rag_long_term: 0.9` not working from UI - config not saving to localStorage
**Status**: 🔍 **INVESTIGATING ROOT CAUSE**

---

## User Report Timeline

1. **Initial Report**:
   > "can you check why the weight setting about .9 for Long term rag still wan't be able to route it to pick documents when i asked about 'Who is Aadhan' ? is the ui config setting working ?? it used to so.. ensure all the parameters are respected and used in the calls with right routing and right weights ..etc .. fix it and rebuld without cache"

2. **Root Cause Identified by User**:
   > "its not getting saved in the session UI local"

3. **Critical Context**:
   > "its not a button issue.. it was getting saved all the while .. the issue happend only after the cache issue with brain view"

---

## Key Facts

1. ✅ **Backend RAG Routing Works**: Direct API test with `rag_long_term: 0.9` successfully retrieves documents
2. ✅ **UI Config Code is Correct**: WeightsConfigManager.tsx saveToSession function (lines 200-217) is properly implemented
3. ✅ **ChatInterfaceEnhanced Loads Config**: Lines 267-295 correctly check localStorage first
4. ⚠️ **Issue Started After Brain View Fix**: The problem appeared AFTER the `--no-cache` frontend rebuild for Brain View inline implementation
5. ❌ **Config Not Persisting**: User confirms localStorage.setItem isn't working

---

## Investigation: What Changed During Brain View Fix?

### Changes Made to Frontend

**File**: `frontend/src/components/ChatInterfaceEnhanced.tsx`

**Change 1** - Line 237: Added Brain View state
```typescript
const [expandedBrainView, setExpandedBrainView] = useState<Record<number, boolean>>({})
```

**Change 2** - Lines 444-450: Added toggle function
```typescript
const toggleBrainViewExpansion = (index: number) => {
  setExpandedBrainView(prev => ({
    ...prev,
    [index]: !prev[index]
  }))
}
```

**Change 3** - Lines 1490-1606: Added 117 lines of inline Brain View JSX

**Rebuild**: `docker-compose stop frontend && docker-compose build --no-cache frontend && docker-compose up -d frontend`

### Potential Root Causes

#### Hypothesis 1: Browser Cache Stale JavaScript
- Browser is still loading old JavaScript from before the rebuild
- Hard refresh (Ctrl+Shift+R) should fix but user already tried
- **Test**: Open DevTools → Network tab → Check if files are loading from cache

#### Hypothesis 2: TypeScript/Build Error Not Visible
- Frontend rebuild might have hidden TypeScript errors
- WeightsConfigManager might not be properly compiled
- **Test**: Check frontend build logs for errors

#### Hypothesis 3: React State Conflict
- Adding new state (`expandedBrainView`) might have broken existing state management
- Unlikely but possible if there's a state initialization order issue
- **Test**: Check browser console for React errors

#### Hypothesis 4: localStorage API Blocked/Disabled
- Browser security settings might be blocking localStorage after container rebuild
- **Test**: Open browser console and manually test `localStorage.setItem('test', 'value')`

#### Hypothesis 5: WeightsConfigManager Not Mounted
- Component might not be rendering properly after rebuild
- **Test**: Check if WeightsConfigManager UI is visible and functional

---

## Debugging Steps for User

### Step 1: Verify Browser Can Access localStorage

Open browser console (F12) and run:
```javascript
// Test write
localStorage.setItem('test_key', 'test_value');

// Test read
console.log(localStorage.getItem('test_key')); // Should print: test_value

// Test delete
localStorage.removeItem('test_key');
```

**Expected Result**: Should work without errors
**If Fails**: Browser localStorage is disabled or blocked

---

### Step 2: Check Frontend Build Logs

```bash
docker logs rag-frontend --tail=100 2>&1 | grep -i -E "(error|failed|warning)"
```

**Look For**:
- TypeScript compilation errors
- Module resolution failures
- Build warnings that might indicate issues

---

### Step 3: Test WeightsConfigManager Directly

1. Open http://localhost:3001
2. Open browser DevTools (F12)
3. Go to Console tab
4. Open WeightsConfigManager (Advanced Settings)
5. Adjust `rag_long_term` slider to 0.9
6. Click "Apply to My Session" button
7. **Watch console for**:
   - ✅ Expected: `🔔 Dispatched weightsConfigUpdated event with 11 parameter groups`
   - ❌ Errors: JavaScript errors preventing save

---

### Step 4: Check localStorage After Save Attempt

In browser console:
```javascript
// Check if config exists
const config = localStorage.getItem('userWeightsConfig');
console.log('Config exists:', config !== null);

// Parse and inspect
if (config) {
  const parsed = JSON.parse(config);
  console.log('rag_long_term weight:', parsed.strategy_weights?.rag_long_term);
  console.log('Full config:', parsed);
} else {
  console.log('❌ No config found in localStorage');
}
```

**Expected Result**: Should show `rag_long_term: 0.9`
**If Null**: Save is failing silently

---

### Step 5: Check Network Request When Sending Query

1. Keep DevTools open → Network tab
2. Send query: "Who is Aadhan?"
3. Click on `/api/v1/query` request
4. Go to "Payload" tab
5. **Look for** `unified_config` field

**Expected**:
```
unified_config: {"strategy_weights":{"rag_long_term":0.9,...},...}
```

**If Missing**: ChatInterfaceEnhanced isn't loading config from localStorage

---

## Potential Fixes

### Fix 1: Clear Browser Cache Completely

**Windows**:
```
Ctrl + Shift + Delete → Select "Cached images and files" → Clear
```

**Then**:
1. Close ALL browser tabs for localhost:3001
2. Close browser completely
3. Reopen browser
4. Navigate to http://localhost:3001
5. Try saving config again

---

### Fix 2: Force Frontend Rebuild with Timestamp

Add cache-busting to Next.js build:

```bash
# Stop frontend
docker-compose stop frontend

# Clear Docker build cache
docker builder prune -f

# Rebuild with no cache
docker-compose build --no-cache frontend

# Restart
docker-compose up -d frontend

# Wait 60 seconds for build
sleep 60

# Check status
docker-compose ps frontend
```

---

### Fix 3: Add Console Logging to saveToSession

**File**: `frontend/src/components/WeightsConfigManager.tsx`
**Line**: 200-217

Add debug logging:
```typescript
const saveToSession = () => {
  console.log('🔧 saveToSession called');
  console.log('   config:', config);

  if (!config) {
    console.error('❌ Config is null, cannot save');
    return;
  }

  try {
    console.log('💾 Attempting localStorage.setItem...');
    localStorage.setItem('userWeightsConfig', JSON.stringify(config));
    console.log('✅ localStorage.setItem SUCCESS');

    setHasSessionConfig(true);
    setSuccess('Settings applied to your session! These will be used for your queries.');
    setTimeout(() => setSuccess(null), 5000);

    // Dispatch custom event to notify ChatInterface that config was updated
    const event = new CustomEvent('weightsConfigUpdated', { detail: config });
    window.dispatchEvent(event);
    console.log('🔔 Dispatched weightsConfigUpdated event with', Object.keys(config).length, 'parameter groups');
  } catch (err) {
    console.error('❌ localStorage.setItem FAILED:', err);
    setError('Error saving to session: ' + (err as Error).message);
  }
};
```

Then rebuild frontend and test again.

---

### Fix 4: Verify ChatInterfaceEnhanced Listener

Check if event listener is properly set up:

**File**: `frontend/src/components/ChatInterfaceEnhanced.tsx`
**Lines**: 318-334

Add logging to verify listener is active:
```typescript
const handleConfigUpdate = (e: CustomEvent) => {
  console.log('📨 weightsConfigUpdated event received');
  if (e.detail) {
    setUnifiedConfig(e.detail);
    console.log('🔄 Config updated from custom event with', Object.keys(e.detail).length, 'parameter groups');
    console.log('   rag_long_term:', e.detail.strategy_weights?.rag_long_term);
  } else {
    console.warn('⚠️ Event detail is empty');
  }
}

// In useEffect
useEffect(() => {
  console.log('🎧 Setting up weightsConfigUpdated listener');

  document.addEventListener('visibilitychange', handleVisibilityChange)
  window.addEventListener('storage', handleStorageChange as EventListener)
  window.addEventListener('weightsConfigUpdated', handleConfigUpdate as EventListener)

  return () => {
    console.log('🔌 Removing weightsConfigUpdated listener');
    document.removeEventListener('visibilitychange', handleVisibilityChange)
    window.removeEventListener('storage', handleStorageChange as EventListener)
    window.removeEventListener('weightsConfigUpdated', handleConfigUpdate as EventListener)
  }
}, [])
```

---

## Next Steps

1. **User runs Step 1-5** to collect debugging information
2. **Report findings** with screenshots/console logs
3. **Apply appropriate fix** based on root cause
4. **Rebuild and test** end-to-end

---

## Related Documentation

- RAG Routing Investigation: `docs/fixes/RAG_ROUTING_UI_CONFIG_INVESTIGATION.md`
- Brain View Implementation: `docs/fixes/BRAIN_VIEW_INLINE_COMPLETE_SUCCESS.md`

---

**Created**: 2025-12-06
**Last Updated**: 2025-12-06
**Status**: Awaiting user debugging results
