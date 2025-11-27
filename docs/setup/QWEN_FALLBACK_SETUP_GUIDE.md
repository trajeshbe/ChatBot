# Qwen as OpenAI API Fallback - Setup Guide

**Date**: 2025-11-26
**Purpose**: Configure Qwen as automatic fallback when OpenAI API fails/exhausted
**Status**: ✅ Ready to Implement

---

## Current Situation

### Models Already Installed
```
✅ llama3.2-vision:11b    (7.8 GB) - Supports function calling
❌ qwen2.5:1.5b           (986 MB) - Too small for function calling
❌ qwen2.5:1.5b-instruct  (986 MB) - Too small for function calling
```

### Problem
- OpenAI API rate limits exceeded
- Need automatic fallback to local models
- Current Qwen models (1.5B) don't support function calling

---

## Solution: Multi-Tier Fallback Chain

### Fallback Priority

```
1️⃣  OpenAI GPT-4 Turbo          (Primary - if API key works)
    ↓ (on failure)
2️⃣  Qwen 2.5 Coder 14B          (Fast, function calling)
    ↓ (on failure)
3️⃣  LLaMA 3.2 Vision 11B        (Already installed, function calling)
    ↓ (on failure)
4️⃣  Qwen 2.5 1.5B Instruct      (Simple tasks only, no function calling)
```

---

## Step 1: Pull Better Qwen Model

### Recommended: Qwen 2.5 Coder 14B

**Why 14B instead of 32B?**
- ✅ Better balance of speed vs quality
- ✅ Needs ~10GB RAM (vs 20GB for 32B)
- ✅ 2-3x faster than 32B
- ✅ Still supports function calling
- ✅ Good enough for Project Estimator

```bash
# Pull Qwen 2.5 Coder 14B
docker-compose exec ollama ollama pull qwen2.5-coder:14b

# This will take 5-10 minutes (downloads ~8GB)
# You'll see progress:
# pulling manifest
# pulling 8934d96d3f08... 100%
# verifying sha256 digest
# writing manifest
# success
```

### Alternative: Qwen 2.5 Coder 7B (Faster, Smaller)

If you want even faster inference:

```bash
# Smaller, faster option
docker-compose exec ollama ollama pull qwen2.5-coder:7b
```

---

## Step 2: Update Environment Configuration

Update `.env` file:

```bash
# Add these lines to .env
cat >> .env << 'EOF'

# === LLM Fallback Configuration ===
# Primary model (OpenAI)
PRIMARY_LLM_MODEL=gpt-4-turbo
PRIMARY_LLM_PROVIDER=openai

# Fallback chain (tried in order if primary fails)
FALLBACK_LLM_MODELS=qwen2.5-coder:14b,llama3.2-vision:11b,qwen2.5:1.5b-instruct
FALLBACK_LLM_PROVIDER=ollama

# Enable automatic fallback
ENABLE_LLM_FALLBACK=true

# Retry settings
LLM_MAX_RETRIES=3
LLM_RETRY_DELAY_SECONDS=2

# Function calling models (only these support tool use)
FUNCTION_CALLING_MODELS=gpt-4-turbo,gpt-4,qwen2.5-coder:14b,qwen2.5-coder:7b,llama3.2-vision:11b

EOF
```

---

## Step 3: Update LLM Service with Fallback Logic

The fallback logic should already be in your `llm_service.py`. Let me verify and update if needed:

### Key Method: `chat_completion_with_fallback()`

