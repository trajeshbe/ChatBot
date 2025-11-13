# Local Models Quick Start Guide
## Lightweight & Fast - Max 7B, Quantized GGUF

---

## Available Local Models (5 Total)

### GPU Models (vLLM) - 3 models

1. **Llama 3.1 8B** - Best quality ⭐
   - Size: ~12 GB GPU RAM (with quantization)
   - Speed: ~50-100 tokens/sec
   - Quality: Excellent
   - Use case: Production workloads

2. **Llama 3.2 3B** - Best balance ⭐
   - Size: ~6 GB GPU RAM
   - Speed: ~100-150 tokens/sec
   - Quality: Very good
   - Use case: Fast, quality responses

3. **Qwen 2.5 7B** - Multilingual
   - Size: ~12 GB GPU RAM
   - Speed: ~50-80 tokens/sec
   - Quality: Excellent (multilingual)
   - Use case: Non-English queries

### CPU Models (llama.cpp GGUF Q4_K_M) - 2 models

4. **Llama 3.2 3B Q4** - Best CPU model ⭐
   - Size: ~2 GB RAM
   - Speed: ~5-10 tokens/sec (CPU)
   - Quality: Very good
   - File: `Llama-3.2-3B-Instruct-Q4_K_M.gguf`

5. **Qwen 1.5B Q4** - Ultra-fast ⭐
   - Size: ~1 GB RAM
   - Speed: ~10-15 tokens/sec (CPU)
   - Quality: Good
   - File: `qwen2.5-1.5b-instruct-q4_k_m.gguf`

---

## Why These Models?

✅ **No 70B models** - Too heavy, max 7B for efficiency
✅ **GGUF Q4_K_M quantization** - 4x smaller, 2x faster, minimal quality loss
✅ **Proven performance** - Battle-tested models from Meta & Alibaba
✅ **Hardware friendly** - Works on modest GPUs and any CPU
✅ **Privacy first** - 100% local, no API calls

---

## Quick Setup (CPU Models)

### Option 1: Automatic Setup (Recommended)

```bash
chmod +x setup-quantized-models.sh
./setup-quantized-models.sh
```

This downloads:
- Llama 3.2 3B Q4 (~2 GB)
- Qwen 1.5B Q4 (~1 GB)

### Option 2: Manual Download

**Llama 3.2 3B Q4** (recommended):
```bash
docker run --rm -v llama_models:/models alpine sh -c "
  apk add --no-cache wget && \
  cd /models && \
  wget https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf
"
```

**Qwen 1.5B Q4** (fastest):
```bash
docker run --rm -v llama_models:/models alpine sh -c "
  apk add --no-cache wget && \
  cd /models && \
  wget https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf
"
```

### Start llama.cpp Service

```bash
# Start with default model (Llama 3.2 3B Q4)
docker compose up -d llama-cpp

# Check logs
docker compose logs llama-cpp -f
```

---

## GPU Setup (vLLM)

### Check GPU

```bash
# Check if GPU is available
docker compose exec backend python -c "
from app.utils.gpu_detector import detect_gpu
gpu = detect_gpu()
print(f'GPU: {gpu.available} ({gpu.type})')
print(f'Memory: {gpu.memory_gb:.1f} GB')
"
```

### Enable vLLM

Edit `.env`:
```bash
USE_VLLM=true
VLLM_MODEL=meta-llama/Llama-3.2-3B-Instruct  # Start with smallest
```

Uncomment vLLM in `docker-compose.yml` and start:
```bash
docker compose up -d vllm-service

# Models auto-download on first start (watch logs)
docker compose logs vllm-service -f
```

### GPU Model Selection

Based on your GPU memory:

| GPU Memory | Recommended Model |
|------------|-------------------|
| 6-8 GB | Llama 3.2 3B |
| 12-16 GB | Llama 3.1 8B or Qwen 2.5 7B |
| 24 GB+ | Llama 3.1 8B (with larger batch) |

---

## Switching Models

### Switch CPU Model

Edit `docker-compose.yml` line 104:

```yaml
# For Llama 3.2 3B:
- /models/Llama-3.2-3B-Instruct-Q4_K_M.gguf

# For Qwen 1.5B (faster):
- /models/qwen2.5-1.5b-instruct-q4_k_m.gguf
```

Restart:
```bash
docker compose restart llama-cpp
```

### Switch GPU Model

Edit `.env`:
```bash
# Options:
VLLM_MODEL=meta-llama/Llama-3.2-3B-Instruct      # Lightweight
VLLM_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct # Best quality
VLLM_MODEL=Qwen/Qwen2.5-7B-Instruct              # Multilingual
```

