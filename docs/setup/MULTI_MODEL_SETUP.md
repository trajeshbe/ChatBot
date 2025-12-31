# Multi-Model LLM Setup Guide
## Intelligent GPU/CPU Detection with Model Selector UI

---

## Overview

This guide shows you how to set up the **enhanced multi-model system** with:

✅ **Automatic GPU/CPU detection**
✅ **Multiple LLM providers**: OpenAI, Claude, Local GPU (vLLM), Local CPU (llama.cpp)
✅ **UI model selector dropdown** with grouping
✅ **11 pre-configured models** (6 proprietary + 5 local, max 7B)
✅ **GGUF Q4 quantization** for CPU models (4x smaller, 2x faster)
✅ **Intelligent fallback** based on hardware

---

## What's Been Added

### Backend Components

1. **`backend/app/utils/gpu_detector.py`**
   - Detects NVIDIA GPUs (nvidia-smi)
   - Detects AMD GPUs (rocm-smi)
   - Falls back to CPU if no GPU
   - Recommends optimal backend

2. **`backend/app/models/model_registry.py`**
   - Registry of 11 models (6 proprietary + 5 local):
     - **Proprietary**: GPT-4 Turbo, GPT-4, GPT-3.5 Turbo, Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku
     - **Local GPU** (max 7B): Llama 3.1 8B, Llama 3.2 3B, Qwen 2.5 7B
     - **Local CPU** (GGUF Q4 quantized): Llama 3.2 3B Q4, Qwen 1.5B Q4
   - Tracks cost, context length, GPU requirements
   - Auto-detects model availability
   - Optimized with quantization for speed

3. **`backend/app/services/llm_service_enhanced.py`**
   - Unified API across all providers
   - Model selection support
   - Cost tracking
   - Automatic provider routing

4. **`backend/app/api/routes/models.py`**
   - `GET /api/v1/models/` - List all models
   - `GET /api/v1/models/available` - Get available models
   - `POST /api/v1/models/select` - Set default model
   - `GET /api/v1/models/gpu-info` - GPU hardware info

5. **`backend/app/core/config.py`**
   - Added `ANTHROPIC_API_KEY` support

6. **`backend/requirements.txt`**
   - Added `anthropic==0.39.0` for Claude support

### Frontend Components

1. **`frontend/src/components/ModelSelector.tsx`**
   - Beautiful dropdown with model grouping
   - Shows proprietary/GPU/CPU models separately
   - Displays cost, context length, recommendations
   - Real-time availability checking

2. **`frontend/src/components/ChatInterfaceEnhanced.tsx`**
   - Integrated model selector in header
   - Shows which model generated each response
   - Passes model_id to backend API

---

## Integration Steps

### Step 1: Update Backend Dependencies

```bash
cd backend
pip install anthropic==0.39.0
```

Or rebuild the Docker container:
```bash
docker compose build backend
```

### Step 2: Configure API Keys

Edit `.env` and add your API keys:

```bash
# OpenAI (existing)
OPENAI_API_KEY=sk-proj-your-key-here

# Anthropic/Claude (NEW)
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional: Keep these as-is
USE_VLLM=false  # Will auto-enable if GPU detected
```

### Step 3: Integrate Enhanced LLM Service

Option A: Replace existing service (recommended):

```bash
# Backup old service
mv backend/app/services/llm_service.py backend/app/services/llm_service_old.py

# Rename enhanced to main
mv backend/app/services/llm_service_enhanced.py backend/app/services/llm_service.py

# Update import in llm_service.py
# Change: llm_service = EnhancedLLMService()
# To:     llm_service = LLMService()
#
# And rename the class from EnhancedLLMService to LLMService
```

Option B: Use alongside existing service:

Update `backend/app/main.py` to import:
```python
from app.services.llm_service_enhanced import llm_service
```

### Step 4: Add Models API Router

Edit `backend/app/main.py` and add the router:

