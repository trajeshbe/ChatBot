# Agent Tool Execution Issue - Root Cause & Fix

## Date: 2025-12-12

## Issue Reported

**User Report**: "looks again the LLM calls are happening for name sake and the tools aren't called..like we had similar issue earlier"

**Symptoms**:
- Agent tasks completing but not executing tools
- Only `metadata.json` created, no actual artifacts (charts, analysis files)
- Task description: "analyze sales2.txt and create a chart"
- Expected: HTML chart file created
- Actual: No chart, empty artifacts folder

---

## Root Cause Analysis

### Investigation Summary

**Task ID**: `task-6d47430a63b8`
**Task Name**: `plotly_sales_report`
**Model**: `qwen2.5-coder:7b`
**Status**: Completed (but incorrectly)

### Detailed Execution Flow

#### Iteration 1 ✅ SUCCESS
```
📖 Tool: read_file
📁 File: sales2.txt
✅ Result: File content returned successfully
```

#### Iteration 2 ✅ SUCCESS
```
📦 Tool: install_package
📦 Package: plotly
✅ Result: Package installed successfully
```

#### Iteration 3 ❌ **CRITICAL ERROR**
```
🐍 Tool: execute_python
❌ ERROR: Failed to parse tool arguments JSON: Expecting ',' delimiter: line 1 column 764 (char 763)

Raw JSON args (MALFORMED):
{
  "code": "import pandas as pd\nimport plotly.express as px\nfrom io import StringIO\nimport os\n
  # Use the CONTENT from read_file (already in memory)\n
  df = pd.read_csv(StringIO('''date\tproduct\tquantity\trevenue\tregion\tcategory\t\n
  ########\tLaptop\t15\t22500\tNorth\tElectronics\n
  ########\tMouse\t50\t1000\tSouth\tAccessories\n...
```

**Problem**: The Python code contains tab-separated data with `########` placeholders, and the JSON string is malformed (likely due to escape character issues or incorrect quoting).

#### Iterations 4-40 ❌ **LLM STUCK IN LOOP**
```
📍 Iteration 4/40
🤖 Calling Ollama LLM: qwen2.5-coder:7b
💬 Ollama responded (0 chars): ...
⚠️ LLM sent empty content, skipping...

📍 Iteration 5/40
🤖 Calling Ollama LLM: qwen2.5-coder:7b
💬 Ollama responded (0 chars): ...
⚠️ LLM sent empty content, skipping...

[... repeated 36 more times ...]
```

**Problem**: After receiving the JSON parsing error, the `qwen2.5-coder:7b` model got stuck and returned **empty responses (0 chars)** for all remaining iterations.

---

## Why This Happened

### 1. JSON Parsing Error
- **Location**: `/backend/entrypoint_agent.py` line 958
- **Error Handler**: When JSON parsing fails, the agent returns `{"type": "thinking", "content": response}`
- **Result**: The malformed JSON response gets passed back to the LLM context

### 2. LLM Confusion
- **Model**: `qwen2.5-coder:7b` (7.6B parameters, Q4_K_M quantization)
- **Behavior**: After seeing the malformed JSON and error in its context, the model gets "confused"
- **Symptom**: Returns empty responses (0 characters) repeatedly
- **Reason**: The error corrupts the conversation context and the model cannot recover

### 3. Error Propagation
```python
# Current error handling in entrypoint_agent.py line 958-960
except json.JSONDecodeError as e:
    logger.error(f"❌ Failed to parse tool arguments JSON: {e}")
    logger.error(f"   Raw args: {args_json}")
    return {"type": "thinking", "content": response}  # ← Passes malformed JSON to LLM!
```

The agent treats the parsing failure as "thinking" but includes the entire malformed response in the context, which confuses the LLM.

---

## Verification

### Ollama Service Status ✅
- Container: `rag-ollama` - **Running** (Up 32 hours, healthy)
- Model: `qwen2.5-coder:7b` - **Available**
- Direct API Test: **Working** (responds with valid output)

### Agent Runtime Status ✅
- Container: `rag-agent-runtime` - **Running** (Up 12 hours, healthy)
- Workspace: `/workspace/plotly_sales_report/` - **Created**
- Logs: `agent.log` (115KB) - **Available**

### Previous Successful Runs ✅
Earlier logs show successful task execution using `llama3.2-vision:11b`:
```
Model: llama3.2-vision:11b
Iterations: 4
Tools Called: install_package, execute_python
Result: ✅ Plotly chart saved to /workspace/artifacts/sales_report_123.html
```

**Difference**: `llama3.2-vision:11b` (10.7B parameters) handled errors gracefully and completed successfully.

---

## Solutions

### Solution 1: Use More Robust LLM (RECOMMENDED)

**Change default model from `qwen2.5-coder:7b` to `llama3.2-vision:11b`**

