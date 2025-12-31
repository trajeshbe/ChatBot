# Enterprise RAG Chatbot - Complete Deployment Guide

## 🎯 Overview

Multi-model RAG chatbot with intelligent model selection:
- **Proprietary APIs**: OpenAI (GPT-4, GPT-3.5), Anthropic Claude
- **Local LLMs**: Ollama (Llama 3.2, Qwen 2.5) - CPU/GPU support
- **Features**: Document upload, web scraping, semantic caching, model selection UI
- **WSL2/Docker Compatible**: Tested on Windows WSL2 environment

---

## 📋 Prerequisites

### Required
- **Docker** & **Docker Compose** (v2.0+)
- **Git**
- **4GB+ RAM** (8GB+ recommended for local models)
- **10GB+ disk space**

### Optional (for proprietary models)
- **OpenAI API Key** → https://platform.openai.com/api-keys
- **Anthropic API Key** → https://console.anthropic.com/

### Optional (for GPU acceleration)
- **NVIDIA GPU** with CUDA support
- **NVIDIA Docker runtime**

---

## 🚀 Quick Start (10 Minutes)

### Step 1: Clone & Configure

```bash
# Navigate to project directory
cd /home/user/ChatBot

# Create environment file
cp .env.example .env
```

### Step 2: Add API Keys (Optional)

Edit `.env` file:

```bash
# Proprietary models (optional - local models work without these!)
OPENAI_API_KEY=sk-...                    # For GPT models
ANTHROPIC_API_KEY=sk-ant-...             # For Claude models

# Database (use defaults or customize)
POSTGRES_PASSWORD=postgres
DEBUG=true
ENABLE_TRACING=true
```

**💡 Note**: You can skip API keys and use **free local models** via Ollama!

### Step 3: Start Core Services

```bash
# Start infrastructure services first
docker compose up -d postgres redis minio prefect-server tempo

# Wait 30 seconds for initialization
sleep 30
```

### Step 4: Setup Ollama (Local Models)

```bash
# Run automated setup script
./setup-ollama.sh
```

**Expected output:**
```
✅ Ollama Setup Complete!
Downloaded models:
  • Llama 3.2 3B - General purpose, good quality
  • Qwen 2.5 1.5B - Fast, multilingual
```

This downloads ~3GB of models. **Takes 5-10 minutes** depending on internet speed.

### Step 5: Start Application

```bash
# Start backend and frontend
docker compose up -d backend frontend

# Watch backend logs to verify startup
docker compose logs -f backend
```

**Look for success indicators:**
```
✓ Using Enhanced LLM Service with multi-model support
Initializing LLM service... (Type: EnhancedLLMService)
Available models: 11 total
Default model: llama-3.2-3b-cpu
Application startup complete - API is ready
```

Press `Ctrl+C` to stop watching logs.

### Step 6: Verify Deployment

```bash
# Run comprehensive validation
./validate-services.sh

# Or manually check key services:
docker compose ps                           # All services status
curl http://localhost:8000/health          # Backend health
curl http://localhost:8000/api/v1/models/  # Available models
```

**Expected validation output**:
```
✅ Frontend UI          - OK
✅ Backend API Docs     - OK
✅ Backend Health       - OK
✅ Redis                - OK
✅ PostgreSQL           - OK
✅ Ollama Models        - OK (2 models installed)
```

### Step 7: Open Application

🌐 **Frontend**: http://localhost:3001

You should see:
- Chat interface with model dropdown
- Upload and Scrape tabs
- Model selector in the header

---

## 🔗 Service URLs & Validation

### Primary Interfaces

| Service | URL | Default Credentials | Validation |
|---------|-----|---------------------|------------|
| **Frontend UI** | http://localhost:3001 | - | Should load chat interface with model dropdown |
| **Backend API Docs** | http://localhost:8000/api/docs | - | Swagger UI with all endpoints |
| **GraphQL Playground** | http://localhost:8000/graphql | - | Interactive GraphQL explorer |
| **Health Check** | http://localhost:8000/health | - | Returns `{"status": "healthy"}` |