```python
# Add this import at the top
from app.api.routes import models

# Add this after other router includes (around line 222)
app.include_router(models.router)
```

### Step 5: Update Query Endpoint to Accept Model ID

Edit `backend/app/main.py`, find the `/api/v1/query` endpoint and update it:

```python
@app.post("/api/v1/query")
async def query_endpoint(
    query: str = Form(...),
    session_id: Optional[str] = Form(None),
    use_cache: bool = Form(True),
    model_id: Optional[str] = Form(None),  # NEW: Accept model selection
    db: AsyncSession = Depends(get_db)
):
    """Query the RAG system"""
    try:
        result = await rag_service.query(
            query_text=query,
            conversation_history=None,
            use_cache=use_cache,
            model_id=model_id,  # NEW: Pass to RAG service
            db=db
        )

        return result

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 6: Update RAG Service to Use Model Selection

Edit `backend/app/services/rag_service.py` and update the `query()` method:

```python
async def query(
    self,
    query_text: str,
    conversation_history: Optional[List[Dict]] = None,
    use_cache: bool = True,
    model_id: Optional[str] = None,  # NEW parameter
    db: AsyncSession = None
) -> Dict:
    # ... existing code ...

    # When calling llm_service.generate(), pass model_id:
    response = await llm_service.generate(
        prompt=final_prompt,
        messages=messages,
        model_id=model_id  # NEW: Pass model selection
    )
```

### Step 7: Update Frontend Component

Replace the ChatInterface import in `frontend/src/pages/index.tsx`:

```typescript
// Change from:
import ChatInterface from '@/components/ChatInterface'

// To:
import ChatInterface from '@/components/ChatInterfaceEnhanced'
```

Or simply replace the content of `ChatInterface.tsx` with `ChatInterfaceEnhanced.tsx`.

### Step 8: Restart Services

```bash
# Restart backend
docker compose restart backend

# Frontend auto-reloads in dev mode
# Or restart if needed:
docker compose restart frontend
```

---

## Testing the Setup

### Test 1: Check GPU Detection

```bash
curl http://localhost:8000/api/v1/models/gpu-info
```

Expected output:
```json
{
  "available": true/false,
  "type": "nvidia" or "cpu",
  "count": 1,
  "memory_gb": 16.0,
  "recommended_backend": "vllm" or "llama.cpp"
}
```

### Test 2: List Available Models

```bash
curl http://localhost:8000/api/v1/models/ | jq
```

Should show all models grouped by type with availability status.

### Test 3: UI Model Selector

1. Open http://localhost:3001
2. You should see a "Model:" dropdown in the header
3. Click it to see all available models grouped:
   - ☁️ **Proprietary API** (OpenAI, Claude)
   - ⚡ **Local GPU** (only if GPU available)
   - 💻 **Local CPU** (always available)

### Test 4: Query with Different Models

Try sending a message with different models selected:

1. Select "GPT-4 Turbo" → Send "Hello" → Response should show "GPT-4 Turbo" badge
2. Select "Claude 3.5 Sonnet" → Send "Hello" → Response should show "Claude 3.5 Sonnet"
3. Select "TinyLlama 1.1B (CPU)" → Send "Hello" → Response from local model

---

## Model Availability Matrix

| Model | Type | Requires | Available When |
|-------|------|----------|----------------|
| GPT-4 Turbo | ☁️ Proprietary | OpenAI API Key | Always (if key set) |
| GPT-4 | ☁️ Proprietary | OpenAI API Key | Always (if key set) |
| GPT-3.5 Turbo | ☁️ Proprietary | OpenAI API Key | Always (if key set) |
| Claude 3.5 Sonnet | ☁️ Proprietary | Anthropic API Key | Always (if key set) |
| Claude 3 Opus | ☁️ Proprietary | Anthropic API Key | Always (if key set) |
| Claude 3 Haiku | ☁️ Proprietary | Anthropic API Key | Always (if key set) |
| Llama 3.1 8B | ⚡ Local GPU | 12+ GB GPU | GPU with 12GB+ VRAM |
| Llama 3.2 3B | ⚡ Local GPU | 6+ GB GPU | GPU with 6GB+ VRAM |
| Qwen 2.5 7B | ⚡ Local GPU | 12+ GB GPU | GPU with 12GB+ VRAM |
| Llama 3.2 3B Q4 | 💻 Local CPU | ~2GB RAM | Always |
| Qwen 1.5B Q4 | 💻 Local CPU | ~1GB RAM | Always |

**Note**: Local models limited to max 7B for efficiency. CPU models use GGUF Q4_K_M quantization for 4x compression with minimal quality loss.

---

## Downloading Local Models

### For GPU Models (vLLM)

vLLM automatically downloads models from HuggingFace on first use. Just ensure:

1. GPU is available
2. `USE_VLLM=true` in .env
3. vLLM service is running

```bash
# Enable vLLM
echo "USE_VLLM=true" >> .env

