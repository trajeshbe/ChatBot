# Clean SQL Installation Guide

**Date**: 2026-01-07
**Status**: ✅ **COMPLETE**
**Related**: Requirement #9 - Comprehensive Installation Scripts

---

## Overview

This guide documents the comprehensive SQL-based database setup system that replaces the incremental migration approach with a clean, single-source installation strategy.

### Key Improvements Over Previous Approach

| Previous (Migrations) | New (Comprehensive SQL) |
|----------------------|------------------------|
| 44 migration files (000-027) | 13 organized SQL scripts (01-13) |
| Incremental changes only | Complete schema + seed data |
| Order dependencies unclear | Explicit numbered sequence |
| Missing seed data | ALL essential data included |
| Difficult to troubleshoot | Clear, modular structure |
| Prone to partial failures | Idempotent, safe to re-run |

---

## File Structure

```
backend/sql/
├── README.md                          # Comprehensive documentation
├── 00_CLEAN_INSTALL_MASTER.sql       # Master orchestration script
├── 01_extensions.sql                  # PostgreSQL extensions
├── 02_complete_schema.sql             # All 67 tables
├── 03_seed_departments.sql            # 7 departments
├── 04_seed_teams.sql                  # 28 teams
├── 05_seed_roles.sql                  # 5 RBAC roles
├── 06_seed_admin_user.sql             # Admin user (admin/admin)
├── 07_seed_global_project.sql         # Default Global project
├── 08_seed_system_config.sql          # 17 system configurations
├── 09_seed_models_registry.sql        # 17 LLM models
├── 10_seed_modules.sql                # 36 modules (Tier 1, 2, 3)
├── 11_seed_prompt_library.sql         # 25+ production prompts
├── 12_seed_rbac_permissions.sql       # Complete permission matrix
└── 13_create_indexes.sql              # 190+ performance indexes

scripts/setup/
└── clean-install-database.sh          # Automated installation script
```

---

## Installation Methods

### Method 1: Automated Installation (Recommended)

```bash
# Ensure PostgreSQL is running
docker-compose up -d postgres

# Create database
docker exec rag-postgres psql -U postgres -c "CREATE DATABASE ragchatbot;"

# Run automated installation
bash scripts/setup/clean-install-database.sh
```

**Features**:
- Interactive confirmation
- Pre-flight checks
- Progress reporting
- Post-installation verification
- Error handling

### Method 2: Manual SQL Execution

```bash
# Execute master script (recommended)
docker exec -i rag-postgres psql -U postgres -d ragchatbot \
  < backend/sql/00_CLEAN_INSTALL_MASTER.sql

# OR run individual scripts in order
for i in {01..13}; do
  docker exec -i rag-postgres psql -U postgres -d ragchatbot \
    < backend/sql/${i}*.sql
done
```

### Method 3: Direct psql Connection

```bash
# Connect to database
docker exec -it rag-postgres psql -U postgres -d ragchatbot

# Run master script from psql prompt
ragchatbot=# \i /path/to/backend/sql/00_CLEAN_INSTALL_MASTER.sql
```

---

## Script Details

### 00_CLEAN_INSTALL_MASTER.sql (9.9 KB)

**Purpose**: Orchestrates execution of all 13 scripts in correct order

**Features**:
- Pre-flight checks (PostgreSQL version >= 12)
- Executes all scripts using `\i` directive
- Progress reporting with color-coded output
- Post-installation verification summary
- Admin credentials display

**Execution Time**: ~30-60 seconds (depending on hardware)

---

### 01_extensions.sql (1.8 KB)

**Purpose**: Install required PostgreSQL extensions

**Extensions**:
```sql
uuid-ossp (v1.1)  -- UUID generation (uuid_generate_v4())
vector            -- pgvector for embeddings (VECTOR data type)
```

**Idempotent**: ✅ `CREATE EXTENSION IF NOT EXISTS`

