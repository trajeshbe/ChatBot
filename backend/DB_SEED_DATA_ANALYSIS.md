# Database Seed Data Analysis - Migrations vs. Current State

**Date**: 2026-01-05
**Purpose**: Ultra-deep validation of database setup to ensure FIXED script creates fully functional database

---

## Executive Summary

### Critical Findings

🔴 **MAJOR MISMATCH**: Department and team structure in migrations (008) does NOT match current production state
🔴 **MAJOR MISMATCH**: Module schema evolved between migrations (007 vs. 024) - current DB uses newer schema
🟢 **MATCH**: Roles are correctly seeded (5 roles)
🟡 **PARTIAL MATCH**: Modules exist but permissions may be incomplete

---

## 1. Roles Analysis

### Migration 007_seed_rbac_data.sql creates:
```sql
5 roles: Admin, CxO, Manager, User, ReadOnly
```

### Current Production Database has:
```json
[
  {"name":"Admin","description":"Full system access - can manage all resources and users"},
  {"name":"CxO","description":"Executive level access - high-level analytics and reporting"},
  {"name":"Manager","description":"Department manager - can manage team resources"},
  {"name":"ReadOnly","description":"Read-only access - cannot modify data"},
  {"name":"User","description":"Standard user - can use application features"}
]
```

**Status**: ✅ **PERFECT MATCH** - 5 roles with correct names and descriptions

---

## 2. Departments Analysis

### Migration 007_seed_rbac_data.sql creates:
- Enterprise (top-level)
- Data Operations
- Technology
- Support Functions
- Plus 16 "Data Team" sub-departments
- Plus 12 "Tech Team" sub-departments
- Plus 3 Support sub-departments (Marketing, Sales, HR)

**Total from 007**: ~35 departments

### Migration 008_normalize_departments_teams.sql creates:
```sql
7 departments:
- Data Operations (DATA_OPS)
- Technology (TECH)
- Marketing (MARKETING)
- Sales (SALES)
- HR (HR)
- Finance (FINANCE)
- General (GENERAL)
```

### Current Production Database has:
```json
[
  {"name":"Data Operations","description":"Data research and operations teams"},
  {"name":"Support Functions","description":"Support, marketing, sales, and HR"},
  {"name":"Technology","description":"Technology and IT teams"}
]
```

**Status**: 🔴 **MAJOR MISMATCH**

**Issue**: Migration 008 creates 7 departments, but production only has 3 active departments with different structure:
- Marketing, Sales, HR, Finance are consolidated into "Support Functions"
- "General" department doesn't exist in production
- "Enterprise" from 007 doesn't exist

**Root Cause**: Database was manually restructured after migration to simplify organizational hierarchy

---

## 3. Teams Analysis

### Migration 008_normalize_departments_teams.sql creates:
```sql
33 teams:
- Data Team 1, Data Team 2, ..., Data Team 16 (16 teams under Data Operations)
- Tech Team 1, Tech Team 2, ..., Tech Team 12 (12 teams under Technology)
- Marketing Team (under Marketing dept)
- Sales Team (under Sales dept)
- HR Team (under HR dept)
- Legacy Team (under General dept)
```

### Current Production Database has:
```
28 teams across 3 departments:

Data Operations (16 teams):
- Air Business Distribution, ALF, DMS Construction Data Research, DODs
- Glenigan FRO, Haymarket, HSJ, HSJ On Medica
- Informa Connect - Data Research, Leadership, Leadscale, LLI Data
- Political Engagement - Research Support, Quality, Tactical Data, Tactical Data Research

Support Functions (2 teams):
- Marketing, Sales

Technology (10 teams):
- Backend Development, Frontend Development
- ITM1, ITM2, ITM6, ITM7, ITM9, ITM10, ITM11, ITM12
```

**Status**: 🔴 **MAJOR MISMATCH**

**Issue**: Migration creates generic "Data Team 1, Data Team 2" teams, but production has actual business unit names

**Root Cause**: Real team names were imported/created after initial migration from actual company organizational data

---

## 4. Modules Analysis

### Migration 007_seed_rbac_data.sql creates (OLD SCHEMA):
```sql
10 modules using OLD schema (name, code, icon, route):
- RAG Chat (rag_chat)
- File Upload (file_upload)
- Web Scraping (web_scraping)
- Data Extraction (data_extraction)
- Project Estimator (project_estimator)
- Evaluation Metrics (evaluation)
- Tool Usage Dashboard (tools_dashboard)
- Weights Configuration (weights_config)
- Admin Panel (admin_panel)
- Audit Logs (audit_logs)
```

### Migration 024_add_modules_management.sql creates (NEW SCHEMA):
```sql
16 modules using NEW schema (module_key, module_name, tier, category):

Tier 2 (10 modules):
- document-intelligence, generic-rag, predictive-analytics
- multilingual-translator, financial-anomaly, legal-document
- insurance-risk, estimator-one-au, mine-scope, educational-content

Tier 3 (6 modules):
- british-council, cru, grant-thornton
- gt-motive, solera, construction-monitor
```