# Start vLLM (requires GPU)
docker compose up -d vllm-service

# Models auto-download on first request
```

### For CPU Models (llama.cpp)

Download GGUF models manually:

**Llama 3.2 3B (CPU)** - Recommended for CPU:
```bash
docker run --rm -v llama_models:/models alpine sh -c "
  apk add --no-cache wget && \
  cd /models && \
  wget https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf
"
```

**Qwen 1.5B (CPU)** - Smallest, fastest:
```bash
docker run --rm -v llama_models:/models alpine sh -c "
  apk add --no-cache wget && \
  cd /models && \
  wget https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf
"
```

**TinyLlama 1.1B (CPU)** - Already configured:
```bash
# Use the existing setup script
./setup-local-llm.sh
```

Then update `docker-compose.yml` to add multiple llama.cpp instances or switch models.

---

## Enabling vLLM with GPU Auto-Detection

### Update docker-compose.yml

Find the vLLM section (currently commented out) and update it:

```yaml
  vllm-service:
    image: vllm/vllm-openai:latest
    container_name: rag-vllm
    environment:
      HUGGING_FACE_HUB_TOKEN: ${HUGGING_FACE_HUB_TOKEN:-}
    ports:
      - "8100:8000"
    volumes:
      - vllm_cache:/root/.cache/huggingface
    command:
      - --model
      - ${VLLM_MODEL:-meta-llama/Llama-3.2-3B-Instruct}  # Default to smallest
      - --dtype
      - auto
      - --max-model-len
      - "4096"
      - --gpu-memory-utilization
      - "0.9"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    networks:
      - rag-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 120s  # Models take time to load
```

### Start vLLM (GPU required)

```bash
# Set model (optional, defaults to Llama 3.2 3B)
echo "VLLM_MODEL=meta-llama/Llama-3.2-3B-Instruct" >> .env

# Enable vLLM
echo "USE_VLLM=true" >> .env

# Start service
docker compose up -d vllm-service

