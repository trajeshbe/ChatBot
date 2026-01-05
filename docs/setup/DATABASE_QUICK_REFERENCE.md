# Database Quick Reference Card

> **Quick commands for common database operations**

---

## Setup & Installation

```bash
# Complete fresh installation
./scripts/setup/setup-database-complete.sh

# Skip confirmations (automation)
./scripts/setup/setup-database-complete.sh --skip-confirmation

# Verbose output
./scripts/setup/setup-database-complete.sh --verbose
```

---

## Connection & Access

```bash
# Connect to PostgreSQL container
docker exec -it rag-postgres psql -U postgres -d ragchatbot

# Execute single SQL command
docker exec rag-postgres psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM users;"

# Execute SQL file
docker exec -i rag-postgres psql -U postgres -d ragchatbot < script.sql
```

---

## Database Operations

### Create & Drop

```bash
# Create database
docker exec rag-postgres psql -U postgres -c "CREATE DATABASE ragchatbot;"

# Drop database (⚠️  DANGEROUS - deletes all data)
docker exec rag-postgres psql -U postgres -c "DROP DATABASE ragchatbot;"

# Recreate database
docker exec rag-postgres psql -U postgres -c "DROP DATABASE IF EXISTS ragchatbot;"
docker exec rag-postgres psql -U postgres -c "CREATE DATABASE ragchatbot;"
```

### Extensions

```bash
# Enable extensions
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";
CREATE EXTENSION IF NOT EXISTS \"vector\";
"

# List extensions
docker exec rag-postgres psql -U postgres -d ragchatbot -c "SELECT * FROM pg_extension;"
```

---

## Table Operations

### List Tables

```bash
# List all tables
docker exec rag-postgres psql -U postgres -d ragchatbot -c "\dt"

# List tables with sizes
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

# Count tables
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT COUNT(*) FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
"
```

### Table Details

```bash
# Describe table structure
docker exec rag-postgres psql -U postgres -d ragchatbot -c "\d+ users"

# List columns for a table
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT column_name, data_type, character_maximum_length, is_nullable
FROM information_schema.columns
WHERE table_name = 'users';
"

# List indexes for a table
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'users';
"
```

---

## Data Queries

### Row Counts

```bash
# Count rows in all tables
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT
    schemaname,
    tablename,
    n_live_tup AS row_count
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_live_tup DESC;
"

# Quick counts for critical tables
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT
    (SELECT COUNT(*) FROM users) AS users,
    (SELECT COUNT(*) FROM documents) AS documents,
    (SELECT COUNT(*) FROM document_chunks) AS chunks,
    (SELECT COUNT(*) FROM chat_sessions) AS sessions,
    (SELECT COUNT(*) FROM roles) AS roles,
    (SELECT COUNT(*) FROM departments) AS departments,
    (SELECT COUNT(*) FROM teams) AS teams,
    (SELECT COUNT(*) FROM modules) AS modules;
"
```

### User Management

```bash
# List all users
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT username, email, role, is_active, created_at
FROM users
ORDER BY created_at DESC;
"

# Find user by username
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT * FROM users WHERE username = 'admin';
"

# Count users by role
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT role, COUNT(*) FROM users GROUP BY role;
"
```

### Documents & Chunks

```bash
# Document statistics
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT
    source_type,
    processing_status,
    COUNT(*) AS count,
    SUM(file_size) AS total_size_bytes,
    pg_size_pretty(SUM(file_size)) AS total_size
FROM documents
GROUP BY source_type, processing_status;
"

# Chunks with embeddings
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT
    COUNT(*) AS total_chunks,
    COUNT(embedding) AS with_embeddings,
    COUNT(*) - COUNT(embedding) AS without_embeddings
FROM document_chunks;
"
```

---

## Organizational Hierarchy

