# Context Window Optimization Strategy for Small LLMs

**Date**: 2025-11-26
**Purpose**: Optimize Project Estimator workflow for LLaMA 3.2 Vision's limited context window
**Target Model**: LLaMA 3.2 Vision 11B (~8K tokens context window)
**Challenge**: Fit scope, complexity, EDA insights, and sample guidance within small context

---

## Problem Statement

The Project Estimator workflow currently uses verbose prompts designed for GPT-4's 128K token context window. With the fallback to LLaMA 3.2 Vision (only ~8K tokens), we need to optimize:

1. **Agent Prompts**: Compress from verbose instructions to concise templates
2. **State Management**: Pass only essential data between agents
3. **Sample Data**: Summarize instead of including full content
4. **Memory Strategy**: Cache intermediate results intelligently

---

## Context Window Comparison

| Model | Context Window | Current Usage (est.) | Target Usage |
|-------|----------------|---------------------|--------------|
| GPT-4 Turbo | 128K tokens | 5-15K tokens/call | No issues |
| LLaMA 3.2 Vision 11B | **8K tokens** | **10-20K tokens/call** | **<6K tokens/call** |
| Safe margin | - | - | Leave 2K for response |

**Current Problem**: Each agent call potentially uses 10-20K tokens, causing overflow and truncation.

---

## Optimization Strategies

### Strategy 1: Prompt Compression

#### Before (Verbose)
```python
prompt = f"""
You are an expert Project Analyst with deep expertise in software development requirements engineering.

Your task is to analyze the following project scope document and extract structured requirements.

Please carefully read the project description below:
{user_prompt}

Based on the uploaded sample BRDs, you should understand the typical format and structure.

Sample BRD patterns analyzed from {len(uploaded_brd_files)} files:
{brd_patterns_summary}

Now, extract the following information...
[500+ more words of instructions]
"""
```

#### After (Compressed)
```python
prompt = f"""Extract requirements from scope. Return JSON with: project_goal, key_features, technical_scope, constraints, success_criteria.

Scope:
{user_prompt[:1000]}  # Limit scope to 1000 chars

Context from samples: {compress_patterns(brd_patterns_summary, max_tokens=200)}
"""
```

**Token savings**: ~2000 tokens → ~300 tokens

---

### Strategy 2: State Pruning

#### Before (Full State Passed)
```python
state = {
    "user_prompt": full_scope,  # Could be 5000 tokens
    "requirements": {...},  # 1000 tokens
    "complexity_analysis": {
        "eda_report": {...},  # 3000 tokens
        "reasoning": "...",  # 500 tokens
        "full_details": {...}  # 2000 tokens
    },
    "uploaded_brd_files": [...],  # 500 tokens
    # ... more fields
}
```

#### After (Pruned State)
```python
# Only pass ESSENTIAL fields to each agent
state = {
    "user_prompt_summary": user_prompt[:500],  # Truncate
    "requirements_compact": {
        "goal": requirements["project_goal"][:200],
        "features": requirements["key_features"][:5],  # Top 5 only
    },
    "complexity_summary": {
        "rating": complexity_analysis["overall_rating"],
        "multipliers": complexity_analysis["impact_on_estimation"],
        # Skip full EDA report - use summary only
        "key_insights": extract_top_insights(eda_report, top_n=3)
    }
}
```

**Token savings**: ~12,000 tokens → ~1,500 tokens

---

### Strategy 3: EDA Report Summarization

#### Current EDA Report Structure
```python
eda_report = {
    "domain": "construction",
    "detected_data_types": ["drawings", "schedules", "bom"],
    "overall_data_quality": 0.87,
    "complexity_indicators": {...},  # 1000+ tokens
    "file_analysis": [
        {"filename": "...", "detailed_stats": {...}},  # 500+ tokens per file
        # ... more files
    ],
    "recommendations": {...}  # 800 tokens
}
```

#### Optimized Summary
```python
eda_summary = {
    "domain": eda_report["domain"],
    "data_quality": round(eda_report["overall_data_quality"], 2),
    "key_types": eda_report["detected_data_types"][:3],
    "complexity": eda_report.get("overall_complexity", "Medium"),
    "top_insight": get_most_important_insight(eda_report)
}
```

**Token savings**: ~3000 tokens → ~150 tokens

---

### Strategy 4: Chunked Processing

