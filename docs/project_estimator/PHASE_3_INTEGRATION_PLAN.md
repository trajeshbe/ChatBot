# Phase 3: Project Estimator Integration Plan

**Date**: 2025-11-26
**Status**: ⏳ **Ready to Integrate**

---

## Current Status

✅ **Phase 1 Complete**: LLM fallback configuration in `.env`
✅ **Phase 2 Complete**: Core optimization utilities created
✅ **Phase 3 Step 1 Complete**: Text compression tool registered in tool registry
⏳ **Phase 3 Step 2-7**: Project Estimator workflow integration (THIS PLAN)

---

## What Needs to Be Integrated

### 1. Understanding the Current Workflow

**File**: `backend/app/agents/project_estimator/workflow.py`

**Current LLM Call Pattern** (12 locations):
```python
response = await self.llm_service.generate(
    prompt=prompt,
    model_id="gpt-4",  # ← HARDCODED
    temperature=0.3
)
```

**Problem**:
- Hardcoded `model_id="gpt-4"` in all 12 agent calls
- No automatic fallback when OpenAI fails
- No prompt compression for small models
- No compact template selection based on model
- No token usage tracking

### 2. LLM Service Already Has Fallback Logic

**File**: `backend/app/services/llm_service.py`

**The `generate()` method** (line 405):
```python
async def generate(
    self,
    prompt: str,
    messages: Optional[List[Dict]] = None,
    max_tokens: int = 512,
    temperature: float = 0.7,
    use_fallback: bool = True,
    model_id: Optional[str] = None  # ← ALREADY ACCEPTS model_id!
) -> Dict:
    """
    Generate response with automatic fallback chain:
    OpenAI -> Ollama -> vLLM -> llama.cpp
    """
```

**Key Discovery**:
- ✅ LLM service **already supports** `model_id` parameter
- ✅ LLM service **already has** automatic fallback (OpenAI → Ollama → vLLM → llama.cpp)
- ✅ If `model_id` is provided but fails, it falls back to next available provider

**However**:
- ❌ Workflow doesn't use dynamic model selection
- ❌ No prompt compression before sending to small models
- ❌ No compact template selection

---

## Integration Strategy

### Add a Helper Method to Workflow Class

Add a new method `_call_llm_optimized()` to `ProjectEstimatorWorkflow` that:

1. **Detects model availability**
   - Try to determine which LLM is actually available
   - Prefer OpenAI (GPT-4) if available
   - Fallback to Ollama (llama3.2-vision:11b) if OpenAI fails

2. **Selects appropriate prompt template**
   - Use `PromptTemplates.get_prompt()` method (already exists!)
   - Automatically selects COMPACT or VERBOSE based on model's context window
   - Example: GPT-4 gets verbose prompts, LLaMA Vision gets compact prompts

3. **Compresses text if needed**
   - Check if model is small (context window < 16K tokens)
   - If small, use `compress_for_llm()` to compress prompts
   - Preserve structure while reducing tokens by 70-85%

4. **Logs token usage**
   - Track which model was used
   - Log original vs compressed token counts
   - Calculate cost savings

### Implementation Code

