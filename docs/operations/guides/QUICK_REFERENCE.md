# Operations Quick Reference

> **Last Updated**: 2025-11-27
> **Purpose**: Quick access to most commonly used operational commands

---

## Emergency Quick Fixes

```bash
# Service won't start
docker-compose restart backend

# Empty responses from chat
docker-compose exec redis redis-cli FLUSHALL && docker-compose restart backend

# Database connection issues
docker-compose restart postgres && sleep 10 && docker-compose restart backend

# Complete system reset (WARNING: deletes all data)
docker-compose down -v && docker-compose up -d && ./scripts/setup/setup-database.sh

# Frontend cache issues
./fix-frontend-cache.sh
```

---

## Most Used Log Commands

```bash
# Last 50 errors
docker-compose logs backend | grep ERROR | tail -50

# Follow logs in real-time
docker-compose logs -f backend

# Last hour of logs
docker-compose logs --since 1h backend

# Search for specific error
docker-compose logs backend | grep "your error text"

# Count errors
docker-compose logs backend | grep -c ERROR

# Extract JSON responses
docker-compose logs backend | grep -o '{.*}' | jq '.'
```

---

## Component-Specific Logs

```bash
# RAG pipeline
docker-compose logs backend | grep -E "(RAG|retrieval|embedding)" | tail -50

# Project Estimator
docker-compose logs backend | grep -E "(project_estimator|workflow|BRD)" | tail -50

# Web Scraper
docker-compose logs backend | grep -E "(scrap|playwright|extract)" | tail -50

# Agent workflows
docker-compose logs backend | grep -E "(Agent|workflow|state)" | tail -50

# LLM service
docker-compose logs backend | grep -E "(LLM|model|token)" | tail -50
```

---

## Health Checks

```bash
# Quick health check all services
docker-compose ps

# Backend API health
curl http://localhost:8000/health

# Database health
docker-compose exec postgres pg_isready

# Redis health
docker-compose exec redis redis-cli ping

# Ollama health
curl http://localhost:11434/api/tags

# Comprehensive health check
./scripts/maintenance/verify-complete-setup.sh
```

---

## Database Quick Queries

```bash
# Count documents
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM documents;"

# Count processed documents
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM documents WHERE processed=true;"

# Count chunks with embeddings
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL;"

# Recent documents
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT filename, processed, upload_date FROM documents ORDER BY upload_date DESC LIMIT 10;"

# Recent sessions
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT session_id, created_at FROM chat_sessions ORDER BY created_at DESC LIMIT 10;"

# Failed documents
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT filename, processing_error FROM documents WHERE processed=false AND processing_error IS NOT NULL;"
```

---

## Testing Quick Commands

```bash
# Comprehensive system test
./test_comprehensive_chatbot.sh

# Test RAG pipeline
cd backend && python test_rag_pipeline.py

# Test Project Estimator
./test_project_estimator.sh

# Test document upload
./scripts/testing/test-upload-endpoint.sh

# Debug RAG with specific query
cd backend && python debug_rag_pipeline.py "your query here"

# Test vector search
cd backend && python test_vector_search.py
```

---

## Cache Management

```bash
# Clear all Redis cache
docker-compose exec redis redis-cli FLUSHALL

# Clear query cache only
docker-compose exec redis redis-cli KEYS "query:*" | xargs docker-compose exec redis redis-cli DEL

# View cache stats
docker-compose exec redis redis-cli INFO stats

# Monitor cache in real-time
docker-compose exec redis redis-cli MONITOR
```

---

## Service Control

```bash
# Restart backend only
docker-compose restart backend

# Rebuild and restart backend
docker-compose build backend && docker-compose up -d backend

# View service resource usage
docker stats --no-stream

# Stop all services
docker-compose down

# Start all services
docker-compose up -d
```

---

## Debugging Commands

```bash
# Access backend shell
docker-compose exec backend bash

# Access database shell
docker-compose exec postgres psql -U postgres ragchatbot

# Access Redis CLI
docker-compose exec redis redis-cli

# View container logs with timestamps
docker-compose logs --timestamps backend | tail -100

# Copy file from container
docker cp chatbot_backend_1:/tmp/output.json ./

# View resource usage
docker stats
```

---

## Most Common Debugging Scenarios

### Empty Chat Responses

```bash
# 1. Check if documents are processed
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM documents WHERE processed=true;"

# 2. Check if embeddings exist
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL;"

# 3. Debug RAG pipeline
cd backend && python debug_rag_pipeline.py "test query"

# 4. Check logs
docker-compose logs backend | grep -E "(retrieval|embedding)" | tail -50
```

### Service Won't Start

```bash
# 1. Check logs
docker-compose logs backend | tail -100

# 2. Check dependencies
docker-compose ps

# 3. Restart with fresh build
docker-compose down && docker-compose build backend && docker-compose up -d

# 4. Check port conflicts
netstat -tulpn | grep 8000
```

### Slow Responses

```bash
# 1. Check resource usage
docker stats --no-stream

# 2. Check database performance
docker-compose logs postgres | grep "duration:"

# 3. Check cache hit rate
docker-compose exec redis redis-cli INFO stats | grep keyspace

# 4. Monitor in real-time
watch -n 2 'docker stats --no-stream'
```

### Document Processing Fails

```bash
# 1. Check failed documents
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT filename, processing_error FROM documents WHERE processed=false;"

# 2. Check document service logs
docker-compose logs backend | grep -E "(document|chunk|error)" | tail -100

# 3. Check MinIO connectivity
curl http://localhost:9000/minio/health/live

# 4. Restart processing
docker-compose restart backend
```