For agents that need access to full scope or samples:

```python
async def process_with_chunks(full_text: str, max_chunk_size: int = 2000):
    """
    Process long text in chunks and aggregate results.
    """
    chunks = split_text_smart(full_text, max_chunk_size)

    results = []
    for chunk in chunks:
        result = await llm_service.generate(
            prompt=f"Analyze: {chunk}",
            max_tokens=500
        )
        results.append(result)

    # Aggregate results
    return aggregate_insights(results)
```

---

### Strategy 5: Caching & Memory Hierarchy

```python
class OptimizedStateManager:
    """
    Smart state management with Redis caching.
    """

    def __init__(self):
        self.redis_client = redis.Redis()
        self.cache_ttl = 3600  # 1 hour

    async def get_compact_state(self, workflow_id: str, agent_name: str):
        """
        Return only the state fields needed by this specific agent.
        """
        full_state = await self.get_full_state(workflow_id)

        # Agent-specific state views
        agent_state_map = {
            "analyst": ["user_prompt_summary"],
            "complexity_analyzer": ["uploaded_files", "user_prompt_summary"],
            "team_planner": ["requirements_compact", "complexity_summary"],
            "task_generator": ["requirements_compact", "team_structure"],
            "rate_assignment": ["team_structure", "complexity_summary"],
            "doc_generator": ["all"]  # Only this agent needs full state
        }

        required_fields = agent_state_map.get(agent_name, ["user_prompt_summary"])

        return {k: full_state[k] for k in required_fields if k in full_state}

    async def cache_intermediate_result(self, workflow_id: str, agent_name: str, result: Dict):
        """
        Cache agent outputs to avoid re-computation.
        """
        cache_key = f"workflow:{workflow_id}:agent:{agent_name}"
        await self.redis_client.setex(
            cache_key,
            self.cache_ttl,
            json.dumps(result)
        )
```

---

## Agent-Specific Optimizations

### Agent 1: Requirements Analyst

#### Current Token Usage: ~8,000 tokens
- Prompt instructions: 2,000 tokens
- User scope: 3,000 tokens
- Sample BRD patterns: 2,000 tokens
- Other context: 1,000 tokens

#### Optimized: ~3,500 tokens
```python
async def requirements_analyst_optimized(state: Dict) -> Dict:
    """
    Optimized requirements extraction with compressed prompts.
    """
    # Compress user prompt
    scope_summary = compress_text(
        state["user_prompt"],
        max_length=800,
        method="extractive"  # Keep key sentences only
    )

    # Get cached BRD patterns summary (pre-computed)
    brd_patterns = await get_cached_patterns_summary(
        state["uploaded_brd_files"],
        max_tokens=300
    )

    # Ultra-concise prompt
    prompt = f"""Extract JSON: {{project_goal, key_features[], technical_scope{{}}, constraints{{}}, success_criteria[]}}.

Scope: {scope_summary}

BRD patterns: {brd_patterns}
"""

    response = await llm_service.generate(
        prompt=prompt,
        model_id="llama3.2-vision:11b",
        temperature=0.3,
        max_tokens=800  # Limit response size
    )

    return json.loads(extract_json_from_response(response))
```

**Token savings**: 8,000 → 3,500 tokens (56% reduction)

---

### Agent 1.1: Sample Complexity Analyzer (EDA)

#### Current Token Usage: ~12,000 tokens
- Prompt: 1,500 tokens
- Full EDA report in state: 5,000 tokens
- File analysis details: 4,000 tokens
- Tech stack recommendations: 1,500 tokens

#### Optimized: ~2,000 tokens
```python
async def complexity_analyzer_optimized(state: Dict) -> Dict:
    """
    Generate compact EDA summary instead of full report.
    """
    # Run EDA analysis (same as before)
    eda_report = await perform_full_eda(state["uploaded_sample_data"])

    # Cache full report in Redis for later use (not in state)
    await cache_full_eda_report(state["workflow_id"], eda_report)

    # Create ultra-compact summary for state
    eda_compact = {
        "complexity": eda_report["overall_complexity"],  # "Low" | "Medium" | "High"
        "quality_score": round(eda_report["overall_data_quality"], 2),
        "domain": eda_report["domain"],
        "key_data_types": eda_report["detected_data_types"][:3],
        "effort_multiplier": eda_report["impact_on_estimation"]["effort_multiplier"],
        "rate_multiplier": eda_report["impact_on_estimation"]["rate_multiplier"],
        "top_3_insights": extract_top_insights(eda_report, n=3),  # 100 tokens total
        "recommended_teams": eda_report["recommended_teams"][:5]
    }

    # Prompt uses only compact summary
    return {
        **state,
        "complexity_analysis": eda_compact,
        # Full report cached separately, not in state
    }
```

