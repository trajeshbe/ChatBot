# LangGraph Recursion Limit: Complete Explanation

**Date**: 2025-11-27
**Context**: Understanding the recursion limit error in Project Estimator workflow

---

## Your Questions

> "engineer it wisely,, isn't 25 high ? btw, what does this limit actually mean??"

Great questions! Let me explain both in detail.

---

## What Does "Recursion Limit" Mean?

### Simple Analogy

Think of your workflow as a train traveling from Station A (Start) to Station Z (End):

- **Normal Route**: A → B → C → D → End (5 stops)
- **Loop Problem**: A → B → C → B → C → B → C → ... (never reaches End!)

The recursion limit is like a **safety brake** that stops the train after 25 stops, preventing it from going in circles forever.

### Technical Explanation

In **LangGraph**, a workflow is a **directed graph** where:
- **Nodes** = Individual agents or tasks (like Agent 1, Agent 2, etc.)
- **Edges** = Transitions between nodes (what happens next)

The workflow executes like this:
```
Start → Node 1 → Node 2 → Node 3 → ... → END
```

**Recursion limit = Maximum number of node executions allowed** before LangGraph forces the workflow to stop.

### Why Does This Exist?

**Purpose**: Prevent infinite loops from crashing your system.

**Example Problem Scenarios**:
1. **Circular routing**: Agent 3 → Agent 4 → Agent 3 → Agent 4 → ...
2. **Conditional loop**: Agent checks condition, condition never becomes true, keeps looping
3. **Missing END transition**: Workflow never reaches the END node

---

## Is 25 High or Low?

### Context Matters

**For your 6-agent workflow**:
- **Expected path**: Start → Agent 1 → Agent 2 → Agent 3 → Agent 4 → Agent 5 → Agent 6 → Document Generator → Validator → END
- **Expected iterations**: ~10 nodes

**So why 25?**
- **Safety margin**: Allows for conditional branches, retries, and fallback paths
- **Industry standard**: LangGraph's default is 25 (not too high, not too low)

### Comparison with Other Frameworks

| Framework | Default Limit | Purpose |
|-----------|---------------|---------|
| **LangGraph** | 25 | Workflow node executions |
| **LangChain Agent** | 15 | LLM tool-calling loops |
| **Python recursion** | 1000 | Function call stack depth |

**Verdict**: 25 is **reasonable** for most workflows, but **insufficient if your workflow has a loop bug**.

---

## What's Happening in Your Case

### Error Message
```json
{
  "message": "Workflow completed with errors",
  "errors": ["Workflow error: Recursion limit of 25 reached without hitting a stop condition"]
}
```

### What This Means

1. ✅ Bug #6 (NoneType error) is **FIXED** - that error is gone!
2. ❌ **NEW ISSUE**: The workflow is **stuck in a loop**
3. 🔍 **After 25 node executions**, LangGraph stopped it to prevent infinite loop

### Your Workflow Design

Looking at `workflow.py` lines 172-245, your graph structure is:

```python
workflow = StateGraph(ProjectEstimatorState)

# Add nodes
workflow.add_node("project_scope_analyzer", self.project_scope_analyzer)
workflow.add_node("team_identifier", self.team_identifier)
workflow.add_node("task_generator", self.task_generator)
workflow.add_node("workflow_agent", self.workflow_agent)
workflow.add_node("rate_assigner", self.rate_assigner)
workflow.add_node("document_generator", self.document_generator)

# Add edges (transitions)
workflow.set_entry_point("project_scope_analyzer")
workflow.add_edge("project_scope_analyzer", "team_identifier")
workflow.add_edge("team_identifier", "task_generator")
# ... more edges
workflow.add_edge("document_generator", END)
```

---

## The Problem: Where's the Loop?

### Recent Backend Logs Show

From your latest error:
```
Agent 3: Task Generator for DevOps Infrastructure - Applying effort multiplier: 1.0x
ERROR - Workflow execution failed: Recursion limit of 25 reached
```

This tells us:
1. **Agent 3** (Task Generator) is the last agent to execute before the error
2. The workflow is **stuck** after Agent 3
3. Either:
   - Agent 3 is looping back to itself
   - Agent 3 → Agent 4 transition is misconfigured
   - There's a conditional routing issue after Agent 3

### Likely Root Causes

#### Option 1: Conditional Routing Bug
If your workflow uses **conditional edges** (dynamic routing based on state), there might be a logic error:

```python
def route_after_agent_3(state):
    if some_condition:
        return "agent_4"
    else:
        return "agent_3"  # ❌ Loops back to Agent 3!
```

#### Option 2: Missing END Transition
If the workflow never reaches `END`, it keeps executing:

```python
# Bad:
workflow.add_edge("document_generator", "validator")
workflow.add_edge("validator", "document_generator")  # ❌ Loops forever!

# Good:
workflow.add_edge("document_generator", "validator")
workflow.add_edge("validator", END)  # ✅ Terminates properly
```

