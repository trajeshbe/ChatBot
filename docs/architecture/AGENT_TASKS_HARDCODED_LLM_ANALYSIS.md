# Agent Tasks - Hardcoded LLM Models Analysis & Fix

**Date**: 2025-12-10
**Issue**: Agent Tasks (🎯 Create Task) uses hardcoded LLM models instead of UI-selected model
**Status**: 🔧 ANALYSIS COMPLETE - Ready for Implementation
**Priority**: P1 - User-Requested Feature Enhancement

---

## Executive Summary

**Problem**: When users create tasks via the 🎯 Create Task feature, the system uses **hardcoded LLM models** instead of respecting the model selected in the UI.

**Impact**:
- User selects "GPT-4" in UI → Agent uses "qwen2.5:1.5b" (hardcoded default)
- User selects "Claude Sonnet" in UI → Project Estimator uses "gpt-4" (hardcoded)
- User has no control over which model powers their agent tasks

**Solution**: Pass `model_id` parameter from UI through the entire agent execution chain.

---

## Hardcoded Models Found

### 1. EnhancedRAGAgent - GPT-4 Function Calling

**File**: `backend/app/agents/enhanced_rag_agent.py`
**Line**: 889
**Hardcoded Model**: `"gpt-4-turbo-preview"`

**Context**:
```python
response = await self.openai_client.chat.completions.create(
    model="gpt-4-turbo-preview",  # ❌ HARDCODED
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    tools=available_tools,
    tool_choice="auto",
    temperature=0.3
)
```

**Purpose**: Uses GPT-4 for intelligent tool selection via OpenAI function calling.

**Issue**: Even if user selects a different model in UI, this always uses GPT-4.

---

### 2. Project Estimator - Multiple GPT-4 References

**File**: `backend/app/agents/project_estimator/workflow.py`
**Lines**: 364, 392, 420 (and more)
**Hardcoded Model**: `"gpt-4"`

**Context** (Line 362-366):
```python
response = await self.llm_service.generate(
    prompt=prompt,
    model_id="gpt-4",  # ❌ HARDCODED
    temperature=0.3
)
```

**Purpose**: Analyzes BRD examples, cost examples, and sample data.

**Issue**: All Project Estimator LLM calls hardcoded to "gpt-4".

**Additional Instances**:
- Line 392: `model_id="gpt-4"` (analyze cost examples)
- Line 420: `model_id="gpt-4"` (analyze sample data)
- Multiple other instances in requirements extraction, team planning, etc.

---

### 3. Construction Metrics Agent - Vision Model

**File**: `backend/app/agents/construction_metrics/extractors.py`
**Referenced Model**: `"llama3.2-vision:11b"` (in workflow.py and state.py)

**Context**: This agent needs vision capabilities, so it requires a vision-capable model.

**File**: `backend/app/agents/construction_metrics/workflow.py`
**Line**: Approximately 60-70 (model_id initialization)

**Issue**: Vision model selection is hardcoded instead of checking if user's selected model supports vision.

---

### 4. Tool Registry - Default Parameters

**File**: `backend/app/agents/tool_registry.py`
**Lines**: 740, 1117
**Hardcoded Model**: `"qwen2.5:1.5b"`

**Context** (Line 737-741):
```python
async def _wrap_smart_extraction(
    self,
    url: str,
    user_instructions: str,
    llm_provider: str = "ollama",
    model_id: str = "qwen2.5:1.5b"  # ❌ HARDCODED DEFAULT
) -> Dict[str, Any]:
```

**Purpose**: Default parameter for web scraping smart extraction.

**Issue**: If `model_id` not explicitly passed, defaults to "qwen2.5:1.5b" instead of UI selection.

---

### 5. Claude CLI Agent

**File**: `backend/app/agents/claude_cli_agent.py`
**Line**: 147
**Hardcoded Model**: `"claude-sonnet-4.5"`

**Context**:
```python
await self.agent_service.update_agent_task(
    task_id=self.task_id,
    agent_option="claude_cli",
    tokens_used=self.total_tokens,
    model_name="claude-sonnet-4.5"  # ❌ HARDCODED
)
```

**Purpose**: Records which model was used for the Claude CLI agent task.

**Issue**: Always reports "claude-sonnet-4.5" even if a different Claude model variant is used.

---

### 6. Agent Sandbox Manager - **MOST CRITICAL!** 🚨