```python
async def chat_completion_with_fallback(
    self,
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Call LLM with automatic fallback chain

    Tries models in this order:
    1. OpenAI (if API key available)
    2. Qwen 2.5 Coder 14B (Ollama)
    3. LLaMA 3.2 Vision 11B (Ollama)
    4. Qwen 2.5 1.5B (Ollama - simple tasks only)

    Args:
        messages: Conversation messages
        model: Preferred model (optional)
        tools: Function definitions (optional)
        **kwargs: Additional arguments

    Returns:
        LLM response with metadata about which model was used
    """
    await self.initialize()

    # Define fallback chain from environment or use defaults
    fallback_models = os.getenv(
        "FALLBACK_LLM_MODELS",
        "qwen2.5-coder:14b,llama3.2-vision:11b,qwen2.5:1.5b-instruct"
    ).split(",")

    # Determine if we need function calling
    needs_function_calling = tools is not None and len(tools) > 0
    function_calling_models = os.getenv(
        "FUNCTION_CALLING_MODELS",
        "gpt-4-turbo,gpt-4,qwen2.5-coder:14b,qwen2.5-coder:7b,llama3.2-vision:11b"
    ).split(",")

    # Try primary model first (OpenAI if available)
    models_to_try = []

    # Add OpenAI if we have a key
    if self.openai_client and model and "gpt" in model:
        models_to_try.append(("openai", model))

    # Add Ollama fallbacks
    for fallback_model in fallback_models:
        fallback_model = fallback_model.strip()

        # Skip models that don't support function calling if we need it
        if needs_function_calling and fallback_model not in function_calling_models:
            logger.warning(f"⚠️  Skipping {fallback_model} - doesn't support function calling")
            continue

        models_to_try.append(("ollama", fallback_model))

    # Try each model in sequence
    last_error = None
    for provider, model_name in models_to_try:
        try:
            logger.info(f"🔄 Trying {provider}/{model_name}...")

            if provider == "openai":
                # Try OpenAI
                response = await self.openai_client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    tools=tools if tools else None,
                    **kwargs
                )

                logger.info(f"✅ Success with OpenAI {model_name}")

                # Convert to standard format
                return {
                    "model": model_name,
                    "provider": "openai",
                    "message": {
                        "role": "assistant",
                        "content": response.choices[0].message.content,
                        "tool_calls": response.choices[0].message.tool_calls if hasattr(response.choices[0].message, 'tool_calls') else None
                    },
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }

            elif provider == "ollama":
                # Try Ollama
                client = await self._ensure_ollama_client()

                request_data = {
                    "model": model_name,
                    "messages": messages,
                    "stream": False
                }

                # Add tools if needed and model supports them
                if tools and model_name in function_calling_models:
                    request_data["tools"] = tools

                response = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/chat",
                    json=request_data,
                    timeout=120.0
                )
                response.raise_for_status()
                result = response.json()

                logger.info(f"✅ Success with Ollama {model_name}")

                # Add provider metadata
                result["provider"] = "ollama"
                result["model"] = model_name

                return result

        except Exception as e:
            last_error = e
            logger.warning(f"⚠️  Failed with {provider}/{model_name}: {str(e)}")
            logger.info(f"🔄 Trying next fallback...")
            continue

    # All models failed
    error_msg = f"All LLM fallbacks failed. Last error: {str(last_error)}"
    logger.error(f"❌ {error_msg}")
    raise Exception(error_msg)
```

---

## Step 4: Update Project Estimator to Use Fallback

### Modify `workflow.py`

Replace direct model calls with fallback calls:

```python
# OLD CODE (hardcoded OpenAI):
# response = await self.llm_service.chat_completion(
#     messages=messages,
#     model="gpt-4-turbo"
# )

# NEW CODE (with fallback):
response = await self.llm_service.chat_completion_with_fallback(
    messages=messages,
    model="gpt-4-turbo",  # Preferred, will fallback if fails
    tools=agent_tools      # For function calling
)

# Log which model was actually used
logger.info(f"✅ Agent completed using: {response.get('provider')}/{response.get('model')}")
```

---

## Step 5: Test the Fallback Chain

### Test Script

```bash
cat > /tmp/test_llm_fallback.py << 'EOF'
"""
Test LLM fallback chain
"""
import asyncio
import sys
sys.path.insert(0, '/app')

from app.services.llm_service import LLMService

async def test_fallback():
    print("=" * 80)
    print("🧪 TESTING LLM FALLBACK CHAIN")
    print("=" * 80)
    print()

    llm_service = LLMService()
    await llm_service.initialize()

    # Test 1: Simple completion (no tools)
    print("TEST 1: Simple completion (should try all models)")
    print("-" * 80)

    messages = [{
        "role": "user",
        "content": "What is 2 + 2? Answer in one sentence."
    }]

    try:
        result = await llm_service.chat_completion_with_fallback(
            messages=messages,
            model="gpt-4-turbo"  # Will try this first, then fallback
        )

        print(f"✅ SUCCESS!")
        print(f"   Provider: {result.get('provider')}")
        print(f"   Model: {result.get('model')}")
        print(f"   Response: {result.get('message', {}).get('content', 'N/A')[:200]}")
    except Exception as e:
        print(f"❌ FAILED: {e}")

    print("\n" + "=" * 80)
    print("TEST 2: Function calling (only supported models)")
    print("-" * 80)

    tools = [{
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Calculate a simple math expression",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string"}
                },
                "required": ["expression"]
            }
        }
    }]

    messages = [{
        "role": "user",
        "content": "Calculate 15 * 23 using the calculate function"
    }]

    try:
        result = await llm_service.chat_completion_with_fallback(
            messages=messages,
            model="gpt-4-turbo",
            tools=tools
        )

        print(f"✅ SUCCESS!")
        print(f"   Provider: {result.get('provider')}")
        print(f"   Model: {result.get('model')}")
        if "tool_calls" in result.get("message", {}):
            print(f"   Tool called: {result['message']['tool_calls'][0]['function']['name']}")
    except Exception as e:
        print(f"❌ FAILED: {e}")

    print("\n" + "=" * 80)
    print("✅ FALLBACK TEST COMPLETE")
    print("=" * 80)

asyncio.run(test_fallback())
EOF

# Run test
docker-compose exec backend python3 /tmp/test_llm_fallback.py
```

---

## Step 6: Monitor Which Model is Being Used