**Token savings**: 12,000 → 2,000 tokens (83% reduction)

---

### Agent 2: Team Planner

#### Current: Receives full requirements + full complexity analysis
#### Optimized: Receives compact summaries only

```python
async def team_planner_optimized(state: Dict) -> Dict:
    """
    Team planning with minimal context.
    """
    # Only needs: project goal + complexity + recommended teams
    compact_input = {
        "goal": state["requirements"]["project_goal"][:200],
        "complexity": state["complexity_analysis"]["complexity"],
        "recommended_teams": state["complexity_analysis"]["recommended_teams"]
    }

    prompt = f"""Identify engineering teams needed.

Goal: {compact_input["goal"]}
Complexity: {compact_input["complexity"]}
Suggested: {', '.join(compact_input["recommended_teams"])}

Return JSON: {{teams: [{{name, role, justification}}]}}
"""

    response = await llm_service.generate(
        prompt=prompt,
        model_id="llama3.2-vision:11b",
        max_tokens=600
    )

    return json.loads(extract_json_from_response(response))
```

**Token savings**: 6,000 → 1,500 tokens (75% reduction)

---

### Agent 3-5: Task Generator, Workflow, Rate Assignment

Similar optimizations:
1. Receive only relevant state fields
2. Use compressed prompts
3. Reference cached data via IDs instead of including full content
4. Limit response tokens

---

### Agent 6: Document Generator

**Special Case**: This agent DOES need full state to generate complete BRD and Excel files.

**Strategy**:
- Pull full cached data from Redis
- Reconstruct complete state
- Use GPT-4 if available (fallback for this agent only)

```python
async def doc_generator_optimized(state: Dict) -> Dict:
    """
    Document generation with full state reconstruction.
    """
    # Reconstruct full state from cache
    full_eda_report = await get_cached_eda_report(state["workflow_id"])
    full_requirements = await get_cached_requirements(state["workflow_id"])

    # Try GPT-4 first for this agent (better quality for final docs)
    # Only use LLaMA Vision if GPT-4 fails
    models_to_try = ["gpt-4-turbo", "llama3.2-vision:11b"]

    for model in models_to_try:
        try:
            brd_doc = await generate_brd(
                requirements=full_requirements,
                eda_report=full_eda_report,
                # ... other full data
                model_id=model
            )
            break
        except Exception as e:
            logger.warning(f"Failed with {model}: {e}")
            continue

    return {"brd_url": brd_doc_url, ...}
```

---

## Implementation Plan

### Phase 1: Add Fallback Environment Variables ✅
```bash
# Already documented in LLAMA_VISION_FALLBACK_QUICK_SETUP.md
ENABLE_LLM_FALLBACK=true
FALLBACK_LLM_MODELS=llama3.2-vision:11b
FUNCTION_CALLING_MODELS=gpt-4-turbo,gpt-4,llama3.2-vision:11b
```

### Phase 2: Implement Text Compression Utilities
Create `backend/app/utils/text_compression.py`:
```python
def compress_text(text: str, max_length: int, method: str = "extractive") -> str:
    """
    Compress text to fit within max_length using various methods.
    """
    if len(text) <= max_length:
        return text

    if method == "truncate":
        return text[:max_length] + "..."

    elif method == "extractive":
        # Keep most important sentences
        sentences = sent_tokenize(text)
        # Score by position and keyword density
        scored = score_sentences(sentences)
        # Take top sentences until max_length
        return " ".join(select_top_sentences(scored, max_length))

    elif method == "abstractive":
        # Use small summarization model (e.g., BART)
        return summarize_with_model(text, max_length)
```

### Phase 3: Add State Manager with Redis Caching
Create `backend/app/services/optimized_state_manager.py`

### Phase 4: Refactor Agent Prompts
Update `backend/app/agents/project_estimator/workflow.py`:
- Add `use_compact_prompts` flag
- Detect model context window size
- Switch prompts based on model