### Current Production Database has:
```
26 modules total:

Tier 1/Core (10 modules) - No tier/category specified:
- Chat, Upload Files, Web Scraping, Admin
- Chat History, Project Estimator, Evaluation
- Weights Config, Tool Usage, Fine-Tuning

Tier 2 (10 modules):
- predictive-analytics, estimator-one-au, document-intelligence, generic-rag
- educational-content, financial-anomaly, insurance-risk, multilingual-translator
- legal-document, mine-scope

Tier 3 (6 modules):
- construction-monitor, cru, british-council
- grant-thornton, gt-motive, solera
```

**Status**: 🟡 **SCHEMA EVOLVED - Needs Migration**

**Key Issue**: Module schema changed between migrations!
- Old schema: `name, code, icon, route` (migration 007)
- New schema: `module_key, module_name, tier, category, module_type` (migration 024)

**Current DB uses**: New schema with `module_key` and `module_name` fields

**Problem**: Migration 007 seeds 10 core modules with OLD schema, but table was later altered to NEW schema (migration 024). Core modules were likely migrated from old format to new, but the FIXED script doesn't handle this properly.

---

## 5. Role-Module Permissions Analysis

### Migration 007 creates permissions for:
- 10 old-schema modules (rag_chat, file_upload, etc.)
- Based on module.code field

### Migration 024 creates permissions for:
- References modules using new schema
- Grants admin role access to all Tier 2/3 modules

### Current Production Database has:
```
45 role-module permissions:

Admin: 10 permissions (full access to all core modules)
CxO: 9 permissions (no Fine-Tuning access)
Manager: 9 permissions (no Admin access)
User: 9 permissions (no Admin access)
ReadOnly: 8 permissions (no Admin or Fine-Tuning access)
```

**Status**: 🟡 **INCOMPLETE**

**Issue**: Current permissions only cover 10 Tier 1 modules. No permissions seeded for Tier 2/3 modules (16 modules)!

**Gap**: Production DB should have permissions for all 26 modules, but only has permissions for 10 core modules.

---

## 6. Database Tables Comparison

### SQLAlchemy Models define: 55 tables
### Current Database has: 64 tables
### **Extra tables (9)** - Created by migrations, no SQLAlchemy models:
1. document_extractions (024_add_tier2_module_tables.sql)
2. extraction_results (024_add_tier2_module_tables.sql)
3. module_activations (024_add_tier2_module_tables.sql)
4. module_usage_logs (024_add_modules_management.sql)
5. role_permissions (024_add_modules_management.sql)
6. saved_css_templates (004_add_saved_css_templates.sql)
7. skill_modules (024_add_tier2_module_tables.sql)
8. tool_usage_stats (005_add_tool_usage_tracking.sql)
9. training_checkpoints (mentioned in analysis but not in current DB)

**Status**: ✅ **EXPECTED** - These tables are managed purely by migrations

---

## 7. Foreign Key Constraints

### Retrieved: 113 foreign key constraints
### Critical relationships verified:
- ✅ modules.id ← role_module_permissions.module_id (CASCADE DELETE)
- ✅ modules.id ← module_usage_logs.module_id (CASCADE DELETE)
- ✅ roles.id ← role_module_permissions.role_id (CASCADE DELETE)
- ✅ departments.id ← teams.department_id (CASCADE DELETE)
- ✅ users.id ← documents.uploaded_by
- ✅ documents.id ← document_chunks.document_id

**Status**: ✅ **ALL CONSTRAINTS IN PLACE**

---

## 8. Indexes

### Retrieved: 335 indexes
### Critical indexes verified:
- ✅ idx_modules_module_key (modules.module_key)
- ✅ idx_modules_is_active (modules.is_active)
- ✅ idx_role_module_perms_role (role_module_permissions.role_id)
- ✅ idx_role_module_perms_module (role_module_permissions.module_id)
- ✅ idx_chunks_embedding (document_chunks.embedding USING ivfflat)
- ✅ idx_departments_name (departments.name)
- ✅ idx_teams_department_id (teams.department_id)

**Status**: ✅ **COMPREHENSIVE INDEXING**

---

## 9. Issues Summary & Impact

### 🔴 CRITICAL Issues (Breaks Fresh Install):

1. **Department Mismatch**
   - **Impact**: Migration 008 creates 7 departments, but production needs 3
   - **Fix Required**: Update seed data to match production (3 departments)

2. **Team Mismatch**
   - **Impact**: Migration creates generic "Data Team 1, Tech Team 2" but production has actual business names
   - **Fix Required**: Seed actual production team names (28 teams)

3. **Module Schema Evolution**
   - **Impact**: Migration 007 uses old schema, but production uses new schema from 024
   - **Fix Required**: Either migrate 007 modules to new schema OR ensure 024 properly handles existing modules

4. **Missing Tier 2/3 Permissions**
   - **Impact**: No role-module permissions for 16 Tier 2/3 modules
   - **Fix Required**: Add seed data to grant appropriate role access to Tier 2/3 modules

### 🟡 MEDIUM Issues (Works but suboptimal):