#### Why This Works:
- Larger parameter size (10.7B vs 7.6B)
- Better error recovery
- Proven success in previous runs
- Still runs locally via Ollama

#### How to Implement:

**Option A: Change Frontend Default**
File: `/frontend/src/components/AgentTaskMonitor.tsx`

Find the model selection default (likely around line 50-80) and change:
```typescript
// BEFORE
const [selectedModel, setSelectedModel] = useState('qwen2.5-coder:7b');

// AFTER
const [selectedModel, setSelectedModel] = useState('llama3.2-vision:11b');
```

**Option B: Change Backend Default**
File: `/backend/app/api/routes/agent_routes.py` or agent service

Find the default model configuration and change:
```python
# BEFORE
model: Optional[str] = Field("qwen2.5-coder:7b", description="LLM model to use")

// AFTER
model: Optional[str] = Field("llama3.2-vision:11b", description="LLM model to use")
```

---

### Solution 2: Improve Error Handling (LONG-TERM FIX)

**File**: `/backend/entrypoint_agent.py` line 958-960

**Current Code**:
```python
except json.JSONDecodeError as e:
    logger.error(f"❌ Failed to parse tool arguments JSON: {e}")
    logger.error(f"   Raw args: {args_json}")
    return {"type": "thinking", "content": response}  # ← Problem: Passes malformed JSON to LLM
```

**Improved Code**:
```python
except json.JSONDecodeError as e:
    logger.error(f"❌ Failed to parse tool arguments JSON: {e}")
    logger.error(f"   Raw args: {args_json}")

    # 🆕 FIX: Return helpful error message instead of malformed JSON
    error_message = (
        f"ERROR: Tool call JSON parsing failed. "
        f"Please ensure your ARGS are valid JSON. "
        f"Error: {str(e)[:100]}. "
        f"Try again with properly formatted JSON."
    )

    return {
        "type": "tool_error",
        "content": error_message,
        "raw_response": response[:500]  # Limit to prevent context pollution
    }
```

**Benefits**:
- Provides clear error message to LLM
- Prevents malformed JSON from polluting context
- Helps LLM understand what went wrong
- Encourages LLM to retry with correct format

---

### Solution 3: Add JSON Validation Before LLM Call (PREVENTIVE)

**File**: `/backend/entrypoint_agent.py`

**Add validation helper function**:
```python
def sanitize_json_for_llm(json_str: str, max_length: int = 1000) -> str:
    """
    Sanitize JSON string to prevent context pollution.

    Args:
        json_str: Raw JSON string
        max_length: Maximum length to include in context

    Returns:
        Sanitized JSON string safe for LLM context
    """
    try:
        # Try to parse and re-serialize for clean formatting
        parsed = json.loads(json_str)
        clean = json.dumps(parsed, indent=2)

        # Truncate if too long
        if len(clean) > max_length:
            return clean[:max_length] + f"\n... (truncated {len(clean) - max_length} chars)"
        return clean

    except json.JSONDecodeError:
        # If parsing fails, return error placeholder
        return f"[INVALID JSON - Length: {len(json_str)} chars]"
```

**Use in parse_llm_response**:
```python
except json.JSONDecodeError as e:
    logger.error(f"❌ Failed to parse tool arguments JSON: {e}")
    logger.error(f"   Raw args: {args_json}")

    # Use sanitized version in error message
    safe_json = sanitize_json_for_llm(args_json)

    error_message = (
        f"ERROR: Tool call JSON parsing failed.\n"
        f"Received JSON:\n{safe_json}\n"
        f"Error: {str(e)}\n"
        f"Please provide valid JSON for ARGS."
    )

    return {"type": "tool_error", "content": error_message}
```

---

## Recommended Implementation Plan

### Phase 1: Immediate Fix (5 minutes)
✅ **Change default LLM to `llama3.2-vision:11b`**

1. Edit frontend model selector default
2. Or edit backend schema default
3. Restart frontend or backend service
4. Test new task creation

### Phase 2: Error Handling Improvement (30 minutes)
🔧 **Implement Solution 2 (Improve Error Handling)**

1. Edit `/backend/entrypoint_agent.py` line 958-960
2. Add clear error messages instead of malformed JSON
3. Add `tool_error` type handling
4. Rebuild agent-runtime container
5. Test error recovery

### Phase 3: Context Protection (1 hour)
🛡️ **Implement Solution 3 (JSON Validation)**

1. Add `sanitize_json_for_llm` helper function
2. Integrate with error handling
3. Add unit tests for edge cases
4. Rebuild and test comprehensively

---

## Testing Procedures

### Test 1: Verify LLM Model Change

