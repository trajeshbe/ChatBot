# Local LLM Setup Guide
## Testing llama.cpp CPU-based inference

---

## Overview

This guide helps you set up and test **llama.cpp** as a local LLM fallback for your RAG chatbot. Since vLLM requires GPU (not available), we're using llama.cpp which runs on CPU.

**Model:** TinyLlama-1.1B-Chat-v1.0 (Q4_K_M quantization)
- **Size:** ~637 MB
- **Quality:** Good for testing, basic conversations
- **Speed:** 2-5 tokens/second on CPU (depending on hardware)

---

## Setup Steps

### 1. Download the Model

Run the setup script to download TinyLlama:

```bash
chmod +x setup-local-llm.sh
./setup-local-llm.sh
```

This will:
- Create a Docker volume `llama_models`
- Download the TinyLlama GGUF model (~637MB)
- Verify the download

**Alternative manual download:**
```bash
docker volume create llama_models
docker run --rm -v llama_models:/models alpine sh -c "
  apk add --no-cache wget && \
  cd /models && \
  wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
"
```

---

### 2. Start llama.cpp Service

The `docker-compose.yml` has been updated to include llama.cpp. Start it:

```bash
docker compose up -d llama-cpp
```

Wait for the model to load (~30-60 seconds):

```bash
# Watch logs until you see "HTTP server listening"
docker compose logs llama-cpp -f
```

Expected output:
```
llama server listening at http://0.0.0.0:8080
```

Press `Ctrl+C` to exit logs.

---

### 3. Verify llama.cpp is Working

Test the health endpoint:

```bash
curl http://localhost:8080/health
```

Expected: `{"status":"ok"}` or similar

Test a simple completion:

```bash
curl http://localhost:8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello, my name is",
    "max_tokens": 20,
    "temperature": 0.7
  }'
```

You should get a JSON response with generated text.

---

### 4. Configure Backend to Use llama.cpp

**Option A: Force llama.cpp (disable OpenAI temporarily)**

Edit `.env` and remove the OpenAI API key:

```bash
# Comment out or clear the value
OPENAI_API_KEY=
```

Restart backend:

```bash
docker compose restart backend
```

**Option B: Let OpenAI fail naturally**

If your OpenAI API key is invalid or you're rate-limited, the backend will automatically fall back to llama.cpp.

---

### 5. Test the Integration

Run the test script:

```bash
chmod +x test-local-llm.sh
./test-local-llm.sh
```

This script will:
1. ✓ Check llama.cpp service status
2. ✓ Test llama.cpp health endpoint
3. ✓ Test direct llama.cpp completion
4. ✓ Check backend configuration
5. ✓ Test full RAG pipeline with llama.cpp

---

## Testing in the UI

1. Open http://localhost:3001
2. Send a message like: **"Hello, introduce yourself"**
3. Check the response metadata to see which model was used

**To verify which model responded:**
- Open browser DevTools (F12)
- Go to Network tab
- Send a message
- Check the response - it should show `"model": "llama.cpp"`

---

## Understanding the LLM Fallback Chain

Your backend tries LLMs in this order:

```
1. OpenAI (gpt-4-turbo-preview)
   ↓ (if fails)
2. vLLM (meta-llama/Llama-2-7b-chat-hf) - requires GPU
   ↓ (if fails)
3. llama.cpp (TinyLlama-1.1B-Chat) - CPU fallback ✓
```

**Current State:**
- ✅ OpenAI: Working (primary)
- ❌ vLLM: Disabled (no GPU)
- ✅ llama.cpp: Enabled (CPU fallback)

---

## Performance Expectations

### TinyLlama-1.1B (Q4_K_M on CPU)

| Metric | Value |
|--------|-------|
| Model size | 637 MB |
| Context length | 2048 tokens |
| Speed (4-core CPU) | 2-5 tokens/sec |
| Speed (8-core CPU) | 5-10 tokens/sec |
| RAM usage | ~1-2 GB |

### Comparison with OpenAI