---

### 02_complete_schema.sql (93 KB)

**Purpose**: Create all 67 database tables with proper dependencies

**Table Count**: 67 tables organized in dependency layers

**Key Tables**:
- **Core RAG**: documents, document_chunks, query_cache, conversations, messages
- **RBAC**: users, roles, user_roles, departments, teams, user_teams
- **Modules**: modules, module_configurations, module_activations
- **Projects**: projects, project_members
- **Audit**: audit_logs, usage_metrics, tool_usage_stats
- **Sessions**: chat_sessions, session_documents, session_contexts
- **Evaluation**: evaluation_configs, evaluation_results, evaluation_benchmarks
- **Fine-tuning**: finetuning_jobs, finetuning_datasets, finetuned_models
- **Phase 2**: system_config, models
- **Export**: export_packages, export_jobs, export_templates

**Embedding Dimensions**:
- Primary: VECTOR(384) - sentence-transformers
- Table: VECTOR(512)
- Visual: VECTOR(512) - CLIP
- Numerical: VECTOR(256)
- Code: VECTOR(768) - CodeBERT

**Idempotent**: ✅ `CREATE TABLE IF NOT EXISTS`

---

### 03_seed_departments.sql (2.3 KB)

**Purpose**: Create 7 organizational departments

**Departments**:
1. Data Operations (DATA_OPS)
2. Technology (TECH)
3. Marketing (MARKETING)
4. Sales (SALES)
5. HR (HR)
6. Finance (FINANCE)
7. General (GENERAL)

**Idempotent**: ✅ `ON CONFLICT (code) DO NOTHING`

---

### 04_seed_teams.sql (3.4 KB)

**Purpose**: Create 28 teams across departments

**Team Distribution**:
- **Data Operations**: 16 teams (DATA_TEAM_1 to DATA_TEAM_16)
- **Technology**: 11 teams (ITM1 to ITM11)
- **Marketing**: 1 team (MKT_TEAM_1)

**Total**: 28 teams

**Idempotent**: ✅ `ON CONFLICT (department_id, code) DO NOTHING`

---

### 05_seed_roles.sql (2.1 KB)

**Purpose**: Create 5 base RBAC roles

**Roles**:
1. **admin** - Full system access
2. **user** - Standard user access
3. **analyst** - Data analysis capabilities
4. **engineer** - Technical capabilities, fine-tuning access
5. **guest** - Read-only access

**Idempotent**: ✅ `ON CONFLICT (name) DO NOTHING`

---

### 06_seed_admin_user.sql (6.2 KB)

**Purpose**: Create default admin user

**Admin User**:
- **Username**: admin
- **Password**: admin (bcrypt hash: `$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LezvpFQ5vz1vEI1tG`)
- **Email**: admin@example.com
- **Department**: Technology (TECH)
- **Team**: ITM11
- **Role**: admin
- **Active**: Yes

**Security Warning**: ⚠️ Change password in production!

**Idempotent**: ✅ Checks for existing admin user

---

### 07_seed_global_project.sql (5.6 KB)

**Purpose**: Create default "Global" project

**Global Project**:
- **Name**: Global
- **Type**: shared
- **Owner**: admin
- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2
- **Dimensions**: 384
- **Similarity Threshold**: 0.7
- **Top K Results**: 5
- **Default**: Yes (is_default = TRUE)

**Idempotent**: ✅ Checks for existing Global project

---

### 08_seed_system_config.sql (6.6 KB)

**Purpose**: Seed 17 database-driven system configurations

**Configuration Categories**:

**Agent Runtime** (4 configs):
- default_model: qwen2.5-coder:7b
- api_base_url: http://ollama:11434
- max_iterations: 15
- timeout_seconds: 300

**Embedding** (5 configs):
- default_provider: sentence-transformers
- default_model: sentence-transformers/all-MiniLM-L6-v2
- default_dimensions: 384
- cache_enabled: true
- batch_size: 32