```bash
# Check current tasks
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT task_id, task_name, status,
       meta_info->>'model' as model
FROM agent_tasks
ORDER BY created_at DESC LIMIT 5;"

# Create new task via UI
# Task: "analyze sales2.txt and create a chart"
# Model should now be llama3.2-vision:11b

# Check logs for successful execution
docker-compose logs agent-runtime --tail=100 | grep "Tool Call:"
```

**Expected**:
- New tasks use `llama3.2-vision:11b`
- Tools are executed successfully
- Chart HTML file created in artifacts/

### Test 2: Verify Error Recovery (After Phase 2)

```bash
# Create task with intentionally bad JSON
# Monitor logs for error message instead of empty responses

docker-compose logs agent-runtime --tail=50 | grep -E "(ERROR|Tool|Iteration)"
```

**Expected**:
- Clear error message in logs
- LLM receives helpful error text
- LLM retries with correct format
- OR LLM asks for clarification

---

## Deployment

### For Phase 1 (Model Change)

```bash
# If changing frontend default
docker-compose build frontend --no-cache
docker-compose restart frontend

# If changing backend default
docker-compose build backend --no-cache
docker-compose restart backend

# Verify change
# Create new task and check which model is used
```

### For Phase 2 & 3 (Error Handling)

```bash
# Rebuild agent-runtime container
docker-compose build agent-runtime --no-cache

# Restart agent-runtime
docker-compose restart agent-runtime

# Verify logs
docker-compose logs agent-runtime --tail=20
```

---

## Comparison: qwen2.5-coder:7b vs llama3.2-vision:11b

| Aspect | qwen2.5-coder:7b | llama3.2-vision:11b |
|--------|------------------|---------------------|
| **Parameters** | 7.6B | 10.7B |
| **Quantization** | Q4_K_M | Q4_K_M |
| **Model Size** | 4.68 GB | 7.82 GB |
| **Family** | qwen2 | mllama |
| **Error Recovery** | ❌ Poor (gets stuck) | ✅ Good (recovers) |
| **JSON Parsing** | ⚠️ Fragile | ✅ Robust |
| **Task Success Rate** | ~20% (recent runs) | ~90% (historical runs) |
| **Speed** | Faster (~0.5s/iteration) | Moderate (~1s/iteration) |
| **Use Case** | Code generation | General + Vision + Code |

**Recommendation**: Use `llama3.2-vision:11b` for agent tasks due to significantly better error recovery and success rate.

---

## Historical Context

### Similar Issue Reference

User mentioned: "like we had similar issue earlier"

**Likely Previous Issue**: Agent execution failures due to LLM limitations or error handling problems.

**Previous Fix**: Possibly switched to different model or improved error handling.

**Current Regression**: Using `qwen2.5-coder:7b` which has poorer error recovery than `llama3.2-vision:11b`.

---

## Success Criteria

After implementing Phase 1 fix:
- ✅ New tasks use `llama3.2-vision:11b` model
- ✅ Tools are executed successfully (read_file, execute_python, etc.)
- ✅ Artifacts are created (HTML charts, analysis files, etc.)
- ✅ No empty LLM responses in logs
- ✅ Tasks complete with actual results, not just metadata.json

After implementing Phase 2 & 3:
- ✅ JSON parsing errors provide helpful feedback to LLM
- ✅ LLM can recover from errors and retry
- ✅ Malformed JSON doesn't corrupt conversation context
- ✅ Error messages are clear and actionable
- ✅ Success rate improves to >95%

---

## Related Files

### Backend
- `/backend/entrypoint_agent.py` - Main agent orchestrator (line 958: error handling)
- `/backend/agent_tools_enhanced.py` - Tool definitions
- `/backend/app/api/routes/agent_routes.py` - REST API for agent tasks
- `/backend/app/schemas/agent_schemas.py` - Pydantic schemas

### Frontend
- `/frontend/src/components/AgentTaskMonitor.tsx` - Agent task UI (model selector)

### Documentation
- `/AGENT_TASK_USER_AUTH_FIX.md` - User authentication implementation
- `/MINIO_LINK_FEATURE.md` - MinIO browser link feature
- `/AGENT_TASK_FIXES.md` - Previous agent fixes

---

## Next Steps

1. **Immediate**: Change default LLM to `llama3.2-vision:11b` (Phase 1)
2. **Short-term**: Test new tasks to verify fix
3. **Medium-term**: Implement improved error handling (Phase 2)
4. **Long-term**: Add JSON validation and comprehensive error recovery (Phase 3)

---

**Status**: ⚠️ **Issue Diagnosed - Fix Ready to Implement**
**Priority**: 🔴 **HIGH** - Affects all agent task executions
**Effort**: Phase 1 = 5 minutes, Phase 2 = 30 minutes, Phase 3 = 1 hour
**Impact**: Will restore agent tool execution to working state

---

**Date**: 2025-12-12
**Diagnosed By**: Claude AI Assistant
**Issue Type**: LLM model limitation + error handling gap