**File**: `backend/app/services/agent_sandbox_manager.py`
**Lines**: 123-124
**Hardcoded Models**: `"qwen2.5-coder:7b"` and `"llama3.2-vision:11b"`

**Context**:
```python
# Add LLM credentials based on agent type
if agent_type == "local_mini":
    env_vars["OLLAMA_BASE_URL"] = "http://rag-ollama:11434"
    env_vars["AGENT_CODE_MODEL"] = "qwen2.5-coder:7b"      # ❌ HARDCODED!
    env_vars["AGENT_VISION_MODEL"] = "llama3.2-vision:11b" # ❌ HARDCODED!
```

**Purpose**: Sets environment variables for Docker-in-Docker agent sandbox.

**Issue**: **THIS IS THE CRITICAL ONE!** The agent that writes and executes Python code for "Create Task" always uses `qwen2.5-coder:7b`, even if user selected GPT-4, Claude, or another model.

**Impact**:
- User selects "GPT-4" in UI → Code generation still uses qwen2.5-coder:7b ❌
- Results in lower quality pandas/plotly code
- Complex data analysis tasks fail
- User has NO control over code-writing agent's LLM

**Real-World Example**:
```
User Task: "Create a complex sales dashboard with plotly"
UI Selection: GPT-4 (excellent for complex code)
Actual Model: qwen2.5-coder:7b (basic model)
Result: Poorly generated code, missing features, errors ❌
```

---

## Root Cause Analysis

### Current Flow (BROKEN):

```
UI Model Selection (e.g., "GPT-4")
    ↓
API Endpoint (/api/v1/agent/create_task)
    ↓
EnhancedRAGAgent.run(query, session_id, user_preferences)
    ↓
    ❌ BREAKS HERE: model_id NOT extracted from user_preferences
    ↓
_select_tools_with_llm()
    ↓
    Uses hardcoded "gpt-4-turbo-preview"
    ↓
Tool execution (e.g., Project Estimator)
    ↓
    Uses hardcoded "gpt-4" for all LLM calls
```

### Expected Flow (FIXED):

```
UI Model Selection (e.g., "GPT-4")
    ↓
API Endpoint (/api/v1/agent/create_task)
    ↓
    Extract model_id from request
    ↓
EnhancedRAGAgent.run(query, session_id, user_preferences, model_id)  ✅
    ↓
    Extract model_id from user_preferences or parameter
    ↓
_select_tools_with_llm(query, available_tools, model_id=model_id)  ✅
    ↓
    Uses UI-selected model for tool selection
    ↓
Tool execution (e.g., Project Estimator)
    ↓
    Receives model_id via state['model_id']  ✅
    ↓
    Uses state['model_id'] for all LLM calls
```

---

## Solution: Code Fixes

### Fix 1: EnhancedRAGAgent - Accept model_id Parameter

**File**: `backend/app/agents/enhanced_rag_agent.py`

**Change 1 - Update `run()` method signature (Line ~92-97)**:

```python
async def run(
    self,
    query: str,
    session_id: Optional[str] = None,
    user_preferences: Optional[Dict[str, Any]] = None,
    model_id: Optional[str] = None  # ✅ ADD THIS PARAMETER
) -> Dict[str, Any]:
```

**Change 2 - Extract model_id from user_preferences or parameter (Line ~100-105)**:

```python
# ✅ ADD THIS CODE at the beginning of run() method
# Extract model_id from user_preferences or use parameter
if model_id is None and user_preferences:
    model_id = user_preferences.get('model_id')

# If still None, use a sensible default
if model_id is None:
    model_id = "gpt-4"  # Default for agents that need function calling
    logger.info(f"⚠️ No model_id provided, defaulting to {model_id} for agent tasks")
else:
    logger.info(f"✅ Using model_id from UI: {model_id}")
```

**Change 3 - Pass model_id to _select_tools_with_llm() (Line ~200-210)**:

Find this section:
```python
# Enhanced Phase 3 (November 2024): Use GPT-4 function calling for tool selection
tool_selection = await self._select_tools_with_llm(
    query=query,
    available_tools=available_tools,
    session_id=session_id,
    user_preferences=user_preferences
)
```

Update to:
```python
tool_selection = await self._select_tools_with_llm(
    query=query,
    available_tools=available_tools,
    session_id=session_id,
    user_preferences=user_preferences,
    model_id=model_id  # ✅ ADD THIS
)
```

**Change 4 - Update _select_tools_with_llm() signature (Line ~860-870)**:

```python
async def _select_tools_with_llm(
    self,
    query: str,
    available_tools: List[Dict[str, Any]],
    session_id: Optional[str] = None,
    user_preferences: Optional[Dict[str, Any]] = None,
    model_id: Optional[str] = None  # ✅ ADD THIS
) -> Dict[str, Any]:
```

**Change 5 - Use model_id instead of hardcoded value (Line 888-890)**:

BEFORE:
```python
response = await self.openai_client.chat.completions.create(
    model="gpt-4-turbo-preview",  # ❌ HARDCODED
    messages=[...],
    tools=available_tools,
    tool_choice="auto",
    temperature=0.3
)
```

AFTER:
```python
# ✅ Use UI-selected model, fallback to gpt-4-turbo-preview if None
llm_model = model_id or "gpt-4-turbo-preview"
logger.info(f"🎯 Tool selection using model: {llm_model}")

response = await self.openai_client.chat.completions.create(
    model=llm_model,  # ✅ USE UI-SELECTED MODEL
    messages=[...],
    tools=available_tools,
    tool_choice="auto",
    temperature=0.3
)
```

---

### Fix 2: Project Estimator - Use model_id from State

**File**: `backend/app/agents/project_estimator/workflow.py`

**Context**: Project Estimator already has `model_id` in its state definition (line 99):

```python
class ProjectEstimatorState(TypedDict):
    # ... other fields ...
    model_id: str  # LLM model to use (from UI or Model Registry)  ✅ ALREADY EXISTS
```

**The Problem**: State has `model_id`, but LLM calls use hardcoded "gpt-4".

**Change 1 - Use state['model_id'] in _analyze_brd_examples() (Line 362-366)**:

BEFORE:
```python
response = await self.llm_service.generate(
    prompt=prompt,
    model_id="gpt-4",  # ❌ HARDCODED
    temperature=0.3
)
```

AFTER:
```python
# ✅ Use model_id from state (passed from UI)
model_id = state.get('model_id', 'gpt-4')
logger.info(f"🎯 Project Estimator using model: {model_id}")

response = await self.llm_service.generate(
    prompt=prompt,
    model_id=model_id,  # ✅ USE UI-SELECTED MODEL
    temperature=0.3
)
```

**Change 2 - Apply same fix to _analyze_cost_examples() (Line 390-394)**:

```python
model_id = state.get('model_id', 'gpt-4')

response = await self.llm_service.generate(
    prompt=prompt,
    model_id=model_id,  # ✅ USE UI-SELECTED MODEL
    temperature=0.3
)
```

**Change 3 - Apply same fix to _analyze_sample_data() (Line 418-422)**:

```python
model_id = state.get('model_id', 'gpt-4')

response = await self.llm_service.generate(
    prompt=prompt,
    model_id=model_id,  # ✅ USE UI-SELECTED MODEL
    temperature=0.3
)
```

**Change 4 - Search for ALL instances of `model_id="gpt-4"` and replace**:

```bash
# Find all hardcoded instances
grep -n 'model_id="gpt-4"' backend/app/agents/project_estimator/workflow.py

# Replace each one with:
model_id = state.get('model_id', 'gpt-4')
# ... then use model_id variable
```

---

### Fix 3: Construction Metrics Agent - Vision Model Selection

**File**: `backend/app/agents/construction_metrics/workflow.py`

**Context**: This agent needs vision capabilities, so we need intelligent model selection.

**Change 1 - Add vision model detection logic**:

```python
def _get_vision_model(self, state: ConstructionMetricsState) -> str:
    """
    Get appropriate vision model based on user selection.

    If user selected a vision-capable model, use it.
    Otherwise, fallback to llama3.2-vision:11b.
    """
    model_id = state.get('model_id')

    # List of known vision-capable models
    vision_models = [
        'llama3.2-vision',
        'qwen2.5vl',
        'gpt-4-vision',
        'gpt-4o',
        'claude-3-opus',
        'claude-3-sonnet',
        'claude-3.5-sonnet'
    ]

    # Check if user's selected model supports vision
    if model_id:
        for vm in vision_models:
            if vm in model_id.lower():
                logger.info(f"✅ Using UI-selected vision model: {model_id}")
                return model_id

    # Fallback to default vision model
    default_vision = "llama3.2-vision:11b"
    logger.info(f"⚠️ UI model '{model_id}' doesn't support vision, using {default_vision}")
    return default_vision
```

**Change 2 - Use _get_vision_model() in workflow nodes**:

```python
# In the metric extraction node
vision_model = self._get_vision_model(state)

# Pass to extraction functions
extracted_metrics = await batch_extract_metrics(
    documents=state['classified_documents'],
    vision_service=self.vision_service,
    llm_service=self.llm_service,
    model_id=vision_model  # ✅ USE DETECTED VISION MODEL
)
```

---

### Fix 4: Tool Registry - Use model_id from kwargs

**File**: `backend/app/agents/tool_registry.py`

**Context**: Tool wrappers should extract model_id from kwargs instead of using hardcoded defaults.

**Change 1 - Update _wrap_smart_extraction() (Line 737-741)**:

BEFORE:
```python
async def _wrap_smart_extraction(
    self,
    url: str,
    user_instructions: str,
    llm_provider: str = "ollama",
    model_id: str = "qwen2.5:1.5b",  # ❌ HARDCODED DEFAULT
    **kwargs
) -> Dict[str, Any]:
```

AFTER:
```python
async def _wrap_smart_extraction(
    self,
    url: str,
    user_instructions: str,
    llm_provider: str = "ollama",
    model_id: Optional[str] = None,  # ✅ REMOVE HARDCODED DEFAULT
    **kwargs
) -> Dict[str, Any]:
    """
    Wrapper for Smart Web Extraction.

    Args:
        url: URL to scrape
        user_instructions: Extraction instructions
        llm_provider: LLM provider (default: ollama)
        model_id: LLM model to use (if None, uses UI-selected model from kwargs)
        **kwargs: Additional parameters including unified_config
    """

    # ✅ Extract model_id from unified_config if not provided
    if model_id is None:
        unified_config = kwargs.get('unified_config', {})
        model_id = unified_config.get('model_id', 'qwen2.5:1.5b')
        logger.info(f"✅ Using model_id from UI: {model_id}")

    # Rest of the method...
```

**Change 2 - Apply same pattern to all tool wrappers**:

Find all methods with `model_id: str = "..."` default parameters and replace with:
- `model_id: Optional[str] = None`
- Extract from `kwargs.get('unified_config', {}).get('model_id')`

---

### Fix 5: Claude CLI Agent - Use actual model name

**File**: `backend/app/agents/claude_cli_agent.py`

**Change 1 - Accept model_id in constructor**:

```python
def __init__(
    self,
    task_id: str,
    agent_service: AgentService,
    model_id: Optional[str] = None  # ✅ ADD THIS
):
    self.task_id = task_id
    self.agent_service = agent_service
    self.model_id = model_id or "claude-sonnet-4.5"  # ✅ USE PROVIDED OR DEFAULT
    self.total_tokens = 0
```

**Change 2 - Use self.model_id in update_agent_task() (Line 147)**:

BEFORE:
```python
await self.agent_service.update_agent_task(
    task_id=self.task_id,
    agent_option="claude_cli",
    tokens_used=self.total_tokens,
    model_name="claude-sonnet-4.5"  # ❌ HARDCODED
)
```

AFTER:
```python
await self.agent_service.update_agent_task(
    task_id=self.task_id,
    agent_option="claude_cli",
    tokens_used=self.total_tokens,
    model_name=self.model_id  # ✅ USE ACTUAL MODEL
)
```

---

### Fix 6: Agent Sandbox Manager - **MOST CRITICAL!** 🚨

**File**: `backend/app/services/agent_sandbox_manager.py`

**This is the most important fix** because it controls the LLM used by the Docker-in-Docker code execution agent.

**Change 1 - Update execute_task() method signature (Line 52-61)**:

BEFORE:
```python
async def execute_task(
    self,
    task: str,
    task_id: str,
    session_id: str,
    agent_type: str = "local_mini",
    context: Dict[str, Any] = None,
    max_iterations: int = 20,
    uploaded_files: list = None
) -> Dict[str, Any]:
```

AFTER:
```python
async def execute_task(
    self,
    task: str,
    task_id: str,
    session_id: str,
    agent_type: str = "local_mini",
    context: Dict[str, Any] = None,
    max_iterations: int = 20,
    uploaded_files: list = None,
    model_id: Optional[str] = None  # ✅ ADD THIS PARAMETER
) -> Dict[str, Any]:
    """
    Execute task in sandbox container

    Args:
        task: Task description/query
        task_id: Unique task ID
        session_id: Session ID
        agent_type: 'local_mini' or 'claude_cli'
        context: Additional context (uploaded files, etc.)
        max_iterations: Max iterations for agentic loop
        uploaded_files: List of uploaded files to mount
        model_id: LLM model to use (from UI selection)  # ✅ ADD DOCUMENTATION

    Returns:
        Task execution result with artifacts
    """
```