**Ollama** (3 configs):
- auto_discovery_enabled: true
- sync_interval_seconds: 300
- api_base_url: http://ollama:11434

**Prefect** (3 configs):
- database_schema: prefect
- api_url: http://prefect-server:4200
- enabled: true

**RAG** (3 configs):
- top_k_results: 5
- similarity_threshold: 0.7
- max_context_length: 4000

**Idempotent**: ✅ `ON CONFLICT (config_key) DO UPDATE`

---

### 09_seed_models_registry.sql (9.6 KB)

**Purpose**: Seed 17 LLM models across 3 providers

**Models by Provider**:

**Ollama** (8 models):
- Code: qwen2.5-coder:7b ⭐, codellama:7b, deepseek-coder:6.7b
- Text: llama3.2:3b, mistral:7b, phi3:mini
- Vision: llava:7b, bakllava:7b

**OpenAI** (6 models):
- gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo, o1, o1-mini
- Costs: $0.00015-$0.015 per 1K input tokens

**Anthropic** (3 models):
- claude-3-5-sonnet, claude-3-5-haiku, claude-3-opus
- Costs: $0.0008-$0.015 per 1K input tokens

**Total**: 17 models

**Idempotent**: ✅ `ON CONFLICT (model_id) DO UPDATE`

---

### 10_seed_modules.sql (19 KB)

**Purpose**: Seed all 36 modules across 3 tiers

**Module Distribution**:

**Tier 1 - Core Platform** (10 modules):
- Chat, Fine-Tuning, Admin, Weights Config, Tool Usage
- Evaluation, Project Estimator, Web Scraping, Upload Files, Chat History

**Tier 2 - Domain Verticals** (20 modules):
- Analytics: Predictive Analytics, Sales Performance, Customer Churn, Financial Anomaly
- Construction: EstimatorOne (AU), Planning Classifier, Mine Scope
- Core: Document Intelligence, Generic RAG, Relation Extractor
- Education: Educational Content Management
- E-commerce: Product Recommendation
- HR/Talent: Talent Search, Talent Pulse, Taxonomy SkillMatch
- Insurance: Insurance Risk Assessment
- Language: Multilingual Translator, Code Analysis
- Legal: Legal Document Processing
- Marketing: Campaign Optimizer, Sentiment Social
- Maritime: Maritime Logistics
- Procurement: Procurement Matcher, Spend Smart, Tender Intelligence, Vendor Recommendation

**Tier 3 - Customer Solutions** (6 modules):
- Construction: CRU POC, Construction Monitor POC
- Education: British Council POC
- Finance: Grant Thornton POC
- Insurance: Solera POC, GT Motive POC

**Total**: 36 modules

**Idempotent**: ✅ `ON CONFLICT (module_name) DO UPDATE`

---

### 11_seed_prompt_library.sql (27 KB)

**Purpose**: Seed 25+ production-ready prompts

**Prompt Categories**:

**General** (5 prompts):
- Document Summarization, Q&A Answering, Content Generation, Translation, Classification

**Business** (6 prompts):
- Meeting Minutes, Report Generation, Email Drafting, Comparative Analysis, SWOT Analysis, Executive Briefing

**Data Analysis** (5 prompts):
- Table Extraction, Chart Analysis, Data Validation, Entity Extraction, Statistical Summary

**Technical** (5 prompts):
- Code Review, API Documentation, Debug Analysis, Test Case Generation, Architecture Design

**Legal** (2 prompts):
- Contract Review, Compliance Check

**Education** (2 prompts):
- Course Material, Quiz Generation

**Total**: 25+ prompts

**Features**:
- Variable placeholders ({{document}}, {{question}}, etc.)
- Expected output formats (JSON, Markdown, Text)
- Example inputs and outputs
- Public and verified flags