5. **Permissions Table References**
   - Migration 024 references a `permissions` table that may not exist yet
   - **Fix Required**: Verify permissions table exists or adjust migration order

---

## 10. Recommended FIXED Script Updates

### Phase 1: Foundation & RBAC
```bash
# Apply in order:
000_base_schema.sql
001_add_rbac_and_audit.sql
006_add_rbac_tables.sql
007_seed_rbac_data.sql  # Seeds 5 roles + OLD module schema
```

### Phase 2: Department/Team Normalization
```bash
008_normalize_departments_teams.sql  # Creates 7 departments + 33 teams
# THEN apply custom seed data update:
UPDATE_departments_to_production.sql  # NEW FILE NEEDED
UPDATE_teams_to_production.sql  # NEW FILE NEEDED
```

### Phase 3: Module Management System
```bash
024_add_tier2_module_tables.sql
024_add_modules_management.sql
# THEN apply custom migration:
MIGRATE_old_modules_to_new_schema.sql  # NEW FILE NEEDED
SEED_tier2_tier3_permissions.sql  # NEW FILE NEEDED
```

---

## 11. Required New Migration Files

### File 1: `UPDATE_departments_to_production.sql`
```sql
-- Delete departments not in production
DELETE FROM departments WHERE name NOT IN ('Data Operations', 'Technology', 'Support Functions');

-- Update descriptions
UPDATE departments SET description = 'Data research and operations teams' WHERE name = 'Data Operations';
UPDATE departments SET description = 'Technology and IT teams' WHERE name = 'Technology';
UPDATE departments SET description = 'Support, marketing, sales, and HR' WHERE name = 'Support Functions';
```

### File 2: `UPDATE_teams_to_production.sql`
```sql
-- Delete generic teams
DELETE FROM teams WHERE name LIKE 'Data Team %' OR name LIKE 'Tech Team %';

-- Insert actual production teams (28 teams)
-- [Full INSERT statements with actual team names from production]
```

### File 3: `MIGRATE_old_modules_to_new_schema.sql`
```sql
-- Migrate 10 core modules from old schema to new schema
-- Map old 'code' values to new 'module_key' values
-- Add tier, category, module_type fields
```

### File 4: `SEED_tier2_tier3_permissions.sql`
```sql
-- Grant appropriate role-module permissions for all 16 Tier 2/3 modules
-- Admin: full access to all
-- CxO: read access to analytics modules
-- Manager: execute access to most modules
-- User: limited access
-- ReadOnly: view-only access
```

---

## 12. Verification Checklist for Fresh Install

After running updated FIXED script, verify:

### Tables (64 expected)
```sql
SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';
-- Expected: 64
```

### Roles (5 expected)
```sql
SELECT COUNT(*) FROM roles;
-- Expected: 5
```

### Departments (3 expected)
```sql
SELECT name FROM departments ORDER BY name;
-- Expected: Data Operations, Support Functions, Technology
```

### Teams (28 expected)
```sql
SELECT COUNT(*) FROM teams;
-- Expected: 28

SELECT d.name as dept, COUNT(t.id) as team_count
FROM departments d
LEFT JOIN teams t ON d.id = t.department_id
GROUP BY d.name;
-- Expected: Data Operations (16), Support Functions (2), Technology (10)
```

### Modules (26 expected)
```sql
SELECT tier, COUNT(*) as count
FROM modules
GROUP BY tier
ORDER BY tier;
-- Expected: NULL/1 (10), 2 (10), 3 (6)
```

### Role-Module Permissions (should cover all 26 modules)
```sql
SELECT r.name, COUNT(DISTINCT m.id) as modules_count
FROM roles r
LEFT JOIN role_module_permissions rmp ON r.id = rmp.role_id
LEFT JOIN modules m ON rmp.module_id = m.id
GROUP BY r.name;
-- Expected: Admin (26), CxO (~20), Manager (~20), User (~15), ReadOnly (~10)
```

### Foreign Keys (113 expected)
```sql
SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_type = 'FOREIGN KEY';
-- Expected: 113
```

### Indexes (335 expected)
```sql
SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';
-- Expected: 335
```

---

## 13. Conclusion

**Current FIXED Script Status**: ❌ **WILL NOT CREATE PRODUCTION-READY DATABASE**

**Required Updates**:
1. Replace generic seed data in 008 with actual production department/team structure
2. Handle module schema migration from old (007) to new (024) format
3. Add comprehensive role-module permissions for all 26 modules
4. Verify migration order ensures all dependencies are met

**Next Steps**:
1. Create 4 new migration files (UPDATE_departments, UPDATE_teams, MIGRATE_modules, SEED_permissions)
2. Update FIXED script to apply these migrations in correct order
3. Test fresh database installation
4. Validate all 26 modules are accessible with proper RBAC permissions
5. Verify all 28 teams are correctly seeded under 3 departments

**Estimated Impact**: HIGH - Without these fixes, fresh installations will have:
- Wrong organizational structure (7 deps vs. 3 deps)
- Generic team names instead of actual business units
- No permissions for 16 Tier 2/3 modules (62% of modules unusable)

---

**Analysis Complete** - Ready to update FIXED script
