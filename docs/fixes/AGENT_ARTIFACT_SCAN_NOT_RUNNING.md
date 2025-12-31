# Agent Artifact Scan Not Running - Investigation

> **Date**: 2025-12-11
> **Status**: 🔍 Under Investigation
> **Issue**: Final artifact scan code exists but doesn't execute

---

## 🎯 Current Situation

**What Works**:
- ✅ Agent completes in 4 iterations (not 20) - auto-complete working
- ✅ Agent uses `os.chdir('/workspace')` correctly in generated code
- ✅ File is created successfully: `/workspace/artifacts/sales_report_123.html` (3.6MB)
- ✅ Task marked as "completed" with success=true

**What's Broken**:
- ❌ Artifacts array in result.json is empty: `"artifacts": []`
- ❌ Database only shows input file: `{/workspace/sales2.txt}`
- ❌ No MinIO upload of output file
- ❌ No download button in UI

---

## 🔍 Investigation Findings

### 1. File Creation - WORKS ✅

```bash
$ docker exec rag-agent-runtime find /workspace -name "*.html" -mmin -5
/workspace/artifacts/sales_report_123.html
```

File exists at correct location.

### 2. Agent Code - WORKS ✅

From result.json conversation_history:
```python
import plotly.express as px
import pandas as pd
import os
# Change to workspace to access files
os.chdir('/workspace')
df = pd.read_csv('sales2.txt', sep='\\t', parse_dates=['date'])
os.makedirs('artifacts', exist_ok=True)
fig = px.bar(df, x='product', y='revenue', title='Sales Report')
fig.write_html('artifacts/sales_report_123.html')
print('Chart saved successfully')
```

Agent correctly:
- Changes to `/workspace/` directory
- Creates `artifacts/` directory
- Saves file with relative path

### 3. Final Scan Code - EXISTS BUT DOESN'T RUN ❌

**Code Location**: `backend/entrypoint_agent.py` lines 622-662

```python
# Line 625
logger.info("🔍 Running final artifact scan after loop completion...")
```

**Expected**: This log should appear after the while loop completes
**Actual**: Log never appears in backend output
**Conclusion**: Code exists but is not being executed

### 4. Code Structure Analysis

```python
# Line 466 - While loop starts
while self.iteration < self.max_iterations and not task_complete:
    # ... loop body (lines 467-620)

# Line 622-662 - Final scan code
# 🆕 FINAL ARTIFACT SCAN - Scan workspace one more time AFTER loop completes
logger.info("🔍 Running final artifact scan after loop completion...")
# ... scan logic ...

# Line 664-675 - Build result
result = {
    "success": task_complete,
    "final_answer": final_answer,
    "iterations": self.iteration,
    "artifacts": self.orchestrator.session_state["artifacts"],  # Empty!
    ...
}

# Line 678 - Return
return result
```

**Indentation Analysis**:
- Line 466: `while` statement at 8 spaces
- Line 467-620: Loop content at 12+ spaces
- Line 622: Comment at 8 spaces (should be outside loop)
- Line 625: logger.info at 8 spaces (should be outside loop)
- Line 664: Build result at 8 spaces (IS outside loop - executes)
- Line 678: Return at 8 spaces (IS outside loop - executes)

**Problem**: Lines 622-662 are at 8 spaces (same as while statement), which suggests they should be outside the loop. But they're not executing. This indicates a **Python indentation structure issue**.

### 5. Backend Extraction - PARTIAL ✅

From backend logs:
```
📎 Extracted 1 artifact paths from conversation (NOTE: existence not verified)
```

Backend IS extracting artifact paths from the conversation, but:
- Database only shows input file `/workspace/sales2.txt`
- Output file `/workspace/artifacts/sales_report_123.html` not in database

---

## 🐛 Root Cause Hypothesis

The final artifact scan code (lines 622-662) is at the correct indentation level (8 spaces) to be OUTSIDE the while loop, but it's not being executed. Possible causes:

### Theory 1: Still Inside While Loop
Despite being at 8 spaces (same as `while` statement), the Python interpreter might still consider it inside the loop due to:
- Improper dedenting after nested blocks
- Empty line issues (line 621 has only 1 space)
- Carriage return (^M) issues in file

### Theory 2: Early Return
Something is causing an early return before reaching the final scan code. But this doesn't explain why the result dict (line 664) IS being built and returned.

### Theory 3: Exception Being Swallowed
An exception might be raised in the final scan code but is being caught and ignored somewhere.

---

## 🔧 Proposed Solutions

### Solution 1: Move Final Scan to Separate Function

Extract the final scan logic into a separate function that's called explicitly:

```python
def _final_artifact_scan(self):
    """Scan workspace for artifacts after loop completes"""
    logger.info("🔍 Running final artifact scan...")
    # ... scan logic ...

# In run() method, after while loop:
while self.iteration < self.max_iterations and not task_complete:
    # ... loop body ...

# Explicitly call final scan
self._final_artifact_scan()

# Build result
result = {...}
return result
```

### Solution 2: Backend Extraction from final_answer

Since the agent's final_answer contains the file path, extract it in the backend:

```python
# agent_service.py
final_answer = agent_result.get("final_answer", "")
if "saved to" in final_answer.lower() or "created" in final_answer.lower():
    # Extract file path from final_answer
    import re
    matches = re.findall(r'/workspace/[\w/\-\.]+\.(html|png|pdf|csv|xlsx)', final_answer)
    for match in matches:
        # Verify file exists in container
        # Add to artifacts list
```

### Solution 3: Scan in Backend Instead of Agent

Move the artifact scanning logic to the backend after the agent completes:

```python
# In agent_service.py, after task completes:
# Scan container workspace for output files
exec_result = await docker_client.exec_run(
    f"find /workspace/artifacts -type f -newer /workspace/sales2.txt"
)
# Parse output and add to artifacts
```

---

## 🎯 Recommended Next Steps

1. **Immediate**: Implement Solution 2 (backend extraction from final_answer)
   - Quick fix that doesn't require understanding the indentation issue
   - Works with existing agent code
   - Can be done in agent_service.py without rebuilding agent container

2. **Short-term**: Debug why final scan doesn't execute
   - Add explicit logging before/after final scan code
   - Check if there's a hidden return/exit
   - Verify Python interpretation of indentation

3. **Long-term**: Refactor to Solution 1 (separate function)
   - Cleaner code structure
   - Easier to test and debug
   - More reliable execution

---

## 📊 Impact

**User Experience**:
- Agent completes tasks successfully
- Files are created correctly
- BUT users can't download the files (no download button)
- No MinIO storage of outputs

**Severity**: HIGH - Core functionality broken
**Priority**: P0 - Blocks main use case

---

**Status**: Investigation complete, ready to implement Solution 2
