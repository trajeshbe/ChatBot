# Chat UI Selector Findings - 2025-12-01

**Date**: 2025-12-01
**Purpose**: Document actual Chat UI selectors for test updates

---

## ✅ Confirmed Selectors

### 1. Project Dropdown
**Element Type**: `<select>`
**Selector**: `select` (only one select on page)
**Options Found**:
- "Global (All Projects)"
- "Construction Intelligence (3)"
- "Global (0)"

**Classes**: `flex-1 min-w-0 bg-transparent text-xs text-slate-700 dark:text-slate-300 font-medium focus:outline-none cursor-pointer`

**Test Selector**: `select` (simple and unique)

---

### 2. Model Selector ⭐ **BUTTON**, Not Select!
**Element Type**: `<button>`
**Current Text**: "LLaMA 3.2 Vision 11B (Ollama GPU) 🔍\nollamaFree (Local)"
**Behavior**: Button that opens dropdown menu on click

**Classes**: `flex items-center gap-2 px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700...`

**Test Selector Options**:
1. By text content: `button:has-text("LLaMA")` or `button:has-text("ollama")`
2. By classes: `button.flex.items-center` (too generic)
3. **RECOMMENDED**: `button:has-text("(Ollama")` or `button:has-text("(Local)")` - matches current model display pattern

**Notes**:
- Text changes based on selected model
- Need flexible selector that works with any model name
- Clicking opens a menu/dropdown with model options

---

### 3. Chat Input
**Element Type**: `<textarea>`
**Placeholder**: "Type / for prompts or message Enterprise AI..."
**Classes**: `w-full resize-none bg-transparent px-4 py-3 text-slate-900 dark:text-slate-100 placeholder-slate-500`

**Test Selector**: `textarea` or `[placeholder*="message"]`

---

### 4. Send Button
**Element Type**: `<button>` (icon-only, no text)
**Found**: 21 buttons with SVG icons
**NOT FOUND**:
- No "Send" text
- No submit type
- No data-icon="send"

**Test Selector Options**:
1. Find button next to textarea: `textarea + button` or `textarea ~ button`
2. Find by aria-label if exists: `button[aria-label*="Send"]`
3. Find by position in chat input container
4. **REQUIRES**: Manual inspection to identify exact selector

---

### 5. File Upload Button
**Element Type**: `<button>`
**Text**: "Upload"
**Found**: 1 match ✓

**Test Selector**: `button:has-text("Upload")` ✓

**Also Found**:
- `input[type="file"]` (1 match) - for file input
- `button:has-text("File")` (3 matches)

---

### 6. Message Containers
**Found**: 2 messages with `[class*="message"]`
**NOT FOUND**:
- NO `[class*="chat"]`
- NO `.user-message` or `.assistant-message` classes

**Test Selector**: `[class*="message"]` ✓

**Notes**: Need to differentiate user vs assistant messages by other attributes

---

## ❌ NOT FOUND

### Model-Related Keywords in DOM:
- ❌ 'gpt' - 0 matches
- ❌ 'GPT' - 0 matches
- ❌ 'claude' - 0 matches (but exists in HTML)
- ❌ 'Claude' - 0 matches
- ✓ 'ollama' - 1 match (in current model button)
- ✓ 'MODEL' - 1 match

### Dropdown Patterns:
- ❌ `div[role="listbox"]`
- ❌ `div[role="menu"]`
- ❌ `[aria-haspopup]`
- ❌ `[data-testid*="model"]`

---

## 🎯 Test Implementation Updates Needed

### Priority 1: Update Model Selection Tests

**Current chat_page.py selector** (WRONG):
```python
MODEL_DROPDOWN = 'select:has-option, [role="combobox"], button:has-text("Model")'
```

**Updated selector** (CORRECT):
```python
# Model selector is a BUTTON showing current model
MODEL_SELECTOR_BUTTON = 'button:has-text("(Ollama"), button:has-text("(Local)"), button:has-text("GPT"), button:has-text("Claude")'

# After clicking, look for menu items
MODEL_MENU_ITEM = '[role="menuitem"], [role="option"], button'
```