### Monitoring & Administration

| Service | URL | Default Credentials | Purpose |
|---------|-----|---------------------|---------|
| **Grafana Dashboards** | http://localhost:3000 | admin / admin | Metrics visualization |
| **MinIO Console** | http://localhost:9001 | minioadmin / minioadmin | Object storage for documents |
| **Redis Insight** | http://localhost:8002 | - | Redis cache monitoring |
| **Prefect UI** | http://localhost:4200 | - | Workflow orchestration |
| **Flink Dashboard** | http://localhost:8081 | - | Stream processing |
| **Envoy Admin** | http://localhost:9901 | - | Service mesh admin |

### Validation Steps

#### 1. Frontend (React UI)
```bash
# Test frontend is accessible
curl -I http://localhost:3001

# Expected: HTTP 200 OK
```
**Manual Check**: Open http://localhost:3001 and verify:
- ✅ Chat interface loads
- ✅ Model dropdown shows 11 models
- ✅ Upload and Scrape tabs are visible

#### 2. Backend API
```bash
# Health check
curl http://localhost:8000/health

# Expected output:
{"status":"healthy","timestamp":"2024-...","version":"1.0.0"}

# Test models endpoint
curl http://localhost:8000/api/v1/models/ | jq

# Expected: List of 11 available models
```

#### 3. GraphQL API
```bash
# Test GraphQL endpoint
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __schema { types { name } } }"}'

# Expected: GraphQL schema response
```
**Manual Check**: Open http://localhost:8000/graphql for interactive playground

#### 4. MinIO (Object Storage)
```bash
# Check MinIO is running
curl -I http://localhost:9001

# Expected: HTTP 200 or 302
```
**Manual Check**:
1. Open http://localhost:9001
2. Login: `minioadmin` / `minioadmin`
3. Should see buckets: `documents`, `uploads`

#### 5. Grafana (Monitoring)
**Manual Check**:
1. Open http://localhost:3000
2. Login: `admin` / `admin`
3. Navigate to Dashboards
4. Should see pre-configured dashboards for:
   - Backend API metrics
   - Database performance
   - LLM usage tracking

#### 6. Prefect (Workflows)
```bash
# Check Prefect UI
curl -I http://localhost:4200

# Expected: HTTP 200 OK
```
**Manual Check**: Open http://localhost:4200 to view:
- Document processing workflows
- Scraping job status
- Scheduled tasks

#### 7. Redis (Cache)
```bash
# Test Redis connection
docker exec -it rag-redis redis-cli ping

# Expected output: PONG

# Check cached queries
docker exec -it rag-redis redis-cli KEYS "*"
```
**Manual Check**: Open http://localhost:8002 for Redis Insight dashboard

#### 8. PostgreSQL (Database)
```bash
# Test database connection
docker exec -it rag-postgres psql -U postgres -c "SELECT version();"

# Expected: PostgreSQL version info

# Check tables exist
docker exec -it rag-postgres psql -U postgres -d rag_chatbot -c "\dt"

# Expected: List of tables (documents, chunks, conversations, etc.)
```

#### 9. Ollama (Local LLM)
```bash
# List installed models
docker exec rag-ollama ollama list

# Expected output:
# NAME                             SIZE
# llama3.2:3b-instruct-q4_K_M     2.0GB
# qwen2.5:1.5b-instruct-q4_K_M    1.0GB

# Test inference
docker exec rag-ollama ollama run llama3.2:3b-instruct-q4_K_M "Hello, what model are you?"

# Expected: Response from Llama 3.2
```

#### 10. All Services Status
```bash
# Check all services are running
docker compose ps

# Expected: All services should show "Up" status
```

