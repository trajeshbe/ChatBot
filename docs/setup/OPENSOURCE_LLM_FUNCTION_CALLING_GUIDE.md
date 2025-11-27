# Open-Source LLM Function Calling Guide for Project Estimator

**Date**: 2025-11-26
**Purpose**: Replace OpenAI API with open-source alternatives for LLM function calling
**Status**: ✅ Ready for Implementation

---

## Problem Statement

OpenAI API limits have been exhausted. Need to migrate the Project Estimator workflow (6-agent system) to an open-source alternative that supports:
- ✅ Function/Tool calling
- ✅ Complex agentic workflows
- ✅ JSON mode for structured outputs
- ✅ Long context windows (32K+)
- ✅ Fast local inference

---

## 🏆 Top Recommended Solution: Qwen 2.5 Coder

### Why Qwen 2.5 Coder?

1. **Native Function Calling**: Built-in tool use matching GPT-4 quality
2. **Optimized for Code**: Trained specifically for software development tasks
3. **Multiple Sizes**: From 7B (fast) to 72B (best quality)
4. **Long Context**: Up to 128K tokens
5. **JSON Mode**: Reliable structured outputs
6. **Ollama Support**: Easy deployment and management
7. **Production Ready**: Actively maintained by Alibaba Cloud

### Quick Comparison

| Model | Size | Function Calling | Context | Speed | Quality |
|-------|------|------------------|---------|-------|---------|
| **Qwen 2.5 Coder** | 32B | ✅ Native | 128K | Fast | ⭐⭐⭐⭐⭐ |
| Qwen 2.5 Coder | 14B | ✅ Native | 128K | Very Fast | ⭐⭐⭐⭐ |
| Hermes 3 | 70B | ✅ Native | 128K | Medium | ⭐⭐⭐⭐ |
| DeepSeek Coder V2 | 16B | ✅ Via Prompt | 64K | Fast | ⭐⭐⭐⭐ |
| Command R+ | 104B | ✅ Native | 128K | Slow | ⭐⭐⭐⭐⭐ |

---

## 🚀 Implementation Guide

### Step 1: Install Qwen 2.5 Coder with Ollama

```bash
# Option A: 32B model (recommended - best balance)
docker-compose exec ollama ollama pull qwen2.5-coder:32b

# Option B: 14B model (faster, good for testing)
docker-compose exec ollama ollama pull qwen2.5-coder:14b

# Option C: 7B model (fastest, acceptable quality)
docker-compose exec ollama ollama pull qwen2.5-coder:7b

# Verify installation
docker-compose exec ollama ollama list
```

**Expected Output**:
```
NAME                    ID              SIZE      MODIFIED
qwen2.5-coder:32b       abc123def456    19 GB     2 minutes ago
```

---

### Step 2: Test Function Calling

Create a test script to verify function calling works:

```bash
cat > /tmp/test_qwen_function_calling.py << 'EOF'
"""
Test Qwen 2.5 Coder function calling capabilities
"""
import httpx
import json

# Test 1: Simple function call
print("=" * 80)
print("🧪 TEST 1: Simple Function Call")
print("=" * 80)

url = "http://localhost:11434/api/chat"

# Define a simple function
tools = [{
    "type": "function",
    "function": {
        "name": "calculate_project_cost",
        "description": "Calculate total project cost based on team size, rate, and duration",
        "parameters": {
            "type": "object",
            "properties": {
                "developers": {
                    "type": "number",
                    "description": "Number of developers"
                },
                "hourly_rate": {
                    "type": "number",
                    "description": "Hourly rate per developer in USD"
                },
                "duration_months": {
                    "type": "number",
                    "description": "Project duration in months"
                }
            },
            "required": ["developers", "hourly_rate", "duration_months"]
        }
    }
}]

messages = [{
    "role": "user",
    "content": "Calculate the cost for a project with 5 developers at $60/hour for 4 months"
}]

request_data = {
    "model": "qwen2.5-coder:32b",
    "messages": messages,
    "tools": tools,
    "stream": False
}

print(f"\n📤 Sending request to Ollama...")
print(f"Model: qwen2.5-coder:32b")
print(f"User Query: {messages[0]['content']}")
print()

try:
    response = httpx.post(url, json=request_data, timeout=60.0)
    result = response.json()

    print("📥 Response received:")
    print("-" * 80)
    print(json.dumps(result, indent=2))
    print("-" * 80)

    # Check if function was called
    if "message" in result and "tool_calls" in result["message"]:
        print("\n✅ SUCCESS: Function calling works!")
        print(f"\nTool calls:")
        for tool_call in result["message"]["tool_calls"]:
            print(f"  - Function: {tool_call['function']['name']}")
            print(f"    Arguments: {tool_call['function']['arguments']}")
    else:
        print("\n⚠️  No function call detected in response")
        if "message" in result and "content" in result["message"]:
            print(f"\nModel response: {result['message']['content']}")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("✅ Test complete")
print("=" * 80)
EOF

python3 /tmp/test_qwen_function_calling.py
```