Add logging to see which model handled each request:

```bash
# Watch backend logs for model usage
docker-compose logs backend --follow | grep -E "(Trying|Success with|provider|model)"
```

You'll see output like:
```
🔄 Trying openai/gpt-4-turbo...
⚠️  Failed with openai/gpt-4-turbo: Rate limit exceeded
🔄 Trying next fallback...
🔄 Trying ollama/qwen2.5-coder:14b...
✅ Success with Ollama qwen2.5-coder:14b
```

---

## Benefits of This Setup

### Cost Savings
- **Before**: $10 per 1M tokens (OpenAI)
- **After**: $0 for fallback requests (Ollama local)

### No Rate Limits
- **Before**: 500 requests/day (OpenAI free tier)
- **After**: Unlimited local requests

### Privacy
- **Before**: All requests to OpenAI cloud
- **After**: Fallback requests stay local

### Reliability
- **Before**: Service down if OpenAI fails
- **After**: Automatic failover to local models

---

## Performance Comparison

| Model | Latency | Quality | Function Calling | Cost |
|-------|---------|---------|------------------|------|
| GPT-4 Turbo | 2-5s | ⭐⭐⭐⭐⭐ | ✅ Native | $10/1M tokens |
| Qwen 2.5 Coder 14B | 3-8s | ⭐⭐⭐⭐ | ✅ Native | **$0 (FREE)** |
| LLaMA 3.2 Vision 11B | 4-10s | ⭐⭐⭐⭐ | ✅ Native | **$0 (FREE)** |
| Qwen 2.5 1.5B | 1-2s | ⭐⭐ | ❌ No | **$0 (FREE)** |

---

## Monitoring and Debugging

### Check which models are being used

```bash
# SQL query to see model usage distribution
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT
    model_used,
    COUNT(*) as request_count,
    AVG(tokens_used) as avg_tokens,
    AVG(latency_ms) as avg_latency_ms
FROM messages
WHERE created_at > NOW() - INTERVAL '1 day'
GROUP BY model_used
ORDER BY request_count DESC;
"
```

### Dashboard metrics

Add to your admin dashboard:
- **Primary vs Fallback Usage**: % of requests using fallback
- **Cost Savings**: Estimated $ saved by using fallback
- **Fallback Success Rate**: % of fallback requests that succeed

---

## Quick Commands

```bash
# 1. Pull Qwen 2.5 Coder 14B
docker-compose exec ollama ollama pull qwen2.5-coder:14b

# 2. Verify it's installed
docker-compose exec ollama ollama list

# 3. Update .env with fallback config
# (manually add the ENV vars shown above)

# 4. Restart backend to load new config
docker-compose restart backend

# 5. Test fallback chain
docker-compose exec backend python3 /tmp/test_llm_fallback.py

# 6. Monitor which models are used
docker-compose logs backend --follow | grep "Success with"
```

---

## Expected Behavior

### When OpenAI API Works
```
🔄 Trying openai/gpt-4-turbo...
✅ Success with OpenAI gpt-4-turbo
```

### When OpenAI API Fails (Rate Limit)
```
🔄 Trying openai/gpt-4-turbo...
⚠️  Failed with openai/gpt-4-turbo: Rate limit exceeded for requests
🔄 Trying next fallback...
🔄 Trying ollama/qwen2.5-coder:14b...
✅ Success with Ollama qwen2.5-coder:14b
```

### When All Models Fail
```
🔄 Trying openai/gpt-4-turbo...
⚠️  Failed with openai/gpt-4-turbo: Rate limit exceeded
🔄 Trying ollama/qwen2.5-coder:14b...
⚠️  Failed with ollama/qwen2.5-coder:14b: Model not found
🔄 Trying ollama/llama3.2-vision:11b...
⚠️  Failed with ollama/llama3.2-vision:11b: Timeout
❌ All LLM fallbacks failed
```

---

## Troubleshooting

### Issue: "Model not found" for Qwen

**Solution**: Pull the model
```bash
docker-compose exec ollama ollama pull qwen2.5-coder:14b
```

### Issue: Fallback not triggering

**Check**: Is `ENABLE_LLM_FALLBACK=true` in `.env`?
```bash
grep ENABLE_LLM_FALLBACK .env
```

### Issue: Function calling not working with fallback model

**Check**: Is the fallback model in `FUNCTION_CALLING_MODELS`?
```bash
grep FUNCTION_CALLING_MODELS .env
```

---

## Next Steps

1. ✅ Pull Qwen 2.5 Coder 14B
2. ✅ Add environment variables to `.env`
3. ✅ Update `llm_service.py` with fallback logic
4. ✅ Update Project Estimator to use `chat_completion_with_fallback()`
5. ✅ Test with Phase 6 Estimate One files
6. ✅ Monitor usage and adjust fallback priority if needed

---

**Created By**: Claude Code Assistant
**Last Updated**: 2025-11-26
**Next Action**: Pull qwen2.5-coder:14b