| Feature | OpenAI GPT-4 | llama.cpp TinyLlama |
|---------|--------------|---------------------|
| Speed | ~50 tokens/sec | 2-5 tokens/sec |
| Quality | Excellent | Basic |
| Context | 128K tokens | 2K tokens |
| Cost | $$ per request | Free (local) |
| Privacy | Sent to OpenAI | 100% local |

---

## Troubleshooting

### Issue: "llama-cpp not running"

**Solution:**
```bash
docker compose up -d llama-cpp
docker compose logs llama-cpp --tail 50
```

Check for errors in logs.

---

### Issue: "Model not found" error

**Solution:**
```bash
# Verify model exists in volume
docker run --rm -v llama_models:/models alpine ls -lh /models/

# Should show: tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

If missing, re-run `./setup-local-llm.sh`

---

### Issue: "Backend still using OpenAI"

**Solution:**
```bash
# Check backend env vars
docker compose exec backend env | grep OPENAI_API_KEY

# If it has a value, clear it in .env and restart
docker compose restart backend

# Verify llama.cpp is in depends_on
docker compose config | grep -A5 "depends_on" | grep llama
```

---

### Issue: Slow response times

**Expected:** llama.cpp on CPU is slower than OpenAI (2-5 tokens/sec vs 50 tokens/sec)

**Improve performance:**
1. Use a smaller model (TinyLlama is already small)
2. Reduce max_tokens in backend config
3. Increase CPU allocation in docker-compose.yml:
   ```yaml
   llama-cpp:
     deploy:
       resources:
         limits:
           cpus: '4'
           memory: 4G
   ```

---

### Issue: Out of memory errors

**Solution:**
```bash
# Check memory usage
docker stats llama-cpp

# If using too much RAM, try a smaller quantization:
# Q4_K_M (current) → Q4_0 (smaller, lower quality)
```

---

## Upgrading to Better Models

Once llama.cpp is working, you can upgrade to better models:

### Recommended Models (by size):

1. **TinyLlama-1.1B** (current) - 637 MB
   - Speed: Fast
   - Quality: Basic
   - Good for: Testing

2. **Llama-3.2-3B** - 2.0 GB
   - Speed: Medium
   - Quality: Good
   - Good for: General use
   ```bash
   wget https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf
   ```

3. **Llama-3.1-8B** - 4.9 GB
   - Speed: Slower
   - Quality: Excellent
   - Good for: Production
   ```bash
   wget https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf
   ```

**To switch models:**
1. Download new GGUF file to volume
2. Update model path in docker-compose.yml (line 103)
3. Restart: `docker compose restart llama-cpp`

---

## Monitoring

### View llama.cpp logs:
```bash
docker compose logs llama-cpp -f
```

### View backend logs (shows which LLM is used):
```bash
docker compose logs backend -f | grep -i "llm\|openai\|llama"
```

### Check llama.cpp stats:
```bash
curl http://localhost:8080/v1/models
```

---

## Stopping llama.cpp

If you want to disable local LLM and use only OpenAI:

```bash
# Stop llama.cpp
docker compose stop llama-cpp

# Re-enable OpenAI in .env
# OPENAI_API_KEY=sk-proj-...

# Restart backend
docker compose restart backend
```

---

## Summary

✅ **What you have now:**
- llama.cpp service configured and ready
- TinyLlama-1.1B model (or you can download it)
- Automatic fallback: OpenAI → llama.cpp
- Test scripts to verify everything works

🚀 **Next steps:**
1. Run `./setup-local-llm.sh` to download the model
2. Run `docker compose up -d llama-cpp` to start the service
3. Run `./test-local-llm.sh` to verify it works
4. Test in UI at http://localhost:3001

📊 **Performance:**
- CPU-based, no GPU required
- 2-5 tokens/second (slower than OpenAI but 100% local)
- Perfect for testing, development, or privacy-sensitive use cases

---

## Resources

- **llama.cpp GitHub:** https://github.com/ggerganov/llama.cpp
- **GGUF Models:** https://huggingface.co/models?search=gguf
- **TinyLlama:** https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0
- **Quantization Guide:** https://github.com/ggerganov/llama.cpp/blob/master/examples/quantize/README.md

---

*Generated: 2025-11-13*
