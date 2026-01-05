# Database Setup Script - Issues Analysis

> **Date**: 2026-01-05
> **Purpose**: Comprehensive evaluation of setup-database-complete.sh against actual database state

---

## Executive Summary

**Status**: ❌ **CRITICAL ISSUES FOUND**

The database setup script has significant gaps and issues that need immediate correction:

- **Migration Files**: 47 actual files vs script only handles ~35
- **Actual Tables**: 64 tables in database
- **Missing Migrations**: 12+ migration files not included in script
- **Duplicate Migrations**: Multiple files with same numbers (e.g., 001_, 004_, 012_, 013_, etc.)
- **Order Issues**: Migrations applied in incorrect dependency order

---

## Issues Identified

### 1. Missing Migration Files

The script does **NOT** apply these existing migration files:

```
❌ 008_update_department_structure.sql - NOT IN SCRIPT
❌ training_checkpoints table - NOT CREATED (from finetuning)
❌ skill_modules table - NOT CREATED
❌ document_permissions table - NOT CREATED
❌ extraction_results table - NOT CREATED
❌ output_templates table - NOT CREATED
❌ document_extractions table - NOT CREATED
❌ domain_statistics table - NOT CREATED
❌ scraping_audit_log table - NOT CREATED
❌ prompt_ratings table - NOT CREATED
❌ prompt_usage_log table - NOT CREATED
❌ user_teams table - NOT CREATED
❌ module_activations table - NOT CREATED
```

### 2. Duplicate Migration Numbers

Multiple migrations share the same number prefix, creating ambiguity:

**001_** (2 files):
- `001_add_evaluation_tables.sql`
- `001_add_rbac_and_audit.sql`

**004_** (3 files):
- `004_add_api_credentials.sql`
- `004_add_saved_css_templates.sql`
- `004_add_scraping_configs.sql`

**006_** (2 files):
- `006_add_modules_and_projects.sql`
- `006_add_rbac_tables.sql`

**007_** (2 files):
- `007_add_project_tracking.sql`
- `007_seed_rbac_data.sql`

**008_** (2 files):
- `008_normalize_departments_teams.sql`
- `008_update_department_structure.sql` ❌ NOT IN SCRIPT

**012_** (4 files):
- `012_add_default_project.sql`
- `012_add_project_based_scraping.sql`
- `012_add_project_to_sessions.sql`
- `012_add_prompt_library_and_templates.sql`

**013_** (6 files):
- `013_add_agent_tasks_table.sql`
- `013_add_project_model_preferences.sql`
- `013_add_project_organizational_fks.sql`
- `013_add_user_organizational_fields.sql`
- `013_create_default_global_project.sql`
- `013_seed_role_permissions.sql`

**014_** (3 files):
- `014_add_task_name_and_minio_paths.sql`
- `014_fix_file_type_length.sql`
- `014_fix_web_scrape_jobs_foreign_key.sql`

**020_** (2 files):
- `020_add_dataset_id_to_finetuning_jobs.sql`
- `020_add_finetuning_job_fields.sql`

**024_** (2 files):
- `024_add_modules_management.sql`
- `024_add_tier2_module_tables.sql`

### 3. Tables in Database But No Clear Migration

These tables exist in the database but their creation is not obvious from migration files:

```sql
-- Missing clear migrations for:
training_checkpoints     -- Should be in finetuning migrations
skill_modules           -- Unknown source
document_permissions    -- Unknown source
extraction_results      -- Unknown source
output_templates        -- Unknown source
document_extractions    -- Unknown source
domain_statistics       -- Unknown source
scraping_audit_log      -- Unknown source
prompt_ratings          -- Unknown source
prompt_usage_log        -- Unknown source
user_teams              -- Unknown source
module_activations      -- Unknown source
```

### 4. Migration Order Issues

The script applies migrations in this order, but dependencies may be violated:

**Current Order Issues:**
1. **Step 13** applies `001_add_evaluation_tables.sql` - This should be earlier since it's numbered 001
2. **Step 8** applies `008_update_department_structure.sql` is missing entirely
3. **Fine-tuning migrations** (019-023) don't include training_checkpoints table

---

## Actual Database State

### Tables Count: 64

```
agent_tasks                 api_credentials            api_key_access_log
api_keys                    audit_logs                 chat_sessions
config_audit_logs           config_schemas             config_templates
config_versions             conversation_messages      conversations
departments                 deployment_instances       document_chunks
document_extractions        document_permissions       documents
domain_statistics           evaluation_benchmarks      evaluation_cache
evaluation_configs          evaluation_results         export_audit_logs
export_jobs                 export_packages            export_templates
extraction_results          finetuned_models           finetuning_datasets
finetuning_jobs             human_feedback             messages
model_approvals             module_activations         module_configurations
module_usage_logs           module_user_overrides      modules
output_templates            project_members            projects
prompt_library              prompt_ratings             prompt_usage_log
query_cache                 role_module_permissions    role_permissions
roles                       saved_css_templates        scraping_audit_log
scraping_configs            session_contexts           session_documents
skill_modules               teams                      tool_usage_stats
training_metrics            usage_metrics              user_module_overrides
user_roles                  user_teams                 users
web_scrape_jobs
```

### Migration Files Count: 47

---

## Correct Migration Order

Based on dependencies, migrations should be applied in this order:

### Phase 1: Foundation (000-005)
```
000_base_schema.sql                           # Base tables
001_add_rbac_and_audit.sql                    # RBAC foundation
002_fix_embedding_dimensions.sql              # Schema fix
003_fix_query_cache_default.sql               # Schema fix
004_add_scraping_configs.sql                  # Feature
004_add_saved_css_templates.sql               # Feature
004_add_api_credentials.sql                   # Feature
005_add_tool_usage_tracking.sql               # Feature
```

### Phase 2: RBAC & Organization (006-009)
```
006_add_rbac_tables.sql                       # RBAC tables
007_seed_rbac_data.sql                        # RBAC seed data
008_normalize_departments_teams.sql           # Org structure
008_update_department_structure.sql           # Org updates ❌ MISSING
009_rename_data_ops_teams.sql                 # Org fixes
```

### Phase 3: Audit & Actions (010-011)
```
010_enhance_audit_action_types.sql
011_add_missing_action_types.sql
```

### Phase 4: Projects & Modules (006-013)
```
006_add_modules_and_projects.sql              # Projects foundation
007_add_project_tracking.sql                  # Project tracking
012_add_default_project.sql
012_add_project_to_sessions.sql
012_add_project_based_scraping.sql
012_add_prompt_library_and_templates.sql
013_add_project_model_preferences.sql
013_add_user_organizational_fields.sql
013_add_project_organizational_fks.sql
013_seed_role_permissions.sql
013_create_default_global_project.sql
```

### Phase 5: Agent Tasks (013-014)
```
013_add_agent_tasks_table.sql
014_add_task_name_and_minio_paths.sql
```

### Phase 6: Schema Fixes (014-017)
```
014_fix_file_type_length.sql
014_fix_web_scrape_jobs_foreign_key.sql
015_fix_query_cache_schema.sql
016_add_multi_column_vector_storage.sql
017_fix_session_documents_session_id_type.sql
```

### Phase 7: Evaluation (001, 018)
```
001_add_evaluation_tables.sql                 # Should be here, not in step 13
018_fix_evaluation_results_meta_info.sql
```

### Phase 8: Fine-Tuning (019-023)
```
019_add_finetuning_tables.sql
020_add_finetuning_job_fields.sql
020_add_dataset_id_to_finetuning_jobs.sql
021_add_training_pipeline_stages.sql
022_add_model_approvals_table.sql
023_add_merge_tracking_columns.sql
```

### Phase 9: Tier 2/3 Modules (024)
```
024_add_tier2_module_tables.sql
024_add_modules_management.sql
```

### Phase 10: Dynamic Config (025)
```
025_add_dynamic_configuration_tables.sql
```

### Phase 11: Export Wizard (026)
```
026_add_export_wizard_tables.sql
```

### Phase 12: Additional Features
```
add_extraction_templates.sql
add_enhanced_scraping_fields.sql
```

---

## Critical Fixes Required

### 1. Add Missing Migrations

The script MUST include:
- `008_update_department_structure.sql`
- Check if training_checkpoints, skill_modules, etc. are in existing migrations or need new ones

### 2. Fix Migration Order

- Move `001_add_evaluation_tables.sql` to correct position (after foundation, before project setup)
- Apply all duplicate-numbered migrations in logical order

### 3. Add Missing Tables

Investigate and add migrations for these tables:
- `training_checkpoints`
- `skill_modules`
- `document_permissions`
- `extraction_results`
- `output_templates`
- `document_extractions`
- `domain_statistics`
- `scraping_audit_log`
- `prompt_ratings`
- `prompt_usage_log`
- `user_teams`
- `module_activations`

### 4. Verify Dependencies

Ensure migrations with foreign keys are applied AFTER their parent tables:
- user_teams depends on users and teams
- module_activations depends on modules
- document_permissions depends on documents and users
- etc.

---

## Recommendations

### Immediate Actions

1. **Audit All Migrations**: Review each migration file to identify which tables it creates
2. **Create Missing Migrations**: For tables without clear migrations
3. **Rewrite Script**: Apply all 47 migrations in correct dependency order
4. **Add Verification**: Check for each expected table after migration
5. **Document Dependencies**: Create dependency map for all migrations

### Long-Term Improvements

1. **Rename Migrations**: Use unique sequential numbers (001-047)
2. **Migration Tracking**: Create `schema_migrations` table to track applied migrations
3. **Idempotency**: Ensure all migrations can be re-run safely
4. **Rollback Scripts**: Create down migrations for each up migration
5. **Testing**: Test setup script on clean database regularly

---

## Impact Assessment

### Current Issues Impact

**Severity**: 🔴 **CRITICAL**

**Impact on Fresh Installations:**
- ❌ Missing 12+ tables out of 64 (18.75% incomplete)
- ❌ Incomplete functionality (extraction, modules, fine-tuning)
- ❌ Potential foreign key violations
- ❌ Application errors due to missing tables

**Impact on Documentation:**
- ❌ Documentation claims 90+ tables, but script only creates ~52
- ❌ Feature descriptions don't match actual setup
- ❌ Troubleshooting guides assume complete installation

---

## Next Steps

1. ✅ Create comprehensive database audit
2. ⏳ Fix setup script with all 47 migrations
3. ⏳ Test on clean database
4. ⏳ Update documentation with accurate counts
5. ⏳ Add migration tracking table
6. ⏳ Create verification script

---

**Analysis Completed**: 2026-01-05
**Analyst**: Database Setup Review
**Status**: Issues Documented - Fixes Pending
