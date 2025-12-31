# Comprehensive Chat UI E2E Test Plan

**Date Created**: 2025-12-01
**Purpose**: Validate all critical chat UI functionality
**Status**: 🚧 **READY TO EXECUTE**

---

## 📊 Test Summary

**Total Test Cases**: 9
**Test Suites**: 7
**Est. Execution Time**: 15-20 minutes

---

## 🎯 Test Coverage

### ✅ Covered Features

1. **Basic Chat Functionality** - Messaging works
2. **Model Selection** - Critical! Verify selected model is actually used
3. **File Uploads** - Files upload to correct projects
4. **Project Switching** - Sessions retained per project
5. **RAG Settings** - Settings affect retrieval
6. **Chat History** - History persists across sessions
7. **Navigation** - Session retained when switching tabs

###

 ⏳ Planned for Future

8. **Prompt Library** - Use prompts from library
9. **Export Functionality** - Excel/Word/JSON export

---

## 🔴 CRITICAL: Model Selection Bug

**User Report**: "Model selection isn't working consistently - the selected model should exactly be the one via which the LLM should respond."

**Tests Created** (TC_CHAT_002, TC_CHAT_003, TC_CHAT_004):
- Test GPT-4 selection and verification
- Test Claude selection and verification
- Test Ollama selection and verification

**Verification Method**:
1. Select model from dropdown
2. Send test message
3. Verify model indicator in response
4. Check backend logs (manual)

**Expected Behavior**: Backend API call should use EXACT model from dropdown

---

## 📋 Test Cases

### TC_CHAT_001: Basic Chat Messaging
**Priority**: P0
**Description**: Verify basic chat works
**Steps**:
1. Send message "Hello"
2. Wait for response
3. Verify response is not empty

**Expected**: Response received with content

---

### TC_CHAT_002: Model Selection - GPT-4 ⚠️ CRITICAL
**Priority**: P0
**Description**: Verify GPT-4 is actually used when selected
**Steps**:
1. Select GPT-4 from dropdown
2. Send message "What model are you?"
3. Verify GPT-4 indicator in response
4. Check backend used GPT-4

**Expected**: Backend API call uses `model: "gpt-4"`

**How to Verify**:
- Check Network tab in DevTools
- Look for `/api/v1/query` or `/api/v1/chat` request
- Request body should have `"model": "gpt-4"`

---

### TC_CHAT_003: Model Selection - Claude ⚠️ CRITICAL
**Priority**: P0
**Description**: Verify Claude is actually used when selected
**Steps**: Same as GPT-4 but for Claude

**Expected**: Backend uses `model: "claude-3-*"`

---

### TC_CHAT_004: Model Selection - Ollama ⚠️ CRITICAL
**Priority**: P0
**Description**: Verify local Ollama model works
**Steps**: Same as GPT-4 but for Ollama

**Expected**: Backend uses `model: "ollama/mistral"` or similar

**Note**: Longer timeout needed for local models

---

### TC_CHAT_005: File Upload to Project
**Priority**: P0
**Description**: Files uploaded to correct project
**Steps**:
1. Select "Default Project"
2. Upload test file
3. Verify file appears in uploads list
4. Query file content
5. Verify content retrieved

**Expected**: File associated with selected project

---

### TC_CHAT_006: Project Switching with Session Retention ⚠️ CRITICAL
**Priority**: P0
**Description**: Each project has independent session
**Steps**:
1. Project A: Send message, count messages
2. Switch to Project B
3. Project B: Send different message
4. Switch back to Project A
5. Verify Project A still has original messages

**Expected**: Sessions completely isolated per project

---

### TC_CHAT_007: RAG Settings Impact
**Priority**: P1
**Description**: RAG settings affect retrieval
**Steps**:
1. Upload document
2. Set top_k=3, query document
3. Set top_k=10, query again
4. Compare responses

**Expected**: Different top_k values affect retrieval

---

### TC_CHAT_008: Chat History Persistence
**Priority**: P1
**Description**: Chat history saved and retrievable
**Steps**:
1. Send unique message
2. Start new chat
3. Access chat history
4. Select previous chat
5. Verify original messages restored

**Expected**: Chat history persists

---

### TC_CHAT_009: Navigation with Session Retention
**Priority**: P0
**Description**: Session retained across tab navigation
**Steps**:
1. Send message in Chat tab
2. Navigate to Settings tab
3. Navigate back to Chat tab
4. Verify messages still present

**Expected**: Session not lost during navigation

---

## 🧪 How to Run Tests

### Prerequisites
```bash
# Ensure app is running
docker-compose ps

# Activate test environment
source virtual_env_for_testing/bin/activate
```

### Run All Chat UI Tests
```bash
cd /mnt/c/AIML/ClaudeCode/chatbot/ChatBot
pytest backend/tests/playwright/test_chat_ui_comprehensive.py -v
```

### Run Single Test
```bash
# Test model selection (CRITICAL)
pytest backend/tests/playwright/test_chat_ui_comprehensive.py::test_model_selection_gpt4 -vvs

# Test basic messaging
pytest backend/tests/playwright/test_chat_ui_comprehensive.py::test_chat_basic_messaging -vvs
```

### Run in Visual Mode (Slow Motion)
```bash
export HEADLESS=false
export SLOW_MO=1000
pytest backend/tests/playwright/test_chat_ui_comprehensive.py::test_model_selection_gpt4 -vvs
```

---

## 🔍 Debug Model Selection Issue

If tests reveal model selection is broken, here's how to investigate:

### Step 1: Browser DevTools Investigation
1. Open app in browser (F12 for DevTools)
2. Go to Network tab
3. Select model from dropdown
4. Send message
5. Find the API request (`/api/v1/query` or similar)
6. Check request payload:
   ```json
   {
     "query": "test message",
     "model": "gpt-4",  // ← Should match dropdown selection
     "session_id": "...",
     ...
   }
   ```