### Phase 5: Add Prompt Templates
Create `backend/app/agents/project_estimator/prompt_templates.py`:
```python
AGENT_PROMPTS = {
    "analyst": {
        "gpt4": VERBOSE_PROMPT,  # Current verbose version
        "llama": COMPACT_PROMPT   # New compressed version
    },
    # ... for each agent
}
```

---

## Token Budget Per Agent

| Agent | GPT-4 Budget | LLaMA Budget | Savings |
|-------|-------------|--------------|---------|
| Agent 1 (Analyst) | 8,000 tokens | 3,500 tokens | 56% |
| Agent 1.1 (EDA) | 12,000 tokens | 2,000 tokens | 83% |
| Agent 1.2 (Debate) | 5,000 tokens | 1,800 tokens | 64% |
| Agent 2 (Teams) | 6,000 tokens | 1,500 tokens | 75% |
| Agent 3 (Tasks) | 7,000 tokens | 2,200 tokens | 69% |
| Agent 4 (Workflow) | 6,000 tokens | 2,000 tokens | 67% |
| Agent 5 (Rates) | 5,000 tokens | 1,800 tokens | 64% |
| Agent 6 (Docs) | 15,000 tokens | Use GPT-4 fallback | N/A |
| **Total** | **64,000 tokens** | **14,800 tokens** | **77% reduction** |

---

## Testing Strategy

### Test 1: Token Usage Measurement
```python
# Add token counter to each LLM call
def count_tokens(text: str) -> int:
    # Use tiktoken for estimation
    import tiktoken
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))

# Log before each LLM call
logger.info(f"Agent {agent_name} - Input tokens: {count_tokens(prompt)}")
```

### Test 2: Quality Comparison
Run same project through:
1. GPT-4 workflow (verbose prompts)
2. LLaMA workflow (compact prompts)
3. Compare output quality metrics

### Test 3: Fallback Chain Validation
Simulate OpenAI failure:
1. Disable OpenAI API key
2. Run workflow
3. Verify LLaMA Vision is used
4. Check output quality

---

## Monitoring & Metrics

### Dashboard Metrics
1. **Token Usage Per Agent**: Track actual vs budget
2. **Model Usage Distribution**: % OpenAI vs LLaMA
3. **Context Overflow Events**: Count truncations
4. **Quality Scores**: Compare outputs from different models
5. **Latency**: LLaMA vs OpenAI response times

### Alerts
- Alert if any agent exceeds 6K tokens with LLaMA
- Alert if fallback success rate < 90%
- Alert if quality score drops > 20% with LLaMA

---

## Expected Outcomes

### Cost Savings
```
Before (OpenAI only):
100 workflow runs × $0.50/run = $50.00

After (50% fallback to LLaMA):
50 OpenAI runs × $0.50 = $25.00
50 LLaMA runs × $0.00 = $0.00
Total: $25.00 (50% savings)
```

### Performance
- **Latency**: LLaMA may be 10-20% slower than GPT-4
- **Throughput**: Unlimited with local LLM (no rate limits)
- **Quality**: Target 90%+ quality retention with optimized prompts

### Reliability
- **Zero downtime**: Automatic fallback ensures workflow continues
- **No rate limit failures**: LLaMA provides unlimited capacity
- **Privacy**: Sensitive data stays local during fallback

---

## Rollout Plan

### Week 1: Infrastructure
- ✅ Add fallback environment variables
- ✅ Update LLM service with fallback logic
- ✅ Test basic fallback chain

### Week 2: Optimization
- Implement text compression utilities
- Create state manager with Redis caching
- Add compact prompt templates

### Week 3: Integration
- Update workflow to use compact prompts for LLaMA
- Implement agent-specific state pruning
- Add token usage monitoring

### Week 4: Testing & Validation
- Run quality comparison tests
- Tune compression ratios
- Optimize based on results

---

## Success Criteria

✅ **Each agent uses < 6K tokens with LLaMA Vision**
✅ **Fallback success rate > 95%**
✅ **Output quality > 90% of GPT-4 baseline**
✅ **Zero workflow failures due to context overflow**
✅ **50%+ cost savings from fallback usage**

---

**Created By**: Claude Code Assistant
**Last Updated**: 2025-11-26
**Next Action**: Implement Phase 2 (text compression utilities)