---

### Step 3: Update LLM Service for Qwen Support

#### Modify `backend/app/services/llm_service.py`

Add Qwen-specific function calling support:

```python
async def call_with_tools_qwen(
    self,
    messages: List[Dict[str, str]],
    tools: List[Dict[str, Any]],
    model: str = "qwen2.5-coder:32b"
) -> Dict[str, Any]:
    """
    Call Qwen model with function calling support via Ollama

    Args:
        messages: Conversation messages
        tools: Function definitions in OpenAI format
        model: Qwen model name

    Returns:
        Response with tool calls
    """
    client = await self._ensure_ollama_client()

    # Qwen uses OpenAI-compatible function calling format
    request_data = {
        "model": model,
        "messages": messages,
        "tools": tools,
        "stream": False,
        "options": {
            "temperature": 0.1,  # Lower temp for more reliable function calling
            "num_ctx": 32768     # Use large context window
        }
    }

    try:
        response = await client.post(
            f"{settings.OLLAMA_BASE_URL}/api/chat",
            json=request_data,
            timeout=120.0
        )
        response.raise_for_status()
        result = response.json()

        logger.info(f"✅ Qwen function calling successful")

        # Track tool usage
        if TOOL_TRACKING_ENABLED and "message" in result:
            if "tool_calls" in result["message"]:
                # Track each tool call
                for tool_call in result["message"]["tool_calls"]:
                    function_name = tool_call["function"]["name"]
                    async with AsyncSessionLocal() as db:
                        await tool_tracker.track_tool_call(
                            db=db,
                            tool_name=function_name,
                            category=ToolCategory.LLM_FUNCTION,
                            model_used=model,
                            success=True
                        )

        return result

    except Exception as e:
        logger.error(f"❌ Qwen function calling error: {e}")
        raise
```

---

### Step 4: Update Project Estimator Workflow

#### Modify `backend/app/agents/project_estimator/workflow.py`

Replace OpenAI calls with Qwen:

```python
# At the top of the file, add:
DEFAULT_LLM_MODEL = os.getenv("PROJECT_ESTIMATOR_MODEL", "qwen2.5-coder:32b")

# In each agent node, replace:
# OLD:
# response = await self.llm_service.chat_completion(
#     messages=messages,
#     model="gpt-4-turbo"
# )

# NEW:
response = await self.llm_service.call_with_tools_qwen(
    messages=messages,
    tools=agent_tools,  # Define tools for each agent
    model=DEFAULT_LLM_MODEL
)
```

#### Example: Agent 1.1 (BRD Analyzer) with Qwen

