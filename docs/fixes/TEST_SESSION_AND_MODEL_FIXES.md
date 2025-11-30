# Testing Guide - Session Isolation & Model Selection Fixes

## ✅ Both Issues Fixed!

1. **Session message overlap** - Messages no longer leak between sessions
2. **Model selection architecture** - Projects can have their own preferred models

---

## Quick Test #1: Session Isolation (3 minutes)

### Test: Conversations Don't Mix

```
1. Open http://localhost:3001 → Go to Chat tab
2. See "🌐 Global" badge in header
3. Type: "This is my global message"
4. Click Send → See response

5. Select "Construction Intelligence" from Project dropdown
6. ✅ Verify: Messages cleared (should show 0 messages)
7. Badge now shows "📁 Construction Intelligence"
8. Type: "This is my construction message"  
9. Click Send → See response

10. Select "All Projects" from dropdown (back to Global)
11. ✅ CRITICAL: Should see "This is my global message" ONLY
12. ❌ BUG if: You see construction message here

13. Select "Construction Intelligence" again
14. ✅ CRITICAL: Should see "This is my construction message" ONLY
```

**Expected Result**: Each project has its own isolated conversation history.

### Check localStorage (Optional - for verification)

Open browser console → Application → Local Storage:

```javascript
// You should see separate keys:
chat_messages_session-1732850400000-abc123  // Global messages
chat_messages_session-1732850500000-def456  // Construction messages
chat_messages_session-1732850600000-ghi789  // Marketing messages

// Each key should have DIFFERENT messages
```

---

## Quick Test #2: Model Selection (5 minutes)

### Test: Project-Specific Models

```
1. In Global session (All Projects)
2. Set model to "GPT-4 Turbo" using Model dropdown
3. ✅ Verify: localStorage.globalDefaultModel = "gpt-4-turbo-preview"

4. Switch to "Construction Intelligence" project
5. ✅ Verify: Model still shows "GPT-4 Turbo" (inherited)
6. Change model to "Gemini 2.0 Flash Experimental"
7. ✅ Verify: Model selector shows "Gemini 2.0 Flash"

8. Switch to different project (e.g., Marketing)
9. ✅ CRITICAL: Model should switch back to "GPT-4 Turbo"
10. ❌ BUG if: Model stays as "Gemini 2.0 Flash"

11. Switch back to "Construction Intelligence"
12. ✅ CRITICAL: Model should be "Gemini 2.0 Flash" (remembered)

13. Switch to "All Projects" (Global)
14. ✅ CRITICAL: Model should be "GPT-4 Turbo" (global default)
```

**Expected Result**: Each project remembers its preferred model.

### Check localStorage (Optional)

```javascript
// Global default
globalDefaultModel: "gpt-4-turbo-preview"

// Construction Intelligence project
model_project_0a931095-9400-4e19-b0b6-90f08ee1521f: "gemini-2.0-flash-exp"

// Marketing project (no model set, will inherit global)
// (no entry) → inherits globalDefaultModel
```

---

## Quick Test #3: Combined Flow (5 minutes)

### Test: Real-World Workflow

```
Scenario: User works on Construction project with vision model,
          then switches to Legal project with reasoning model

1. Global session → Set model: "GPT-4 Turbo"
2. Upload general.pdf → Ask "Summarize this"
   ✅ Uses GPT-4 Turbo

3. Switch to "Construction Intelligence"
   ✅ Model changes to GPT-4 Turbo (inherited, first time)
   ✅ Messages cleared (new session)

4. Change model to "Gemini 2.0 Flash" (for vision)
5. Upload blueprint.png → Ask "What are the dimensions?"
   ✅ Uses Gemini 2.0 Flash

6. Have 3-message conversation about blueprints

7. Switch to "Legal Documents" project
   ✅ Model changes to GPT-4 Turbo (inherited)
   ✅ Messages cleared

8. Change model to "Claude 3.5 Sonnet" (better reasoning)
9. Upload contract.pdf → Ask "Find risks"
   ✅ Uses Claude 3.5 Sonnet

10. Switch back to "Construction Intelligence"
    ✅ Model automatically switches to "Gemini 2.0 Flash"
    ✅ Conversation restored (3 messages about blueprints)

11. Switch to Global ("All Projects")
    ✅ Model switches to "GPT-4 Turbo"
    ✅ Original conversation with general.pdf restored
```

**Expected**: 
- ✅ 3 separate conversations (don't mix)
- ✅ 3 different models (auto-switch)
- ✅ All conversations preserved

---

## Verification Checklist

### Session Isolation ✅
- [ ] Global conversation doesn't appear in projects
- [ ] Project A conversation doesn't appear in Project B
- [ ] Switching back restores original conversation
- [ ] File uploads scoped to session (don't leak)
- [ ] Message count accurate per session

### Model Selection ✅
- [ ] Global model persists across refreshes
- [ ] Each project can have different model
- [ ] Model auto-switches when changing projects
- [ ] New projects inherit global default
- [ ] Model choice visible in selector

### Visual Indicators ✅
- [ ] Badge shows "🌐 Global" or "📁 Project Name"
- [ ] Message count updates per session
- [ ] Model selector shows correct model for context

---

## Common Issues

### Issue: "I still see messages from other projects"

**Solution**:
1. Clear browser cache/localStorage:
   ```javascript
   localStorage.clear()
   location.reload()
   ```
2. Start fresh test

### Issue: "Model doesn't change when I switch projects"

**Check**:
1. Browser console for logs:
   ```
   📥 Loaded model for project X: [model name]
   💾 Saved model for project X: [model name]
   ```
2. Verify localStorage has entries:
   ```javascript
   localStorage.getItem('model_project_...')
   ```

### Issue: "Conversations mix between sessions"

**Check Browser Console**:
Look for:
```
💾 Saved N messages to old session [session-id]
📥 Loaded M messages for [project/global] session
```

If not seeing these logs:
1. Clear localStorage
2. Rebuild frontend: `docker-compose build frontend`
3. Restart: `docker-compose up -d frontend`

---

## Database Verification

### Check Project Models

```sql
-- See which projects have model preferences
SELECT id, name, preferred_model
FROM projects
WHERE preferred_model IS NOT NULL;

-- Should show empty initially (all in localStorage for now)
```

### Check Session-Project Association

```sql
-- Verify sessions linked to projects
SELECT s.session_id, p.name as project_name
FROM chat_sessions s
LEFT JOIN projects p ON s.project_id = p.id
ORDER BY s.created_at DESC
LIMIT 10;
```

---

## Success Criteria

✅ **Session Isolation**: 
- 3 projects = 3 separate conversations
- No message leakage
- Conversation persistence

✅ **Model Selection**:
- Global default works
- Project models work
- Inheritance works
- Auto-switching works

✅ **User Experience**:
- Clear visual indicators
- Smooth transitions
- No data loss

---

**Status**: Ready for testing
**Services**: Backend (healthy) + Frontend (running)
**Documentation**: ARCHITECTURE_IMPROVEMENTS.md