**Quick Validation Script**:
```bash
#!/bin/bash
echo "=== Service Health Check ==="

# Frontend
echo -n "Frontend (3001): "
curl -s -o /dev/null -w "%{http_code}" http://localhost:3001 && echo " ✅" || echo " ❌"

# Backend Health
echo -n "Backend Health (8000): "
curl -s http://localhost:8000/health > /dev/null && echo " ✅" || echo " ❌"

# API Docs
echo -n "API Docs (8000/api/docs): "
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/docs && echo " ✅" || echo " ❌"

# GraphQL
echo -n "GraphQL (8000/graphql): "
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/graphql && echo " ✅" || echo " ❌"

# Grafana
echo -n "Grafana (3000): "
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 && echo " ✅" || echo " ❌"

# MinIO
echo -n "MinIO (9001): "
curl -s -o /dev/null -w "%{http_code}" http://localhost:9001 && echo " ✅" || echo " ❌"

# Prefect
echo -n "Prefect (4200): "
curl -s -o /dev/null -w "%{http_code}" http://localhost:4200 && echo " ✅" || echo " ❌"

# Redis Insight
echo -n "Redis Insight (8002): "
curl -s -o /dev/null -w "%{http_code}" http://localhost:8002 && echo " ✅" || echo " ❌"

# Flink
echo -n "Flink (8081): "
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081 && echo " ✅" || echo " ❌"

# Envoy
echo -n "Envoy (9901): "
curl -s -o /dev/null -w "%{http_code}" http://localhost:9901 && echo " ✅" || echo " ❌"

echo "=== Models Check ==="
curl -s http://localhost:8000/api/v1/models/ | jq -r '.[] | "  • \(.name)"'

echo "=== Ollama Models ==="
docker exec rag-ollama ollama list
```

Save this as `validate-services.sh` and run:
```bash
chmod +x validate-services.sh
./validate-services.sh
```

---

## ✅ Verify Model Selection Works

### Test Local Models (Free!)

1. Open http://localhost:3001
2. Click **model dropdown** in header
3. Select **"Llama 3.2 3B Q4 (CPU)"**
4. Ask: **"What model are you?"**
5. Response should show badge: **"Llama 3.2 3B Q4 (CPU)"** ✅

Try the same with **"Qwen 2.5 1.5B Q4 (CPU)"** - even faster!

### Test Proprietary Models (if API keys configured)

1. Select **"GPT-3.5 Turbo"** from dropdown
2. Ask: **"What model are you?"**
3. Response badge should show: **"GPT-3.5 Turbo"** ✅

---

## 🤖 Available Models

### Proprietary (Requires API Keys)

| Model | Provider | Speed | Quality | Cost | Best For |
|-------|----------|-------|---------|------|----------|
| **GPT-4 Turbo** | OpenAI | Medium | Excellent | $$$ | Complex reasoning |
| **GPT-4** | OpenAI | Slow | Excellent | $$$$ | High-quality tasks |
| **GPT-3.5 Turbo** | OpenAI | Fast | Good | $ | General use, high volume |
| **Claude 3.5 Sonnet** | Anthropic | Fast | Excellent | $$ | Coding, analysis |
| **Claude 3 Opus** | Anthropic | Slow | Best | $$$$ | Most demanding tasks |
| **Claude 3 Haiku** | Anthropic | Very Fast | Good | $ | Simple queries |

### Local (Free, No API Keys Needed!)

| Model | Provider | Speed | Quality | RAM | Best For |
|-------|----------|-------|---------|-----|----------|
| **Llama 3.2 3B Q4** ⭐ | Ollama | Medium | Good | ~2GB | General purpose CPU |
| **Qwen 2.5 1.5B Q4** ⭐ | Ollama | Fast | Good | ~1GB | Fast responses, multilingual |

### GPU Models (if GPU available)

| Model | Provider | Speed | Quality | VRAM | Best For |
|-------|----------|-------|---------|------|----------|
| **Llama 3.1 8B** | vLLM | Very Fast | Excellent | ~12GB | GPU-accelerated |
| **Llama 3.2 3B** | vLLM | Very Fast | Good | ~6GB | Lightweight GPU |
| **Qwen 2.5 7B** | vLLM | Very Fast | Excellent | ~12GB | Multilingual GPU |

---

## 📚 Upload Documents

### Via UI