```python
async def agent_1_1_brd_analyzer(self, state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent 1.1: BRD Analyzer
    Analyzes uploaded BRD files and extracts requirements
    Now using Qwen 2.5 Coder for function calling
    """
    logger.info("🤖 Agent 1.1 (BRD Analyzer) - Starting with Qwen 2.5 Coder")

    # Define tools for this agent
    tools = [{
        "type": "function",
        "function": {
            "name": "extract_requirements",
            "description": "Extract structured requirements from BRD content",
            "parameters": {
                "type": "object",
                "properties": {
                    "functional_requirements": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of functional requirements"
                    },
                    "non_functional_requirements": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of non-functional requirements"
                    },
                    "technical_constraints": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Technical constraints and dependencies"
                    }
                },
                "required": ["functional_requirements"]
            }
        }
    }]

    # Build messages
    messages = [
        {
            "role": "system",
            "content": """You are a Business Analyst expert at extracting requirements from BRD documents.
Analyze the provided BRD content and extract structured requirements using the extract_requirements function."""
        },
        {
            "role": "user",
            "content": f"Analyze this BRD:\n\n{state.get('brd_content', 'No BRD provided')}"
        }
    ]

    try:
        # Call Qwen with function calling
        response = await self.llm_service.call_with_tools_qwen(
            messages=messages,
            tools=tools,
            model="qwen2.5-coder:32b"
        )

        # Extract tool call results
        if "message" in response and "tool_calls" in response["message"]:
            for tool_call in response["message"]["tool_calls"]:
                if tool_call["function"]["name"] == "extract_requirements":
                    import json
                    requirements = json.loads(tool_call["function"]["arguments"])

                    state["brd_analysis"] = {
                        "functional_requirements": requirements.get("functional_requirements", []),
                        "non_functional_requirements": requirements.get("non_functional_requirements", []),
                        "technical_constraints": requirements.get("technical_constraints", []),
                        "analyzed_by": "qwen-2.5-coder-32b",
                        "confidence": "high"
                    }
                    logger.info(f"✅ Agent 1.1: Extracted {len(requirements.get('functional_requirements', []))} functional requirements")

        state["completed_agents"].append("1.1")
        return state

    except Exception as e:
        logger.error(f"❌ Agent 1.1 error: {e}")
        state["errors"].append(f"Agent 1.1 (BRD Analyzer): {str(e)}")
        return state
```

---

### Step 5: Environment Configuration

Update `.env` file:

```bash
# LLM Configuration - Open Source
PROJECT_ESTIMATOR_MODEL=qwen2.5-coder:32b
OLLAMA_BASE_URL=http://ollama:11434
DEFAULT_LLM_PROVIDER=ollama

# Fallback chain (if Qwen fails)
LLM_FALLBACK_MODELS=qwen2.5-coder:14b,deepseek-coder-v2:16b

# Function calling settings
ENABLE_FUNCTION_CALLING=true
FUNCTION_CALLING_TEMPERATURE=0.1
```

---

## 📊 Performance Comparison

### OpenAI GPT-4 Turbo vs Qwen 2.5 Coder 32B

| Metric | GPT-4 Turbo | Qwen 2.5 Coder 32B |
|--------|-------------|---------------------|
| Cost per 1M tokens | $10 (input) | **$0 (FREE)** |
| Latency (avg) | 2-5 seconds | 3-8 seconds |
| Function calling quality | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Code generation | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Context window | 128K | 128K |
| Rate limits | Yes | **No** |
| Privacy | Cloud | **Local** |

---

## 🛠️ Alternative Models

### Option 2: Hermes 3 70B

```bash
ollama pull adrienbrault/nous-hermes2pro:Q5_K_M
```

**Best for**: General-purpose workflows, great reasoning

**Function Calling Example**:
```python
model = "adrienbrault/nous-hermes2pro:Q5_K_M"
# Same API as Qwen
```

### Option 3: DeepSeek Coder V2 16B

```bash
ollama pull deepseek-coder-v2:16b
```

**Best for**: Code-heavy tasks, faster inference

**Note**: Requires prompt engineering for function calling (not native support)

### Option 4: Command R+ 104B

```bash
ollama pull command-r-plus
```

**Best for**: Enterprise workflows, multilingual support

**Function Calling**: Native support, OpenAI compatible

---

## 🔧 Troubleshooting

### Issue 1: Model not responding