**Change 2 - Use UI-selected model in environment variables (Line 121-128)**:

BEFORE:
```python
# Add LLM credentials based on agent type
if agent_type == "local_mini":
    env_vars["OLLAMA_BASE_URL"] = "http://rag-ollama:11434"
    env_vars["AGENT_CODE_MODEL"] = "qwen2.5-coder:7b"      # ❌ HARDCODED!
    env_vars["AGENT_VISION_MODEL"] = "llama3.2-vision:11b" # ❌ HARDCODED!
elif agent_type == "claude_cli":
    import os
    env_vars["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "")
```

AFTER:
```python
# Add LLM credentials based on agent type
if agent_type == "local_mini":
    env_vars["OLLAMA_BASE_URL"] = "http://rag-ollama:11434"

    # ✅ Use UI-selected model for code generation, fallback to default if None
    code_model = model_id or "qwen2.5-coder:7b"
    vision_model = "llama3.2-vision:11b"  # Keep default for vision-specific tasks

    # If UI model supports vision, use it for vision tasks too
    vision_capable_models = ['vision', 'qwen2.5vl', 'gpt-4o', 'gpt-4-vision', 'claude-3']
    if model_id and any(vm in model_id.lower() for vm in vision_capable_models):
        vision_model = model_id
        logger.info(f"✅ Using UI-selected vision model for code generation: {vision_model}")

    env_vars["AGENT_CODE_MODEL"] = code_model
    env_vars["AGENT_VISION_MODEL"] = vision_model

    logger.info(f"🎯 Agent sandbox using code model: {code_model}")
    logger.info(f"🎯 Agent sandbox using vision model: {vision_model}")

elif agent_type == "claude_cli":
    import os
    env_vars["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "")

    # ✅ Pass model_id for Claude agents too
    if model_id:
        env_vars["AGENT_MODEL_ID"] = model_id
        logger.info(f"🎯 Claude CLI agent using model: {model_id}")
    else:
        env_vars["AGENT_MODEL_ID"] = "claude-sonnet-4.5"  # Default
```

**Why This Fix is Critical**:
- This is the **entry point** for code-writing agents
- Affects: pandas code, plotly graphs, data analysis, file manipulation
- Without this fix, **all other fixes are ineffective** for code execution tasks

---

## API Endpoint Changes

### Ensure model_id is passed from UI to Agent

**File**: `backend/app/api/routes/agent_routes.py` (or wherever agent task creation is handled)

**Verify that model_id flows correctly**:

```python
@router.post("/api/v1/agent/create_task")
async def create_agent_task(
    request: AgentTaskRequest,
    db: Session = Depends(get_db)
):
    """Create a new agent task with UI-selected model."""

    # Extract model_id from request
    model_id = request.model_id or request.unified_config.get('model_id')

    logger.info(f"🎯 Creating agent task with model: {model_id}")

    # Pass model_id to agent
    agent = EnhancedRAGAgent()
    result = await agent.run(
        query=request.query,
        session_id=request.session_id,
        user_preferences={
            'model_id': model_id,  # ✅ PASS MODEL_ID
            'unified_config': request.unified_config,
            # ... other preferences
        },
        model_id=model_id  # ✅ ALSO PASS AS EXPLICIT PARAMETER
    )

    return result
```

---

## Testing Plan

### Test 1: Enhanced RAG Agent with UI Model Selection

**Steps**:
1. Select "GPT-4" in UI model selector
2. Create agent task via 🎯 Create Task: "Analyze this document and extract key points"
3. Check logs for: `✅ Using model_id from UI: gpt-4`
4. Verify tool selection uses "gpt-4" instead of "gpt-4-turbo-preview"

**Expected Logs**:
```
✅ Using model_id from UI: gpt-4
🎯 Tool selection using model: gpt-4
```

---

### Test 2: Project Estimator with UI Model Selection

**Steps**:
1. Select "Claude Sonnet 3.5" in UI
2. Upload project scope document
3. Create agent task: "Generate project estimate"
4. Check logs for: `🎯 Project Estimator using model: claude-3.5-sonnet`

**Expected Logs**:
```
🎯 Project Estimator using model: claude-3.5-sonnet
✅ Analyzing BRD examples with claude-3.5-sonnet
✅ Analyzing cost examples with claude-3.5-sonnet
```