**Idempotent**: ✅ `ON CONFLICT (name, category) DO UPDATE`

---

### 12_seed_rbac_permissions.sql (17 KB)

**Purpose**: Create complete role-module permission matrix

**Permission Structure**:

**Admin Role**:
- Access: ALL 36 modules
- Permissions: read, write, delete, share

**CxO Role**:
- Access: ALL modules
- Permissions: read, write, share (no delete on admin modules)

**Manager Role**:
- Access: Tier 1 + Tier 2 modules
- Permissions: read, write, share (limited delete)

**User Role**:
- Access: Tier 1 + basic Tier 2 modules
- Permissions: read, execute (no write/delete)

**ReadOnly Role**:
- Access: Chat, History, Generic RAG only
- Permissions: read only

**Specialized Roles** (also seeded):
- Data Analyst: Analytics modules
- HR Manager: HR/Talent modules
- Procurement Manager: Procurement modules
- Customer Success: Customer Solutions

**Total Permissions**: 200+ permission entries

**Idempotent**: ✅ `ON CONFLICT DO NOTHING`

---

### 13_create_indexes.sql (27 KB)

**Purpose**: Create 190+ performance indexes

**Index Categories**:

**Vector Indexes** (7):
- document_chunks (embedding) - IVFFlat with 100 lists
- query_cache (embedding) - IVFFlat with 50 lists
- document_chunks (table, visual, numerical, code embeddings)
- session_contexts (embedding)

**Foreign Key Indexes** (60+):
- All FK columns for JOIN optimization

**Query Optimization** (50+):
- username, email, session_id, project_id, module_name, etc.

**Date/Time Indexes** (14):
- created_at, updated_at, executed_at for time-series queries

**Composite Indexes** (18):
- Multi-column indexes for common query patterns

**JSONB Indexes** (4):
- GIN indexes on metadata, meta_info, variables, settings

**Full-Text Search** (3):
- Trigram indexes on content, description, name

**Partial Indexes** (10):
- Filtered indexes for specific patterns (is_active=true, etc.)

**Covering Indexes** (3):
- Index-only scan optimization

**Total**: 190+ indexes

**Idempotent**: ✅ `CREATE INDEX IF NOT EXISTS`

---

## Verification

### Automated Verification

```bash
# Run comprehensive verification script
bash scripts/setup/verify-installation.sh
```

**Checks**:
- Docker containers status
- Database schema (extensions, tables)
- Seed data counts
- Service health (backend, frontend, ollama, prefect)
- Phase 2 APIs (system config, models registry)

### Manual Verification

```bash
# Connect to database
docker exec -it rag-postgres psql -U postgres -d ragchatbot

# Check table count
SELECT COUNT(*) FROM information_schema.tables
WHERE table_schema='public' AND table_type='BASE TABLE';
-- Expected: 67 tables

# Check admin user
SELECT username, email, role FROM users WHERE username='admin';
-- Expected: 1 row

# Check seed data
SELECT 'departments' AS table, COUNT(*) AS count FROM departments
UNION ALL SELECT 'teams', COUNT(*) FROM teams
UNION ALL SELECT 'roles', COUNT(*) FROM roles
UNION ALL SELECT 'modules', COUNT(*) FROM modules
UNION ALL SELECT 'prompts', COUNT(*) FROM prompt_library
UNION ALL SELECT 'configs', COUNT(*) FROM system_config
UNION ALL SELECT 'models', COUNT(*) FROM models;

-- Expected:
-- departments: 7
-- teams: 28
-- roles: 5
-- modules: 36
-- prompts: 25+
-- configs: 17
-- models: 17

# Check extensions
SELECT extname, extversion FROM pg_extension
WHERE extname IN ('uuid-ossp', 'vector');
-- Expected: Both extensions present

# Check indexes
SELECT COUNT(*) FROM pg_indexes WHERE schemaname='public';
-- Expected: 190+ indexes
```

