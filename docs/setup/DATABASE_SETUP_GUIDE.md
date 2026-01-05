# Enterprise RAG Chatbot - Database Setup Guide

> **Last Updated**: 2026-01-05
> **Purpose**: Complete guide for database initialization on fresh installations

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Database Architecture](#database-architecture)
4. [Setup Script Details](#setup-script-details)
5. [Organizational Hierarchy](#organizational-hierarchy)
6. [Default Credentials](#default-credentials)
7. [Table Reference](#table-reference)
8. [Troubleshooting](#troubleshooting)
9. [Manual Setup](#manual-setup)

---

## Overview

The Enterprise RAG Chatbot uses PostgreSQL with pgvector extension for document storage, vector embeddings, and comprehensive RBAC (Role-Based Access Control). The database includes:

- **90+ tables** organized into functional modules
- **Organizational hierarchy** with departments, teams, roles
- **RBAC system** with fine-grained permissions
- **Vector storage** for semantic search (384-dimensional embeddings)
- **Audit logging** for compliance and security
- **Module management** for Tier 2/3 features
- **Fine-tuning system** for model training
- **Export wizard** for POC-to-production deployment

---

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- PostgreSQL container running
- Migrations directory available at `backend/migrations/`

### One-Command Setup

```bash
# Navigate to project root
cd /mnt/c/AIML/ClaudeCode/chatbot/ChatBot

# Run the comprehensive setup script
./scripts/setup/setup-database-complete.sh
```

### Options

```bash
# Skip confirmation prompts (useful for automation)
./scripts/setup/setup-database-complete.sh --skip-confirmation

# Verbose output (show detailed SQL execution)
./scripts/setup/setup-database-complete.sh --verbose

# Both options
./scripts/setup/setup-database-complete.sh --skip-confirmation --verbose

# Show help
./scripts/setup/setup-database-complete.sh --help
```

---

## Database Architecture

### Core Components

```
PostgreSQL Database: ragchatbot
├── Extensions
│   ├── uuid-ossp (UUID generation)
│   └── pgvector (vector similarity search)
│
├── Base Tables (000-003)
│   ├── documents (uploaded/scraped files)
│   ├── document_chunks (text chunks with embeddings)
│   ├── conversations (chat sessions)
│   ├── messages (chat messages)
│   ├── web_scrape_jobs (web scraping tasks)
│   └── query_cache (semantic cache)
│
├── RBAC & Security (001, 006-007)
│   ├── users (user accounts)
│   ├── api_keys (API authentication)
│   ├── roles (RBAC roles)
│   ├── departments (organizational units)
│   ├── teams (sub-units within departments)
│   ├── modules (application features)
│   ├── role_module_permissions (role-module access)
│   └── user_roles (user-role assignments)
│
├── Session Management (001)
│   ├── chat_sessions (session metadata)
│   ├── session_documents (short-term memory)
│   ├── conversation_messages (chat messages)
│   └── session_contexts (session preferences)
│
├── Audit & Analytics (001, 010-011)
│   ├── audit_logs (comprehensive audit trail)
│   └── usage_metrics (usage analytics)
│
├── Project Management (006-013)
│   ├── projects (project organization)
│   ├── project_members (project team members)
│   └── prompt_library (reusable prompts)
│
├── Agent Tasks (013-014)
│   └── agent_tasks (LangGraph agent tracking)
│
├── Evaluation System (001, 018)
│   ├── evaluation_configs (evaluation settings)
│   ├── evaluation_results (RAG evaluation metrics)
│   ├── evaluation_cache (cached results)
│   ├── human_feedback (user feedback)
│   └── evaluation_benchmarks (benchmark datasets)
│
├── Fine-Tuning System (019-023)
│   ├── finetuning_datasets (training datasets)
│   ├── finetuning_jobs (training jobs)
│   ├── finetuned_models (model registry)
│   ├── training_metrics (training metrics)
│   ├── training_checkpoints (model checkpoints)
│   └── model_approvals (approval workflow)
│
├── Module Management (024)
│   ├── modules (Tier 2/3 module registry)
│   ├── role_module_permissions (RBAC for modules)
│   ├── user_module_overrides (user-specific access)
│   └── module_usage_logs (usage tracking)
│
├── Dynamic Configuration (025)
│   ├── module_configurations (module configs)
│   ├── module_user_overrides (user overrides)
│   ├── config_versions (version history)
│   ├── config_schemas (JSON schemas)
│   ├── config_templates (reusable templates)
│   └── config_audit_logs (config changes audit)
│
└── Export Wizard (026)
    ├── export_jobs (export job tracking)
    ├── export_packages (exported packages)
    ├── export_templates (export templates)
    ├── deployment_instances (deployed instances)
    └── export_audit_logs (export audit trail)
```

---

## Setup Script Details

The `setup-database-complete.sh` script performs the following steps:

### Step-by-Step Execution

| Step | Description | Key Actions |
|------|-------------|-------------|
| 1 | Prerequisites Check | Verify Docker, PostgreSQL container |
| 2 | Database Creation | Create `ragchatbot` DB, enable extensions |
| 3 | Base Schema | Documents, chunks, conversations, cache |
| 4 | Enhanced Tables | Users, sessions, audit logs |
| 5 | Core Fixes | Embedding dimensions, query cache |
| 6 | Feature Tables | Scraping, API credentials, tools |
| 7 | RBAC Setup | Roles, departments, modules, permissions |
| 8 | Organizational Hierarchy | Departments, teams, hierarchy |
| 9 | Audit Enhancements | Action types, comprehensive logging |
| 10 | Project Management | Projects, members, prompts |
| 11 | Agent Tasks | LangGraph task tracking |
| 12 | Schema Fixes | Various FK and type fixes |
| 13 | Evaluation System | RAG evaluation, benchmarks |
| 14 | Fine-Tuning | Model training infrastructure |
| 15 | Module Management | Tier 2/3 module RBAC |
| 16 | Dynamic Config | Configuration system |
| 17 | Export Wizard | POC-to-production export |
| 18 | Additional Features | Extraction templates, scraping |
| 19 | Vector Indexes | Performance optimization |
| 20 | Default Admin User | Create admin account |
| 21 | Verification | Verify all tables created |
| 22 | Statistics | Display counts and metrics |
| 23 | Hierarchy Display | Show departments and teams |

### Execution Time

- **Small Installation**: 30-60 seconds
- **With Verbose Output**: 1-2 minutes

---

## Organizational Hierarchy

### Default Departments

1. **Data Operations** (DATA_OPS)
   - Data Team 1 through Data Team 16 (16 teams)
   - Focus: Data science, analytics, data engineering

2. **Technology** (TECH)
   - Tech Team 1 through Tech Team 12 (12 teams)
   - Focus: Software engineering, IT operations

3. **Marketing** (MARKETING)
   - Marketing Team
   - Focus: Marketing, communications

4. **Sales** (SALES)
   - Sales Team
   - Focus: Sales, business development

5. **HR** (HR)
   - HR Team
   - Focus: Human resources, people operations

6. **Finance** (FINANCE)
   - Finance Team
   - Focus: Finance, accounting

7. **General** (GENERAL)
   - Legacy Team
   - Focus: Uncategorized/legacy operations

### Default Roles

| Role | Description | Access Level |
|------|-------------|--------------|
| **Admin** | Full system access | All permissions (CRUD on all resources) |
| **CxO** | Executive access | Read all, write to analytics/reports |
| **Manager** | Department manager | Manage team resources, no admin panel |
| **User** | Standard user | Core features (RAG, upload, scraping) |
| **ReadOnly** | View-only access | Read-only on most features |

### Permissions Matrix

| Module | Admin | CxO | Manager | User | ReadOnly |
|--------|-------|-----|---------|------|----------|
| RAG Chat | CRUD | RW | RW | RW | R |
| File Upload | CRUD | R | CRD | CRD | R |
| Web Scraping | CRUD | R | CRD | RW | R |
| Data Extraction | CRUD | R | CRD | RW | R |
| Admin Panel | CRUD | - | - | - | - |
| Audit Logs | CRUD | R | - | - | - |
| Evaluation Metrics | CRUD | RW | R | R | R |

*Legend: C=Create, R=Read, U=Update, D=Delete, W=Write*

---

## Default Credentials

### Admin User

After running the setup script, you can log in with:

```
Username: admin
Email: admin@enterprise-rag.local
Password: admin123
Role: admin
```

**⚠️ IMPORTANT**: Change this password immediately in production!

### Changing Default Password

```bash
# Option 1: Via database
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
UPDATE users
SET hashed_password = '<new_bcrypt_hash>'
WHERE username = 'admin';
"

# Option 2: Via API (after backend is running)
curl -X POST http://localhost:8000/api/v1/users/change-password \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "admin123",
    "new_password": "<your_secure_password>"
  }'
```

### Generating Bcrypt Hash (Python)

```python
import bcrypt
password = "your_secure_password"
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
print(hashed.decode())
```

---

## Table Reference

### Critical Tables with Indexes

#### documents
- **Indexes**: created_at, source_type, processing_status, department_id, team_id, project_id
- **Purpose**: Store uploaded/scraped documents
- **Key Fields**: filename, file_path, file_type, file_size, minio_path

#### document_chunks
- **Indexes**: document_id, embedding (ivfflat), department_id, team_id
- **Purpose**: Text chunks with 384-dim vector embeddings
- **Key Fields**: content, embedding, table_embedding, visual_embedding

#### users
- **Indexes**: username, email, department_id, team_id
- **Purpose**: User accounts with RBAC
- **Key Fields**: username, email, role, department_id, default_project_id

#### chat_sessions
- **Indexes**: session_id, user_id, project_id, department_id
- **Purpose**: Chat session management
- **Key Fields**: session_id, user_id, project_id, title

#### audit_logs
- **Indexes**: user_id, session_id, action, created_at
- **Purpose**: Comprehensive audit trail
- **Key Fields**: action, resource_type, ip_address, latency_ms

### Vector Index Performance

The vector index on `document_chunks.embedding` uses IVFFlat algorithm:

```sql
CREATE INDEX idx_chunks_embedding ON document_chunks
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

- **Type**: IVFFlat (Inverted File with Flat compression)
- **Distance**: Cosine similarity
- **Lists**: 100 (recommended for <1M vectors)
- **Performance**: Sub-second queries on millions of chunks

---

## Troubleshooting

### Issue 1: PostgreSQL Container Not Running

**Error**: `PostgreSQL container 'rag-postgres' is not running`

**Solution**:
```bash
docker-compose up -d postgres
# Wait 10 seconds for initialization
sleep 10
./scripts/setup/setup-database-complete.sh
```

### Issue 2: Database Already Exists

**Warning**: `Database 'ragchatbot' already exists`

**Solution**: The script will use the existing database. If you want a fresh start:

```bash
# CAUTION: This deletes ALL data!
docker exec rag-postgres psql -U postgres -c "DROP DATABASE IF EXISTS ragchatbot;"
./scripts/setup/setup-database-complete.sh
```

### Issue 3: Migration File Not Found

**Error**: `Migration file not found: backend/migrations/XXX.sql`

**Solution**: Check migrations directory structure:

```bash
ls -la backend/migrations/
```

Ensure all required migration files exist. If missing, check the git repository.

### Issue 4: Extension Installation Fails

**Error**: `ERROR: could not open extension control file`

**Solution**: Ensure you're using the correct PostgreSQL image with pgvector:

```yaml
# docker-compose.yml
postgres:
  image: pgvector/pgvector:pg16
  # OR
  image: ankane/pgvector:latest
```

### Issue 5: Permission Denied on Script

**Error**: `Permission denied: ./scripts/setup/setup-database-complete.sh`

**Solution**:
```bash
chmod +x ./scripts/setup/setup-database-complete.sh
./scripts/setup/setup-database-complete.sh
```

### Issue 6: Vector Index Creation Fails

**Warning**: `No embeddings found - vector index will be created automatically`

**Solution**: This is normal on fresh installations. The index will be created when embeddings are added. To verify later:

```bash
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'document_chunks' AND indexname LIKE '%embedding%';
"
```

---

## Manual Setup

If you need to run migrations manually or in a specific order:

### 1. Create Database

```bash
docker exec rag-postgres psql -U postgres -c "CREATE DATABASE ragchatbot;"
docker exec rag-postgres psql -U postgres -d ragchatbot -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
docker exec rag-postgres psql -U postgres -d ragchatbot -c "CREATE EXTENSION IF NOT EXISTS \"vector\";"
```

### 2. Apply Migrations Sequentially

```bash
cd backend/migrations

# Base schema
docker exec -i rag-postgres psql -U postgres -d ragchatbot < 000_base_schema.sql

# Enhanced tables
docker exec -i rag-postgres psql -U postgres -d ragchatbot < 001_add_rbac_and_audit.sql

# Fixes
docker exec -i rag-postgres psql -U postgres -d ragchatbot < 002_fix_embedding_dimensions.sql
docker exec -i rag-postgres psql -U postgres -d ragchatbot < 003_fix_query_cache_default.sql

# Continue with remaining migrations...
```

### 3. Create Admin User Manually

```bash
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
INSERT INTO users (username, email, full_name, hashed_password, role, is_active, is_verified)
VALUES (
    'admin',
    'admin@enterprise-rag.local',
    'System Administrator',
    '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eo7gy7SG6sgu',
    'admin',
    true,
    true
);
"
```

### 4. Verify Installation

```bash
# Check table count
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT COUNT(*) AS table_count
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
"

# List all tables
docker exec rag-postgres psql -U postgres -d ragchatbot -c "\dt"

# Verify critical data
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT
    (SELECT COUNT(*) FROM users) AS users,
    (SELECT COUNT(*) FROM roles) AS roles,
    (SELECT COUNT(*) FROM departments) AS departments,
    (SELECT COUNT(*) FROM teams) AS teams,
    (SELECT COUNT(*) FROM modules) AS modules;
"
```

---

## Post-Setup Steps

### 1. Restart Backend

```bash
docker-compose restart backend
```

### 2. Verify Backend Connection

```bash
# Check backend logs
docker-compose logs backend | grep -E "Application startup|Database|Connected"

# Expected output:
# INFO:     Application startup complete.
# INFO:     Database connected: ragchatbot
```

### 3. Test Database Access

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","database":"connected"}
```

### 4. Access UI

- **Frontend**: http://localhost:3001
- **API Docs**: http://localhost:8000/api/docs
- **GraphQL**: http://localhost:8000/graphql

### 5. Upload Test Document

```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@test.pdf" \
  -F "session_id=test-session-123"
```

---

## Database Backup and Restore

### Backup

```bash
# Full database backup
docker exec rag-postgres pg_dump -U postgres ragchatbot > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
docker exec rag-postgres pg_dump -U postgres ragchatbot | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Schema only (no data)
docker exec rag-postgres pg_dump -U postgres --schema-only ragchatbot > schema_backup.sql

# Data only (no schema)
docker exec rag-postgres pg_dump -U postgres --data-only ragchatbot > data_backup.sql
```

### Restore

```bash
# Restore from backup
docker exec -i rag-postgres psql -U postgres ragchatbot < backup_20260105_120000.sql

# Restore from compressed backup
gunzip -c backup_20260105_120000.sql.gz | docker exec -i rag-postgres psql -U postgres ragchatbot
```

---

## Maintenance Commands

### Vacuum and Analyze

```bash
# Optimize database performance
docker exec rag-postgres psql -U postgres -d ragchatbot -c "VACUUM ANALYZE;"

# Detailed analysis
docker exec rag-postgres psql -U postgres -d ragchatbot -c "VACUUM (VERBOSE, ANALYZE);"
```

### Check Database Size

```bash
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
WHERE datname = 'ragchatbot';
"
```

### Check Table Sizes

```bash
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY size_bytes DESC
LIMIT 20;
"
```

---

## References

- **CLAUDE.md**: Project overview and architecture
- **Migration Files**: `backend/migrations/*.sql`
- **Model Definitions**: `backend/app/models/`
- **pgvector Documentation**: https://github.com/pgvector/pgvector
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/

---

## Support

For issues or questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review backend logs: `docker-compose logs backend`
3. Run diagnostics: `./scripts/debugging/diagnose-backend.sh`
4. Check database status: `./scripts/maintenance/validate-services.sh`

---

**Last Updated**: 2026-01-05
**Version**: 2.0
**Maintainer**: Enterprise RAG Team
