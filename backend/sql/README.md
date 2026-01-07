# Comprehensive SQL Setup Scripts

**Purpose**: Single-source database setup scripts for fresh Enterprise RAG Chatbot installations

**Created**: 2026-01-07
**Related**: Requirement #9 - Comprehensive Installation Scripts

---

## Overview

This directory contains comprehensive SQL scripts that set up the entire database schema and seed all essential data in the correct order. These scripts replace the incremental migration-based approach with a clean, comprehensive setup.

### Design Philosophy

1. **Single Source of Truth**: All schema and seed data in organized SQL files
2. **Idempotent**: Safe to run multiple times (uses IF NOT EXISTS, ON CONFLICT)
3. **Order-Dependent**: Scripts numbered to enforce dependency order
4. **Production-Ready**: Includes all essential data for immediate functionality
5. **Well-Documented**: Each script contains purpose, dependencies, and notes

---

## Current Database State Analysis

### Tables (67 total)
```
Core RAG:          documents, document_chunks, query_cache, conversations, messages
Projects:          projects, project_members
Web Scraping:      web_scrape_jobs, scraping_configs, scraping_audit_log
RBAC:              users, roles, user_roles, departments, teams, user_teams
Permissions:       role_permissions, role_module_permissions, document_permissions
Modules:           modules, module_configurations, module_activations, module_usage_logs
Prompt Library:    prompt_library, prompt_ratings, prompt_usage_log
Audit & Metrics:   audit_logs, usage_metrics, tool_usage_stats, api_key_access_log
Sessions:          chat_sessions, session_documents, session_contexts, conversation_messages
Templates:         output_templates, extraction_results, saved_css_templates
Evaluation:        evaluation_configs, evaluation_results, evaluation_benchmarks, evaluation_cache
Fine-tuning:       finetuning_jobs, finetuning_datasets, finetuned_models, training_metrics, model_approvals
Phase 2 Additions: system_config, models
Configuration:     config_schemas, config_versions, config_templates, config_audit_logs
Export Wizard:     export_packages, export_jobs, export_templates, export_audit_logs
API & Security:    api_keys, api_credentials
Other:             domain_statistics, deployment_instances, agent_tasks, skill_modules, human_feedback
```

### Current Seed Data Counts

| Table | Current Count | Target | Status |
|-------|--------------|--------|--------|
| users | 13 (mostly test) | 1 admin | ⚠️ Needs cleanup |
| departments | 3 | 7 | ⚠️ Incomplete |
| teams | 28 | 28 | ✅ Complete |
| roles | 5 | 5+ | ⚠️ Need verification |
| modules | 26 | 36 | ⚠️ Missing 10 modules |
| prompt_library | 5 | 20+ | ❌ Very incomplete |
| system_config | 17 | 17 | ✅ Complete (Phase 1) |
| models | 17 | 17+ | ✅ Complete (Phase 1) |
| projects | ? | 1 (Global) | ❓ Need verification |
| role_permissions | ? | Full matrix | ❓ Need verification |

---

## Script Organization

### Execution Order

```
00_CLEAN_INSTALL_MASTER.sql         # Master installation script (calls all others)
├── 01_extensions.sql               # PostgreSQL extensions (uuid-ossp, pgvector)
├── 02_complete_schema.sql          # All 67 tables in dependency order
├── 03_seed_departments.sql         # 7 departments
├── 04_seed_teams.sql               # 28 teams (scoped to departments)
├── 05_seed_roles.sql               # 5 base roles + module-specific roles
├── 06_seed_admin_user.sql          # Admin user (admin/admin, Technology/ITM11)
├── 07_seed_global_project.sql      # Default Global project
├── 08_seed_system_config.sql       # 17 system configurations (Phase 1)
├── 09_seed_models_registry.sql     # 17 LLM models (Phase 1)
├── 10_seed_modules.sql             # All 36 modules (Tier 1, 2, 3)
├── 11_seed_prompt_library.sql      # 20+ production prompts
├── 12_seed_rbac_permissions.sql    # Complete role-module permission matrix
└── 13_create_indexes.sql           # Performance indexes (vector, foreign keys)
```