```python
# Add to backend/app/agents/project_estimator/workflow.py

async def _call_llm_optimized(
    self,
    agent_name: str,
    context_variables: Dict[str, Any],
    max_tokens: int = 2000,
    temperature: float = 0.3
) -> str:
    """
    Optimized LLM call with automatic:
    - Model selection (GPT-4 or LLaMA Vision)
    - Prompt template selection (verbose or compact)
    - Text compression for small models
    - Token usage logging

    Args:
        agent_name: Name of agent for prompt template (e.g., "agent_1_analyst")
        context_variables: Variables to inject into prompt template
        max_tokens: Maximum tokens for response
        temperature: LLM temperature

    Returns:
        LLM response content
    """
    from app.agents.project_estimator.prompt_templates import PromptTemplates
    from app.tools.text_compression_tool import compress_for_llm
    from app.utils.text_compression import count_tokens

    # Step 1: Detect model availability and select model
    # Try GPT-4 first (fastest, most capable)
    # Fallback to llama3.2-vision:11b if GPT-4 unavailable
    model_name = "gpt-4"  # LLM service will auto-fallback if this fails

    # Get model's context window size
    context_window = PromptTemplates.get_model_context_window(model_name)

    logger.info(f"🔧 Optimized LLM Call for {agent_name}")
    logger.info(f"   Model: {model_name}")
    logger.info(f"   Context window: {context_window} tokens")

    # Step 2: Select appropriate prompt template (compact or verbose)
    # PromptTemplates.get_prompt() automatically selects based on context_window
    prompt = PromptTemplates.get_prompt(
        agent_name=agent_name,
        context_variables=context_variables,
        model_context_window=context_window
    )

    original_tokens = count_tokens(prompt)
    logger.info(f"   Original prompt: {original_tokens} tokens")

    # Step 3: Compress if model is small (context window < 16K)
    if context_window < 16000:
        logger.info(f"   🗜️  Small model detected - compressing prompt...")

        # Compress to fit within model's context window
        # Reserve 70% for input, 30% for output
        target_tokens = int(context_window * 0.7)

        compressed_prompt = compress_for_llm(
            text=prompt,
            model_name=model_name,
            target_tokens=target_tokens,
            compression_method="smart"
        )

        compressed_tokens = count_tokens(compressed_prompt)
        reduction_pct = (1 - compressed_tokens / original_tokens) * 100

        logger.info(f"   ✅ Compressed: {compressed_tokens} tokens ({reduction_pct:.1f}% reduction)")

        prompt = compressed_prompt
    else:
        logger.info(f"   ✅ Large model - using full prompt")

    # Step 4: Call LLM with automatic fallback
    try:
        result = await self.llm_service.generate(
            prompt=prompt,
            model_id=model_name,  # Will auto-fallback if GPT-4 unavailable
            max_tokens=max_tokens,
            temperature=temperature
        )

        logger.info(f"   ✅ LLM call succeeded")
        logger.info(f"   Model used: {result.get('model_name', model_name)}")
        logger.info(f"   Tokens: {result.get('tokens', 0)}")
        logger.info(f"   Latency: {result.get('latency_ms', 0):.0f}ms")

        return result.get("content", "")

    except Exception as e:
        logger.error(f"   ❌ LLM call failed: {e}")
        raise
```

---

## Step-by-Step Integration

### Step 1: Add Helper Method to Workflow Class ✅

Add `_call_llm_optimized()` method to `ProjectEstimatorWorkflow` class (around line 150).

### Step 2: Replace Hardcoded LLM Calls (12 Locations)

Replace all instances of:
```python
response = await self.llm_service.generate(
    prompt=prompt,
    model_id="gpt-4",
    temperature=0.3
)
```

With:
```python
response_content = await self._call_llm_optimized(
    agent_name="agent_1_analyst",  # Or appropriate agent name
    context_variables={
        "user_prompt": state["user_prompt"],
        "requirements_summary": state.get("requirements", {}),
        # ... other variables needed for prompt
    },
    temperature=0.3
)
```

**12 Locations to Update**:
1. Line ~361: `_analyze_brd_examples` → Use `agent_1_analyst`
2. Line ~389: `_analyze_cost_examples` → Use `agent_4_cost_estimator`
3. Line ~417: `_analyze_sample_data` → Use `agent_1_1_eda`
4. Line ~523: `_extract_requirements` → Use `agent_1_analyst`
5. Line ~758: Team planner → Use `agent_2_team_planner`
6. Line ~802: Clarification response → Use `agent_1_analyst`
7. Line ~935: Task generator → Use `agent_3_task_breakdown`
8. Line ~1179: Workflow agent → Use custom workflow agent prompt
9. Line ~1305: Rate assignment → Use `agent_4_cost_estimator`
10. Line ~1439: Risk analyzer → Use `agent_5_risk_analyzer`
11. Line ~1633: Document generator → Use `agent_6_doc_generator`
12. Line ~2739: Validator agent → Use custom validator prompt

