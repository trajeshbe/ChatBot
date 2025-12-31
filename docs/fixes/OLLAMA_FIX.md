# Ollama 404 Error Fix

## Problem Summary

The Ollama diagnostic revealed two issues:

1. **Healthcheck Failing**: The healthcheck was using `curl` which doesn't exist in the Ollama container
2. **404 Errors on `/api/generate`**: No models are installed, causing the API to return 404

## Root Cause

Looking at the backend logs in the diagnostic:
```
[GIN] 2025/11/16 - 16:23:01 | 404 | 2.543581ms | 172.20.0.12 | POST "/api/generate"
```

This indicates the backend is trying to use Ollama, but **no models are available**.

## Solution Applied

### 1. Fixed Healthcheck (✅ Complete)

**Changed in `docker-compose.yml`:**
```yaml
# OLD (doesn't work - curl not in container)
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]

# NEW (uses ollama CLI)
healthcheck:
  test: ["CMD", "ollama", "list"]
```

This uses the `ollama` CLI that's built into the container instead of relying on `curl`.

### 2. Pull Ollama Models (❌ Action Required)

You need to pull at least one model. Choose one of these options:

## Quick Fix (Recommended)

Run the automated setup script:

```bash
# Option 1: Use existing script (if docker/docker-compose available)
./scripts/setup/setup-ollama-models.sh
```

**OR manually pull models:**

```bash
# Option 2: Pull models manually

# Start Ollama if not running
docker compose up -d ollama

# Wait for Ollama to start (15 seconds)
sleep 15

# Pull a fast, small model (Qwen 1.5B - ~1GB)
docker exec rag-ollama ollama pull qwen2.5:1.5b-instruct-q4_K_M

# OR pull a better quality model (Llama 3.2 3B - ~2GB)
docker exec rag-ollama ollama pull llama3.2:3b-instruct-q4_K_M

# Verify models are installed
docker exec rag-ollama ollama list
```

## Step-by-Step Manual Process

If the automated script doesn't work, follow these steps:

### Step 1: Apply the healthcheck fix and restart Ollama

```bash
# Restart Ollama with the new healthcheck
docker compose up -d ollama

# Check status (should now be healthy after models are pulled)
docker ps | grep ollama
```

### Step 2: Pull a model

Choose based on your needs:

**Fast & Small (Qwen 1.5B - Recommended for testing):**
```bash
docker exec rag-ollama ollama pull qwen2.5:1.5b-instruct-q4_K_M
```
- Size: ~1GB
- Speed: 10-15 tokens/sec on CPU
- Good for quick responses

**Better Quality (Llama 3.2 3B):**
```bash
docker exec rag-ollama ollama pull llama3.2:3b-instruct-q4_K_M
```
- Size: ~2GB
- Speed: 5-10 tokens/sec on CPU
- Better quality responses

### Step 3: Verify models

```bash
# List installed models
docker exec rag-ollama ollama list

# Expected output:
# NAME                            ID              SIZE      MODIFIED
# qwen2.5:1.5b-instruct-q4_K_M   abc123def       1.0 GB    2 minutes ago
```

### Step 4: Test the model

```bash
# Test with a simple prompt
docker exec rag-ollama ollama run qwen2.5:1.5b-instruct-q4_K_M "Say hello"

# Expected: Model should respond with a greeting
```

### Step 5: Restart backend

```bash
# Restart backend to pick up the new model
docker compose restart backend

# Check backend logs for Ollama detection
docker compose logs backend | grep -i ollama
```

## Verification

### Check Ollama Health

```bash
# Container should now be healthy
docker ps | grep ollama

# Should show: (healthy) instead of (unhealthy)
```

### Check Available Models via API

```bash
# From host machine
curl http://localhost:11434/api/tags | python3 -m json.tool

# Expected output:
# {
#   "models": [
#     {
#       "name": "qwen2.5:1.5b-instruct-q4_K_M",
#       "modified_at": "2025-11-16T...",
#       "size": 1000000000
#     }
#   ]
# }
```

### Test via Backend

```bash
# Test RAG query with Ollama model
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Hello, can you hear me?",
    "model": "ollama/qwen2.5:1.5b-instruct-q4_K_M"
  }'
```

## Model Configuration in Backend

The backend should automatically detect available Ollama models. Check `backend/app/services/llm_service.py` to see how models are configured.

### Typical model names in the app:
- `ollama/qwen2.5:1.5b-instruct-q4_K_M` - Qwen 1.5B
- `ollama/llama3.2:3b-instruct-q4_K_M` - Llama 3.2 3B

## Troubleshooting

### Issue: "Cannot connect to Ollama"

```bash
# Check if Ollama is running
docker ps | grep ollama

# Check Ollama logs
docker logs rag-ollama

# Restart if needed
docker compose restart ollama
```

### Issue: "Model not found" (404)

```bash
# List models
docker exec rag-ollama ollama list

# If empty, pull a model
docker exec rag-ollama ollama pull qwen2.5:1.5b-instruct-q4_K_M
```

### Issue: "Healthcheck still failing"

```bash
# Check healthcheck logs
docker inspect rag-ollama | grep -A 10 "Health"

# Manual healthcheck test
docker exec rag-ollama ollama list

# If this works but healthcheck fails, restart:
docker compose up -d --force-recreate ollama
```

### Issue: "Model pulls very slowly"

This is normal. Models are 1-2GB and pull from Ollama's registry. Progress will be shown during pull.

## Next Steps

1. ✅ Apply the docker-compose.yml fix (already done)
2. ⏳ Pull at least one model
3. ⏳ Restart Ollama and backend
4. ⏳ Test via frontend at http://localhost:3001

## Additional Resources

- Ollama Model Library: https://ollama.com/library
- Ollama API Docs: https://github.com/ollama/ollama/blob/main/docs/api.md
- Setup Scripts: `scripts/setup/setup-ollama-models.sh`
- Diagnostics: `./diagnose-ollama.sh`

## Summary

The fix involves:
1. ✅ **Healthcheck fixed** - Changed from `curl` to `ollama list`
2. ❌ **Models required** - Pull at least one model using the commands above
3. ❌ **Backend restart** - Restart backend after pulling models

Once you pull a model and restart the backend, the 404 errors should disappear and Ollama will work properly.