### Schema Dependencies (02_complete_schema.sql)

**Critical Order**:
1. Base tables (no FKs): departments, roles
2. User management: users → user_roles, user_teams
3. Projects: projects → project_members
4. Modules: modules → module_configurations, module_activations
5. Documents: documents → document_chunks, document_permissions
6. Conversations: conversations → messages, conversation_messages
7. All others with FKs

---

## Essential Seed Data Specifications

### 1. Departments (03_seed_departments.sql)
```sql
Data Operations (DATA_OPS)
Technology (TECH)
Marketing (MARKETING)
Sales (SALES)
HR (HR)
Finance (FINANCE)
General (GENERAL)
```

### 2. Teams (04_seed_teams.sql)
```
Data Operations: 16 teams (DATA_TEAM_1 to DATA_TEAM_16)
Technology: 11 teams (ITM1 to ITM11)
Marketing: 1 team (MKT_TEAM_1)
```

### 3. Roles (05_seed_roles.sql)
```
admin       - Full system access
user        - Standard user access
analyst     - Data analysis capabilities
engineer    - Technical capabilities
guest       - Read-only access
```

### 4. Admin User (06_seed_admin_user.sql)
```
Username: admin
Password: admin (hashed: $2b$12$...)
Email: admin@example.com
Department: Technology
Team: ITM11
Role: admin
```

### 5. Global Project (07_seed_global_project.sql)
```
Name: Global
Description: Default project for all users
Type: shared
Default Embedding: sentence-transformers/all-MiniLM-L6-v2 (384 dim)
```

### 6. System Config (08_seed_system_config.sql)
**17 configurations across categories**:
- Agent Runtime (default_model, max_iterations, timeout_seconds)
- RAG (top_k_results, similarity_threshold, max_context_length)
- Embedding (default_model, default_dimensions, batch_size)
- Ollama Integration (base_url, auto_discovery_enabled, sync_interval_seconds)
- Prefect (api_url, enabled)

### 7. Models Registry (09_seed_models_registry.sql)
**17 LLM models**:
- Ollama: qwen2.5-coder:7b, mistral:7b, llama3.2:3b
- OpenAI: gpt-4o, gpt-4o-mini, gpt-3.5-turbo
- Anthropic: claude-3-5-sonnet, claude-3-opus
- OpenRouter: Various (deepseek, qwen, llama)

### 8. Modules (10_seed_modules.sql)
**36 total modules**:

**Tier 1 (Core Platform) - 10 modules**:
- Chat, Fine-Tuning, Admin, Weights Config, Tool Usage
- Evaluation, Project Estimator, Web Scraping, Upload Files, Chat History

**Tier 2 (Domain Verticals) - 20 modules**:
- Analytics: Predictive Analytics, Sales Performance, Customer Churn, Financial Anomaly Detection
- Construction: EstimatorOne (AU), Planning Classifier, Mine Scope Analysis
- Core: Document Intelligence, Generic RAG, Relation Extractor
- Education: Educational Content Management
- E-commerce: Product Recommendation
- Finance: Financial Anomaly Detection
- HR/Talent: Talent Search, Talent Pulse, Taxonomy SkillMatch
- Insurance: Insurance Risk Assessment
- Language: Multilingual Translator, Code Analysis
- Legal: Legal Document Processing
- Marketing: Campaign Optimizer, Sentiment Social
- Maritime: Maritime Logistics
- Procurement: Procurement Matcher, Spend Smart, Tender Intelligence, Vendor Recommendation

**Tier 3 (Customer Solutions) - 6 modules**:
- Construction: CRU POC, Construction Monitor POC
- Education: British Council POC
- Finance: Grant Thornton POC
- Insurance: Solera POC, GT Motive POC