---

### Test 3: Construction Metrics with Vision Model

**Steps**:
1. Select "qwen2.5vl:7b" in UI (vision model)
2. Upload construction drawings ZIP
3. Create agent task: "Extract building metrics"
4. Check logs for: `✅ Using UI-selected vision model: qwen2.5vl:7b`

**Expected Logs**:
```
✅ Using UI-selected vision model: qwen2.5vl:7b
📊 Extracting metrics from drawings with qwen2.5vl:7b
```

---

### Test 4: Non-Vision Model Fallback

**Steps**:
1. Select "GPT-4" in UI (NOT a vision model)
2. Upload construction drawings ZIP
3. Create agent task: "Extract building metrics"
4. Check logs for: `⚠️ UI model 'gpt-4' doesn't support vision, using llama3.2-vision:11b`

**Expected Logs**:
```
⚠️ UI model 'gpt-4' doesn't support vision, using llama3.2-vision:11b
📊 Extracting metrics from drawings with llama3.2-vision:11b
```

---

## Implementation Checklist

### Phase 1: Core Agent Fixes
- [ ] Fix 1: Update EnhancedRAGAgent to accept and use model_id
  - [ ] Update `run()` method signature
  - [ ] Extract model_id from user_preferences
  - [ ] Pass model_id to `_select_tools_with_llm()`
  - [ ] Update `_select_tools_with_llm()` signature
  - [ ] Use model_id in OpenAI function calling

### Phase 2: Specialized Agent Fixes
- [ ] Fix 2: Update Project Estimator workflow
  - [ ] Replace all `model_id="gpt-4"` with `state.get('model_id', 'gpt-4')`
  - [ ] Add logging for model selection
  - [ ] Test with non-GPT-4 models

- [ ] Fix 3: Update Construction Metrics agent
  - [ ] Add `_get_vision_model()` helper
  - [ ] Implement vision model detection
  - [ ] Add fallback logic for non-vision models

### Phase 3: Tool Registry Fixes
- [ ] Fix 4: Update tool_registry.py
  - [ ] Remove hardcoded model_id defaults
  - [ ] Extract model_id from unified_config in kwargs
  - [ ] Update all tool wrapper signatures

- [ ] Fix 5: Update Claude CLI agent
  - [ ] Accept model_id in constructor
  - [ ] Use actual model_id in task updates

### Phase 4: API Integration
- [ ] Verify API endpoint passes model_id correctly
- [ ] Add logging to track model_id flow
- [ ] Test end-to-end model selection

### Phase 5: Testing
- [ ] Test 1: Enhanced RAG Agent
- [ ] Test 2: Project Estimator
- [ ] Test 3: Construction Metrics (vision model)
- [ ] Test 4: Construction Metrics (fallback)
- [ ] Test 5: Tool wrappers (web scraping, etc.)

### Phase 6: Documentation
- [ ] Update agent documentation
- [ ] Add model selection guide
- [ ] Document vision model requirements

---

## Summary

**Issue**: Agent Tasks use hardcoded LLM models instead of UI selection.

**Root Cause**: `model_id` parameter not passed through agent execution chain.

**Solution**:
1. Pass `model_id` from UI → API → EnhancedRAGAgent → Tool Selection → Specialized Agents
2. Update all LLM calls to use `model_id` instead of hardcoded strings
3. Add intelligent vision model detection for Construction Metrics agent

**Files to Modify**:
1. `backend/app/agents/enhanced_rag_agent.py` (5 changes)
2. `backend/app/agents/project_estimator/workflow.py` (Multiple instances)
3. `backend/app/agents/construction_metrics/workflow.py` (Add vision detection)
4. `backend/app/agents/tool_registry.py` (Update all tool wrappers)
5. `backend/app/agents/claude_cli_agent.py` (1 change)
6. `backend/app/api/routes/agent_routes.py` (Verify model_id passing)

**Expected Outcome**:
✅ Users can select any LLM model in the UI
✅ Agent tasks use the selected model throughout execution
✅ Vision agents intelligently fallback to vision models when needed
✅ Model selection is logged and traceable

---

**Status**: 📋 READY FOR IMPLEMENTATION
**Estimated Time**: 2-3 hours for all fixes
**Testing Time**: 1 hour for comprehensive testing

**Next Step**: Begin with Fix 1 (EnhancedRAGAgent) as it's the entry point for all agent tasks.
