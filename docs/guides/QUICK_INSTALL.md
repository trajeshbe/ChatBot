# Quick Installation Guide - Fresh Machine

**Last Updated**: 2025-11-18
**Time Required**: 15-20 minutes
**Prerequisites**: Docker installed

---

## 🚀 5-Step Installation

### Step 1: Clone Repository (1 min)

```bash
git clone <repository-url>
cd ChatBot
```

### Step 2: Environment Setup (1 min)

```bash
# Create environment file
cp .env.example .env

# Optional: Add API keys (nano .env)
# - OPENAI_API_KEY for cloud LLM fallback
# - HUGGING_FACE_HUB_TOKEN for vLLM models
```

### Step 3: Start Services (5-10 min)

```bash
# Start all Docker services
docker-compose up -d

# Wait 60 seconds for services to initialize
sleep 60
```

### Step 4: Setup Database (2 min)

```bash
# Initialize database and apply migrations
./scripts/setup/setup-database.sh

# Expected output:
# ✓ Database 'ragchatbot' created
# ✓ Base schema applied
# ✓ Enhanced schema applied
# ✓ Total tables created: 23
```

### Step 5: Validate Installation (2 min)

```bash
# Run service validation
./scripts/maintenance/validate-services.sh

# Expected: 15/15 checks passing
```

---

## 🌐 Access the Application

- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8000/api/docs
- **GraphQL**: http://localhost:8000/graphql
- **Grafana**: http://localhost:3000 (admin/admin)
- **MinIO**: http://localhost:9001 (minioadmin/minioadmin)

---

## 📋 Optional: Setup Local LLM (5 min)

```bash
# Pull Ollama models
./scripts/setup/setup-ollama-models.sh

# Downloads:
# - qwen2.5:1.5b (~900MB)
# - llama3.2:3b (~2GB)
```

---

## 🧪 Test Your Installation

### Test 1: Upload a Document

```bash
# Create test file
echo "This is a test document about AI and machine learning." > /tmp/test.txt

# Upload
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@/tmp/test.txt" \
  -F "session_id=my-session"

# Expected: {"success": true, "document_id": "...", "chunks_created": 1}
```

### Test 2: Test Web Scraping

```bash
# Test from inside container (IMPORTANT!)
docker exec rag-backend curl -s -X POST http://localhost:8000/api/v1/scraper/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "strategy": "auto"}'

# Expected: {"success": true, "title": "Example Domain", ...}
```

### Test 3: Test Playwright

```bash
# Test from inside container (IMPORTANT!)
docker exec rag-backend curl -s http://localhost:8000/api/v1/test/playwright-minimal

# Expected: {"success": true, "browser_version": "130.0.6723.31"}
```

### Test 4: Query Documents (with Ollama)

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=What is this document about?" \
  -F "session_id=my-session" \
  -F "model_id=qwen2.5:1.5b"

# Expected: {"answer": "...", "sources": [...]}
```

---

## 🔧 Troubleshooting

### Issue: Port Already in Use

```bash
# Check which process is using the port
sudo lsof -i :8000  # Backend
sudo lsof -i :3001  # Frontend

# Kill the process or change ports in docker-compose.yml
```

### Issue: Database Connection Failed

```bash
# Check Postgres status
docker-compose ps postgres

# Restart if needed
docker-compose restart postgres

# Wait 10 seconds and retry setup
sleep 10
./scripts/setup/setup-database.sh
```

### Issue: Backend Container Keeps Restarting

```bash
# Check backend logs
docker-compose logs backend --tail=50

# Common fixes:
# 1. Wait for Postgres (takes 30-60 seconds)
# 2. Rebuild backend: docker-compose build backend
# 3. Clear volumes: docker-compose down -v && docker-compose up -d
```

### Issue: Playwright Tests Failing

```bash
# IMPORTANT: Always test from inside container
docker exec rag-backend curl http://localhost:8000/api/v1/test/playwright-minimal

# DO NOT test from host - may show false errors
# ❌ WRONG: curl http://localhost:8000/api/v1/test/playwright-minimal
```

### Issue: No Ollama Models Found

```bash
# Pull models manually
docker exec rag-ollama ollama pull qwen2.5:1.5b
docker exec rag-ollama ollama list

# Verify
docker exec rag-ollama ollama list
```

---

## 🧹 Clean Restart (if needed)

```bash
# Stop all services
docker-compose down

# Remove all volumes (WARNING: deletes data)
docker-compose down -v

# Clean Docker system
docker system prune -a -f

# Start fresh
docker-compose up -d
./scripts/setup/setup-database.sh
```

---

## 📚 Next Steps

1. **Read Documentation**: See `docs/guides/QUICKSTART.md` for detailed usage
2. **Try Features**: Upload documents, scrape websites, ask questions
3. **Configure LLMs**: Add OpenAI API key for cloud models
4. **Explore UI**: Visit http://localhost:3001 to use the chat interface
5. **Check Metrics**: Visit http://localhost:3000 for Grafana dashboards

---

## 🆘 Getting Help

- **Comprehensive Validation**: See `FRESH_INSTALLATION_VALIDATION.md`
- **Script Documentation**: See `scripts/README.md`
- **Architecture Guide**: See `docs/architecture/MEMORY_HIERARCHY_GUIDE.md`
- **Debugging Guide**: See `docs/debugging/DEBUG_QUICK_REFERENCE.md`
- **Web Scraper Tests**: See `WEB_SCRAPER_TEST_RESULTS.md`

---

## ✅ Installation Checklist

- [ ] Docker and Docker Compose installed
- [ ] Repository cloned
- [ ] `.env` file created from `.env.example`
- [ ] Services started (`docker-compose up -d`)
- [ ] Database setup completed
- [ ] Service validation passed (15/15 checks)
- [ ] Optional: Ollama models downloaded
- [ ] Frontend accessible at http://localhost:3001
- [ ] Backend API accessible at http://localhost:8000

---

**Installation Time**: ~15-20 minutes
**Ready for**: Development, Testing, Production (with proper security config)
**Support**: See documentation or run `./scripts/maintenance/validate-services.sh` for diagnostics

