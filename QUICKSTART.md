# Quick Start Guide - 5 Minutes Setup

## Fixed Issues ✅

The following issues have been resolved:
- ✅ Added missing `package-lock.json` for frontend
- ✅ Added missing Python `__init__.py` files
- ✅ Created `.env` file with defaults
- ✅ Commented out GPU-dependent services (vLLM)
- ✅ Commented out services requiring model downloads (llama.cpp)
- ✅ System now works with minimal dependencies

## Two Setup Options

### Option 1: Without LLM (Testing Only)

The system will run but won't generate AI responses. Good for testing document upload and UI.

```bash
# 1. Start the services
docker-compose up -d

# 2. Wait for services (2-3 minutes)
docker-compose logs -f backend

# 3. Access the application
# Frontend: http://localhost:3001
# Backend: http://localhost:8000/api/docs
```

**Note**: Queries will fail with message: "No LLM backend available"

### Option 2: With OpenAI (Recommended for Testing)

Get full functionality by adding your OpenAI API key.

```bash
# 1. Edit .env file
nano .env  # or use your preferred editor

# 2. Add your OpenAI API key
OPENAI_API_KEY=sk-your-api-key-here

# 3. Start the services
docker-compose up -d

# 4. Wait for services (2-3 minutes)
docker-compose logs -f backend

# 5. Access the application
# Frontend: http://localhost:3001
# Backend: http://localhost:8000/api/docs
```

## Verify It's Working

### 1. Check Service Health

```bash
# Check all services
docker-compose ps

# Should show all services as "healthy" or "running"
```

### 2. Test the Backend

```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy",...}
```

### 3. Test the Frontend

Open browser: http://localhost:3001

You should see the chat interface.

## Quick Test Workflow

### Test 1: Document Upload

1. Go to http://localhost:3001
2. Click "Upload Files" tab
3. Create a test file:
   ```bash
   echo "This is a test document about artificial intelligence." > test.txt
   ```
4. Drag and drop `test.txt` into the upload area
5. Watch it process (takes 5-10 seconds)
6. Status should change to "Processed" ✅

### Test 2: Web Scraping

1. Click "Web Scraping" tab
2. Enter URL: `https://en.wikipedia.org/wiki/Artificial_intelligence`
3. Click "Start Scraping"
4. Wait for completion (10-30 seconds)
5. Status should show "Complete" ✅

### Test 3: Ask Questions (Requires OpenAI Key)

1. Go to "Chat" tab
2. Type: "What documents do I have?"
3. You should get a response with source references
4. Try: "What is artificial intelligence?"
5. You should see answer with Wikipedia source

## Common Issues & Solutions

### Issue: Frontend build fails
```bash
# Solution: Package-lock.json is now included
# If still failing, try:
cd frontend
npm install
cd ..
docker-compose build frontend
```

### Issue: Backend fails to start
```bash
# Check logs
docker-compose logs backend

# Common cause: Database not ready
# Solution: Wait 30 seconds and restart
docker-compose restart backend
```

### Issue: "No LLM backend available"
```bash
# You need to configure an LLM backend
# Easiest option: Add OpenAI API key to .env
OPENAI_API_KEY=sk-your-key-here

# Then restart
docker-compose restart backend
```

### Issue: Services use too much RAM
```bash
# Stop optional services
docker-compose stop grafana tempo loki prefect-server flink-jobmanager flink-taskmanager

# Keep only essentials
# postgres, redis, minio, backend, frontend
```

### Issue: Port conflicts
```bash
# Check what's using the ports
netstat -tulpn | grep -E '3001|8000|5432|6379'

# Edit docker-compose.yml to use different ports
# Change host port (left side):
# ports:
#   - "3002:3000"  # Change 3001 to 3002
```

## Minimal Working Setup

For the absolutely minimal setup that works:

```yaml
# Only these services are required:
services:
  - postgres      # Database
  - redis         # Cache
  - minio         # File storage
  - backend       # API
  - frontend      # UI

# Everything else is optional for basic testing
```

To run minimal setup:
```bash
docker-compose up -d postgres redis minio backend frontend
```

## Next Steps

Once everything is working:

1. **Upload more documents**: Try PDFs, DOCX files
2. **Scrape websites**: Add more URLs
3. **Test queries**: Ask questions about your documents
4. **Check monitoring**: Visit Grafana at http://localhost:3000
5. **Explore API**: Visit http://localhost:8000/api/docs

## Advanced: Enable Local LLM

If you have a GPU and want to use local LLM:

### Option A: vLLM (Requires NVIDIA GPU)

```bash
# 1. Uncomment vLLM service in docker-compose.yml
# 2. Add HuggingFace token to .env
HUGGING_FACE_HUB_TOKEN=hf_your_token

# 3. Update backend config
USE_VLLM=true

# 4. Restart
docker-compose up -d
```

### Option B: llama.cpp (CPU-only)

```bash
# 1. Download a GGUF model
docker run --rm -v ChatBot_llama_models:/models alpine sh -c "apk add wget && wget -O /models/model.gguf https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

# 2. Uncomment llama-cpp service in docker-compose.yml

# 3. Restart
docker-compose up -d
```

## Get Help

- **Error logs**: `docker-compose logs -f backend`
- **Service status**: `docker-compose ps`
- **Restart all**: `docker-compose restart`
- **Clean start**: `docker-compose down -v && docker-compose up -d`

## Resource Usage

Typical resource usage:
- **RAM**: 4-8GB (minimal setup: ~2GB)
- **Disk**: 5-10GB
- **CPU**: 2-4 cores

Adjust Docker Desktop resources if needed:
- Docker Desktop → Settings → Resources
- Increase RAM to 8GB
- Increase CPU to 4 cores

---

**You're all set! 🚀**

The system is now ready to use. Start with Option 2 (with OpenAI) for the best experience.
