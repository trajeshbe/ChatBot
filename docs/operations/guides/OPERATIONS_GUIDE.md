# Operations Guide

> **Last Updated**: 2025-11-27
> **Purpose**: Comprehensive operational guide for running, debugging, and maintaining the Enterprise RAG Chatbot

---

## Table of Contents

1. [Log Analysis Commands](#log-analysis-commands)
2. [Common Debugging Scenarios](#common-debugging-scenarios)
3. [Service Management](#service-management)
4. [Testing Workflows](#testing-workflows)
5. [Quick Reference Commands](#quick-reference-commands)
6. [Script Index](#script-index)

---

## Log Analysis Commands

### Basic Log Viewing

```bash
# View all backend logs
docker-compose logs backend

# Follow backend logs in real-time
docker-compose logs -f backend

# View last 100 lines
docker-compose logs --tail=100 backend

# View logs from last 30 minutes
docker-compose logs --since 30m backend

# View all service logs
docker-compose logs
```

### Search for Errors

```bash
# Find all ERROR level logs
docker-compose logs backend | grep ERROR

# Find all errors with context (3 lines before and after)
docker-compose logs backend | grep -A 3 -B 3 ERROR

# Find critical errors
docker-compose logs backend | grep -E "(CRITICAL|ERROR|Exception)"

# Count errors by type
docker-compose logs backend | grep ERROR | cut -d':' -f3 | sort | uniq -c

# Find recent errors (last hour)
docker-compose logs --since 1h backend | grep ERROR
```

### Component-Specific Log Analysis

#### Agent Workflows
```bash
# Track Agent workflow execution
docker-compose logs backend | grep -E "(Agent|workflow|state)" | tail -50

# Monitor Project Estimator workflow
docker-compose logs backend | grep -E "(project_estimator|workflow|BRD|Excel)" | tail -100

# Check Agent 11 (EDA) execution
docker-compose logs backend | grep -E "(Agent.*11|EDA|complexity)" | tail -50

# Monitor Agent 12 (Debate Coordinator)
docker-compose logs backend | grep "Agent.*12\|Debate\|consensus" | tail -50

# Track validator agent
docker-compose logs backend | grep -E "(validator|validation_report|meta)" | tail -50
```

#### RAG Pipeline
```bash
# RAG query processing
docker-compose logs backend | grep -E "(RAG|query|retrieval|embedding)" | tail -50

# Check vector search
docker-compose logs backend | grep -E "(vector|similarity|pgvector)" | tail -50

# Monitor document processing
docker-compose logs backend | grep -E "(document|chunk|embedding|process)" | tail -50

# Check reranking
docker-compose logs backend | grep -E "(rerank|score|relevance)" | tail -50

# Query classification
docker-compose logs backend | grep -E "(classify|query_type|strategy)" | tail -50
```

#### Web Scraping
```bash
# Scraping operations
docker-compose logs backend | grep -E "(scrap|playwright|extract)" | tail -50

# Template extraction
docker-compose logs backend | grep -E "(template|CSS|selector)" | tail -50

# Compliance checks
docker-compose logs backend | grep -E "(compliance|robots|rate.*limit)" | tail -50

# Navigation agent
docker-compose logs backend | grep -E "(navigation|agent|click|scroll)" | tail -50
```

#### LLM Service
```bash
# LLM requests and responses
docker-compose logs backend | grep -E "(LLM|model|token|OpenAI|Claude)" | tail -50

# Check model selection
docker-compose logs backend | grep -E "(model.*select|fallback)" | tail -50

# Token usage
docker-compose logs backend | grep -E "(token|usage|cost)" | tail -50

# API errors
docker-compose logs backend | grep -E "(API.*error|rate.*limit|timeout)" | tail -50
```

### Performance Monitoring

```bash
# Check response times
docker-compose logs backend | grep -E "latency|duration|ms" | tail -50

# Monitor database queries
docker-compose logs backend | grep -E "(query|SELECT|INSERT|UPDATE)" | tail -50

# Track slow operations
docker-compose logs backend | grep -E "(slow|timeout|exceed)" | tail -50

# Memory usage patterns
docker-compose logs backend | grep -E "(memory|RAM|OOM)" | tail -50
```

### Advanced Log Analysis

```bash
# Extract timestamps and errors for timeline analysis
docker-compose logs backend | grep ERROR | awk '{print $1, $2, $0}' | sort

# Find most common errors
docker-compose logs backend | grep ERROR | cut -d':' -f4- | sort | uniq -c | sort -nr | head -20

# Track user session activity
docker-compose logs backend | grep "session_id" | grep "uuid-here"

# Monitor specific endpoint
docker-compose logs backend | grep "/api/v1/query" | tail -50

# Extract JSON responses
docker-compose logs backend | grep -o '{.*}' | jq '.'

# Filter by log level with colors (if supported)
docker-compose logs backend | grep --color=auto -E "INFO|WARNING|ERROR|CRITICAL"
```

### Database Query Logs

```bash
# Enable PostgreSQL query logging (add to docker-compose.yml)
# postgres:
#   command: postgres -c log_statement=all

# View PostgreSQL logs
docker-compose logs postgres | tail -100

# Find slow queries
docker-compose logs postgres | grep "duration:" | awk '$8 > 1000' | tail -20

# Check connection issues
docker-compose logs postgres | grep -E "(connection|timeout|refused)"
```

---

## Common Debugging Scenarios

### Scenario 1: Empty or Poor Quality Responses in Chat

**Symptoms:**
- Chat returns empty responses
- Responses are generic and don't reference documents
- Sources are not included

**Diagnostic Commands:**

```bash
# 1. Check if documents are processed
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT filename, processed, processing_error FROM documents ORDER BY upload_date DESC LIMIT 10;"

# 2. Check if chunks exist
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL;"

# 3. Check if embeddings are generated
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT d.filename, COUNT(dc.id) as chunk_count
   FROM documents d
   LEFT JOIN document_chunks dc ON d.id = dc.document_id
   GROUP BY d.id, d.filename ORDER BY d.upload_date DESC LIMIT 10;"

# 4. Test RAG pipeline directly
cd backend && python debug_rag_pipeline.py "your test query"

# 5. Check retrieval logs
docker-compose logs backend | grep -E "(retrieval|vector|similarity)" | tail -50
```

**Solution Steps:**

1. **If no documents are processed:**
   ```bash
   # Check document service logs
   docker-compose logs backend | grep -E "(document|upload|process)" | tail -100

   # Restart document processing
   docker-compose restart backend
   ```

2. **If chunks exist but no embeddings:**
   ```bash
   # Check embedding service
   docker-compose logs backend | grep -E "(embedding|sentence.*transform)" | tail -50

   # Regenerate embeddings
   cd backend && python regenerate_embeddings.py
   ```

3. **If embeddings exist but retrieval fails:**
   ```bash
   # Check vector search index
   docker-compose exec postgres psql -U postgres -d ragchatbot -c \
     "SELECT * FROM pg_indexes WHERE tablename='document_chunks';"

   # Check threshold settings (may be too high)
   # Default is 0.3, try lowering to 0.1
   ```

4. **If query classification is wrong:**
   ```bash
   # Check classifier logs
   docker-compose logs backend | grep -E "(classify|query_type)" | tail -50

   # Test classifier directly
   cd backend && python -c "
   from app.services.query_classifier import QueryClassifier
   classifier = QueryClassifier()
   result = classifier.classify_query('your query here')
   print(result)
   "
   ```

### Scenario 2: Document Processing Failures

**Symptoms:**
- Documents uploaded but not appearing in chat
- "processed" field remains False
- Processing errors in database

**Diagnostic Commands:**

```bash
# 1. Check processing status
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT filename, processed, processing_error FROM documents WHERE processed = false;"

# 2. Check document service logs
docker-compose logs backend | grep -E "(document|upload|chunk|error)" | tail -100

# 3. Check MinIO connectivity
curl http://localhost:9000/minio/health/live

# 4. Test document upload
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@test.pdf" \
  -F "session_id=test-session"
```

**Solution Steps:**

1. **Check MinIO access:**
   ```bash
   # Access MinIO console
   open http://localhost:9001
   # Login: minioadmin / minioadmin

   # Check if documents bucket exists
   docker-compose exec minio mc ls local/documents
   ```

2. **Check file permissions:**
   ```bash
   # Check if backend can write to /tmp
   docker-compose exec backend ls -la /tmp

   # Check MinIO permissions
   docker-compose logs minio | grep -E "(error|permission)"
   ```

3. **Restart processing pipeline:**
   ```bash
   # Restart backend
   docker-compose restart backend

   # Re-upload failed documents
   # Or manually trigger reprocessing
   cd backend && python -c "
   from app.services.document_service import DocumentService
   from app.core.database import SessionLocal

   db = SessionLocal()
   service = DocumentService(db)
   # Reprocess documents
   "
   ```

### Scenario 3: RAG Retrieval Issues

**Symptoms:**
- No relevant chunks retrieved
- Retrieval scores are too low
- Wrong documents being retrieved

**Diagnostic Commands:**

```bash
# 1. Check retrieval configuration
docker-compose logs backend | grep -E "(threshold|top_k|retrieval)" | tail -50

# 2. Test vector similarity directly
cd backend && python test_vector_search.py

# 3. Check embedding dimensions
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT vector_dims(embedding) FROM document_chunks LIMIT 1;"

# 4. Run RAG debug script
cd backend && python debug_rag_pipeline.py "test query" --verbose

# 5. Check semantic cache
docker-compose exec redis redis-cli
# In Redis CLI:
# KEYS query:*
# GET query:your_query_hash
```

**Solution Steps:**

1. **Lower retrieval threshold:**
   ```bash
   # Edit config or environment variable
   # RAG_SIMILARITY_THRESHOLD=0.1  (default is 0.3)

   # Or test with different threshold
   curl -X POST http://localhost:8000/api/v1/query \
     -H "Content-Type: application/json" \
     -d '{"query": "test", "similarity_threshold": 0.1}'
   ```

2. **Check embedding model consistency:**
   ```bash
   # Ensure same model for indexing and querying
   docker-compose logs backend | grep -E "(sentence.*transform|model.*load)" | head -20

   # Should be: all-MiniLM-L6-v2 (384 dimensions)
   ```

3. **Rebuild vector index:**
   ```bash
   docker-compose exec postgres psql -U postgres -d ragchatbot -c \
     "DROP INDEX IF EXISTS idx_chunks_embedding;
      CREATE INDEX idx_chunks_embedding ON document_chunks
      USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);"
   ```

4. **Clear semantic cache:**
   ```bash
   docker-compose exec redis redis-cli FLUSHDB
   ```

### Scenario 4: Project Estimator Workflow Failures

**Symptoms:**
- Workflow hangs or times out
- Agents not executing in sequence
- Missing BRD or Excel output
- Validation report not generated

**Diagnostic Commands:**

```bash
# 1. Check workflow execution
docker-compose logs backend | grep -E "(workflow|state|agent)" | tail -100

# 2. Check specific agent logs
docker-compose logs backend | grep "Agent 1\|Agent 2\|Agent 3" | tail -50

# 3. Check state file generation
ls -la /tmp/project_estimator_states/

# 4. Test workflow directly
cd backend && python test_project_estimator_validation.py

# 5. Check LLM connectivity
curl -X POST http://localhost:8000/api/v1/models/test \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4"}'
```

**Solution Steps:**

1. **Check agent configuration:**
   ```bash
   # Verify all 7 agents are registered
   cd backend && python -c "
   from app.agents.project_estimator.workflow import ProjectEstimatorWorkflow
   workflow = ProjectEstimatorWorkflow()
   print(workflow.list_agents())
   "
   ```

2. **Check state persistence:**
   ```bash
   # Ensure state directory exists and is writable
   mkdir -p /tmp/project_estimator_states
   chmod 777 /tmp/project_estimator_states

   # Check recent state files
   ls -laht /tmp/project_estimator_states/ | head -10
   ```

3. **Test individual agents:**
   ```bash
   # Test Agent 1 (Complexity Analyzer)
   curl -X POST http://localhost:8000/api/v1/project-estimator/analyze \
     -F "file=@requirements.txt"

   # Test Agent 11 (EDA)
   curl -X POST http://localhost:8000/api/v1/project-estimator/eda \
     -H "Content-Type: application/json" \
     -d '{"project_id": "test-id"}'
   ```

4. **Check timeout settings:**
   ```bash
   # Increase workflow timeout if needed
   # In environment or config:
   # WORKFLOW_TIMEOUT=600  (10 minutes)
   ```

5. **Monitor validator agent:**
   ```bash
   # Check if validator is running
   docker-compose logs backend | grep -E "(validator|meta.*validation)" | tail -50

   # Validator should produce validation_report in state
   ```

### Scenario 5: Frontend-Backend Communication Issues

**Symptoms:**
- Frontend shows "Network Error"
- API calls timeout
- CORS errors in browser console
- WebSocket connection fails

**Diagnostic Commands:**

```bash
# 1. Check backend health
curl http://localhost:8000/health

# 2. Check CORS configuration
docker-compose logs backend | grep CORS

# 3. Test API endpoint directly
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# 4. Check frontend logs
docker-compose logs frontend | tail -50

# 5. Check network connectivity
docker-compose exec frontend curl http://backend:8000/health
```

**Solution Steps:**

1. **Verify CORS settings:**
   ```python
   # In backend/app/main.py
   # Should have:
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3001"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **Check API base URL in frontend:**
   ```typescript
   // In frontend code, should be:
   const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
   ```

3. **Restart both services:**
   ```bash
   docker-compose restart backend frontend
   ```

4. **Check browser console:**
   ```
   Open browser DevTools (F12)
   Go to Console tab
   Look for errors related to fetch, CORS, or network
   ```

5. **Test with curl:**
   ```bash
   # If curl works but browser doesn't, it's likely CORS
   # If curl also fails, backend is the issue
   ```

### Scenario 6: Web Scraping Failures

**Symptoms:**
- Scraping jobs hang indefinitely
- No data extracted
- Template extraction fails
- Compliance errors

**Diagnostic Commands:**

```bash
# 1. Check scraper service logs
docker-compose logs backend | grep -E "(scrap|playwright|extract)" | tail -100

# 2. Check Playwright browser
docker-compose logs backend | grep -E "(browser|chromium)" | tail -50

# 3. Test URL directly
curl -X POST http://localhost:8000/api/v1/scrape \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com"]}'

# 4. Check compliance engine
docker-compose logs backend | grep -E "(compliance|robots|rate)" | tail -50

# 5. Test template extraction
cd backend && python test_template_extraction_ui.py
```

**Solution Steps:**

1. **Check robots.txt compliance:**
   ```bash
   # Test robots.txt checker
   cd backend && python -c "
   from app.services.webscraper.compliance.robots_txt_checker import RobotsTxtChecker
   checker = RobotsTxtChecker()
   result = checker.can_fetch('https://example.com/page')
   print(result)
   "
   ```

2. **Check rate limiting:**
   ```bash
   # May need to adjust rate limits
   # In config or environment:
   # SCRAPER_RATE_LIMIT=1  (requests per second)
   ```

3. **Test Playwright installation:**
   ```bash
   docker-compose exec backend playwright --version
   docker-compose exec backend playwright install chromium
   ```

4. **Test CSS selectors:**
   ```bash
   # Use inspection script
   cd backend && python inspect_screener.py
   ```

5. **Check template validity:**
   ```bash
   # Validate template
   curl -X POST http://localhost:8000/api/v1/templates/validate \
     -H "Content-Type: application/json" \
     -d @template.json
   ```

---

## Service Management

### Individual Service Control

```bash
# Restart specific service
docker-compose restart backend
docker-compose restart frontend
docker-compose restart postgres
docker-compose restart redis
docker-compose restart ollama

# Stop specific service
docker-compose stop backend

# Start specific service
docker-compose start backend

# Rebuild specific service (after code changes)
docker-compose build backend
docker-compose up -d backend

# View specific service logs
docker-compose logs -f backend
```

### Health Checks

```bash
# Check all services status
docker-compose ps

# Check backend health
curl http://localhost:8000/health

# Check PostgreSQL
docker-compose exec postgres pg_isready

# Check Redis
docker-compose exec redis redis-cli ping

# Check Ollama
curl http://localhost:11434/api/tags

# Comprehensive health check
./scripts/maintenance/verify-complete-setup.sh
```

### Restart Strategies

```bash
# Soft restart (preserves data)
docker-compose restart

# Hard restart (rebuilds containers)
docker-compose down
docker-compose up -d

# Full reset (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
./scripts/setup/setup-database.sh
```

### Container Management

```bash
# View container resource usage
docker stats

# Inspect specific container
docker inspect chatbot_backend_1

# Execute command in container
docker-compose exec backend bash
docker-compose exec postgres psql -U postgres

# Copy files from/to container
docker cp file.txt chatbot_backend_1:/tmp/
docker cp chatbot_backend_1:/tmp/output.json ./

# View container logs with timestamps
docker-compose logs --timestamps backend
```

### Database Operations

```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres ragchatbot > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres ragchatbot < backup.sql

# Connect to database
docker-compose exec postgres psql -U postgres ragchatbot

# Common database queries
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
  SELECT tablename FROM pg_tables WHERE schemaname='public';
"

# Check database size
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
  SELECT pg_size_pretty(pg_database_size('ragchatbot'));
"

# Vacuum database (cleanup)
docker-compose exec postgres psql -U postgres -d ragchatbot -c "VACUUM FULL;"
```

### Cache Management

```bash
# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL

# Clear specific keys
docker-compose exec redis redis-cli KEYS "query:*" | xargs docker-compose exec redis redis-cli DEL

# View cache statistics
docker-compose exec redis redis-cli INFO stats

# Monitor cache in real-time
docker-compose exec redis redis-cli MONITOR
```

### Performance Tuning

```bash
# Increase PostgreSQL shared buffers (in docker-compose.yml)
# postgres:
#   command: postgres -c shared_buffers=256MB -c effective_cache_size=1GB

# Increase backend workers (in docker-compose.yml)
# backend:
#   environment:
#     - UVICORN_WORKERS=4

# Monitor resource usage
docker stats --no-stream

# Check disk usage
df -h
du -sh /var/lib/docker/volumes/
```

---

## Testing Workflows

### Comprehensive Testing

```bash
# Run all tests
make test

# Run backend tests only
cd backend && pytest tests/ -v

# Run with coverage
cd backend && pytest tests/ --cov=app --cov-report=html

# Run specific test file
cd backend && pytest tests/test_rag_service.py -v

# Run specific test function
cd backend && pytest tests/test_rag_service.py::test_query_documents -v
```

### Feature-Specific Testing

```bash
# Test RAG pipeline
cd backend && python test_rag_pipeline.py
cd backend && python debug_rag_pipeline.py "test query"

# Test Project Estimator
./test_project_estimator.sh
cd backend && python test_project_estimator_validation.py

# Test document upload
./scripts/testing/test-upload-endpoint.sh

# Test web scraping
./scripts/testing/test-web-scraper.sh

# Test chat interface
./test_chat_comprehensive.sh

# Test agent workflows
./test_agent11_integration.sh
```

### Integration Testing

```bash
# Full end-to-end test
./scripts/testing/comprehensive-validation.sh

# Test document flow (upload → process → query)
./scripts/testing/test-document-flow.sh

# Test multi-file upload
cd backend && python test_project_estimator_multifile.py

# Test UI flows
cd backend && python test_ui_debug.py
```

### Performance Testing

```bash
# Load test queries
cd backend && python -c "
import requests
import time

for i in range(100):
    start = time.time()
    response = requests.post(
        'http://localhost:8000/api/v1/query',
        json={'query': f'test query {i}'}
    )
    print(f'Query {i}: {time.time() - start:.2f}s')
"

# Monitor during load test
watch -n 1 'docker stats --no-stream'
```

### Testing with Different Models

```bash
# Test with OpenAI
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "model": "gpt-4"}'

# Test with Claude
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "model": "claude-3-opus-20240229"}'

# Test with local Ollama
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "model": "ollama/mistral"}'
```

---

## Quick Reference Commands

### One-Liner Diagnostics

```bash
# Count errors in last hour
docker-compose logs --since 1h backend | grep -c ERROR

# Find most recent error
docker-compose logs backend | grep ERROR | tail -1

# Check if all services are running
docker-compose ps | grep -c "Up"

# Count processed documents
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM documents WHERE processed=true;"

# Check embedding count
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL;"

# Find slow queries (last 100 logs)
docker-compose logs --tail=100 backend | grep "latency" | awk '$NF > 1000'

# Check Redis hit rate
docker-compose exec redis redis-cli INFO stats | grep keyspace

# List recent sessions
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT session_id, created_at FROM chat_sessions ORDER BY created_at DESC LIMIT 10;"
```

### Quick Fixes

```bash
# Quick restart all services
docker-compose restart

# Rebuild and restart backend
docker-compose build backend && docker-compose up -d backend

# Clear all caches
docker-compose exec redis redis-cli FLUSHALL

# Regenerate embeddings for failed documents
cd backend && python regenerate_embeddings.py

# Reset database (WARNING: deletes data)
docker-compose down -v postgres && docker-compose up -d postgres && ./scripts/setup/setup-database.sh

# Fix frontend cache
./fix-frontend-cache.sh
```

### Monitoring Commands

```bash
# Watch logs in real-time
watch -n 1 'docker-compose logs --tail=20 backend | grep ERROR'

# Monitor system resources
watch -n 2 'docker stats --no-stream'

# Monitor PostgreSQL queries
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT pid, query, state FROM pg_stat_activity WHERE state != 'idle';"

# Monitor Redis memory
watch -n 2 'docker-compose exec redis redis-cli INFO memory | grep used_memory_human'

# Watch document processing
watch -n 5 'docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT COUNT(*) as total, SUM(CASE WHEN processed THEN 1 ELSE 0 END) as processed FROM documents;"'
```

### Development Workflow

```bash
# Make code changes, rebuild, test
docker-compose build backend && docker-compose up -d backend && docker-compose logs -f backend

# Quick Python code test
docker-compose exec backend python -c "from app.services.rag_service import RAGService; print('OK')"

# Run linting
cd backend && pylint app/
cd frontend && npm run lint

# Format code
cd backend && black app/
cd frontend && npm run format

# Check types
cd backend && mypy app/
cd frontend && npm run type-check
```

---

## Script Index

### Testing Scripts

Located in `docs/operations/scripts/testing/`

| Script | Purpose | Usage |
|--------|---------|-------|
| `test_comprehensive_chatbot.sh` | Full chat interface testing | `./test_comprehensive_chatbot.sh` |
| `test_project_estimator.sh` | Project Estimator workflow test | `./test_project_estimator.sh` |
| `test_project_estimator_validation.py` | Validator agent testing | `python test_project_estimator_validation.py` |
| `test_agent11_integration.sh` | Agent 11 (EDA) integration test | `./test_agent11_integration.sh` |
| `test_document_handling_comprehensive.sh` | Document upload and processing | `./test_document_handling_comprehensive.sh` |
| `test_phase3_extraction.py` | Template extraction testing | `python test_phase3_extraction.py` |
| `test_rag_pipeline.py` | RAG pipeline testing | `python test_rag_pipeline.py` |
| `test_vector_search.py` | Vector similarity search testing | `python test_vector_search.py` |
| `test_ui_debug.py` | UI flow debugging | `python test_ui_debug.py` |
| `test_vision_tool.py` | Vision model testing | `python test_vision_tool.py` |
| `test_scraper_text_extraction.py` | Web scraper testing | `python test_scraper_text_extraction.py` |

### Debugging Scripts

Located in `docs/operations/scripts/debugging/`

| Script | Purpose | Usage |
|--------|---------|-------|
| `debug_rag_pipeline.py` | Comprehensive RAG debugging | `python debug_rag_pipeline.py "query"` |
| `inspect_screener.py` | CSS selector inspection | `python inspect_screener.py` |
| `inspect_drenting.py` | Website structure inspection | `python inspect_drenting.py` |
| `diagnose_chunks.py` | Document chunking analysis | `python diagnose_chunks.py` |
| `test_direct_aadhan_search.py` | Direct search testing | `python test_direct_aadhan_search.py` |

### Validation Scripts

Located in `docs/operations/scripts/validation/`

| Script | Purpose | Usage |
|--------|---------|-------|
| `test_project_estimator_validation.py` | Workflow validation | `python test_project_estimator_validation.py` |
| `test_simple_workflow.py` | Simple workflow validation | `python test_simple_workflow.py` |

### Maintenance Scripts

Located in `docs/operations/scripts/maintenance/` and `scripts/maintenance/`

| Script | Purpose | Usage |
|--------|---------|-------|
| `verify-complete-setup.sh` | Verify all services | `./verify-complete-setup.sh` |
| `watch-upload-realtime.sh` | Monitor uploads in real-time | `./watch-upload-realtime.sh` |

---

## Best Practices

### Before Making Changes

1. **Check current state:**
   ```bash
   git status
   docker-compose ps
   ```

2. **Backup if needed:**
   ```bash
   docker-compose exec postgres pg_dump -U postgres ragchatbot > backup_$(date +%Y%m%d).sql
   ```

3. **Create feature branch:**
   ```bash
   git checkout -b feature/your-feature
   ```

### After Making Changes

1. **Test changes:**
   ```bash
   make test
   ```

2. **Check logs:**
   ```bash
   docker-compose logs --tail=50 backend
   ```

3. **Verify services:**
   ```bash
   ./scripts/maintenance/verify-complete-setup.sh
   ```

### Regular Maintenance

```bash
# Weekly
docker system prune -f  # Clean unused containers
docker volume prune -f  # Clean unused volumes (careful!)

# Monthly
# Backup database
# Review and archive old logs
# Update dependencies

# As needed
# Regenerate embeddings after model changes
# Rebuild indexes after schema changes
# Clear caches after configuration changes
```

---

## Troubleshooting Quick Reference

| Symptom | First Check | Quick Fix |
|---------|-------------|-----------|
| Empty chat responses | `docker-compose logs backend \| grep ERROR` | Check documents processed, lower threshold |
| Service won't start | `docker-compose logs service_name` | Rebuild container, check dependencies |
| Slow queries | `docker stats` | Check indexes, increase resources |
| Connection timeout | `curl http://localhost:8000/health` | Check network, restart service |
| Missing documents | Check database | Verify MinIO, reprocess documents |
| Wrong search results | Check embeddings | Verify model, regenerate embeddings |
| High memory usage | `docker stats` | Clear caches, restart services |
| API errors | Check logs | Verify API keys, check rate limits |

---

## Additional Resources

- **Main README**: `/README.md`
- **Setup Guide**: `/docs/guides/QUICKSTART.md`
- **Architecture**: `/docs/architecture/MEMORY_HIERARCHY_GUIDE.md`
- **RAG Debugging**: `/docs/debugging/RAG_DEBUGGING_GUIDE.md`
- **Script Documentation**: `/scripts/README.md`

---

**Last Updated**: 2025-11-27
**Maintainer**: DevOps Team
**Version**: 1.0