#### Option 3: State Condition Never Met
If there's a loop that waits for a state condition to become true, but it never does:

```python
while state.get("documents_ready") is not True:
    keep_processing()  # ❌ If documents_ready never becomes True, infinite loop!
```

---

## Should We Increase the Limit?

### ⚠️ **NO** - That's Like Turning Off the Fire Alarm

**Why NOT**:
1. **Masks the problem**: The loop bug will still exist
2. **Wastes resources**: Workflow will run 50, 100, or 1000 times doing useless work
3. **Costs money**: Each LLM call costs tokens/money
4. **Slow performance**: User waits longer for same buggy result

### ✅ **YES** - Only After Fixing the Loop

**When to increase**:
1. **After verifying** the loop bug is fixed
2. **If legitimate workflow** needs more than 25 steps (rare)
3. **For complex multi-agent debates** with many back-and-forth iterations

**How to increase**:
```python
# In workflow.py line 245, change:
return workflow.compile(checkpointer=None)

# To:
from langgraph.checkpoint import MemorySaver
return workflow.compile(
    checkpointer=MemorySaver(),
    config={"recursion_limit": 50}  # Increase to 50
)
```

**⚠️ BUT**: This requires LangGraph >= 0.2.20 (your version is 0.2.16)

---

## How to Fix the Real Problem

### Step 1: Find the Loop

Check the workflow graph routing logic after Agent 3:

```bash
# Search for Agent 3 routing
grep -A 20 "task_generator" backend/app/agents/project_estimator/workflow.py | grep -E "(add_edge|add_conditional_edges|route)"
```

### Step 2: Examine Conditional Routing

Look for any `add_conditional_edges` or routing functions:

```python
# If you see something like this:
workflow.add_conditional_edges(
    "task_generator",
    route_after_task_generator,  # ← Check this function!
    {
        "continue": "workflow_agent",
        "retry": "task_generator",  # ← This could cause loop!
        END: END
    }
)
```

### Step 3: Check State Conditions

Verify that any loop conditions can actually be satisfied:

```python
def route_after_task_generator(state):
    if state.get("tasks_complete"):  # ← Does this ever become True?
        return END
    else:
        return "task_generator"  # ← Could loop forever!
```

---

## Recommended Next Steps

### 1. Investigate Workflow Routing (NOW)

```bash
# Search for the graph structure
grep -n "add_edge\|add_conditional_edges" backend/app/agents/project_estimator/workflow.py
```

### 2. Add Debug Logging (Temporary)

Add logging to see node transitions:

```python
# In workflow.py, add to each agent:
def task_generator(self, state: Dict) -> Dict:
    logger.info(f"🔵 ENTERING Agent 3 - Task Generator (iteration count: {state.get('iteration_count', 0)})")

    # ... agent logic ...

    logger.info(f"🟢 EXITING Agent 3 - Next node: workflow_agent")
    return state
```

### 3. Test with Reduced Complexity

Create a minimal test that triggers the loop:

```bash
# Simple test with just project scope
curl -X POST "http://localhost:8000/api/v1/project-estimator/generate-agentic" \
  -F "project_scope=Simple project test" \
  -F "model_id=llama3.2-vision:11b" \
  -F "project_type=Full Service" \
  -F "scenario=Baseline"
```

### 4. Fix the Loop Bug

Once identified, fix the routing logic to ensure proper termination.

### 5. THEN Consider Increasing Limit (Optional)

Only after confirming the loop is fixed, if workflow legitimately needs more steps.

---

## Summary

### What Recursion Limit Means
- **Safety brake** to prevent infinite loops
- **Counts node executions** in the workflow graph
- **Default: 25** is reasonable for most workflows

### Is 25 High?
- **For normal workflows**: Yes, 25 is plenty (expected ~10 steps)
- **For your bug**: No, the problem is the loop, not the limit

### What to Do
1. ✅ **Bug #6 is fixed** - NoneType error is gone
2. ⚠️ **NEW BUG**: Workflow routing loop after Agent 3
3. 🔍 **Next**: Investigate graph edges and conditional routing
4. 🚫 **DON'T**: Increase limit until loop is fixed

### Key Insight

> **The recursion limit error is a SYMPTOM, not the CAUSE.**
>
> Increasing the limit is like:
> - Turning off a fire alarm because it's too loud 🔥🚫
> - Taking painkillers without treating the injury 💊
> - Adding more gas to a car stuck in a ditch ⛽
>
> **Fix the loop first, THEN decide if 25 is enough.**

---

## Want Me to Help Find the Loop?

I can investigate the workflow routing logic to identify where the loop is occurring. Just confirm you want me to proceed with that analysis.

---

**Created By**: Claude Code Assistant
**Last Updated**: 2025-11-27 05:30 UTC
**Status**: Ready to investigate workflow routing ⏳