### 9. Prompt Library (11_seed_prompt_library.sql)
**20+ production prompts across categories**:
- General: Document Summarization, Q&A Answering, Content Generation
- Business: Meeting Minutes, Report Generation, Email Drafting, Comparative Analysis
- Data Analysis: Table Extraction, Chart Analysis, Data Validation, Entity Relationship Extraction
- Technical: Code Review, API Documentation, Debug Analysis, Test Case Generation
- Legal: Contract Review, Compliance Check, Risk Assessment
- Education: Course Material, Quiz Generation, Feedback Analysis

### 10. RBAC Permissions (12_seed_rbac_permissions.sql)
**Complete role-module permission matrix**:
- admin: ALL modules (read, write, execute)
- user: Tier 1 + assigned Tier 2/3 modules (read, execute)
- analyst: Data analysis modules (read, execute)
- engineer: Technical modules + Fine-tuning (read, write, execute)
- guest: Read-only access to Chat, Generic RAG

---

## Usage

### Fresh Installation

```bash
# 1. Ensure PostgreSQL container is running
docker ps | grep postgres

# 2. Run master installation script
psql -U postgres -d ragchatbot -f backend/sql/00_CLEAN_INSTALL_MASTER.sql

# OR use the installation script
bash scripts/setup/clean-install-database.sh
```

### Verification

```bash
# Run verification script
bash scripts/setup/verify-installation.sh

# Manual checks
psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM users WHERE username='admin';"
psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM modules;"
psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM prompt_library;"
```

---

## Migration from Incremental Migrations

### Current Migration Files (44 files)

The existing migrations in `backend/migrations/` are **NOT replaced**. They remain for:
1. Historical reference
2. Upgrade paths from older installations
3. Development/testing purposes

### Relationship

```
backend/migrations/      # Incremental changes (000 → 027)
  ├─ Development history
  ├─ Upgrade paths
  └─ Reference implementations

backend/sql/            # Comprehensive fresh install (NEW)
  ├─ Production-ready
  ├─ Single source of truth
  └─ All-in-one setup
```

---

## Idempotency Patterns

### CREATE TABLE
```sql
CREATE TABLE IF NOT EXISTS table_name (
    ...
);
```

### INSERT SEED DATA
```sql
-- Option 1: ON CONFLICT DO NOTHING (when unique constraint exists)
INSERT INTO departments (name, code, description) VALUES
    ('Technology', 'TECH', 'Software engineering teams')
ON CONFLICT (code) DO NOTHING;

-- Option 2: Conditional insert (for complex checks)
INSERT INTO users (username, email, password_hash, role)
SELECT 'admin', 'admin@example.com', '$2b$12$...', 'admin'
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin');
```

### CREATE INDEX
```sql
CREATE INDEX IF NOT EXISTS idx_name ON table_name(column);
```

---

## Maintenance

### Adding New Seed Data

1. Identify the appropriate script (e.g., `11_seed_prompt_library.sql` for new prompts)
2. Add data using idempotent INSERT pattern
3. Test script independently
4. Update `00_CLEAN_INSTALL_MASTER.sql` if new script added

### Schema Changes

1. Update `02_complete_schema.sql` with new table
2. Add corresponding seed data script if needed
3. Maintain dependency order
4. Test clean install

---

## Known Issues from Previous Attempts

### Issue 1: Embedding Dimension Mismatches
- **Problem**: Hardcoded 1536 dimensions (OpenAI), but using 384 (sentence-transformers)
- **Solution**: `02_complete_schema.sql` uses VECTOR(384), configurable via `system_config`

### Issue 2: Missing Admin User Defaults
- **Problem**: Admin created without department/team assignment
- **Solution**: `06_seed_admin_user.sql` assigns Technology/ITM11

### Issue 3: Prefect Database Conflicts
- **Problem**: Prefect created separate `prefect` database
- **Solution**: Phase 3 - Prefect uses `ragchatbot` with `prefect` schema