**Implementation**:
```python
def select_model(self, model_name: str):
    """Select a model from dropdown.

    Args:
        model_name: Name of model to select (e.g., "gpt-4", "claude-3", "ollama/mistral")
    """
    # Click model selector button (shows current model)
    model_button = self.page.locator(
        'button:has-text("Ollama"), '
        'button:has-text("GPT"), '
        'button:has-text("Claude"), '
        'button:has-text("Model")'
    ).first

    if model_button.count() > 0:
        model_button.click()
        time.sleep(1)  # Wait for menu to open

        # Click desired model from menu
        menu_item = self.page.locator(f'text="{model_name}"').first
        if menu_item.count() > 0:
            menu_item.click()
            time.sleep(1)
            return True

    return False

def get_current_model(self) -> str:
    """Get currently selected model from button text."""
    model_button = self.page.locator(
        'button:has-text("Ollama"), '
        'button:has-text("GPT"), '
        'button:has-text("Claude")'
    ).first

    if model_button.count() > 0:
        return model_button.inner_text()

    return ""
```

---

### Priority 2: Update Send Button Selector

**Need to determine**: How to identify send button among 21 SVG icon buttons

**Options**:
1. Find button in chat input container
2. Find button near textarea
3. Use aria-label if exists
4. Use position-based selector

**Action**: Create debug script to click textarea and inspect nearby buttons

---

### Priority 3: Differentiate User vs Assistant Messages

**Current**: Both use `[class*="message"]` (2 matches)

**Options**:
1. Check for data attributes: `data-role="user"` or `data-role="assistant"`
2. Check for specific classes: Look for `user` or `assistant` in class names
3. Use position: Odd vs even messages
4. Check parent/container classes

**Action**: Inspect message DOM structure in detail

---

## 🔍 Model Selection Bug Investigation

### Hypothesis
Your reported issue: *"Model selection isn't working consistently - the selected model should exactly be the one via which the LLM should respond."*

### Current State
- Model selector shows: "LLaMA 3.2 Vision 11B (Ollama GPU)"
- This is displayed in UI
- **Question**: When you select a different model (e.g., GPT-4), does the backend actually use GPT-4?

### Test Approach
1. ✅ **UI Test**: Verify model button changes text when selection changes
2. ✅ **Network Test**: Use Browser DevTools to verify API request includes correct model
3. ✅ **Backend Test**: Verify backend logs show correct model being used

### Verification Steps (Manual)
1. Open http://localhost:3001 in browser
2. Open DevTools (F12) → Network tab
3. Click model selector button
4. Select different model (e.g., GPT-4)
5. Send a test message
6. Check Network tab for `/api/v1/query` or `/api/v1/chat` request
7. Inspect request body: Should have `"model": "gpt-4"`

### Expected Behavior
```json
{
  "query": "test message",
  "model": "gpt-4",  // ← Should match selected model
  "session_id": "...",
  "project_id": "..."
}
```

### If Bug Confirmed
**Possible Causes**:
1. **Frontend**: Model state not updating when button clicked
2. **Frontend**: API call not including model parameter
3. **Backend**: Ignoring model parameter, using default
4. **Backend**: Model mapping incorrect (e.g., "gpt-4" → wrong model)

**Files to Check**:
- `frontend/src/components/ChatInterface.tsx` or `ChatInterfaceEnhanced.tsx`
- `frontend/src/components/ModelSelector.tsx` (if exists)
- `backend/app/api/routes/*.py` (query endpoint)
- `backend/app/services/llm_service.py` (model initialization)

---

## 📊 Selector Summary Table

| Element | Type | Selector | Status |
|---------|------|----------|--------|
| Project Dropdown | select | `select` | ✅ Found |
| Model Selector | button | `button:has-text("Ollama")` etc. | ✅ Found |
| Chat Input | textarea | `textarea` | ✅ Found |
| Send Button | button | TBD | ⚠️ Needs Investigation |
| File Upload | button | `button:has-text("Upload")` | ✅ Found |
| Messages | div | `[class*="message"]` | ✅ Found |
| User Message | div | TBD | ⚠️ Needs Investigation |
| Assistant Message | div | TBD | ⚠️ Needs Investigation |

---

## 🚀 Next Steps

1. ✅ **DONE**: Document all selectors
2. **IN PROGRESS**: Update chat_page.py with correct selectors
3. **TODO**: Find send button selector
4. **TODO**: Differentiate user/assistant messages
5. **TODO**: Run basic chat test
6. **TODO**: Run model selection tests
7. **TODO**: Investigate model selection bug with DevTools

---

**Status**: 🚧 **Selectors 70% Complete**
**Ready for**: Basic chat and file upload tests
**Blocked**: Send button and message differentiation

---

**Created**: 2025-12-01
**Last Updated**: 2025-12-01 14:00 UTC