### Step 2: Frontend Code Check
**File**: `frontend/src/components/ModelSelector.tsx` or `ChatInterface.tsx`

**Look for**:
```typescript
// Model state
const [selectedModel, setSelectedModel] = useState('gpt-4');

// When dropdown changes
const handleModelChange = (event) => {
  setSelectedModel(event.target.value);  // ← Is this being called?
};

// When sending message
const sendMessage = async (message) => {
  await fetch('/api/v1/query', {
    method: 'POST',
    body: JSON.stringify({
      query: message,
      model: selectedModel,  // ← Is this using current state?
    })
  });
};
```

**Common Bug**: Model state not being passed to API call

### Step 3: Backend Code Check
**File**: `backend/app/api/routes/*.py`

**Look for**:
```python
@router.post("/api/v1/query")
async def query(request: QueryRequest):
    model = request.model  # ← Is this being used?

    # Should use requested model, not hardcoded
    response = await llm_service.query(
        query=request.query,
        model=model  # ← Not hardcoded!
    )
```

**Common Bug**: Hardcoded model instead of using request.model

### Step 4: Check Backend Logs
```bash
# Watch backend logs during test
docker-compose logs -f backend | grep -i "model\|gpt\|claude"

# Should see lines like:
# "Using model: gpt-4"
# "LLM service initialized with model: gpt-4"
```

---

## 🐛 Known Issues to Watch For

### Issue 1: Model State Not Syncing
**Symptom**: Dropdown shows one model, but different model responds

**Cause**: Frontend state not updating or not being sent to backend

**Fix**: Ensure state updates and API calls use latest state

---

### Issue 2: Default Model Overriding Selection
**Symptom**: Always uses default model regardless of selection

**Cause**: Backend ignoring `model` parameter from request

**Fix**: Backend should respect `request.model`, not use default

---

### Issue 3: Model Persisting Across Sessions
**Symptom**: New chat keeps previous chat's model

**Cause**: Model state not resetting on new chat

**Fix**: Reset model state when starting new chat

---

## 📊 Expected Test Results

### Best Case (All Working)
```
TC_CHAT_001: ✅ PASSED
TC_CHAT_002: ✅ PASSED (GPT-4 verified)
TC_CHAT_003: ✅ PASSED (Claude verified)
TC_CHAT_004: ✅ PASSED (Ollama verified)
TC_CHAT_005: ✅ PASSED
TC_CHAT_006: ✅ PASSED
TC_CHAT_007: ✅ PASSED
TC_CHAT_008: ✅ PASSED
TC_CHAT_009: ✅ PASSED

Total: 9/9 PASSED (100%)
```

### Likely Case (Model Issue Confirmed)
```
TC_CHAT_001: ✅ PASSED (basic messaging works)
TC_CHAT_002: ⚠️ WARNING (can't verify model - needs investigation)
TC_CHAT_003: ⚠️ WARNING (can't verify model)
TC_CHAT_004: ⚠️ WARNING (can't verify model)
TC_CHAT_005: ✅ PASSED
TC_CHAT_006: ✅ PASSED
TC_CHAT_007: ✅ PASSED
TC_CHAT_008: ✅ PASSED
TC_CHAT_009: ✅ PASSED

Total: 6/9 PASSED, 3 WARNINGS
```

**If warnings occur**: Manual verification needed with browser DevTools

---

## 📁 Test Artifacts Generated

After running tests, check:

```
backend/tests/playwright/test_results/
├── chat_ui_test_report.html          # Interactive HTML report
├── chat_ui_test_report.json          # JSON report for CI/CD
└── TC_CHAT_*_step*_before/after.png  # Screenshots for each step
```

---

## 🔧 Test Maintenance

### When UI Changes
If selectors break, update `chat_page.py`:

```python
# Old selector (if it breaks)
MODEL_DROPDOWN = 'select'

# New selector (more flexible)
MODEL_DROPDOWN = 'select, [role="combobox"], button:has-text("Model")'
```

### Adding New Test Cases
1. Add test function to `test_chat_ui_comprehensive.py`
2. Use TestCase/TestStep pattern
3. Take before/after screenshots
4. Add to reporter

---

## 🎯 Priority Order for Fixes

If tests reveal issues:

1. **P0 - Model Selection** - CRITICAL, affects all LLM calls
2. **P0 - Project Session Isolation** - Data leakage risk
3. **P0 - Navigation Session Retention** - UX issue
4. **P1 - File Upload Project Association** - Data organization
5. **P1 - RAG Settings** - Feature functionality
6. **P2 - Chat History** - Convenience feature

---

## 📚 Related Documentation

- [CREATING_PLAYWRIGHT_TESTS_GUIDE.md](./CREATING_PLAYWRIGHT_TESTS_GUIDE.md) - How to create tests
- [Model Selection Bug Report](../debugging/MODEL_SELECTION_BUG_REPORT.md) - If created
- [Chat Page Object](../../backend/tests/playwright/page_objects/chat_page.py) - Page object reference

---

## 🚀 Next Steps

1. **Run tests**: Execute test suite
2. **Analyze results**: Check which tests pass/fail
3. **Investigate failures**: Use DevTools for model selection
4. **Fix bugs**: Update frontend/backend code
5. **Re-run tests**: Verify fixes work
6. **Document findings**: Update bug reports

---

**Status**: ✅ **READY TO RUN**
**Estimated Time**: 15-20 minutes for full suite
**Critical Focus**: Model selection verification

---

**Created**: 2025-12-01
**Author**: Claude AI Assistant
**Purpose**: Validate Chat UI and catch model selection bugs
