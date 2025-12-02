# Enterprise RAG Chatbot - Database Disaster Recovery Plan

**Date Created**: 2025-12-01
**Last Updated**: 2025-12-01
**Version**: 1.0
**Database**: PostgreSQL 16 with pgvector extension

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Database Architecture Overview](#database-architecture-overview)
3. [Prerequisites](#prerequisites)
4. [Complete Database Recovery Procedure](#complete-database-recovery-procedure)
5. [Migration Files Reference](#migration-files-reference)
6. [Schema Documentation](#schema-documentation)
7. [Data Backup Procedures](#data-backup-procedures)
8. [Data Restore Procedures](#data-restore-procedures)
9. [Frontend-Backend-DB Sync Requirements](#frontend-backend-db-sync-requirements)
10. [Validation & Testing](#validation--testing)
11. [Common Recovery Scenarios](#common-recovery-scenarios)
12. [Troubleshooting](#troubleshooting)
13. [Disaster Recovery Checklist](#disaster-recovery-checklist)

---

## Executive Summary

This document provides a comprehensive disaster recovery plan for the Enterprise RAG Chatbot database. It includes complete procedures for:

- **Full database restoration from scratch**
- **Schema recreation**
- **Data format and column mapping**
- **Frontend-backend-database synchronization**
- **Backup and restore procedures**
- **Validation and testing**

**Recovery Time Objective (RTO)**: < 30 minutes
**Recovery Point Objective (RPO)**: < 24 hours (with daily backups)

---

## Database Architecture Overview

### Technology Stack

- **Database**: PostgreSQL 16
- **Extensions**:
  - `uuid-ossp` - UUID generation
  - `vector` (pgvector) - Vector similarity search for embeddings
- **Vector Dimensions**: 384 (sentence-transformers/all-MiniLM-L6-v2)
- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions)

### Key Tables (28 Total)

#### Core Tables
1. **documents** - Uploaded/scraped documents
2. **document_chunks** - Text chunks with vector embeddings
3. **query_cache** - Semantic cache for queries

#### User & Auth Tables
4. **users** - User accounts with RBAC
5. **api_keys** - API authentication keys
6. **chat_sessions** - User chat sessions

#### Messaging Tables
7. **conversations** - Chat conversations
8. **conversation_messages** - Messages within sessions

#### Project Management Tables
9. **projects** - Project organization
10. **project_members** - Project membership
11. **session_documents** - Short-term memory

#### RBAC Tables
12. **departments** - Organizational departments
13. **teams** - Department teams
14. **roles** - User roles
15. **permissions** - System permissions
16. **role_permissions** - Role-permission mapping

#### Monitoring & Audit Tables
17. **audit_logs** - Comprehensive audit trail
18. **usage_metrics** - Usage analytics
19. **tool_usage_logs** - Tool usage tracking

#### Web Scraping Tables
20. **web_scrape_jobs** - Scraping job queue
21. **scraping_configs** - Scraping configurations
22. **saved_css_templates** - CSS extraction templates

#### ML & Evaluation Tables
23. **rag_evaluations** - RAG system evaluation metrics
24. **evaluation_runs** - Evaluation test runs

#### Advanced Tables
25. **prompt_library** - Saved prompts
26. **extraction_templates** - Data extraction templates
27. **session_contexts** - Session preferences
28. **document_permissions** - Document access control

---

## Prerequisites

### Required Software

```bash
# PostgreSQL 16+
sudo apt-get install postgresql-16 postgresql-contrib-16

# pgvector extension
sudo apt-get install postgresql-16-pgvector

# OR via Docker
docker pull postgres:16
```

### Required Extensions

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
```

### Environment Variables

```bash
# Database connection
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=your_secure_password
export POSTGRES_DB=ragchatbot
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432

# MinIO (object storage)
export MINIO_ROOT_USER=minioadmin
export MINIO_ROOT_PASSWORD=minioadmin
export MINIO_ENDPOINT=http://localhost:9000

# Redis (caching)
export REDIS_HOST=localhost
export REDIS_PORT=6379
```

---

## Complete Database Recovery Procedure

### Step 1: Prepare the Environment

```bash
# Navigate to project root
cd /mnt/c/AIML/ClaudeCode/chatbot/ChatBot

# Stop all services
docker-compose down -v  # WARNING: This deletes volumes!

# Or if using system PostgreSQL
sudo systemctl stop postgresql
```

---

### Step 2: Create Fresh Database

```bash
# Using Docker Compose
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
docker-compose exec postgres pg_isready -U postgres

# Create database
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE ragchatbot;"

# OR if using system PostgreSQL
sudo -u postgres createdb ragchatbot
```

---

### Step 3: Install Required Extensions

```bash
# Using Docker
docker-compose exec postgres psql -U postgres -d ragchatbot -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
docker-compose exec postgres psql -U postgres -d ragchatbot -c "CREATE EXTENSION IF NOT EXISTS \"vector\";"

# OR using system PostgreSQL
sudo -u postgres psql -d ragchatbot -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
sudo -u postgres psql -d ragchatbot -c "CREATE EXTENSION IF NOT EXISTS \"vector\";"
```

**Verify Extensions**:
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT * FROM pg_extension WHERE extname IN ('uuid-ossp', 'vector');"
```

**Expected Output**:
```
  oid  | extname  | extowner | extnamespace | extrelocatable | extversion | extconfig | extcondition
-------+----------+----------+--------------+----------------+------------+-----------+--------------
 16393 | uuid-ossp|      10 |         2200 | t              | 1.1        |           |
 16401 | vector   |      10 |         2200 | t              | 0.5.1      |           |
```

---

### Step 4: Execute Migration Files (In Order)

**IMPORTANT**: Migrations must be executed in the exact order below.

```bash
# Change to migrations directory
cd backend/migrations

# Execute migrations in order
# 000: Base schema
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 000_base_schema.sql

# 001: RBAC and Audit (choose ONE of these)
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 001_add_rbac_and_audit.sql
# OR
# docker-compose exec -T postgres psql -U postgres -d ragchatbot < 001_add_evaluation_tables.sql

# 002: Fix embedding dimensions (CRITICAL!)
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 002_fix_embedding_dimensions.sql

# 003: Fix query cache default
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 003_fix_query_cache_default.sql

# 004: Additional features (execute all 004_* files)
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 004_add_api_credentials.sql
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 004_add_saved_css_templates.sql
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 004_add_scraping_configs.sql

# 005: Tool tracking
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 005_add_tool_usage_tracking.sql

# 006: Projects and RBAC
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 006_add_modules_and_projects.sql
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 006_add_rbac_tables.sql

# 007: Project tracking and RBAC seed data
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 007_add_project_tracking.sql
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 007_seed_rbac_data.sql

# 008: Department structure
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 008_normalize_departments_teams.sql
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 008_update_department_structure.sql

# 009: Team rename
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 009_rename_data_ops_teams.sql

# 010-011: Audit enhancements
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 010_enhance_audit_action_types.sql
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 011_add_missing_action_types.sql

# 012: Projects, scraping, prompts
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 012_add_default_project.sql
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 012_add_project_based_scraping.sql
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 012_add_project_to_sessions.sql
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 012_add_prompt_library_and_templates.sql

# 013: User organization, agent tasks, Global project (execute all 013_* files)
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 013_add_agent_tasks_table.sql
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 013_add_project_model_preferences.sql
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 013_add_project_organizational_fks.sql
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 013_add_user_organizational_fields.sql
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 013_create_default_global_project.sql

# 014: File type length fix (if exists)
docker-compose exec -T postgres psql -U postgres -d ragchatbot < 014_fix_file_type_length.sql || true

# Additional migrations (if exist)
docker-compose exec -T postgres psql -U postgres -d ragchatbot < add_extraction_templates.sql || true
docker-compose exec -T postgres psql -U postgres -d ragchatbot < add_enhanced_scraping_fields.sql || true
```

**Automated Migration Script**:

```bash
# Create automated migration script
cat > /tmp/run_all_migrations.sh << 'SCRIPT'
#!/bin/bash
set -e

MIGRATIONS=(
    "000_base_schema.sql"
    "001_add_rbac_and_audit.sql"
    "002_fix_embedding_dimensions.sql"
    "003_fix_query_cache_default.sql"
    "004_add_api_credentials.sql"
    "004_add_saved_css_templates.sql"
    "004_add_scraping_configs.sql"
    "005_add_tool_usage_tracking.sql"
    "006_add_modules_and_projects.sql"
    "006_add_rbac_tables.sql"
    "007_add_project_tracking.sql"
    "007_seed_rbac_data.sql"
    "008_normalize_departments_teams.sql"
    "008_update_department_structure.sql"
    "009_rename_data_ops_teams.sql"
    "010_enhance_audit_action_types.sql"
    "011_add_missing_action_types.sql"
    "012_add_default_project.sql"
    "012_add_project_based_scraping.sql"
    "012_add_project_to_sessions.sql"
    "012_add_prompt_library_and_templates.sql"
    "013_add_agent_tasks_table.sql"
    "013_add_project_model_preferences.sql"
    "013_add_project_organizational_fks.sql"
    "013_add_user_organizational_fields.sql"
    "013_create_default_global_project.sql"
)

cd backend/migrations

for migration in "${MIGRATIONS[@]}"; do
    echo "Executing: $migration"
    docker-compose exec -T postgres psql -U postgres -d ragchatbot < "$migration"
    if [ $? -eq 0 ]; then
        echo "✅ $migration - SUCCESS"
    else
        echo "❌ $migration - FAILED"
        exit 1
    fi
done

echo "✅ All migrations completed successfully!"
SCRIPT

chmod +x /tmp/run_all_migrations.sh
bash /tmp/run_all_migrations.sh
```

---

### Step 5: Verify Schema Creation

```bash
# List all tables
docker-compose exec postgres psql -U postgres -d ragchatbot -c "\dt"

# Expected output should show ~28 tables
# Count tables
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
```

**Expected Table Count**: ~28-30 tables

**Verify Critical Tables**:
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
"
```

---

### Step 6: Verify Default Data

```bash
# Check default users (admin, anonymous)
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT username, email, role FROM users;"

# Expected: admin and anonymous users

# Check Global project
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT id, name, description FROM projects WHERE name = 'Global';"

# Expected: 1 Global project

# Check RBAC roles
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT name, description FROM roles;"

# Expected: multiple roles (admin, user, viewer, etc.)
```

---

### Step 7: Restore Data from Backup (Optional)

If you have a backup, restore it now:

```bash
# Restore from SQL dump
docker-compose exec -T postgres psql -U postgres -d ragchatbot < /path/to/backup.sql

# OR restore from custom format
docker-compose exec postgres pg_restore -U postgres -d ragchatbot /path/to/backup.dump

# OR restore from directory format
docker-compose exec postgres pg_restore -U postgres -d ragchatbot -F directory /path/to/backup_dir
```

---

### Step 8: Recreate Vector Indexes

**IMPORTANT**: Vector indexes must be recreated after data restoration.

```sql
-- Recreate vector indexes
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
ON document_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_query_cache_embedding
ON query_cache USING ivfflat (query_embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_session_contexts_embedding
ON session_contexts USING ivfflat (conversation_embedding vector_cosine_ops)
WITH (lists = 100);
```

Execute:
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
ON document_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_query_cache_embedding
ON query_cache USING ivfflat (query_embedding vector_cosine_ops)
WITH (lists = 100);
"
```

---

### Step 9: Update Statistics

```bash
# Analyze all tables
docker-compose exec postgres psql -U postgres -d ragchatbot -c "ANALYZE;"

# Vacuum all tables
docker-compose exec postgres psql -U postgres -d ragchatbot -c "VACUUM ANALYZE;"
```

---

### Step 10: Start Application Services

```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps

# Check backend logs
docker-compose logs backend --tail=50

# Check frontend logs
docker-compose logs frontend --tail=50
```

---

## Migration Files Reference

### Migration Order and Dependencies

| Order | Migration File | Purpose | Dependencies |
|-------|----------------|---------|--------------|
| 1 | `000_base_schema.sql` | Core tables (documents, chunks, cache) | None |
| 2 | `001_add_rbac_and_audit.sql` | Users, sessions, audit logging | 000 |
| 3 | `002_fix_embedding_dimensions.sql` | Change embeddings from 1536→384 | 000, 001 |
| 4 | `003_fix_query_cache_default.sql` | Fix cache defaults | 000, 002 |
| 5 | `004_add_api_credentials.sql` | API key management | 001 |
| 6 | `004_add_saved_css_templates.sql` | CSS extraction templates | 000 |
| 7 | `004_add_scraping_configs.sql` | Scraping configurations | 000 |
| 8 | `005_add_tool_usage_tracking.sql` | Tool usage analytics | 001 |
| 9 | `006_add_modules_and_projects.sql` | Project management | 001 |
| 10 | `006_add_rbac_tables.sql` | Full RBAC structure | 001 |
| 11 | `007_add_project_tracking.sql` | Enhanced project tracking | 006 |
| 12 | `007_seed_rbac_data.sql` | Default RBAC data | 006 |
| 13 | `008_normalize_departments_teams.sql` | Department structure | 006, 007 |
| 14 | `008_update_department_structure.sql` | Department updates | 008 |
| 15 | `009_rename_data_ops_teams.sql` | Team renames | 008 |
| 16 | `010_enhance_audit_action_types.sql` | Audit action types | 001 |
| 17 | `011_add_missing_action_types.sql` | Additional action types | 010 |
| 18 | `012_add_default_project.sql` | Default project | 006 |
| 19 | `012_add_project_based_scraping.sql` | Project-scoped scraping | 006 |
| 20 | `012_add_project_to_sessions.sql` | Session-project link | 001, 006 |
| 21 | `012_add_prompt_library_and_templates.sql` | Prompt management | 001, 006 |
| 22 | `013_add_agent_tasks_table.sql` | Agent task tracking | 001, 006 |
| 23 | `013_add_project_model_preferences.sql` | Model preferences | 006 |
| 24 | `013_add_project_organizational_fks.sql` | Org foreign keys | 006, 008 |
| 25 | `013_add_user_organizational_fields.sql` | User org fields | 001, 008 |
| 26 | `013_create_default_global_project.sql` | Global project | 006, 001 |

---

## Schema Documentation

### Core Tables

#### 1. `documents` Table

**Purpose**: Stores metadata for uploaded/scraped documents.

**Columns**:
```sql
id                  UUID PRIMARY KEY (auto-generated)
filename            VARCHAR(255) NOT NULL
file_path           TEXT NOT NULL (MinIO path)
file_type           VARCHAR(100) (pdf, docx, txt, etc.)
file_size           BIGINT (bytes)
source_type         VARCHAR(50) ('upload', 'scrape')
source_url          TEXT (if scraped)
processing_status   VARCHAR(50) ('pending', 'processing', 'completed', 'failed')
error_message       TEXT
project_id          UUID (FK → projects.id)
metadata            JSONB
created_at          TIMESTAMP WITH TIME ZONE
updated_at          TIMESTAMP WITH TIME ZONE
```

**Indexes**:
- `idx_documents_created_at` (created_at DESC)
- `idx_documents_source_type` (source_type)
- `idx_documents_processing_status` (processing_status)
- `idx_documents_project_id` (project_id)

**Foreign Keys**:
- `project_id` → `projects.id` ON DELETE SET NULL

---

#### 2. `document_chunks` Table

**Purpose**: Stores text chunks with vector embeddings for similarity search.

**Columns**:
```sql
id              UUID PRIMARY KEY
document_id     UUID NOT NULL (FK → documents.id)
chunk_index     INTEGER NOT NULL
content         TEXT NOT NULL
embedding       vector(384) (384-dimensional vector)
meta_info       JSONB
created_at      TIMESTAMP WITH TIME ZONE
```

**Indexes**:
- `idx_document_chunks_document_id` (document_id)
- `idx_document_chunks_embedding` USING ivfflat (embedding vector_cosine_ops)

**Foreign Keys**:
- `document_id` → `documents.id` ON DELETE CASCADE

**CRITICAL**: Embedding dimension is 384 (sentence-transformers/all-MiniLM-L6-v2)

---

#### 3. `users` Table

**Purpose**: User accounts with RBAC.

**Columns**:
```sql
id                  UUID PRIMARY KEY
username            VARCHAR(100) UNIQUE NOT NULL
email               VARCHAR(255) UNIQUE NOT NULL
full_name           VARCHAR(255)
hashed_password     VARCHAR(255) NOT NULL (bcrypt hash)
role                user_role ('admin', 'user', 'viewer', 'api_user')
is_active           BOOLEAN DEFAULT TRUE
is_verified         BOOLEAN DEFAULT FALSE
created_at          TIMESTAMP WITH TIME ZONE
updated_at          TIMESTAMP WITH TIME ZONE
last_login          TIMESTAMP WITH TIME ZONE
department_id       UUID (FK → departments.id)
team_id             UUID (FK → teams.id)
meta_info           JSONB
```

**Default Users**:
1. **admin** / admin@example.com / password: admin123 (bcrypt: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU3bKuYjh/5u)
2. **anonymous** / anonymous@example.com / password: admin123

---

#### 4. `projects` Table

**Purpose**: Project organization for documents and sessions.

**Columns**:
```sql
id              UUID PRIMARY KEY
name            VARCHAR(255) UNIQUE NOT NULL
description     TEXT
owner_id        UUID (FK → users.id)
department_id   UUID (FK → departments.id)
created_at      TIMESTAMP WITH TIME ZONE
updated_at      TIMESTAMP WITH TIME ZONE
meta_info       JSONB
```

**Default Project**:
- **Global** - Default project for documents not assigned to specific projects

---

#### 5. `chat_sessions` Table

**Purpose**: User chat sessions with project tracking.

**Columns**:
```sql
id              UUID PRIMARY KEY
session_id      VARCHAR(255) UNIQUE NOT NULL
user_id         UUID (FK → users.id)
project_id      UUID (FK → projects.id)
title           VARCHAR(255)
created_at      TIMESTAMP WITH TIME ZONE
updated_at      TIMESTAMP WITH TIME ZONE
last_activity   TIMESTAMP WITH TIME ZONE
is_active       BOOLEAN DEFAULT TRUE
meta_info       JSONB
```

---

### RBAC Tables

#### 6. `roles` Table

**Columns**:
```sql
id              UUID PRIMARY KEY
name            VARCHAR(100) UNIQUE NOT NULL
description     TEXT
created_at      TIMESTAMP WITH TIME ZONE
```

**Default Roles**:
- admin
- user
- viewer
- analyst
- developer

---

#### 7. `permissions` Table

**Columns**:
```sql
id              UUID PRIMARY KEY
name            VARCHAR(100) UNIQUE NOT NULL
resource        VARCHAR(100)
action          VARCHAR(50)
description     TEXT
created_at      TIMESTAMP WITH TIME ZONE
```

---

#### 8. `role_permissions` Table

**Purpose**: Maps roles to permissions (many-to-many).

**Columns**:
```sql
id              UUID PRIMARY KEY
role_id         UUID (FK → roles.id)
permission_id   UUID (FK → permissions.id)
created_at      TIMESTAMP WITH TIME ZONE
UNIQUE(role_id, permission_id)
```

---

### Audit & Monitoring Tables

#### 9. `audit_logs` Table

**Purpose**: Comprehensive audit trail.

**Columns**:
```sql
id              UUID PRIMARY KEY
user_id         UUID (FK → users.id)
session_id      UUID (FK → chat_sessions.id)
action          action_type ENUM
resource_type   VARCHAR(50)
resource_id     UUID
description     TEXT
request_data    JSONB
response_data   JSONB
ip_address      VARCHAR(45)
user_agent      VARCHAR(512)
status_code     INTEGER
error_message   TEXT
latency_ms      DOUBLE PRECISION
created_at      TIMESTAMP WITH TIME ZONE
meta_info       JSONB
```

---

#### 10. `tool_usage_logs` Table

**Purpose**: Track tool/service usage.

**Columns**:
```sql
id              UUID PRIMARY KEY
session_id      VARCHAR(255)
user_id         UUID (FK → users.id)
tool_name       VARCHAR(255)
parameters      JSONB
result          JSONB
execution_time_ms DOUBLE PRECISION
timestamp       TIMESTAMP WITH TIME ZONE
success         BOOLEAN
error_message   TEXT
```

---

## Data Backup Procedures

### Daily Automated Backup

**Script**: `/tmp/backup_database.sh`

```bash
#!/bin/bash
set -e

# Configuration
BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="ragchatbot"
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database (SQL format)
docker-compose exec -T postgres pg_dump -U postgres -d "$DB_NAME" -F p -f "/tmp/backup_${DATE}.sql"
docker cp rag-postgres:/tmp/backup_${DATE}.sql "$BACKUP_DIR/backup_${DATE}.sql"

# Backup database (Custom format - supports parallel restore)
docker-compose exec -T postgres pg_dump -U postgres -d "$DB_NAME" -F c -f "/tmp/backup_${DATE}.dump"
docker cp rag-postgres:/tmp/backup_${DATE}.dump "$BACKUP_DIR/backup_${DATE}.dump"

# Compress SQL backup
gzip "$BACKUP_DIR/backup_${DATE}.sql"

# Remove old backups
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "backup_*.dump" -mtime +$RETENTION_DAYS -delete

echo "✅ Backup completed: $BACKUP_DIR/backup_${DATE}.dump"
```

**Setup Cron Job**:
```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /tmp/backup_database.sh >> /var/log/postgres_backup.log 2>&1
```

---

### Manual Backup

```bash
# SQL format backup
docker-compose exec postgres pg_dump -U postgres -d ragchatbot -F p > backup_$(date +%Y%m%d).sql

# Custom format backup (recommended)
docker-compose exec postgres pg_dump -U postgres -d ragchatbot -F c -f backup_$(date +%Y%m%d).dump

# Directory format backup (parallel restore support)
docker-compose exec postgres pg_dump -U postgres -d ragchatbot -F directory -f backup_$(date +%Y%m%d)
```

---

### Backup Specific Tables

```bash
# Backup only critical data tables
docker-compose exec postgres pg_dump -U postgres -d ragchatbot \
  -t documents -t document_chunks -t users -t projects -t chat_sessions \
  -F c -f critical_tables_backup.dump
```

---

## Data Restore Procedures

### Restore from SQL Backup

```bash
# Stop application
docker-compose stop backend frontend

# Drop and recreate database
docker-compose exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS ragchatbot;"
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE ragchatbot;"

# Restore from SQL
docker-compose exec -T postgres psql -U postgres -d ragchatbot < backup_20251201.sql

# Recreate vector indexes (if not in backup)
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
ON document_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
"

# Restart application
docker-compose up -d backend frontend
```

---

### Restore from Custom Format Backup

```bash
# Stop application
docker-compose stop backend frontend

# Drop and recreate database
docker-compose exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS ragchatbot;"
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE ragchatbot;"

# Restore with pg_restore (supports parallel restore)
docker-compose exec postgres pg_restore -U postgres -d ragchatbot -j 4 backup_20251201.dump

# -j 4 = use 4 parallel jobs (faster)

# Restart application
docker-compose up -d backend frontend
```

---

### Selective Table Restore

```bash
# Restore only specific tables
docker-compose exec postgres pg_restore -U postgres -d ragchatbot \
  -t documents -t document_chunks \
  backup_20251201.dump
```

---

## Frontend-Backend-DB Sync Requirements

### Critical Sync Points

#### 1. **Embedding Dimensions**

**Database**: `embedding vector(384)` in `document_chunks`

**Backend** (`backend/app/services/embedding_service.py`):
```python
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384
```

**Verification**:
```bash
# Check DB dimension
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT column_name, udt_name, character_maximum_length
FROM information_schema.columns
WHERE table_name = 'document_chunks' AND column_name = 'embedding';
"
```

---

#### 2. **Project Structure**

**Database**: `projects` table with `id`, `name`, `description`, `owner_id`

**Frontend** (`frontend/src/components/ProjectSelector.tsx`):
```typescript
interface Project {
  id: string;
  name: string;
  description?: string;
  owner_id?: string;
}
```

**Backend API** (`backend/app/api/routes/teams_projects_routes.py`):
```python
class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    owner_id: Optional[UUID]
```

---

#### 3. **User Roles**

**Database**: `user_role` ENUM ('admin', 'user', 'viewer', 'api_user')

**Backend** (`backend/app/models/database_enhanced.py`):
```python
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    API_USER = "api_user"
```

**Frontend**: Must match backend enum values exactly.

---

#### 4. **Document Processing Status**

**Database**: `processing_status` VARCHAR(50) ('pending', 'processing', 'completed', 'failed')

**Backend** (`backend/app/services/document_service.py`):
```python
class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
```

---

#### 5. **Session-Project Linking**

**Database**: `chat_sessions.project_id` (FK → projects.id)

**Frontend** (`frontend/src/components/ChatInterface.tsx`):
- Must send `project_id` in FormData for /api/v1/query endpoint

**Backend** (`backend/app/main.py`):
```python
@app.post("/api/v1/query")
async def query_endpoint(
    query: str = Form(...),
    project_id: Optional[str] = Form(None),  # Must accept project_id
    ...
):
```

---

### Sync Validation Checklist

- [ ] Embedding dimensions match (384)
- [ ] User role enums match
- [ ] Project schema matches frontend interface
- [ ] Document status enums match
- [ ] API endpoints accept project_id parameter
- [ ] Frontend sends project_id in requests
- [ ] Database has Global project created
- [ ] All users are members of Global project

---

## Validation & Testing

### Database Schema Validation

```bash
# Validate table count
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT COUNT(*) as table_count
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
"
# Expected: ~28-30 tables

# Validate extensions
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT extname, extversion FROM pg_extension
WHERE extname IN ('uuid-ossp', 'vector');
"
# Expected: uuid-ossp (1.1), vector (0.5.1 or higher)

# Validate embedding dimensions
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT
    table_name,
    column_name,
    udt_name,
    SUBSTRING(udt_name FROM 'vector\\((\\d+)\\)') as dimension
FROM information_schema.columns
WHERE udt_name LIKE 'vector%';
"
# Expected: All embeddings should be vector(384)

# Validate default users
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT username, email, role, is_active FROM users;
"
# Expected: admin and anonymous users

# Validate Global project
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT id, name, owner_id FROM projects WHERE name = 'Global';
"
# Expected: 1 Global project

# Validate RBAC structure
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT
    (SELECT COUNT(*) FROM roles) as roles_count,
    (SELECT COUNT(*) FROM permissions) as permissions_count,
    (SELECT COUNT(*) FROM role_permissions) as role_permissions_count;
"
```

---

### Application Integration Testing

#### Test 1: Health Check

```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

#### Test 2: Database Connection

```bash
curl http://localhost:8000/api/v1/health
# Expected: {"database": "connected", "redis": "connected"}
```

#### Test 3: User Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
# Expected: {"access_token": "...", "token_type": "bearer"}
```

#### Test 4: List Projects

```bash
curl -X GET http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer <your-token>"
# Expected: [{"id": "...", "name": "Global", ...}]
```

#### Test 5: Upload Document

```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -H "Authorization: Bearer <your-token>" \
  -F "file=@test.pdf" \
  -F "project_id=<Global-UUID>"
# Expected: {"document_id": "...", "status": "processing"}
```

#### Test 6: Query RAG System

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is this document about?",
    "project_id": "<Global-UUID>"
  }'
# Expected: {"answer": "...", "sources": [...]}
```

---

## Common Recovery Scenarios

### Scenario 1: Complete Data Loss

**Steps**:
1. Execute Step 1-6 of Complete Database Recovery Procedure
2. Restore from latest backup (Step 7)
3. Recreate vector indexes (Step 8)
4. Update statistics (Step 9)
5. Start services (Step 10)
6. Validate (Section: Validation & Testing)

**Estimated Time**: 20-30 minutes

---

### Scenario 2: Embedding Dimension Mismatch

**Symptom**: "dimension of vector is 1536 but expected 384"

**Fix**:
```bash
# Execute migration 002
docker-compose exec -T postgres psql -U postgres -d ragchatbot < backend/migrations/002_fix_embedding_dimensions.sql

# Re-generate all embeddings
docker-compose exec backend python regenerate_embeddings.py
```

---

### Scenario 3: Missing Global Project

**Symptom**: Frontend shows no projects, documents not scoped

**Fix**:
```bash
# Execute migration 013
docker-compose exec -T postgres psql -U postgres -d ragchatbot < backend/migrations/013_create_default_global_project.sql

# Verify
docker-compose exec postgres psql -U postgres -d ragchatbot -c "SELECT * FROM projects WHERE name = 'Global';"
```

---

### Scenario 4: Orphaned Documents

**Symptom**: Documents with NULL project_id

**Fix**:
```bash
# Assign to Global project
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
UPDATE documents
SET project_id = (SELECT id FROM projects WHERE name = 'Global' LIMIT 1)
WHERE project_id IS NULL;
"

# Verify
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT COUNT(*) FROM documents WHERE project_id IS NULL;
"
# Expected: 0
```

---

### Scenario 5: Missing Vector Indexes

**Symptom**: Slow vector similarity search

**Fix**:
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
ON document_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_query_cache_embedding
ON query_cache USING ivfflat (query_embedding vector_cosine_ops)
WITH (lists = 100);

ANALYZE document_chunks;
ANALYZE query_cache;
"
```

---

### Scenario 6: Password Reset for Admin User

**Symptom**: Forgot admin password

**Fix**:
```bash
# Reset to default password (admin123)
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
UPDATE users
SET hashed_password = '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU3bKuYjh/5u'
WHERE username = 'admin';
"
```

---

## Troubleshooting

### Issue: Migration fails with "relation already exists"

**Cause**: Migration was partially executed before failure.

**Fix**:
```bash
# Option 1: Use IF NOT EXISTS clauses (already in migrations)
# Re-run migration - it should skip existing tables

# Option 2: Drop and recreate database
docker-compose exec postgres psql -U postgres -c "DROP DATABASE ragchatbot;"
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE ragchatbot;"
# Then re-run all migrations
```

---

### Issue: "extension 'vector' does not exist"

**Cause**: pgvector extension not installed.

**Fix**:
```bash
# Install pgvector
docker-compose exec postgres apt-get update && apt-get install -y postgresql-16-pgvector

# Or rebuild postgres container with pgvector
# Update docker-compose.yml to use pgvector-enabled image
```

---

### Issue: Slow vector search queries

**Cause**: Missing or suboptimal vector indexes.

**Fix**:
```bash
# Drop and recreate index with optimal parameters
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
DROP INDEX IF EXISTS idx_document_chunks_embedding;

CREATE INDEX idx_document_chunks_embedding
ON document_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

ANALYZE document_chunks;
"
```

---

### Issue: Frontend-Backend project_id mismatch

**Cause**: Frontend not sending project_id or backend not receiving it.

**Debug**:
```bash
# Check backend logs
docker-compose logs backend -f | grep -E "project_id|🔍 DEBUG"

# Check if project_id is None at API level
# Expected: project_id = <UUID>
# Actual (if broken): project_id = None
```

**Fix**: Ensure `frontend/src/pages/index.tsx` line 137 includes:
```typescript
<ChatInterface activeTab={activeTab} ragConfig={ragConfig} projectId={selectedProjectId} />
```

---

## Disaster Recovery Checklist

### Pre-Disaster Preparation

- [ ] Daily automated backups configured
- [ ] Backup retention policy set (30 days)
- [ ] Backup storage location secured
- [ ] Database migration files versioned in Git
- [ ] Recovery procedures documented and tested
- [ ] Team members trained on recovery process

---

### During Disaster

- [ ] Assess extent of data loss
- [ ] Identify most recent valid backup
- [ ] Notify stakeholders of estimated downtime
- [ ] Document incident for post-mortem

---

### Recovery Execution

- [ ] Stop all application services
- [ ] Create fresh database
- [ ] Install required extensions (uuid-ossp, vector)
- [ ] Execute migrations in order
- [ ] Restore data from backup
- [ ] Recreate vector indexes
- [ ] Update statistics (ANALYZE, VACUUM)
- [ ] Validate schema and data
- [ ] Test critical application flows
- [ ] Start application services
- [ ] Monitor for errors

---

### Post-Recovery

- [ ] Verify all services operational
- [ ] Validate data integrity
- [ ] Check user access and authentication
- [ ] Verify project isolation working
- [ ] Monitor application logs for 24 hours
- [ ] Conduct post-mortem analysis
- [ ] Update disaster recovery procedures
- [ ] Review and improve backup strategy

---

## Contact & Support

**Database Administrator**: [Your Name]
**On-Call Support**: [Phone Number]
**Escalation Path**: [Manager Contact]

**Documentation Location**: `/tmp/DATABASE_DISASTER_RECOVERY_PLAN.md`
**Last Reviewed**: 2025-12-01

---

**End of Disaster Recovery Plan**