```bash
# List departments and teams
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT
    d.name AS department,
    COUNT(t.id) AS team_count,
    STRING_AGG(t.name, ', ' ORDER BY t.name) AS teams
FROM departments d
LEFT JOIN teams t ON t.department_id = d.id
WHERE d.is_active = TRUE
GROUP BY d.id, d.name
ORDER BY d.name;
"

# User distribution by department
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT
    d.name AS department,
    COUNT(u.id) AS user_count
FROM departments d
LEFT JOIN users u ON u.department_id = d.id
GROUP BY d.id, d.name
ORDER BY user_count DESC;
"
```

---

## RBAC & Permissions

```bash
# List roles and permissions
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT
    r.name AS role_name,
    COUNT(rmp.id) AS module_permissions
FROM roles r
LEFT JOIN role_module_permissions rmp ON r.id = rmp.role_id
GROUP BY r.id, r.name
ORDER BY r.name;
"

# User roles
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT
    u.username,
    r.name AS role,
    d.name AS department
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
LEFT JOIN departments d ON ur.department_id = d.id
WHERE ur.is_active = TRUE;
"

# Module access by role
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT
    r.name AS role,
    m.module_name AS module,
    rmp.can_access,
    rmp.can_execute,
    rmp.can_view_results
FROM role_module_permissions rmp
JOIN roles r ON rmp.role_id = r.id
JOIN modules m ON rmp.module_id = m.id
ORDER BY r.name, m.module_name;
"
```

---

## Audit Logs

```bash
# Recent audit logs
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT
    created_at,
    u.username,
    action,
    resource_type,
    status_code
FROM audit_logs al
LEFT JOIN users u ON al.user_id = u.id
ORDER BY created_at DESC
LIMIT 20;
"

# Actions by type
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT action, COUNT(*) FROM audit_logs GROUP BY action ORDER BY COUNT(*) DESC;
"

# Failed actions
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT * FROM audit_logs WHERE status_code >= 400 ORDER BY created_at DESC LIMIT 10;
"
```

---

## Maintenance

### Vacuum & Analyze

```bash
# Full vacuum and analyze
docker exec rag-postgres psql -U postgres -d ragchatbot -c "VACUUM ANALYZE;"

# Vacuum specific table
docker exec rag-postgres psql -U postgres -d ragchatbot -c "VACUUM ANALYZE document_chunks;"

# Verbose vacuum
docker exec rag-postgres psql -U postgres -d ragchatbot -c "VACUUM (VERBOSE, ANALYZE);"
```

### Database Statistics

```bash
# Database size
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
WHERE datname = 'ragchatbot';
"

# Connection statistics
docker exec rag-postgres psql -U postgres -c "
SELECT
    datname,
    numbackends AS connections,
    xact_commit AS commits,
    xact_rollback AS rollbacks
FROM pg_stat_database
WHERE datname = 'ragchatbot';
"

# Bloat check
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    n_dead_tup AS dead_rows,
    ROUND(100 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_pct
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY dead_pct DESC NULLS LAST
LIMIT 10;
"
```

---

## Backup & Restore

### Backup

```bash
# Full database backup
docker exec rag-postgres pg_dump -U postgres ragchatbot > backup.sql

# Compressed backup
docker exec rag-postgres pg_dump -U postgres ragchatbot | gzip > backup.sql.gz

# Schema only
docker exec rag-postgres pg_dump -U postgres --schema-only ragchatbot > schema.sql

# Data only
docker exec rag-postgres pg_dump -U postgres --data-only ragchatbot > data.sql

# Specific table
docker exec rag-postgres pg_dump -U postgres -t users ragchatbot > users_backup.sql
```

### Restore

```bash
# Restore from backup
docker exec -i rag-postgres psql -U postgres ragchatbot < backup.sql

# Restore compressed
gunzip -c backup.sql.gz | docker exec -i rag-postgres psql -U postgres ragchatbot

# Restore specific table
docker exec -i rag-postgres psql -U postgres ragchatbot < users_backup.sql
```

