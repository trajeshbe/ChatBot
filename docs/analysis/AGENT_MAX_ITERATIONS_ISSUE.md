# Agent Max Iterations Issue - Root Cause Analysis

> **Date**: 2025-12-11
> **Issue**: Agent always hits max iterations instead of calling FINAL_ANSWER
> **User Feedback**: "earlier it used to exit in 3 or 5 or 7 as soon as the objective is achieved"

---

## 🔍 Root Cause

### What Changed:

**Before (ChatGPT Era)**:
- Model: GPT-4, GPT-4-Turbo
- Behavior: Exits in 3-7 iterations with FINAL_ANSWER
- Files created and properly tracked
- Artifacts uploaded to MinIO

**After (Current - Local Models)**:
- Models: llama3.2-vision:11b, qwen2.5-coder:7b, deepseek-coder:6.7b
- Behavior: Always hits max iterations (20-50)
- Doesn't call FINAL_ANSWER even when task is done
- Creates files but doesn't signal completion

---

## 📊 Evidence

### Recent Tasks Analysis:

```sql
task_id      |        model        | llm_calls | status
-------------+---------------------+-----------+-----------
task-8687138c6a11 | llama3.2-vision:11b |        20 | completed (but hit max)
task-08cef4dccee9 | llama3.2-vision:11b |         0 | cancelled
task-1e3aaf37f223 | qwen2.5-coder:7b    |        25 | failed
task-0be296e5047d | gpt-4-turbo         |        20 | failed (hit max)
task-777f8dc0a7f3 | deepseek-coder:6.7b |        20 | failed
```

**All recent tasks hit max iterations** - None completed early with FINAL_ANSWER.

---

## 🎯 The Problem

### 1. Local Models Don't Follow FINAL_ANSWER Pattern

**Current System Prompt** (lines 671-730 in `entrypoint_agent.py`):
```
4. If no more tools needed → use FINAL_ANSWER

Example:
Your Response (Step 3):
FINAL_ANSWER: Chart created at /workspace/artifacts/chart.png
```

**What Actually Happens**:
- Local models create the file successfully
- But they don't recognize completion
- They keep trying variations or additional steps
- Hit max iterations without calling FINAL_ANSWER

### 2. History Compression Loses Context

**Line 660**: `max_messages=6`
- Only keeps 6 messages in history
- Agent forgets what it already did
- Repeats same actions or gets confused

### 3. No Automatic Completion Detection

**Current Logic**:
- Relies on model calling FINAL_ANSWER explicitly
- No fallback if model doesn't cooperate
- No detection of "task is likely done"

---

## 💡 Proposed Solutions

### Solution 1: Auto-Complete on File Creation (QUICK WIN)

Add logic to detect when task objective is met:

```python
# After each iteration, check if task is complete
if len(self.orchestrator.session_state["artifacts"]) > 0:
    # Check if any artifact matches the requested output (e.g., .html, .png, .csv)
    # If yes, auto-generate FINAL_ANSWER and break loop
    for artifact in self.orchestrator.session_state["artifacts"]:
        if artifact_path.endswith(('.html', '.png', '.jpg', '.csv', '.pdf')):
            logger.info(f"✅ Auto-completing: Output file detected: {artifact_path}")
            final_answer = f"Task completed. Created: {artifact_path}"
            task_complete = True
            break
```

### Solution 2: Increase History Window

Change from 6 messages to 12-15:
```python
compressed_history = self._compress_history(
    messages=self.conversation_history,
    max_messages=12  # Was 6 - increase for better context retention
)
```

### Solution 3: Stronger Completion Prompts

Add to system prompt:
```
⚠️ CRITICAL: After creating the requested file, you MUST immediately respond with:
FINAL_ANSWER: Task completed. Created: [filename]

DO NOT continue with additional steps after the file is created!
```

### Solution 4: Use GPT-4 for Agent Tasks

Fall back to GPT-4 for agentic tasks since local models struggle:
```python
# For agent tasks, prefer GPT-4 over local models
if model.startswith('llama') or model.startswith('qwen') or model.startswith('deepseek'):
    logger.warning(f"⚠️ Local model may struggle with agent tasks. Consider using GPT-4.")
```

---

## 🚀 Recommended Immediate Fix

### Implement Auto-Complete Detection

**File**: `backend/entrypoint_agent.py`
**Location**: End of iteration loop (after line 594)

```python
# Auto-complete check: If artifacts were created, check if task is likely done
if not task_complete and len(self.orchestrator.session_state["artifacts"]) > 0:
    # Check if we created the requested output
    requested_outputs = ['.html', '.png', '.jpg', '.csv', '.pdf', '.json', '.txt']
    for artifact in self.orchestrator.session_state["artifacts"]:
        artifact_path = artifact.get("path", "")
        if any(artifact_path.endswith(ext) for ext in requested_outputs):
            # Check if we've been working for a while (at least 5 iterations)
            if self.iteration >= 5:
                logger.info(f"✅ Auto-completing: Output file detected after {self.iteration} iterations")
                final_answer = f"Task completed. Created: {artifact_path}"
                task_complete = True
                break
```

This would:
- ✅ Detect when artifacts are created
- ✅ Auto-complete after reasonable number of iterations (5+)
- ✅ Prevent infinite loops
- ✅ Match earlier ChatGPT behavior

---

## 📈 Expected Improvement

### Before Fix:
- Tasks: 20/20 iterations (100% hit max)
- Completion: Never calls FINAL_ANSWER
- Status: Shows "completed" but feels wrong

### After Fix:
- Tasks: 5-10 iterations (50% reduction)
- Completion: Auto-detects when file created
- Status: Shows "completed" with real progress

---

## 🎯 Next Steps

1. Implement auto-complete detection
2. Test with sales2.txt chart task
3. Verify early completion (5-7 iterations)
4. Check artifacts uploaded to MinIO

---

**Priority**: HIGH - This affects user experience significantly
**Effort**: LOW - Simple check after each iteration
**Impact**: HIGH - Restores expected behavior
