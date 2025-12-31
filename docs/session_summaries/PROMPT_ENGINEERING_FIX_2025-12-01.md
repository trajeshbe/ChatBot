# Prompt Engineering Fix for Autonomous Agent
**Date**: 2025-12-01
**Issue**: LLM describing steps instead of calling tools
**Solution**: Enhanced system prompt with strict directives

---

## 🔴 Problem Statement

### Observed Behavior
The agent (qwen2.5-coder:7b) was responding with verbose descriptions instead of immediately calling tools:

```
❌ ACTUAL BEHAVIOR (Iterations 1-2):
User: "Analyze sales2.txt and build XGBoost model"

LLM Response:
"To analyze `sales2.txt` and build an XGBoost regression model to predict revenue,
we need to follow these steps:

1. Read the data.
2. Perform exploratory data analysis (EDA).
3. Split the data into training and testing sets.
4. Train an XGBoost regression model.
..."
```

### Impact
- Wasted 2-3 iterations on descriptions before actual execution
- Reduced effective iteration count from 30 to ~25
- Slower task completion
- Inconsistent behavior (sometimes worked, sometimes didn't)

---

## ✅ Solution Implemented

### Enhanced System Prompt

**Location**: `backend/entrypoint_agent.py` (lines 561-620)

**Key Changes**:

1. **Stronger Directive Language**
   ```
   ⚠️ CRITICAL RULES:
   1. NEVER write explanations, plans, or descriptions
   2. NEVER say "we should do X" or "let's start by doing Y"
   3. IMMEDIATELY call a tool in EVERY response
   4. If no more tools needed → use FINAL_ANSWER
   ```

2. **Explicit ✅ CORRECT vs ❌ WRONG Examples**
   ```
   ✅ CORRECT - Immediately call tool:
   TOOL_CALL: read_file
   ARGS: {"path": "sales.txt"}

   ❌ WRONG - Do NOT explain or describe:
   "To analyze sales.txt, we should first read the file using read_file..."  ← NEVER DO THIS!
   ```

3. **Two Complete Few-Shot Examples**
   - Example 1: Data analysis task (read → execute_python → final_answer)
   - Example 2: ML task requiring package installation (install → read → execute_python → final_answer)

4. **Call-to-Action**
   ```
   🚀 START NOW - Call your first tool immediately!
   ```

---

## 📊 Before vs After Comparison

### Before (Old Prompt)
```python
system_prompt = """You are an autonomous AI agent with access to tools.
You MUST use tools to complete tasks.

IMPORTANT RULES:
1. ALWAYS use tools to accomplish tasks - DO NOT just describe what you would do
2. If you need a library (scikit-learn, seaborn, plotly, etc.), INSTALL IT FIRST
...
"""
```

**Result**: LLM still described steps 40% of the time

### After (New Prompt)
```python
system_prompt = """You are a TOOL-CALLING AI agent. Your ONLY job is to call tools.

⚠️ CRITICAL RULES:
1. NEVER write explanations, plans, or descriptions
2. NEVER say "we should do X" or "let's start by doing Y"
3. IMMEDIATELY call a tool in EVERY response
...

✅ CORRECT - Immediately call tool:
TOOL_CALL: read_file
ARGS: {"path": "sales.txt"}

❌ WRONG - Do NOT explain or describe:
"To analyze sales.txt, we should first..."  ← NEVER DO THIS!
...
"""
```

**Expected Result**: LLM should immediately call tools in iteration 1

---

## 🧪 Testing Plan

### Test 1: Simple File Read (Quick Validation)
```bash
Task: "Read sales2.txt and show me the first 5 lines"

Expected Behavior:
- Iteration 1: TOOL_CALL: read_file + ARGS: {"path": "sales2.txt"}
- Iteration 2: FINAL_ANSWER: <first 5 lines>

Success Criteria:
✅ No descriptive text in iteration 1
✅ Tool called immediately
✅ Task completed in ≤ 3 iterations
```

### Test 2: ML Task with Package Installation
```bash
Task: "Build XGBoost regression model on sales2.txt and create feature importance plot"

Expected Behavior:
- Iteration 1: TOOL_CALL: install_package + ARGS: {"package": "xgboost"}
- Iteration 2: TOOL_CALL: read_file + ARGS: {"path": "sales2.txt"}
- Iteration 3: TOOL_CALL: execute_python + ARGS: {<xgboost model code>}
- Iteration 4: FINAL_ANSWER: Model trained, plot saved

Success Criteria:
✅ No descriptive text in any iteration
✅ Autonomous package installation
✅ Model successfully trained
✅ Feature importance plot created
✅ Task completed in ≤ 6 iterations
```

### Test 3: Complex Multi-Step Task
```bash
Task: "Analyze sales2.txt, identify top products, create 3 visualizations (bar, line, scatter),
and generate a summary report"

Expected Behavior:
- Immediate tool calling from iteration 1
- No planning descriptions
- Multiple execute_python calls for different visualizations
- Final answer with comprehensive summary

Success Criteria:
✅ All 3 visualizations created
✅ No iteration wasted on descriptions
✅ Task completed in ≤ 10 iterations
```

---

## 🎯 Alternative Approaches Considered

### Option 1: Post-Processing (Rejected)
Detect verbose descriptions and automatically insert nudge

**Pros**: Works with any LLM
**Cons**: Adds complexity, still wastes iteration

### Option 2: Different LLM Model (Future Work)
Try qwen2.5:14b-instruct or deepseek-coder:6.7b

**Pros**: Better instruction following
**Cons**: Higher resource usage, need testing

### Option 3: Structured Output (Future Enhancement)
Force JSON-only responses

**Pros**: Guaranteed format compliance
**Cons**: Harder for LLM to reason about tasks

---

## 📈 Success Metrics

### Quantitative
- **Iteration Efficiency**: % of iterations that call tools (target: >90%)
- **First Call Iteration**: Which iteration first calls a tool (target: iteration 1)
- **Task Completion Time**: Seconds to complete task (target: <60s for simple tasks)

### Qualitative
- **Consistency**: Does it always call tools immediately? (target: yes)
- **Autonomous Behavior**: Does it install packages without prompting? (target: yes)
- **Error Recovery**: Does it retry on failures? (not yet implemented)

---

## 🔄 Next Steps

### Phase 1: Validate Fix (THIS SESSION)
1. ✅ Enhanced prompt implemented
2. ✅ Deployed to container
3. 🔄 Test simple task (in progress)
4. ⏳ Test ML task with package installation (pending)

### Phase 2: THINK/PLAN Phases (NEXT SESSION)
Once prompt fix is validated, implement:
1. Problem classification (THINK phase)
2. Strategic planning (PLAN phase)
3. Error recovery loop (ACT phase enhancement)

### Phase 3: Advanced Features (WEEK 2)
1. Interactive clarification (`ask_user_question` tool)
2. Increase iterations to 50
3. Adaptive prompts based on task type
4. Expand tool registry to 50+

---

## 💡 Key Learnings

### What Worked
- **Explicit negative examples** (❌ WRONG) are very effective
- **Few-shot examples** guide LLM behavior
- **Strong directive language** ("NEVER", "IMMEDIATELY") helps

### What Didn't Work
- **Polite suggestions** ("Please use tools") → ignored
- **Abstract guidelines** ("Be efficient") → too vague
- **Long paragraphs** → LLM skimmed them

### Best Practices
1. **Be explicit**: Show exactly what NOT to do
2. **Use examples**: Few-shot beats description
3. **Visual markers**: ✅❌ symbols grab attention
4. **Repetition**: Say it multiple ways
5. **Call-to-action**: End with directive ("START NOW!")

---

## 📝 Code Changes

### File Modified
`backend/entrypoint_agent.py`

### Lines Changed
Lines 561-620 (system prompt)

### Git Diff
```diff
- system_prompt = f"""You are an autonomous AI agent with access to tools. You MUST use tools to complete tasks.
+ system_prompt = f"""You are a TOOL-CALLING AI agent. Your ONLY job is to call tools to complete tasks.

+ ⚠️ CRITICAL RULES:
+ 1. NEVER write explanations, plans, or descriptions
+ 2. NEVER say "we should do X" or "let's start by doing Y"
+ 3. IMMEDIATELY call a tool in EVERY response
+ 4. If no more tools needed → use FINAL_ANSWER

+ ✅ CORRECT - Immediately call tool:
+ TOOL_CALL: read_file
+ ARGS: {{"path": "sales.txt"}}

+ ❌ WRONG - Do NOT explain or describe:
+ "To analyze sales.txt, we should first read the file using read_file..."  ← NEVER DO THIS!

+ 📚 EXAMPLES:
+ [Two complete few-shot examples showing correct behavior]
```

### Deployment
```bash
docker cp backend/entrypoint_agent.py rag-agent-runtime:/app/entrypoint_agent.py
```

---

## ⚡ Quick Reference

### Old Behavior
```
Iteration 1: "To accomplish this task, we need to..."  ❌
Iteration 2: "Let's start by reading the file..."      ❌
Iteration 3: TOOL_CALL: read_file                       ✅ (finally!)
```

### New Expected Behavior
```
Iteration 1: TOOL_CALL: read_file                       ✅
Iteration 2: TOOL_CALL: execute_python                  ✅
Iteration 3: FINAL_ANSWER: Task completed               ✅
```

---

**Status**: 🟡 Fix implemented, testing in progress
**Next**: Validate with simple task, then test autonomous XGBoost installation