Restart:
```bash
docker compose restart vllm-service
```

---

## Testing

### Test CPU Model

```bash
# Direct test
curl http://localhost:8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello, who are you?",
    "max_tokens": 50
  }'
```

### Test GPU Model (if enabled)

```bash
curl http://localhost:8100/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.2-3B-Instruct",
    "prompt": "Hello, who are you?",
    "max_tokens": 50
  }'
```

### Test in UI

1. Open http://localhost:3001
2. Click "Model:" dropdown
3. Select a local model:
   - **Local GPU**: Llama 3.2 3B (GPU), Llama 3.1 8B (GPU), or Qwen 2.5 7B (GPU)
   - **Local CPU**: Llama 3.2 3B Q4 (CPU) or Qwen 1.5B Q4 (CPU)
4. Send a message
5. Check response badge shows the selected model

---

## Performance Comparison

| Model | Platform | Speed | RAM | Quality | Use Case |
|-------|----------|-------|-----|---------|----------|
| Llama 3.1 8B | GPU | ~100 tok/s | 12 GB | ⭐⭐⭐⭐⭐ | Production |
| Llama 3.2 3B | GPU | ~150 tok/s | 6 GB | ⭐⭐⭐⭐ | Fast responses |
| Qwen 2.5 7B | GPU | ~80 tok/s | 12 GB | ⭐⭐⭐⭐⭐ | Multilingual |
| Llama 3.2 3B Q4 | CPU | ~8 tok/s | 2 GB | ⭐⭐⭐⭐ | No GPU |
| Qwen 1.5B Q4 | CPU | ~12 tok/s | 1 GB | ⭐⭐⭐ | Ultra-fast |

**Speed baseline**: 8-core CPU, RTX 3080 (10GB) GPU

---

## Why Q4_K_M Quantization?

**Q4_K_M** = 4-bit quantization with K-means optimization + Mixed precision

Benefits:
- **4x smaller** file size
- **2-3x faster** inference
- **<3% quality loss** vs full precision
- **Works on CPU** without GPU

Quality comparison:
- FP16 (original): 100% quality, 12 GB
- Q8 (8-bit): 99% quality, 6 GB
- Q4_K_M (4-bit): 97% quality, 3 GB ← **Sweet spot**
- Q2 (2-bit): 85% quality, 1.5 GB

---

## Troubleshooting

### Issue: Model file not found

```bash
# Check downloaded models
docker run --rm -v llama_models:/models alpine ls -lh /models/

# Re-download if needed
./setup-quantized-models.sh
```

### Issue: llama.cpp crashes

**Cause**: Not enough RAM

**Solution**: Use smaller model (Qwen 1.5B instead of Llama 3.2 3B)

### Issue: GPU model out of memory

**Solution**: Use smaller model or enable quantization

Edit `docker-compose.yml` for vLLM:
```yaml
command:
  - --model
  - meta-llama/Llama-3.2-3B-Instruct  # Smaller model
  - --quantization
  - awq  # or gptq - enables quantization
```

### Issue: Slow CPU inference

**Expected**: CPU is 10-20x slower than GPU

**Optimize**:
1. Use Qwen 1.5B (faster than Llama 3.2 3B)
2. Reduce max_tokens in queries
3. Close other apps (more RAM = more cache)

---

## Cost Comparison

| Model | Cost per 1M tokens | Monthly (10K queries) |
|-------|-------------------|----------------------|
| GPT-4 Turbo | $30 | $300 |
| Claude 3.5 Sonnet | $15 | $150 |
| **Local GPU** | **$0** | **$0** |
| **Local CPU** | **$0** | **$0** |

Electricity cost: ~$5-10/month for GPU, <$1/month for CPU

---

## Summary

✅ **5 local models** (3 GPU + 2 CPU)
✅ **Max 7B size** - Fast and efficient
✅ **Q4_K_M quantized** - 4x smaller, 2x faster
✅ **No API costs** - 100% free
✅ **Privacy** - Data never leaves your server

**Recommended Setup**:
- **Have GPU?** → Llama 3.2 3B (GPU) for speed
- **No GPU?** → Llama 3.2 3B Q4 (CPU) for quality
- **Need speed?** → Qwen 1.5B Q4 (CPU) for fast responses

**Download & start**:
```bash
./setup-quantized-models.sh
docker compose up -d llama-cpp
```

**Test in UI**:
http://localhost:3001 → Select model from dropdown!

---

*Last updated: 2025-11-13*