1. Click **"Upload"** tab
2. Drag & drop files (PDF, DOCX, TXT, MD, JSON)
3. Wait for processing (progress indicator shown)
4. Go back to **"Chat"** tab
5. Ask questions about your documents!

### Via API

```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@document.pdf"
```

### Supported Formats

- **PDF** - Extracted with layout preservation
- **DOCX** - Microsoft Word documents
- **TXT** - Plain text files
- **MD** - Markdown files
- **JSON** - JSON data

---

## 🌐 Web Scraping

### Via UI

1. Click **"Scrape"** tab
2. Enter URL (e.g., https://example.com)
3. Optional: Add scraping instructions
4. Click **"Scrape URL"**
5. Content is extracted and indexed
6. Ask questions in **"Chat"** tab!

### Via API

```bash
curl -X POST http://localhost:8000/api/v1/scrape \
  -d "url=https://example.com" \
  -d "scrape_prompt=Extract main content"
```

---

## 🔧 Configuration

### Environment Variables

All configuration in `.env`:

```bash
# === LLM API Keys (Optional) ===
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# === Database ===
POSTGRES_SERVER=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=ragchatbot

# === Storage ===
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# === Features ===
DEBUG=true
ENABLE_TRACING=true
USE_SEMANTIC_CACHE=true

# === RAG Settings ===
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K_RESULTS=5
SIMILARITY_THRESHOLD=0.7
```

### Add More Ollama Models

```bash
# List available models
docker exec rag-ollama ollama list

# Pull additional models
docker exec rag-ollama ollama pull mistral:7b
docker exec rag-ollama ollama pull codellama:7b
docker exec rag-ollama ollama pull phi3:3.8b
docker exec rag-ollama ollama pull gemma:7b

# View all available models
docker exec rag-ollama ollama list --available
```

To add them to the UI dropdown, update `backend/app/models/model_registry.py`.

---

## 📊 Monitoring & Logs

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f ollama
docker compose logs -f frontend

# Search for errors
docker compose logs backend | grep -i error
docker compose logs backend | grep -i "model"
```

### Quick Service Access

For complete service URLs, credentials, and validation steps, see **[🔗 Service URLs & Validation](#-service-urls--validation)** section above.

**Quick Links**:
- Frontend UI: http://localhost:3001
- API Docs: http://localhost:8000/api/docs
- GraphQL: http://localhost:8000/graphql
- Grafana: http://localhost:3000 (admin/admin)
- MinIO: http://localhost:9001 (minioadmin/minioadmin)

**Validate All Services**:
```bash
./validate-services.sh
```

---

## 🔄 Common Operations

### Restart Services

```bash
# Restart everything
docker compose restart

# Restart specific service
docker compose restart backend
docker compose restart ollama

# Rebuild and restart
docker compose up -d --build backend
```

### Stop Services

```bash
# Stop all (keeps data)
docker compose down

# Stop and remove ALL data (⚠️ DELETES EVERYTHING!)
docker compose down -v
```

### Update Application

```bash
git pull
docker compose build backend frontend
docker compose up -d
```

### Reset Database Only

```bash
docker compose stop backend
docker compose down postgres
docker volume rm chatbot_postgres_data
docker compose up -d postgres

# Wait 10 seconds
sleep 10

docker compose up -d backend
```

---

## 🛠️ Troubleshooting

### Backend Won't Start

```bash
# Check logs for errors
docker compose logs backend | tail -50

# Common fixes:
docker compose restart postgres redis
sleep 10
docker compose restart backend
```

### Models Not Showing in Dropdown

```bash
# Verify enhanced service is loaded
docker compose logs backend | grep "Enhanced"

# Should see: "✓ Using Enhanced LLM Service"

# If you see "Using basic LLM service" instead:
docker compose build backend
docker compose restart backend
```

### Ollama Models Not Responding

```bash
# Check Ollama container is running
docker compose ps ollama

# Verify models are downloaded
docker exec rag-ollama ollama list

# Expected output:
# NAME                              SIZE
# llama3.2:3b                       2.0GB
# qwen2.5:1.5b                      1.0GB

# Re-download if needed
./setup-ollama.sh
```

### Connection Errors

```bash
# Check all services are running
docker compose ps

# Restart dependent services
docker compose restart postgres redis minio
sleep 10
docker compose restart backend
```

### Out of Memory

```bash
# Check Docker resource usage
docker stats

# Solutions:
# 1. Increase Docker Desktop memory limit (8GB+)
# 2. Stop unused services:
docker compose stop prefect-server tempo

# 3. Use smaller models only (Qwen 1.5B instead of Llama 3.2 3B)
```

### Permission Errors (WSL2)

```bash
# Fix file permissions
sudo chown -R $USER:$USER /home/user/ChatBot
chmod -R 755 /home/user/ChatBot

# Fix script permissions
chmod +x setup-ollama.sh
chmod +x scripts/*.sh
```

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│              Frontend (Next.js + TypeScript)         │
│             http://localhost:3001                    │
│                                                      │
│  • Chat Interface                                    │
│  • Model Selection Dropdown                          │
│  • Upload & Scrape Tabs                              │
│  • Real-time Model Badge Display                     │
└───────────────────┬──────────────────────────────────┘
                    │ HTTP/REST
┌───────────────────▼──────────────────────────────────┐
│          Backend API (FastAPI + Python)              │
│           http://localhost:8000                      │
│                                                      │
│  ┌────────────────────────────────────────────┐     │
│  │    Enhanced LLM Service                    │     │
│  │    • Model Registry (11 models)            │     │
│  │    • Intelligent Routing                   │     │
│  │    • Cost Tracking                         │     │
│  │    • Model Selection                       │     │
│  └──┬──────────┬──────────┬──────────┬────────┘     │
│     │          │          │          │              │
└─────┼──────────┼──────────┼──────────┼──────────────┘
      │          │          │          │
      ▼          ▼          ▼          ▼
  ┌────────┐┌─────────┐┌────────┐┌──────────┐
  │ OpenAI ││ Claude  ││ vLLM   ││  Ollama  │
  │  API   ││   API   ││  GPU   ││ CPU/GPU  │
  └────────┘└─────────┘└────────┘└────┬─────┘
                                       ├─ Llama 3.2 3B
                                       └─ Qwen 2.5 1.5B

      ┌──────────────────────────────────────┐
      │      Supporting Services             │
      ├──────────────────────────────────────┤
      │  • PostgreSQL + pgvector (vectors)   │
      │  • Redis (semantic caching)          │
      │  • MinIO (document storage)          │
      │  • Prefect (workflow orchestration)  │
      │  • Tempo (distributed tracing)       │
      └──────────────────────────────────────┘
```

---

## 🚀 Performance Optimization

### For Faster Responses

1. **Use Qwen 1.5B** - 2x faster than Llama 3.2 3B
2. **Enable semantic caching** (already enabled by default)
3. **Reduce chunk size** in `.env`: `CHUNK_SIZE=300`
4. **Use GPT-3.5 Turbo** - Fastest proprietary model

### For Better Quality

1. **Use GPT-4 Turbo** - Best overall quality
2. **Use Claude 3.5 Sonnet** - Best for coding/analysis
3. **Use Llama 3.2 3B** - Best free local model
4. **Upload relevant documents** - Better RAG context

### For Lower Cost

1. **Use local Ollama models** - Completely free!
2. **Use GPT-3.5 Turbo** - Cheapest proprietary model
3. **Enable caching** - Reuses responses for similar queries (already enabled)
4. **Batch similar questions** - Cache hit rate improves

---

## 🎓 Advanced: GPU Support

If you have an NVIDIA GPU, you can use GPU-accelerated models:

### 1. Install NVIDIA Docker Runtime

```bash
# Ubuntu/Debian
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### 2. Uncomment vLLM Service

Edit `docker-compose.yml` and uncomment the vLLM service section (~lines 70-90).

### 3. Start vLLM

```bash
docker compose up -d vllm-service

# Check logs
docker compose logs -f vllm-service
```

### 4. Test GPU Model

Select **"Llama 3.1 8B (GPU)"** from dropdown and test!

---

## 📖 API Reference

### Query Endpoint

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=What is RAG?" \
  -F "model_id=llama-3.2-3b-cpu" \
  -F "use_cache=true"
```

### List Models

```bash
curl http://localhost:8000/api/v1/models/
```

Response:
```json
{
  "models": [...],
  "grouped": {
    "proprietary": [...],
    "local_gpu": [...],
    "local_cpu": [...]
  },
  "default": "llama-3.2-3b-cpu",
  "gpu_info": {...}
}
```

### Health Check

```bash
curl http://localhost:8000/health
```

---

## 🏭 Production Deployment

For production environments:

### 1. Security

- [ ] Change all default passwords in `.env`
- [ ] Use Docker secrets instead of `.env` files
- [ ] Enable HTTPS with proper SSL certificates
- [ ] Add authentication middleware
- [ ] Configure firewall rules
- [ ] Enable rate limiting

### 2. Scalability

```bash
# Scale backend horizontally
docker compose up -d --scale backend=3

# Or use Kubernetes
kubectl scale deployment backend --replicas=5 -n rag-chatbot
```

### 3. Monitoring

- Set up Prometheus + Grafana
- Configure alerts for errors
- Monitor resource usage
- Track model costs

### 4. Backups

```bash
# Backup PostgreSQL
docker exec rag-postgres pg_dump -U postgres ragchatbot > backup.sql

# Backup MinIO (documents)
docker exec rag-minio mc mirror /data/documents /backup/
```

---

## 📋 Quick Command Reference

```bash
# === Setup ===
./setup-ollama.sh                    # Setup local models
docker compose up -d                 # Start all services
docker compose logs -f backend       # Watch logs

# === Operations ===
docker compose ps                    # Check status
docker compose restart backend       # Restart service
docker compose down                  # Stop all (keep data)
docker compose down -v               # Stop all (DELETE data)
docker compose build backend         # Rebuild backend

# === Testing ===
curl http://localhost:8000/health            # Health check
curl http://localhost:8000/api/v1/models/    # List models

# === Ollama ===
docker exec rag-ollama ollama list            # List models
docker exec rag-ollama ollama pull mistral   # Download model
docker exec rag-ollama ollama ps              # Running models

# === Logs ===
docker compose logs -f backend               # Backend logs
docker compose logs -f ollama                # Ollama logs
docker compose logs backend | grep error     # Search errors
```

---

## 🎯 Next Steps

Now that your deployment is complete:

1. **✅ Test Model Selection**
   - Try all available models
   - Compare response quality
   - Check model badges appear

2. **📚 Upload Your Documents**
   - Upload PDFs, DOCX, TXT files
   - Ask questions about them
   - Verify source citations work

3. **🌐 Try Web Scraping**
   - Scrape a documentation site
   - Ask questions about scraped content
   - Verify it works with different websites

4. **⚙️ Customize**
   - Add more Ollama models
   - Adjust RAG settings
   - Customize UI theme

5. **🚀 Deploy to Production** (optional)
   - Set up Kubernetes cluster
   - Configure monitoring
   - Enable security features

---

## 📞 Support

- **Documentation**: See `/docs` folder
- **API Docs**: http://localhost:8000/api/docs
- **Logs**: `docker compose logs -f backend`
- **Issues**: Check backend logs first for error messages

---

## 🎉 Summary

**Congratulations!** You now have a fully functional enterprise RAG chatbot with:

✅ **11 LLM models** (6 proprietary + 5 local)
✅ **Intelligent model selection** with UI dropdown
✅ **Document upload & processing**
✅ **Web scraping** capability
✅ **Semantic caching** for performance
✅ **Model validation** with response badges
✅ **Working local models** via Ollama (no API keys needed!)
✅ **WSL2/Docker compatible** (tested and verified)

**Your chatbot is ready to use!** 🚀

Enjoy exploring different models and comparing their capabilities!