---

## Expected Benefits

### 🎯 Automatic Model Selection
- ✅ Tries GPT-4 first for best quality
- ✅ Falls back to LLaMA Vision 11B if OpenAI unavailable
- ✅ Falls back to Ollama → vLLM → llama.cpp if all fail

### 💰 Cost Savings
- ✅ Use free local LLaMA models when GPT-4 quota exceeded
- ✅ Reduce token usage by 70-85% for small models
- ✅ Zero OpenAI API costs when using local models

### 📊 Token Optimization
- ✅ Compact prompts for small models (reduce from 1500 → 300 tokens per agent call)
- ✅ Verbose prompts for large models (maintain quality)
- ✅ Smart compression preserves structure

### 🔧 Maintainability
- ✅ Single method to maintain (`_call_llm_optimized`)
- ✅ Easy to add new agents
- ✅ Centralized token logging

---

## Prompt Template Mapping

The `PromptTemplates` class already has:

### Verbose Prompts (for GPT-4, Claude, etc.)
- `AGENT_1_VERBOSE`: Detailed requirements extraction (~800 tokens)
- `AGENT_2_VERBOSE`: Comprehensive team planning (~600 tokens)
- `AGENT_3_VERBOSE`: Detailed task breakdown (~700 tokens)
- `AGENT_4_VERBOSE`: Comprehensive cost estimation (~800 tokens)
- `AGENT_5_VERBOSE`: Detailed risk analysis (~600 tokens)
- `AGENT_6_VERBOSE`: Comprehensive doc generation (~900 tokens)

### Compact Prompts (for LLaMA, Qwen, Mistral)
- `AGENT_1_COMPACT`: Concise requirements extraction (~150 tokens)
- `AGENT_2_COMPACT`: Brief team planning (~120 tokens)
- `AGENT_3_COMPACT`: Concise task breakdown (~140 tokens)
- `AGENT_4_COMPACT`: Brief cost estimation (~130 tokens)
- `AGENT_5_COMPACT`: Concise risk analysis (~100 tokens)
- `AGENT_6_COMPACT`: Brief doc generation (~180 tokens)

**Token savings**: ~85% per agent call when using compact prompts!

---

## Next Steps

1. ✅ Create this integration plan
2. ⏳ Add `_call_llm_optimized()` helper method to workflow.py
3. ⏳ Replace all 12 hardcoded LLM calls with optimized calls
4. ⏳ Test with GPT-4 (should use verbose prompts)
5. ⏳ Test with LLaMA Vision 11B (should use compact prompts + compression)
6. ⏳ Measure token savings and quality comparison
7. ⏳ Document results

---

## Testing Strategy

### Test 1: GPT-4 (Baseline)
- Run Project Estimator with GPT-4
- Verify it uses **verbose prompts**
- Verify it does **NOT compress** (context window = 128K)
- Measure total tokens used

### Test 2: LLaMA Vision 11B (Optimized)
- Disable OpenAI (or exhaust quota)
- Run Project Estimator with LLaMA Vision
- Verify it uses **compact prompts** (context window = 8K)
- Verify it **compresses** prompts to fit
- Measure total tokens used
- Compare output quality vs GPT-4

### Expected Results
- **GPT-4**: ~15,000 tokens total (6 agents × ~2,500 tokens each)
- **LLaMA Vision**: ~3,000 tokens total (6 agents × ~500 tokens each)
- **Token reduction**: 80% savings when using LLaMA Vision
- **Quality**: Should be comparable (compact prompts preserve key info)

---

**Created By**: Claude Code Assistant
**Last Updated**: 2025-11-26
**Status**: Ready for implementation in workflow.py
