# Phase 3: User Feedback - Model Selection Integration

**Date**: 2025-11-26
**Status**: ⚠️ **Important User Feedback Received**

---

## User Feedback

**User said**:
> "model_id="gpt-4" ?? it should pick up from the dropdown OR pick the right model id from db(chat gpt_)"

**User is 100% CORRECT!**

The model selection should come from:
1. **Frontend UI dropdown** (user's choice)
2. **Model Registry database** (for model metadata and capabilities)

NOT from hardcoded `model_id="gpt-4"` in the workflow!

---

## Current Situation Analysis

### Current Project Estimator API (`project_estimator_routes.py`)

**Does NOT have a model selection parameter:**

```python
@router.post("/generate-agentic")
async def generate_agentic_estimate(
    # Required: Project description
    project_scope: str = Form(..., description="Project description/prompt"),

    # Required: Project configuration
    project_type: str = Form(..., description="POC, Staff Augmentation, or Full Service"),
    scenario: str = Form(..., description="baseline, conservative, or aggressive"),

    # Required: Rate configuration (JSON string)
    rate_config: str = Form(..., description="JSON object with rate categories and values"),

    # Optional: Overhead configuration
    overhead_config: Optional[str] = Form(None, description="JSON object with overhead percentages"),

    # ❌ NO MODEL_ID PARAMETER!
    # ... other parameters ...
)
```

### Current Workflow (`workflow.py`)

**Hardcoded model selection in all 12 agent calls:**

```python
response = await self.llm_service.generate(
    prompt=prompt,
    model_id="gpt-4",  # ← HARDCODED - WRONG!
    temperature=0.3
)
```

---

## What Needs to Be Implemented

### 1. Add Model Selection to API Endpoint ✅ (Easy Fix)

**File**: `backend/app/api/routes/project_estimator_routes.py`

**Add parameter to endpoint:**

```python
@router.post("/generate-agentic")
async def generate_agentic_estimate(
    # ... existing parameters ...

    # ✅ ADD THIS:
    model_id: Optional[str] = Form(None, description="LLM model to use (e.g., 'gpt-4', 'llama3.2-vision:11b')"),

    db: Session = Depends(get_db)
):
    # If no model_id provided, use Model Registry to get recommended model
    if not model_id:
        from app.models.model_registry import get_model_registry
        registry = get_model_registry()
        recommended_model = registry.get_recommended_model()
        model_id = recommended_model.model_path if recommended_model else "gpt-4"
        logger.info(f"No model specified, using recommended: {model_id}")

    # Pass model_id to workflow
    workflow = ProjectEstimatorWorkflow(llm_service, db)
    result = await workflow.run(
        user_prompt=project_scope,
        model_id=model_id,  # ← Pass user's choice
        # ... other parameters ...
    )
```

### 2. Update Workflow to Accept Model ID ✅

**File**: `backend/app/agents/project_estimator/workflow.py`

**Update workflow `run()` method:**

```python
class ProjectEstimatorWorkflow:
    def __init__(self, llm_service: LLMService, db: Session):
        self.llm_service = llm_service
        self.db = db
        self.model_id = None  # ← Add instance variable

    async def run(
        self,
        user_prompt: str,
        model_id: str = "gpt-4",  # ← Add parameter with default
        # ... other parameters ...
    ) -> Dict[str, Any]:
        """
        Run the Project Estimator workflow.

        Args:
            user_prompt: Project description
            model_id: LLM model to use (from user selection or Model Registry)
            ...
        """
        self.model_id = model_id  # ← Store for agent calls

        # Initialize state
        state = ProjectEstimatorState(
            user_prompt=user_prompt,
            model_id=model_id,  # ← Add to state
            # ... other state fields ...
        )

        # Run workflow
        result = await self.graph.ainvoke(state)
        return result
```

### 3. Update Helper Method to Use User's Model Selection ✅

**File**: `backend/app/agents/project_estimator/workflow.py`

**Update `_call_llm_optimized()` helper method:**

```python
async def _call_llm_optimized(
    self,
    agent_name: str,
    context_variables: Dict[str, Any],
    max_tokens: int = 2000,
    temperature: float = 0.3
) -> str:
    """
    Optimized LLM call with user's model selection.
    """
    from app.agents.project_estimator.prompt_templates import PromptTemplates
    from app.tools.text_compression_tool import compress_for_llm
    from app.utils.text_compression import count_tokens

    # ✅ Use user's model selection (from self.model_id or state)
    model_name = self.model_id if self.model_id else "gpt-4"

    logger.info(f"🔧 Optimized LLM Call for {agent_name}")
    logger.info(f"   User selected model: {model_name}")

    # Get model's context window size
    context_window = PromptTemplates.get_model_context_window(model_name)
    logger.info(f"   Context window: {context_window} tokens")

    # Select appropriate prompt template (compact or verbose)
    prompt = PromptTemplates.get_prompt(
        agent_name=agent_name,
        context_variables=context_variables,
        model_context_window=context_window
    )

    original_tokens = count_tokens(prompt)
    logger.info(f"   Original prompt: {original_tokens} tokens")

    # Compress if model is small (context window < 16K)
    if context_window < 16000:
        logger.info(f"   🗜️  Small model detected - compressing prompt...")
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

    # Call LLM with user's selected model
    # LLM service will automatically fallback if this model fails
    try:
        result = await self.llm_service.generate(
            prompt=prompt,
            model_id=model_name,  # ← User's choice!
            max_tokens=max_tokens,
            temperature=temperature
        )

        logger.info(f"   ✅ LLM call succeeded")
        logger.info(f"   Model used: {result.get('model_name', model_name)}")
        logger.info(f"   Tokens: {result.get('tokens', 0)}")

        return result.get("content", "")

    except Exception as e:
        logger.error(f"   ❌ LLM call failed: {e}")
        raise
```

### 4. Update Frontend to Send Model Selection ✅

**File**: `frontend/src/components/ProjectEstimator.tsx`

**Add model selection to form submission:**

```typescript
const handleSubmit = async () => {
  const formData = new FormData();

  // ... existing form fields ...

  // ✅ ADD THIS: Include user's model selection
  formData.append('model_id', selectedModel);  // From ModelSelector dropdown

  const response = await axios.post(
    'http://localhost:8000/api/v1/project-estimator/generate-agentic',
    formData
  );
};
```

---

## Benefits of This Approach

### ✅ User Control
- User selects their preferred model from UI dropdown
- Respects user's choice (GPT-4, Claude, LLaMA, etc.)
- No hardcoded assumptions

### ✅ Model Registry Integration
- Uses Model Registry database for model metadata
- Gets context window size, capabilities, pricing
- Recommends best model if user doesn't select one

### ✅ Automatic Optimization
- Still uses compact prompts for small models
- Still compresses text when needed
- Still falls back if selected model fails

### ✅ Flexibility
- User can try different models easily
- Compare GPT-4 vs LLaMA quality
- Use local models when OpenAI quota exhausted

---

## Implementation Priority

### Priority 1 (MUST HAVE):
1. ✅ Add `model_id` parameter to API endpoint
2. ✅ Update workflow to accept and use `model_id`
3. ✅ Update frontend to send model selection

### Priority 2 (SHOULD HAVE):
4. ✅ Add Model Registry lookup for recommended model
5. ✅ Log which model was actually used
6. ✅ Track token usage per model

### Priority 3 (NICE TO HAVE):
7. ⏳ Display model used in UI response
8. ⏳ Show token savings when using small models
9. ⏳ Add model performance metrics

---

## Next Steps

1. **First**: Add `model_id` parameter to API endpoint
2. **Second**: Update workflow to use user's model selection
3. **Third**: Test with different models (GPT-4, LLaMA Vision)
4. **Fourth**: Update Phase 3 integration plan to reflect this

---

## User is Correct!

The user's feedback is **100% correct** and highlights an important missing feature:

❌ **Current (WRONG)**:
- Hardcoded `model_id="gpt-4"`
- Ignores user's dropdown selection
- Doesn't use Model Registry

✅ **Should Be (CORRECT)**:
- `model_id` from user's UI dropdown
- Or from Model Registry recommendation
- Flexible and user-controlled

---

**Created By**: Claude Code Assistant
**Last Updated**: 2025-11-26
**Status**: Important user feedback - needs immediate implementation

**Thank you for catching this!** This is a critical improvement that makes the system truly flexible and user-friendly.
