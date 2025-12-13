# Chat Session Persistence Debug Guide

## Issue
When navigating between tabs (chat → other menu → back to chat), messages appear to be lost or reset.

## Root Cause Analysis

### Current Architecture
1. **Component Mounting** (`index.tsx:137`):
   - ChatInterface stays mounted but hidden when switching tabs
   - Uses CSS `hidden` class, component is NOT unmounted

2. **Session Storage**:
   - Session ID stored in `sessionStorage` (temporary, cleared on tab close)
   - Messages stored in `localStorage` with key `chat_messages_{sessionId}`
   - Global session key: `session_global`
   - Project-specific keys: `session_project_{projectId}`

3. **Message Loading** (`ChatInterfaceEnhanced.tsx:536-562`):
   - Loads messages from localStorage ONCE on component mount
   - Does NOT reload when switching tabs (by design, component stays mounted)

## Debugging Steps

### 1. Check Browser Console
Open browser DevTools (F12) and look for these log messages:

```
📥 Loaded X messages for session {sessionId}
💾 Debounced save: X messages for session {sessionId}
🔄 Switching session from {old} to {new}
```

### 2. Check localStorage
Run this in browser console:

```javascript
// Check current session
console.log('Session ID:', sessionStorage.getItem('chat_session_id'));
console.log('Global Session:', localStorage.getItem('session_global'));

// Check saved messages
Object.keys(localStorage)
  .filter(key => key.startsWith('chat_messages_'))
  .forEach(key => {
    const messages = JSON.parse(localStorage.getItem(key));
    console.log(key, ':', messages.length, 'messages');
  });
```

### 3. Check Component State
Add this temporarily to ChatInterfaceEnhanced.tsx after line 332:

```typescript
// DEBUG: Log component state changes
useEffect(() => {
  console.log('🔍 Component State:', {
    sessionId,
    messageCount: messages.length,
    activeTab,
    selectedProjectId,
    isHydrated
  });
}, [sessionId, messages.length, activeTab, selectedProjectId, isHydrated]);
```

## Potential Issues & Fixes

### Issue 1: localStorage Quota Exceeded
**Symptom**: Messages not saving
**Check**: Look for "QuotaExceededError" in console
**Fix**: Already handled with fallback at line 253-286

### Issue 2: Session ID Changing
**Symptom**: Different session loaded each time
**Check**: Compare sessionId in console logs
**Fix**: Session should persist in sessionStorage for same browser tab

### Issue 3: Component Remounting
**Symptom**: Initial load message appears each time
**Check**: Look for "📥 Loaded" messages when switching tabs
**Fix**: Component should stay mounted (verify index.tsx:137)

### Issue 4: Browser Tab Refresh
**Symptom**: Messages lost after page refresh
**Cause**: sessionStorage is cleared on page close/refresh
**Expected Behavior**: New session created, old messages available via Chat History

### Issue 5: Project Switching
**Symptom**: Messages change when project changes
**Cause**: Different projects have different sessions
**Expected Behavior**: Each project has its own chat session

## Recommended Fix

The component SHOULD preserve state when switching tabs. If it's not working:

### Fix 1: Add Session Persistence Key
Ensure the component has a stable key in index.tsx:

```tsx
<ChatInterface
  key={sessionId || 'default-session'}  // Add this
  activeTab={activeTab}
  ragConfig={ragConfig}
  projectId={selectedProjectId}
/>
```

### Fix 2: Save Messages on Tab Switch
Add visibility change listener to save messages immediately:

```typescript
useEffect(() => {
  const handleVisibilityChange = () => {
    if (document.visibilityState === 'hidden' && sessionId && messages.length > 0) {
      saveMessages(sessionId, messages);
      console.log('💾 Saved messages on tab switch');
    }
  };

  document.addEventListener('visibilitychange', handleVisibilityChange);
  return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
}, [sessionId, messages]);
```

### Fix 3: Reload Messages on Tab Return
Add focus listener to reload messages when returning to tab:

```typescript
useEffect(() => {
  const handleFocus = () => {
    if (sessionId && isHydrated) {
      const loadedMessages = loadMessages(sessionId);
      if (loadedMessages.length !== messages.length) {
        console.log('🔄 Reloaded messages on tab focus');
        setMessages(loadedMessages);
      }
    }
  };

  window.addEventListener('focus', handleFocus);
  return () => window.removeEventListener('focus', handleFocus);
}, [sessionId, messages.length, isHydrated]);
```

## Testing Procedure

1. **Start a chat**: Send 2-3 messages
2. **Switch to another tab**: e.g., Evaluation
3. **Check console**: Should NOT see "📥 Loaded" message (component stays mounted)
4. **Switch back to chat**: Messages should still be visible
5. **Check localStorage**: Run debug command above
6. **Refresh page**: Messages gone (expected - sessionStorage cleared)
7. **Go to Chat History**: Should see previous session with messages

## Expected Behavior

✅ **Within same browser session**: Messages persist when switching tabs
❌ **After page refresh**: New session created (old messages in history)
✅ **Different projects**: Separate chat sessions per project
✅ **localStorage backup**: Messages saved every 1 second after changes

## Quick Test

Run this in browser console while on chat tab:

```javascript
// Get current session and message count
const sessionId = sessionStorage.getItem('chat_session_id');
const messagesKey = `chat_messages_${sessionId}`;
const messages = JSON.parse(localStorage.getItem(messagesKey) || '[]');

console.log('Session ID:', sessionId);
console.log('Messages stored:', messages.length);
console.log('First message:', messages[0]);
console.log('Last message:', messages[messages.length - 1]);

// Verify messages are actually saved
if (messages.length === 0) {
  console.error('❌ No messages in localStorage!');
} else {
  console.log('✅ Messages are persisted');
}
```