---

## Performance Tuning

### Index Management

```bash
# List all indexes with sizes
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid::regclass)) AS index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid::regclass) DESC;
"

# Unused indexes (candidates for removal)
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan AS index_scans
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
    AND idx_scan = 0
    AND indexrelname NOT LIKE '%_pkey'
ORDER BY pg_relation_size(indexrelid::regclass) DESC;
"

# Rebuild vector index
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
REINDEX INDEX idx_chunks_embedding;
"
```

### Query Performance

```bash
# Slow queries (requires pg_stat_statements extension)
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
"

# Active connections and queries
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT
    pid,
    usename,
    application_name,
    state,
    query_start,
    LEFT(query, 100) AS query
FROM pg_stat_activity
WHERE datname = 'ragchatbot'
    AND state != 'idle'
ORDER BY query_start;
"
```

---

## Troubleshooting

### Check Container

```bash
# Container status
docker ps | grep postgres

# Container logs
docker logs rag-postgres --tail 50

# Container resource usage
docker stats rag-postgres --no-stream
```

### Connection Issues

```bash
# Test connection
docker exec rag-postgres psql -U postgres -c "SELECT 1;"

# Check listening ports
docker exec rag-postgres netstat -tlnp | grep 5432

# Check PostgreSQL process
docker exec rag-postgres ps aux | grep postgres
```

### Reset Database

```bash
# ⚠️  CAUTION: Deletes ALL data
docker-compose down -v  # Stop and remove volumes
docker-compose up -d postgres  # Start fresh
sleep 10  # Wait for initialization
./scripts/setup/setup-database-complete.sh  # Reinitialize
```

---

## Useful Aliases

Add these to your `~/.bashrc` or `~/.zshrc`:

```bash
# Database shortcuts
alias db-connect='docker exec -it rag-postgres psql -U postgres -d ragchatbot'
alias db-query='docker exec rag-postgres psql -U postgres -d ragchatbot -c'
alias db-backup='docker exec rag-postgres pg_dump -U postgres ragchatbot > backup_$(date +%Y%m%d_%H%M%S).sql'
alias db-restore='docker exec -i rag-postgres psql -U postgres ragchatbot <'
alias db-tables='docker exec rag-postgres psql -U postgres -d ragchatbot -c "\dt"'
alias db-size='docker exec rag-postgres psql -U postgres -d ragchatbot -c "SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname)) AS size FROM pg_database WHERE datname = '\''ragchatbot'\'';"'

# Application shortcuts
alias app-restart='docker-compose restart backend frontend'
alias app-logs='docker-compose logs -f backend frontend'
alias app-health='curl http://localhost:8000/health'
```

---

## Environment Variables

Key environment variables for database configuration in `.env`:

```bash
# PostgreSQL Configuration
POSTGRES_DB=ragchatbot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Connection Pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30

# Vector Search
VECTOR_DIMENSIONS=384
VECTOR_DISTANCE_METRIC=cosine
```

---

## Quick Diagnostics

```bash
# One-liner health check
docker exec rag-postgres psql -U postgres -d ragchatbot -c "
SELECT
    'Database' AS component,
    CASE WHEN COUNT(*) > 0 THEN 'OK' ELSE 'FAIL' END AS status
FROM information_schema.tables
WHERE table_schema = 'public'
UNION ALL
SELECT
    'Extensions',
    CASE WHEN COUNT(*) = 2 THEN 'OK' ELSE 'FAIL' END
FROM pg_extension
WHERE extname IN ('uuid-ossp', 'vector')
UNION ALL
SELECT
    'Users',
    CASE WHEN COUNT(*) > 0 THEN 'OK' ELSE 'FAIL' END
FROM users;
"
```

---

**Quick Reference Version**: 1.0
**Last Updated**: 2026-01-05
**For**: Enterprise RAG Chatbot Database