# Watch logs (model downloads on first start)
docker compose logs vllm-service -f
```

First start will download the model (~6GB for Llama 3.2 3B). Subsequent starts are fast.

---

## Model Selection Logic

The backend uses this priority:

1. **User selects model in UI** → Use that model
2. **No selection** → Use default model
3. **Default model selection**:
   - If OpenAI API key: GPT-4 Turbo
   - Else if Claude API key: Claude 3.5 Sonnet
   - Else if GPU available: Llama 3.1 8B (GPU)
   - Else: Llama 3.2 3B (CPU)
   - Fallback: TinyLlama (CPU)

---

## Cost Tracking

The system tracks costs automatically:

```json
{
  "answer": "...",
  "model": "gpt-4-turbo",
  "model_name": "GPT-4 Turbo",
  "tokens": 1523,
  "cost": 0.04569,  // $0.03 per 1K tokens
  "latency_ms": 1247
}
```

Local models always return `cost: 0.0`.

---

## UI Features

### Model Selector Dropdown

- **Grouped by type**: Proprietary / Local GPU / Local CPU
- **Visual indicators**:
  - ☁️ Cloud icon for proprietary
  - ⚡ Lightning for GPU
  - 💻 CPU icon for CPU models
- **Badges**: "Recommended", "Proprietary", "GPU", "CPU"
- **Details shown**:
  - Model name and description
  - Cost per 1K tokens
  - Context length
  - GPU requirements

### Chat Interface

- **Model badge** on assistant responses showing which model answered
- **Message counter** in header
- **Responsive design** works on mobile

---

## Troubleshooting

### Issue: "Anthropic client not initialized"

**Solution**: Add `ANTHROPIC_API_KEY` to .env and restart backend

### Issue: GPU models not showing

**Solution**: Check GPU detection:
```bash
curl http://localhost:8000/api/v1/models/gpu-info
```

If GPU not detected but you have one:
```bash
# Check nvidia-smi works
docker compose exec backend nvidia-smi

# Check Docker GPU support
docker info | grep -i gpu
```

### Issue: vLLM fails to start

**Common causes**:
- Not enough GPU memory
- Model too large for GPU
- CUDA version mismatch

**Solution**: Use smaller model:
```bash
echo "VLLM_MODEL=meta-llama/Llama-3.2-3B-Instruct" >> .env
docker compose restart vllm-service
```

### Issue: Model selector shows no models

**Check**:
1. Backend running: `curl http://localhost:8000/health`
2. Models endpoint: `curl http://localhost:8000/api/v1/models/`
3. Browser console for errors

---

## Advanced Configuration

### Add Custom Model

Edit `backend/app/models/model_registry.py` and add to `_initialize_models()`:

```python
self.register(ModelInfo(
    id="my-custom-model",
    name="My Custom Model",
    provider=ModelProvider.VLLM,  # or LLAMA_CPP
    model_type=ModelType.LOCAL_GPU,
    model_path="username/model-name",
    context_length=4096,
    cost_per_1k_tokens=0.0,
    requires_gpu=True,
    min_gpu_memory_gb=8,
    description="My custom model description",
    recommended=False
))
```

Restart backend and it will appear in the UI!

### Change Default Model

Via API:
```bash
curl -X POST http://localhost:8000/api/v1/models/select \
  -H "Content-Type: application/json" \
  -d '{"model_id": "claude-3.5-sonnet"}'
```

Or in code (`backend/app/services/llm_service_enhanced.py`):
```python
# Edit priority_models list in _set_default_model()
priority_models = [
    "claude-3.5-sonnet",  # Try Claude first
    "gpt-4-turbo",
    # ...
]
```

---

## Performance Comparison

| Model | Speed (tokens/sec) | Quality | Cost | Privacy |
|-------|-------------------|---------|------|---------|
| GPT-4 Turbo | ~50 | Excellent | $$$ | Low (API) |
| Claude 3.5 Sonnet | ~45 | Excellent | $$ | Low (API) |
| Llama 3.1 8B (GPU) | ~100 | Very Good | Free | 100% |
| Llama 3.2 3B (CPU) | ~5-10 | Good | Free | 100% |
| Qwen 1.5B (CPU) | ~10-15 | Good | Free | 100% |
| TinyLlama (CPU) | ~15-20 | Basic | Free | 100% |

---

## Summary

You now have:

✅ **12 models** across 3 providers
✅ **Automatic GPU detection** and intelligent defaults
✅ **Beautiful UI** with model selector dropdown
✅ **Cost tracking** for API models
✅ **Fallback chain** for reliability
✅ **100% local option** for privacy

**Next Steps**:
1. Add your API keys to `.env`
2. Follow integration steps above
3. Test in UI at http://localhost:3001
4. Download local models if desired
5. Enable vLLM if you have GPU

Enjoy your multi-model RAG chatbot! 🚀
