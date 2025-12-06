# Complete Installation & Database Setup Guide

**Version**: 1.0.0
**Date**: 2025-12-06
**Platform**: Docker Compose / Kubernetes
**Supported OS**: Linux, macOS, Windows (WSL2)

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (5 Minutes)](#quick-start-5-minutes)
3. [Detailed Installation](#detailed-installation)
4. [Database Setup](#database-setup)
5. [Configuration](#configuration)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Setup](#advanced-setup)
9. [Production Deployment](#production-deployment)

---

## Prerequisites

### Required Software

| Software | Minimum Version | Purpose | Installation |
|----------|----------------|---------|--------------|
| **Docker** | 24.0+ | Container runtime | [docker.com](https://docs.docker.com/get-docker/) |
| **Docker Compose** | 2.20+ | Multi-container orchestration | Included with Docker Desktop |
| **Git** | 2.30+ | Source control | [git-scm.com](https://git-scm.com/downloads) |

### Optional (Recommended)

| Software | Purpose | Installation |
|----------|---------|--------------|
| **Make** | Simplified commands | Linux/macOS: pre-installed, Windows: `choco install make` |
| **jq** | JSON processing | `apt install jq` / `brew install jq` |
| **curl** | API testing | Pre-installed on most systems |

### System Requirements

#### Minimum (Development)
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disk**: 20 GB free space
- **Network**: Broadband internet (for downloading Docker images)

#### Recommended (Production)
- **CPU**: 8+ cores
- **RAM**: 16+ GB
- **Disk**: 100+ GB SSD
- **Network**: Low latency, high bandwidth
- **GPU** (optional): NVIDIA GPU with CUDA support for local LLM acceleration

### API Keys (Optional but Recommended)

| Service | Purpose | Cost | Sign Up |
|---------|---------|------|---------|
| **OpenAI** | GPT-4o, GPT-4o-mini | $0.15/1M tokens | [platform.openai.com](https://platform.openai.com) |
| **Anthropic** | Claude 3.5 Sonnet | $3/1M tokens | [console.anthropic.com](https://console.anthropic.com) |
| **HuggingFace** | Model downloads | Free | [huggingface.co](https://huggingface.co) |

**Note**: The system can run fully locally with Ollama (no API keys required).

---

## Quick Start (5 Minutes)

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd ChatBot
```

### Step 2: Copy Environment File

```bash
cp .env.example .env
```

### Step 3: (Optional) Add API Keys

Edit `.env` file:

```bash
# Recommended: Add at least one LLM provider
OPENAI_API_KEY=sk-proj-...          # For GPT-4o-mini (cheapest)
# OR
ANTHROPIC_API_KEY=sk-ant-...        # For Claude 3.5 Sonnet

# Optional: For local LLM models
HUGGING_FACE_HUB_TOKEN=hf_...
```

### Step 4: Start Services

```bash
# Using Make (recommended)
make up

# OR using Docker Compose directly
docker-compose up -d
```

### Step 5: Initialize Database

```bash
# Wait for PostgreSQL to be ready (10-15 seconds)
sleep 15

# Run database migrations
docker-compose exec backend python -c "
from app.core.database import init_db
import asyncio
asyncio.run(init_db())
"
```

### Step 6: Access Application

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3001 | No login required |
| **Backend API** | http://localhost:8000 | - |
| **API Docs** | http://localhost:8000/api/docs | - |
| **GraphQL** | http://localhost:8000/graphql | - |
| **Grafana** | http://localhost:3000 | admin / admin |
| **MinIO Console** | http://localhost:9001 | minioadmin / minioadmin |

### Step 7: Test Upload & Query

```bash
# Test document upload
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@sample.pdf" \
  -F "session_id=test_session"

# Test query
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=What is in the document?" \
  -F "session_id=test_session" \
  -F "model=gpt-4o-mini"
```

**✅ Installation Complete!** Your RAG chatbot is now running.

---

## Detailed Installation

### 1. Clone and Navigate

```bash
# Clone repository
git clone <repository-url>
cd ChatBot

# Check current directory
pwd
# Expected: /path/to/ChatBot
```

### 2. Environment Configuration

#### Copy Template

```bash
cp .env.example .env
```

#### Required Variables

Edit `.env` and configure:

```bash
# ========================================
# DATABASE CONFIGURATION (Required)
# ========================================
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres           # Change in production!
POSTGRES_DB=ragchatbot

# ========================================
# LLM API KEYS (At least one recommended)
# ========================================

# Option 1: OpenAI (Cheapest for GPT-4o-mini)
OPENAI_API_KEY=sk-proj-abc123...

# Option 2: Anthropic Claude (Best quality)
ANTHROPIC_API_KEY=sk-ant-abc123...

# Option 3: HuggingFace (For vLLM local models)
HUGGING_FACE_HUB_TOKEN=hf_abc123...

# ========================================
# REDIS CONFIGURATION
# ========================================
REDIS_PASSWORD=                      # Optional: Set password in production

# ========================================
# MINIO (Object Storage) CONFIGURATION
# ========================================
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin          # Change in production!

# ========================================
# APPLICATION CONFIGURATION
# ========================================
DEBUG=true                           # Set to false in production
ENABLE_TRACING=true                  # OpenTelemetry tracing

# ========================================
# FRONTEND CONFIGURATION
# ========================================
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GRAPHQL_URL=http://localhost:8000/graphql

# ========================================
# AGENT CONFIGURATION (Advanced)
# ========================================
AGENT_MODE_ENABLED=true
DAILY_API_BUDGET_LIMIT=10.0         # Daily budget cap ($USD)
MONTHLY_API_BUDGET_LIMIT=200.0      # Monthly budget cap ($USD)
AGENT_CODE_MODEL=qwen2.5-coder:7b   # Ollama model for agents
```

#### Optional: Master Encryption Key

For encrypting API keys in database:

```bash
# Generate random 32-byte key
MASTER_ENCRYPTION_KEY=$(openssl rand -hex 32)
echo "MASTER_ENCRYPTION_KEY=$MASTER_ENCRYPTION_KEY" >> .env
```

### 3. Build and Start Services

#### Using Make (Recommended)

```bash
# Build images
make build

# Start all services
make up

# Check status
make status

# View logs
make logs
```

#### Using Docker Compose

```bash
# Build images
docker-compose build

# Start services (detached mode)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 4. Wait for Services

```bash
# Wait for all services to be healthy (60-90 seconds)
./scripts/wait-for-services.sh

# OR manually check
docker-compose ps
```

Expected output:
```
NAME                    STATUS
rag-backend             Up (healthy)
rag-frontend            Up
rag-postgres            Up (healthy)
rag-redis               Up (healthy)
rag-minio               Up (healthy)
rag-ollama              Up (healthy)
rag-grafana             Up
rag-tempo               Up
rag-loki                Up
rag-prometheus          Up
```

---

## Database Setup

### Database Architecture

The database schema consists of:
- **Core tables**: 10 tables (documents, chunks, conversations, etc.)
- **RBAC tables**: 8 tables (users, roles, permissions, departments, teams)
- **Audit tables**: 3 tables (audit logs, usage metrics, tool tracking)
- **Project tables**: 4 tables (projects, modules, prompt library)
- **Advanced features**: 5+ tables (agents, scraping, templates)

**Total**: 30+ tables

### Migration Files (34 migrations)

Migrations are located in `backend/migrations/` and applied in order:

| Migration | Description | Tables Created |
|-----------|-------------|----------------|
| `000_base_schema.sql` | Core RAG tables | documents, document_chunks, conversations, messages, query_cache |
| `001_add_rbac_and_audit.sql` | Security & logging | users, audit_logs, usage_metrics |
| `002_fix_embedding_dimensions.sql` | Update embeddings from 1536→384 | - |
| `003_fix_query_cache_default.sql` | Fix cache defaults | - |
| `004_add_api_credentials.sql` | Encrypted API keys | api_credentials |
| `004_add_scraping_configs.sql` | Web scraping | scraping_configs |
| `004_add_saved_css_templates.sql` | CSS templates | saved_css_templates |
| `005_add_tool_usage_tracking.sql` | Tool analytics | tool_usage_stats |
| `006_add_modules_and_projects.sql` | Project management | projects, modules |
| `006_add_rbac_tables.sql` | RBAC system | roles, permissions, departments, teams |
| `007_add_project_tracking.sql` | Project tracking | - |
| `007_seed_rbac_data.sql` | Default roles & permissions | - |
| `008_normalize_departments_teams.sql` | Org structure | - |
| `009_rename_data_ops_teams.sql` | Team renaming | - |
| `010_enhance_audit_action_types.sql` | Audit actions | - |
| `011_add_missing_action_types.sql` | More audit actions | - |
| `012_add_default_project.sql` | Global project | - |
| `012_add_project_based_scraping.sql` | Project scraping | - |
| `012_add_project_to_sessions.sql` | Session projects | - |
| `012_add_prompt_library_and_templates.sql` | Prompt library | prompt_library, prompt_templates |
| `013_add_agent_tasks_table.sql` | Agent tracking | agent_tasks |
| `014_fix_file_type_length.sql` | Field size fix | - |
| `015_fix_query_cache_schema.sql` | Cache schema fix | - |
| `016_add_multi_column_vector_storage.sql` | 5 vector columns | - |
| `017_fix_session_documents_session_id_type.sql` | FK fix | - |

### Method 1: Automatic Migration (Recommended)

The backend automatically runs migrations on startup:

```bash
# Start services
docker-compose up -d

# Backend will log:
# "Running database migrations..."
# "✅ Database migrations complete"

# Verify logs
docker-compose logs backend | grep -i migration
```

### Method 2: Manual Migration

```bash
# Connect to backend container
docker-compose exec backend bash

# Run migrations manually
cd /app
python -c "
from app.core.database import init_db
import asyncio
asyncio.run(init_db())
"

# Exit container
exit
```

### Method 3: SQL Files Directly

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d ragchatbot

# Run each migration file in order
\i /app/migrations/000_base_schema.sql
\i /app/migrations/001_add_rbac_and_audit.sql
\i /app/migrations/002_fix_embedding_dimensions.sql
-- ... (continue for all migrations)

# Exit PostgreSQL
\q
```

### Verify Database Setup

```bash
# Check tables exist
docker-compose exec postgres psql -U postgres -d ragchatbot -c "\dt"

# Expected output (30+ tables):
# documents, document_chunks, users, roles, permissions,
# departments, teams, projects, modules, audit_logs,
# usage_metrics, tool_usage_stats, agent_tasks, etc.

# Check pgvector extension
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT * FROM pg_extension WHERE extname='vector';"

# Check vector indexes
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT tablename, indexname
FROM pg_indexes
WHERE indexname LIKE '%embedding%';
"

# Expected:
# document_chunks | idx_document_chunks_embedding
# document_chunks | idx_chunks_visual_embedding
# document_chunks | idx_chunks_table_embedding
# query_cache     | idx_query_cache_embedding
```

### Create Admin User

```bash
# Option 1: Using Python script
docker-compose exec backend python create_admin_user.py

# Option 2: Using SQL
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
INSERT INTO users (username, email, role, is_active)
VALUES ('admin', 'admin@example.com', 'super_admin', true)
ON CONFLICT (username) DO NOTHING;
"

# Verify
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT username, email, role FROM users WHERE role = 'super_admin';
"
```

### Seed Demo Data (Optional)

```bash
# Upload sample document
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@README.md" \
  -F "session_id=demo_session"

# Create sample project
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
INSERT INTO projects (name, description, department, team)
VALUES ('Demo Project', 'Sample project for testing', 'Technology', 'Tech Team 1')
ON CONFLICT DO NOTHING;
"
```

---

## Configuration

### Backend Configuration

Key configuration files:

1. **`backend/app/core/config.py`**
   - Database connection
   - MinIO settings
   - LLM endpoints
   - Feature flags

2. **`backend/app/config/weights_config.yaml`**
   - RAG strategy weights
   - Query classification thresholds
   - Similarity thresholds
   - Reranking weights
   - Brain View toggle

Example `weights_config.yaml`:

```yaml
strategy_weights:
  conversation_only: 1.0        # Highest priority
  rag_short_term: 0.95          # Session documents
  rag_hybrid: 0.90              # Short + long term
  rag_long_term: 0.80           # All documents
  direct_llm: 0.75              # General knowledge
  enable_brain_view: false      # Debug context (default: off)

rag_settings:
  top_k: 5                      # Number of chunks to retrieve
  chunk_size: 800               # Chunk size in characters
  chunk_overlap: 150            # Overlap between chunks
  no_relevant_docs_threshold: 0.35  # Threshold for "no answer"

similarity_thresholds:
  default: 0.60                 # Default similarity threshold
  proper_nouns: 0.50            # For names, places
  short_query: 0.55             # For short queries
  minimum: 0.45                 # Absolute minimum
```

### Frontend Configuration

Key files:

1. **`frontend/next.config.js`**
   - Build configuration
   - Environment variables
   - Image optimization

2. **`frontend/src/components/WeightsConfigManager.tsx`**
   - User-facing RAG settings
   - Brain View toggle
   - Model selection

### Ollama Models

Pull models for local inference:

```bash
# Pull recommended models
docker-compose exec ollama ollama pull qwen2.5-coder:7b
docker-compose exec ollama ollama pull llama3.1:8b
docker-compose exec ollama ollama pull mistral:7b

# List installed models
docker-compose exec ollama ollama list

# Test model
docker-compose exec ollama ollama run qwen2.5-coder:7b "Hello, write a Python function"
```

### MinIO Buckets

MinIO automatically creates buckets on startup. Verify:

```bash
# Access MinIO Console
open http://localhost:9001
# Login: minioadmin / minioadmin

# OR use CLI
docker-compose exec minio mc alias set local http://localhost:9000 minioadmin minioadmin
docker-compose exec minio mc ls local/

# Expected output:
# ragchatbot/  (main bucket)
```

---

## Verification

### 1. Health Checks

```bash
# Check all services
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "redis": "connected",
    "minio": "connected",
    "ollama": "connected"
  }
}
```

### 2. Test Document Upload

```bash
# Create test file
echo "This is a test document for RAG system" > test.txt

# Upload
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@test.txt" \
  -F "session_id=verify_session" \
  | jq .

# Expected response:
{
  "document_id": "uuid-here",
  "filename": "test.txt",
  "status": "processing",
  "message": "Document uploaded successfully"
}
```

### 3. Wait for Processing

```bash
# Check document status (poll every 2 seconds)
while true; do
  STATUS=$(curl -s http://localhost:8000/api/v1/documents | jq -r '.documents[0].processing_status')
  echo "Status: $STATUS"
  [ "$STATUS" = "completed" ] && break
  sleep 2
done
```

### 4. Test Query

```bash
# Query the document
curl -X POST http://localhost:8000/api/v1/query \
  -F "query=What is this document about?" \
  -F "session_id=verify_session" \
  -F "model=gpt-4o-mini" \
  | jq .

# Expected response:
{
  "answer": "This document is about testing the RAG system...",
  "sources": [
    {
      "document_id": "uuid-here",
      "filename": "test.txt",
      "similarity_score": 0.95,
      "content": "This is a test document for RAG system"
    }
  ],
  "model_used": "gpt-4o-mini",
  "tokens_used": 123,
  "latency_ms": 1234.5
}
```

### 5. Test GraphQL

```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { documents { id filename fileType processingStatus } }"
  }' | jq .
```

### 6. Test Frontend

```bash
# Open browser
open http://localhost:3001

# Expected:
# - Chat interface loads
# - File upload widget visible
# - Model selector shows available models
# - Settings panel accessible
```

### 7. Test Agent Runtime

```bash
# Create agent task
curl -X POST http://localhost:8000/api/v1/agent/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "List files in /workspace",
    "session_id": "verify_session",
    "model": "qwen2.5-coder:7b"
  }' | jq .

# Get task status
TASK_ID=<task_id_from_response>
curl http://localhost:8000/api/v1/agent/tasks/$TASK_ID | jq .
```

---

## Troubleshooting

### Issue 1: Services Won't Start

**Symptom**: `docker-compose up` fails or services exit immediately

**Diagnosis**:
```bash
# Check logs
docker-compose logs

# Check specific service
docker-compose logs backend
docker-compose logs postgres
```

**Common Causes**:

1. **Port conflicts**:
   ```bash
   # Check if ports are in use
   lsof -i :8000  # Backend
   lsof -i :3001  # Frontend
   lsof -i :5433  # PostgreSQL

   # Kill conflicting process
   kill -9 <PID>
   ```

2. **Insufficient resources**:
   ```bash
   # Check Docker resources
   docker system df

   # Prune unused resources
   docker system prune -a
   ```

3. **Missing .env file**:
   ```bash
   # Copy template
   cp .env.example .env
   ```

### Issue 2: Database Migration Errors

**Symptom**: "relation already exists" or "column does not exist"

**Solution**:

```bash
# Reset database (WARNING: Deletes all data!)
docker-compose down -v
docker-compose up -d postgres
sleep 10

# Re-run migrations
docker-compose exec backend python -c "
from app.core.database import init_db
import asyncio
asyncio.run(init_db())
"
```

### Issue 3: Ollama Models Not Working

**Symptom**: "model not found" or connection errors

**Solution**:

```bash
# Check Ollama status
docker-compose logs ollama

# Pull model manually
docker-compose exec ollama ollama pull qwen2.5-coder:7b

# Verify model
docker-compose exec ollama ollama list

# Test model
curl http://localhost:11434/api/tags
```

### Issue 4: Frontend 404 Errors

**Symptom**: Frontend shows blank page or 404

**Solution**:

```bash
# Rebuild frontend
docker-compose build frontend --no-cache
docker-compose restart frontend

# Check logs
docker-compose logs frontend

# Clear browser cache
# Chrome: Ctrl+Shift+Delete
# Firefox: Ctrl+Shift+Delete
```

### Issue 5: MinIO Connection Errors

**Symptom**: "S3 error" or "MinIO connection refused"

**Solution**:

```bash
# Check MinIO status
docker-compose logs minio

# Restart MinIO
docker-compose restart minio

# Verify bucket
curl http://localhost:9000/minio/health/live
```

### Issue 6: Out of Memory

**Symptom**: Services killed or "Out of memory" errors

**Solution**:

```bash
# Increase Docker memory limit
# Docker Desktop → Settings → Resources → Memory → 8GB

# OR reduce service memory limits in docker-compose.yml
# backend:
#   deploy:
#     resources:
#       limits:
#         memory: 2G
```

### Issue 7: Slow Performance

**Diagnosis**:

```bash
# Check resource usage
docker stats

# Check database performance
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT schemaname, tablename, n_live_tup, n_dead_tup
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC
LIMIT 10;
"

# Check index usage
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY schemaname, tablename;
"
```

**Solutions**:

1. **Vacuum database**:
   ```bash
   docker-compose exec postgres psql -U postgres -d ragchatbot -c "VACUUM ANALYZE;"
   ```

2. **Clear old cache entries**:
   ```bash
   docker-compose exec redis redis-cli FLUSHDB
   ```

3. **Rebuild vector indexes**:
   ```bash
   docker-compose exec postgres psql -U postgres -d ragchatbot -c "
   REINDEX INDEX idx_document_chunks_embedding;
   "
   ```

---

## Advanced Setup

### GPU Support (Ollama with CUDA)

Edit `docker-compose.yml`:

```yaml
ollama:
  image: ollama/ollama:0.11.0
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

Verify GPU:

```bash
docker-compose exec ollama nvidia-smi
```

### External PostgreSQL

Edit `.env`:

```bash
# External PostgreSQL
POSTGRES_SERVER=postgres.example.com
POSTGRES_PORT=5432
POSTGRES_USER=rag_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=ragchatbot
```

Comment out `postgres` service in `docker-compose.yml`.

### External Redis

Edit `.env`:

```bash
# External Redis
REDIS_HOST=redis.example.com
REDIS_PORT=6379
REDIS_PASSWORD=secure_password
```

Comment out `redis` service in `docker-compose.yml`.

### SSL/TLS

1. **Generate certificates**:
   ```bash
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout nginx/ssl/key.pem \
     -out nginx/ssl/cert.pem
   ```

2. **Configure Nginx**:
   Create `nginx/nginx.conf`:
   ```nginx
   server {
     listen 443 ssl;
     server_name chat.example.com;

     ssl_certificate /etc/nginx/ssl/cert.pem;
     ssl_certificate_key /etc/nginx/ssl/key.pem;

     location / {
       proxy_pass http://frontend:3000;
     }

     location /api {
       proxy_pass http://backend:8000;
     }
   }
   ```

3. **Add to docker-compose.yml**:
   ```yaml
   nginx:
     image: nginx:alpine
     ports:
       - "443:443"
     volumes:
       - ./nginx/nginx.conf:/etc/nginx/nginx.conf
       - ./nginx/ssl:/etc/nginx/ssl
     depends_on:
       - frontend
       - backend
   ```

---

## Production Deployment

### Pre-Production Checklist

- [ ] Change default passwords (PostgreSQL, MinIO, Grafana)
- [ ] Set `DEBUG=false` in `.env`
- [ ] Configure SSL/TLS certificates
- [ ] Set up backup strategy (database, MinIO)
- [ ] Configure monitoring alerts (Grafana)
- [ ] Review RBAC permissions
- [ ] Enable rate limiting (API Gateway)
- [ ] Set up log rotation
- [ ] Configure secret management (Vault, AWS Secrets Manager)
- [ ] Test disaster recovery procedures

### Environment Variables (Production)

```bash
# Security
DEBUG=false
ENABLE_TRACING=true
MASTER_ENCRYPTION_KEY=<generated-32-byte-key>

# Database
POSTGRES_PASSWORD=<strong-random-password>
REDIS_PASSWORD=<strong-random-password>

# Object Storage
MINIO_ACCESS_KEY=<generated-access-key>
MINIO_SECRET_KEY=<generated-secret-key>

# API Keys
OPENAI_API_KEY=<production-key>
ANTHROPIC_API_KEY=<production-key>

# Budget Limits
DAILY_API_BUDGET_LIMIT=100.0
MONTHLY_API_BUDGET_LIMIT=2000.0
```

### Kubernetes Deployment

See `infrastructure/kubernetes/` for manifests:

```bash
# Apply base configuration
kubectl apply -k infrastructure/kubernetes/base/

# Apply production overlays
kubectl apply -k infrastructure/kubernetes/overlays/prod/

# Verify deployment
kubectl get pods -n rag-chatbot

# Check logs
kubectl logs -f deployment/rag-backend -n rag-chatbot
```

### Backup Strategy

#### Database Backup

```bash
# Automated daily backup
docker-compose exec postgres pg_dump -U postgres ragchatbot | gzip > backups/ragchatbot_$(date +%Y%m%d).sql.gz

# Restore from backup
gunzip -c backups/ragchatbot_20251206.sql.gz | docker-compose exec -T postgres psql -U postgres -d ragchatbot
```

#### MinIO Backup

```bash
# Sync to S3
docker-compose exec minio mc mirror local/ragchatbot s3://backup-bucket/ragchatbot
```

### Monitoring & Alerts

Configure Grafana alerts:

1. **High error rate**: >5% errors in 5 minutes
2. **High latency**: P95 >2s for 5 minutes
3. **Low cache hit ratio**: <70% for 10 minutes
4. **Database connection failures**: >10 failures in 5 minutes
5. **Disk usage**: >80% full

---

## Summary

### Quick Reference Commands

```bash
# Start
make up

# Stop
make down

# Restart
make restart

# Logs
make logs

# Status
make status

# Clean (remove volumes)
make down-v

# Rebuild
make rebuild

# Database shell
make db-shell

# Backend shell
make shell-backend

# Test
make test
```

### Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3001 | Chat interface |
| Backend API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/api/docs | Swagger UI |
| GraphQL | http://localhost:8000/graphql | GraphQL Playground |
| Grafana | http://localhost:3000 | Dashboards |
| MinIO | http://localhost:9001 | Object storage console |
| Prometheus | http://localhost:9090 | Metrics |
| Prefect | http://localhost:4200 | Workflow UI |

### Support & Documentation

- **Architecture**: `docs/architecture/COMPLETE_END_TO_END_ARCHITECTURE.md`
- **Quick Start**: `docs/guides/QUICKSTART.md`
- **Debugging**: `docs/debugging/DEBUG_QUICK_REFERENCE.md`
- **API Examples**: `docs/guides/GRAPHQL_EXAMPLES.md`
- **RBAC Guide**: `docs/features/RBAC_DEVELOPER_GUIDE.md`

---

**Installation Complete!** 🚀

For questions or issues, check the troubleshooting section or review the comprehensive architecture document.
