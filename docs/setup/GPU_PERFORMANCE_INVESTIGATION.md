# GPU Performance Investigation & Qwen Model Recommendations

**Date**: 2025-11-24
**Status**: IN PROGRESS
**Hardware**: NVIDIA RTX 5060 Laptop (8GB VRAM)

---

## Executive Summary

### Issues Identified:
1. **Slow Response Time**: 103 seconds despite GPU being used
2. **Missing Model Name**: `model` and `model_used` fields showing `null` in responses
3. **GPU Memory**: Successfully reduced from 98% to 38% by removing heavy models

### Actions Taken:
- ✅ Removed llama3.1:8b (4.9GB) and llama3.2:3b (2.0GB)
- ✅ Kept only qwen2.5:1.5b (986MB) for GPU inference
- ⏳ Investigating slow response times
- ⏳ Fixing missing model name display

---

## Issue #1: Slow Response Time (103 seconds)

### Problem:
Even with only qwen2.5:1.5b loaded (1.9GB on GPU), responses taking 1m43s (103 seconds).

### Expected Performance:
- qwen2.5:1.5b should generate at ~20-30 tokens/sec on RTX 5060
- Expected response time: 10-20 seconds for typical queries

### Investigation:
```bash
# Test query took 103 seconds:
time: 1m43.689s
model: null
tokens: 0
latency_ms: 103303.04956436157
```

### Possible Causes:
1. **Agent Orchestration Overhead**: EnhancedRAGAgent may be running multiple tools unnecessarily
2. **Token Generation Not Happening**: `tokens: 0` suggests no actual LLM generation occurred
3. **Fallback Chain Issues**: Multiple retries or fallback attempts
4. **Network/Connection Issues**: httpx client issues with Ollama

### Next Steps:
- [ ] Check backend logs for EnhancedRAGAgent execution
- [ ] Verify Ollama is receiving requests
- [ ] Test direct Ollama API call (bypass agent)
- [ ] Monitor GPU utilization during query

---

## Issue #2: Missing Model Name Display

### Problem:
User reported: "the response used to show which model generated it, it's now missing now"

### Root Cause Analysis:

**Location 1: LLM Service** (`backend/app/services/llm_service.py:297-302`)
```python
# ✅ CORRECTLY returns model information
return {
    "content": content,
    "model": "ollama",
    "model_name": f"Ollama ({ollama_model})",
    "tokens": tokens
}
```

**Location 2: Query Endpoint** (`backend/app/main.py:458-606`)
```python
# ❌ DOES NOT expose model field properly
# At line 606, it just returns result from enhanced_rag_agent
# The agent's 'model' field is not being exposed at top level
return result  # Missing: result['model_used'] = result.get('model', 'unknown')
```

### Fix Required:
Add model information to top-level response in `main.py` query endpoint around line 580-604:

```python
# ADD THIS:
result['model'] = result.get('model', 'unknown')
result['model_used'] = result.get('model_name', result.get('model', 'unknown'))
```

---

## Qwen GPU Model Recommendations

### Currently Installed:
- ✅ `qwen2.5:1.5b` (986MB) - Quantized q4_K_M
- ✅ `qwen2.5:1.5b-instruct-q4_K_M` (986MB) - Same model, instruct-tuned

### Recommended Qwen Models for 8GB RTX 5060:

#### 1. qwen2.5:0.5b (FASTEST - 500MB)
```bash
docker-compose exec ollama ollama pull qwen2.5:0.5b
```
**Specs:**
- Parameters: 500M
- VRAM: ~600MB
- Speed: ~40-60 tokens/sec on RTX 5060
- Quality: Good for simple queries, chat

**Best For:**
- Ultra-fast responses
- Simple Q&A
- Chatbot interactions
- Testing

---

#### 2. qwen2.5:1.5b-instruct-q4_K_M (BALANCED - 986MB) ✅ CURRENT
```bash
docker-compose exec ollama ollama pull qwen2.5:1.5b-instruct-q4_K_M
```
**Specs:**
- Parameters: 1.5B
- VRAM: ~1.9GB (with KV cache)
- Speed: ~25-35 tokens/sec on RTX 5060
- Quality: Very good for most tasks

**Best For:**
- General RAG queries
- Document Q&A
- Good quality/speed balance
- **RECOMMENDED DEFAULT**

---

#### 3. qwen2.5:3b-instruct-q4_K_M (HIGH QUALITY - 1.9GB)
```bash
docker-compose exec ollama ollama pull qwen2.5:3b-instruct-q4_K_M
```
**Specs:**
- Parameters: 3B
- VRAM: ~2.9GB (with KV cache)
- Speed: ~15-25 tokens/sec on RTX 5060
- Quality: Excellent reasoning, better complex queries

**Best For:**
- Complex document analysis
- Multi-step reasoning
- Higher quality responses
- When speed is less critical

---

#### 4. qwen2.5:7b-instruct-q4_K_M (MAX QUALITY - 4.4GB)
```bash
docker-compose exec ollama ollama pull qwen2.5:7b-instruct-q4_K_M
```
**Specs:**
- Parameters: 7B
- VRAM: ~5.5GB (with KV cache)
- Speed: ~10-15 tokens/sec on RTX 5060
- Quality: Best quality in Qwen 2.5 series

**Best For:**
- Maximum quality responses
- Complex analysis
- Production deployments (if speed acceptable)
- Fits comfortably in 8GB VRAM

**WARNING**: Leave ~2.5GB free for:
- KV cache (context window)
- System overhead
- Embeddings model

---

### ❌ NOT Recommended for 8GB VRAM:

- `qwen2.5:14b` - Requires ~10GB VRAM
- `qwen2.5:32b` - Requires ~20GB VRAM
- `qwen2.5:72b` - Requires ~40GB VRAM
- Non-quantized models (F16/F32) - 2-4x more VRAM

---

## Performance Comparison Table

| Model | VRAM | Speed (tok/s) | Quality | Response Time* | Recommended Use |
|-------|------|--------------|---------|----------------|-----------------|
| qwen2.5:0.5b | 600MB | 40-60 | ⭐⭐⭐ | 5-10s | Fast chat, testing |
| qwen2.5:1.5b-q4 | 1.9GB | 25-35 | ⭐⭐⭐⭐ | 10-15s | **DEFAULT** |
| qwen2.5:3b-q4 | 2.9GB | 15-25 | ⭐⭐⭐⭐⭐ | 15-20s | Complex queries |
| qwen2.5:7b-q4 | 5.5GB | 10-15 | ⭐⭐⭐⭐⭐ | 20-30s | Production quality |

*For 200-token responses

---

## Recommended Setup

### Option A: Single Model (Simple)
```bash
# Keep only qwen2.5:1.5b-instruct-q4_K_M
docker-compose exec ollama ollama pull qwen2.5:1.5b-instruct-q4_K_M
```
✅ Best balance of speed and quality
✅ Low VRAM usage (1.9GB)
✅ Fast responses (10-15s expected)

### Option B: Two Models (Flexibility)
```bash
# Fast model for simple queries
docker-compose exec ollama ollama pull qwen2.5:0.5b

# Quality model for complex analysis
docker-compose exec ollama ollama pull qwen2.5:3b-instruct-q4_K_M
```
✅ Total VRAM: ~3.5GB when both loaded
✅ Can switch based on query complexity
✅ Still leaves room for embeddings

### Option C: Three Models (Maximum Flexibility)
```bash
docker-compose exec ollama ollama pull qwen2.5:0.5b          # Fast: 600MB
docker-compose exec ollama ollama pull qwen2.5:1.5b-instruct-q4_K_M  # Default: 1.9GB
docker-compose exec ollama ollama pull qwen2.5:7b-instruct-q4_K_M    # Quality: 5.5GB
```
⚠️ Load only ONE at a time (Ollama auto-manages)
✅ Maximum flexibility
✅ Can switch via model_id parameter

---

## Configuration Changes Required

### 1. Update `.env` or Backend Config
```bash
# Current (change this):
OLLAMA_MODEL=llama3.2:3b

# Recommended:
OLLAMA_MODEL=qwen2.5:1.5b-instruct-q4_K_M
```

### 2. Verify Ollama GPU Settings
```bash
# Check current model
docker-compose exec ollama ollama ps

# Should show 100% GPU allocation
NAME                            ID              SIZE      PROCESSOR
qwen2.5:1.5b-instruct-q4_K_M    65ec06548149    1.9 GB    100% GPU
```

---

## Testing Plan

### Test 1: Direct Ollama API (Baseline)
```bash
# Measure raw Ollama performance
time curl -X POST http://localhost:11434/api/generate \
  -d '{
    "model": "qwen2.5:1.5b-instruct-q4_K_M",
    "prompt": "What is machine learning?",
    "stream": false
  }'
```
**Expected**: 5-15 seconds

### Test 2: Backend LLM Service
```bash
# Test LLM service directly (bypass RAG)
time curl -X POST http://localhost:8000/api/v1/query \
  -F "query=What is 2+2?" \
  -F "session_id=test" \
  -F "model_id=ollama/qwen2.5:1.5b-instruct-q4_K_M"
```
**Expected**: 10-20 seconds

### Test 3: Full RAG Pipeline
```bash
# Test complete pipeline with documents
time curl -X POST http://localhost:8000/api/v1/query \
  -F "query=Summarize the uploaded document" \
  -F "session_id=test" \
  -F "use_cache=false"
```
**Expected**: 15-30 seconds (includes retrieval)

---

## Next Actions

### Immediate (Today):
1. ✅ Remove llama models (DONE)
2. ⏳ Fix missing model name in responses
3. ⏳ Investigate slow response time (103s → should be 10-15s)
4. ⏳ Update OLLAMA_MODEL in config

### Short-term (This Week):
1. Test direct Ollama API performance
2. Profile EnhancedRAGAgent execution
3. Add query classification to skip unnecessary tools
4. Implement model switching based on query complexity

### Medium-term (Next Week):
1. Add frontend model selector for Qwen variants
2. Benchmark all recommended Qwen models
3. Create auto-model-selection logic
4. Document optimal model for each use case

---

## Questions for User

1. **Which model would you prefer as default?**
   - Fast (0.5b) - 5-10s responses
   - Balanced (1.5b) - 10-15s responses ← RECOMMENDED
   - Quality (3b) - 15-20s responses
   - Max Quality (7b) - 20-30s responses

2. **Should we implement auto model switching?**
   - Simple queries → qwen2.5:0.5b
   - Normal queries → qwen2.5:1.5b
   - Complex queries → qwen2.5:3b

3. **Is 10-15s response time acceptable for RAG queries?**
   - If yes → proceed with qwen2.5:1.5b
   - If no → use qwen2.5:0.5b for faster responses

---

## Status

- [x] Llama models removed
- [x] GPU memory freed (98% → 38%)
- [x] Qwen 2.5 models recommended
- [ ] Model name display fix pending
- [ ] Response time investigation ongoing
- [ ] User preference for default model needed

**Next Update**: After fixing model display and investigating 103s response time

---

**Updated**: 2025-11-24 08:30 UTC