---

## Troubleshooting

### Issue: Master script fails midway

**Solution**: Check error message, fix issue, re-run script (idempotent)

```bash
# Re-run is safe
bash scripts/setup/clean-install-database.sh
```

### Issue: "Database does not exist"

**Solution**: Create database first

```bash
docker exec rag-postgres psql -U postgres -c "CREATE DATABASE ragchatbot;"
```

### Issue: "Extension not available"

**Solution**: Verify pgvector is installed in PostgreSQL container

```bash
# Check available extensions
docker exec rag-postgres psql -U postgres -c "\dx"

# If pgvector missing, rebuild postgres container with pgvector support
```

### Issue: Permission denied on scripts

**Solution**: Make scripts executable

```bash
chmod +x scripts/setup/clean-install-database.sh
chmod +x scripts/setup/verify-installation.sh
```

### Issue: Slow vector index creation

**Expected**: Vector indexes on large datasets can take 1-5 minutes

**Solution**: Wait for completion or run indexes separately:

```bash
# Skip indexes in initial run, add them later
docker exec -i rag-postgres psql -U postgres -d ragchatbot \
  < backend/sql/13_create_indexes.sql
```

---

## Migration from Old System

### For Existing Installations

If you have an existing installation using the old migration system:

**Option 1: Fresh Install (Recommended)**

```bash
# 1. Backup existing data
docker exec rag-postgres pg_dump -U postgres ragchatbot > backup.sql

# 2. Drop and recreate database
docker exec rag-postgres psql -U postgres -c "DROP DATABASE ragchatbot;"
docker exec rag-postgres psql -U postgres -c "CREATE DATABASE ragchatbot;"

# 3. Run clean installation
bash scripts/setup/clean-install-database.sh

# 4. Restore user data (documents, conversations, etc.)
# ... custom restore script ...
```

**Option 2: Continue with Migrations**

The old migration system in `backend/migrations/` still works and is maintained for upgrade paths. New installations should use the comprehensive SQL system.

---

## Benefits of New System

### 1. Single Source of Truth
- All schema and seed data in one organized location
- Easy to understand complete database structure
- Clear documentation of all defaults

### 2. Idempotent Operations
- Safe to run multiple times
- No state tracking needed
- Easier error recovery

### 3. Faster Installation
- ~30-60 seconds for complete setup
- Parallel execution potential
- No incremental complexity

### 4. Better Testability
- Clear verification points
- Automated testing friendly
- Reproducible environments

### 5. Improved Maintainability
- Modular structure (13 scripts vs 44 migrations)
- Easy to add new seed data
- Clear dependency order

### 6. Production Ready
- All essential data included
- No manual configuration needed
- Immediate functionality

---

## Future Enhancements

### Planned Improvements

1. **Data Export/Import**
   - Export existing user data
   - Import into fresh installation
   - Selective data migration

2. **Environment Variants**
   - Development seed data
   - Staging configurations
   - Production minimal seed

3. **Automated Testing**
   - Integration tests for installation
   - Verification test suite
   - Performance benchmarks

4. **Docker Integration**
   - Database initialization in docker-compose
   - Volume mounting for SQL scripts
   - Automatic setup on first run

---

## Related Documentation

- **SQL Scripts**: `backend/sql/README.md`
- **Verification Guide**: `scripts/setup/verify-installation.sh`
- **Phase 1 Summary**: `docs/implementation/COMPREHENSIVE_ENHANCEMENT_STRATEGY_2026-01-07.md`
- **Phase 2 Summary**: `docs/implementation/PHASE2_BACKEND_COMPLETION_SUMMARY.md`
- **Requirements**: `docs/future_enhancements/Enhancements.txt`

---

**Last Updated**: 2026-01-07
**Status**: ✅ Production Ready
**Tested**: ✅ Verified on PostgreSQL 16 + pgvector
**Maintenance**: Active