---

## Performance Monitoring

```bash
# Watch system resources
watch -n 2 'docker stats --no-stream'

# Monitor query latency
docker-compose logs backend | grep "latency" | tail -20

# Monitor database connections
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM pg_stat_activity;"

# Monitor Redis memory
watch -n 2 'docker-compose exec redis redis-cli INFO memory | grep used_memory_human'
```

---

## Data Management

```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres ragchatbot > backup_$(date +%Y%m%d).sql

# Restore database
docker-compose exec -T postgres psql -U postgres ragchatbot < backup.sql

# Export documents list
docker-compose exec postgres psql -U postgres -d ragchatbot -c "COPY (SELECT * FROM documents) TO STDOUT CSV HEADER" > documents.csv

# Check disk usage
df -h
du -sh /var/lib/docker/volumes/
```

---

## API Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test query endpoint
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "session_id": "test-session"}'

# Test upload endpoint
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@test.pdf" \
  -F "session_id=test-session"

# Test scraping endpoint
curl -X POST http://localhost:8000/api/v1/scrape \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com"]}'

# List documents
curl http://localhost:8000/api/v1/documents?session_id=test-session
```

---

## Cleanup Commands

```bash
# Remove stopped containers
docker system prune -f

# Remove unused volumes (WARNING: deletes data)
docker volume prune -f

# Remove unused images
docker image prune -a -f

# Full cleanup (WARNING: deletes everything)
docker system prune -a -f --volumes

# Clean logs
truncate -s 0 /var/lib/docker/containers/*/*-json.log
```

---

## Development Workflow

```bash
# 1. Make code changes
# Edit files...

# 2. Rebuild affected service
docker-compose build backend

# 3. Restart service
docker-compose up -d backend

# 4. Watch logs
docker-compose logs -f backend

# 5. Test changes
./test_comprehensive_chatbot.sh

# 6. If issues, debug
cd backend && python debug_rag_pipeline.py "test"
```

---

## Project Estimator Quick Commands

```bash
# Test workflow
./test_project_estimator.sh

# Test with validation
cd backend && python test_project_estimator_validation.py

# Check workflow state files
ls -laht /tmp/project_estimator_states/ | head -10

# Monitor workflow execution
docker-compose logs backend | grep -E "(workflow|state|agent)" -f

# Test specific agent
curl -X POST http://localhost:8000/api/v1/project-estimator/analyze -F "file=@requirements.txt"
```

---

## Web Scraping Quick Commands

```bash
# Test scraper
cd backend && python test_scraper_text_extraction.py

# Inspect website
cd backend && python inspect_screener.py

# Test compliance
./docs/operations/scripts/testing/test_scraping_compliance.sh

# Test template extraction
./test_template_extraction_now.sh

# Check Playwright
docker-compose exec backend playwright --version
```

---

## Useful Aliases

Add to your `.bashrc` or `.zshrc`:

```bash
alias dcup='docker-compose up -d'
alias dcdown='docker-compose down'
alias dcrestart='docker-compose restart'
alias dclogs='docker-compose logs -f backend'
alias dcps='docker-compose ps'
alias dcbuild='docker-compose build backend && docker-compose up -d backend'

alias be='docker-compose exec backend'
alias db='docker-compose exec postgres psql -U postgres ragchatbot'
alias redis='docker-compose exec redis redis-cli'

alias errors='docker-compose logs backend | grep ERROR | tail -50'
alias health='curl -s http://localhost:8000/health | jq'
alias testrag='cd backend && python debug_rag_pipeline.py'
```

---

## Environment Variables Quick Reference

```bash
# View current environment
docker-compose exec backend env | grep -E "(OPENAI|ANTHROPIC|POSTGRES|REDIS)"

# Set temporary variable
docker-compose exec backend bash -c "export VAR=value && python script.py"

# Update .env file
nano .env
docker-compose down && docker-compose up -d
```

---

## Network Debugging

```bash
# Check if backend is accessible from frontend
docker-compose exec frontend curl http://backend:8000/health

# Check if backend is accessible from host
curl http://localhost:8000/health

# Check network connectivity
docker network inspect chatbot_default

# Check DNS resolution
docker-compose exec backend nslookup postgres
```

---

## Security Quick Checks

```bash
# Check for exposed secrets
grep -r "sk-" .env backend/

# Check API key configuration
docker-compose exec backend env | grep API_KEY

# Check database permissions
docker-compose exec postgres psql -U postgres -d ragchatbot -c "\du"

# Check Redis security
docker-compose exec redis redis-cli CONFIG GET requirepass
```

---

## Common Error Messages and Fixes

| Error | Quick Fix |
|-------|-----------|
| "Connection refused" | `docker-compose restart backend` |
| "Database does not exist" | `./scripts/setup/setup-database.sh` |
| "No embeddings found" | `cd backend && python regenerate_embeddings.py` |
| "Model not found" | Check API keys, verify model name |
| "Timeout" | Increase timeout in config, check resources |
| "Out of memory" | `docker-compose restart`, increase limits |
| "Port already in use" | Stop conflicting service, change port |
| "CORS error" | Check CORS settings in backend |

---

## Related Documentation

- **Full Operations Guide**: `docs/operations/guides/OPERATIONS_GUIDE.md`
- **Script Inventory**: `docs/operations/scripts/README.md`
- **RAG Debugging**: `docs/debugging/RAG_DEBUGGING_GUIDE.md`
- **Testing Guide**: `docs/testing/TESTING_GUIDE.md`

---

**Last Updated**: 2025-11-27
**Version**: 1.0