```bash
# Check Ollama is running
docker-compose ps ollama

# Check model is loaded
docker-compose exec ollama ollama list

# Restart Ollama
docker-compose restart ollama
```

### Issue 2: Function calling not working

**Symptoms**: Model returns text instead of tool calls

**Solution**:
1. Ensure using Qwen 2.5 (not Qwen 2.0)
2. Check tools are in correct format
3. Lower temperature (0.1 recommended)
4. Add explicit instruction in system prompt

### Issue 3: Slow inference

**Solutions**:
1. Use smaller model (14B or 7B)
2. Enable GPU acceleration (if available)
3. Reduce context window
4. Use quantized models (Q5_K_M)

---

## 📝 Migration Checklist

- [ ] Pull Qwen 2.5 Coder model via Ollama
- [ ] Test function calling with simple example
- [ ] Add `call_with_tools_qwen()` to LLM service
- [ ] Update Agent 1.1 (BRD Analyzer) to use Qwen
- [ ] Update Agent 1.2 (Sample Analyzer) to use Qwen
- [ ] Update Agent 2 (Task Generator) to use Qwen
- [ ] Update Agent 3 (Task Validator) to use Qwen
- [ ] Update Agent 4 (BRD Generator) to use Qwen
- [ ] Update Agent 5 (Rate Assignment) to use Qwen
- [ ] Update Agent 6 (Excel Generator) to use Qwen
- [ ] Update `.env` with Qwen configuration
- [ ] Test complete workflow with Estimate One files
- [ ] Validate generated BRD and Excel outputs
- [ ] Document any quality differences vs GPT-4
- [ ] Update README with new LLM configuration

---

## 🎯 Quick Start Commands

```bash
# 1. Pull the model
docker-compose exec ollama ollama pull qwen2.5-coder:32b

# 2. Test function calling
python3 /tmp/test_qwen_function_calling.py

# 3. Update environment
echo "PROJECT_ESTIMATOR_MODEL=qwen2.5-coder:32b" >> .env

# 4. Rebuild backend
docker-compose build backend --no-cache

# 5. Restart services
docker-compose up -d backend

# 6. Run Phase 6 test
python3 /tmp/test_phase6_with_estimate_one.py
```

---

## 📚 Additional Resources

### Qwen Documentation
- Official docs: https://github.com/QwenLM/Qwen2.5-Coder
- Function calling guide: https://qwen.readthedocs.io/en/latest/framework/function_call.html
- Model card: https://huggingface.co/Qwen/Qwen2.5-Coder-32B

### Ollama Documentation
- Function calling: https://github.com/ollama/ollama/blob/main/docs/api.md#function-calling
- Model library: https://ollama.com/library

### Alternative Models
- Hermes 3: https://huggingface.co/NousResearch/Hermes-3-Llama-3.1-70B
- DeepSeek Coder: https://github.com/deepseek-ai/DeepSeek-Coder
- Command R+: https://huggingface.co/CohereForAI/c4ai-command-r-plus

---

## ✅ Success Criteria

After migration, verify:

1. **Function Calling Works**: All 6 agents successfully call their tools
2. **Quality Maintained**: Generated BRD and Excel match OpenAI quality
3. **No Rate Limits**: Can run unlimited workflows
4. **Cost Reduced**: $0 inference costs
5. **Privacy**: All processing happens locally
6. **Speed**: Acceptable latency (< 10s per agent)

---

## 🚨 Important Notes

1. **GPU Recommended**: For best performance, use GPU-enabled Docker containers
2. **RAM Requirements**: 32B model needs ~20GB RAM, 14B needs ~10GB RAM
3. **First Run Slow**: Model loading takes 30-60 seconds first time
4. **Quantization**: Use Q5_K_M or Q4_K_M for lower memory usage
5. **Context Window**: Qwen 2.5 supports up to 128K tokens (same as GPT-4 Turbo)

---

**Created By**: Claude Code Assistant
**Last Updated**: 2025-11-26
**Next Steps**: Pull Qwen model and test function calling