### Issue 4: Incomplete RBAC Setup
- **Problem**: Roles exist but no module permissions
- **Solution**: `12_seed_rbac_permissions.sql` creates full permission matrix

### Issue 5: Module Registration Gaps
- **Problem**: Only 26/36 modules registered
- **Solution**: `10_seed_modules.sql` includes all Tier 1, 2, 3 modules

---

## References

- **Requirements**: `docs/future_enhancements/Enhancements.txt` (Requirement #9)
- **Phase 1 Summary**: `docs/implementation/COMPREHENSIVE_ENHANCEMENT_STRATEGY_2026-01-07.md`
- **Migration History**: `backend/migrations/` directory
- **External Reference**: https://github.com/trajeshbe/merit-aiml.git (kiaa-cpu branch)

---

**Last Updated**: 2026-01-07
**Status**: ✅ Complete - All 13 SQL Scripts Created
**Next Steps**: Test and integrate into master installation script

---

## Script Details

### 10_seed_modules.sql (563 lines, ~19KB)
- **Purpose**: Seeds all 36 modules across 3 tiers
- **Coverage**:
  - Tier 1: 10 core platform modules
  - Tier 2: 20 domain vertical modules
  - Tier 3: 6 customer solution modules
- **Features**:
  - Complete module metadata (name, code, description, icon, route)
  - JSONB meta_info with tier and category tags
  - Idempotent (ON CONFLICT DO UPDATE)
  - Verification reporting

### 11_seed_prompt_library.sql (801 lines, ~27KB)
- **Purpose**: Seeds 25+ production-ready prompts
- **Coverage**:
  - General: 5 prompts (summarization, Q&A, content generation, translation, classification)
  - Business: 6 prompts (meeting minutes, reports, email, comparison, SWOT, executive briefing)
  - Data Analysis: 5 prompts (table extraction, chart analysis, validation, entity extraction, statistics)
  - Technical: 5 prompts (code review, API docs, debug analysis, test cases, architecture)
  - Legal: 2 prompts (contract review, compliance check)
  - Education: 2 prompts (course material, quiz generation)
- **Features**:
  - Complete prompt templates with variables
  - Expected output formats (JSON, Markdown, Text)
  - Example inputs and outputs
  - Public and verified flags
  - Category and tag metadata

### 12_seed_rbac_permissions.sql (498 lines, ~17KB)
- **Purpose**: Creates complete role-module permission matrix
- **Coverage**:
  - Admin: Full access to all 36 modules
  - CxO: Full access except admin deletions
  - Manager: Tier 1 + Tier 2 modules (limited admin)
  - User: Tier 1 + basic Tier 2 modules
  - ReadOnly: View-only access (chat, history, generic RAG)
- **Features**:
  - Granular permissions (can_read, can_write, can_delete, can_share)
  - Specialized role grants (Data Analyst, HR Manager, Procurement Manager, Customer Success)
  - Both role_module_permissions (FK-based) and role_permissions (legacy)
  - Verification queries and reporting

### 13_create_indexes.sql (574 lines, ~27KB)
- **Purpose**: Creates all performance indexes
- **Coverage**:
  - Vector Indexes: 7 indexes (embedding, table, visual, numerical, code, cache, session)
  - Foreign Key Indexes: 60+ indexes for JOIN optimization
  - Query Optimization: 50+ indexes on frequently queried columns
  - Date/Time Indexes: 14 indexes for time-series queries
  - Composite Indexes: 18 indexes for multi-column queries
  - JSONB Indexes: 4 GIN indexes for metadata queries
  - Full-Text Search: 3 trigram indexes
  - Partial Indexes: 10 indexes for specific patterns
  - Covering Indexes: 3 indexes for index-only scans
- **Features**:
  - All indexes use IF NOT EXISTS
  - IVFFlat vector indexes with tuned lists parameter
  - GIN indexes for JSONB and array queries
  - Partial indexes for active records and specific states
  - Index maintenance commands and performance tips
  - Verification reporting with index counts
